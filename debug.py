"""
Diagnostic ciblé — run : python debug.py
"""
import asyncio, json, re, urllib.parse
import httpx
from bs4 import BeautifulSoup
from config import SEARCH

def banner(t): print(f"\n{'═'*60}\n  {t}\n{'═'*60}")
def ok(m):     print(f"  ✅  {m}")
def warn(m):   print(f"  ⚠️   {m}")
def err(m):    print(f"  ❌  {m}")
def info(m):   print(f"  →   {m}")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"

# ─── PAP ──────────────────────────────────────────────────
async def test_pap():
    banner("PAP.fr — liens /annonce/ dans la page")
    url = f"https://www.pap.fr/annonce/ventes-maisons-val-d-oise-g439-budgetmax-{SEARCH['budget_max']}"
    async with httpx.AsyncClient(headers={"User-Agent": UA, "Accept-Language": "fr-FR"}, timeout=20, follow_redirects=True) as c:
        r = await c.get(url)
    info(f"Status : {r.status_code}")
    soup = BeautifulSoup(r.text, "lxml")
    import re as _re
    links = soup.find_all("a", href=_re.compile(r"/annonce/ventes-maisons-\d{5}-[a-z]"))
    info(f"Liens /annonce/ trouvés : {len(links)}")
    for lk in links[:5]:
        href = lk.get("href", "")
        # cherche prix dans le bloc parent
        p = lk
        for _ in range(6):
            p = p.parent or p
            if "€" in (p.get_text() if p else ""):
                break
        txt = (p.get_text(" ", strip=True) if p else "") [:120]
        info(f"  {href[:60]}  →  {txt}")

# ─── BIENICI ──────────────────────────────────────────────
async def test_bienici():
    banner("BienIci — décoder l'URL API exacte utilisée par la page")
    from playwright.async_api import async_playwright
    nav_url = f"https://www.bienici.com/recherche/achat/maison/val-d-oise--95?prix-max={SEARCH['budget_max']}&nombreDeChambresMin={SEARCH['chambres_min']}"
    info(f"Navigation : {nav_url}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(user_agent=UA, locale="fr-FR")

        async def on_resp(resp):
            if "realEstateAds" in resp.url and resp.status == 200:
                # Décoder le filtre complet
                parsed = urllib.parse.urlparse(resp.url)
                qs = urllib.parse.parse_qs(parsed.query)
                raw = qs.get("filters", ["{}"])[0]
                try:
                    flt = json.loads(raw)
                    info(f"  Filtre décodé :\n{json.dumps(flt, indent=4, ensure_ascii=False)}")
                except Exception:
                    info(f"  Filtre brut : {raw[:400]}")
                try:
                    data = await resp.json()
                    ads = data if isinstance(data, list) else data.get("realEstateAds", [])
                    info(f"  Annonces : {len(ads)}")
                    if ads:
                        a = ads[0] if isinstance(ads[0], dict) else {}
                        info(f"  Ville[0]  : {a.get('city')}")
                        info(f"  Prix[0]   : {a.get('price')}")
                        info(f"  Surface[0]: {a.get('surfaceArea')}")
                        info(f"  Clés      : {list(a.keys())[:15]}")
                except Exception as ex:
                    warn(f"  JSON parse : {ex}")

        page.on("response", on_resp)
        try:
            await page.goto(nav_url, wait_until="networkidle", timeout=35_000)
        except Exception as e:
            warn(str(e))
        await browser.close()

# ─── LEBONCOIN ────────────────────────────────────────────
async def test_leboncoin():
    banner("LeBonCoin — log TOUS les appels XHR/fetch")
    from playwright.async_api import async_playwright
    url = (
        "https://www.leboncoin.fr/recherche"
        "?category=9&real_estate_types=2"
        f"&price=max-{SEARCH['budget_max']}"
        f"&rooms=min-{SEARCH['chambres_min']}"
        "&locations=Val-d%27Oise"
    )
    info(f"Navigation : {url}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(user_agent=UA, locale="fr-FR")

        async def on_resp(resp):
            if resp.request.resource_type in ("xhr", "fetch"):
                ct = resp.headers.get("content-type", "")
                status = resp.status
                u = resp.url[:110]
                if "json" in ct and status == 200:
                    try:
                        data = await resp.json()
                        # Cherche une liste d'annonces dans n'importe quelle clé
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if isinstance(v, list) and len(v) > 2:
                                    sample = v[0] if v else {}
                                    if isinstance(sample, dict) and len(sample) > 3:
                                        ok(f"Annonces dans '{k}' : {len(v)} — URL: {u}")
                                        info(f"    Clés item: {list(sample.keys())[:10]}")
                                        return
                        info(f"JSON {status} : {u}")
                    except Exception:
                        info(f"JSON (parse fail) {status} : {u}")
                else:
                    if status not in (204, 301, 302, 304):
                        info(f"{status} {resp.request.resource_type:5} : {u}")

        page.on("response", on_resp)
        try:
            await page.goto(url, wait_until="networkidle", timeout=35_000)
        except Exception as e:
            warn(str(e))
        await browser.close()

# ─── SELOGER ──────────────────────────────────────────────
async def test_seloger():
    banner("SeLoger — log appels XHR/fetch + __NEXT_DATA__")
    from playwright.async_api import async_playwright
    url = (
        "https://www.seloger.com/immobilier/achat/maison/val-d-oise-95/"
        f"?prix=max-{SEARCH['budget_max']}&pieces=min-{SEARCH['chambres_min']}"
    )
    info(f"Navigation : {url}")
    content = ""

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(user_agent=UA, locale="fr-FR")

        async def on_resp(resp):
            if resp.request.resource_type in ("xhr", "fetch") and resp.status == 200:
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    try:
                        data = await resp.json()
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                                    ok(f"Liste '{k}' ({len(v)}) dans : {resp.url[:80]}")
                                    info(f"    Clés: {list(v[0].keys())[:10]}")
                                    return
                            info(f"JSON clés top: {list(data.keys())[:8]} — {resp.url[:80]}")
                    except Exception:
                        pass

        page.on("response", on_resp)
        try:
            await page.goto(url, wait_until="networkidle", timeout=35_000)
            await page.wait_for_timeout(3000)
            content = await page.content()
        except Exception as e:
            warn(str(e))
        await browser.close()

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', content, re.DOTALL)
    if m:
        try:
            nd = json.loads(m.group(1))
            pp = nd.get("props", {}).get("pageProps", {})
            info(f"__NEXT_DATA__ pageProps clés : {list(pp.keys())[:10]}")
            cards = pp.get("cards", {}).get("list", []) or pp.get("listingData", []) or pp.get("listings", [])
            info(f"Cards trouvées : {len(cards)}")
            if cards:
                ok(f"Premier card clés : {list(cards[0].keys())[:12]}")
        except Exception as ex:
            err(f"__NEXT_DATA__ parse : {ex}")
    else:
        warn("Pas de __NEXT_DATA__")

# ──────────────────────────────────────────────────────────
async def main():
    print("\n🔍  Diagnostic ciblé — Veille Immo 95")
    await test_pap()
    await test_bienici()
    await test_leboncoin()
    await test_seloger()
    print(f"\n{'═'*60}\n  Fin\n{'═'*60}\n")

asyncio.run(main())
