from __future__ import annotations
import logging
import re

from config import SEARCH
from models import Listing
from scrapers.base import BaseScraper, commune_match, is_excluded

logger = logging.getLogger(__name__)

# Playwright intercepte l'appel API authentifié que le navigateur fait lui-même
LBC_URL = (
    "https://www.leboncoin.fr/recherche"
    "?category=9"
    "&real_estate_types=2"
    f"&price=max-{SEARCH['budget_max']}"
    f"&rooms=min-{SEARCH['chambres_min']}"
    "&locations=Val-d%27Oise"
)


class LeBonCoinScraper(BaseScraper):
    source = "leboncoin"

    async def fetch(self) -> list[Listing]:
        from playwright.async_api import async_playwright

        captured: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="fr-FR",
            )
            page = await ctx.new_page()

            async def on_response(resp):
                if "finder/classified/search" in resp.url or "api/adfinder" in resp.url:
                    try:
                        data = await resp.json()
                        captured.extend(data.get("ads", []))
                    except Exception:
                        pass

            page.on("response", on_response)
            try:
                await page.goto(LBC_URL, wait_until="networkidle", timeout=35_000)
            except Exception as e:
                logger.error(f"[LeBonCoin] Playwright: {e}")
            finally:
                await browser.close()

        listings: list[Listing] = []
        for ad in captured:
            try:
                listing = self._parse_ad(ad)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"[LeBonCoin] parse: {e}")

        logger.info(f"[LeBonCoin] {len(listings)} annonce(s)")
        return listings

    def _parse_ad(self, ad: dict) -> Listing | None:
        ad_id = str(ad.get("list_id", ""))
        prices = ad.get("price", [0])
        price = prices[0] if isinstance(prices, list) else prices
        if not price or price > SEARCH["budget_max"]:
            return None

        loc = ad.get("location", {})
        city = loc.get("city", "")
        if not commune_match(city):
            return None

        title = ad.get("subject", "") or f"Maison {city}"
        if is_excluded(title):
            return None

        attrs = {a["key"]: a.get("value_label", a.get("value", "")) for a in ad.get("attributes", [])}
        surface = _num(attrs.get("square", ""))
        rooms = int(_num(attrs.get("rooms", "")) or 0)
        bedrooms = int(_num(attrs.get("bedrooms", "")) or 0)
        chambres = bedrooms or max(0, rooms - 1)
        if chambres and chambres < SEARCH["chambres_min"]:
            return None

        photos = ad.get("images", {}).get("urls_large", [])[:5]
        url = ad.get("url", f"https://www.leboncoin.fr/ventes_immobilieres/{ad_id}.htm")

        return Listing(
            id=f"leboncoin:{ad_id}",
            source="leboncoin",
            url=url,
            title=title,
            price=int(price),
            surface=float(surface) if surface else None,
            chambres=chambres or None,
            commune=city,
            code_postal=loc.get("zipcode", ""),
            description=(ad.get("body", "") or "")[:800],
            photos=photos,
        )


def _num(s: str) -> float | None:
    v = re.sub(r"[^\d.,]", "", str(s)).replace(",", ".")
    try:
        return float(v) if v else None
    except ValueError:
        return None
