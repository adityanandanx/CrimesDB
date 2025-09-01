from django.contrib import admin
from .models import (
    Incident,
    Case,
    Person,
    CasePerson,
    Evidence,
    CaseStatusHistory,
    CaseAssignment,
    AuditLog,
)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "reported_by", "created_at")
    search_fields = ("title", "description")
    list_filter = ("status",)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case_number",
        "title",
        "status",
        "lead_investigator",
        "created_at",
    )
    search_fields = ("case_number", "title")
    list_filter = ("status",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "date_of_birth")
    search_fields = ("first_name", "last_name")


@admin.register(CasePerson)
class CasePersonAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "person", "role", "created_at")
    list_filter = ("role",)


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "case", "collected_by", "created_at")
    search_fields = ("code",)


@admin.register(CaseStatusHistory)
class CaseStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "old_status",
        "new_status",
        "changed_at",
        "changed_by",
    )
    list_filter = ("new_status",)


@admin.register(CaseAssignment)
class CaseAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "user", "role", "created_at")
    list_filter = ("role",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "user", "action", "entity_type", "entity_id")
    search_fields = ("action", "entity_type", "entity_id")
