import pygame
import random
from Secteur import *


class Habitant(pygame.sprite.Sprite):
    CLASSES = {0: "Basse", 1: "Moyenne", 2: "Supérieure", 3: "Riche"}

    def __init__(self, x, y,smic):
        # Représentation graphique des habitants
        super().__init__()
        self.image = pygame.Surface((25, 25))  # Taille de l'habitant
        self.rect = self.image.get_rect(center=(x, y))  # Position de l'habitant
        # Stocker les coordonnées
        self.x = x
        self.y = y

        # Caractéristiques de chaque habitant
        self.classe = random.choices(list(self.CLASSES.keys()), [0.4, 0.3, 0.2, 0.1])[0]
        self.achats_par_secteur = {}
        self.target_entreprise = None
        self.smic = smic

        #pour éviter des erreurs de tableau (avec le smic)
        self.REVENUS = [
            (int(smic*0.8), smic),
            (smic + 1, int(smic*1.5)),
            (int(smic*1.5) + 1, int(smic*2)),
            (int(smic*2) + 1, int(smic*3))
        ]
        self.revenu = random.randint(*self.REVENUS[self.classe])
        self.budget = self.revenu  # Ce qu'il peut dépenser
        # Définir les besoins (secteurs prioritaires et seuils de satisfaction)
        self.besoins = self.generer_besoins()

    def generer_besoins(self):
        # Liste des secteurs
        secteurs = list(Secteur.PONDERATIONS.keys())
        # Liste des probabilités associées à chaque secteur
        poids = list(Secteur.PONDERATIONS.values())

        # Tirer les secteurs selon leurs probabilités
        secteurs_tries = random.choices(secteurs, weights=poids, k=len(secteurs))

        besoins = {}
        # Ajoute le seuil de satisfaction pour chaque besoins
        for secteur in secteurs_tries:
            ajout = random.randint(*Secteur.SEUIL_ACHAT[secteur])
            if secteur in besoins:
                besoins[secteur] += ajout
            else:
                besoins[secteur] = ajout

        return besoins

    def ajouter_besoins(self):
        # Liste des secteurs
        secteurs = list(Secteur.PONDERATIONS.keys())
        # Liste des probabilités associées à chaque secteur
        poids = list(Secteur.PONDERATIONS.values())

        # Tirer les secteurs selon leurs probabilités
        secteurs_tries = random.choices(secteurs, weights=poids, k=len(secteurs))

        # Ajoute le seuil de satisfaction pour chaque besoins
        for secteur in secteurs_tries:
            ajout = random.randint(*Secteur.SEUIL_ACHAT[secteur])
            if secteur in self.besoins:
                self.besoins[secteur] += ajout
            else:
                self.besoins[secteur] = ajout

    def entreprise_choisie(self, entreprises_par_secteur, importance_dist):
        # Verifie si l'habitant à encore quelque chose à acheter
        if self.besoins:
            # Trouver le secteur prioritaire actuel (le 1er)
            secteur_prioritaire = next(iter(self.besoins))
            besoin = self.besoins[secteur_prioritaire]

            # Sélectionne l'entreprise ayant le score le plus faible
            meilleur_score = float('inf')
            meilleure_entreprise = None

            # Parcours toutes les entreprises
            for secteur in entreprises_par_secteur:
                for entreprise in entreprises_par_secteur[secteur]:
                    # Ne prends en compte que les secteurs prioritaires et dont l'achat est possible

                    if entreprise.secteur == secteur_prioritaire and self.budget >= entreprise.prix and entreprise.production > 0:

                        # Détermine la quantité de produit que l'habitant peut acheter
                        quantite_possible = min(entreprise.production, self.budget // entreprise.prix)
                        # Verifie qu'il est capable d'effectuer un achat dans cette entreprise
                        if quantite_possible > 0:
                            distance = ((self.rect.centerx - entreprise.rect.centerx) ** 2 +
                                        (self.rect.centery - entreprise.rect.centery) ** 2) ** 0.5

                            # Score basé sur prix + distance
                            score = entreprise.prix + importance_dist * distance

                            # Si cette entreprise permet de satisfaire le besoin en une fois, on donne un petit bonus au score
                            if quantite_possible >= besoin:
                                score *= 0.95  # bonus

                            # Selectionne le score le plus faible
                            if score < meilleur_score:
                                meilleur_score = score
                                meilleure_entreprise = entreprise

            # Si aucune entreprise ne produit dans le secteur prioritaire
            if not meilleure_entreprise:
                # On retire ce besoin
                del self.besoins[secteur_prioritaire]
                # Rechoisis l'entreprise à partir des besoins suivants
                self.entreprise_choisie(entreprises_par_secteur, importance_dist)
            else:
                self.target_entreprise = meilleure_entreprise


    def deplacer(self, vitesse, delta_temps):
        if self.target_entreprise:
            dx = self.target_entreprise.rect.centerx - self.x
            dy = self.target_entreprise.rect.centery - self.y
            d_totale = (dx ** 2 + dy ** 2) ** 0.5

            # Évite les divisions par 0
            if d_totale > 0:
                # Vitesse ajustée par distance pour interpolation douce
                deplacement = min((6.75 * delta_temps) * vitesse, d_totale)
                self.x += (dx / d_totale) * deplacement
                self.y += (dy / d_totale) * deplacement

            self.rect.centerx = int(self.x)
            self.rect.centery = int(self.y)


    def acheter(self):
        if self.target_entreprise is None:
            return
        # Si arriver à l'entreprise
        if (
                self.rect.centerx == self.target_entreprise.rect.centerx and self.rect.centery == self.target_entreprise.rect.centery):
            secteur = self.target_entreprise.secteur

            # Vérifier si le secteur est dans les besoins de l'habitant
            if secteur in self.besoins:

                # Calculer la quantité maximale que l'habitant peut acheter
                quantite_max = min(
                    self.budget // self.target_entreprise.prix,  # Budget disponible
                    self.target_entreprise.production,  # Production disponible
                    self.besoins[secteur]  # Besoin restant dans ce secteur
                )
                #print(self.besoins)
                if quantite_max > 0:
                    # Effectuer l'achat
                    self.target_entreprise.vendre(quantite_max)
                    self.budget -= quantite_max * self.target_entreprise.prix
                    self.besoins[secteur] -= quantite_max

                    # Si le besoin est satisfait, retirer le secteur de la liste des besoins
                    if self.besoins[secteur] == 0:
                        del self.besoins[secteur]

