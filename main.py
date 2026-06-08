"""
Guard onboarding demo API — login + bearer-protected product/profile endpoints.

Run:  uvicorn main:app --reload --port 8099
Docs: http://127.0.0.1:8099/docs
OpenAPI JSON: http://127.0.0.1:8099/openapi.json
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

APP_SECRET = os.environ.get("DEMO_API_SECRET", "guard-demo-dev-secret-change-me")
TOKEN_TTL_MINUTES = 60

app = FastAPI(
    title="Guard Onboarding Demo API",
    description=(
        "Minimal backend for testing ProxyHawk Guard onboarding: "
        "login, product list/detail, and profile with nested JSON shapes."
    ),
    version="1.0.0",
)

bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

USERS = {
    "demo@proxyhawk.io": {
        "password": "demo1234",
        "profile": {
            "id": "usr_1001",
            "email": "demo@proxyhawk.io",
            "displayName": "Demo User",
            "role": "customer",
            "createdAt": "2025-01-10T08:00:00Z",
            "preferences": {
                "theme": "light",
                "locale": "en-US",
                "notifications": {
                    "email": True,
                    "push": False,
                    "marketing": False,
                },
            },
            "address": {
                "line1": "100 Market Street",
                "line2": "Suite 400",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US",
            },
            "subscription": {
                "plan": "pro",
                "status": "active",
                "renewsAt": "2026-07-01T00:00:00Z",
                "features": ["guard", "traffic-capture", "ci-checkpoint"],
            },
        },
    },
    "admin@proxyhawk.io": {
        "password": "admin1234",
        "profile": {
            "id": "usr_2001",
            "email": "admin@proxyhawk.io",
            "displayName": "Admin User",
            "role": "admin",
            "createdAt": "2024-06-01T12:00:00Z",
            "preferences": {
                "theme": "dark",
                "locale": "en-US",
                "notifications": {
                    "email": True,
                    "push": True,
                    "marketing": True,
                },
            },
            "address": {
                "line1": "500 Howard Street",
                "line2": None,
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US",
            },
            "subscription": {
                "plan": "enterprise",
                "status": "active",
                "renewsAt": "2026-12-01T00:00:00Z",
                "features": ["guard", "traffic-capture", "ci-checkpoint", "sso", "audit-log"],
            },
        },
    },
}

PRODUCTS = [
    {
        "id": "prod_001",
        "sku": "WH-1000",
        "name": "Wireless Headphones",
        "category": "electronics",
        "price": {"amount": 249.99, "currency": "USD"},
        "inventory": {"inStock": True, "quantity": 42, "warehouse": {"id": "wh_sf", "name": "SF Bay"}},
        "tags": ["audio", "wireless"],
        "rating": {"average": 4.6, "count": 1284},
    },
    {
        "id": "prod_002",
        "sku": "KB-MECH-01",
        "name": "Mechanical Keyboard",
        "category": "electronics",
        "price": {"amount": 129.50, "currency": "USD"},
        "inventory": {"inStock": True, "quantity": 18, "warehouse": {"id": "wh_austin", "name": "Austin"}},
        "tags": ["peripherals"],
        "rating": {"average": 4.8, "count": 532},
    },
    {
        "id": "prod_003",
        "sku": "MUG-TEAM",
        "name": "Team Mug",
        "category": "merchandise",
        "price": {"amount": 18.00, "currency": "USD"},
        "inventory": {"inStock": False, "quantity": 0, "warehouse": {"id": "wh_sf", "name": "SF Bay"}},
        "tags": ["swag"],
        "rating": {"average": 4.2, "count": 89},
    },
]

PRODUCT_DETAILS = {
    "prod_001": {
        **PRODUCTS[0],
        "description": "Noise-cancelling over-ear headphones with 30h battery life.",
        "specifications": {
            "weightGrams": 250,
            "connectivity": ["bluetooth", "usb-c"],
            "battery": {"hours": 30, "fastChargeMinutes": 15},
        },
        "vendor": {
            "id": "vnd_acme",
            "name": "Acme Audio",
            "contact": {"email": "support@acme-audio.example", "phone": "+1-555-0100"},
        },
        "reviews": [
            {
                "id": "rev_1",
                "author": "alex",
                "score": 5,
                "title": "Great sound",
                "body": "Deep bass and comfortable fit.",
                "createdAt": "2025-11-02T14:22:00Z",
            },
            {
                "id": "rev_2",
                "author": "jordan",
                "score": 4,
                "title": "Good but heavy",
                "body": "Sound quality is excellent; a bit heavy for long calls.",
                "createdAt": "2025-12-18T09:05:00Z",
            },
        ],
        "relatedProductIds": ["prod_002"],
    },
    "prod_002": {
        **PRODUCTS[1],
        "description": "Hot-swappable mechanical keyboard with RGB backlight.",
        "specifications": {
            "weightGrams": 980,
            "connectivity": ["usb-c", "bluetooth"],
            "switches": {"type": "tactile", "brand": "Cherry", "model": "MX Brown"},
        },
        "vendor": {
            "id": "vnd_keys",
            "name": "KeyForge",
            "contact": {"email": "hello@keyforge.example", "phone": None},
        },
        "reviews": [
            {
                "id": "rev_3",
                "author": "sam",
                "score": 5,
                "title": "Best keyboard I've owned",
                "body": "Typing feel is perfect.",
                "createdAt": "2026-01-05T18:40:00Z",
            }
        ],
        "relatedProductIds": ["prod_001", "prod_003"],
    },
    "prod_003": {
        **PRODUCTS[2],
        "description": "Ceramic mug with ProxyHawk team logo.",
        "specifications": {
            "weightGrams": 320,
            "material": "ceramic",
            "capacityMl": 350,
        },
        "vendor": {
            "id": "vnd_swag",
            "name": "SwagCo",
            "contact": {"email": "orders@swagco.example", "phone": "+1-555-0199"},
        },
        "reviews": [],
        "relatedProductIds": [],
    },
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str = Field(examples=["demo@proxyhawk.io"])
    password: str = Field(examples=["demo1234"])


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: Literal["Bearer"] = "Bearer"
    expiresIn: int = Field(description="Seconds until expiry")
    user: dict


class ErrorResponse(BaseModel):
    error: str
    message: str


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    totalItems: int
    totalPages: int


class ProductListData(BaseModel):
    products: list[dict]
    pagination: PaginationMeta
    filters: dict


class ProductListResponse(BaseModel):
    data: ProductListData
    meta: dict


class ProductDetailResponse(BaseModel):
    data: dict
    meta: dict


class ProfileResponse(BaseModel):
    data: dict
    meta: dict


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def create_access_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, APP_SECRET, algorithm="HS256")


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, APP_SECRET, algorithms=["HS256"])
        email = payload.get("sub")
        if not email or email not in USERS:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        return email
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def current_user_email(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Use: Bearer <accessToken>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": "guard-onboarding-demo-api"}


@app.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["auth"],
    summary="Login and receive access token",
)
def login(body: LoginRequest) -> TokenResponse:
    user = USERS.get(body.email.strip().lower())
    if user is None or user["password"] != body.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(body.email.strip().lower())
    return TokenResponse(
        accessToken=token,
        expiresIn=TOKEN_TTL_MINUTES * 60,
        user={
            "id": user["profile"]["id"],
            "email": user["profile"]["email"],
            "displayName": user["profile"]["displayName"],
            "role": user["profile"]["role"],
        },
    )


@app.get(
    "/products",
    response_model=ProductListResponse,
    tags=["products"],
    summary="List products (paginated, nested data envelope)",
)
def list_products(
    page: int = 1,
    pageSize: int = 20,
    category: str | None = None,
    _: str = Depends(current_user_email),
) -> ProductListResponse:
    items = PRODUCTS
    if category:
        items = [p for p in items if p["category"] == category.lower()]
    total = len(items)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    page_items = items[start:end]
    total_pages = max(1, (total + pageSize - 1) // pageSize)
    return ProductListResponse(
        data=ProductListData(
            products=page_items,
            pagination=PaginationMeta(
                page=page,
                pageSize=pageSize,
                totalItems=total,
                totalPages=total_pages,
            ),
            filters={"category": category, "applied": category is not None},
        ),
        meta={"requestId": "req_list_001", "generatedAt": datetime.now(timezone.utc).isoformat()},
    )


@app.get(
    "/products/{product_id}",
    response_model=ProductDetailResponse,
    tags=["products"],
    summary="Product detail with nested vendor, specs, and reviews",
)
def get_product(product_id: str, _: str = Depends(current_user_email)) -> ProductDetailResponse:
    detail = PRODUCT_DETAILS.get(product_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")
    return ProductDetailResponse(
        data=detail,
        meta={"requestId": f"req_detail_{product_id}", "generatedAt": datetime.now(timezone.utc).isoformat()},
    )


@app.get(
    "/profile",
    response_model=ProfileResponse,
    tags=["profile"],
    summary="Current user profile with nested preferences and subscription",
)
def get_profile(email: str = Depends(current_user_email)) -> ProfileResponse:
    profile = USERS[email]["profile"]
    return ProfileResponse(
        data=profile,
        meta={"requestId": "req_profile_001", "generatedAt": datetime.now(timezone.utc).isoformat()},
    )
