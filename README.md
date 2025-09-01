# Criminal Case Management

## Setup (SQLite quick start)

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser --username admin --email admin@example.com
uv run python manage.py runserver 0.0.0.0:8000
```

## Postgres (Docker) Setup

The project supports Postgres via Docker. Two approaches:

### A. Dev (live reload, runserver)

Uses `docker-compose.yml` (overrides the image CMD):

```bash
docker compose up -d --build
docker compose exec web uv run python manage.py migrate  # first time / after model changes
docker compose exec web uv run python manage.py createsuperuser --username admin --email admin@example.com
```

### B. Production-like (Gunicorn, auto migrate, wait for DB)

If you build the image and run it directly (not overriding CMD) it will:

1. Wait for Postgres (`wait_for_db.py`)
2. Run `migrate`
3. Optionally create a superuser (if env vars set, see below)
4. Start Gunicorn

### Environment Variable Precedence

1. `DATABASE_URL` (e.g. `postgres://user:pass@host:5432/dbname?sslmode=require`)
2. Individual `POSTGRES_*` variables (legacy compose dev)
3. Fallback to SQLite when `DB_ENGINE=django.db.backends.sqlite3`

Defaults used when individual vars not supplied:

```
POSTGRES_DB=criminal
POSTGRES_USER=criminal
POSTGRES_PASSWORD=criminal
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Automatic Superuser Creation

On container start the script `create_superuser.py` runs. If these are set it will create (once):

```
DJANGO_SUPERUSER_USERNAME
DJANGO_SUPERUSER_PASSWORD
DJANGO_SUPERUSER_EMAIL (optional, default admin@example.com)
DJANGO_SUPERUSER_ROLE=admin (optional)
```

Remove or clear the password env var after first successful deploy for security.

## Deploying to Render.com

1. Push repository to GitHub.
2. Create a Managed Postgres instance in Render (note the Internal Database URL).
3. Create a new Web Service (Docker) for this repo.
4. Set environment variables (minimum):
   - `DATABASE_URL=<Render Internal Database URL>` (already includes sslmode)
   - `DJANGO_SECRET_KEY=<generate secure key>`
   - `DJANGO_DEBUG=false`
   - `ALLOWED_HOSTS=<your-service.onrender.com>`
   - (Optional first deploy) `DJANGO_SUPERUSER_USERNAME=admin` `DJANGO_SUPERUSER_PASSWORD=strongpass` `DJANGO_SUPERUSER_EMAIL=admin@example.com`
5. Deploy. Logs should show: DB wait -> migrations -> superuser creation -> Gunicorn start.
6. After confirming superuser created, remove the `DJANGO_SUPERUSER_PASSWORD` (and optionally the username/email) env vars and redeploy.

Static Files: Served by WhiteNoise (compressed manifest). `collectstatic` occurs during build.

Health Check: You can set `/admin/login/` as a health check path or create a lightweight ping view later.

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
# Local (SQLite)
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser --username admin --email admin@example.com
uv run python manage.py runserver 0.0.0.0:8000

# Docker compose dev (Postgres)
docker compose up -d --build
docker compose exec web uv run python manage.py migrate

# Tests
uv run python manage.py test crimes

# Data utilities
uv run python manage.py refresh_case_counts
uv run python manage.py generate_demo_data --incidents 10 --people 20
```
