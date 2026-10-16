"""Showroom face analysis via Google Gemini (plain REST through httpx).

Read-only by design: it looks at a photo and describes skin tone / undertone and suggests
shades. It never edits or returns an image - the user applies shades themselves in the app.
The API key stays server-side (never ship it in the Android app).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.config import get_settings

log = logging.getLogger(__name__)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_DELAYS = (1.0, 3.0)
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

SYSTEM_PROMPT = """You are a professional makeup artist analysing ONE portrait photo.
Describe only what is visible. Do not identify the person. Be accurate for deep skin tones.
Suggest shades that genuinely suit the skin depth and undertone (foundation must match the
skin as it appears in the photo's lighting). Respond with JSON only."""

USER_PROMPT = """Analyse this face and return JSON with:
- skin_depth: integer 1 (very fair) to 10 (deepest)
- undertone: one of "warm", "cool", "neutral", "olive"
- skin_hex: the average natural skin colour of cheeks/forehead as "#RRGGBB" (ignore shadows/highlights)
- lip_hex: the natural lip colour as "#RRGGBB"
- face_shape: one of "oval","round","square","heart","long","diamond"
- photo_warnings: list of short strings for problems that would make makeup placement look off
  (e.g. "face turned sideways", "strong colour cast", "face partly covered", "low light"). Empty if fine.
- suggestions: 2-3 items EACH for categories "foundation","lipstick","blush","eyebrow";
  each item {category, name (a short generic shade name like "Warm Cocoa" - never a brand or product name), hex ("#RRGGBB"), reason (max 12 words)}
- summary: one friendly sentence (max 25 words) about the look that would suit this face."""


class Suggestion(BaseModel):
    category: str
    name: str
    hex: str
    reason: str = ""


class FaceAnalysis(BaseModel):
    skin_depth: int = Field(ge=1, le=10)
    undertone: str
    skin_hex: str
    lip_hex: str
    face_shape: str
    photo_warnings: list[str] = []
    suggestions: list[Suggestion] = []
    summary: str = ""


class ShowroomUnavailable(Exception):
    """Gemini is not configured, unreachable, or declined/garbled the request."""

    def __init__(self, message: str, *, configured: bool = True):
        super().__init__(message)
        self.configured = configured


async def analyze_face(image_bytes: bytes, media_type: str, *, client: httpx.AsyncClient | None = None) -> FaceAnalysis:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ShowroomUnavailable("Showroom analysis is not configured.", configured=False)

    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": media_type, "data": base64.b64encode(image_bytes).decode()}},
                    {"text": USER_PROMPT},
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3,
            "maxOutputTokens": 4096,
        },
    }

    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))
    try:
        response = None
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                # Key in a header, never the URL, so it can't leak into access logs.
                response = await client.post(
                    f"{BASE_URL}/models/{settings.gemini_model}:generateContent",
                    headers={"x-goog-api-key": settings.gemini_api_key},
                    json=body,
                )
                if response.status_code not in RETRY_STATUSES:
                    break
                log.warning("gemini transient status %s (attempt %d)", response.status_code, attempt + 1)
            except httpx.HTTPError as exc:
                response = None
                log.warning("gemini transport error %s (attempt %d)", type(exc).__name__, attempt + 1)
            if attempt < len(RETRY_DELAYS):
                await asyncio.sleep(RETRY_DELAYS[attempt])
    finally:
        if owns_client:
            await client.aclose()

    if response is None:
        raise ShowroomUnavailable("Could not reach the AI provider.")
    if response.status_code != 200:
        log.error("gemini status error %s", response.status_code)
        raise ShowroomUnavailable(f"AI provider returned HTTP {response.status_code}.")

    data = response.json()
    candidates = data.get("candidates") or []
    if data.get("promptFeedback", {}).get("blockReason") or not candidates:
        raise ShowroomUnavailable("The AI provider declined this photo.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p["text"] for p in parts if "text" in p and not p.get("thought"))
    try:
        analysis = FaceAnalysis.model_validate(json.loads(text))
    except (ValueError, ValidationError) as exc:
        log.error("gemini returned unusable analysis: %s", type(exc).__name__)
        raise ShowroomUnavailable("The AI response could not be understood.") from exc

    # Never hand the app a colour it can't parse.
    analysis.suggestions = [s for s in analysis.suggestions if HEX_RE.match(s.hex)]
    if not HEX_RE.match(analysis.skin_hex) or not HEX_RE.match(analysis.lip_hex):
        raise ShowroomUnavailable("The AI response had invalid colours.")
    return analysis
