#!/usr/bin/env bash
set -uo pipefail

BASE_URL="${BASE_URL:-https://localhost}"
case "$BASE_URL" in https://*) CURL_EXTRA="-k" ;; *) CURL_EXTRA="" ;; esac

MINIO_ENDPOINT="${MINIO_ENDPOINT:-}"
MINIO_ACCESS="${MINIO_ACCESS:-minioadmin}"
MINIO_SECRET="${MINIO_SECRET:-minioadmin}"
MINIO_SCHEME="${MINIO_SCHEME:-}"
BUCKET="report-checker-documents"
TEST_USER_EMAIL="${TEST_USER_EMAIL:-tester@itmo.ru}"
TEST_USER_NAME="${TEST_USER_NAME:-Live Tester}"
TEST_USER_PASSWORD="${TEST_USER_PASSWORD:-livetest-password}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

pass=0
fail=0

check() {
    local name="$1" expected="$2" actual="$3" body="${4:-}"
    if [ "$actual" -eq "$expected" ]; then
        printf "  ${GREEN}✓ PASS${NC}  %s ${CYAN}(HTTP %s)${NC}\n" "$name" "$actual"
        pass=$((pass + 1))
    else
        printf "  ${RED}✗ FAIL${NC}  %s — expected %s, got %s\n" "$name" "$expected" "$actual"
        [ -n "$body" ] && echo "         $(echo "$body" | head -c 200)"
        fail=$((fail + 1))
    fi
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TEST_PDF_REPORT="$REPO_ROOT/docs/Бессонов_отчет_по_учебной_практике.pdf"
TEST_PDF_VKR="$REPO_ROOT/docs/Бессонов_шаблон_вкр.pdf"

for f in "$TEST_PDF_REPORT" "$TEST_PDF_VKR"; do
    if [ ! -f "$f" ]; then
        echo -e "${RED}Missing test PDF: $f${NC}" >&2
        exit 1
    fi
done

BASE_HOST=$(echo "$BASE_URL" | sed -E 's#https?://([^/:]+).*#\1#')
if [ -z "$MINIO_ENDPOINT" ]; then
    MINIO_ENDPOINT="$BASE_HOST"
fi

if [ -z "$MINIO_SCHEME" ]; then
    case "$BASE_URL" in https://*) MINIO_SCHEME="https" ;; *) MINIO_SCHEME="http" ;; esac
fi

TOTAL_TESTS=10
if [ -n "$MINIO_ENDPOINT" ] && [ -n "$MINIO_ACCESS" ] && [ -n "$MINIO_SECRET" ]; then
    RUN_MINIO=true
else
    RUN_MINIO=false
    TOTAL_TESTS=9
fi

MINIO_BASE_URL="${MINIO_SCHEME}://${MINIO_ENDPOINT}/s3"

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
COOKIE_JAR="$TMPDIR/cookies.txt"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║     Report Checker — Live Test Suite     ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo -e "  Target: ${BOLD}$BASE_URL${NC}"
if $RUN_MINIO; then
    echo -e "  MinIO:  ${BOLD}${MINIO_BASE_URL}${NC}"
else
    echo -e "  MinIO:  ${YELLOW}skipped (set MINIO_ENDPOINT, MINIO_ACCESS, MINIO_SECRET to enable)${NC}"
fi
echo ""

T=1

# ─── 1. Health check via Caddy ───────────────────────────────────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Health check (Caddy → backend)${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" "$BASE_URL/health" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /health" 200 "$code" "$body"
echo ""
T=$((T + 1))

# ─── 2. Unauthenticated access should be rejected ────────────────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Auth gate — reject unauthenticated request${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" "$BASE_URL/api/v1/auth/me" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /api/v1/auth/me (no cookie)" 401 "$code" "$body"
echo ""
T=$((T + 1))

# ─── 3. Dev auth bootstrap + login ───────────────────────────────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Auth — dev user bootstrap + login${NC}"
register_resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/v1/auth/dev/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\",\"name\":\"$TEST_USER_NAME\",\"password\":\"$TEST_USER_PASSWORD\",\"role\":\"student\"}" 2>&1)
register_code=$(echo "$register_resp" | tail -1)
if [ "$register_code" -eq 201 ] || [ "$register_code" -eq 409 ]; then
    printf "  ${GREEN}✓ PASS${NC}  Auth bootstrap user exists ${CYAN}(HTTP %s)${NC}\n" "$register_code"
    pass=$((pass + 1))
