from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Incident, Evidence, AuditLog, CaseStatusHistory, Person
from .services import escalate_incident

User = get_user_model()


class CoreFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u1", password="pw", role="investigator"
        )
        self.reporter = User.objects.create_user(
            username="rep", password="pw", role="officer"
        )
        self.client = APIClient()
        logged_in = self.client.login(username="rep", password="pw")
        self.assertTrue(logged_in)

    def test_incident_escalation_creates_case_and_history(self):
        inc = Incident.objects.create(
            title="Test Inc", description="Desc", reported_by=self.reporter
        )
        case = escalate_incident(inc.id, self.user.id)
        self.assertIsNotNone(case.case_number)
        self.assertTrue(case.status_history.filter(new_status="open").exists())

    def test_status_change_creates_history_row(self):
        inc = Incident.objects.create(
            title="Test Inc2", description="Desc", reported_by=self.reporter
        )
        case = escalate_incident(inc.id, self.user.id)
        case.status = case.Status.INVESTIGATING
        case._status_changed_by = self.user
        case.save()
        self.assertTrue(
            CaseStatusHistory.objects.filter(
                case=case, new_status=case.Status.INVESTIGATING
            ).exists()
        )

    def test_evidence_creation_logs_audit(self):
        inc = Incident.objects.create(
            title="Test Inc3", description="Desc", reported_by=self.reporter
        )
        case = escalate_incident(inc.id, self.user.id)
        Evidence.objects.create(
            code="E1", case=case, description="Item", collected_by=self.user
        )
        self.assertTrue(AuditLog.objects.filter(action="create_evidence").exists())

    def test_api_incident_create_and_escalate_and_add_person_and_evidence(self):
        # Create incident via API
        resp = self.client.post(
            "/api/incidents/",
            {"title": "API Incident", "description": "API desc"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        incident_id = resp.data["id"]

        # Escalate (need investigator user id)
        self.client.logout()
        self.client.login(username="u1", password="pw")
        resp2 = self.client.post(
            f"/api/incidents/{incident_id}/escalate/",
            {"lead_investigator_user_id": self.user.id},
            format="json",
        )
        self.assertEqual(resp2.status_code, 201)
        case_id = resp2.data["id"]

        # Add a person
        person = Person.objects.create(first_name="P", last_name="One")
        resp3 = self.client.post(
            f"/api/cases/{case_id}/people/",
            {"person_id": person.id, "role": "witness"},
            format="json",
        )
        self.assertEqual(resp3.status_code, 201)

        # Add evidence
        resp4 = self.client.post(
            f"/api/cases/{case_id}/evidence/",
            {"code": "EVAPI1", "description": "Desc"},
            format="json",
        )
        self.assertEqual(resp4.status_code, 201)

        # History
        resp5 = self.client.get(f"/api/cases/{case_id}/history/")
        self.assertEqual(resp5.status_code, 200)

    def test_html_escalate_flow(self):
        # Create incident (reported by officer)
        inc = Incident.objects.create(
            title="HTML Flow", description="Desc", reported_by=self.reporter
        )
        inc_pk = inc.pk
        # Login as investigator to escalate
        self.client.logout()
        self.client.login(username="u1", password="pw")
        lead_pk = self.user.pk
        resp = self.client.post(
            f"/incidents/{inc_pk}/escalate/", {"lead_investigator_user_id": lead_pk}
        )
        # Should redirect to case detail
        self.assertIn(resp.status_code, (302, 301))
        hist = CaseStatusHistory.objects.first()
        self.assertIsNotNone(hist)
        case_obj = getattr(hist, "case", None)
        self.assertIsNotNone(case_obj)
        self.assertEqual(getattr(case_obj, "incident_id"), inc_pk)

    def test_close_case_api(self):
        inc = Incident.objects.create(
            title="To Close", description="Desc", reported_by=self.reporter
        )
        inc_pk = inc.pk
        lead_pk = self.user.pk
        case = escalate_incident(inc_pk, lead_pk)
        case_pk = case.pk
        self.client.logout()
        self.client.login(username="u1", password="pw")
        resp = self.client.post(
            f"/api/cases/{case_pk}/close/", {"reason": "Completed"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        case.refresh_from_db()
        self.assertEqual(case.status, case.Status.CLOSED)
