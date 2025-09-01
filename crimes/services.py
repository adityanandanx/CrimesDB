from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import Incident, Case, CaseStatusHistory, AuditLog


def log_action(user, entity, action, details: str = ""):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(getattr(entity, "pk", "")),
        details=details,
    )


def _generate_case_number():
    """Generate sequential case number CASE-YYYY-XXXX where XXXX is zero-padded sequence per year."""
    year = timezone.now().year
    prefix = f"CASE-{year}-"
    from django.db.models import Max

    latest = Case.objects.filter(case_number__startswith=prefix).aggregate(
        m=Max("case_number")
    )["m"]
    if latest:
        try:
            seq = int(latest.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@transaction.atomic
def escalate_incident(incident_id: int, lead_investigator_user_id: int):
    incident = Incident.objects.select_for_update().get(pk=incident_id)
    if incident.status == Incident.Status.ESCALATED:
        return Case.objects.get(incident=incident)

    # Ensure submitted status first
    if incident.status != Incident.Status.SUBMITTED:
        incident.status = Incident.Status.SUBMITTED
        incident.save(update_fields=["status"])

    case_number = _generate_case_number()
    Case_model = Case  # local alias
    lead_user = settings.AUTH_USER_MODEL and Case_model._meta.apps.get_model(
        settings.AUTH_USER_MODEL
    )
    from django.contrib.auth import get_user_model

    User = get_user_model()
    lead = User.objects.get(pk=lead_investigator_user_id)

    case = Case.objects.create(
        case_number=case_number,
        title=incident.title,
        description=incident.description,
        incident=incident,
        status=Case.Status.OPEN,
        lead_investigator=lead,
    )

    CaseStatusHistory.objects.create(
        case=case, old_status=None, new_status=case.status, changed_by=lead
    )

    incident.status = Incident.Status.ESCALATED
    incident.save(update_fields=["status"])

    log_action(
        lead,
        case,
        "escalate_incident",
        details=f"Incident {incident.pk} escalated to case {case.case_number}",
    )
    return case


@transaction.atomic
def close_case(case_id: int, user_id: int, reason: str = ""):
    """Transition a case to CLOSED status if allowed.

    Creates CaseStatusHistory via Case.save() override.
    Logs audit action. Returns updated case.
    """
    return change_case_status(
        case_id, user_id, Case.Status.CLOSED, reason or "Closing case"
    )


ALLOWED_CASE_STATUS_TRANSITIONS = {
    Case.Status.OPEN: {Case.Status.INVESTIGATING, Case.Status.CLOSED},
    Case.Status.INVESTIGATING: {Case.Status.CLOSED},
    Case.Status.CLOSED: {
        Case.Status.ARCHIVED,
        Case.Status.INVESTIGATING,
    },  # allow reopen to investigating
    Case.Status.ARCHIVED: set(),  # terminal
}


@transaction.atomic
def change_case_status(case_id: int, user_id: int, new_status: str, reason: str = ""):
    case = Case.objects.select_for_update().get(pk=case_id)
    if new_status == case.status:
        return case
    # Validate transition
    # Runtime lookup (ignore static typing nuances of TextChoices)
    allowed = ALLOWED_CASE_STATUS_TRANSITIONS.get(case.status, ALLOWED_CASE_STATUS_TRANSITIONS.get(str(case.status), set()))  # type: ignore
    if new_status not in allowed:
        raise ValueError(f"Illegal transition {case.status} -> {new_status}")
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.get(pk=user_id)
    old = case.status
    case.status = new_status
    setattr(case, "_status_changed_by", user)
    case.save(update_fields=["status", "updated_at"])
    log_action(user, case, "change_status", f"{old} -> {new_status}. {reason}")
    return case
