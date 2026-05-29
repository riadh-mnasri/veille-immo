"""
Point d'entrée principal : lance le scanner + le serveur web dans le même process.

    source .venv/bin/activate && python run.py

Dashboard disponible sur http://localhost:8080
"""
import asyncio
import logging
from datetime import datetime

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import SCAN_INTERVAL_MINUTES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)


async def main():
    # Import ici pour éviter les imports circulaires au niveau module
    from main import scan_once
    from server import app

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scan_once, "interval",
        minutes=SCAN_INTERVAL_MINUTES,
        next_run_time=datetime.now(),
    )
    scheduler.start()

    config = uvicorn.Config(
        app, host="0.0.0.0", port=3000,
        log_level="warning", access_log=False,
    )
    server = uvicorn.Server(config)

    logging.getLogger(__name__).info(
        "Dashboard disponible sur http://localhost:3000"
    )
    await server.serve()
    scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
