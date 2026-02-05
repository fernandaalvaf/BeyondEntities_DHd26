# Triple-Extraktor für frühneuzeitliche Briefe

KI-gestützte semantische Triple-Extraktion (Subjekt-Prädikat-Objekt) aus historischen Briefen im TEI-XML-Format.

## Features

- **Multi-API-Support**: OpenAI-kompatible APIs (ChatAI) + Google Gemini
- **TEI-XML-Optimierung**: 72-87% Token-Ersparnis durch intelligente Metadaten-Extraktion
- **Rekursive Verarbeitung**: Unterstützt Unterverzeichnisse mit Strukturerhalt
- **Batch-Verarbeitung**: Skip-Funktion, Limit-Parameter, Fortsetzen unterbrochener Runs
- **Interaktive Visualisierung**: PlantUML-Diagramme + Plotly HTML-Graphen

### Feature-Details

#### Multi-API-Support
Unterstützt verschiedene LLM-APIs über ein Profil-System:
- **OpenAI-kompatibel**: ChatAI (academiccloud.de), lokale Ollama-Instanzen
- **Google Gemini**: Native Gemini-API mit systemInstruction-Support
- Einfacher Wechsel via `active_profile` in config.yaml

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
# Installation
pip install -r requirements.txt

# Konfiguration
cp config.example.yaml config.yaml
# Bearbeite config.yaml: API-Profil wählen (chatai/gemini), API-Key setzen

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

```yaml
api:
  active_profile: "chatai"  # Wähle: chatai, gemini
  
  profiles:
    chatai:
      api_provider: "openai"
      base_url: "https://chat-ai.academiccloud.de"
      model: "llama-3.3-70b-instruct"
    gemini:
      api_provider: "gemini"
      base_url: "https://generativelanguage.googleapis.com"
      model: "gemini-2.5-flash-lite"
```

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
├── analyze/              # Input: TEI-XML/TXT-Dateien (mit Unterverzeichnissen)
├── output_json/          # Output: JSON + PlantUML + HTML-Graphen
├── csv/                  # Exportierte CSV-Dateien
├── logs/                 # Verarbeitungs-Logs
├── src/
│   ├── main.py           # CLI-Einstiegspunkt
│   ├── processor.py      # Verarbeitungs-Pipeline
│   ├── file_client.py    # TEI-XML-Parser mit Token-Optimierung
│   ├── db_client.py      # Datenbank-Client (SQLAlchemy)
│   ├── openwebui_client.py  # Multi-API-Client (OpenAI/Gemini)
│   ├── csv_exporter.py   # CSV-Export mit Label-Auflösung
│   └── config_loader.py  # YAML-Konfiguration
├── config.yaml           # Konfiguration (nicht im Repo)
├── config.example.yaml   # Beispiel-Konfiguration
└── prompt.txt            # LLM-Instruktionen
```

Vollständige Entwickler-Dokumentation: Siehe `.github/copilot-instructions.md`
