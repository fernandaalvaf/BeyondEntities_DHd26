# Beschreibungsverarbeitung über OpenWebUI

Dieses Projekt lädt Beschreibungen aus einer Datenbank, verarbeitet sie über eine OpenWebUI-API (mit KI-Modellen wie Llama) und speichert die strukturierten JSON-Ergebnisse. Zusätzlich können alle Vergleichsdaten in eine CSV-Datei exportiert werden.

## Features

- ✅ Automatische Verarbeitung von Beschreibungen in zwei Sprachen
- ✅ JSON-Ausgabe mit semantischen Konzepten und Vergleichen
- ✅ Retry-Logik bei API-Fehlern
- ✅ CSV-Export aller Vergleichsdaten
- ✅ Zeitstempel und Ausführungszeit in Metadaten
- ✅ Konfigurierbar über YAML-Datei
- ✅ Farbige Terminal-Ausgabe mit API-Call-Counter

## Projektstruktur

```
project_root/
  config.yaml              # Konfigurationsdatei (wird nicht committet)
  config.example.yaml      # Beispiel-Konfiguration
  prompt.txt               # System-/Instruktionsprompt
  requirements.txt         # Python-Abhängigkeiten
  src/
    __init__.py
    config_loader.py       # YAML-Konfiguration laden
    db_client.py           # Datenbank-Zugriff
    openwebui_client.py    # OpenWebUI-API-Client
    processor.py           # Verarbeitungslogik
    csv_exporter.py        # CSV-Export-Funktionalität
    main.py                # Einstiegspunkt für Verarbeitung
    export_csv.py          # Einstiegspunkt für CSV-Export
  logs/                    # Log-Dateien
  output_json/             # Generierte JSON-Dateien
  csv/                     # Exportierte CSV-Dateien
```

## Installation

1. Python 3.10+ erforderlich

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

## Konfiguration

### 1. `config.yaml` anpassen

Passe die Datenbankverbindung, API-Einstellungen und Verarbeitungsparameter an:

```yaml
database:
  driver: "postgresql"
  host: "localhost"
  port: 5432
  user: "dein_user"
  password: "dein_password"
  name: "deine_datenbank"
  query: |
    SELECT
      id,
      description_column_1 as field1,
      description_column_2 as field2
    FROM descriptions
    WHERE processed = FALSE

api:
  base_url: "http://localhost:11434"
  endpoint: "/api/chat/completions"
  api_key: "your-api-key-here"
  model: "llama-3.3-70b-instruct"
  languages:
    field1: "de"
    field2: "en"
  timeout_seconds: 60
  max_retries: 3
  retry_delay_seconds: 3

processing:
  output_dir: "output_json"
  required_keys:
    - "konzepte"
    - "vergleich"
```

**Hinweise:**
- **driver**: Unterstützt `postgresql`, `mysql+pymysql`, `sqlite` etc.
- **query**: SQL-Query muss die Felder `id`, `field1`, `field2` zurückgeben (mit AS-Alias)
- **api_key**: API-Schlüssel für die Authentifizierung (optional, falls die API keinen Key benötigt)
- **languages**: ISO-Codes (zweistellig) für field1 und field2 - werden im Prompt an die KI übergeben
- **required_keys**: JSON-Validierung prüft auf diese Top-Level-Keys (muss zum Prompt-Schema passen)

### 2. `prompt.txt` anpassen

Definiere den System-/Instruktionsprompt, der das gewünschte JSON-Schema vorgibt:

```
Du bist ein System, das aus ikonographischen Beschreibungen Konzepte extrahiert und vergleicht.
Liefere ausschließlich gültigen JSON mit folgendem Schema:

{
  "original": { "de": "...", "en": "..." },
  "konzepte": { "de": [...], "en": [...] },
  "vergleich": [
    {
      "konzept_de": "...",
      "konzept_en": "...",
      "similarity": 0-100,
      "abweichung": true/false,
      "beschreibung": "..."
    }
  ]
}

Gib keine erklärenden Texte aus, nur reinen JSON.
```

