import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_api_create_and_list(client):
    resp = client.post("/api/notes", json={"title": "Hello", "body": "World"})
    assert resp.status_code == 201
    note = resp.get_json()
    assert note["title"] == "Hello"
    assert note["body"] == "World"

    notes = client.get("/api/notes").get_json()
    assert len(notes) == 1
    assert notes[0]["id"] == note["id"]


def test_api_requires_title(client):
    resp = client.post("/api/notes", json={"title": "   "})
    assert resp.status_code == 400
    assert "required" in resp.get_json()["error"]


def test_api_delete(client):
    note_id = client.post("/api/notes", json={"title": "Temp"}).get_json()["id"]
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    assert client.delete(f"/api/notes/{note_id}").status_code == 404


def test_form_create_and_delete(client):
    resp = client.post("/notes", data={"title": "From form", "body": "text"})
    assert resp.status_code == 302
    assert b"From form" in client.get("/").data

    notes = client.get("/api/notes").get_json()
    client.post(f"/notes/{notes[0]['id']}/delete")
    assert client.get("/api/notes").get_json() == []


def test_index_renders_empty_state(client):
    assert b"No notes yet" in client.get("/").data