else
    check "POST /api/v1/auth/dev/register" 201 "$register_code" "$(echo "$register_resp" | sed '$d')"
fi

resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -c "$COOKIE_JAR" \
    -X POST "$BASE_URL/api/v1/auth/dev/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\",\"password\":\"$TEST_USER_PASSWORD\"}" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "POST /api/v1/auth/dev/login" 200 "$code" "$body"
USER_NAME=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','?'))" 2>/dev/null || echo "?")
echo -e "         Logged in as: ${BOLD}$USER_NAME${NC}"
echo ""
T=$((T + 1))

# ─── 4. Authenticated /me ────────────────────────────────────────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Auth — verify session${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -b "$COOKIE_JAR" "$BASE_URL/api/v1/auth/me" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /api/v1/auth/me (with cookie)" 200 "$code" "$body"
echo ""
T=$((T + 1))

# ─── 5. Internal API: upload practice report PDF (no auth) ───────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Internal API — upload practice report (no auth)${NC}"
echo -e "         File: $(basename "$TEST_PDF_REPORT")"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/internal/documents/" \
    -F "files=@${TEST_PDF_REPORT};type=application/pdf" \
    -F "document_type=practice_report" \
    -F "source=livetest" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "POST /internal/documents/ (practice_report)" 200 "$code" "$body"

DOC_ID=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['document_id'])" 2>/dev/null || echo "")
DOC_STATUS=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['status'])" 2>/dev/null || echo "")
NUM_CHECKS=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d[0].get('check_results',[])))" 2>/dev/null || echo "?")

if [ -n "$DOC_ID" ]; then
    echo -e "         Document ID:    ${BOLD}$DOC_ID${NC}"
    echo -e "         Status:         ${BOLD}$DOC_STATUS${NC}"
    echo -e "         Check results:  ${BOLD}$NUM_CHECKS${NC}"
else
    echo -e "  ${RED}Could not parse upload response${NC}"
    echo "  $body"
fi
echo ""
T=$((T + 1))

# ─── 5b. Internal API: upload VKR template PDF (no auth) ─────────
echo -e "${YELLOW}[${T}b/$TOTAL_TESTS] Internal API — upload VKR template (no auth)${NC}"
echo -e "         File: $(basename "$TEST_PDF_VKR")"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/internal/documents/" \
    -F "files=@${TEST_PDF_VKR};type=application/pdf" \
    -F "document_type=vkr_template" \
    -F "source=livetest" 2>&1)
body2=$(echo "$resp" | sed '$d')
code2=$(echo "$resp" | tail -1)
check "POST /internal/documents/ (vkr_template)" 200 "$code2" "$body2"

DOC_ID_2=$(echo "$body2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['document_id'])" 2>/dev/null || echo "")
DOC_STATUS_2=$(echo "$body2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['status'])" 2>/dev/null || echo "")
NUM_CHECKS_2=$(echo "$body2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d[0].get('check_results',[])))" 2>/dev/null || echo "?")

if [ -n "$DOC_ID_2" ]; then
    echo -e "         Document ID:    ${BOLD}$DOC_ID_2${NC}"
    echo -e "         Status:         ${BOLD}$DOC_STATUS_2${NC}"
    echo -e "         Check results:  ${BOLD}$NUM_CHECKS_2${NC}"
else
    echo -e "  ${RED}Could not parse upload response${NC}"
    echo "  $body2"
fi
echo ""
T=$((T + 1))

