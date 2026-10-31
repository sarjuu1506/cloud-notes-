# Cloud Notes

A small notes app built with Flask and SQLite, packaged in a Docker container so it
runs the same locally and on any cloud platform that runs containers.

It demonstrates the core cloud-computing ideas:

- **Containerization** – the app and its dependencies ship as one Docker image.
- **Configuration via environment variables** – the database path and port are not hard-coded.
- **Persistent storage** – data lives in a volume, so it survives container restarts.
- **Health checks** – `/health` lets a load balancer or platform know the service is alive.
- **Stateless web tier** – the app runs under Gunicorn with multiple workers and can be scaled horizontally (move to a managed database for multiple instances).

## Project structure

```
cloud-notes-app/
├── app/
│   ├── __init__.py        # Flask app factory, routes, DB setup
│   ├── templates/
│   │   └── index.html     # Web UI
│   └── static/
│       └── style.css
├── tests/
│   └── test_app.py        # pytest suite
├── wsgi.py                # Entry point for Gunicorn
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── .gitignore
```

## API

| Method | Path                 | Description            |
|--------|----------------------|------------------------|
| GET    | `/health`            | Health check           |
| GET    | `/`                  | Web UI                 |
| GET    | `/api/notes`         | List notes             |
| POST   | `/api/notes`         | Create note (JSON)     |
| DELETE | `/api/notes/<id>`    | Delete note            |

Example:

```bash
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "First cloud note", "body": "Hello from a container"}'
```

## Run locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                           # run tests
python wsgi.py                   # open http://localhost:8000
```

## Run with Docker

```bash
docker compose up --build        # open http://localhost:8000
```

Or without Compose:

```bash
docker build -t cloud-notes .
docker run -p 8000:8000 -v notes-data:/data cloud-notes
```

## Deploy to the cloud

The same image works on most platforms. Common options:

- **Render / Railway / Fly.io** – connect the Git repo; the Dockerfile is detected automatically. Set `PORT` if the platform requires it and attach a persistent volume at `/data`.
- **Google Cloud Run** – `gcloud run deploy cloud-notes --source .` (use a Cloud Storage–backed or Cloud SQL database for durable data, because Cloud Run instances are ephemeral).
- **AWS** – push the image to ECR and run it on App Runner or ECS Fargate; for persistence use EFS or RDS.

Push the image to a registry first if your platform needs one:

```bash
docker build -t <registry>/cloud-notes:1.0 .
docker push <registry>/cloud-notes:1.0
```

## Configuration

| Variable        | Default              | Purpose                        |
|-----------------|----------------------|--------------------------------|
| `DATABASE_PATH` | `instance/notes.db`  | Path to the SQLite file        |
| `PORT`          | `8000`               | Port Gunicorn listens on       |

## Next steps to extend the project

- Swap SQLite for PostgreSQL (e.g. Amazon RDS or Cloud SQL) so multiple instances can share data.
- Add user accounts with Flask-Login.
- Add CI with GitHub Actions: run `pytest`, build the image, and push it on each release.
