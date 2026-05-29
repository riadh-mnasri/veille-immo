from __future__ import annotations
import asyncio
import json
import logging

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from database import Database
from events import sse_queue

logger = logging.getLogger(__name__)
app = FastAPI(title="Veille Immo")
db = Database()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _row_to_dict(row) -> dict:
    photos = []
    try:
        photos = json.loads(row.photos or "[]")
    except Exception:
        pass
    prix_m2 = round(row.price / row.surface) if row.price and row.surface else None
    return {
        "id": row.id,
        "source": row.source,
        "url": row.url,
        "title": row.title,
        "price": row.price,
        "surface": row.surface,
        "chambres": row.chambres,
        "commune": row.commune,
        "code_postal": row.code_postal,
        "description": row.description,
        "photos": photos,
        "score": row.score,
        "prix_m2": prix_m2,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@app.get("/api/listings")
def get_listings(
    source: str = Query(None),
    commune: str = Query(None),
    score_min: float = Query(0),
    price_max: int = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    rows = db.all_listings()
    if source:
        rows = [r for r in rows if r.source == source]
    if commune:
        rows = [r for r in rows if commune.lower() in (r.commune or "").lower()]
    if price_max:
        rows = [r for r in rows if (r.price or 0) <= price_max]
    if score_min:
        rows = [r for r in rows if (r.score or 0) >= score_min]
    total = len(rows)
    page = rows[offset : offset + limit]
    return {"total": total, "listings": [_row_to_dict(r) for r in page]}


@app.get("/api/stats")
def get_stats():
    rows = db.all_listings()
    if not rows:
        return {"total": 0, "avg_price": 0, "min_price": 0, "sources": {}, "top_communes": []}

    prices = [r.price for r in rows if r.price]
    sources: dict[str, int] = {}
    communes: dict[str, int] = {}
    for r in rows:
        sources[r.source] = sources.get(r.source, 0) + 1
        if r.commune:
            communes[r.commune] = communes.get(r.commune, 0) + 1

    top_communes = sorted(communes.items(), key=lambda x: x[1], reverse=True)[:6]
    return {
        "total": len(rows),
        "avg_price": int(sum(prices) / len(prices)) if prices else 0,
        "min_price": min(prices) if prices else 0,
        "sources": sources,
        "top_communes": [{"name": c, "count": n} for c, n in top_communes],
    }


@app.get("/api/events")
async def sse_events():
    async def stream():
        while True:
            try:
                data = await asyncio.wait_for(sse_queue.get(), timeout=25)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield 'data: {"ping":true}\n\n'

    return StreamingResponse(stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


app.mount("/", StaticFiles(directory="static", html=True), name="static")
