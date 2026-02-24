# Triple-Extraktion Pipeline – Docker

Die Pipeline extrahiert Entitäten, Prädikate und Triples aus historischen Briefen (XML/TEI) mithilfe verschiedener KI-APIs und speichert die Ergebnisse als JSON und interaktive HTML-Graphen.

---

## Docker installieren

### Windows

1. **Systemvoraussetzungen prüfen**: Windows 10 (Version 2004+) oder Windows 11, aktiviertes WSL 2
2. **WSL 2 aktivieren** (falls noch nicht geschehen):
   ```powershell
   # PowerShell als Administrator öffnen
   wsl --install
   # Neustart erforderlich
   ```
3. **Docker Desktop herunterladen und installieren**:
   → [Docker Desktop für Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
4. Nach der Installation Docker Desktop starten – das Docker-Wal-Symbol erscheint in der Taskleiste
5. **Prüfen** (in PowerShell oder CMD):
   ```powershell
   docker --version
   docker compose version
   ```

> **Hinweis für Windows-Nutzer**: `run.sh` ist ein Bash-Skript. Es läuft in:
> - **WSL 2** (empfohlen): Terminal öffnen → `wsl` → ins Projektverzeichnis wechseln → `./run.sh`
> - **Git Bash**: Rechtsklick im Projektordner → „Git Bash Here" → `./run.sh`
>
> Alternativ können die Docker-Befehle direkt in PowerShell ausgeführt werden (siehe [Ohne run.sh](#ohne-runsh)).

### macOS

1. **Docker Desktop herunterladen und installieren**:
   → [Docker Desktop für Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
   - Apple Silicon (M1/M2/M3/M4): „Apple Chip" wählen
   - Intel: „Intel Chip" wählen
2. Docker Desktop starten (Wal-Symbol in der Menüleiste)
3. **Prüfen**:
   ```bash
   docker --version
   docker compose version
   ```

### Linux (Ubuntu/Debian)

```bash
# Docker Engine installieren (offizielle Anleitung)
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Ohne sudo nutzen
sudo usermod -aG docker $USER
newgrp docker

# Prüfen
docker --version
docker compose version
```

Für andere Distributionen: [Docker Engine – Unterstützte Plattformen](https://docs.docker.com/engine/install/)

---

## Voraussetzungen

- Docker (inkl. Docker Compose) – siehe oben
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
cp .env.example .env
```

`.env` (im Projekt-Root) öffnen und die gewünschten Keys eintragen, z. B.:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

Die Keys werden automatisch in die `config.yaml` eingesetzt – dort stehen keine Secrets mehr.

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
├── .env.example            # Vorlage für .env (API-Keys)
├── .env                    # API-Keys (nicht eingecheckt!)
├── docker/
│   ├── Dockerfile          # Image-Definition
│   └── docker-compose.yml  # Service-Konfiguration
├── pipeline/
│   ├── analyze/            # Eingabe-XMLs (hier eigene Daten ablegen)
│   ├── output_json/        # JSON-Ergebnisse
│   ├── csv/                # CSV-Exporte
│   ├── logs/               # Verarbeitungs-Logs
│   └── config.yaml         # Konfiguration (ohne Keys, im Repo)
└── run.sh                  # Wrapper-Skript
```

---

## Hinweise

- `.env` enthält API-Keys und ist in `.gitignore` eingetragen – diese Datei niemals einchecken.
- `pipeline/config.yaml` enthält keine Secrets mehr und ist im Repo versioniert.
- Die Volumes in `docker-compose.yml` sorgen dafür, dass Ergebnisse direkt auf dem Host landen, auch wenn der Container danach gelöscht wird.
- Nach Änderungen am Code muss das Image neu gebaut werden: `docker build -f docker/Dockerfile -t triple-pipeline .`

---

## Ohne run.sh

Falls `run.sh` nicht verfügbar ist (z. B. PowerShell unter Windows ohne WSL), können die Docker-Befehle direkt ausgeführt werden:

```powershell
# Image bauen (einmalig, vom Projekt-Root)
docker build -f docker/Dockerfile -t triple-pipeline .

# Pipeline starten (interaktiv)
docker compose -f docker/docker-compose.yml run --rm pipeline

# Mit Parametern
docker compose -f docker/docker-compose.yml run --rm pipeline --profile anthropic --model claude-haiku-4-5 --limit 5
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `docker: command not found` | Docker ist nicht installiert oder nicht im PATH – siehe [Docker installieren](#docker-installieren) |
| `permission denied` bei `docker` (Linux) | `sudo usermod -aG docker $USER` ausführen, dann neu einloggen |
| `error during connect` (Windows) | Docker Desktop starten – das Wal-Symbol muss in der Taskleiste sichtbar sein |
| `run.sh: Permission denied` | `chmod +x run.sh` ausführen |
| `run.sh` startet nicht (Windows) | WSL oder Git Bash verwenden, oder Befehle direkt in PowerShell ausführen (siehe oben) |
| `no matching manifest for windows/amd64` | In Docker Desktop: Settings → General → „Use WSL 2 based engine" aktivieren |
| Container startet, aber keine API-Antworten | API-Key in `.env` prüfen – ist er eingetragen und nicht auskommentiert? |
| Ergebnisse erscheinen nicht auf dem Host | Prüfen, ob `pipeline/output_json/` existiert (`mkdir -p pipeline/output_json`) |
