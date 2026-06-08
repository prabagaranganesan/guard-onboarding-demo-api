# Guard Onboarding Demo API

Minimal FastAPI backend for testing ProxyHawk Guard onboarding: login, bearer-protected endpoints, nested JSON responses, and OpenAPI import.

**Location:** `/Users/prabhakarg/Workspace/Personal/guard-onboarding-demo-api`

## Quick start

```bash
cd /Users/prabhakarg/Workspace/Personal/guard-onboarding-demo-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8099
```

- Swagger UI: http://127.0.0.1:8099/docs
- OpenAPI JSON (live): http://127.0.0.1:8099/openapi.json
- Health: http://127.0.0.1:8099/health (includes `gitSha` for deploy verification)

## GitHub Actions

Main pipeline: `.github/workflows/ci.yml` (`test` → `deploy-staging` → `guard-staging`).

Required GitHub config:
- Variable `STAGING_DEPLOY_PLATFORM` = `render`
- Variable `STAGING_API_URL` — Render service URL
- Secret `STAGING_DEPLOY_HOOK` — Render deploy hook (Settings → Auto-Deploy OFF)
- Secrets `PROXYHAWK_API_EMAIL`, `PROXYHAWK_API_PASSWORD`

Smoke test:

```bash
./scripts/smoke-test.sh
```

## Demo credentials

| Email | Password | Role |
|-------|----------|------|
| `demo@proxyhawk.io` | `demo1234` | customer |
| `admin@proxyhawk.io` | `admin1234` | admin |

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/auth/login` | No | Returns `accessToken` (Bearer JWT) |
| `GET` | `/products` | Bearer | Paginated product list with nested `data.products[]`, `pagination`, `inventory.warehouse` |
| `GET` | `/products/{product_id}` | Bearer | Detail with nested `specifications`, `vendor.contact`, `reviews[]` |
| `GET` | `/profile` | Bearer | Profile with nested `preferences.notifications`, `address`, `subscription.features[]` |

### Login

```bash
curl -s -X POST http://127.0.0.1:8099/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@proxyhawk.io","password":"demo1234"}'
```

Use the returned `accessToken`:

```bash
export TOKEN="<accessToken>"
curl -s http://127.0.0.1:8099/products -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8099/products/prod_001 -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8099/profile -H "Authorization: Bearer $TOKEN"
```

## Files for Guard / ProxyHawk testing

Use these when exercising onboarding import flows:

| File | Use in Guard |
|------|----------------|
| **`openapi.yaml`** | OpenAPI / Swagger URL import (upload file in Phase 1 stub, or paste URL `http://127.0.0.1:8099/openapi.json` in Phase 2) |
| **`openapi.json`** | Same spec in JSON — works with Guard JSON file import |
| **`examples/login-response.json`** | Example upload after traffic capture (auth anchor / token path testing) |
| **`examples/products-list-response.json`** | Example upload — nested list + pagination fields |
| **`examples/product-detail-response.json`** | Example upload — deep nesting: vendor, specs, reviews |
| **`examples/profile-response.json`** | Example upload — role/preferences/subscription nesting |

### Suggested Guard onboarding flow

1. **Start this API** on port `8099`.
2. **Capture traffic** in ProxyHawk (login → products → detail → profile) using demo credentials.
3. **Or import OpenAPI:**
   - Add Endpoints → **OpenAPI / Swagger** → upload `openapi.yaml` or `openapi.json`
   - Expect **4 endpoints** separated by path/method.
4. **Quality check** — upload example JSON files from `examples/` to grow field coverage (nested paths like `data.products[].inventory.warehouse.name`).
5. **Auth anchor** — mark `POST /auth/login` as auth endpoint; token path: `accessToken`; header: `Authorization: Bearer`.
6. **Field review** — compare required vs optional on nested fields (`subscription.features`, `reviews[].score`, etc.).

### OpenAPI URL (when server is running)

```
http://127.0.0.1:8099/openapi.json
```

Point ProxyHawk at this URL from the Mac client (Phase 2) or upload the static files from this repo (Phase 1).

## Nested response shapes (intentional)

Designed to stress Guard baseline + field classification:

- **List:** `data.products[].price.amount`, `data.products[].inventory.warehouse.id`, `data.pagination.totalPages`
- **Detail:** `data.specifications.battery.hours`, `data.vendor.contact.phone`, `data.reviews[].createdAt`
- **Profile:** `data.preferences.notifications.email`, `data.address.postalCode`, `data.subscription.features[]`

Some fields appear only on detail/profile (good for watch-list / example-upload testing).

## Product IDs

- `prod_001` — Wireless Headphones (reviews + vendor)
- `prod_002` — Mechanical Keyboard
- `prod_003` — Team Mug (out of stock, empty reviews)

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_API_SECRET` | `guard-demo-dev-secret-change-me` | JWT signing secret |

## Project layout

```
guard-onboarding-demo-api/
├── main.py                 # FastAPI app
├── requirements.txt
├── openapi.yaml            # Static OpenAPI for Guard import
├── openapi.json
├── examples/               # Sample responses for example-upload flow
├── scripts/smoke-test.sh
└── README.md
```
