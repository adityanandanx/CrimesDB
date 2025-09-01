"""
URL configuration for criminal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from crimes.views import (
    IncidentViewSet,
    CaseViewSet,
    CaseSummaryReportView,
    IncidentListView,
    IncidentDetailView,
    IncidentCreateView,
    CaseListView,
    CaseDetailView,
    DashboardView,
    CaseSummaryReportPage,
    incident_escalate_view,
    case_add_person_view,
    case_add_evidence_view,
    case_close_view,
    PersonListView,
    PersonDetailView,
    PersonViewSet,
    PersonCreateView,
    HomeView,
)
from django.contrib.auth import views as auth_views
from users.views import logout_view

router = DefaultRouter()
router.register(r"incidents", IncidentViewSet, basename="incident")
router.register(r"cases", CaseViewSet, basename="case")
router.register(r"people", PersonViewSet, basename="person")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", HomeView.as_view(), name="home"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", logout_view, name="logout"),
    path("accounts/login/", RedirectView.as_view(url="/login/", permanent=False)),
    path("api/", include(router.urls)),
    path(
        "api/reports/case-summary",
        CaseSummaryReportView.as_view(),
        name="case-summary-report",
    ),
    path("incidents/", IncidentListView.as_view(), name="incidents-list"),
    path("incidents/new/", IncidentCreateView.as_view(), name="incident-create"),
    path("incidents/<int:pk>/", IncidentDetailView.as_view(), name="incident-detail"),
    path(
        "incidents/<int:pk>/escalate/", incident_escalate_view, name="incident-escalate"
    ),
    path("cases/", CaseListView.as_view(), name="cases-list"),
    path("cases/<int:pk>/", CaseDetailView.as_view(), name="case-detail"),
    path("cases/<int:pk>/people/add/", case_add_person_view, name="case-add-person"),
    path(
        "cases/<int:pk>/evidence/add/", case_add_evidence_view, name="case-add-evidence"
    ),
    path("cases/<int:pk>/close/", case_close_view, name="case-close"),
    path("people/", PersonListView.as_view(), name="people-list"),
    path("people/<int:pk>/", PersonDetailView.as_view(), name="person-detail"),
    path("people/new/", PersonCreateView.as_view(), name="person-create"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(
        "reports/case-summary",
        CaseSummaryReportPage.as_view(),
        name="reports-case-summary",
    ),
]
