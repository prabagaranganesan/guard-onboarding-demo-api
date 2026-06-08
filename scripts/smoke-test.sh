#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
BASE="${BASE_URL:-http://127.0.0.1:8099}"

echo "=== Login ==="
LOGIN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@proxyhawk.io","password":"demo1234"}')
echo "$LOGIN" | python3 -m json.tool
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo ""
echo "=== Products list ==="
curl -s "$BASE/products" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40

echo ""
echo "=== Product detail ==="
curl -s "$BASE/products/prod_001" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50

echo ""
echo "=== Profile ==="
curl -s "$BASE/profile" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
