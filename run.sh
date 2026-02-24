#!/usr/bin/env bash
# ============================================================
# run.sh – Wrapper-Skript für die Triple-Extraktion Pipeline
# ============================================================
# Nutzung:
#   ./run.sh                       # Interaktiver Modus
#   ./run.sh --profile anthropic --model claude-haiku-4-5 --limit 5
#   ./run.sh --beispieldaten       # Beispieldaten nach analyze/ kopieren
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${SCRIPT_DIR}/docker"
PIPELINE_DIR="${SCRIPT_DIR}/pipeline"

# --- Farben ---
BOLD='\033[1m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
RESET='\033[0m'

info()  { echo -e "${GREEN}[INFO]${RESET}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error() { echo -e "${RED}[ERROR]${RESET} $*" >&2; }

# --- Verzeichnisse sicherstellen ---
ensure_dirs() {
    mkdir -p "${PIPELINE_DIR}/analyze"
    mkdir -p "${PIPELINE_DIR}/output_json"
    mkdir -p "${PIPELINE_DIR}/csv"
    mkdir -p "${PIPELINE_DIR}/logs"
}

# --- Beispieldaten kopieren ---
copy_beispieldaten() {
    local src="${SCRIPT_DIR}/data/uebung_1"
    local dest="${PIPELINE_DIR}/analyze"

    if [[ ! -d "$src" ]]; then
        error "Beispieldaten nicht gefunden unter: $src"
        exit 1
    fi

    info "Kopiere Beispieldaten nach ${dest}/ ..."
    cp -r "${src}"/dataset_* "${dest}/"
    info "Fertig. $(find "${dest}" -name '*.xml' | wc -l) XML-Dateien bereit."
}

# --- Config prüfen ---
check_config() {
    if [[ ! -f "${PIPELINE_DIR}/config.yaml" ]]; then
        warn "Keine config.yaml gefunden."
        info "Erstelle config.yaml aus Vorlage ..."
        cp "${PIPELINE_DIR}/config.example.yaml" "${PIPELINE_DIR}/config.yaml"
        warn "Bitte API-Keys in pipeline/config.yaml eintragen!"
        warn "Alternativ: docker/.env verwenden (siehe docker/.env.example)"
    fi
}

# --- .env prüfen ---
check_env() {
    if [[ ! -f "${DOCKER_DIR}/.env" ]]; then
        warn "Keine docker/.env gefunden – verwende nur config.yaml."
        info "Tipp: cp docker/.env.example docker/.env und Keys eintragen."
        # Leere .env anlegen, damit docker compose nicht warnt
        touch "${DOCKER_DIR}/.env"
    fi
}

# --- Hauptlogik ---
main() {
    # Sonderbehandlung: --beispieldaten
    if [[ "${1:-}" == "--beispieldaten" ]]; then
        ensure_dirs
        copy_beispieldaten
        exit 0
    fi

    ensure_dirs
    check_config
    check_env

    info "Starte Triple-Extraktion Pipeline (Docker) ..."
    echo ""

    docker compose -f "${DOCKER_DIR}/docker-compose.yml" \
        run --rm pipeline "$@"
}

main "$@"
