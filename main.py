import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alerts import AlertManager
from config import SCAN_INTERVAL_MINUTES, SEARCH
from database import Database
from scorer import score_listing
from scrapers.bienici import BienIciScraper
from scrapers.leboncoin import LeBonCoinScraper
from scrapers.pap import PAPScraper
from scrapers.seloger import SeLogerScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

db = Database()
alerts = AlertManager()
SCRAPERS = [PAPScraper(), BienIciScraper(), LeBonCoinScraper(), SeLogerScraper()]


async def scan_once():
    logger.info("── Scan démarré ──────────────────────────────")
    new_total = 0

    tasks = [scraper.fetch() for scraper in SCRAPERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for scraper, result in zip(SCRAPERS, results):
        if isinstance(result, Exception):
            logger.error(f"[{scraper.source}] Exception: {result}")
            continue
        for listing in result:
            if db.is_known(listing.id):
                continue
            listing.score = score_listing(listing)
            if listing.score == 0:
                continue  # hors budget ou filtré
            db.save(listing)
            await alerts.send(listing)
            # Pousse vers le dashboard en temps réel (SSE)
            try:
                from events import sse_queue
                import json as _json
                photos = listing.photos[:1]
                prix_m2 = round(listing.price / listing.surface) if listing.price and listing.surface else None
                sse_queue.put_nowait({
                    "id": listing.id, "source": listing.source, "url": listing.url,
                    "title": listing.title, "price": listing.price,
                    "surface": listing.surface, "chambres": listing.chambres,
                    "commune": listing.commune, "code_postal": listing.code_postal,
                    "description": listing.description[:300],
                    "photos": photos, "score": listing.score, "prix_m2": prix_m2,
                    "created_at": listing.created_at.isoformat(),
                })
            except Exception:
                pass
            new_total += 1

    logger.info(f"── Scan terminé — {new_total} nouvelle(s) annonce(s) ──")


async def main():
    logger.info(
        f"Veille immobilière démarrée\n"
        f"  Zone    : {', '.join(SEARCH['communes'][:5])}...\n"
        f"  Budget  : ≤ {SEARCH['budget_max']:,} €\n"
        f"  Chambres: ≥ {SEARCH['chambres_min']}\n"
        f"  Sources : {', '.join(s.source for s in SCRAPERS)}\n"
        f"  Scan    : toutes les {SCAN_INTERVAL_MINUTES} minutes"
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scan_once, "interval",
        minutes=SCAN_INTERVAL_MINUTES,
        next_run_time=datetime.now(),  # scan immédiat au démarrage
    )
    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Veille arrêtée.")


if __name__ == "__main__":
    asyncio.run(main())
