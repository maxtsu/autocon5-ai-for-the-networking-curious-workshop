#!/usr/bin/env bash
#
# postCreate.sh — runs once on Codespace first-create.
#
# Responsibilities:
#  1. Wait for Docker daemon (docker-in-docker feature) to be ready
#  2. Load SR Linux image from baked-in tarball
#  3. Load Open WebUI image from baked-in tarball
#  4. Seed .env from .env.example if missing
#  5. Start Open WebUI container
#  6. Print welcome banner

set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Wait for Docker daemon
#
# The docker-in-docker feature starts Docker during Codespace startup, but
# postCreateCommand might fire before the daemon is fully up. Poll briefly.
# ---------------------------------------------------------------------------
echo "==> Waiting for Docker daemon..."
for i in $(seq 1 30); do
    if docker info > /dev/null 2>&1; then
        echo "    Docker is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "    ERROR: Docker daemon not ready after 30 seconds."
        exit 1
    fi
    sleep 1
done

# ---------------------------------------------------------------------------
# 2. Load SR Linux image from baked-in tarball
# ---------------------------------------------------------------------------
SRLINUX_TAR="/opt/images/srlinux.tar"

if [ -f "$SRLINUX_TAR" ]; then
    echo ""
    echo "==> Loading SR Linux image from $SRLINUX_TAR..."
    docker load -i "$SRLINUX_TAR"
    echo ""
    docker images ghcr.io/nokia/srlinux
else
    echo ""
    echo "WARNING: $SRLINUX_TAR not found."
    echo "         Containerlab topology won't deploy without it."
fi

# ---------------------------------------------------------------------------
# 3. Load Open WebUI image from baked-in tarball
# ---------------------------------------------------------------------------
WEBUI_TAR="/opt/images/open-webui.tar"

if [ -f "$WEBUI_TAR" ]; then
    echo ""
    echo "==> Loading Open WebUI image from $WEBUI_TAR..."
    docker load -i "$WEBUI_TAR"
    echo ""
    docker images ghcr.io/open-webui/open-webui
else
    echo ""
    echo "WARNING: $WEBUI_TAR not found."
    echo "         GUI chat interface won't be available."
fi

# ---------------------------------------------------------------------------
# 4. Seed .env from .env.example if missing
# ---------------------------------------------------------------------------
echo ""
echo "==> Setting up .env..."
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "    Created .env from .env.example."
    echo "    Edit .env and add your OPENAI_API_KEY before running OpenAI labs."
elif [ -f .env ]; then
    echo "    .env already exists; leaving it alone."
else
    echo "    No .env.example found; skipping."
fi

# ---------------------------------------------------------------------------
# 5. Start Open WebUI container
#
# Wrapped in `if ! ...` so a failure here doesn't halt postCreate.sh — the
# workshop must remain usable even if the GUI hiccups. Attendees can always
# run scripts/start-webui.sh manually later.
# ---------------------------------------------------------------------------
echo ""
echo "==> Starting Open WebUI..."
if [ -f scripts/start-webui.sh ]; then
    if ! bash scripts/start-webui.sh; then
        echo "    WARNING: Open WebUI failed to start — continuing without GUI."
        echo "             Try 'bash scripts/start-webui.sh' manually later."
    fi
else
    echo "    scripts/start-webui.sh not found; skipping GUI startup."
fi

# ---------------------------------------------------------------------------
# 6. Welcome banner
# ---------------------------------------------------------------------------
cat <<'EOF'

==================================================
  AutoCon 5 AI Workshop — environment ready!
==================================================

Quick sanity checks:
  ollama --version           # expect 0.23.1
  containerlab version       # expect 0.74.3
  docker images              # SR Linux + Open WebUI should be listed

Open WebUI (chat GUI for Ollama):
  → http://localhost:8080
  → VS Code auto-opens this in the 'Ports' panel preview pane.
  → Models appear once 'ollama serve' is running (covered in Lab 1).

Next steps:
  1. Edit .env to add your OpenAI API key
  2. See README.md for the lab walkthrough order
  3. Workshop FAQ: WORKSHOP_FAQ.md

==================================================

EOF
