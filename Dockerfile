FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/notes.db \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

# Run as a non-root user
RUN useradd --create-home appuser \
    && mkdir -p /data /app/instance \
    && chown -R appuser:appuser /data /app \
    && chmod 777 /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request, sys; port = os.environ.get('PORT', '8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/health').status == 200 else 1)"

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 2 --access-logfile - --error-logfile - wsgi:app"]
