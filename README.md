# Triple-Extraktor für frühneuzeitliche Briefe

KI-gestützte semantische Triple-Extraktion (Subjekt–Prädikat–Objekt) aus historischen Briefen im TEI-XML-Format.

Das Tool analysiert Briefkorpora mithilfe großer Sprachmodelle (LLMs) und extrahiert strukturierte Wissensgraphen: Wer schreibt wem, worüber, mit welchen Bezügen – als maschinenlesbare Triples.

---

## Features

- **6 API-Provider**: ChatAI (AcademicCloud), Google Gemini, OpenAI, Anthropic, Mistral, OpenRouter
- **TEI-XML-Optimierung**: 72–87 % Token-Ersparnis durch intelligente Metadaten-Extraktion
- **Batch-Verarbeitung**: Rekursive Verzeichnisse, Skip-Funktion, Limit-Parameter
- **Interaktive Visualisierung**: Plotly-HTML-Graphen + PlantUML-Diagramme
- **CSV-Export**: Für tabellarische Weiterverarbeitung in Excel, R, pandas etc.
- **Themenanalyse**: Automatische Aggregation häufiger Prädikate und Entitäten
- **Docker-Support**: Reproduzierbare Umgebung für alle Plattformen (Win/Mac/Linux)
- **Jupyter-Notebooks**: Interaktive Variante für Google Colab und JupyterHub

---

## Schnellstart

### Voraussetzungen

