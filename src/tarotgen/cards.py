"""Shared card loading utilities."""

import json
from pathlib import Path

import yaml

DOCS_DIR = Path("./docs")
DOCS_CARDS_DIR = DOCS_DIR / "cards"
CARDS_YML = Path("cards.yml")
MEANINGS_JSON = Path("meanings.json")
MEANINGS_ORIGINAL_JSON = Path("meanings_original.json")


def load_cards():
    with open(CARDS_YML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("cards", [])


def load_meanings(path=MEANINGS_JSON):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def id_to_tarot_name(cid: str) -> str:
    """Convert card ID like '00-the-fool' or 'ace-of-wands' to 'The Fool' or 'Ace of Wands'."""
    parts = cid.split("-")
    if parts[0].isdigit():
        parts = parts[1:]
    return " ".join(p.title() for p in parts)
