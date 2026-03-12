#!/usr/bin/env bash
set -uo pipefail

BASE_URL="${BASE_URL:-https://localhost}"
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
# Allow self-signed certs when using HTTPS (e.g. Caddy local_certs)
case "$BASE_URL" in https://*) CURL_EXTRA="-k" ;; *) CURL_EXTRA="" ;; esac
MINIO_ENDPOINT="${MINIO_ENDPOINT:-localhost:9000}"
MINIO_ACCESS="${MINIO_ACCESS:-minioadmin}"
MINIO_SECRET="${MINIO_SECRET:-minioadmin}"
BUCKET="report-checker-documents"

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

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
COOKIE_JAR="$TMPDIR/cookies.txt"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║     Report Checker — Live Test Suite     ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo -e "  Target (Caddy): ${BOLD}$BASE_URL${NC}"
echo -e "  Backend direct: ${BOLD}$BACKEND_URL${NC}"
echo ""

# ─── 1. Health check via Caddy ───────────────────────────────────
echo -e "${YELLOW}[1/11] Health check (Caddy → backend)${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" "$BASE_URL/health" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /health" 200 "$code" "$body"
echo ""

# ─── 2. Health check directly ────────────────────────────────────
echo -e "${YELLOW}[2/11] Health check (backend direct inside container)${NC}"
resp=$(docker compose exec -T backend python - <<'PY'
import sys
import urllib.request

url = "http://localhost:8000/health"
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        body = r.read().decode("utf-8", errors="replace")
        sys.stdout.write(body.rstrip("\n") + "\n")
        sys.stdout.write(str(r.getcode()) + "\n")
except Exception as e:
    sys.stdout.write(str(e) + "\n")
    sys.stdout.write("0\n")
PY
)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /health (direct inside container)" 200 "$code" "$body"
echo ""

# ─── 3. Unauthenticated access should be rejected ────────────────
echo -e "${YELLOW}[3/11] Auth gate — reject unauthenticated request${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" "$BASE_URL/api/v1/auth/me" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /api/v1/auth/me (no cookie)" 401 "$code" "$body"
echo ""

# ─── 4. Dev login ────────────────────────────────────────────────
echo -e "${YELLOW}[4/11] Auth — dev login${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -c "$COOKIE_JAR" \
    -X POST "$BASE_URL/api/v1/auth/dev/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"tester@itmo.ru","name":"Live Tester"}' 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "POST /api/v1/auth/dev/login" 200 "$code" "$body"
USER_NAME=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','?'))" 2>/dev/null || echo "?")
echo -e "         Logged in as: ${BOLD}$USER_NAME${NC}"
echo ""

# ─── 5. Authenticated /me ────────────────────────────────────────
echo -e "${YELLOW}[5/11] Auth — verify session${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -b "$COOKIE_JAR" "$BASE_URL/api/v1/auth/me" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /api/v1/auth/me (with cookie)" 200 "$code" "$body"
echo ""

# ─── 6. Internal API: upload practice report PDF (no auth) ───────
echo -e "${YELLOW}[6/11] Internal API — upload practice report (no auth)${NC}"
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

# ─── 6b. Internal API: upload VKR template PDF (no auth) ─────────
echo -e "${YELLOW}[6b/11] Internal API — upload VKR template (no auth)${NC}"
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