**Wichtig:** Die `required_keys` in `config.yaml` müssen mit dem Prompt-Schema übereinstimmen!
  "abweichungen": [...]
}

Gib keine erklärenden Texte aus, nur reinen JSON.
```

## Verwendung

### 1. Beschreibungen verarbeiten (Haupt-Workflow)

**Standard-Ausführung:**

```bash
cd src
python main.py
```

oder vom Projektroot:

```bash
python src/main.py
```

**Mit benutzerdefinierten Pfaden:**

```bash
python src/main.py --config /pfad/zu/config.yaml --prompt /pfad/zu/prompt.txt
```

**Kommandozeilen-Optionen:**

```bash
python src/main.py --help
```

- `--config`: Pfad zur Konfigurationsdatei (Standard: `config.yaml`)
- `--prompt`: Pfad zur Prompt-Datei (Standard: `prompt.txt`)
- `--log-file`: Pfad zur Log-Datei (Standard: `logs/processing.log`)
- `--skip-existing`: Überspringe IDs mit existierenden JSON-Dateien (für inkrementelle Updates)
- `--update-metadata`: Aktualisiere nur Metadaten (original_texts) in existierenden JSON-Dateien ohne API-Aufruf

**Skip-Existing Modus:**

Wenn du die Verarbeitung fortsetzen möchtest ohne bereits verarbeitete IDs erneut zu prozessieren:

```bash
python src/main.py --skip-existing
```

Dies ist nützlich wenn:
- Die Verarbeitung unterbrochen wurde (Strg+C, Verbindungsfehler, etc.)
- Nur neue Datensätze aus der Datenbank verarbeitet werden sollen
- Zeit und API-Kosten gespart werden sollen bei wiederholten Durchläufen

Der Skip-Modus prüft für jede ID ob bereits eine `{id}.json` Datei existiert und überspringt diese dann.

**Update-Metadata Modus:**

Wenn du die Originaltexte nachträglich in bereits verarbeitete JSON-Dateien eintragen möchtest:

```bash
python src/main.py --update-metadata
```

Dies ist nützlich wenn:
- JSON-Dateien bereits existieren, aber noch keine `original_texts` in den Metadaten haben
- Die Datenbank aktualisiert wurde und du die aktualisierten Texte in die JSONs übernehmen möchtest
- Keine API-Aufrufe gemacht werden sollen (schneller und kostenfrei)

Der Update-Modus:
- Liest alle Datensätze aus der Datenbank
- Lädt nur existierende JSON-Dateien
- Aktualisiert/ergänzt das Feld `meta.original_texts` mit den aktuellen DB-Werten
- Überspringt IDs ohne existierende JSON-Datei

### 2. CSV-Export der Vergleichsdaten

Nach der Verarbeitung können alle Vergleichsergebnisse in eine CSV-Datei exportiert werden:

**Standard-Export:**

```bash
python src/export_csv.py
```

Dies liest automatisch:
- JSON-Dateien aus dem konfigurierten `output_dir` (z.B. `output_json/`)
- Sprachen aus der `config.yaml`
- Exportiert nach `csv/vergleiche.csv`

**Mit benutzerdefinierten Optionen:**

```bash
# Eigener Output-Pfad
python src/export_csv.py --output meine_vergleiche.csv

# Eigenes JSON-Verzeichnis
python src/export_csv.py --input-dir /pfad/zu/json --output export.csv

