from django.db.models import Count
from .models import Case


def open_cases_with_evidence_count():
    """Return queryset of open cases annotated with evidence_count for EXPLAIN demonstration."""
    return Case.objects.filter(status=Case.Status.OPEN).annotate(
        evidence_count=Count("evidence_items")
    )
