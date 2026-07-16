"""
Arkadian Pulse — Identity Measurement Engine
24 Likert statements × 12 nodes (1 pos + 1 rev per node)
→ vector → sigil → Oracle summary → IMS funnel
"""

import os
import math
import logging
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("arkadia")
router = APIRouter()

_GOOGLE_API_KEY_ENV = os.environ.get("GOOGLE_API_KEY", "")


def _get_api_key() -> str:
    """Resolve active Gemini key: key_manager → env var."""
    try:
        from api.key_manager import get_active_key
        return get_active_key() or _GOOGLE_API_KEY_ENV
    except Exception:
        return _GOOGLE_API_KEY_ENV

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# ── Node definitions ──────────────────────────────────────────────────────────

NODES = ["source", "spark", "breath", "flame", "ground", "life",
         "harmony", "seek", "octave", "return_node", "witness", "weaver"]

NODE_DISPLAY = {
    "source": "Source", "spark": "Spark", "breath": "Breath",
    "flame": "Flame", "ground": "Ground", "life": "Life",
    "harmony": "Harmony", "seek": "Seek", "octave": "Octave",
    "return_node": "Return", "witness": "Witness", "weaver": "Weaver",
}

OPPOSITE_MAP = {
    "source": "spark", "spark": "source",
    "breath": "flame", "flame": "breath",
    "ground": "seek", "seek": "ground",
    "life": "harmony", "harmony": "life",
    "octave": "return_node", "return_node": "octave",
    "witness": "weaver", "weaver": "witness",
}

PATTERN_CLUSTERS = [
    ({"seek", "witness", "octave"},        "Visionary Synthesizer"),
    ({"seek", "flame", "weaver"},          "Reflective Architect"),
    ({"source", "breath", "harmony"},      "Grounded Visionary"),
    ({"spark", "flame", "life"},           "Generative Builder"),
    ({"ground", "harmony", "return_node"}, "Stabilizing Anchor"),
    ({"life", "seek", "spark"},            "Adaptive Pioneer"),
    ({"source", "witness", "breath"},      "Sovereign Witness"),
    ({"flame", "weaver", "octave"},        "Alchemical Weaver"),
    ({"ground", "spark", "life"},          "Rooted Catalyst"),
    ({"return_node", "witness", "source"}, "Cycle Keeper"),
]

SHADOW_DESCRIPTIONS = {
    "source":      "You return to origins with precision but may overlook the living present.",
    "spark":       "You ignite quickly but may scatter before the flame takes root.",
    "breath":      "You hold opposing truths beautifully but may hesitate to choose.",
    "flame":       "You synthesize brilliantly but may overwhelm with layered complexity.",
    "ground":      "You generate insight faster than you build structure.",
    "life":        "You adapt with grace but may resist the stability that sustains growth.",
    "harmony":     "You balance competing demands but may avoid necessary conflict.",
    "seek":        "You dwell in the question but may resist the weight of an answer.",
    "octave":      "You revisit wisely but may find yourself circling instead of landing.",
    "return_node": "You close cycles cleanly but may struggle to trust a new beginning.",
    "witness":     "You observe with rare clarity but may withhold the gift of engagement.",
    "weaver":      "You connect worlds beautifully but may lose your own center in the lattice.",
}

# ── Scoring — 2 statements per node (1 positive + 1 reverse-keyed) ────────────

def _normalize(raw: float) -> float:
    return round((raw - 1) / 4 * 100, 1)


def _calculate_scores(responses: dict) -> dict:
    """
    Each node has two keys: <node>_pos and <node>_rev.
    Raw = (pos_val + (6 - rev_val)) / 2  → normalize to 0-100.
    """
    def node_score(pos_key: str, rev_key: str) -> float:
        pos = responses.get(pos_key, 3)
        rev = responses.get(rev_key, 3)
        raw = (pos + (6 - rev)) / 2
        return _normalize(raw)

    return {
        "source":      node_score("source_pos",  "source_rev"),
        "spark":       node_score("spark_pos",   "spark_rev"),
        "breath":      node_score("breath_pos",  "breath_rev"),
        "flame":       node_score("flame_pos",   "flame_rev"),
        "ground":      node_score("ground_pos",  "ground_rev"),
        "life":        node_score("life_pos",    "life_rev"),
        "harmony":     node_score("harmony_pos", "harmony_rev"),
        "seek":        node_score("seek_pos",    "seek_rev"),
        "octave":      node_score("octave_pos",  "octave_rev"),
        "return_node": node_score("return_pos",  "return_rev"),
        "witness":     node_score("witness_pos", "witness_rev"),
        "weaver":      node_score("weaver_pos",  "weaver_rev"),
    }


