import os
from pathlib import Path

TEST_DB = "test.db"
BASE_DIR = Path(__file__).resolve().parent.parent

# Flask-SQLAlchemy creates its engine when the app module is imported, so the
# test database must be chosen *before* project.app is imported. conftest.py
# is loaded by pytest before any test module, which guarantees that ordering
# (and stops tests from ever touching the dev SQLite file or Postgres).
os.environ["DATABASE_URL"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"
