"""Vercel's Python runtime auto-detects an ASGI `app` object in files under api/ and
serves it as a serverless function - this file just re-exports the real FastAPI app
defined in app/main.py so nothing about the app itself needs to know it's on Vercel."""

from app.main import app

__all__ = ["app"]
