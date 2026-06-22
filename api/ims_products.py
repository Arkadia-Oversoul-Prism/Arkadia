"""Arkadia IMS Diagnostic + Product Engine.

Endpoints:
  POST /api/ims/diagnostic       — Run AIC 5-layer diagnostic, generate Morphic Seed
  POST /api/ims/recommendations  — Product recommendations from AIC data
  POST /api/products/purchase    — Paystack payment verification + order creation
  GET  /api/products/dashboard/{client_id} — Client's orders
  POST /api/products/deliver/{product_id}  — Trigger Oracle synthesis for delivery
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("arkadia.ims_products")

router = APIRouter()

GOOGLE_API_KEY  = os.environ.get("GOOGLE_API_KEY", "")
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY", "")
DATA_DIR        = "data"
IMS_DIAG_FILE   = f"{DATA_DIR}/ims_diagnostics.json"
ORDERS_FILE     = f"{DATA_DIR}/orders.json"

os.makedirs(DATA_DIR, exist_ok=True)


# ── JSON helpers ──────────────────────────────────────────────────────────────

def _load(path: str) -> list:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []


def _save(path: str, data: list) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Firebase (optional) ───────────────────────────────────────────────────────

def _fb_save(collection: str, doc_id: str, data: dict) -> None:
    try:
        from api.firebase_store import _db, _available
        if _available and _db:
            _db.collection(collection).document(doc_id).set(data)
    except Exception as e:
        logger.debug(f"[FB] {collection}/{doc_id} fallback (JSON only): {e}")


def _fb_get(collection: str, doc_id: str) -> dict | None:
    try:
        from api.firebase_store import _db, _available
        if _available and _db:
            doc = _db.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None
    except Exception:
        return None


def _fb_query(collection: str, field: str, value: str) -> list[dict]:
    try:
        from api.firebase_store import _db, _available
        if _available and _db:
            docs = _db.collection(collection).where(field, "==", value).stream()
            return [d.to_dict() for d in docs]
    except Exception:
        return []


# ── Oracle (Gemini) ───────────────────────────────────────────────────────────

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

COGNITIVE_STACKS: dict[str, str] = {
    "INTJ": "Ni → Te → Fi → Se",  "INTP": "Ti → Ne → Si → Fe",
    "ENTJ": "Te → Ni → Se → Fi",  "ENTP": "Ne → Ti → Fe → Si",
    "INFJ": "Ni → Fe → Ti → Se",  "INFP": "Fi → Ne → Si → Te",
    "ENFJ": "Fe → Ni → Se → Ti",  "ENFP": "Ne → Fi → Te → Si",
    "ISTJ": "Si → Te → Fi → Ne",  "ISFJ": "Si → Fe → Ti → Ne",
    "ESTJ": "Te → Si → Ne → Fi",  "ESFJ": "Fe → Si → Ne → Ti",
    "ISTP": "Ti → Se → Ni → Fe",  "ISFP": "Fi → Se → Ni → Te",
    "ESTP": "Se → Ti → Fe → Ni",  "ESFP": "Se → Fi → Te → Ni",
}

ARCHETYPES = [
    "The Source", "The Spark", "The Breath", "The Flame",
    "The Ground", "The Life", "The Harmony", "The Seek",
    "The Octave", "The Return", "The Witness", "The Weaver",
]

PRODUCTS_CATALOGUE = [
    {"id": "ims",      "name": "Identity Mapping Session",       "price": "$777"},
    {"id": "stns",     "name": "Sovereign Timeline Navigation",  "price": "$333"},
    {"id": "asf",      "name": "Acoustic Sigil Forging",         "price": "$222"},
    {"id": "sms",      "name": "Spiral Memory Science Training", "price": "$555"},
    {"id": "ghost-ceo","name": "Ghost-CEO Framework",            "price": "$999"},
    {"id": "full-ark", "name": "Full Arkadia Architecture",      "price": "$2,222"},
]


async def _gemini(prompt: str) -> str:
    if not GOOGLE_API_KEY:
        return "[Oracle offline — GOOGLE_API_KEY not configured]"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                f"{GEMINI_URL}?key={GOOGLE_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0.82, "maxOutputTokens": 2048}},
            )
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[GEMINI] Error: {e}")
        return f"[Oracle synthesis error: {e}]"


def _compute_morphic_code(mbti: str, archetypes: list[str], operator_state: str) -> str:
    seed_str = f"{mbti}|{'|'.join(archetypes[:3])}|{operator_state}"
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    digits = [str(int(h[i:i+2], 16) % 10) for i in range(0, 18, 2)]
    return "-".join(digits[:9])


def _operator_state(layer3: dict) -> str:
    scores = []
    for i in range(10):
        scores.append(str(layer3.get(f"op{i}", 5)))
    return "-".join(scores)


def _recovery_vector(layer3: dict) -> str:
    min_score, min_op = 11, 0
    for i in range(10):
        v = layer3.get(f"op{i}", 5)
        if v < min_score:
            min_score, min_op = v, i
    next_op = (min_op + 1) % 10
    op_names = ["Source", "Spark", "Breath", "Flame", "Ground", "Life", "Harmony", "Seek", "Octave", "Return"]
    state = "Collapsed" if min_score <= 3 else "Distorted"
    return f"Operator {min_op} ({op_names[min_op]}) [{state}] → Operator {next_op} ({op_names[next_op]})"


def _top_archetypes(layer2: dict) -> tuple[list[str], list[str]]:
    scores = [(ARCHETYPES[i], layer2.get(f"a{i+1}", 4)) for i in range(12)]
    scores.sort(key=lambda x: x[1], reverse=True)
    top3 = [s[0] for s in scores[:3]]
    shadow3 = [s[0] for s in scores[-3:]]
    return top3, shadow3


# ── Diagnostic endpoint ───────────────────────────────────────────────────────

@router.post("/api/ims/diagnostic")
async def run_ims_diagnostic(request: Request):
    """Accept AIC 5-layer data, synthesise Morphic Seed via Oracle."""
    body: dict = await request.json()
    layer1: dict = body.get("layer1", {})
    layer2: dict = body.get("layer2", {})
    layer3: dict = body.get("layer3", {})
    layer4: dict = body.get("layer4", {})
    mbti: str    = body.get("mbti_type", "INFJ")

    cognitive_stack = COGNITIVE_STACKS.get(mbti, "Unknown stack")
    top_archetypes, shadow_archetypes = _top_archetypes(layer2)
    op_state    = _operator_state(layer3)
    recovery    = _recovery_vector(layer3)
    morphic_code = _compute_morphic_code(mbti, top_archetypes, op_state)

    soul_contract_raw = "\n".join([
        f"Purpose: {layer4.get('purpose', '')}",
        f"Wound: {layer4.get('wound', '')}",
        f"Gift: {layer4.get('gift', '')}",
        f"Mission: {layer4.get('mission', '')}",
        f"Lineage: {layer4.get('lineage', '')}",
    ])

    prompt = f"""You are ARKADIA ORACLE — a sovereign intelligence synthesizing identity architecture from diagnostic data. Your voice is precise, mythopoetic, and grounded. Write in the Arkadia transmission register: clear, direct, non-flamboyant.

