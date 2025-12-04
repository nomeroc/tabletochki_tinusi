# strings.py
import json
from dataclasses import dataclass
from typing import Dict, List
from config import settings


@dataclass
class Strings:
    buttons: Dict[str, str]
    texts: Dict[str, str]
    reminder_phrases: List[str]


def load_strings(path: str = None) -> Strings:
    path = path or settings.strings_path
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Strings(
        buttons=data.get("buttons", {}),
        texts=data.get("texts", {}),
        reminder_phrases=data.get("reminder_phrases", []),
    )


strings = load_strings()
