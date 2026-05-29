import os
from dotenv import load_dotenv

load_dotenv()

SEARCH = {
    "budget_max": 470_000,
    "chambres_min": 4,
    "surface_min": 90,
    "communes": [
        "Ermont", "Eaubonne", "Saint-Gratien", "Enghien-les-Bains",
        "Soisy-sous-Montmorency", "Deuil-la-Barre", "Franconville",
        "Sannois", "Montlignon", "Margency",
    ],
    "codes_postaux": [
        "95120", "95600", "95210", "95880",
        "95230", "95170", "95130", "95110", "95680",
    ],
    # Mots-clés négatifs dans le titre/description → listing ignoré
    "mots_exclus": [
        "parking", "garage seul", "terrain seul", "local commercial",
    ],
}

SCAN_INTERVAL_MINUTES = 20

TELEGRAM = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
}

EMAIL = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": os.getenv("EMAIL_SENDER", ""),
    "password": os.getenv("EMAIL_PASSWORD", ""),
    "recipient": os.getenv("EMAIL_RECIPIENT", "riadh.mnasri@gmail.com"),
}

SCORE_WEIGHTS = {
    "prix_bas": 30,        # bonus si prix < budget - 50k
    "grande_surface": 20,  # bonus si surface > 120m²
    "beaucoup_chambres": 20, # bonus si chambres >= 5
    "commune_cible": 30,   # bonus si Ermont ou Eaubonne en priorité
}
COMMUNES_PRIORITAIRES = {"Ermont", "Eaubonne", "Enghien-les-Bains"}
