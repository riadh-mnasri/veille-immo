import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from config import EMAIL, TELEGRAM
from models import Listing

logger = logging.getLogger(__name__)


def _format_message(listing: Listing) -> str:
    prix_m2 = f"{listing.prix_m2:.0f} €/m²" if listing.prix_m2 else "?"
    chambres = f"{listing.chambres} ch." if listing.chambres else "? ch."
    surface = f"{listing.surface:.0f} m²" if listing.surface else "? m²"

    stars = "⭐" * int(listing.score / 25)

    return (
        f"{stars} Score {listing.score}/100\n"
        f"📍 {listing.commune} ({listing.code_postal})\n"
        f"💰 {listing.price:,} € — {prix_m2}\n"
        f"🏠 {surface} · {chambres}\n"
        f"📝 {listing.title}\n"
        f"🔗 {listing.url}"
    )


async def _send_telegram(listing: Listing) -> None:
    if not TELEGRAM["bot_token"] or not TELEGRAM["chat_id"]:
        return
    text = _format_message(listing)
    url = f"https://api.telegram.org/bot{TELEGRAM['bot_token']}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={
            "chat_id": TELEGRAM["chat_id"],
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        })


def _send_email(listing: Listing) -> None:
    if not EMAIL["sender"] or not EMAIL["password"]:
        return

    prix_m2 = f"{listing.prix_m2:.0f} €/m²" if listing.prix_m2 else "?"
    chambres = listing.chambres or "?"
    surface = f"{listing.surface:.0f} m²" if listing.surface else "?"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px">
    <h2>🏠 Nouvelle annonce — Score {listing.score}/100</h2>
    <table style="border-collapse:collapse;width:100%">
      <tr><td style="padding:8px;background:#f5f5f5"><b>Source</b></td><td>{listing.source.upper()}</td></tr>
      <tr><td style="padding:8px;background:#f5f5f5"><b>Commune</b></td><td>{listing.commune} ({listing.code_postal})</td></tr>
      <tr><td style="padding:8px;background:#f5f5f5"><b>Prix</b></td><td><b>{listing.price:,} €</b> ({prix_m2})</td></tr>
      <tr><td style="padding:8px;background:#f5f5f5"><b>Surface</b></td><td>{surface}</td></tr>
      <tr><td style="padding:8px;background:#f5f5f5"><b>Chambres</b></td><td>{chambres}</td></tr>
      <tr><td style="padding:8px;background:#f5f5f5"><b>Titre</b></td><td>{listing.title}</td></tr>
    </table>
    <br>
    <p>{listing.description[:400]}...</p>
    <a href="{listing.url}" style="background:#0066cc;color:white;padding:12px 24px;text-decoration:none;border-radius:4px">
      Voir l'annonce →
    </a>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏠 [{listing.source.upper()}] {listing.price:,}€ — {listing.commune} (Score {listing.score})"
    msg["From"] = EMAIL["sender"]
    msg["To"] = EMAIL["recipient"]
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(EMAIL["smtp_host"], EMAIL["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL["sender"], EMAIL["password"])
            server.sendmail(EMAIL["sender"], EMAIL["recipient"], msg.as_string())
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}")


class AlertManager:
    async def send(self, listing: Listing) -> None:
        tasks = [_send_telegram(listing)]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.to_thread(_send_email, listing)
        logger.info(f"Alerte envoyée: {listing.title} ({listing.price:,}€)")
