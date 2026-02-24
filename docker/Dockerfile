# ============================================================
# Triple-Extraktion Pipeline – Docker Image
# ============================================================
# Build-Context ist das Projekt-Root (..),
# daher: docker build -f docker/Dockerfile ..
# ============================================================

FROM python:3.10-slim AS base

# System-Pakete für psycopg2 / lxml
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------- Dependencies ----------
COPY pipeline/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Pipeline-Code ----------
COPY pipeline/src/          ./src/
COPY pipeline/prompt.txt    ./prompt.txt
COPY pipeline/tags_ignore.txt ./tags_ignore.txt
COPY pipeline/config.example.yaml ./config.example.yaml

# ---------- Beispieldaten (Übung 1) ----------
COPY data/uebung_1/dataset_JeanPaul/       ./analyze/beispieldaten/dataset_JeanPaul/
COPY data/uebung_1/dataset_Schleiermacher/  ./analyze/beispieldaten/dataset_Schleiermacher/
COPY data/uebung_1/dataset_WvH/            ./analyze/beispieldaten/dataset_WvH/

# ---------- Verzeichnisse anlegen ----------
RUN mkdir -p output_json csv logs analyze

# ---------- Laufzeit ----------
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "src/main.py"]
# Standard-Argumente (können per docker run überschrieben werden)
CMD ["--source", "file"]
