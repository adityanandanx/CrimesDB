from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Incident, Case, Person, CasePerson, Evidence
from .serializers import (
    IncidentSerializer,
    CaseSerializer,
    PersonSerializer,
    EvidenceSerializer,
    CaseStatusHistorySerializer,
    CaseAddPersonSerializer,
    CaseAddEvidenceSerializer,
    EscalateIncidentSerializer,
    PersonCreateSerializer,
)
from .permissions import RolePermission
from .services import (
    escalate_incident,
    log_action,
    close_case,
    change_case_status,
    ALLOWED_CASE_STATUS_TRANSITIONS,
)

User = get_user_model()


class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Incident.objects.all().order_by("-created_at")
    serializer_class = IncidentSerializer
    permission_classes = [RolePermission]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="escalate")
    def escalate(self, request, pk=None):
        incident = self.get_object()
        ser = EscalateIncidentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        case = escalate_incident(
            incident.id, ser.validated_data["lead_investigator_user_id"]
        )
        return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        q = request.query_params.get("q")
        qs = self.get_queryset()
        if q:
            qs = qs.filter(title__icontains=q)
        return Response(IncidentSerializer(qs, many=True).data)


class CaseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,  # enable PUT/PATCH for inline edits
    viewsets.GenericViewSet,
):
    queryset = (
        Case.objects.select_related("lead_investigator", "incident")
        .all()
        .order_by("-created_at")
    )
    serializer_class = CaseSerializer
    permission_classes = [RolePermission]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=True, methods=["post"], url_path="people")
    def add_person(self, request, pk=None):
        case = self.get_object()
        ser = CaseAddPersonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        person = get_object_or_404(Person, pk=ser.validated_data["person_id"])
        CasePerson.objects.create(
            case=case, person=person, role=ser.validated_data["role"]
        )
        log_action(request.user, case, "add_person", f"Person {person.pk}")
        return Response({"status": "ok"}, status=201)

    @action(detail=True, methods=["post"], url_path="evidence")
    def add_evidence(self, request, pk=None):
        case = self.get_object()
        ser = CaseAddEvidenceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        evidence = Evidence.objects.create(
            case=case,
            code=ser.validated_data["code"],
            description=ser.validated_data.get("description", ""),
            collected_by=request.user,
        )
        return Response(EvidenceSerializer(evidence).data, status=201)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        case = self.get_object()
        history_qs = case.status_history.order_by("-changed_at")
        data = CaseStatusHistorySerializer(history_qs, many=True).data
        return Response(data)

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        case = self.get_object()
        user = request.user
        reason = request.data.get("reason", "")
        updated = close_case(case.id, user.id, reason=reason)
        return Response(CaseSerializer(updated).data)

    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        case = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response({"detail": "status required"}, status=400)
        try:
            updated = change_case_status(
                case.id,
                request.user.id,
                new_status,
                reason=request.data.get("reason", ""),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(CaseSerializer(updated).data)


class PersonViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Person.objects.all().order_by("last_name", "first_name")
    serializer_class = PersonSerializer
    permission_classes = [RolePermission]

    def get_serializer_class(self):
        if self.action == "create":
            return PersonCreateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("search")
        if q:
            qs = qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
        return qs


from django.db import connection
from rest_framework.views import APIView


class CaseSummaryReportView(APIView):
    permission_classes = [RolePermission]

    def get(self, request):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT case_id, case_number, status, evidence_count, people_count FROM view_case_summary"
            )
            desc = cur.description or []
            cols = [c[0] for c in desc]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return Response(rows)


# ---------- HTML Views (minimal) ----------
from django.views.generic import ListView, DetailView, CreateView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ["title", "description"]


class IncidentListView(LoginRequiredMixin, ListView):
    model = Incident
    template_name = "incidents_list.html"
    context_object_name = "incidents"
    queryset = Incident.objects.order_by("-created_at")


class IncidentDetailView(LoginRequiredMixin, DetailView):
    model = Incident
    template_name = "incident_detail.html"
    context_object_name = "incident"


@login_required
def incident_escalate_view(request, pk: int):
    """HTML endpoint to escalate an incident and redirect to the new case detail page.
    Expects POST with lead_investigator_user_id field.
    """
    if request.method != "POST":
        return redirect("incident-detail", pk=pk)
    inc = get_object_or_404(Incident, pk=pk)
    # If already escalated, just redirect to existing case
    if inc.status == Incident.Status.ESCALATED:
        existing_case = Case.objects.filter(incident=inc).first()
        if existing_case:
            return redirect("case-detail", pk=existing_case.pk)
    lead_investigator_user_id = request.POST.get("lead_investigator_user_id")
    if not lead_investigator_user_id:
        return redirect("incident-detail", pk=pk)
    try:
        lead_id_int = int(lead_investigator_user_id)
    except (TypeError, ValueError):
        return redirect("incident-detail", pk=pk)
    inc_id = inc.pk  # store before service call to satisfy analyzer
    case = escalate_incident(inc_id, lead_id_int)
    return redirect("case-detail", pk=case.pk)


