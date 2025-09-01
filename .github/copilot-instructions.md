## AI Assistant Project Instructions (criminal)

Focused context so an AI agent can be productive immediately in this repo. Keep responses concise and aligned with these norms.

### 1. Project Snapshot

- Framework: Django 5.2.x (started from `django-admin startproject`).
- Python: >=3.13 (see `pyproject.toml`). Dependency manager implied by `uv.lock` (use `uv sync` / `uv add <pkg>` when adding deps).
- Current dependencies: Only Django; no custom apps yet.
- Two runnable entry points:
  - Web: `manage.py` (Django management / dev server, migrations, etc.).
  - Script: `main.py` (simple standalone CLI stub printing a greeting).

### 2. Layout & Key Files

- Root: `manage.py` (management command runner), `main.py` (standalone script), `pyproject.toml`, `uv.lock`.
- Project package: `criminal/` containing `settings.py`, `urls.py`, `asgi.py`, `wsgi.py`.
- No domain/apps yet (e.g., `accounts`, `cases`, etc.). First app you create should live at repo root (`python manage.py startapp crimes`) and then be added to `INSTALLED_APPS`.

### 3. Settings Conventions

- `criminal/settings.py` is vanilla; DB = SQLite file at `BASE_DIR/db.sqlite3`.
- SECRET_KEY hard-coded (dev only). If adding auth / sensitive features: move to env var (`os.environ.get("DJANGO_SECRET_KEY")`). Do not commit real secrets.
- Add new third-party libraries by editing `[project].dependencies` in `pyproject.toml` then run `uv sync`.

### 4. Common Workflows (prefer these exact commands)

```bash
# Install deps
uv sync

# Run dev server
uv run python manage.py runserver 0.0.0.0:8000

# Create an app
uv run python manage.py startapp crimes

# Migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Run tests (once tests exist)
uv run python manage.py test
```

Use `uv run` rather than raw `python` so the locked env is honored.

### 5. Adding Features (Patterns)

- New app: create -> add to `INSTALLED_APPS` -> create models -> `makemigrations` -> `migrate` -> register URLs using `include()` in `criminal/urls.py`.
- URLs: extend `urlpatterns` in `criminal/urls.py`; for a new app `crimes`, create `crimes/urls.py` and add: `path('crimes/', include('crimes.urls'))`.
- Models: Keep them minimal; SQLite is default. If switching DB, adjust `DATABASES['default']` and ensure new dependency added via `pyproject.toml`.
- Admin: Register models in each app's `admin.py` to leverage built-in admin at `/admin/`.

### 6. Testing Conventions (to introduce)

- Place tests inside each app: `crimes/tests/test_models.py`, etc. Use Django's built-in test runner (no pytest config present yet). When generating tests, import from local app path.

### 7. Static & Templates

- Currently `TEMPLATES['DIRS']` empty and no `STATICFILES_DIRS`. If generating templates, create `templates/` at root and append to `DIRS`. When adding static asset handling, prefer configuring `STATIC_ROOT` for collectstatic later (leave production settings out unless implemented).

### 8. ASGI / WSGI

- `asgi.py` & `wsgi.py` are standard; if introducing async features (e.g., Channels), modify only `asgi.py` and add dependency explicitly.

### 9. Agent Guidance

- Always reflect actual repo state; do not invent config or unadded libs (e.g., DRF, Celery) unless user explicitly requests adding them.
- Before altering `settings.py`, specify minimal diff and rationale (e.g., enabling new app, adding middleware).
- After creating models: generate & run migrations in instructions.
- Favor incremental, explicit changes (one concern per patch: model, URL, view, template, test).
- Keep instructions/environment commands using `uv run` to ensure reproducibility.

### 10. Safe Changes Checklist (apply mentally)

1. Will this require an `INSTALLED_APPS` update? Add it.
2. Added models? Provide migrations step.
3. Added URL patterns? Ensure import of `include` if needed.
4. Added dependency? Update `pyproject.toml` + remind `uv sync`.
5. Touched secrets? Move to env var pattern.

### 11. Example: Adding a Case model (sketch)

1. `uv run python manage.py startapp cases`
2. Add `'cases'` to `INSTALLED_APPS`.
3. In `cases/models.py`: define `Case(models.Model): name = models.CharField(max_length=200)`.
4. Migrate: `uv run python manage.py makemigrations && uv run python manage.py migrate`.
5. Register in `cases/admin.py` for admin visibility.
6. Create `cases/urls.py` + simple view; include in root URLs.

### 12. Future Enhancements (only if asked)

- Switch to Postgres (add `psycopg[binary]`), configure env-driven DB settings.
- Introduce pytest + coverage (would require adding dev deps section).
- Add `.env` management (e.g., `python-dotenv`).

---

Feedback welcome: Tell me if you want deeper guidance on testing, deployment, or converting to API (DRF) so I can extend these instructions.
