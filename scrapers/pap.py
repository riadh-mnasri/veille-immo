from __future__ import annotations
import logging
import re

from bs4 import BeautifulSoup

from config import SEARCH
from models import Listing
from scrapers.base import BaseScraper, commune_match, is_excluded, parse_price, parse_surface, parse_chambres

logger = logging.getLogger(__name__)

SEARCH_URL = f"https://www.pap.fr/annonce/ventes-maisons-val-d-oise-g439-budgetmax-{SEARCH['budget_max']}"
# Pattern d'URL individuelle PAP : /annonce/ventes-maisons-95120-ermont-r431289.htm
_HREF_RE = re.compile(r"^/annonce/ventes-maisons-(\d{5})-([a-z][a-z0-9\-]+)-r(\d+)", re.I)


class PAPScraper(BaseScraper):
    source = "pap"

    async def fetch(self) -> list[Listing]:
        async with self.new_client() as client:
            try:
                resp = await client.get(SEARCH_URL)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"[PAP] {e}")
                return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Les annonces PAP sont des <a href="/annonce/ventes-maisons-95xxx-...">
        seen: set[str] = set()
        listings: list[Listing] = []

        for link in soup.find_all("a", href=_HREF_RE):
            href = link.get("href", "")
            if href in seen:
                continue
            seen.add(href)
            try:
                listing = self._parse_link(link, href)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"[PAP] {e}")

        logger.info(f"[PAP] {len(listings)} annonce(s)")
        return listings

    def _parse_link(self, link, href: str) -> Listing | None:
        m = _HREF_RE.match(href)
        if not m:
            return None

        code_postal = m.group(1)
        commune_slug = m.group(2)
        listing_id = m.group(3)
        commune = commune_slug.replace("-", " ").title()

        # Filtre géographique : commune OU code postal dans notre liste
        if not commune_match(commune) and code_postal not in SEARCH["codes_postaux"]:
            return None

        url = f"https://www.pap.fr{href}"

        # Remonter dans le DOM pour trouver le bloc complet de l'annonce
        container = link
        for _ in range(5):
            parent = container.parent
            if parent is None:
                break
            text = parent.get_text(" ", strip=True)
            if "€" in text and ("m²" in text or "pièce" in text or "chambre" in text):
                container = parent
                break
            container = parent

        text = container.get_text(" ", strip=True)

        price = parse_price(text)
        if not price or price > SEARCH["budget_max"]:
            return None

        title = link.get_text(strip=True)[:200] or f"Maison {commune}"
        if is_excluded(title):
            return None

        surface = parse_surface(text)
        chambres = parse_chambres(text)
        if chambres and chambres < SEARCH["chambres_min"]:
            return None

        img = container.find("img")
        photos = [img["src"]] if img and img.get("src") else []

        return Listing(
            id=f"pap:{listing_id}",
            source="pap",
            url=url,
            title=title,
            price=price,
            surface=surface or None,
            chambres=chambres or None,
            commune=commune,
            code_postal=code_postal,
            description=text[:600],
            photos=photos,
        )
