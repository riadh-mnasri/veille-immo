from __future__ import annotations
import logging

from models import Listing
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# SeLoger retourne une page vide aux navigateurs headless (bot detection).
# list.htm retourne 404 depuis leur migration Next.js.
# La nouvelle URL /immobilier/achat/... ne contient pas de __NEXT_DATA__ en mode headless.
# Pour débloquer : utiliser un proxy résidentiel ou les cookies d'une session réelle.


class SeLogerScraper(BaseScraper):
    source = "seloger"

    async def fetch(self) -> list[Listing]:
        logger.debug("[SeLoger] scraper désactivé — site protégé contre les bots headless")
        return []
