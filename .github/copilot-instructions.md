# Copilot Instructions: Concept-Vergleich

## Project Overview

AI-powered semantic concept extractor for bilingual numismatic (coin) iconographic descriptions. Processes database records → LLM analysis → structured JSON with concept matching and similarity scoring.

**Core workflow**: `DB → Processor → OpenWebUI Client → LLM (Llama 3.3-70B) → JSON validation → {id}.json → CSV export`

## Architecture

### Component Responsibilities

- **`src/db_client.py`**: SQLAlchemy client supporting PostgreSQL/MySQL/SQLite, executes custom query from config
- **`src/openwebui_client.py`**: LLM API wrapper with retry logic, JSON cleanup, colored terminal output, API call counter
- **`src/processor.py`**: Orchestrates pipeline with 3 modes: standard/skip-existing/update-metadata
- **`src/csv_exporter.py`**: Flattens JSON vergleich arrays → CSV rows
- **Entry points**: `src/main.py` (processing), `src/export_csv.py` (CSV export)

### Data Flow

```
DB query (id, field1, field2)
  ↓
Processor checks skip_existing flag → skips if {id}.json exists
  ↓
OpenWebUI Client builds payload with system_prompt + user descriptions
  ↓
LLM returns JSON (with retry on failure)
  ↓
JSON cleanup: strip markdown fences (```json), validate required_keys
  ↓
Save to output_json/{id}.json with meta.original_texts
  ↓
CSVExporter collects all JSONs → csv/vergleiche.csv
```

## Critical Patterns

### 1. LLM Prompt Contract (prompt.txt)

The system's correctness depends entirely on `prompt.txt` adherence:

**Non-negotiable rules**:
- LLM must output **only** pure JSON (first char `{`, last char `}`, no markdown fences)
- Concepts = `Subject + Action/Attribute/Position` (never isolated words like "nach rechts")
- Synonyms ("Perlkreis" = "border of dots") → `similarity=100`, each concept matched **once only**
- Critical parameters (left/right, upper/lower, hand position) → always `abweichung=true` if different
- 1:1 matching: Each DE concept maps to exactly one EN concept, no reuse after synonym match

**Similarity scoring**:
- 100 = fully equivalent (includes synonyms)
- 95-99 = practically identical
- 70-94 = significantly similar
- <70 = partial/low similarity

**Example valid concept**: "Anchialos nach rechts" ✓ (subject + position)  
**Invalid**: "nach rechts" ✗ (missing subject)

### 2. JSON Schema Contract

Validated via `processing.required_keys` in config (default: `["konzepte", "vergleich"]`):

```json
{
  "originaleingabe": { "de": "...", "en": "..." },
  "konzepte": { "de": [...], "en": [...] },
  "vergleich": [
    {
      "konzept_de": "Subjekt mit Attribut",
      "konzept_en": "Subject with attribute",
      "similarity": 0-100,
      "abweichung": true/false,
      "beschreibung": "nur wenn abweichung=true"
    }
  ],
  "meta": {
    "source_id": 123,
    "timestamp": "2025-12-17T10:30:00",
    "model": "llama-3.3-70b-instruct",
    "original_texts": { "de": "...", "en": "..." }
  }
}
```

**Key relationships**:
- `konzepte` lists must align 1:1 in `vergleich` array
- `abweichung=false` requires `similarity ≥ 95` AND no critical parameter differences
- `beschreibung` field only populated when `abweichung=true`

### 3. Processing Modes (--flags)

**Standard** (no flags): Process all DB records, call LLM for each
```bash
python src/main.py  # or: cd src && python main.py
```

**Skip-existing** (`--skip-existing`): Resume interrupted runs, skip IDs with existing JSON files
```bash
python src/main.py --skip-existing
```
Use when: Connection dropped, batch interrupted, only processing new DB records

**Update-metadata** (`--update-metadata`): Backfill `meta.original_texts` without LLM calls
```bash
python src/main.py --update-metadata
```
Use when: DB texts updated, JSONs exist but lack `original_texts`, no API quota consumption needed

### 4. Configuration System (config.yaml)

**Critical constraints**:
- `database.query` MUST return columns aliased as `id`, `field1`, `field2`
- `api.languages` maps field names to ISO codes (e.g., `field1: "de"`) → used in prompt and JSON keys
- `processing.required_keys` MUST match prompt.txt schema (default: `["konzepte", "vergleich"]`)
- `api.base_url` + `api.endpoint` = full LLM API URL
- `api.model` must match OpenWebUI/Ollama model name exactly

**Never commit `config.yaml`** (use `config.example.yaml` as template, contains sensitive API keys)

Example query requirement:
```sql
SELECT id, design_de AS field1, design_en AS field2
FROM cn_data.data_designs
```

### 5. Error Handling & Retry Logic

**OpenWebUI Client retry mechanism**:
1. Attempts API call (timeout: `api.timeout_seconds`)
2. On failure: exponential backoff for `max_retries` attempts with `retry_delay_seconds` base delay
3. JSON cleanup: strips markdown code fences (`^```json\n` and `\n```$`)
4. Validates `required_keys` presence in parsed JSON
5. Logs failures with colored output (RED=fail, YELLOW=retry, GREEN=success)

**Validation failures** (processor.py):
- Missing required keys → error logged, processing continues to next record
- Invalid JSON → retry or skip after max attempts

### 6. CSV Export

Run after batch processing to generate flat CSV:
```bash
python src/export_csv.py --output csv/vergleiche.csv
```

**Output structure**: One row per `vergleich` entry:
- `id`, `original_field1`, `original_field2` (from `meta.original_texts`)
- `konzept_field1`, `konzept_field2`, `similarity`, `abweichung`, `beschreibung`

## Development Workflows

### Modifying JSON Schema

1. **Update `prompt.txt` first** (LLM instructions define contract)
2. Update `config.yaml` → `processing.required_keys` (add/remove top-level keys)
3. Adjust validation in `processor.py` → `_validate_json_result()` if adding complex validation
4. Update CSV exporter (`csv_exporter.py`) if adding exportable fields to `vergleich`

### Adding Language Support

1. Update `config.yaml` → `api.languages` (e.g., `field3: "bg"`)
2. Modify `prompt.txt` to reference new language in user prompt template
3. Update database query to include new field: `SELECT id, field1, field2, field3 AS field3`
4. Test with `LIMIT 1` in query before full batch

### Changing LLM Provider/Model

1. Update `config.yaml`:
   - `api.base_url`: New provider URL
   - `api.endpoint`: Provider-specific endpoint (e.g., `/v1/chat/completions`)
   - `api.model`: Exact model name
   - `api.api_key`: Authentication token
2. Test payload format compatibility in `openwebui_client.py` → `build_payload()`
3. Verify JSON cleanup logic handles new provider's response format

### Testing Changes

**No automated tests exist.** Manual testing pattern:

```bash
# Test single record (modify config.yaml query)
# Add "LIMIT 1" to database.query
python src/main.py --config config.yaml

