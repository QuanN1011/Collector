"""
Gemini Vision for Static Maps satellite chips (hackathon address pipeline).

Uses ``GEMINI_API_KEY`` via ``get_settings().gemini_api_key`` and ``google-genai``.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from services.settings import get_settings

logger = logging.getLogger(__name__)


class GeminiQuotaError(Exception):
    """Raised when Gemini returns 429 / RESOURCE_EXHAUSTED (rate limit or free-tier quota)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class GeminiOverloadedError(Exception):
    """Raised when Gemini returns 503 UNAVAILABLE (model temporarily at capacity)."""

    def __init__(self, message: str, retry_after: int | None = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _retry_after_seconds(exc: BaseException) -> int | None:
    m = re.search(r"retry in ([\d.]+)\s*s", str(exc), re.IGNORECASE)
    if m:
        return max(1, int(float(m.group(1))))
    return None


def _is_gemini_quota_error(exc: BaseException) -> bool:
    s = str(exc).lower()
    if "429" in s or "resource_exhausted" in s:
        return True
    if "quota" in s and ("exceed" in s or "exhausted" in s):
        return True
    return False


def _is_gemini_overloaded_error(exc: BaseException) -> bool:
    """503 UNAVAILABLE / high demand — Google's side is temporarily saturated for this model."""
    s = str(exc).lower()
    if "unavailable" in s and ("503" in s or "status" in s):
        return True
    if "high demand" in s or "try again later" in s:
        return True
    if "503" in s and "gemini" in s:
        return True
    return False


def _short_error_message(exc: BaseException, max_len: int = 320) -> str:
    msg = str(exc).strip()
    if len(msg) <= max_len:
        return msg
    return msg[: max_len - 1].rsplit(" ", 1)[0] + "…"

_PROMPT = """Analyze this satellite image of a commercial building roof.
Estimate:
1) roof size as one of: small, medium, large (relative to typical commercial flat roofs in the image)
2) whether cooling towers or large evaporative cooling infrastructure are visible
3) your overall confidence as a number from 0 to 1

Return ONLY valid JSON, no markdown, in this exact shape:
{"roof_estimate": "small"|"medium"|"large", "cooling_tower_detected": true or false, "confidence": 0.0-1.0, "roof_area_sqft_estimate": null or a number}

If you cannot estimate square feet, set roof_area_sqft_estimate to null."""


def _parse_analysis_json(text: str) -> dict[str, Any] | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def analyze_building_image(image_url: str) -> dict[str, Any]:
    """
    Download the image from ``image_url`` and run Gemini Vision.

    Returns: roof_estimate, cooling_tower_detected, confidence, roof_area_sqft_estimate (optional).
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        ir = client.get(image_url)
        ir.raise_for_status()
        blob = ir.content
        mime = (ir.headers.get("content-type") or "image/png").split(";")[0].strip()

    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except ImportError as e:
        raise RuntimeError("google-genai package is required for Gemini vision") from e

    try:
        with genai.Client(api_key=settings.gemini_api_key) as gen_client:
            response = gen_client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Part.from_text(text=_PROMPT),
                    types.Part.from_bytes(
                        data=blob,
                        mime_type=mime if mime.startswith("image/") else "image/png",
                    ),
                ],
            )
        text = (getattr(response, "text", None) or "").strip()
    except Exception as e:
        logger.warning("Gemini building analysis failed: %s", e)
        if _is_gemini_quota_error(e):
            raise GeminiQuotaError(
                "Gemini API quota or rate limit exceeded. The free tier allows only a small number of requests per day "
                "per model (often ~20 for newer models). Options: wait and retry, set GEMINI_MODEL=gemini-2.0-flash in "
                "backend/.env, or enable billing on your Google AI project. See https://ai.google.dev/gemini-api/docs/rate-limits",
                retry_after=_retry_after_seconds(e),
            ) from e
        if _is_gemini_overloaded_error(e):
            raise GeminiOverloadedError(
                "Gemini reports this model is temporarily overloaded (high demand on Google's side). "
                "Wait 1–2 minutes and retry, or set GEMINI_MODEL=gemini-2.0-flash in backend/.env to try another model.",
                retry_after=_retry_after_seconds(e) or 60,
            ) from e
        raise RuntimeError(f"Gemini vision call failed: {_short_error_message(e)}") from e

    parsed = _parse_analysis_json(text)
    if not parsed:
        raise RuntimeError("Could not parse JSON from Gemini response")

    est = str(parsed.get("roof_estimate", "medium")).lower().strip()
    if est not in ("small", "medium", "large"):
        est = "medium"

    conf = float(parsed.get("confidence", 0.5))
    conf = max(0.0, min(1.0, conf))

    return {
        "roof_estimate": est,
        "cooling_tower_detected": bool(parsed.get("cooling_tower_detected", False)),
        "confidence": conf,
        "roof_area_sqft_estimate": parsed.get("roof_area_sqft_estimate"),
    }
