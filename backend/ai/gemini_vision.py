"""
Gemini multimodal: cooling-tower cue from a satellite image chip.

Uses the Google Gen AI SDK (`google-genai`). Set GEMINI_API_KEY (see services.settings).
"""

from __future__ import annotations

import json
import logging
import re

from services.settings import get_settings

logger = logging.getLogger(__name__)


def analyze_cooling_tower_from_image(png_bytes: bytes) -> tuple[bool, float] | None:
    """
    Returns (detected, confidence in 0..1) or None if API unavailable / parse failed.
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

    prompt = """You are assisting a water-efficiency prospecting tool for commercial/industrial sites.
Look at this satellite or aerial image (RGB). Answer ONLY valid JSON, no markdown:
{"cooling_tower_likely": true or false, "confidence": number from 0 to 1, "reason": "one short phrase"}

cooling_tower_likely means visible large cooling tower(s) or dense cooling infrastructure typical of industrial/HVAC plants (not small residential AC)."""

    try:
        with genai.Client(api_key=settings.gemini_api_key) as client:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                ],
            )
        text = (getattr(response, "text", None) or "").strip()
        return _parse_tower_json(text)
    except Exception as e:
        logger.warning("Gemini vision call failed: %s", e)
        return None


def _parse_tower_json(text: str) -> tuple[bool, float] | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    raw = m.group(0)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    detected = bool(data.get("cooling_tower_likely"))
    conf = float(data.get("confidence", 0.5))
    conf = max(0.0, min(1.0, conf))
    return detected, conf