# Verify JSON structure
cat output_json/1.json | python -m json.tool

# Test CSV export
python src/export_csv.py --output test.csv
head test.csv
```

**Check API connectivity**: Examine `logs/processing.log` for colored status messages

## Common Operations

| Task | Command |
|------|---------|
| Resume interrupted batch | `python src/main.py --skip-existing` |
| Backfill metadata only | `python src/main.py --update-metadata` |
| Change LLM model | Edit `config.yaml` → `api.model` |
| Export to CSV | `python src/export_csv.py` |
| Test single record | Add `LIMIT 1` to `database.query` in config |
| View API call count | Check terminal output (colored counter) |

## Dependencies & Installation

```bash
pip install -r requirements.txt
```

**Key dependencies**:
- `sqlalchemy`: Database abstraction (dialect-agnostic)
- `requests`: HTTP client for LLM API
- `pyyaml`: Configuration parsing
- `psycopg2-binary` / `pymysql`: DB drivers (install based on DB type)

## Project Conventions

- **Encoding**: UTF-8 everywhere (handles Greek, Cyrillic numismatic text)
- **Terminal output**: ANSI color codes via `Colors` class (GREEN/YELLOW/RED/BLUE/CYAN)
- **Logging**: Dual output to `logs/processing.log` + stdout
- **File naming**: JSON files named `{record_id}.json` (e.g., `1.json`, `1234.json`)
- **Path handling**: `pathlib.Path` for cross-platform compatibility
- **Config security**: `config.yaml` in `.gitignore`, use `config.example.yaml` as template