# ─── 7. Internal API: get check results for practice report ──────
if [ -n "$DOC_ID" ]; then
    echo -e "${YELLOW}[7/11] Internal API — fetch check results (practice report)${NC}"
    resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" "$BASE_URL/internal/documents/$DOC_ID/checks" 2>&1)
    body=$(echo "$resp" | sed '$d')
    code=$(echo "$resp" | tail -1)
    check "GET /internal/documents/$DOC_ID/checks" 200 "$code" "$body"
    RESULT_COUNT=$(echo "$body" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    echo -e "         Results returned: ${BOLD}$RESULT_COUNT${NC}"
    echo ""
else
    echo -e "${YELLOW}[7/11] SKIPPED — no document ID${NC}"
    echo ""
fi

# ─── 8. Web API: download document (proves MinIO round-trip) ─────
if [ -n "$DOC_ID" ]; then
    echo -e "${YELLOW}[8/11] Web API — download practice report (proves MinIO works)${NC}"
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
    echo -e "${YELLOW}[8/11] SKIPPED — no document ID${NC}"
    echo ""
fi

# ─── 9. Direct MinIO verification ────────────────────────────────
if [ -n "$DOC_ID" ]; then
    echo -e "${YELLOW}[9/11] MinIO — direct S3 object verification${NC}"
    MINIO_OK=$(python3 -c "
import urllib.request, urllib.error, hmac, hashlib, datetime, sys

endpoint = 'http://$MINIO_ENDPOINT'
access_key = '$MINIO_ACCESS'
secret_key = '$MINIO_SECRET'
bucket = '$BUCKET'
prefix = 'documents/internal/$DOC_ID/'

now = datetime.datetime.now(datetime.timezone.utc)
date_stamp = now.strftime('%Y%m%d')
amz_date = now.strftime('%Y%m%dT%H%M%SZ')
region = 'us-east-1'
service = 's3'

host = '$MINIO_ENDPOINT'
canonical_uri = '/' + bucket + '/'
canonical_querystring = 'list-type=2&prefix=' + urllib.parse.quote(prefix, safe='')

headers_to_sign = 'host:' + host + '\n' + 'x-amz-content-sha256:UNSIGNED-PAYLOAD\n' + 'x-amz-date:' + amz_date + '\n'
signed_headers = 'host;x-amz-content-sha256;x-amz-date'

canonical_request = 'GET\n' + canonical_uri + '\n' + canonical_querystring + '\n' + headers_to_sign + '\n' + signed_headers + '\nUNSIGNED-PAYLOAD'

credential_scope = date_stamp + '/' + region + '/' + service + '/aws4_request'
string_to_sign = 'AWS4-HMAC-SHA256\n' + amz_date + '\n' + credential_scope + '\n' + hashlib.sha256(canonical_request.encode()).hexdigest()

def sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()

signing_key = sign(sign(sign(sign(('AWS4' + secret_key).encode(), date_stamp), region), service), 'aws4_request')
signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

authorization = 'AWS4-HMAC-SHA256 Credential=' + access_key + '/' + credential_scope + ', SignedHeaders=' + signed_headers + ', Signature=' + signature

url = endpoint + canonical_uri + '?' + canonical_querystring
req = urllib.request.Request(url, headers={
    'Host': host,
    'x-amz-date': amz_date,
    'x-amz-content-sha256': 'UNSIGNED-PAYLOAD',
    'Authorization': authorization,
})
try:
    resp = urllib.request.urlopen(req)
    body = resp.read().decode()
    if '<Key>' in body:
        import re
        keys = re.findall(r'<Key>([^<]+)</Key>', body)
        for k in keys:
            print('FOUND:' + k)
    else:
        print('EMPTY')
except Exception as e:
    print('ERROR:' + str(e))
" 2>&1)

    if echo "$MINIO_OK" | grep -q "^FOUND:"; then
        S3_KEY=$(echo "$MINIO_OK" | grep "^FOUND:" | head -1 | sed 's/^FOUND://')
        printf "  ${GREEN}✓ PASS${NC}  Object found in MinIO: %s\n" "$S3_KEY"
        pass=$((pass + 1))
    elif echo "$MINIO_OK" | grep -q "^EMPTY"; then
        printf "  ${RED}✗ FAIL${NC}  No objects under prefix documents/internal/%s/\n" "$DOC_ID"
        fail=$((fail + 1))
    else
        printf "  ${RED}✗ FAIL${NC}  MinIO check error: %s\n" "$MINIO_OK"
        fail=$((fail + 1))
    fi
    echo ""
else
    echo -e "${YELLOW}[9/11] SKIPPED — no document ID${NC}"
    echo ""
fi

# ─── 10. Web API: list documents (both uploads visible) ──────────
echo -e "${YELLOW}[10/11] Web API — list documents (verify both uploads)${NC}"
resp=$(curl $CURL_EXTRA -s -w "\n%{http_code}" -b "$COOKIE_JAR" "$BASE_URL/api/v1/documents/?size=50" 2>&1)
body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -1)
check "GET /api/v1/documents/" 200 "$code" "$body"
TOTAL=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total','?'))" 2>/dev/null || echo "?")
echo -e "         Total documents in DB: ${BOLD}$TOTAL${NC}"
echo ""

# ─── 11. Logout ──────────────────────────────────────────────────
echo -e "${YELLOW}[11/11] Auth — logout${NC}"
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
