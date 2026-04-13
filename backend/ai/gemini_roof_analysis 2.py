"""
Gemini Vision: full rooftop + cooling-tower read from a satellite image (e.g. Static Maps PNG).

Uses the same ``GEMINI_API_KEY`` / model as ``ai/gemini_vision.py``.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from services.settings import get_settings

logger = logging.getLogger(__name__)

ROOF_PROMPT = """Analyze this satellite image of a commercial building rooftop.

Determine:
1. Whether the roof appears extremely large (>100,000 sq ft)
2. Whether cooling towers or large HVAC water systems appear present

Return JSON only (no markdown), exactly this shape:
{
  "roof_large": true or false,
  "cooling_tower_detected": true or false,
  "roof_confidence": number from 0 to 1,
  "cooling_tower_confidence": number from 0 to 1,
  "estimated_roof_sqft": number (your best estimate of total roof footprint in square feet),
  "reasoning": string (brief)
}"""


def analyze_building_satellite(image_bytes: bytes) -> dict[str, Any] | None:
    """
    Send ``image_bytes`` (PNG) to Gemini; parse structured JSON.

    Returns a dict with keys roof_large, cooling_tower_detected, roof_confidence,
    cooling_tower_confidence, estimated_roof_sqft, reasoning — or None on failure.
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except ImportError:
        logger.warning("google-genai not installed")
        return None

    try:
        with genai.Client(api_key=settings.gemini_api_key) as client:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Part.from_text(text=ROOF_PROMPT),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ],
            )
        text = (getattr(response, "text", None) or "").strip()
        return _parse_roof_json(text)
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or ("quota" in err.lower() and "exceed" in err.lower()):
            logger.warning("Gemini roof analysis hit quota/rate limit; falling back to catalog/mock.")
        else:
            logger.warning("Gemini roof analysis failed: %s", e)
        return None


def _parse_roof_json(text: str) -> dict[str, Any] | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    raw = m.group(0)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    roof_large = bool(data.get("roof_large"))
    tower = bool(data.get("cooling_tower_detected"))
    roof_conf = float(data.get("roof_confidence", 0.5))
    tower_conf = float(data.get("cooling_tower_confidence", 0.5))
    roof_conf = max(0.0, min(1.0, roof_conf))
    tower_conf = max(0.0, min(1.0, tower_conf))

    est = data.get("estimated_roof_sqft")
    try:
        estimated_roof_sqft = float(est) if est is not None else 0.0
    except (TypeError, ValueError):
        estimated_roof_sqft = 0.0

    reasoning = data.get("reasoning")
    if reasoning is not None and not isinstance(reasoning, str):
        reasoning = str(reasoning)

    return {
        "roof_large": roof_large,
        "cooling_tower_detected": tower,
        "roof_confidence": roof_conf,
        "cooling_tower_confidence": tower_conf,
        "estimated_roof_sqft": estimated_roof_sqft,
        "reasoning": (reasoning or "").strip(),
    }
