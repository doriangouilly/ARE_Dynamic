import random

# Couleurs
BLANC = (255, 255, 255)
GRIS = (200,200,200)
ORANGE = (255,150,0)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)
VIOLET = (180,0,255)
BLEU = (0, 0, 255)
VERT = (0, 255, 0)
TYPES = {1: "Micro", 2: "Petite", 3: "Moyenne", 4: "Grande"}
FOND = [(10000, 20000), (20001, 30000), (30001, 40000), (40001, 50000)]


class Secteur:
    # Intervalle des frais de production dans chaque secteur
    SECTEURS = {"alimentation":(2,50), "logement":(500,1500), "transport":(15,100), "vetement":(20,150), "soins":(10,250), "boisson":(2,40), "meuble":(30,200), "loisir":(15,150)}
    # Cout marginal dans chaque secteur
    COUT_MARGINAL = {"alimentation":2, "logement":500, "transport":15, "vetement":20, "soins":10, "boisson":2, "meuble":30, "loisir":15}
    # Probabilité à ce qu'une entreprise réalise des productions dans ces secteurs
    PROBABILITES = [0.1, 0.25, 0.03, 0.1, 0.07, 0.05, 0.3, 0.1]
    # Intervalle du seuil d'achat réalisé dans chaque secteurs
    SEUIL_ACHAT = {"alimentation":(5,50), "logement":(1,3), "transport":(1,10), "vetement":(5,15), "soins":(1,5), "boisson":(5,50), "meuble":(2,10), "loisir":(3,10)}
    # Poids représentant l'importance du secteur dans le budget moyen des habitants
    PONDERATIONS = {
        "alimentation": 0.2,
        "logement": 0.3,
        "transport": 0.15,
        "vetement": 0.1,
        "soins": 0.1,
        "boisson": 0.05,
        "meuble": 0.05,
        "loisir": 0.05
    }

    @staticmethod
    def generate_secteur():
        return random.choices(list(Secteur.SECTEURS.keys()), Secteur.PROBABILITES)[0]

