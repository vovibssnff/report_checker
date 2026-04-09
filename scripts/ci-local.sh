#!/usr/bin/env bash
# Run CI pipeline locally: lint, security checks, tests, image build, image scan.
# No image push or deploy.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
FRONTEND="$REPO_ROOT/frontend"
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

ensure_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo -e "${RED}Missing required command: $1${NC}" >&2
    exit 1
  fi
}

# Use backend venv if present
if [ -d "$BACKEND/.venv" ]; then
  echo -e "${YELLOW}Using $BACKEND/.venv${NC}"
  export PATH="$BACKEND/.venv/bin:$PATH"
fi

# ─── Tool availability checks ────────────────────────────────────────
ensure_cmd python3
ensure_cmd pip
ensure_cmd npm
ensure_cmd docker

# ─── Backend lint (same as CI: backend dev deps, run from repo root) ─
run "Lint" "Install backend dev deps" pip install -e "$BACKEND/[dev]" -q
run "Lint" "Ruff check" ruff check backend/
run "Lint" "Ruff format" ruff format --check backend/
run "Lint" "Mypy" mypy backend/app/ --ignore-missing-imports

# ─── Frontend lint + dependency audit ────────────────────────────────
run "Frontend Lint" "Install frontend deps" bash -c "cd \"$FRONTEND\" && npm ci"
run "Frontend Lint" "ESLint" bash -c "cd \"$FRONTEND\" && npm run lint"
run "Frontend Security" "NPM audit (high+)" bash -c "cd \"$FRONTEND\" && npm audit --audit-level=high"

# ─── SAST (bandit + semgrep, like CI) ────────────────────────────────
run "SAST" "Install bandit + semgrep" pip install bandit semgrep -q
run "SAST" "Bandit" bandit -r backend/app/ -ll
run "SAST" "Semgrep" semgrep --config auto backend/app/ frontend/src/ --error

# ─── Test ─────────────────────────────────────────────────────────────
run "Test" "Install pytest-cov" pip install pytest-cov -q
run "Test" "Pytest with coverage threshold" bash -c "cd \"$BACKEND\" && pytest tests/ -v --tb=short -x --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=75"

# ─── Build (no login/push) ────────────────────────────────────────────
IMAGE_TAG="${IMAGE_TAG:-local}"
run "Build" "Docker build backend" docker build --target final -t "report-checker-backend:${IMAGE_TAG}" backend/
run "Build" "Docker build frontend" docker build --target runtime -t "report-checker-frontend:${IMAGE_TAG}" frontend/

# ─── Container security scan (Trivy) ─────────────────────────────────
if ! command -v trivy >/dev/null 2>&1; then
  echo -e "\n${YELLOW}[Container Security]${NC} Trivy not found, using Docker image fallback"
  TRIVY_CMD=(docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:canary image)
else
  TRIVY_CMD=(trivy image)
fi

run "Container Security" "Scan backend image (CRITICAL,HIGH)" "${TRIVY_CMD[@]}" --format table --ignore-unfixed --vuln-type os,library --severity CRITICAL,HIGH --exit-code 1 "report-checker-backend:${IMAGE_TAG}"
run "Container Security" "Scan frontend image (CRITICAL,HIGH)" "${TRIVY_CMD[@]}" --format table --ignore-unfixed --vuln-type os,library --severity CRITICAL,HIGH --exit-code 1 "report-checker-frontend:${IMAGE_TAG}"

echo -e "\n${BOLD}${GREEN}All CI steps passed.${NC}\n"
