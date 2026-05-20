#!/usr/bin/env bash
# ============================================================
# Setup: .env-Datei anlegen (einmalig vor dem ersten Start)
# ============================================================
# Verwendung: bash setup.sh
# ============================================================

set -euo pipefail

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

echo ""
echo "=== Triple-Extraktion Pipeline – Ersteinrichtung ==="
echo ""

# Prüfen ob .env.example vorhanden
if [[ ! -f "$ENV_EXAMPLE" ]]; then
    echo "FEHLER: $ENV_EXAMPLE nicht gefunden."
    echo "Bitte im Projektverzeichnis ausführen: bash setup.sh"
    exit 1
fi

# .env anlegen falls nicht vorhanden
if [[ -f "$ENV_FILE" ]]; then
    echo "✓  .env existiert bereits – überspringe."
else
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "✓  .env wurde aus .env.example erstellt."
fi

echo ""
echo "──────────────────────────────────────────────────────"
echo "NÄCHSTER SCHRITT:"
echo "  Öffne die Datei .env und trage deinen API-Key ein,"
echo "  z. B.:"
echo ""
echo "  ANTHROPIC_API_KEY=sk-ant-..."
echo "  # oder OPENAI_API_KEY=sk-..."
echo ""
echo "Danach startest du die Pipeline mit:"
echo "  docker compose run --rm pipeline"
echo "  (oder über Docker Desktop → compose.yaml öffnen → Run)"
echo "──────────────────────────────────────────────────────"
echo ""
