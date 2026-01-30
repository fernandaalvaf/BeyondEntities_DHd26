# Copilot Instructions: Triple-Extraktor für frühneuzeitliche Briefe

## Project Overview

KI-gestützte semantische Triple-Extraktion (SPO: Subjekt-Prädikat-Objekt) aus historischen Briefen im TEI-XML-Format. Verarbeitet Textdateien oder Datenbank → LLM-Analyse → strukturiertes JSON mit normalisierten Entitäten.

**Core workflow**: `TEI-XML/TXT → Token-Optimierung → Processor → Multi-API-Client → LLM → JSON → {timestamp}_{source}.json → CSV`

## Architecture

### Component Responsibilities

- **`src/file_client.py`**: Liest `.txt`/`.xml`-Dateien rekursiv aus `analyze/`, optimiert TEI-XML (72-87% Token-Ersparnis), liefert `{id, sourcetext, source_path, relative_path}`
- **`src/db_client.py`**: SQLAlchemy-Client (PostgreSQL/MySQL/SQLite), Query muss `id` und `sourcetext` zurückgeben
- **`src/openwebui_client.py`**: Multi-API-Wrapper (OpenAI + Gemini) mit Retry-Logik, Exponential Backoff, JSON-Cleanup, Farbausgabe
- **`src/processor.py`**: Orchestriert Pipeline, Skip-Logik, Limit-Handling, Graph-Generierung (optional)
- **`src/csv_exporter.py`**: Exportiert Triples rekursiv mit aufgelösten Entity-Labels
- **Entry points**: `src/main.py` (Verarbeitung), `src/export_csv.py` (CSV-Export)

### Data Flow

```
File/DB → {id, sourcetext, relative_path}
  ↓
TEI-XML → _extract_tei_optimized() → TITEL, ABSENDER, ORT, DATUM, EMPFÄNGER, BRIEFTEXT
  ↓
Processor → Skip-Check → Limit-Check → OpenWebUI Client (build_payload)
  ↓
LLM (OpenAI/Gemini) → JSON (entities, praedikate, triples)
  ↓
JSON-Cleanup + Validierung (required_keys)
  ↓
Save to {subdir}/{YYYYMMDD-HHMMSS}_{source}.json + .puml + .html
  ↓
CSV-Exporter (rglob) → triples.csv (one row per triple, labels aufgelöst)
```

## Critical Patterns

### 1. LLM Prompt Contract (`prompt.txt`)

**Abstraktionslevel 1-5**:
- 1 = Kernaussage (1-2 Triples)
- 3 = Standard (6-12 Triples)
- 5 = Vollständig (25+ Triples)

**Entitäten-Normalisierung**:
- "Ew. Hochehrwürden" → "Erhard Friedrich Vogel"
- "ich" → Absendername aus Brief
- Moderne Rechtschreibung: "Göthe" → "Goethe"

**Prädikate-Normalisierung**:
- "bittet gehorsamst um" → "bittet um"
- `normalisiert_von`: Liste der Original-Formulierungen

**Entity-Typen**: Person, Ort, Werk, Institution, Ereignis, Konzept, Zeitpunkt, Sonstiges

### 2. JSON-Schema Contract

