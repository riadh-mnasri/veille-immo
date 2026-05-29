from models import Listing
from config import SEARCH, SCORE_WEIGHTS, COMMUNES_PRIORITAIRES


def score_listing(listing: Listing) -> float:
    score = 50.0  # base

    # Prix
    if listing.price <= SEARCH["budget_max"] - 50_000:
        score += SCORE_WEIGHTS["prix_bas"]
    elif listing.price > SEARCH["budget_max"]:
        return 0.0  # hors budget → on ne notifie pas

    # Surface
    if listing.surface and listing.surface >= 120:
        score += SCORE_WEIGHTS["grande_surface"]
    elif listing.surface and listing.surface >= 100:
        score += SCORE_WEIGHTS["grande_surface"] / 2

    # Chambres
    if listing.chambres and listing.chambres >= 5:
        score += SCORE_WEIGHTS["beaucoup_chambres"]
    elif listing.chambres and listing.chambres >= 4:
        score += SCORE_WEIGHTS["beaucoup_chambres"] / 2

    # Commune prioritaire
    if listing.commune in COMMUNES_PRIORITAIRES:
        score += SCORE_WEIGHTS["commune_cible"]

    return round(score, 1)
