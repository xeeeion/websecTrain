FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    ENABLE_HSTS=1 \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data && chown -R app:app /app

USER app

EXPOSE 8080
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8080\")}/healthz', timeout=3).read()" || exit 1

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} app:app"]
