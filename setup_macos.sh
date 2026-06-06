#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.11 or 3.12, then run this script again."
  exit 1
fi

python3 - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit("SourceLens requires Python 3.11 or newer. Install Python 3.11 or 3.12 and try again.")

print(f"Using Python {sys.version.split()[0]}")
PY

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Add your OpenAI API key before building an index."
else
  echo "Existing .env file kept unchanged."
fi

echo
echo "Setup complete."
echo "Next steps:"
echo "  1. Open .env and replace the placeholder OPENAI_API_KEY value."
echo "  2. Run: ./run_macos.sh"
