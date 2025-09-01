# Criminal Case Management

## Setup (SQLite quick start)

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser --username admin --email admin@example.com
uv run python manage.py runserver 0.0.0.0:8000
```

## Postgres (Docker) Setup

The project now supports Postgres via Docker.

```bash
docker compose up -d --build
# Run migrations inside the web container
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py createsuperuser --username admin --email admin@example.com
```

Environment variables (with defaults) used in `settings.py`:

```
POSTGRES_DB=criminal
POSTGRES_USER=criminal
POSTGRES_PASSWORD=criminal
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

Fallback: Set `DB_ENGINE=django.db.backends.sqlite3` to force SQLite.

## Features

- Custom user with roles (admin, officer, investigator, viewer)
- Incidents & escalation to Cases with sequential case number
- People linkage (CasePerson) & Evidence tracking
- Automatic case status history via overridden save
- Audit logging (escalation, evidence creation)
- DRF API (/api/) with role-based permissions
- SQL view `view_case_summary` & report endpoint `/api/reports/case-summary`
- Basic HTML pages for browsing & managing incidents and cases
- Management commands: refresh_case_counts, generate_demo_data
- Indexes on case status & evidence.case for performance

## API Highlights

- POST /api/incidents/ create incident (officer)
- POST /api/incidents/{id}/escalate/ escalate to case
- POST /api/cases/{id}/people add person
- POST /api/cases/{id}/evidence add evidence
- GET /api/cases/{id}/history status history
- GET /api/reports/case-summary summarized counts

## DBMS Concepts Mapping

| Concept                       | Implementation                                                              |
| ----------------------------- | --------------------------------------------------------------------------- |
| Primary Keys                  | Implicit auto PK on all models (`crimes/models.py`)                         |
| Unique Keys                   | Case.case_number, Evidence.code, CasePerson (case, person, role) constraint |
| Optional 1:1                  | Case.incident OneToOneField nullable/blank                                  |
| Foreign Keys                  | Numerous (Incident.reported_by, Evidence.case, etc.)                        |
| Enumerations                  | Choices classes inside models (Incident.Status, Case.Status, etc.)          |
| Indexes                       | case_status_idx, evidence_case_idx (migration 0002)                         |
| View                          | `view_case_summary` (migration 0003)                                        |
| (Simulated) Materialized View | refresh_case_counts command (table mv_case_counts)                          |
| Trigger/Signal Equivalent     | Case.save override + evidence post_save signal                              |
| Audit Logging                 | `log_action` in services.py, AuditLog model                                 |
| Transaction                   | `escalate_incident` wrapped in `transaction.atomic`                         |

### Normalization (Brief)

Data separated into entities (Incident, Case, Person, Evidence) reducing duplication. Junction (CasePerson) resolves many-to-many with role attribute. AuditLog is append-only, avoiding update anomalies.

### Transaction Example (Pseudo SQL)

```
BEGIN;
SELECT * FROM incident WHERE id=? FOR UPDATE;
UPDATE incident SET status='submitted' WHERE id=?;
INSERT INTO case (...);
INSERT INTO casestatushistory (...);
UPDATE incident SET status='escalated' WHERE id=?;
COMMIT;
```

### View Usage

`view_case_summary` pre-aggregates counts for quick dashboard/report queries.

### Index Rationale

- case_status_idx: speeds filtering cases by status (common list filter)
- evidence_case_idx: accelerates evidence count aggregation per case

## ER Diagram (Text)

```
Incident 1--0..1 Case
Case 1--* Evidence
Case 1--* CasePerson *--1 Person
Case 1--* CaseStatusHistory
Case 1--* CaseAssignment *--1 User
AuditLog *--1 User (optional)
```

## Tests

Run:

```bash
uv run python manage.py test crimes
```

Tests cover escalation, status history, evidence audit, API flow.

## Future Work

- Real materialized view (Postgres) & refresh scheduling
- Full-text search (Postgres tsvector) for incidents
- Pagination & filtering enhancements
- Fine-grained permissions per action
- Frontend styling & UX improvements

## Command Summary

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser --username admin --email admin@example.com
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py test crimes
uv run python manage.py refresh_case_counts
uv run python manage.py generate_demo_data --incidents 10 --people 20
```