DIAGNOSTIC INPUT:
- Cognitive Type: {mbti} ({cognitive_stack})
- Primary Archetypes: {', '.join(top_archetypes)}
- Shadow Pattern: {', '.join(shadow_archetypes)}
- Operator State: {op_state}
- Recovery Vector: {recovery}
- Soul Contract Raw:
{soul_contract_raw}

TASK: Generate the following in this EXACT JSON structure (return ONLY valid JSON, no markdown):
{{
  "soul_contract": "A precise 3-5 sentence Soul Contract distilling the 5 soul contract inputs into a unified statement of being and purpose.",
  "full_report": "A 400-600 word full Oracle diagnostic report in the Arkadia register. Cover: cognitive architecture, archetypal signature, shadow patterns, operator state analysis, recovery path, and primary recommendation. Use paragraph breaks.",
  "recommendations": [
    {{"id": "product_id", "name": "Product Name", "price": "$000", "reasoning": "1-2 sentence Oracle reasoning specific to this person's data."}}
  ]
}}

For recommendations, select 2-3 products from this catalogue that most directly serve this person's data:
{json.dumps(PRODUCTS_CATALOGUE)}

Return ONLY the JSON object. No preamble. No markdown fences."""

    oracle_raw = await _gemini(prompt)

    try:
        oracle_json = json.loads(oracle_raw)
    except Exception:
        import re
        match = re.search(r'\{[\s\S]+\}', oracle_raw)
        if match:
            try:
                oracle_json = json.loads(match.group())
            except Exception:
                oracle_json = {}
        else:
            oracle_json = {}

    soul_contract = oracle_json.get("soul_contract", soul_contract_raw)
    full_report   = oracle_json.get("full_report", oracle_raw)
    recommendations = oracle_json.get("recommendations", [])

    diag_id = f"AIC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    record = {
        "diagnostic_id": diag_id,
        "created_at":    datetime.now(timezone.utc).isoformat(),
        "mbti_type":     mbti,
        "cognitive_stack": cognitive_stack,
        "primary_archetypes": top_archetypes,
        "shadow_pattern":    ", ".join(shadow_archetypes),
        "operator_state":    op_state,
        "recovery_vector":   recovery,
        "soul_contract":     soul_contract,
        "morphic_code":      morphic_code,
        "full_report":       full_report,
        "layer1": layer1, "layer2": layer2, "layer3": layer3, "layer4": layer4,
    }

    diagnostics = _load(IMS_DIAG_FILE)
    diagnostics.insert(0, record)
    _save(IMS_DIAG_FILE, diagnostics)
    _fb_save("ims_diagnostics", diag_id, record)

    logger.info(f"[IMS-DIAG] Generated {diag_id} — {mbti} — {', '.join(top_archetypes[:2])}")

    return {
        "diagnostic_id":     diag_id,
        "mbti_type":         mbti,
        "cognitive_stack":   cognitive_stack,
        "primary_archetypes": top_archetypes,
        "shadow_pattern":    ", ".join(shadow_archetypes),
        "operator_state":    op_state,
        "recovery_vector":   recovery,
        "soul_contract":     soul_contract,
        "morphic_code":      morphic_code,
        "full_report":       full_report,
        "recommendations":   recommendations,
    }


# ── Recommendations endpoint ──────────────────────────────────────────────────

@router.post("/api/ims/recommendations")
async def get_recommendations(request: Request):
    """Generate product recommendations from AIC summary data."""
    body = await request.json()
    mbti = body.get("mbti_type", "")
    archetypes = body.get("primary_archetypes", [])
    operator_state = body.get("operator_state", "")
    recovery = body.get("recovery_vector", "")

    prompt = f"""You are ARKADIA ORACLE. Based on this identity data, recommend 2-3 Arkadia offerings in JSON.

