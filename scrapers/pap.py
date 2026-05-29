from __future__ import annotations
import logging
import re

from bs4 import BeautifulSoup

from config import SEARCH
from models import Listing
from scrapers.base import BaseScraper, is_excluded, parse_price, parse_surface, parse_chambres

logger = logging.getLogger(__name__)

# Geo IDs PAP — via https://www.pap.fr/json/ac-geo?q={commune}
COMMUNES_PAP = {
    "ermont-95120":                 43399,
    "eaubonne-95600":               43526,
    "enghien-les-bains-95880":      43570,
    "sannois-95110":                43407,
    "deuil-la-barre-95170":         43398,
    "soisy-sous-montmorency-95230": 43428,
    "montlignon-95680":             43538,
    "margency-95580":               43507,
    "saint-prix-95390":             43558,
    "andilly-95580":                43553,
}

_HREF_RE  = re.compile(r"/annonces/maison-([a-z][a-z0-9\-]+)-(\d{5})-r(\d+)", re.I)
_PRICE_RE = re.compile(r"\d{2,3}[\.\s]\d{3}\s*€")


class PAPScraper(BaseScraper):
    source = "pap"

    async def fetch(self) -> list[Listing]:
        seen: set[str] = set()
        listings: list[Listing] = []

        async with self.new_client() as client:
            for slug, geo_id in COMMUNES_PAP.items():
                url = (
                    f"https://www.pap.fr/annonce/ventes-maisons-{slug}"
                    f"-g{geo_id}-budgetmax-{SEARCH['budget_max']}"
                )
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.debug(f"[PAP] {slug}: {e}")
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Partir du PRIX → remonter pour trouver le lien de l'annonce
                for price_text in soup.find_all(string=_PRICE_RE):
                    try:
                        listing = self._parse_from_price(price_text)
                        if listing and listing.id not in seen:
                            seen.add(listing.id)
                            listings.append(listing)
                    except Exception as e:
                        logger.debug(f"[PAP] price parse: {e}")

        logger.info(f"[PAP] {len(listings)} annonce(s)")
        return listings

    def _parse_from_price(self, price_text) -> Listing | None:
        raw_price = parse_price(str(price_text))
        if not raw_price or raw_price > SEARCH["budget_max"]:
            return None

        # Remonter depuis le nœud prix pour trouver le bloc complet de l'annonce
        container = price_text.parent
        listing_link = None
        for _ in range(15):
            if container is None:
                break
            link = container.find("a", href=_HREF_RE)
            if link:
                listing_link = link
                break
            container = container.parent

        if listing_link is None:
            return None

        href = listing_link.get("href", "")
        m = _HREF_RE.match(href)
        if not m:
            return None

        commune_slug = m.group(1)
        code_postal  = m.group(2)
        listing_id   = m.group(3)
        commune = commune_slug.replace("-", " ").title()

        text = container.get_text(" ", strip=True) if container else ""
        title = listing_link.get_text(strip=True)[:200] or f"Maison {commune}"

        if is_excluded(title):
            return None

        surface  = parse_surface(text)
        chambres = parse_chambres(text)
        if chambres and chambres < SEARCH["chambres_min"]:
            return None

        img = container.find("img") if container else None
        photos = [img["src"]] if img and img.get("src") else []

        return Listing(
            id=f"pap:{listing_id}",
            source="pap",
            url=f"https://www.pap.fr{href}",
            title=title,
            price=raw_price,
            surface=surface or None,
            chambres=chambres or None,
            commune=commune,
            code_postal=code_postal,
            description=text[:600],
            photos=photos,
        )
