from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Incident(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        ESCALATED = "escalated", "Escalated"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_incidents",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    def __str__(self):
        return f"Incident #{self.pk} {self.title} ({self.status})"


class Case(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    case_number = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    incident = models.OneToOneField(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case",
        unique=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    lead_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_cases",
    )

    def __str__(self):
        return f"Case {self.case_number} ({self.status})"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        old_status = None
        if not creating:
            try:
                old_status = Case.objects.only("status").get(pk=self.pk).status
            except Case.DoesNotExist:
                old_status = None
        super().save(*args, **kwargs)
        # Log status change AFTER saving (and not on initial create)
        if not creating and old_status != self.status:
            CaseStatusHistory.objects.create(
                case=self,
                old_status=old_status,
                new_status=self.status,
                changed_by=getattr(self, "_status_changed_by", None),
            )

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="case_status_idx"),
        ]


class Person(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class CasePerson(TimeStampedModel):
    class Role(models.TextChoices):
        SUSPECT = "suspect", "Suspect"
        VICTIM = "victim", "Victim"
        WITNESS = "witness", "Witness"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="case_people")
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="person_cases"
    )
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "person", "role"], name="uniq_case_person_role"
            ),
        ]

    def __str__(self):
        return f"{self.person} as {self.role} in {self.case.case_number}"


class Evidence(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="evidence_items"
    )
    description = models.TextField(blank=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collected_evidence",
    )

    def __str__(self):
        return f"Evidence {self.code} ({self.case.case_number})"

    class Meta:
        indexes = [
            models.Index(fields=["case"], name="evidence_case_idx"),
        ]


class CaseStatusHistory(models.Model):
    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="status_history"
    )
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="case_status_changes",
    )

    def __str__(self):
        return f"{self.case.case_number}: {self.old_status} -> {self.new_status} at {self.changed_at:%Y-%m-%d %H:%M:%S}"


class CaseAssignment(TimeStampedModel):
    class Role(models.TextChoices):
        LEAD = "lead", "Lead"
        INVESTIGATOR = "investigator", "Investigator"
        OFFICER = "officer", "Officer"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="case_assignments",
    )
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        unique_together = ("case", "user", "role")

    def __str__(self):
        return f"{self.user} -> {self.case.case_number} ({self.role})"


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"Audit[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.action} {self.entity_type}#{self.entity_id}"
