from __future__ import annotations
import json
import logging
import re

from config import SEARCH
from models import Listing
from scrapers.base import BaseScraper, commune_match, is_excluded, parse_surface, parse_chambres

logger = logging.getLogger(__name__)

# SeLoger est en Next.js : on charge la page avec Playwright et on lit __NEXT_DATA__
# URL propre sans paramètres JSON encodés
SELOGER_URL = (
    "https://www.seloger.com/immobilier/achat/maison/val-d-oise-95/"
    f"?prix=max-{SEARCH['budget_max']}"
    f"&pieces=min-{SEARCH['chambres_min']}"
    "&tri=initial"
)


class SeLogerScraper(BaseScraper):
    source = "seloger"

    async def fetch(self) -> list[Listing]:
        from playwright.async_api import async_playwright

        content = ""
        captured: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="fr-FR",
            )
            page = await ctx.new_page()

            async def on_response(resp):
                if "api.seloger.com" in resp.url or "/list-only" in resp.url:
                    try:
                        data = await resp.json()
                        cards = (
                            data.get("cards", {}).get("list", [])
                            or data.get("listingData", [])
                            or data.get("results", [])
                        )
                        captured.extend(cards)
                    except Exception:
                        pass

            page.on("response", on_response)
            try:
                await page.goto(SELOGER_URL, wait_until="domcontentloaded", timeout=35_000)
                await page.wait_for_timeout(3_000)
                content = await page.content()
            except Exception as e:
                logger.error(f"[SeLoger] Playwright: {e}")
            finally:
                await browser.close()

        listings: list[Listing] = []

        # 1) Données interceptées depuis les appels API
        for card in captured:
            try:
                l = self._parse_card(card)
                if l:
                    listings.append(l)
            except Exception:
                pass

        # 2) Fallback : __NEXT_DATA__ embarqué dans le HTML
        if not listings and content:
            nd = self._next_data(content)
            if nd:
                cards = (
                    nd.get("props", {}).get("pageProps", {}).get("cards", {}).get("list", [])
                    or nd.get("props", {}).get("pageProps", {}).get("listingData", [])
                )
                for card in cards:
                    try:
                        l = self._parse_card(card)
                        if l:
                            listings.append(l)
                    except Exception:
                        pass

        logger.info(f"[SeLoger] {len(listings)} annonce(s)")
        return listings

    def _next_data(self, html: str) -> dict | None:
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

    def _parse_card(self, card: dict) -> Listing | None:
        ad_id = str(card.get("id", "") or card.get("listingId", ""))
        if not ad_id:
            return None

        price = (
            card.get("pricing", {}).get("rawPrice")
            or card.get("price")
            or card.get("priceRaw")
            or 0
        )
        if not price or price > SEARCH["budget_max"]:
            return None

        city = card.get("cityLabel", "") or card.get("city", "") or card.get("ville", "")
        if not commune_match(city):
            return None

        title = card.get("title", "") or card.get("titre", "") or f"Maison {city}"
        if is_excluded(title):
            return None

        surface = card.get("surface", 0) or card.get("surfaceArea", 0) or 0
        rooms = card.get("rooms", 0) or card.get("nbPieces", 0) or 0
        bedrooms = card.get("bedRoomsCount", 0) or card.get("nbChambres", 0) or 0
        chambres = bedrooms or max(0, rooms - 1)
        if chambres and chambres < SEARCH["chambres_min"]:
            return None

        photos = []
        for p in card.get("photos", [])[:5]:
            url_p = p.get("url", "") or p.get("src", "") if isinstance(p, dict) else str(p)
            if url_p:
                photos.append(url_p)

        slug = card.get("classifiedURL", "") or card.get("permalink", "")
        if slug.startswith("/"):
            url = f"https://www.seloger.com{slug}"
        elif slug.startswith("http"):
            url = slug
        else:
            url = f"https://www.seloger.com/annonces/achat/{ad_id}.htm"

        return Listing(
            id=f"seloger:{ad_id}",
            source="seloger",
            url=url,
            title=title,
            price=int(price),
            surface=float(surface) if surface else None,
            chambres=chambres or None,
            commune=city,
            code_postal=card.get("zipCode", "") or card.get("codePostal", ""),
            description=(card.get("description", "") or card.get("descriptif", "") or "")[:800],
            photos=photos,
        )
