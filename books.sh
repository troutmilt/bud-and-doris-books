#!/usr/bin/env bash
# Open the Bud and Doris Farms books in Fava.
#   ./books.sh        pull the latest from GitHub, check the books, open Fava
# Press Ctrl+C in this terminal to stop Fava.
set -euo pipefail

# Always work from the repo folder, wherever this is run from.
cd "$(dirname "$(readlink -f "$0")")"
PORT=5000
URL="http://127.0.0.1:$PORT"

echo "== Getting the latest entries from GitHub"
git pull --ff-only || echo "!! git pull failed; showing the books as they are on this computer."

if [ ! -x .venv/bin/fava ]; then
  echo "== Setting up Python tools (first run only)"
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

echo "== Checking that the books balance"
if ! .venv/bin/bean-check main.beancount; then
  echo "!! The books have errors (listed above). Fava will show them too."
fi

if curl -s -o /dev/null "$URL" 2>/dev/null; then
  echo "== Fava is already running; opening it"
  xdg-open "$URL" >/dev/null 2>&1 || echo "Open $URL in your browser."
  exit 0
fi

echo "== Starting Fava at $URL (Ctrl+C to stop)"
( sleep 2; xdg-open "$URL" >/dev/null 2>&1 || true ) &
exec .venv/bin/fava --port "$PORT" main.beancount