- Python 3.10+ **oder** Docker
- API-Key für mindestens einen Provider (siehe [Unterstützte Provider](#unterstützte-provider))

### Installation (lokal)

```bash
git clone <repo-url>
cd triple-colab

# Abhängigkeiten installieren
pip install -r pipeline/requirements.txt

# API-Keys konfigurieren
cp .env.example .env
# .env öffnen und Keys eintragen
```

### Installation (Docker)

```bash
git clone <repo-url>
cd triple-colab

# API-Keys konfigurieren
cp .env.example .env
# .env öffnen und Keys eintragen

# Starten
./run.sh
```

### Erste Schritte

```bash
# Beispieldaten laden
./run.sh --beispieldaten

# Pipeline starten (interaktive Provider-/Modellauswahl)
./run.sh

# Oder direkt mit Parametern
./run.sh --profile anthropic --model claude-haiku-4-5 --limit 5
```

---

## Unterstützte Provider

| Profil | Anbieter | Modelle (Auswahl) |
|--------|----------|-------------------|
| `chatai` | [AcademicCloud](https://chat-ai.academiccloud.de/) | Llama 3.3 70B, Sauerkraut 70B, Mistral Large, Qwen3 |
| `gemini` | [Google Gemini](https://aistudio.google.com/) | Gemini 3 Pro/Flash, 2.5 Flash/Lite |
| `openai` | [OpenAI](https://platform.openai.com/) | GPT-5.2, GPT-4o-mini |
| `anthropic` | [Anthropic](https://console.anthropic.com/) | Claude Sonnet 4.6, Claude Haiku 4.5 |
| `mistral` | [Mistral AI](https://console.mistral.ai/) | Mistral Large/Medium/Small |
| `openrouter` | [OpenRouter](https://openrouter.ai/) | Multi-Provider (Claude, Gemini, Llama, GPT u. a.) |

---

## Konfiguration

| Datei | Zweck | Im Repo? |
|-------|-------|----------|
| `.env` | API-Keys (Secrets) | Nein |
| `.env.example` | Vorlage für `.env` | Ja |
| `pipeline/config.yaml` | Alle Einstellungen (Provider, Modelle, Extraction-Parameter) | Ja |

API-Keys werden über Umgebungsvariablen in `.env` gesetzt und zur Laufzeit automatisch in die Konfiguration eingesetzt. `config.yaml` enthält keine Secrets.

---

## Projektstruktur

```
triple-colab/
├── README.md                  # ← Du bist hier
├── .env.example               # Vorlage für API-Keys
├── run.sh                     # Wrapper-Skript (lokal + Docker)
│
├── pipeline/                  # Kernkomponente: Extraktions-Pipeline
│   ├── README.md              # Technische Dokumentation
│   ├── config.yaml            # Konfiguration (ohne Keys)
│   ├── prompt.txt             # LLM-Instruktionen
│   ├── requirements.txt       # Python-Abhängigkeiten
│   ├── src/                   # Python-Quellcode
│   ├── analyze/               # Input: TEI-XML/TXT-Dateien
│   ├── output_json/           # Output: JSON-Ergebnisse
│   ├── csv/                   # CSV-Exporte
│   └── logs/                  # Verarbeitungs-Logs
│
├── docker/                    # Docker-Umgebung
│   ├── README.md              # Docker-Anleitung
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── notebooks/                 # Interaktive Jupyter-Notebooks
│   ├── README.md              # Notebook-Anleitung
│   ├── Triple_Extraktion_Colab.ipynb
│   └── Triple_Extraktion_jupyterhub.ipynb
│
├── data/                      # Beispieldaten für Übungen
│   ├── uebung_1/             # Einzelbriefe (Schnellstart)
│   └── uebung_2/             # 10er-Sets (Batch-Verarbeitung)
│
└── tests/                     # Tests und Experimente
```

---

## Komponenten

### Pipeline (`pipeline/`)

Die Kernkomponente: Liest TEI-XML-Briefe, optimiert den Token-Verbrauch, sendet den Text an ein LLM und speichert die extrahierten Triples als JSON. Unterstützt auch Datenbank-Input (SQLAlchemy).

→ Details: [pipeline/README.md](pipeline/README.md)

### Docker (`docker/`)

Reproduzierbare Umgebung auf Basis von `python:3.10-slim`. Volumes für Quellcode, Daten und Ergebnisse werden automatisch gemountet. Das Wrapper-Skript `run.sh` startet die Pipeline über Docker Compose.

→ Details: [docker/README.md](docker/README.md)

### Jupyter-Notebooks (`notebooks/`)

Interaktive Variante für Google Colab und JupyterHub. Ideal für Workshops, Lehre und Einzelanalysen ohne lokale Installation.

→ Details: [notebooks/README.md](notebooks/README.md)

### Beispieldaten (`data/`)

Drei Briefkorpora für Tests und Workshops:
- **Jean Paul** – Briefe aus dem VI. Abt. (Bayerische Akademie)
- **Schleiermacher** – Korrespondenz 1809 (Schleiermacher-Edition)
- **Wilhelm von Humboldt** – Briefe 1787–1794 (Humboldt-Edition)

---

## Workflow

```
TEI-XML/TXT → Token-Optimierung → LLM-Analyse → JSON → HTML-Graph / CSV
```

1. **Input**: TEI-XML-Briefe in `pipeline/analyze/` ablegen
2. **Optimierung**: Metadaten (Absender, Empfänger, Datum) werden extrahiert, XML-Overhead entfernt
3. **LLM-Analyse**: Der optimierte Text wird mit dem Prompt an das gewählte Modell gesendet
4. **Output**: Strukturierte JSON-Dateien mit Entitäten, Prädikaten und Triples
5. **Visualisierung**: Interaktive HTML-Graphen (Plotly/NetworkX) pro Brief
6. **Export**: Aggregierter CSV-Export für tabellarische Auswertung

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `docker: command not found` | Docker installieren – siehe [docker/README.md](docker/README.md#docker-installieren) |
| `run.sh: Permission denied` | `chmod +x run.sh` |
| `run.sh` startet nicht (Windows) | WSL oder Git Bash verwenden, oder Docker-Befehle direkt in PowerShell – siehe [docker/README.md](docker/README.md#ohne-runsh) |
| `Konfigurationsdatei nicht gefunden` | `git pull` – `config.yaml` ist jetzt im Repo |
| API-Fehler / leere Antworten | `.env` prüfen – Key eingetragen und nicht auskommentiert? |
| `ModuleNotFoundError: dotenv` | `pip install python-dotenv` oder Docker verwenden |

---

## Lizenz

<!-- TODO: Lizenz ergänzen -->

---

## Zitation

<!-- TODO: Zitationshinweis ergänzen (z. B. für DHd-Konferenz) -->
