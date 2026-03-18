"""Centralised configuration — loaded once at import time."""

import os
from dotenv import load_dotenv

load_dotenv()                        # backend/.env
load_dotenv(dotenv_path="../.env")   # project root .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Add it to backend/.env or the project root .env file."
    )
