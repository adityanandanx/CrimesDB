from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.core.management import call_command
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


class SeedAdminSiteMixin:
    """Mixin to add a 'Seed Demo Data' button on change list of Incident (or any)"""

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "seed-demo-data/",
                self.admin_site.admin_view(self.seed_demo_view),
                name="seed-demo-data",
            ),
        ]
        return custom + urls

    def seed_demo_view(self, request):
        if not request.user.is_staff:
            return redirect("admin:index")
        try:
            call_command("generate_demo_data", incidents=5, people=10)
            messages.success(request, "Demo data generated.")
        except Exception as e:
            messages.error(request, f"Error generating demo data: {e}")
        return redirect("..")

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        from django.urls import reverse

        extra["seed_demo_url"] = reverse("admin:seed-demo-data")
        return super().changelist_view(request, extra_context=extra)


@admin.register(Incident)
class IncidentAdmin(SeedAdminSiteMixin, admin.ModelAdmin):
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