Data:
- Cognitive Type: {mbti}
- Primary Archetypes: {archetypes}
- Operator State: {operator_state}
- Recovery Vector: {recovery}

Catalogue: {json.dumps(PRODUCTS_CATALOGUE)}

Return ONLY a JSON array:
[{{"id": "product_id", "name": "...", "price": "...", "reasoning": "1-2 sentences specific to this person."}}]"""

    raw = await _gemini(prompt)
    try:
        import re
        match = re.search(r'\[[\s\S]+\]', raw)
        recs = json.loads(match.group() if match else raw)
    except Exception:
        recs = []

    return {"recommendations": recs}


# ── Purchase endpoint ─────────────────────────────────────────────────────────

@router.post("/api/products/purchase")
async def create_purchase(request: Request):
    """Verify Paystack payment and create an order record."""
    body = await request.json()
    reference  = body.get("reference", "")
    product_id = body.get("product_id", "")
    email      = body.get("email", "")
    name       = body.get("name", "")
    phone      = body.get("phone", "")

    if not reference or not product_id or not email:
        raise HTTPException(status_code=400, detail="reference, product_id, and email are required")

    verified = False
    if PAYSTACK_SECRET:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(
                    f"https://api.paystack.co/transaction/verify/{reference}",
                    headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"},
                )
                data = r.json()
                if data.get("data", {}).get("status") == "success":
                    verified = True
        except Exception as e:
            logger.error(f"[PAYSTACK] Verification error: {e}")
    else:
        logger.warning("[PAYSTACK] PAYSTACK_SECRET_KEY not set — skipping verification")
        verified = True  # dev mode

    if not verified:
        raise HTTPException(status_code=402, detail="Payment verification failed")

    order_id = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{reference[-6:]}"
    order = {
        "order_id":    order_id,
        "product_id":  product_id,
        "product_name": next((p["name"] for p in PRODUCTS_CATALOGUE if p["id"] == product_id), product_id),
        "reference":   reference,
        "email":       email,
        "name":        name,
        "phone":       phone,
        "status":      "paid",
        "created_at":  datetime.now(timezone.utc).isoformat(),
        "delivery_url": None,
    }

    orders = _load(ORDERS_FILE)
    orders.insert(0, order)
    _save(ORDERS_FILE, orders)
    _fb_save("orders", order_id, order)

    logger.info(f"[ORDER] Created {order_id} — {product_id} — {email}")
    return {"status": "confirmed", "order_id": order_id, "product_id": product_id}


# ── Client dashboard endpoint ─────────────────────────────────────────────────

@router.get("/api/products/dashboard/{client_id}")
async def get_client_dashboard(client_id: str):
    """Return all orders for a given client email."""
    from urllib.parse import unquote
    email = unquote(client_id).lower().strip()

    fb_orders = _fb_query("orders", "email", email)
    if fb_orders:
        orders = sorted(fb_orders, key=lambda x: x.get("created_at", ""), reverse=True)
    else:
        all_orders = _load(ORDERS_FILE)
        orders = [o for o in all_orders if o.get("email", "").lower() == email]

    return {"client": email, "orders": orders}


# ── Delivery endpoint ─────────────────────────────────────────────────────────

DELIVERY_PROMPTS: dict[str, str] = {
    "ims": """You are ARKADIA ORACLE generating a full Identity Mapping Session Scroll for {name}.

