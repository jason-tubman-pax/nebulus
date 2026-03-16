#!/usr/bin/env bash
# Seed the history DB with fake data for local dev. Run from repo root.
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
if [[ ! -d .venv ]]; then
  echo "Run ./scripts/dev.sh first to create the venv, or: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
.venv/bin/python scripts/seed_fake_data.py "$@"
