"""
Configuración del sistema - Carga variables desde .env
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ─── Google Sheets ───
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_SHEET_ID: str = ""

    # ─── Email SMTP ───
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_NOTIFY_TO: str = ""

    # ─── CORS ───
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
