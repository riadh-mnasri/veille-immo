from __future__ import annotations
import logging

from models import Listing
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# LeBonCoin détecte et bloque les navigateurs headless (page anti-bot de 1810 chars).
# L'API REST retourne 403 même avec stealth.
# Pour débloquer : utiliser un proxy résidentiel ou les cookies d'une session navigateur réelle.


class LeBonCoinScraper(BaseScraper):
    source = "leboncoin"

    async def fetch(self) -> list[Listing]:
        logger.debug("[LeBonCoin] scraper désactivé — site protégé contre les bots headless")
        return []
