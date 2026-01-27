# Triple-Extraktor für frühneuzeitliche Briefe

KI-gestützte semantische Triple-Extraktion (Subjekt-Prädikat-Objekt) aus historischen Briefen.

## Schnellstart

```bash
# Installation
pip install -r requirements.txt

# Konfiguration
cp config.example.yaml config.yaml
# Bearbeite config.yaml: API-URL, Model

# Brief verarbeiten
python src/main.py --source file --filename jean-paul-1.txt --granularity 3

# CSV exportieren
python src/export_csv.py
```

## Workflow

`Textdatei/DB → LLM-Analyse → JSON mit normalisierten Entitäten/Prädikaten → CSV`

## Abstraktionslevel

| Level | Beschreibung | Triples |
|-------|--------------|---------|
| 1 | Kernaussage | 1-2 |
| 2 | + Hauptthemen | 3-5 |
| 3 | + Nebenthemen & Argumente (Standard) | 6-12 |
| 4 | + Alle Erwähnungen | 12-25 |
| 5 | + Implizite Aussagen | 25+ |

## CLI-Optionen

```bash
python src/main.py --source {file,db} --filename TEXT --granularity {1-5}
python src/export_csv.py --output csv/triples.csv
```

## JSON-Schema

```json
{
  "entities": {
    "E1": {"label": "Jean Paul", "typ": "Person"}
  },
  "praedikate": {
    "P1": {"label": "bittet um", "normalisiert_von": ["bittet gehorsamst um"]}
  },
  "triples": [
    {"subjekt": "E1", "praedikat": "P1", "objekt": "E2"}
  ]
}
```

Vollständige Dokumentation: Siehe `.github/copilot-instructions.md`
