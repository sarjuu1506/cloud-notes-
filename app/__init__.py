"""Cloud Notes - a small Flask app backed by SQLite, ready for container deployment."""
import os
import sqlite3

from flask import Flask, g, jsonify, redirect, render_template, request, url_for

MAX_TITLE_LENGTH = 200


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("DATABASE_PATH", os.path.join(app.instance_path, "notes.db")),
    )
    if test_config:
        app.config.update(test_config)

    db_dir = os.path.dirname(os.path.abspath(app.config["DATABASE"]))
    os.makedirs(db_dir, exist_ok=True)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Create the table on startup (idempotent).
    init_db = sqlite3.connect(app.config["DATABASE"])
    init_db.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    init_db.commit()
    init_db.close()

    def validate(title, body):
        title = (title or "").strip()
        body = (body or "").strip()
        if not title:
            return None, None, "Title is required."
        if len(title) > MAX_TITLE_LENGTH:
            return None, None, f"Title must be {MAX_TITLE_LENGTH} characters or fewer."
        return title, body, None

    def fetch_notes():
        rows = get_db().execute(
            "SELECT id, title, body, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------- Health (used by load balancers / container platforms) ----------
    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return jsonify(status="ok")

    # ---------- Web UI ----------
    @app.get("/")
    def index():
        return render_template("index.html", notes=fetch_notes(), error=request.args.get("error"))

    @app.post("/notes")
    def create_note_form():
        title, body, error = validate(request.form.get("title"), request.form.get("body"))
        if error:
            return redirect(url_for("index", error=error))
        db = get_db()
        db.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body))
        db.commit()
        return redirect(url_for("index"))

    @app.post("/notes/<int:note_id>/delete")
    def delete_note_form(note_id):
        db = get_db()
        db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        db.commit()
        return redirect(url_for("index"))

    # ---------- JSON API ----------
    @app.get("/api/notes")
    def api_list():
        return jsonify(fetch_notes())

    @app.post("/api/notes")
    def api_create():
        payload = request.get_json(silent=True) or {}
        title, body, error = validate(payload.get("title"), payload.get("body"))
        if error:
            return jsonify(error=error), 400
        db = get_db()
        cur = db.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body))
        db.commit()
        row = db.execute(
            "SELECT id, title, body, created_at FROM notes WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return jsonify(dict(row)), 201

    @app.delete("/api/notes/<int:note_id>")
    def api_delete(note_id):
        db = get_db()
        cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify(error="Note not found."), 404
        return "", 204

    return app
