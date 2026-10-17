# Flaskr-TDD (ECE444 PRA6)

A small Flask blog built test-first, following the
[course README](https://github.com/shuruizUofT/flaskr-tdd/blob/main/README.md),
and deployed to Render with a Postgres database.

**Live app:** _add your Render URL here_

## Features

- Log in / log out (`admin` / `admin`)
- Create posts (HTML allowed in the body, titles are escaped)
- Click a post to delete it (AJAX, `login_required`)
- Search posts by title or text (case-insensitive)

## Run locally

```sh
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python create_db.py
FLASK_APP=project/app.py python -m flask run -p 5001
```

## Tests, lint, format

```sh
python -m pytest
python -m flake8 --exclude env --ignore E402,E501 .
python -m black --exclude=env .
```

`tests/conftest.py` points `DATABASE_URL` at `test.db` *before* the app is
imported. Flask-SQLAlchemy builds its engine at import time, so changing the
config later in a fixture would not take effect and tests would otherwise run
against (and `drop_all` on) the real database.

## Deploy on Render

1. **New → Web Service**, connect this GitHub repo, branch `main`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python create_db.py && gunicorn project.app:app`
   (`create_db.py` is idempotent; it creates the table on first boot.)
4. Plan: Free. Python version comes from `.python-version`
   (or set the `PYTHON_VERSION` env var).
5. **New → Postgres** (Free), then copy its **Internal Database URL** into the
   web service's `DATABASE_URL` environment variable. Optionally also set
   `SECRET_KEY` to a random string.
