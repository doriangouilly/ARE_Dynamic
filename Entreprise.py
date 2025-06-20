import pygame
import random
from Secteur import *

class Entreprise(pygame.sprite.Sprite):
    TYPES = {1: "Micro", 2: "Petite", 3: "Moyenne", 4: "Grande"}
    FOND = [(10000, 20000), (20001, 30000), (30001, 40000), (40001, 50000)]
    AGGRESSIVITE_PAR_TYPE = {
        1: 0.03,  # Micro - très agressif
        2: 0.02,  # Petite
        3: 0.01,  # Moyenne
        4: 0.005  # Grande - très prudent
    }

    def __init__(self, x, y):
        # Représentation graphique des entreprises
        super().__init__()
        
        self.x = x
        self.y = y

        self.distance_max = 150 # distance max entre les entreprises pour qu'elles se concurrencent

        self.image = pygame.Surface((25, 25))  # Taille de l'entreprise
        self.rect = self.image.get_rect(center=(x, y))  # Position de l'entreprise

        # Caractéristique de l'entreprise
        self.type = random.choices(list(self.TYPES.keys()), [0.4, 0.3, 0.2, 0.1])[0]  # Type d'entreprise
        self.secteur = Secteur.generate_secteur()  # Secteur de production
        self.fond = random.randint(*self.FOND[self.type-1])  # Capital initial

        

        self.prix = random.randint(*Secteur.SECTEURS[self.secteur])  # Prix initial des produits
        self.frais_production = Secteur.COUT_MARGINAL[self.secteur] # prix de fabrication des produits par unité
        self.production = 10  # Quantité produite


        # Vitesse d'ajustement du prix
        self.timer_prix = 0

    def ajuster_prix(self, entreprises):
        # Appliquer Bertrand pour ajustement de base
        self.ajuster_prix_bertrand(entreprises)
        """
        # Rester dans l'intervalle [cout marginal, prix_max]
        cout_marginal = Secteur.COUT_MARGINAL[self.secteur]
        prix_max = max(Secteur.SECTEURS[self.secteur])
        self.prix = max(cout_marginal, min(self.prix, prix_max))
        """

    def ajuster_prix_bertrand(self, entreprises):
        # Facteur d'agressivité dependant de la taille de l'entreprise
        agressivite = self.AGGRESSIVITE_PAR_TYPE[self.type]  # Micro/petite entreprises plus agressives
        # 1. Seclectionne les entreprises concurrents (meme secteur,meme région, prix >= cout marginal)
        liste_concurrents = self.liste_entreprises_proches(entreprises)
        concurrents = [e[0] for e in liste_concurrents
                       if e[0].prix >= Secteur.COUT_MARGINAL[e[0].secteur]]

        if not concurrents:
            self.prix = max(Secteur.SECTEURS[self.secteur])
            return

        # 2. Determine le meilleur prix
        prix_min_concurrent = min(e.prix for e in concurrents) # prix le plus bas parmi les concurrents
        cout_marginal = Secteur.COUT_MARGINAL[self.secteur] # Coût minimal du secteur

        # 3. Application du Duopole de Bertrand
        if self.prix > prix_min_concurrent:
            # Rappochement du prix de vente vers le prix minimal
            self.prix = max(self.prix - (0.1 * agressivite * prix_min_concurrent), cout_marginal)
        # 10% de chance à ce que l'entreprise baisse un peu son prix afin de s'approprier le marché
        elif self.prix == prix_min_concurrent and len(concurrents) > 1:
            if random.random() <= 0.1:
                self.prix = max(self.prix - 0.005, cout_marginal)

        # 4. Fluctuation aléatoire autour du coût marginal
        marge_minimale = 0.01  # 1% de marge minimale
        fluctuation = random.uniform(-0.005, 0.005)  # ±0.5%
        # Garantie à ce que le prix ne soit pas absurde ( >= cout marginal, <= prix_max)
        self.prix = max(cout_marginal * (1 + marge_minimale + fluctuation),min(self.prix, max(Secteur.SECTEURS[self.secteur]))) # Fluctuation aléatoire

    def planifier_production_cournot(self, entreprises, habitants):

        # 1. Seclectionne les entreprises concurrents (meme secteur)
        liste_concurrents = self.liste_entreprises_proches(entreprises)
        concurrents = [e[0] for e in liste_concurrents if e[0].secteur == self.secteur]
        N = len(concurrents)

        # 2. Calculer la demande totale des habitants pour ce secteur
        demande_totale = sum(h.besoins.get(self.secteur, 0) for h in habitants)

        # 3. Initialisation des parametres
        prix_max = max(Secteur.SECTEURS[self.secteur])
        b = prix_max / (demande_totale+1)  # Sensibilité prix/quantité
        c = self.frais_production

        # Coefficient de compétitivité basé sur le prix de chaque entreprise
        prix_relatif = self.prix / prix_max
        competitivite = 1.5 - prix_relatif  # Entre 0.5 et 1.5 (plus compétitif si prix bas)

        # 4. Quantité de base avec Cournot
        quantite_base = (prix_max - c) / (b * (N + 1))

        # 5. Ajustement par la compétitivité
        if N > 0:
            prix_moyen = sum(e.prix for e in concurrents) / N
            ratio_prix = prix_moyen / max(self.prix, 1)  # >1 si notre prix est bas

            # Produit plus si ratio > 1,produit moins si ratio < 1
            quantite_ajustee = quantite_base * (ratio_prix ** 0.5) * competitivite
        else:
            quantite_ajustee = quantite_base * competitivite

        # 6. Capacité max de production
        capacite = int(self.fond / max(c, 1))

        # 7. Production finale avec variation aléatoire
        if (quantite_ajustee > self.production or self.production < 10) and (capacite>0):
            quantite_ajustee = int((quantite_ajustee - self.production) * random.uniform(0.8, 1.2)) # quantite à rajouter
            quantite_produite = min(max(quantite_ajustee, 10 - self.production),capacite) # avoir au minimum 10 unités
            self.production += quantite_produite

            # Mise à jour des fond de l'entreprise
            cout_total = quantite_produite * c
            self.fond -= cout_total

    def vendre(self,quantite):
        self.production -= quantite
        self.fond += quantite * self.prix

    def liste_entreprises_proches(self, entreprises, always=True):
        entreprises_return = []
        entreprise_plus_proche = None
        distance_min = float('inf')
        distance_max = self.distance_max  # pixels
        for entreprise in entreprises:

            if entreprise == self:
                continue

            if self.secteur == entreprise.secteur:
                distance = ((self.x - entreprise.x) ** 2 + (self.y - entreprise.y) ** 2) ** 0.5
                if distance <= distance_max:
                    entreprises_return.append((entreprise, distance, (entreprise.x, entreprise.y)))
                if distance < distance_min:
                    distance_min = distance
                    entreprise_plus_proche = (entreprise, distance, (entreprise.x, entreprise.y))

        if len(entreprises_return) == 0 and always and entreprise_plus_proche:
            return [entreprise_plus_proche]
        return entreprises_return

    def step(self,entreprises,vitesse,delta_temps):
        self.timer_prix += 4.25 * delta_temps * vitesse  # avance plus vite avec vitesse haute
        if self.timer_prix >= 1.0:  # tous les "1 mois simulé"
            self.ajuster_prix(entreprises)
            self.timer_prix = 0


        
        

    
