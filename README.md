# 🏠 Veille Immo 95

> Surveillance automatique du marché immobilier dans le Val-d'Oise — alertes instantanées par Telegram et email, dashboard en temps réel.

Scrape **PAP**, **BienIci**, **LeBonCoin** et **SeLoger** toutes les 20 minutes. Chaque nouvelle annonce est scorée, dédupliquée, et envoyée avant que tu aies eu le temps d'ouvrir ton navigateur.

---

## Aperçu

![Dashboard](https://github.com/riadh-mnasri/veille-immo/raw/main/static/preview.png)

| Fonctionnalité | Détail |
|---|---|
| **Sources** | PAP · BienIci · LeBonCoin · SeLoger |
| **Zone** | Ermont, Eaubonne, Enghien, Sannois, Deuil, Soisy… (95) |
| **Budget** | ≤ 470 000 € |
| **Critères** | ≥ 4 chambres, maison uniquement |
| **Scan** | Toutes les 20 minutes |
| **Alertes** | Telegram (instantané) + Email (Gmail) |
| **Dashboard** | Dark UI temps réel sur `http://localhost:3000` |
| **Score** | 0–100 par annonce (prix, surface, chambres, commune) |

---

## Démarrage rapide

### 1. Installer

```bash
git clone https://github.com/riadh-mnasri/veille-immo.git
cd veille-immo
bash setup.sh
```

### 2. Configurer les alertes

```bash
cp .env.example .env
nano .env
```

```env
# Telegram — créer un bot via @BotFather, obtenir l'ID via @userinfobot
TELEGRAM_BOT_TOKEN=1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=123456789

# Gmail — utiliser un mot de passe d'application (pas ton vrai MDP)
# myaccount.google.com → Sécurité → Mots de passe des applications
EMAIL_SENDER=ton.email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_RECIPIENT=toi@gmail.com
```

### 3. Lancer

```bash
source .venv/bin/activate && python run.py
```

Ouvre **http://localhost:3000** — le premier scan démarre immédiatement.

---

## Structure du projet

```
veille-immo/
├── run.py              ← Point d'entrée (scanner + serveur web)
├── main.py             ← Scheduler APScheduler
├── server.py           ← API FastAPI + SSE temps réel
├── config.py           ← Critères de recherche (budget, communes…)
├── models.py           ← Dataclass Listing
├── database.py         ← SQLite via SQLAlchemy
├── scorer.py           ← Algorithme de scoring 0–100
├── alerts.py           ← Telegram + email
├── scrapers/
│   ├── pap.py          ← PAP.fr (geo IDs + parsing DOM)
│   ├── bienici.py      ← BienIci (API REST)
│   ├── leboncoin.py    ← LeBonCoin (Playwright)
│   └── seloger.py      ← SeLoger (Playwright + __NEXT_DATA__)
├── static/
│   └── index.html      ← Dashboard SPA (Alpine.js)
├── seed.py             ← Injecte des annonces de test
└── debug.py            ← Diagnostic des scrapers
```

---

## Dashboard

Interface dark glassmorphism accessible sur `http://localhost:3000`.

**Header** — stats en temps réel : nombre d'annonces, prix moyen, prix min, répartition par source

**Sidebar** — filtres instantanés :
- Source (PAP / BienIci / LeBonCoin / SeLoger)
- Score minimum (slider)
- Budget maximum (slider)
- Commune (chips cliquables)

**Cards** — chaque annonce affiche :
- Photo avec zoom au survol
- Badge source coloré + badge **NOUVEAU** (< 2h) ou **COUP DE CŒUR** (score ≥ 90)
- Score ring SVG circulaire (vert ≥ 90 · indigo ≥ 70 · ambre ≥ 50)
- Prix · surface · chambres · €/m²
- Description · lien direct vers l'annonce

**Alertes temps réel** — toast en bas à droite dès qu'une nouvelle annonce est détectée pendant que le dashboard est ouvert (Server-Sent Events).

---

## Système de score

Chaque annonce reçoit un score entre 0 et 100 :

| Critère | Points |
|---|---|
| Prix ≤ budget − 50 000 € | +30 |
| Surface ≥ 120 m² | +20 |
| ≥ 5 chambres | +20 |
| Commune prioritaire (Ermont, Eaubonne, Enghien) | +30 |

Les annonces hors budget (> 470 000 €) sont ignorées (score = 0).

---

## Adapter à ta recherche

Tout se configure dans `config.py` :

```python
SEARCH = {
    "budget_max": 470_000,       # Budget maximum
    "chambres_min": 4,           # Nombre de chambres minimum
    "communes": [                # Communes surveillées
        "Ermont", "Eaubonne", "Enghien-les-Bains", ...
    ],
    "mots_exclus": [             # Annonces ignorées si ces mots apparaissent
        "parking", "garage seul", "terrain seul",
    ],
}

SCAN_INTERVAL_MINUTES = 20       # Fréquence de scan

COMMUNES_PRIORITAIRES = {        # Bonus score commune
    "Ermont", "Eaubonne", "Enghien-les-Bains"
}
```

Pour changer les communes de PAP, récupère les geo IDs via :
```bash
curl "https://www.pap.fr/json/ac-geo?q=NomCommune"
# → [{"id": 43399, "name": "Ermont (95120)"}]
```

Puis ajoute l'entrée dans `scrapers/pap.py` → `COMMUNES_PAP`.

---

## Telegram — mise en place

1. Ouvre Telegram, cherche **@BotFather**
2. Envoie `/newbot` → choisis un nom → copie le **token**
3. Cherche **@userinfobot** → envoie `/start` → copie ton **ID**
4. Colle les deux dans `.env`

Chaque alerte ressemble à :
```
🏠 Nouvelle annonce · Score 90
📍 Eaubonne (95600)
💰 380 000 € — 4 310 €/m²
🏡 88 m² · 4 ch.
Voir sur PAP →
```

---

## Diagnostic

Si un scraper ne trouve rien :

```bash
source .venv/bin/activate && python debug.py
```

Le script teste chaque source indépendamment et affiche les réponses HTTP brutes, les appels réseau interceptés par Playwright, et les données parsées.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | Python 3.9+ · FastAPI · APScheduler |
| Scraping HTTP | httpx · BeautifulSoup · lxml |
| Scraping JS | Playwright (Chromium headless) |
| Base de données | SQLite · SQLAlchemy |
| Frontend | Alpine.js · CSS custom · Server-Sent Events |
| Alertes | python-telegram-bot · smtplib |

---

## Lancer en arrière-plan (optionnel)

```bash
# Avec screen
screen -S veille-immo
source .venv/bin/activate && python run.py
# Ctrl+A puis D pour détacher

# Avec nohup
nohup source .venv/bin/activate && python run.py > veille.log 2>&1 &
```

---

## Données de test

Pour tester le dashboard sans attendre le premier scan :

```bash
source .venv/bin/activate && python seed.py
```

Injecte 6 annonces fictives avec de vraies photos pour vérifier que l'interface fonctionne.

---

*Projet personnel — usage strictement privé. Respecte les CGU de chaque site.*
