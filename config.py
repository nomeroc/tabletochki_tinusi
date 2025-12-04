# config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str
    db_path: str = "pills.db"
    strings_path: str = "strings.json"
    timezone: str = os.getenv("TZ", "UTC")


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
)

if not settings.bot_token:
    raise RuntimeError("BOT_TOKEN is not set in .env")
