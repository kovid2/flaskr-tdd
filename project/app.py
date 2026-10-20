import os
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
    abort,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy

basedir = Path(__file__).resolve().parent

# configuration
DATABASE = "flaskr.db"
USERNAME = "admin"
PASSWORD = "admin"
SECRET_KEY = os.getenv("SECRET_KEY", "change_me")


def normalize_db_url(url):
    """Points Postgres URLs at the installed psycopg2 driver.

    Render gives "postgres://" (which SQLAlchemy rejects), and since
    SQLAlchemy 2.1 a bare "postgresql://" defaults to psycopg v3, which is
    not installed, so the driver is pinned explicitly.
    """
    for scheme in ("postgres://", "postgresql://"):
        if url.startswith(scheme):
            return url.replace(scheme, "postgresql+psycopg2://", 1)
    return url


# use DATABASE_URL (e.g. Postgres on Render) if set, otherwise local SQLite
url = os.getenv("DATABASE_URL", f"sqlite:///{Path(basedir).joinpath(DATABASE)}")

SQLALCHEMY_DATABASE_URI = normalize_db_url(url)
SQLALCHEMY_TRACK_MODIFICATIONS = False


# create and initialize a new Flask app
app = Flask(__name__)
# load the config
app.config.from_object(__name__)
# init sqlalchemy
db = SQLAlchemy(app)

from project import models


def login_required(f):
    """Rejects the request with a 401 JSON error unless the user is logged in."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.")
            return jsonify({"status": 0, "message": "Please log in."}), 401
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """Searches the database for entries, then displays them."""
    entries = db.session.query(models.Post).order_by(models.Post.id.desc())
    return render_template("index.html", entries=entries)


@app.route("/add", methods=["POST"])
def add_entry():
    """Adds new post to the database."""
    if not session.get("logged_in"):
        abort(401)
    new_entry = models.Post(request.form["title"], request.form["text"])
    db.session.add(new_entry)
    db.session.commit()
    flash("New entry was successfully posted")
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login/authentication/session management."""
    error = None
    if request.method == "POST":
        if request.form["username"] != app.config["USERNAME"]:
            error = "Invalid username"
        elif request.form["password"] != app.config["PASSWORD"]:
            error = "Invalid password"
        else:
            session["logged_in"] = True
            flash("You were logged in")
            return redirect(url_for("index"))
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """User logout/authentication/session management."""
    session.pop("logged_in", None)
    flash("You were logged out")
    return redirect(url_for("index"))


@app.route("/search/", methods=["GET"])
def search():
    """Shows posts whose title or text contains the query (case-insensitive)."""
    query = request.args.get("query")
    if query:
        entries = db.session.query(models.Post).filter(
            db.or_(
                models.Post.title.icontains(query, autoescape=True),
                models.Post.text.icontains(query, autoescape=True),
            )
        )
        return render_template("search.html", entries=entries, query=query)
    return render_template("search.html")


@app.route("/delete/<int:post_id>", methods=["GET"])
@login_required
def delete_entry(post_id):
    """Deletes post from database."""
    result = {"status": 0, "message": "Error"}
    try:
        db.session.query(models.Post).filter_by(id=post_id).delete()
        db.session.commit()
        result = {"status": 1, "message": "Post Deleted"}
        flash("The entry was deleted.")
    except Exception as e:
        result = {"status": 0, "message": repr(e)}
    return jsonify(result)


if __name__ == "__main__":
    app.run()