Validated via `processing.required_keys` (default: `["entities", "praedikate", "triples"]`):

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
  "parameter": {
    "granularitaet": 3,
    "anzahl_triples": 8
  },
  "quelle": {
    "datei": "jean-paul-1",
    "verarbeitet": "2026-01-27T14:30:22",
    "ausfuehrungszeit_sekunden": 12.45,
    "original_text": "..."
  }
}
```

### 3. Processing Modes

**Standard** (kein Flag): Verarbeite alle Records, rufe LLM für jeden auf
```bash
python src/main.py --source file
```

**Skip-existing** (`--skip-existing`): Überspringe bereits verarbeitete Dateien
- Prüft via Pattern `*_{originalname}.json` im entsprechenden Unterverzeichnis
- Ideal für Fortsetzen unterbrochener Batch-Verarbeitungen

**Limit** (`--limit N`): Verarbeite maximal N Dateien
```bash
python src/main.py --source file --skip-existing --limit 10
```

**No-graphs** (`--no-graphs`): Deaktiviert HTML-Graph-Generierung
- Spart Speicherplatz und Zeit bei großen Batches
- PlantUML-Diagramme werden weiterhin generiert

**Update-metadata** (`--update-metadata`): Aktualisiert `quelle.original_text` ohne LLM

### 4. Configuration System (`config.yaml`)

**Kritische Constraints**:
- `api.active_profile`: Wähle API-Profil (`chatai`, `telota`, `gemini`)
- `api.profiles.*.api_provider`: `openai` oder `gemini`
- `api.profiles.*.exponential_backoff`: Exponentielles Backoff aktivieren (default: true)
- `database.query` MUSS `id` und `sourcetext` zurückgeben (mit `AS`)
- `extraction.default_granularity`: 1-5 (Default: 3)
- `extraction.entity_types`: Liste erlaubter Typen
- `files.input_dir`: Verzeichnis für Textdateien (default: `analyze`)

**Beispiel API-Profile**:
```yaml
api:
  active_profile: "gemini"
  profiles:
    gemini:
      api_provider: "gemini"
      base_url: "https://generativelanguage.googleapis.com"
      endpoint: "/v1beta/models/gemini-2.5-flash-lite:generateContent"
      api_key: "YOUR_API_KEY"
      exponential_backoff: true
```

**Beispiel DB-Query**:
```sql
SELECT id, brieftext AS sourcetext FROM briefe LIMIT 10
```

### 5. Error Handling & Retry Logic

OpenWebUI-Client:
1. API-Aufruf (timeout: `api.timeout_seconds`)
2. Exponential backoff bei Fehler (`max_retries`, `retry_delay_seconds`)
3. JSON-Cleanup: Entferne `^```json\n` und `\n```$`
4. Validiere `required_keys`
5. Farbige Ausgabe: RED=Fehler, YELLOW=Retry, GREEN=Erfolg

### 6. CSV Export

```bash
python src/export_csv.py --output csv/triples.csv
```

**Output**: Eine Zeile pro Triple:
- `datei`, `source_id`, `verarbeitet`
- `subjekt_id`, `subjekt`, `subjekt_typ`
- `praedikat_id`, `praedikat`, `praedikat_normalisiert_von`
- `objekt_id`, `objekt`, `objekt_typ`
- `original_text`

## Development Workflows

### Modifying JSON Schema

1. Update `prompt.txt` (LLM-Anweisungen)
2. Update `config.yaml` → `processing.required_keys`
3. Adjust `processor.py` → `_validate_json_result()` if complex validation
4. Update `csv_exporter.py` for new exportable fields

### Changing Granularity Logic

1. Update `prompt.txt` → Abstraktionslevel-Beschreibungen
2. Test mit verschiedenen Levels:
```bash
python src/main.py --source file --filename jean-paul-1.txt --granularity 1
python src/main.py --source file --filename jean-paul-1.txt --granularity 5
```

### Adding Entity Types

1. Update `config.yaml` → `extraction.entity_types`
2. Update `prompt.txt` → Entitätstypen-Liste
3. Test Extraktion

## Common Operations

| Task | Command |
|------|---------|
| Einzelnen Brief verarbeiten | `python src/main.py --source file --filename name.xml --granularity 3` |
| Alle Briefe (Batch) | `python src/main.py --source file` |
| Nächste 10 unverarbeitete | `python src/main.py --source file --skip-existing --limit 10` |
| Batch ohne HTML-Graphen | `python src/main.py --source file --skip-existing --no-graphs` |
| Datenbank-Modus | `python src/main.py --source db --granularity 4` |
| CSV exportieren | `python src/export_csv.py --output csv/triples.csv` |
| Test single record | Nutze `--filename` für File-Mode oder `LIMIT 1` in DB-Query |

## Project Conventions

- **Encoding**: UTF-8 (frühneuzeitliche Texte)
- **Terminal output**: ANSI color codes (Colors class in openwebui_client.py)
- **Logging**: Dual output → `logs/processing.log` + stdout
- **File naming**: `{YYYYMMDD-HHMMSS}_{source}.json` (Unterverzeichnisse gespiegelt)
- **Path handling**: `pathlib.Path` für Cross-Platform
- **Config security**: `config.yaml` in `.gitignore`
- **API-Retry**: Exponential Backoff (3s, 6s, 12s bei max_retries=3)
