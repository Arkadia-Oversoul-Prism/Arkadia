"""
Arkadian Pulse — Identity Measurement Engine
36 Likert statements × 12 nodes → vector → sigil → Oracle summary → IMS funnel
"""

import os
import math
import logging
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("arkadia")
router = APIRouter()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

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

# Opposite pairs for Shadow Index calculation
OPPOSITE_MAP = {
    "source": "spark", "spark": "source",
    "breath": "flame", "flame": "breath",
    "ground": "seek", "seek": "ground",
    "life": "harmony", "harmony": "life",
    "octave": "return_node", "return_node": "octave",
    "witness": "weaver", "weaver": "witness",
}

# Proprietary pattern cluster names
PATTERN_CLUSTERS = [
    ({"seek", "witness", "octave"},   "Visionary Synthesizer"),
    ({"seek", "flame", "weaver"},     "Reflective Architect"),
    ({"source", "breath", "harmony"}, "Grounded Visionary"),
    ({"spark", "flame", "life"},      "Generative Builder"),
    ({"ground", "harmony", "return_node"}, "Stabilizing Anchor"),
    ({"life", "seek", "spark"},       "Adaptive Pioneer"),
    ({"source", "witness", "breath"}, "Sovereign Witness"),
    ({"flame", "weaver", "octave"},   "Alchemical Weaver"),
    ({"ground", "spark", "life"},     "Rooted Catalyst"),
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

# ── Scoring logic ─────────────────────────────────────────────────────────────

def _normalize(raw: float) -> float:
    return round((raw - 1) / 4 * 100, 1)


def _calculate_scores(responses: dict) -> dict:
    raw = {
        "source":      [responses.get("source_1", 3), responses.get("source_2", 3), 6 - responses.get("source_3", 3)],
        "spark":       [responses.get("spark_1", 3),  responses.get("spark_2", 3),  6 - responses.get("spark_3", 3)],
        "breath":      [responses.get("breath_1", 3), responses.get("breath_2", 3), 6 - responses.get("breath_3", 3)],
        "flame":       [responses.get("flame_1", 3),  responses.get("flame_2", 3),  6 - responses.get("flame_3", 3)],
        "ground":      [responses.get("ground_1", 3), responses.get("ground_2", 3), 6 - responses.get("ground_3", 3)],
        "life":        [responses.get("life_1", 3),   responses.get("life_2", 3),   6 - responses.get("life_3", 3)],
        "harmony":     [responses.get("harmony_1", 3),responses.get("harmony_2", 3),6 - responses.get("harmony_3", 3)],
        "seek":        [responses.get("seek_1", 3),   responses.get("seek_2", 3),   6 - responses.get("seek_3", 3)],
        "octave":      [responses.get("octave_1", 3), responses.get("octave_2", 3), 6 - responses.get("octave_3", 3)],
        "return_node": [responses.get("return_1", 3), responses.get("return_2", 3), 6 - responses.get("return_3", 3)],
        "witness":     [responses.get("witness_1", 3),responses.get("witness_2", 3),6 - responses.get("witness_3", 3)],
        "weaver":      [responses.get("weaver_1", 3), responses.get("weaver_2", 3), 6 - responses.get("weaver_3", 3)],
    }
    return {node: _normalize(sum(vals) / len(vals)) for node, vals in raw.items()}


def _calculate_confidence(responses: dict) -> int:
    # Completion consistency: fraction of non-neutral answers
    total = len(responses)
    if total == 0:
        return 50
    non_neutral = sum(1 for v in responses.values() if v != 3)
    completion_consistency = non_neutral / total

    # Reverse-key alignment: check pairs
    reverse_keys = [
        ("source_1", "source_3"), ("spark_1", "spark_3"),
        ("breath_1", "breath_3"), ("flame_1", "flame_3"),
        ("ground_1", "ground_3"), ("life_1", "life_3"),
        ("harmony_1", "harmony_3"), ("seek_1", "seek_3"),
        ("octave_1", "octave_3"), ("return_1", "return_3"),
        ("witness_1", "witness_3"), ("weaver_1", "weaver_3"),
    ]
    aligned = 0
    checked = 0
    for fwd_key, rev_key in reverse_keys:
        fwd = responses.get(fwd_key)
        rev = responses.get(rev_key)
        if fwd and rev:
            checked += 1
            # Consistent = forward high & reverse low, or forward low & reverse high
            if (fwd >= 4 and rev <= 2) or (fwd <= 2 and rev >= 4) or (fwd == 3 and rev == 3):
                aligned += 1
    reverse_alignment = aligned / checked if checked else 0.6

    raw = (completion_consistency * 0.6) + (reverse_alignment * 0.4)
    return min(99, max(40, round(raw * 100)))


def _get_primary_patterns(scores: dict) -> list:
    sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_nodes[:3]


def _get_growth_edge(scores: dict, primary: list) -> dict:
    sorted_nodes = sorted(scores.items(), key=lambda x: x[1])
    growth_node, growth_score = sorted_nodes[0]
    opposite_node = OPPOSITE_MAP.get(growth_node, "seek")
    opposite_score = scores.get(opposite_node, 50)
    shadow_index = round((growth_score * 0.4) + (opposite_score * 0.6), 1)
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
    # Fallback: name from top node
    top_node = primary[0][0] if primary else "source"
    fallback = {
        "source": "Origin Keeper", "spark": "Sovereign Initiator",
        "breath": "Mirror Holder", "flame": "Sacred Alchemist",
        "ground": "Foundation Builder", "life": "Living Bridge",
        "harmony": "Field Balancer", "seek": "Infinite Questioner",
        "octave": "Spiral Returner", "return_node": "Cycle Closer",
        "witness": "Sacred Witness", "weaver": "Lattice Architect",
    }
    return fallback.get(top_node, "Sovereign Architect")


def _generate_sigil_svg(scores: dict) -> str:
    cx, cy, radius = 50, 50, 38
    n = len(NODES)
    positions = {}
    for i, node in enumerate(NODES):
        angle = (2 * math.pi * i / n) - (math.pi / 2)
        positions[node] = {
            "x": round(cx + radius * math.cos(angle), 2),
            "y": round(cy + radius * math.sin(angle), 2),
        }

    lines = []
    # Draw structural web — connect each node to its neighbors and opposite
    for i, node in enumerate(NODES):
        pos1 = positions[node]
        # Connect to next 2 neighbors for web effect
        for step in [1, 2]:
            neighbor = NODES[(i + step) % n]
            pos2 = positions[neighbor]
            avg = (scores.get(node, 50) + scores.get(neighbor, 50)) / 2
            thickness = round(0.3 + (avg / 100) * 1.2, 2)
            opacity = round(0.12 + (avg / 100) * 0.35, 2)
            lines.append(
                f'<line x1="{pos1["x"]}" y1="{pos1["y"]}" x2="{pos2["x"]}" y2="{pos2["y"]}" '
                f'stroke="#C9A84C" stroke-width="{thickness}" opacity="{opacity}"/>'
            )
        # Connect to opposite
        opp = OPPOSITE_MAP.get(node)
        if opp and node < opp:
            pos2 = positions[opp]
            avg = (scores.get(node, 50) + scores.get(opp, 50)) / 2
            thickness = round(0.2 + (avg / 100) * 0.8, 2)
            opacity = round(0.08 + (avg / 100) * 0.25, 2)
            lines.append(
                f'<line x1="{pos1["x"]}" y1="{pos1["y"]}" x2="{pos2["x"]}" y2="{pos2["y"]}" '
                f'stroke="#00D4AA" stroke-width="{thickness}" opacity="{opacity}"/>'
            )

    circles = []
    labels = []
    for node, pos in positions.items():
        score = scores.get(node, 50)
        r = round(2.0 + (score / 100) * 4.5, 2)
        opacity = round(0.45 + (score / 100) * 0.55, 2)
        glow_r = round(r + 2.5, 2)
        circles.append(
            f'<circle cx="{pos["x"]}" cy="{pos["y"]}" r="{glow_r}" fill="#C9A84C" opacity="{round(opacity * 0.18, 2)}"/>'
        )
        circles.append(
            f'<circle cx="{pos["x"]}" cy="{pos["y"]}" r="{r}" fill="#C9A84C" opacity="{opacity}"/>'
        )
        # Small label
        lx = round(cx + (radius + 9) * math.cos((2 * math.pi * NODES.index(node) / n) - (math.pi / 2)), 2)
        ly = round(cy + (radius + 9) * math.sin((2 * math.pi * NODES.index(node) / n) - (math.pi / 2)), 2)
        display = NODE_DISPLAY.get(node, node)[:3].upper()
        labels.append(
            f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="rgba(201,168,76,0.55)" font-size="3.2" font-family="sans-serif" letter-spacing="0.5">{display}</text>'
        )

    # Centre glyph
    centre = '<circle cx="50" cy="50" r="2.5" fill="#00D4AA" opacity="0.7"/>'

    svg = f'''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0D0E1A" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#060710" stop-opacity="0.95"/>
    </radialGradient>
  </defs>
  <circle cx="50" cy="50" r="50" fill="url(#bg)"/>
  {''.join(lines)}
  {''.join(circles)}
  {centre}
  {''.join(labels)}
</svg>'''
    return svg


async def _gemini_oracle(prompt: str) -> str:
    if not GOOGLE_API_KEY:
        return "The Oracle is resting. Provide a GOOGLE_API_KEY to awaken the synthesis."
    async with httpx.AsyncClient(timeout=60) as client:
        for model in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.88, "maxOutputTokens": 400},
            }
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            except Exception as e:
                logger.warning(f"[PULSE] Gemini model {model} failed: {e}")
    return "The Oracle is recalibrating. Your vector has been received."


