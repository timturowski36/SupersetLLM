FROM apache/superset:latest

USER root

# System-Abhängigkeiten installieren
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# psycopg2-binary direkt im venv site-packages installieren
RUN pip3 install --target=/app/.venv/lib/python3.10/site-packages --no-cache-dir psycopg2-binary

USER superset

EXPOSE 8088