@login_required
def case_add_person_view(request, pk: int):
    """HTML endpoint to add a person to a case.
    Expects POST with person_id and role.
    Only investigators and admins (or lead investigator of the case) can add.
    """
    case = get_object_or_404(Case, pk=pk)
    if request.method != "POST":
        return redirect("case-detail", pk=pk)
    user = request.user
    allowed = (
        user.role in ("admin", "investigator")
        or getattr(case, "lead_investigator_id", None) == user.id
    )
    if not allowed:
        return redirect("case-detail", pk=pk)
    person_id = request.POST.get("person_id")
    role = request.POST.get("role")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    if not role:
        messages.warning(request, "Role required.")
        return redirect("case-detail", pk=pk)
    person = None
    if person_id:
        try:
            person = Person.objects.get(pk=int(person_id))
        except (Person.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Invalid person id.")
            return redirect("case-detail", pk=pk)
    else:
        if not (first_name and last_name):
            messages.error(request, "Provide person id or first & last name.")
            return redirect("case-detail", pk=pk)
        person = Person.objects.create(first_name=first_name, last_name=last_name)
    from .models import CasePerson

    try:
        CasePerson.objects.create(case=case, person=person, role=role)
    except Exception:
        messages.info(request, "Person already linked for that role.")
        return redirect("case-detail", pk=pk)
    log_action(user, case, "add_person_html", f"Person {person.pk}")
    messages.success(request, f"Added {person} as {role}.")
    return redirect("case-detail", pk=pk)


@login_required
def case_add_evidence_view(request, pk: int):
    """HTML endpoint to add evidence to a case.
    Expects POST with code and optional description.
    """
    case = get_object_or_404(Case, pk=pk)
    if request.method != "POST":
        return redirect("case-detail", pk=pk)
    user = request.user
    allowed = (
        user.role in ("admin", "investigator")
        or getattr(case, "lead_investigator_id", None) == user.id
    )
    if not allowed:
        return redirect("case-detail", pk=pk)
    code = request.POST.get("code")
    description = request.POST.get("description", "")
    if not code:
        return redirect("case-detail", pk=pk)
    try:
        Evidence.objects.create(
            case=case, code=code, description=description, collected_by=user
        )
    except Exception:
        pass  # duplicate codes etc.
    return redirect("case-detail", pk=pk)


@login_required
def case_close_view(request, pk: int):
    """HTML endpoint to close a case."""
    case = get_object_or_404(Case, pk=pk)
    if request.method != "POST":
        return redirect("case-detail", pk=pk)
    user = request.user
    allowed = (
        user.role in ("admin", "investigator")
        or getattr(case, "lead_investigator_id", None) == user.id
    )
    if not allowed:
        return redirect("case-detail", pk=pk)
    reason = request.POST.get("reason", "")
    case_pk = case.pk
    close_case(case_pk, user.id, reason=reason)
    from django.contrib import messages

    messages.success(request, "Case closed.")
    return redirect("case-detail", pk=pk)


class IncidentCreateView(LoginRequiredMixin, CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = "incident_form.html"
    success_url = reverse_lazy("incidents-list")

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        return super().form_valid(form)


class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = "case_list.html"
    context_object_name = "cases"

    def get_queryset(self):
        qs = Case.objects.order_by("-created_at")
        status_param = self.request.GET.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class CaseDetailView(LoginRequiredMixin, DetailView):
    model = Case
    template_name = "case_detail.html"
    context_object_name = "case"


class PersonListView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "person_list.html"
    context_object_name = "people"

    def get_queryset(self):
        qs = Person.objects.order_by("last_name", "first_name")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(last_name__icontains=q) | qs.filter(first_name__icontains=q)
        return qs


class PersonDetailView(LoginRequiredMixin, DetailView):
    model = Person
    template_name = "person_detail.html"
    context_object_name = "person"


class PersonCreateView(LoginRequiredMixin, CreateView):
    model = Person
    fields = ["first_name", "last_name", "date_of_birth"]
    template_name = "person_form.html"
    success_url = reverse_lazy("people-list")


from django.views import View
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import render
from django.db import connection


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard.html"

    def get(self, request):
        case_counts = Case.objects.values("status").annotate(c=Count("id"))
        incident_counts = Incident.objects.values("status").annotate(c=Count("id"))
        recent_cases = Case.objects.order_by("-created_at")[:5]
        recent_incidents = Incident.objects.order_by("-created_at")[:5]
        evidence_total = Evidence.objects.count()
        people_total = Person.objects.count()
        from django.db.models import Avg

        avg_evidence = (
            Evidence.objects.values("case")
            .annotate(c=Count("id"))
            .aggregate(avg=Avg("c"))["avg"]
            or 0
        )
        recent_people = Person.objects.order_by("-created_at")[:5]
        return render(
            request,
            self.template_name,
            {
                "case_counts": case_counts,
                "incident_counts": incident_counts,
                "recent_cases": recent_cases,
                "recent_incidents": recent_incidents,
                "evidence_total": evidence_total,
                "people_total": people_total,
                "avg_evidence": avg_evidence,
                "recent_people": recent_people,
                "now": timezone.now(),
            },
        )


class CaseSummaryReportPage(LoginRequiredMixin, View):
    template_name = "reports_case_summary.html"

    def get(self, request):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT case_number, status, evidence_count, people_count FROM view_case_summary ORDER BY case_number"
            )
            desc = cur.description or []
            cols = [c[0] for c in desc]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return render(request, self.template_name, {"rows": rows})


class HomeView(TemplateView):
    template_name = "home.html"