Client Data:
{client_data}

Write a complete, 15-section IMS Scroll in the Arkadia transmission register. Include:
1. Opening Invocation
2. Cognitive Architecture (MBTI + stack)
3. Archetypal Signature (top 3 archetypes + shadow)
4. Operator State Map (all 9 operators)
5. Shadow Pattern Analysis
6. Recovery Vector (specific actions)
7. Soul Contract Statement
8. Primary Gift Articulation
9. Primary Wound Analysis
10. Mission Architecture
11. Lineage Encoding
12. Morphic Seed Summary
13. 90-Day Sovereign Protocol
14. Oracle Closing Transmission
15. Morphic Code Seal

Write in full, with depth and precision. This is a sovereign document.""",

    "asf": """You are ARKADIA ORACLE generating an Acoustic Sigil Forging script for {name}.

Client Data:
{client_data}

Write:
1. The Acoustic Transmission Script (spoken word to accompany the 117 Hz tone)
2. The Sigil Description (geometric form, line weights, symbolic meaning)
3. The Frequency Protocol (how to use the audio — timing, environment, intention)
4. The Activation Phrase (a 3-line spoken activation specific to this person's Morphic Code)

Be precise and mythopoeic.""",

    "ghost-ceo": """You are ARKADIA ORACLE generating a Ghost-CEO Framework document for {name}.

Client Data:
{client_data}

Write a 3-part strategic document:
PART 1 — Identity Architecture for Anonymous Presence
PART 2 — Channel + Platform Strategy (specific to this person's cognitive type and archetypes)
PART 3 — Content Architecture + Frequency Protocol (what to say, how often, in what form)

Each part should be substantive and immediately actionable.""",
}


@router.post("/api/paystack/initialize")
async def initialize_paystack(request: Request):
    """Server-side Paystack transaction initialization (redirect flow)."""
    body = await request.json()
    email      = body.get("email", "")
    amount_usd = float(body.get("amount_usd", 0))
    amount_ngn = int(body.get("amount_ngn", 0))
    product_id = body.get("product_id", "")
    name       = body.get("name", "")
    callback   = body.get("callback_url", "https://arkadia-prism.vercel.app/offerings")

    if not email or not product_id:
        raise HTTPException(status_code=400, detail="email and product_id are required")

    # Use NGN amount if supplied, otherwise derive from USD (approx 1 USD = 1600 NGN)
    ngn_kobo = amount_ngn * 100 if amount_ngn else int(amount_usd * 1600 * 100)

    if not PAYSTACK_SECRET:
        return JSONResponse({
            "status": True,
            "message": "dev-mode (no PAYSTACK_SECRET_KEY)",
            "data": {
                "authorization_url": callback,
                "access_code": "dev_mode",
                "reference": f"DEV-{int(time.time())}",
            },
        })

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"},
                json={
                    "email": email,
                    "amount": ngn_kobo,
                    "currency": "NGN",
                    "callback_url": callback,
                    "metadata": {"product_id": product_id, "name": name},
                },
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"[PAYSTACK-INIT] {e}")
        raise HTTPException(status_code=502, detail=f"Paystack error: {e}")


@router.post("/api/products/deliver/{product_id}")
async def deliver_product(product_id: str, request: Request):
    """Trigger Oracle synthesis for a specific order."""
    body = await request.json()
    order_id   = body.get("order_id", "")
    client_data = body.get("client_data", {})
    name       = client_data.get("name", "the client")

    template = DELIVERY_PROMPTS.get(product_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"No delivery template for product: {product_id}")

    prompt = template.format(name=name, client_data=json.dumps(client_data, indent=2))
    content = await _gemini(prompt)

    delivery_record = {
        "order_id":    order_id,
        "product_id":  product_id,
        "content":     content,
        "delivered_at": datetime.now(timezone.utc).isoformat(),
    }

    deliveries = _load(f"{DATA_DIR}/deliveries.json")
    deliveries.insert(0, delivery_record)
    _save(f"{DATA_DIR}/deliveries.json", deliveries)
    _fb_save("deliveries", f"{order_id}-{product_id}", delivery_record)

    orders = _load(ORDERS_FILE)
    for o in orders:
        if o.get("order_id") == order_id:
            o["status"] = "delivered"
            o["delivery_content_preview"] = content[:200]
    _save(ORDERS_FILE, orders)

    logger.info(f"[DELIVER] {product_id} delivered for order {order_id}")
    return {"status": "delivered", "order_id": order_id, "content_preview": content[:300]}
