from __future__ import annotations
import logging

from models import Listing
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# BienIci : leur API publique ignore totalement les filtres géographiques
# sans token d'authentification — retourne des résultats d'Auvergne quel que
# soit le zoneId ou departmentCode passé.
# Pour débloquer : authentification OAuth de l'app mobile BienIci.


class BienIciScraper(BaseScraper):
    source = "bienici"

    async def fetch(self) -> list[Listing]:
        logger.debug("[BienIci] scraper désactivé — API géo non fonctionnelle sans auth")
        return []
