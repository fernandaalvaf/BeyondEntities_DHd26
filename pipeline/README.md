# Triple-Extraktor für frühneuzeitliche Briefe

**Version 1.0.2.0** · KI-gestützte semantische Triple-Extraktion (Subjekt-Prädikat-Objekt) aus historischen Briefen im TEI-XML-Format.

## Features

- **Multi-API-Support**: ChatAI (AcademicCloud), Google Gemini, OpenAI, Anthropic, Mistral, OpenRouter
- **TEI-XML-Optimierung**: 72-87% Token-Ersparnis durch intelligente Metadaten-Extraktion
- **Rekursive Verarbeitung**: Unterstützt Unterverzeichnisse mit Strukturerhalt
- **Batch-Verarbeitung**: Skip-Funktion, Limit-Parameter, Fortsetzen unterbrochener Runs
- **Interaktive Visualisierung**: PlantUML-Diagramme + Plotly HTML-Graphen

### Feature-Details

#### Multi-API-Support
Unterstützt sechs Anbieter über ein Profil-System in `config.yaml`:

| Profil | Anbieter | Verfügbare Modelle |
|--------|----------|--------------------|
| `chatai` | AcademicCloud | `llama-3.3-70b-instruct`, `llama-3.1-sauerkrautlm-70b-instruct`, `mistral-large-3-675b-instruct-2512`, `qwen3-30b-a3b-instruct-2507` |
| `gemini` | Google | `gemini-3-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` |
| `openai` | OpenAI | `gpt-5.2-2025-12-11`, `gpt-4o-mini` |
| `anthropic` | Anthropic | `claude-sonnet-4-6`, `claude-haiku-4-5` |
| `mistral` | Mistral AI | `mistral-large-2512`, `mistral-medium-2508`, `mistral-small-2506` |
| `openrouter` | OpenRouter | Multi-Provider: Claude, Gemini, Llama, GPT u. a. |

Auswahl erfolgt interaktiv beim Start oder via `--profile`-Flag.

#### TEI-XML-Optimierung
Reduziert Token-Verbrauch durch intelligente Extraktion:
```
Vorher:  <TEI xmlns="..."><teiHeader>...</teiHeader><text>...</text></TEI>  (15.000 Zeichen)
Nachher: TITEL: Brief an X | ABSENDER: Y | DATUM: Z | BRIEFTEXT: ...       (4.000 Zeichen)
```
Extrahiert automatisch: TITEL, ABSENDER, EMPFÄNGER, ORT, DATUM, BRIEFTEXT

#### Skip-Funktion & Batch-Verarbeitung
Ermöglicht unterbrechbare und fortsetzbare Verarbeitungen:
```bash
# Verarbeite 50 Dateien, unterbreche mit Ctrl+C
python src/main.py --source file --limit 50

# Später fortsetzen - bereits verarbeitete werden übersprungen
python src/main.py --source file --skip-existing --limit 50
```
Erkennt bereits verarbeitete Dateien via Muster `*_{originalname}.json`

#### Exponential Backoff (Retry-Strategie)
Bei API-Fehlern (Timeout, Rate-Limit) wird die Wartezeit verdoppelt:
```
1. Versuch → Fehler → Warte 3s
2. Versuch → Fehler → Warte 6s  
3. Versuch → Fehler → Warte 12s → Aufgeben
```
Verhindert Überlastung bei überlasteten APIs und Rate-Limiting.

## Schnellstart

```bash
# Installation (im Projekt-Root)
pip install -r pipeline/requirements.txt

# API-Keys konfigurieren (im Projekt-Root)
cp .env.example .env
# .env öffnen und Keys eintragen

# Einzelnen Brief verarbeiten
python src/main.py --source file --filename brief.xml --granularity 3

# Batch: Nächste 10 unverarbeitete Dateien
python src/main.py --source file --skip-existing --limit 10

# Nicht-TEI-XML unoptimiert verarbeiten
python src/main.py --source file --filename custom.xml --raw-xml

# CSV exportieren
python src/export_csv.py --output csv/triples.csv
```

## Workflow

```
TEI-XML/TXT → Token-Optimierung → LLM-Analyse → JSON → PlantUML + HTML-Graph → CSV
```

