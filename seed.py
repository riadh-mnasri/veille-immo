"""
Injecte des annonces de test dans la base pour vérifier le dashboard.
    python seed.py
"""
from database import Database
from models import Listing
from scorer import score_listing

db = Database()

annonces = [
    Listing(id="test:1", source="pap", url="https://www.pap.fr/annonce/test1",
            title="Maison 6 pièces avec jardin et garage",
            price=439000, surface=135, chambres=5,
            commune="Ermont", code_postal="95120",
            description="Superbe maison familiale de 135m² avec grand jardin arboré, garage double, 5 chambres dont suite parentale. Proche école et RER C.",
            photos=["https://images.pexels.com/photos/106399/pexels-photo-106399.jpeg"]),

    Listing(id="test:2", source="seloger", url="https://www.seloger.com/annonces/test2",
            title="Maison 4 chambres calme résidentiel",
            price=465000, surface=118, chambres=4,
            commune="Eaubonne", code_postal="95600",
            description="Maison dans quartier calme, 4 chambres, cuisine aménagée, terrasse 40m², cave. À 5 min de la gare.",
            photos=["https://images.pexels.com/photos/1396122/pexels-photo-1396122.jpeg"]),

    Listing(id="test:3", source="leboncoin", url="https://www.leboncoin.fr/ventes_immobilieres/test3",
            title="Grande maison familiale 5 chambres",
            price=398000, surface=160, chambres=5,
            commune="Saint-Gratien", code_postal="95210",
            description="Rare sur le secteur. Maison de ville sur 3 niveaux, 5 chambres, salon de 40m², jardin de 250m², parking.",
            photos=["https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg"]),

    Listing(id="test:4", source="bienici", url="https://www.bienici.com/annonce/test4",
            title="Maison contemporaine avec piscine",
            price=455000, surface=145, chambres=4,
            commune="Enghien-les-Bains", code_postal="95880",
            description="Maison d'architecte, 4 chambres, piscine chauffée, domotique, proche lac. Prestation haut de gamme.",
            photos=["https://images.pexels.com/photos/323780/pexels-photo-323780.jpeg"]),

    Listing(id="test:5", source="pap", url="https://www.pap.fr/annonce/test5",
            title="Maison de caractère 4 chambres jardin",
            price=412000, surface=122, chambres=4,
            commune="Deuil-la-Barre", code_postal="95170",
            description="Belle maison de caractère années 30, 4 chambres, beau jardin, sous-sol total. RER D à pied.",
            photos=["https://images.pexels.com/photos/2102587/pexels-photo-2102587.jpeg"]),

    Listing(id="test:6", source="seloger", url="https://www.seloger.com/annonces/test6",
            title="Maison 5 chambres coup de cœur",
            price=449000, surface=155, chambres=5,
            commune="Ermont", code_postal="95120",
            description="Coup de cœur assuré. Maison lumineuse entièrement rénovée, 5 chambres, cuisine ilôt, grande terrasse, garage. Quartier prisé.",
            photos=["https://images.pexels.com/photos/1643389/pexels-photo-1643389.jpeg"]),
]

print("Injection des annonces de test...\n")
for l in annonces:
    l.score = score_listing(l)
    db.save(l)
    print(f"  ✅  {l.commune} — {l.price:,}€ — {l.surface}m² — {l.chambres}ch — score {l.score}")

print(f"\n{len(annonces)} annonces ajoutées → ouvre http://localhost:3000")
