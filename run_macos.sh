#!/usr/bin/env bash
set -euo pipefail

if [ ! -d .venv ]; then
  echo "Virtual environment not found. Run ./setup_macos.sh first."
  exit 1
fi

source .venv/bin/activate
python -m streamlit run app.py
