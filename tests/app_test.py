import json
import pytest
from pathlib import Path

from project.app import app, db
from project.models import Post

TEST_DB = "test.db"


@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    with app.app_context():
        db.create_all()  # setup
        yield app.test_client()  # tests run here
        db.drop_all()  # teardown


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def add_post(client, title, text):
    """Log in and create a post (helper)"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    return client.post("/add", data=dict(title=title, text=text), follow_redirects=True)


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_database(client):
    """initial test. ensure that the database exists"""
    tester = Path("test.db").is_file()
    assert tester


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data


def test_delete_message(client):
    """Ensure the messages are being deleted"""
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 0
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 1


# ---------------------------------------------------------------------------
# Search page (own tests)
# ---------------------------------------------------------------------------


def test_search_matches_title_and_text(client):
    """A query matches posts by title or by body text; others are hidden"""
    add_post(client, "Testing in Flask", "pytest fixtures")
    add_post(client, "Deploying", "render is a hosting platform for flask apps")
    add_post(client, "Unrelated", "nothing to see here")
    rv = client.get("/search/", query_string={"query": "flask"})
    assert b"Testing in Flask" in rv.data  # match in title
    assert b"Deploying" in rv.data  # match in text only
    assert b"Unrelated" not in rv.data


def test_search_is_case_insensitive(client):
    """Search ignores the case of both the query and the post"""
    add_post(client, "Hello World", "body")
    rv = client.get("/search/", query_string={"query": "hELLo"})
    assert b"Hello World" in rv.data


# ---------------------------------------------------------------------------
# login_required on delete (own tests)
# ---------------------------------------------------------------------------


def test_delete_requires_login(client):
    """Logged-out delete is rejected with 401 and a JSON error"""
    rv = client.get("/delete/1")
    assert rv.status_code == 401
    data = json.loads(rv.data)
    assert data == {"status": 0, "message": "Please log in."}


def test_delete_logged_in_removes_post(client):
    """A logged-in user can remove a post; it disappears from the page"""
    add_post(client, "Delete me", "body")
    with app.app_context():
        post_id = db.session.query(Post).one().id
    rv = client.get(f"/delete/{post_id}")
    assert rv.status_code == 200
    assert json.loads(rv.data)["status"] == 1
    with app.app_context():
        assert db.session.get(Post, post_id) is None
    assert b"Delete me" not in client.get("/").data