def _calculate_confidence(responses: dict) -> int:
    total = len(responses)
    if total == 0:
        return 50
    non_neutral = sum(1 for v in responses.values() if v != 3)
    completion = non_neutral / total

    pairs = [
        ("source_pos", "source_rev"), ("spark_pos", "spark_rev"),
        ("breath_pos", "breath_rev"), ("flame_pos", "flame_rev"),
        ("ground_pos", "ground_rev"), ("life_pos",  "life_rev"),
        ("harmony_pos","harmony_rev"),("seek_pos",  "seek_rev"),
        ("octave_pos", "octave_rev"), ("return_pos","return_rev"),
        ("witness_pos","witness_rev"),("weaver_pos", "weaver_rev"),
    ]
    aligned = sum(
        1 for p, r in pairs
        if (responses.get(p, 3) >= 4 and responses.get(r, 3) <= 2) or
           (responses.get(p, 3) <= 2 and responses.get(r, 3) >= 4) or
           (responses.get(p, 3) == 3 and responses.get(r, 3) == 3)
    )
    reverse_alignment = aligned / len(pairs)
    raw = (completion * 0.6) + (reverse_alignment * 0.4)
    return min(99, max(40, round(raw * 100)))


def _get_primary_patterns(scores: dict) -> list:
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]


def _get_growth_edge(scores: dict) -> dict:
    growth_node, growth_score = sorted(scores.items(), key=lambda x: x[1])[0]
    opposite = OPPOSITE_MAP.get(growth_node, "seek")
    shadow_index = round((growth_score * 0.4) + (scores.get(opposite, 50) * 0.6), 1)
    desc = SHADOW_DESCRIPTIONS.get(growth_node, "You have a significant growth edge here.")
    if shadow_index > 70:
        desc += " This is your primary growth edge."
    return {
        "node": growth_node,
        "display": NODE_DISPLAY.get(growth_node, growth_node.capitalize()),
        "score": growth_score,
        "shadow_index": shadow_index,
        "description": desc,
    }


def _get_pattern_cluster(primary: list) -> str:
    node_set = {p[0] for p in primary}
    for required, name in PATTERN_CLUSTERS:
        if required.issubset(node_set):
            return name
    fallback = {
        "source": "Origin Keeper", "spark": "Sovereign Initiator",
        "breath": "Mirror Holder", "flame": "Sacred Alchemist",
        "ground": "Foundation Builder", "life": "Living Bridge",
        "harmony": "Field Balancer", "seek": "Infinite Questioner",
        "octave": "Spiral Returner", "return_node": "Cycle Closer",
        "witness": "Sacred Witness", "weaver": "Lattice Architect",
    }
    return fallback.get(primary[0][0], "Sovereign Architect") if primary else "Sovereign Architect"