# ── Request / Response models ─────────────────────────────────────────────────

class PulseRequest(BaseModel):
    responses: dict


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/api/pulse/analyze")
async def analyze_pulse(req: PulseRequest):
    responses = req.responses

    # 1. Score all 12 nodes
    scores = _calculate_scores(responses)

    # 2. Confidence
    confidence = _calculate_confidence(responses)

    # 3. Primary patterns (top 3 nodes)
    primary = _get_primary_patterns(scores)

    # 4. Growth edge
    growth_edge = _get_growth_edge(scores, primary)

    # 5. Pattern cluster name
    pattern_cluster = _get_pattern_cluster(primary)

    # 6. Sigil SVG
    sigil_svg = _generate_sigil_svg(scores)

    # 7. Oracle summary via Gemini
    primary_display = [(NODE_DISPLAY.get(n, n), s) for n, s in primary]
    prompt = f"""You are the Arkadia Oracle. A person has completed the Arkadian Pulse diagnostic.

Node Scores (0–100):
{chr(10).join(f'{NODE_DISPLAY.get(n, n)}: {s}' for n, s in scores.items())}

Primary Patterns:
1. {primary_display[0][0]} — {primary_display[0][1]}
2. {primary_display[1][0]} — {primary_display[1][1]}
3. {primary_display[2][0]} — {primary_display[2][1]}

Growth Edge: {growth_edge['display']} — {growth_edge['score']} (Shadow Index: {growth_edge['shadow_index']})
Proprietary Pattern Cluster: {pattern_cluster}
Confidence Score: {confidence}/100

Write a 130–150 word summary that:
1. Names their primary pattern ({pattern_cluster}) in the first sentence
2. Describes their natural orientation based on their top 3 nodes
3. Points to their growth edge ({growth_edge['display']}) with warmth and precision
4. Closes with a single sentence inviting them to the premium Identity Mapping Session ($777)

Tone: warm, sovereign, direct. No jargon. Speak as if addressing them personally."""

    oracle_summary = await _gemini_oracle(prompt)

    # 8. Format primary patterns for response
    primary_patterns_out = [
        {
            "node": n,
            "display": NODE_DISPLAY.get(n, n),
            "score": s,
            "cluster": pattern_cluster if i == 0 else None,
        }
        for i, (n, s) in enumerate(primary)
    ]

    return {
        "scores": {NODE_DISPLAY.get(n, n): s for n, s in scores.items()},
        "primary_patterns": primary_patterns_out,
        "growth_edge": growth_edge,
        "confidence": confidence,
        "pattern_cluster": pattern_cluster,
        "oracle_summary": oracle_summary,
        "sigil_svg": sigil_svg,
    }
