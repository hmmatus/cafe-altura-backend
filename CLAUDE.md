# CLAUDE.md

Guidance for Claude Code working in this repository.

## Status

Greenfield. The repo currently contains only `requirements.txt` and a `.venv/` — there is no
Django project scaffold yet (no `manage.py`, no settings module, no apps, no git repo).
Expect to create structure rather than discover it. Update this file once the layout exists.

## Stack

- Python 3.12 (`.venv/`, Python 3.12.10)
- Django 6.0.7
- Django REST Framework 3.17.1
- PostgreSQL via `psycopg` 3.3.4 (binary wheels included)
- `django-environ` 0.14.0 for config — settings read from environment / `.env`, never hardcoded

## Commands

Always use the in-repo virtualenv; it is not auto-activated.

```bash
source .venv/bin/activate          # or prefix commands with .venv/bin/
pip install -r requirements.txt

python manage.py runserver
python manage.py migrate
python manage.py makemigrations
python manage.py test
python manage.py createsuperuser
```

Pinning: `requirements.txt` uses exact `==` pins. Keep new dependencies pinned, and regenerate
with `pip freeze > requirements.txt` after installs.

## Conventions

- Config through `django-environ`: `env = environ.Env()`, values from `.env`. `.env` must never
  be committed — add it to `.gitignore` along with `.venv/`, `__pycache__/`, `*.pyc`, `db.sqlite3`.
- `SECRET_KEY`, `DEBUG`, and `DATABASE_URL` come from the environment. No secrets in source.
- DRF for the API layer: serializers in `serializers.py`, viewsets/views in `views.py`, routes
  registered via a router in the app's `urls.py`.
- Database is PostgreSQL — use `env.db()` / `DATABASE_URL` rather than the sqlite default.
