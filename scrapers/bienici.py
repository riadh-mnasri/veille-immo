from __future__ import annotations
import json
import logging
import urllib.parse

from config import SEARCH
from models import Listing
from scrapers.base import BaseScraper, commune_match, is_excluded

logger = logging.getLogger(__name__)

# BienIci attend le filtre complet (size + from inclus) dans un seul param JSON
_FILTER = json.dumps({
    "size": 24,
    "from": 0,
    "filters": {
        "status": "available",
        "active": True,
        "ad_type": "transaction",
        "real_estate_types": ["house"],
        "price": {"max": SEARCH["budget_max"]},
        "minRooms": SEARCH["chambres_min"],
        "departments": ["95"],
    },
})

BIENICI_URL = f"https://www.bienici.com/realEstateAds.json?filters={urllib.parse.quote(_FILTER)}"


class BienIciScraper(BaseScraper):
    source = "bienici"

    async def fetch(self) -> list[Listing]:
        async with self.new_client() as client:
            try:
                resp = await client.get(BIENICI_URL, headers={
                    **dict(client.headers),
                    "Accept": "application/json",
                    "Referer": "https://www.bienici.com/",
                    "Origin": "https://www.bienici.com",
                })
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"[BienIci] Erreur: {e}")
                return []

        listings: list[Listing] = []
        for ad in data.get("realEstateAds", []):
            try:
                listing = self._parse_ad(ad)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"[BienIci] Parsing: {e}")

        logger.info(f"[BienIci] {len(listings)} annonce(s)")
        return listings

    def _parse_ad(self, ad: dict) -> Listing | None:
        ad_id = str(ad.get("id", ""))
        price = ad.get("price", 0) or 0
        if not price or price > SEARCH["budget_max"]:
            return None

        city = ad.get("city", "") or ""
        if not commune_match(city):
            return None

        title = ad.get("title", "") or f"Maison {city}"
        if is_excluded(title):
            return None

        bedrooms = ad.get("bedroomsQuantity", 0) or 0
        rooms = ad.get("roomsQuantity", 0) or 0
        chambres = bedrooms or max(0, rooms - 1)
        if chambres and chambres < SEARCH["chambres_min"]:
            return None

        surface = ad.get("surfaceArea", 0) or 0
        photos = [p["url"] for p in ad.get("photos", [])[:5] if p.get("url")]

        return Listing(
            id=f"bienici:{ad_id}",
            source="bienici",
            url=f"https://www.bienici.com/annonce/{ad_id}",
            title=title,
            price=int(price),
            surface=float(surface) if surface else None,
            chambres=chambres or None,
            commune=city,
            code_postal=ad.get("postalCode", ""),
            description=(ad.get("description", "") or "")[:800],
            photos=photos,
        )
