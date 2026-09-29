import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(
    BASE_DIR / ".env"
)


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-change-me"
    )

    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        str(BASE_DIR / "pocketsmart.db")
    )

    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY",
        ""
    ).strip()

    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    ).strip()
