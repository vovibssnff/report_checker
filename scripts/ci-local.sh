#!/usr/bin/env bash
# Run CI pipeline locally: lint, SAST, test, Docker build.
# No image push or deploy.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
cd "$REPO_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

run() {
  echo -e "\n${BOLD}${YELLOW}[$1]${NC} $2"
  if ! ( shift 2; "$@" ); then
    echo -e "${RED}Failed: $1${NC}" >&2
    return 1
  fi
  echo -e "${GREEN}✓ $1${NC}"
}

# Use backend venv if present
if [ -d "$BACKEND/.venv" ]; then
  echo -e "${YELLOW}Using $BACKEND/.venv${NC}"
  export PATH="$BACKEND/.venv/bin:$PATH"
fi

# ─── Lint (same as CI: backend dev deps, run from repo root) ───────
run "Lint" "Install backend dev deps" pip install -e "$BACKEND/[dev]" -q
run "Lint" "Ruff check" ruff check backend/
run "Lint" "Ruff format" ruff format --check backend/
run "Lint" "Mypy" mypy backend/app/ --ignore-missing-imports

# ─── SAST (bandit + semgrep, like CI) ──────────────────────────────
run "SAST" "Install bandit + semgrep" pip install bandit semgrep -q
run "SAST" "Bandit" bandit -r backend/app/ -ll
run "SAST" "Semgrep" semgrep --config auto backend/app/ --error

# ─── Test ─────────────────────────────────────────────────────────
run "Test" "Pytest" bash -c "cd $BACKEND && pytest tests/ -v --tb=short -x"

# ─── Build (no login/push) ──────────────────────────────────────────
IMAGE_TAG="${IMAGE_TAG:-local}"
run "Build" "Docker build backend" docker build -t "report-checker-backend:${IMAGE_TAG}" backend/

echo -e "\n${BOLD}${GREEN}All CI steps passed.${NC}\n"