# Andere Config-Datei
python src/export_csv.py --config andere_config.yaml
```

**CSV-Format:**

Die CSV-Datei enthält folgende Spalten (Semikolon-getrennt):

```csv
id;original_de;original_en;konzept_de;konzept_en;similarity;abweichung;beschreibung
1;Aphrodite stehend vor...;Aphrodite standing before...;Aphrodite stehend;Aphrodite standing;95;false;
1;Aphrodite stehend vor...;Aphrodite standing before...;Eros fliegend;Eros flying;100;false;
2;Zeus thronend...;null;Zeus thronend;null;0;true;Nur in DE vorhanden
```

Die Spaltennamen passen sich automatisch an die konfigurierten Sprachen an (z.B. `original_de`, `konzept_de` bei de/en).

**Hinweis:** Die `original_*` Spalten enthalten die vollständigen Originaltexte aus der Datenbank und werden seit der neuesten Version automatisch in den JSON-Metadaten gespeichert.

## Funktionsweise

### Verarbeitungs-Workflow

1. **Datenbankabfrage**: Lädt Datensätze mit `id` und zwei Beschreibungen (field1, field2)
2. **API-Aufruf**: Sendet für jeden Datensatz einen Prompt mit beiden Beschreibungen an OpenWebUI
3. **JSON-Bereinigung**: Entfernt Markdown-Code-Blöcke (```json) aus der KI-Antwort
4. **JSON-Validierung**: Prüft die Antwort auf erwartete Felder (`konzepte`, `vergleich`)
5. **Retry-Logik**: Wiederholt fehlgeschlagene Anfragen bis zu `max_retries`
6. **Speicherung**: Speichert validierte Ergebnisse als `{id}.json` mit Metadaten
7. **CSV-Export**: Optional können alle Vergleiche in eine CSV-Datei exportiert werden

### Workflow-Diagramm

```
Datenbank → Python-Script → OpenWebUI-API → KI-Modell
                                               ↓
                                          JSON-Antwort
                                               ↓
                                     Bereinigung & Validierung
                                               ↓
                                        {id}.json Datei
                                               ↓
                                   CSV-Export (optional)
                                               ↓
                                        vergleiche.csv
```

## Output-Format

### JSON-Dateien

Jede generierte Datei (`{id}.json`) hat folgende Struktur:

```json
{
  "original": {
    "de": "Originalbeschreibung Deutsch",
    "en": "Original description English"
  },
  "konzepte": {
    "de": ["Konzept 1", "Konzept 2"],
    "en": ["Concept 1", "Concept 2"]
  },
  "vergleich": [
    {
      "konzept_de": "Aphrodite stehend",
      "konzept_en": "Aphrodite standing",
      "similarity": 95,
      "abweichung": false,
      "beschreibung": ""
    }
  ],
  "meta": {
    "source_id": 1234,
    "languages": ["de", "en"],
    "original_texts": {
      "de": "Vollständiger Originaltext Deutsch aus der Datenbank",
      "en": "Full original text English from database"
    },
    "execution_date": "2025-12-09T16:45:23.123456",
    "execution_time_seconds": 12.34
  }
}
```

**Metadaten:**
- `source_id`: ID aus der Datenbank
- `languages`: Verwendete Sprachen
- `original_texts`: Originaltexte aus field1/field2 (seit neuster Version)
- `execution_date`: Zeitstempel der Verarbeitung (ISO-Format)
- `execution_time_seconds`: Ausführungszeit in Sekunden

### CSV-Export

Die exportierte CSV-Datei enthält alle Vergleichseinträge aus allen JSON-Dateien in tabellarischer Form. Ideal für:
- Analyse in Excel/LibreOffice
- Import in andere Systeme
- Statistische Auswertungen
- Schnelle Übersicht über Abweichungen

## Logging

- **Konsole**: Live-Output während der Verarbeitung mit farbiger Kennzeichnung
- **Datei**: Vollständiges Log in `logs/processing.log`

Log-Level: INFO (Start/Ende, Erfolg/Fehler pro Datensatz)

### Farbige Terminal-Ausgabe

Die Terminal-Ausgabe nutzt Farben zur besseren Übersichtlichkeit:

- 🟢 **Grün**: Übersprungene Datensätze (wenn `--skip-existing` aktiv)
- 🟡 **Gelb**: API-Aufrufe und -Antworten
- 🔴 **Rot**: Fehler und fehlgeschlagene Versuche
- 🔵 **Blau**: Zusammenfassungen und Statistiken
- 🔷 **Cyan**: Informationsmeldungen und Fortschritt

