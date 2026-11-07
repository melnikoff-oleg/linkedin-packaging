#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python_command="${LINKEDIN_PACK_PYTHON:-python3}"
if ! command -v "$python_command" >/dev/null 2>&1; then
  echo "Python 3.10 or newer is required. Install it from https://www.python.org/downloads/, reopen your terminal, and run bash setup.sh again." >&2
  exit 1
fi
"$python_command" -c 'import sys; sys.exit("Python 3.10 or newer is required. Set LINKEDIN_PACK_PYTHON to a newer Python executable.") if sys.version_info < (3, 10) else None'
if ! "$python_command" -m venv .venv; then
  echo "Could not create .venv. On Linux, install the Python venv package (often python3-venv), then rerun setup." >&2
  exit 1
fi
.venv/bin/python -m pip install -e .
if ! .venv/bin/python -m playwright install chromium; then
  echo "Chromium installation failed. Check your network, then rerun bash setup.sh." >&2
  exit 1
fi
if ! .venv/bin/python -c 'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); b.close(); p.stop()'; then
  echo "Chromium could not launch. On Linux run: .venv/bin/python -m playwright install-deps chromium" >&2
  echo "Then rerun bash setup.sh. Existing .env values will be preserved." >&2
  exit 1
fi
if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
fi
chmod +x package.sh
echo "Setup complete. Open .env in a text editor and add your own KIE_AI_API_KEY."
echo "Also add APIFY_API_KEY for --linkedin, or FIRECRAWL_API_KEY for --website."
echo "Then run the example command in README.md. Generation uses paid provider credits."
