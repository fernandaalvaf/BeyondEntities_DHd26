# Triple-Extraktion Pipeline – Docker

Die Pipeline extrahiert Entitäten, Prädikate und Triples aus historischen Briefen (XML/TEI) mithilfe verschiedener KI-APIs und speichert die Ergebnisse als JSON und interaktive HTML-Graphen.

---

## Voraussetzungen

- [Docker](https://docs.docker.com/get-docker/) (inkl. Docker Compose)
- API-Key für mindestens einen der unterstützten Provider

---

## Schnellstart

### 1. Image bauen

```bash
# Vom Projekt-Root aus:
docker build -f docker/Dockerfile -t triple-pipeline .
```

### 2. API-Keys eintragen

```bash
cp docker/.env.example docker/.env
```

`docker/.env` öffnen und die gewünschten Keys eintragen, z. B.:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

Alternativ können Keys auch direkt in `pipeline/config.yaml` stehen – die Umgebungsvariablen aus `.env` haben aber Vorrang und sind sicherer (`.env` wird nicht eingecheckt).

### 3. Pipeline starten

```bash
./run.sh
```

Das interaktive Menü fragt nacheinander:
- welchen **Provider** (ChatAI, Gemini, OpenAI, Anthropic, Mistral, OpenRouter)
- welches **Modell**
- ein optionales **Limit** (Anzahl Dateien, Enter = alle)

---

## Eigene Daten verarbeiten

XML- oder TXT-Dateien in `pipeline/analyze/` legen (Unterverzeichnisse sind erlaubt):

```bash
mkdir -p pipeline/analyze/MeinKorpus
cp meine_briefe/*.xml pipeline/analyze/MeinKorpus/
./run.sh
```

Die Ergebnisse erscheinen in `pipeline/output_json/` – gespiegelte Verzeichnisstruktur, je eine JSON-Datei pro Brief.

### Beispieldaten einrichten

```bash
./run.sh --beispieldaten
```

Kopiert die Beispiel-XMLs aus `data/uebung_1/` nach `pipeline/analyze/`.

---

## Nicht-interaktiver Modus (z. B. für Skripte)

```bash
./run.sh --profile anthropic --model claude-haiku-4-5 --limit 10
```

| Flag | Werte | Bedeutung |
|------|-------|-----------|
| `--profile` | `chatai` · `gemini` · `openai` · `anthropic` · `mistral` · `openrouter` | Provider wählen |
| `--model` | Modellname aus dem Profil | Modell wählen |
| `--limit N` | Ganzzahl | Nur N Dateien verarbeiten |
| `--source` | `file` (Standard) · `db` | Datenquelle |
| `--skip-existing` | – | Bereits verarbeitete Dateien überspringen |
| `--no-graphs` | – | Keine HTML-Graphen erzeugen |

---

## Verzeichnisstruktur

```
triple-colab/
├── docker/
│   ├── Dockerfile          # Image-Definition
│   ├── docker-compose.yml  # Service-Konfiguration
│   ├── .env                # API-Keys (nicht eingecheckt!)
│   └── .env.example        # Vorlage für .env
├── pipeline/
│   ├── analyze/            # Eingabe-XMLs (hier eigene Daten ablegen)
│   ├── output_json/        # JSON-Ergebnisse
│   ├── csv/                # CSV-Exporte
│   ├── logs/               # Verarbeitungs-Logs
│   ├── config.yaml         # Konfiguration mit API-Keys (nicht eingecheckt!)
│   └── config.example.yaml # Vorlage für config.yaml
└── run.sh                  # Wrapper-Skript
```

---

## Hinweise

- `docker/.env` und `pipeline/config.yaml` enthalten API-Keys und sind in `.gitignore` eingetragen – diese Dateien niemals einchecken.
- Die Volumes in `docker-compose.yml` sorgen dafür, dass Ergebnisse direkt auf dem Host landen, auch wenn der Container danach gelöscht wird.
- Nach Änderungen am Code muss das Image neu gebaut werden: `docker build -f docker/Dockerfile -t triple-pipeline .`
