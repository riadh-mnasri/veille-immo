from __future__ import annotations
import re
import unicodedata
from abc import ABC, abstractmethod

import httpx

from config import SEARCH
from models import Listing

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def normalize(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode().lower()


def commune_match(commune: str) -> bool:
    norm = normalize(commune)
    return any(normalize(c) in norm or norm in normalize(c) for c in SEARCH["communes"])


def is_excluded(text: str) -> bool:
    low = text.lower()
    return any(mot in low for mot in SEARCH["mots_exclus"])


def parse_price(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def parse_surface(text: str) -> float:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m", text, re.IGNORECASE)
    return float(m.group(1).replace(",", ".")) if m else 0.0


def parse_chambres(text: str) -> int:
    m = re.search(r"(\d+)\s*(?:chambre|ch\.)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


class BaseScraper(ABC):
    source: str = ""

    def new_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True)

    @abstractmethod
    async def fetch(self) -> list[Listing]:
        ...