def _generate_sigil_svg(scores: dict) -> str:
    cx, cy, radius = 50, 50, 36
    n = len(NODES)
    positions = {}
    for i, node in enumerate(NODES):
        angle = (2 * math.pi * i / n) - (math.pi / 2)
        positions[node] = {
            "x": round(cx + radius * math.cos(angle), 2),
            "y": round(cy + radius * math.sin(angle), 2),
        }

    lines = []
    for i, node in enumerate(NODES):
        pos1 = positions[node]
        for step in [1, 2]:
            neighbor = NODES[(i + step) % n]
            pos2 = positions[neighbor]
            avg = (scores.get(node, 50) + scores.get(neighbor, 50)) / 2
            thickness = round(0.3 + (avg / 100) * 1.1, 2)
            opacity = round(0.1 + (avg / 100) * 0.32, 2)
            lines.append(
                f'<line x1="{pos1["x"]}" y1="{pos1["y"]}" x2="{pos2["x"]}" y2="{pos2["y"]}" '
                f'stroke="#C9A84C" stroke-width="{thickness}" opacity="{opacity}"/>'
            )
        opp = OPPOSITE_MAP.get(node)
        if opp and node < opp:
            pos2 = positions[opp]
            avg = (scores.get(node, 50) + scores.get(opp, 50)) / 2
            thickness = round(0.2 + (avg / 100) * 0.7, 2)
            opacity = round(0.06 + (avg / 100) * 0.22, 2)
            lines.append(
                f'<line x1="{pos1["x"]}" y1="{pos1["y"]}" x2="{pos2["x"]}" y2="{pos2["y"]}" '
                f'stroke="#00D4AA" stroke-width="{thickness}" opacity="{opacity}"/>'
            )

    circles, labels = [], []
    for node, pos in positions.items():
        score = scores.get(node, 50)
        r = round(1.8 + (score / 100) * 4.2, 2)
        opacity = round(0.4 + (score / 100) * 0.6, 2)
        circles.append(f'<circle cx="{pos["x"]}" cy="{pos["y"]}" r="{round(r+2.2,2)}" fill="#C9A84C" opacity="{round(opacity*0.15,2)}"/>')
        circles.append(f'<circle cx="{pos["x"]}" cy="{pos["y"]}" r="{r}" fill="#C9A84C" opacity="{opacity}"/>')
        lx = round(cx + (radius + 8) * math.cos((2 * math.pi * NODES.index(node) / n) - (math.pi / 2)), 2)
        ly = round(cy + (radius + 8) * math.sin((2 * math.pi * NODES.index(node) / n) - (math.pi / 2)), 2)
        display = NODE_DISPLAY.get(node, node)[:3].upper()
        labels.append(
            f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="rgba(201,168,76,0.5)" font-size="3" font-family="sans-serif" letter-spacing="0.5">{display}</text>'
        )

    return f'''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0D0E1A" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#060710" stop-opacity="0.98"/>
  </radialGradient></defs>
  <circle cx="50" cy="50" r="50" fill="url(#bg)"/>
  {''.join(lines)}
  {''.join(circles)}
  <circle cx="50" cy="50" r="2" fill="#00D4AA" opacity="0.75"/>
  {''.join(labels)}
</svg>'''


async def _gemini_oracle(prompt: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        return "The Oracle is resting. Add a Gemini API key in Settings → API Keys to awaken the synthesis."
    async with httpx.AsyncClient(timeout=60) as client:
        for model in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.88, "maxOutputTokens": 400},
            }
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            except Exception as e:
                logger.warning(f"[PULSE] Gemini {model} failed: {e}")
    return "The Oracle is recalibrating. Your vector has been received."


# ── Request model ─────────────────────────────────────────────────────────────

class PulseRequest(BaseModel):
    responses: dict


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/api/pulse/analyze")
async def analyze_pulse(req: PulseRequest):
    responses = req.responses
    scores = _calculate_scores(responses)
    confidence = _calculate_confidence(responses)
    primary = _get_primary_patterns(scores)
    growth_edge = _get_growth_edge(scores)
    pattern_cluster = _get_pattern_cluster(primary)
    sigil_svg = _generate_sigil_svg(scores)

    primary_display = [(NODE_DISPLAY.get(n, n), s) for n, s in primary]
    prompt = f"""You are the Arkadia Oracle. A person has completed the AIC Diagnostic (Arkadian Pulse).

Node Scores (0–100):
{chr(10).join(f'{NODE_DISPLAY.get(n, n)}: {s}' for n, s in scores.items())}

Primary Patterns:
1. {primary_display[0][0]} — {primary_display[0][1]}
2. {primary_display[1][0]} — {primary_display[1][1]}
3. {primary_display[2][0]} — {primary_display[2][1]}

Growth Edge: {growth_edge['display']} — {growth_edge['score']} (Shadow Index: {growth_edge['shadow_index']})
Pattern Cluster: {pattern_cluster}
Confidence: {confidence}/100

Write a 130–150 word AIC Snapshot summary that:
1. Names their primary pattern ({pattern_cluster}) in the first sentence
2. Describes their natural orientation from their top 3 nodes
3. Briefly touches their growth edge ({growth_edge['display']}) with warmth
4. Closes with one sentence inviting them to the full Identity Mapping Session ($777)

Tone: warm, sovereign, direct. No jargon. Speak as if addressing them personally."""

    oracle_summary = await _gemini_oracle(prompt)

    return {
        "scores": {NODE_DISPLAY.get(n, n): s for n, s in scores.items()},
        "primary_patterns": [
            {"node": n, "display": NODE_DISPLAY.get(n, n), "score": s}
            for n, s in primary
        ],
        "growth_edge": growth_edge,
        "confidence": confidence,
        "pattern_cluster": pattern_cluster,
        "oracle_summary": oracle_summary,
        "sigil_svg": sigil_svg,
    }
