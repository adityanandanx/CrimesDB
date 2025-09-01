---
mode: agent
---

PHASE 0: SETUP
Task 0.2: Add a custom User model (AbstractUser or OneToOne extension). Fields: username, role (choices: admin, officer, investigator, viewer), created_at (auto now add). Migrate.
Task 0.3: Create superuser and document how to run server. Provide commands only (no explanation).

PHASE 1: DATABASE CORE
Task 1.1: Implement models: Incident, Case, Person, CasePerson, Evidence, CaseStatusHistory, CaseAssignment, AuditLog. Include **str** methods. Keep fields simple (as in earlier simplified plan).
Task 1.2: Add relationships and constraints:

- Unique: case_number on Case, (case, person, role) on CasePerson, evidence code
- Optional 1:1: Incident to Case (Case.incident FK unique + nullable)
  Task 1.3: Add simple enumerations using choices for statuses and roles.
  Task 1.4: Generate migrations and show the migration file contents (summary only).
  Task 1.5: Create admin registrations for all models with list_display basics.

PHASE 2: BASIC BUSINESS LOGIC
Task 2.1: Write a service function escalate_incident(incident_id, lead_investigator_user_id) that:

- Creates Case (with case_number auto: e.g., CASE-YYYY-XXXX sequential)
- Adds initial CaseStatusHistory (old_status=None, new_status='open')
- Updates incident status to 'submitted' if not already
  Wrap in a transaction.atomic block.
  Task 2.2: Add model save() or signal to automatically append CaseStatusHistory when Case.status changes (except on create).
  Task 2.3: Add a simple audit log utility log_action(user, entity, action) and call it inside the escalation function and on evidence creation.

PHASE 3: SERIALIZERS & API (Django REST Framework)
Task 3.1: Install DRF, add to INSTALLED_APPS.
Task 3.2: Create serializers for User (read-only basic), Incident (list/create), Case (detail), Person (create/link), Evidence (add), CaseStatusHistory (read).
Task 3.3: Create viewsets or APIViews:

- IncidentViewSet: list, retrieve, create
- CaseViewSet: list (filter by status), retrieve
- Case escalate endpoint (custom action POST /incidents/{id}/escalate)
- Case add person POST /cases/{id}/people
- Case add evidence POST /cases/{id}/evidence
- Case history GET /cases/{id}/history
  Task 3.4: Add URL routing under /api/.
  Task 3.5: Implement simple permission classes:
- Admin: all
- Investigator: can modify cases assigned or lead
- Officer: can create incidents
- Viewer: read-only
  Return 403 for disallowed actions.

PHASE 4: VIEWS / QUERIES / OPTIMIZATION
Task 4.1: Create a database view (migration RunSQL) view_case_summary: columns (case_id, case_number, status, evidence_count, people_count).
Task 4.2: Add a read-only API endpoint /api/reports/case-summary that queries the view.
Task 4.3: Add indexes:

- models.Index(fields=['status']) on Case
- UniqueConstraint for composite on CasePerson
- Index on Evidence.case
  Task 4.4: Provide EXPLAIN example for a query listing open cases including evidence count (annotate).

PHASE 5: UI (Minimal Templates)
Task 5.1: Create simple Django template pages (no fancy JS):

- incidents_list.html
- incident_detail.html (button escalate if not escalated)
- case_list.html (filter dropdown)
- case_detail.html (tabs: overview, people, evidence, history)
  Task 5.2: Add forms for creating Incident, adding Person to Case, adding Evidence.
  Task 5.3: Protect pages with login_required and role checks.

PHASE 6: AUTH & SESSIONS
Task 6.1: Implement login/logout views using Django auth templates.
Task 6.2: Add navbar (links: Incidents, Cases, Reports, Logout).

PHASE 7: TESTS
Task 7.1: Write unit tests:

- Model creation (Incident → escalate → Case exists)
- Status change triggers history row
- Evidence creation logs audit
  Task 7.2: Write API tests for:
- Create incident
- Escalate incident
- Add person to case
- Add evidence
  Return JSON snippets for each result.

PHASE 8: DOCUMENT DBMS CONCEPTS
Task 8.1: Generate an ER diagram description (text-based) with cardinalities.
Task 8.2: Produce a README section mapping:

- Keys (list)
- Constraints
- Normalization (brief)
- Transaction example (pseudo SQL)
- Trigger/Signal explanation
- View usage
- Index list (why each)

PHASE 9: OPTIONAL EXTRAS (PICK ANY 2)
Task 9.1: Add a materialized view mv_case_counts (status, count) with a management command to refresh.
Task 9.2: Add a management command to auto-generate demo data (n incidents, people, cases).
Task 9.3: Add a simple full-text search index on Incident.title (Postgres: to_tsvector) and API endpoint /api/incidents/search?q=.

PHASE 10: CLEANUP & DELIVERY
Task 10.1: Produce final README with:

- Setup steps
- Run commands
- Feature list
- DBMS concepts demonstration
- Future work list
  Task 10.2: Provide a compressed list of all commands (migrate, runserver, createsuperuser, tests).

PROMPT TEMPLATES YOU CAN COPY (Examples)

Prompt A (Models):
Generate Django models for Incident, Case, Person, CasePerson (junction), Evidence, CaseStatusHistory, CaseAssignment, AuditLog following this schema: [paste schema]. Include constraints and **str**.

Prompt B (Service Function):
Write a Django service function escalate_incident(incident_id, lead_investigator_user_id) with transaction.atomic that creates a Case, initial history row, updates Incident, logs audit.

Prompt C (Trigger Behavior via Signals):
Add a Django signal or overridden save on Case that, when status changes (and not first creation), inserts a CaseStatusHistory row.

Prompt D (View SQL):
Write a Django migration RunSQL creating view_case_summary combining Case with counts of Evidence and CasePerson.

Prompt E (API):
Create DRF serializers and viewsets for Incident, Case, Person, Evidence plus custom actions (escalate, add person, add evidence, history).

Prompt F (Permissions):
Implement DRF permission classes enforcing: viewers read-only; officers create incidents; investigators modify cases where they’re lead or assigned; admin full access.

Prompt G (Indexes):
Add Meta indexes/constraints for Case.status, CasePerson composite uniqueness, Evidence.case. Show final model Meta snippets only.

Prompt H (Tests):
Write pytest (or Django TestCase) tests for: incident escalation, status change history insertion, adding evidence logs audit row.

Prompt I (Materialized View):
Create SQL migration for materialized view mv_case_counts and a Django management command refresh_case_counts.

Prompt J (README Mapping):
Generate a README section mapping each DBMS concept (keys, constraints, normalization, transactions, view, index, trigger/signal, audit) to exact file names and code references.

CHECKLIST FOR YOU (Do not skip):

1. Models
2. Migrations
3. Admin
4. Service escalation
5. Signals/history
6. Serializers
7. Views/URLs
8. Permissions
9. View + materialized view
10. Templates/forms
11. Tests
12. README mapping

Build this. if you are unsure about what to do at any step, ask questions till you are atleast 90% sure about what to do.