**Verzeichnisstruktur wird gespiegelt:**
```
analyze/Schleiermacher/brief.xml → output_json/Schleiermacher/20260130-143022_brief.json
```

## Abstraktionslevel (Granularität)

| Level | Beschreibung | Triples |
|-------|--------------|---------|
| 1 | Kernaussage | 1-2 |
| 2 | + Hauptthemen | 3-5 |
| 3 | + Nebenthemen & Argumente (Standard) | 6-12 |
| 4 | + Alle Erwähnungen | 12-25 |
| 5 | + Implizite Aussagen | 25+ |

## CLI-Optionen

```bash
# Hauptverarbeitung
python src/main.py --source {file,db}     # Datenquelle
                   --filename NAME.xml     # Einzelne Datei (optional)
                   --granularity {1-5}     # Abstraktionslevel
                   --skip-existing         # Überspringe bereits verarbeitete
                   --limit N               # Max. N Dateien verarbeiten
                   --no-graphs             # Keine HTML-Graphen generieren
                   --raw-xml               # XML unverarbeitet übergeben (ohne TEI-Optimierung)
                   --update-metadata       # Nur Metadaten aktualisieren

# CSV-Export
python src/export_csv.py --output csv/triples.csv

# Themenanalyse (neue Funktion!)
python src/analyze_themes.py                           # Analysiere alle JSON-Dateien
python src/analyze_themes.py --top 30                  # Top 30 statt Top 20
python src/analyze_themes.py --output csv/themes.csv   # Mit CSV-Export
```

## API-Profile (config.yaml)

Die API-Keys stehen **nicht** in `config.yaml`, sondern in der `.env`-Datei im Projekt-Root.
Siehe `.env.example` für die verfügbaren Variablen.

```yaml
api:
  profiles:
    chatai:
      api_provider: "openai"
      base_url: "https://chat-ai.academiccloud.de"
      model: "llama-3.3-70b-instruct"
    gemini:
      api_provider: "gemini"
      base_url: "https://generativelanguage.googleapis.com"
      model: "gemini-3-pro-preview"
    openai:
      api_provider: "openai"
      base_url: "https://api.openai.com"
      model: "gpt-5.2-2025-12-11"
    anthropic:
      api_provider: "anthropic"
      base_url: "https://api.anthropic.com"
      model: "claude-sonnet-4-6"
    mistral:
      api_provider: "mistral"
      base_url: "https://api.mistral.ai"
      model: "mistral-large-2512"
    openrouter:
      api_provider: "openrouter"
      base_url: "https://openrouter.ai/api"
      model: "anthropic/claude-sonnet-4-6"
```

**Temperatur**: Standard 0.3 (konsistent, aber leicht variabel). Einstellbar pro Profil von 0.0–2.0.

## JSON-Output-Schema

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
  ],
  "quelle": {
    "datei": "brief",
    "verarbeitet": "2026-01-30T14:30:22",
    "zeichenanzahl": 2847,
    "original_text": "..."
  }
}
```

## Projektstruktur

```
pipeline/
├── analyze/              # Input: TEI-XML/TXT-Dateien (mit Unterverzeichnissen)
├── output_json/          # Output: JSON + PlantUML + HTML-Graphen
├── csv/                  # Exportierte CSV-Dateien
├── logs/                 # Verarbeitungs-Logs
├── src/
│   ├── main.py           # CLI-Einstiegspunkt
│   ├── processor.py      # Verarbeitungs-Pipeline
│   ├── file_client.py    # TEI-XML-Parser mit Token-Optimierung
│   ├── db_client.py      # Datenbank-Client (SQLAlchemy)
│   ├── openwebui_client.py  # Multi-API-Client
│   ├── csv_exporter.py   # CSV-Export mit Label-Auflösung
│   ├── analyze_themes.py # Themenanalyse
│   ├── export_csv.py     # CSV-Export-CLI
│   └── config_loader.py  # YAML-Konfiguration + .env-Laden
├── config.yaml           # Konfiguration (im Repo, ohne Keys)
├── prompt.txt            # LLM-Instruktionen
├── tags_ignore.txt       # XML-Tags, die bei Optimierung entfernt werden
└── requirements.txt      # Python-Abhängigkeiten
```

Vollständige Entwickler-Dokumentation: Siehe `.github/copilot-instructions.md`