Zusätzlich wird jeder API-Aufruf mit einer fortlaufenden Nummer markiert: `[API #1]`, `[API #2]`, etc.

## Fehlerbehandlung

- **Netzwerkfehler**: Automatische Wiederholung mit konfigurierbarer Verzögerung
- **Ungültiges JSON**: Markdown-Code-Blöcke werden automatisch entfernt, bei weiterem Fehler: Retry
- **Datenbankfehler**: Aussagekräftige Fehlermeldungen
- **Einzelne Fehler**: Verarbeitung wird fortgesetzt, Fehler werden geloggt
- **CSV-Export**: Fehlende oder ungültige JSON-Dateien werden übersprungen

## Tipps & Best Practices

### Optimale Performance

- **LIMIT in Query**: Teste zuerst mit wenigen Datensätzen (z.B. `LIMIT 5`)
- **Timeout**: Erhöhe `timeout_seconds` bei langsamen Modellen
- **Batch-Verarbeitung**: Für große Datenmengen in mehreren Sessions
- **Zwei Sprachen**: Reduziert Nachdenkzeit der KI erheblich vs. drei Sprachen

### Workflow-Empfehlung

1. Teste mit 1-5 Datensätzen
2. Prüfe JSON-Output auf Korrektheit
3. Exportiere CSV und validiere das Format
4. Bei Bedarf Prompt anpassen
5. Dann vollständige Verarbeitung starten (nutze `--skip-existing` bei Unterbrechungen)

### Inkrementelle Verarbeitung

Bei großen Datenmengen empfiehlt sich folgendes Vorgehen:

1. **Erste Verarbeitung** mit kleinem LIMIT (z.B. 100 Datensätze)
   ```bash
   python src/main.py
   ```

2. **LIMIT erhöhen** in `config.yaml` (z.B. auf 500)

3. **Mit Skip-Modus fortsetzen** (verarbeitet nur neue IDs)
   ```bash
   python src/main.py --skip-existing
   ```

4. **Fehlgeschlagene IDs erneut verarbeiten**: Lösche deren JSON-Dateien und führe erneut mit `--skip-existing` aus

Dies spart API-Kosten und Zeit, da bereits verarbeitete Datensätze nicht erneut an die KI gesendet werden.

### Originaltexte nachtragen

Falls du bereits JSON-Dateien hast, die noch keine `original_texts` in den Metadaten enthalten:

```bash
python src/main.py --update-metadata
```

Dies:
- Liest alle Datensätze aus der Datenbank
- Aktualisiert nur die Metadaten in existierenden JSON-Dateien
- Macht **keine** API-Aufrufe (schnell und kostenfrei)
- Überspringt IDs ohne JSON-Datei

Danach kannst du den CSV-Export neu ausführen, um die vollständigen Originaltexte in den Spalten zu haben.

### CSV-Export nutzen

Der CSV-Export ist ideal für:
- **Schnelle Übersicht** über alle Vergleiche
- **Analyse in Excel/LibreOffice** (Filter, Pivot-Tabellen)
- **Import in andere Systeme** (z.B. Datenbanken)
- **Statistische Auswertungen** (Similarity-Verteilung, Abweichungsrate)

## Anpassungen

### Andere Datenbanken

Für MySQL:
```yaml
database:
  driver: "mysql+pymysql"
  # ... restliche Konfiguration
```

Für SQLite:
```yaml
database:
  driver: "sqlite"
  name: "path/to/database.db"
  # host, port, user, password nicht benötigt
```

### API-Format anpassen

Falls deine OpenWebUI-Installation ein anderes Format erwartet, passe die Methoden in `openwebui_client.py` an:

- `build_payload()`: Request-Struktur
- `_extract_model_output()`: Response-Parsing

## Abhängigkeiten

- **pyyaml**: YAML-Konfiguration
- **sqlalchemy**: Datenbank-Abstraktionsschicht
- **requests**: HTTP-Client für API-Aufrufe
- **psycopg2-binary**: PostgreSQL-Treiber

## Lizenz

[Deine Lizenz hier einfügen]