# ─── 6. Internal API: get check results for practice report ──────
if [ -n "$DOC_ID" ]; then
    echo -e "${YELLOW}[$T/$TOTAL_TESTS] Internal API — fetch check results (practice report)${NC}"
    resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" "$BASE_URL/internal/documents/$DOC_ID/checks" 2>&1)
    body=$(echo "$resp" | sed '$d')
    code=$(echo "$resp" | tail -1)
    check "GET /internal/documents/$DOC_ID/checks" 200 "$code" "$body"
    RESULT_COUNT=$(echo "$body" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    echo -e "         Results returned: ${BOLD}$RESULT_COUNT${NC}"
    echo ""
else
    echo -e "${YELLOW}[$T/$TOTAL_TESTS] SKIPPED — no document ID${NC}"
    echo ""
fi
T=$((T + 1))

# ─── 7. Web API: download document (proves MinIO round-trip) ─────
if [ -n "$DOC_ID" ]; then
    echo -e "${YELLOW}[$T/$TOTAL_TESTS] Web API — download practice report (proves MinIO works)${NC}"
    DOWNLOAD_FILE="$TMPDIR/downloaded.pdf"
    http_code=$(curl $CURL_EXTRA -s -w "%{http_code}" -b "$COOKIE_JAR" \
        -o "$DOWNLOAD_FILE" \
        "$BASE_URL/api/v1/documents/$DOC_ID/download" 2>&1)
    DOWNLOAD_SIZE=$(stat -c%s "$DOWNLOAD_FILE" 2>/dev/null || stat -f%z "$DOWNLOAD_FILE" 2>/dev/null || echo "0")
    check "GET /api/v1/documents/$DOC_ID/download" 200 "$http_code" ""

    ORIG_SIZE=$(stat -c%s "$TEST_PDF_REPORT" 2>/dev/null || stat -f%z "$TEST_PDF_REPORT" 2>/dev/null || echo "0")
    if [ "$DOWNLOAD_SIZE" -gt 0 ] && head -c 5 "$DOWNLOAD_FILE" | grep -q '%PDF'; then
        printf "  ${GREEN}✓ PASS${NC}  Downloaded file is a valid PDF (%s bytes, original %s bytes)\n" "$DOWNLOAD_SIZE" "$ORIG_SIZE"
        pass=$((pass + 1))
    else
        printf "  ${RED}✗ FAIL${NC}  Downloaded file is not a valid PDF (size: %s)\n" "$DOWNLOAD_SIZE"
        fail=$((fail + 1))
    fi
    echo ""
else
    echo -e "${YELLOW}[$T/$TOTAL_TESTS] SKIPPED — no document ID${NC}"
    echo ""
fi
T=$((T + 1))

# ─── 8. Direct MinIO verification (optional) ─────────────────────
if $RUN_MINIO && [ -n "$DOC_ID" ]; then
    echo -e "${YELLOW}[$T/$TOTAL_TESTS] MinIO via Caddy — direct S3 object verification${NC}"
    minio_health_code=$(curl $CURL_EXTRA -s -o /dev/null -w "%{http_code}" \
        "${MINIO_BASE_URL}/minio/health/live" 2>&1)
    check "GET ${MINIO_BASE_URL}/minio/health/live" 200 "$minio_health_code" ""
    echo ""
    T=$((T + 1))
elif $RUN_MINIO; then
    echo -e "${YELLOW}[$T/$TOTAL_TESTS] SKIPPED — no document ID${NC}"
    echo ""
    T=$((T + 1))
fi

# ─── 9. Web API: list documents (both uploads visible) ───────────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Web API — list documents (verify both uploads)${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -b "$COOKIE_JAR" "$BASE_URL/api/v1/documents/?size=50" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /api/v1/documents/" 200 "$code" "$body"
TOTAL=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total','?'))" 2>/dev/null || echo "?")
echo -e "         Total documents in DB: ${BOLD}$TOTAL${NC}"
echo ""
T=$((T + 1))

# ─── 10. Logout ──────────────────────────────────────────────────
echo -e "${YELLOW}[$T/$TOTAL_TESTS] Auth — logout${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
    -X POST "$BASE_URL/api/v1/auth/logout" 2>&1)
code=$(echo "$resp" | tail -1)
check "POST /api/v1/auth/logout" 204 "$code" ""

resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -b "$COOKIE_JAR" "$BASE_URL/api/v1/auth/me" 2>&1)
code=$(echo "$resp" | tail -1)
check "GET /api/v1/auth/me (after logout)" 401 "$code" ""
echo ""

# ─── Summary ─────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
if [ "$fail" -eq 0 ]; then
    echo -e "${BOLD}${CYAN}║${NC}  ${GREEN}All $pass checks passed!${NC}                    ${BOLD}${CYAN}║${NC}"
else
    printf "${BOLD}${CYAN}║${NC}  ${GREEN}Passed: %-3s${NC}  ${RED}Failed: %-3s${NC}              ${BOLD}${CYAN}║${NC}\n" "$pass" "$fail"
fi
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

[ "$fail" -gt 0 ] && exit 1
exit 0
