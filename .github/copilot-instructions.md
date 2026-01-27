# Copilot Instructions: Triple-Extraktor für frühneuzeitliche Briefe

## Project Overview

KI-gestützte semantische Triple-Extraktion (SPO: Subjekt-Prädikat-Objekt) aus historischen Briefen. Verarbeitet Textdateien oder Datenbank → LLM-Analyse → strukturiertes JSON mit normalisierten Entitäten.

**Core workflow**: `Datei/DB → Processor → OpenWebUI Client → LLM (Llama 3.3-70B) → JSON → {timestamp}-{source}.json → CSV`

## Architecture

### Component Responsibilities

- **`src/file_client.py`**: Liest `.txt`-Dateien aus `analyze/`, liefert `{id, sourcetext}`
- **`src/db_client.py`**: SQLAlchemy-Client (PostgreSQL/MySQL/SQLite), Query muss `sourcetext` zurückgeben
- **`src/openwebui_client.py`**: LLM-API-Wrapper mit Retry-Logik, JSON-Cleanup, Farbausgabe
- **`src/processor.py`**: Orchestriert Pipeline, generiert Timestamp-Dateinamen, Granularität-Handling
- **`src/csv_exporter.py`**: Exportiert Triples mit aufgelösten Entity-Labels
- **Entry points**: `src/main.py` (Verarbeitung), `src/export_csv.py` (CSV-Export)

### Data Flow

```
File/DB → {id, sourcetext}
  ↓
Processor → OpenWebUI Client (build_payload mit Granularität + Entity-Typen)
  ↓
LLM → JSON (entities, praedikate, triples)
  ↓
JSON-Cleanup (strip markdown) + Validierung (required_keys)
  ↓
Save to {YYYYMMDD-HHMMSS}-{source}.json mit quelle.original_text
  ↓
CSV-Exporter → triples.csv (one row per triple, labels aufgelöst)
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

**Skip-existing** (`--skip-existing`): Timestamp-Naming verhindert Kollisionen
**Update-metadata** (`--update-metadata`): Aktualisiert `quelle.original_text` ohne LLM

### 4. Configuration System (`config.yaml`)

**Kritische Constraints**:
- `database.query` MUSS `id` und `sourcetext` zurückgeben (mit `AS`)
- `extraction.default_granularity`: 1-5 (Default: 3)
- `extraction.entity_types`: Liste erlaubter Typen
- `files.input_dir`: Verzeichnis für Textdateien (default: `analyze`)
- `api.base_url` + `api.endpoint` = LLM-API-URL

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
| Einzelnen Brief verarbeiten | `python src/main.py --source file --filename name.txt --granularity 3` |
| Alle Briefe (Batch) | `python src/main.py --source file` |
| Datenbank-Modus | `python src/main.py --source db --granularity 4` |
| CSV exportieren | `python src/export_csv.py --output csv/triples.csv` |
| Test single record | Nutze `--filename` für File-Mode oder `LIMIT 1` in DB-Query |

## Project Conventions

- **Encoding**: UTF-8 (frühneuzeitliche Texte)
- **Terminal output**: ANSI color codes (Colors class)
- **Logging**: Dual output → `logs/processing.log` + stdout
- **File naming**: `{YYYYMMDD-HHMMSS}-{source}.json`
- **Path handling**: `pathlib.Path` für Cross-Platform
- **Config security**: `config.yaml` in `.gitignore`
