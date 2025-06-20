import pygame
import random
import time
import numpy as np
from Habitant import *
from Entreprise import *
from Secteur import *
from collections import defaultdict
import csv
import Graphique
from Config import *
        
class Simulation:


    def save_to_csv(self):
        with open('data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Mois', 'IPC', 'Année(s)', 'Inflation'])
            for month in range(1, len(self.historique_ipc) + 1):
                ipc = self.historique_ipc[month - 1]
                year = ((month - 1) // 12) + 1
                inflation = ''
                if month % 12 == 0:
                    inflation_index = (month // 12) - 1
                    if inflation_index < len(self.historique_inflation):
                        inflation = self.historique_inflation[inflation_index]
                writer.writerow([month, ipc, year, inflation])

    def initialize_simulation(self, params):
        self.input_hab = params['n_hab']
        self.input_ent = params['n_ent']
        self.importance_dist = params['dist_importance']
        self.SMIC = params['smic']

        self.habitants = pygame.sprite.Group()
        self.entreprises = pygame.sprite.Group()

        for _ in range(self.input_hab):
            x, y = self.generer_point_en_france_selon_densite()
            habitant = Habitant(x, y, self.SMIC) 
            self.habitants.add(habitant)

        for _ in range(self.input_ent):
            x, y = self.generer_point_en_france_selon_densite()
            entreprise = Entreprise(x, y)
            self.entreprises.add(entreprise)
            entreprise.planifier_production_cournot(self.entreprises, self.habitants)
            
        self.entreprises_par_secteur = defaultdict(list)
        for e in self.entreprises:
            self.entreprises_par_secteur[e.secteur].append(e)

        self.cout_panier_base = None
        self.historique_ipc = []
        self.historique_inflation = []

    def __init__(self):
        pygame.init()

        self.largeur = 1920
        self.hauteur = 1080

        self.fenetre = pygame.display.set_mode((self.largeur, self.hauteur), pygame.SCALED | pygame.FULLSCREEN)
        

        self.started = False

        self.habitants   = pygame.sprite.Group()
        self.entreprises = pygame.sprite.Group()

        self.slider_rect = pygame.Rect(10, 868, 750, 20)
        self.handle_rect = pygame.Rect(10, 865, 25, 25)
        self.slider_dragging = False
        self.drag_offset_x = 0
        
        self.config = Config(self.slider_rect)
        
        self.fenetre = pygame.display.set_mode((self.largeur, self.hauteur), pygame.SCALED | pygame.FULLSCREEN)

        pygame.display.set_caption("Simulation Inflation")

        # Paramètres du graphe
        self.largeur_carte = 750
        self.hauteur_carte = 750

        self.image_rect = pygame.Rect((0,0,self.largeur_carte,self.hauteur_carte))

        # Taille du cadre où la carte sera affichée
        self.map_cadre_rect = pygame.Rect((10,
                                           100,

                                           self.largeur_carte,
                                           self.hauteur_carte))
        self.map_cadre = pygame.Surface((self.map_cadre_rect.width, self.map_cadre_rect.height))

        # Charger la carte de la france
        self.image = pygame.image.load("assets/france.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.largeur_carte, self.hauteur_carte))
        self.masque_france = pygame.mask.from_surface(self.image)

        try:
            self.densite_image = pygame.image.load("assets/france_densite.png").convert()
            self.densite_image = pygame.transform.scale(self.densite_image, (self.largeur_carte, self.hauteur_carte))
            self.densite_array = pygame.surfarray.array3d(self.densite_image)
        except FileNotFoundError:
            self.densite_array = np.full((self.hauteur_carte, self.largeur_carte, 3), 128)

        # Caractéristique de la carte aggrandissable
        self.zoom = 1.0 # Zoom actuel
        self.min_zoom = 0.7 # Zoom minimum possible
        self.max_zoom = 3.0 # Zoom maximum possible
        self.decale_x = 0 # Decale la carte horizontalement
        self.decale_y = 0 # Décale la carte verticalement

        self.dragging = False # Indique si on est en train de deplacer la carte
        self.drag_start = (0, 0) # Position initiale de la souris avant le deplacement de la carte



        #debug
        self.select_entreprises = None
        self.entreprises_proches = []

        # Calcul de l'inflation
        self.cout_panier_base = None
        self.historique_ipc = []
        self.historique_inflation = []

        # Initialiser le temps
        self.temps = 0  # Temps en mois
        self.debut_mois = time.time()  # Temps de début du mois
        self.vitesse = 1  # Vitesse à laquelle avance la simulation

        # Icone representant chaque secteur d'entreprise
        chemin = "assets/icones/"
        self.icones_secteur = {
            "alimentation": pygame.image.load(chemin+"alimentation.png").convert_alpha(),
            "logement": pygame.image.load(chemin+"logement.png").convert_alpha(),
            "transport": pygame.image.load(chemin+"transport.png").convert_alpha(),
            "vetement": pygame.image.load(chemin+"vetement.png").convert_alpha(),
            "soins": pygame.image.load(chemin+"soin.png").convert_alpha(),
            "boisson": pygame.image.load(chemin+"boisson.png").convert_alpha(),
            "meuble": pygame.image.load(chemin+"meuble.png").convert_alpha(),
            "loisir": pygame.image.load(chemin+"loisir.png").convert_alpha()
        }
        # Paramètre à initialiser par l'utilisateur



    # Boucle principale du programme
    def run(self):
        # Boucle principale
        clock = pygame.time.Clock()
        running = True
        pause = False
        temps_accumule_pause = 0  # Temps total passé en pause
        dernier_temps_pause = 0  # Moment où la pause a été activée
        self.debug = False
        temps_ecoule = 0

        while running:
            # Gestion des événements
            for event in pygame.event.get():

                #Attendre avant de démarrer la simulation
                self.config.handle_event(event)
                if not self.started:
                    if not self.config.active: 
                        self.initialize_simulation(self.config.params)  
                        self.started = True

                if event.type == pygame.QUIT:
                    running = False


                if self.config.request_start:
                    self.initialize_simulation(self.config.params)
                    self.started = True
                    self.config.request_start = False  

                elif self.config.request_stop:
                    self.started = False  
                    self.config.request_stop = False  
                    self.config.active = True  
                    return
                # Si une touche est appuyée
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
    
                    

                    #UNIQUEMENT POUR LE DEBUG
                    if event.key == pygame.K_a:
                        self.debug = not(self.debug)
                        self.select_entreprises = None

                    if event.key == pygame.K_SPACE:  # Si la touche espace est appuyée
                        pause = not(pause)
                        if pause:
                            dernier_temps_pause = time.time()
                        else:
                            temps_accumule_pause += time.time() - dernier_temps_pause

                # Si la molette est utiliser,
                elif event.type == pygame.MOUSEWHEEL:
                    ancien_zoom = self.zoom

                    # On zoom de 0.1 ou dezoom de 0.1 selon la molette
                    self.zoom += event.y * 0.1 # event.y = +1 molette haut, -1 bas
                    self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom)) # intervalle [min_zoom,max_zoom]

                    # Zoom centré sur la souris
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Coordonnée x de la souris par rapport à la carte
                    dx = mouse_x - self.image_rect.left
                    # Coordonnée y de la souris par rapport à la carte
                    dy = mouse_y - self.image_rect.top

                    # Déterminer de combien on decale l'image après le zoom
                    ratio_zoom = self.zoom / ancien_zoom # Ratio entre l'ancien et le nouveau degre de zoom
                    self.decale_x = ratio_zoom * (self.decale_x - dx) + dx
                    self.decale_y = ratio_zoom * (self.decale_y - dy) + dy

                # Si clique droit, autorise le deplacement sur la carte
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.handle_rect.collidepoint(event.pos):
                            self.slider_dragging = True
                            self.drag_offset_x = event.pos[0] - self.handle_rect.x
                        else:
                            self.dragging = True
                            self.drag_start = pygame.mouse.get_pos()


                        #debug
                        if self.debug:
                            for entreprise in self.entreprises:
                                if entreprise.rect.collidepoint(mouse_world_x, mouse_world_y):
                                    self.select_entreprises = entreprise
                                    self.entreprises_proches = entreprise.liste_entreprises_proches(self.entreprises)
                                    break
                            else:
                                self.select_entreprises = None
                                self.entreprises_proches = []

                # Si clique droit soulevé, arrete le deplacement sur la carte
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                        self.slider_dragging = False

                # Si la souris est en mouvement
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        dx, dy = event.rel
                        self.decale_x -= dx
                        self.decale_y -= dy
                    elif self.slider_dragging:
                        mouse_x = event.pos[0]
                        new_x = mouse_x - self.drag_offset_x
                        new_x = max(self.slider_rect.left, min(new_x, self.slider_rect.right - self.handle_rect.width))
                        self.handle_rect.x = new_x
                        pos = (new_x - self.slider_rect.left) / (self.slider_rect.width - self.handle_rect.width)
                        self.vitesse = pos * 99 + 1



            # Détecte si l'utilisateur survole une entreprise
            detail_entreprise = None
            mouse_pos = pygame.mouse.get_pos()

            # Vérifie si la souris est dans le cadre de la simulation
            if self.map_cadre_rect.collidepoint(mouse_pos):
                # Coordonnées de la souris par rapport au cadre
                mouse_rel_x = mouse_pos[0] - self.map_cadre_rect.left
                mouse_rel_y = mouse_pos[1] - self.map_cadre_rect.top

                # Ajuster les coordonnées selon les zoom/decalage
                mouse_world_x = (mouse_rel_x + self.decale_x) / self.zoom
                mouse_world_y = (mouse_rel_y + self.decale_y) / self.zoom

                for entreprise in self.entreprises:
                    # Si collision entre l'entreprise et la souris
                    if entreprise.rect.collidepoint(mouse_world_x, mouse_world_y):
                        # Stocke l'entreprise survoler
                        detail_entreprise = entreprise
                        break
            if self.started:
                # durée d'un mois en fonction de la vitesse de simulation
                duree_mois = 15 / self.vitesse
                if not pause:
                    temps_ecoule = (time.time() - self.debut_mois) - temps_accumule_pause
                    # Vérifier si un mois s'est écoulé
                    if temps_ecoule >= duree_mois:
                        self.passage_mois_suivant()  # Passer au mois suivant
                        self.debut_mois = time.time()  # Réinitialiser l'heure de début du mois
                        temps_accumule_pause = 0

                    delta_temps = clock.get_time() / 1000.0  # secondes entre chaques frames
                    for entreprise in self.entreprises.sprites():
                        entreprise.step(self.entreprises,self.vitesse,delta_temps)

                    for habitant in self.habitants:
                        habitant.entreprise_choisie(self.entreprises_par_secteur, self.importance_dist)
                        

                        #STEP : Action de l'habitant
                        habitant.deplacer(self.vitesse, delta_temps)
                        habitant.acheter()



            # Remplir l'écran avec une couleur noire
            self.fenetre.fill(NOIR)

            # Dessiner le champ de simulation   
            self.config.draw(self.fenetre)  
            self.draw_simulation()

            # Afficher le temps écoulé
            texte_temps = self.afficher_temps()
            font = pygame.font.SysFont("Trebuchet MS", 32)
            texte_surface = font.render(texte_temps, True, BLANC)
            self.fenetre.blit(texte_surface, (15, 65))  # Afficher en haut à droite

            textsr = font.render(str(float("{:.2f}".format(temps_ecoule))), True, BLANC)
            self.fenetre.blit(textsr, (680, 65))  # Afficher en haut à droite

            # Afficher les details de l'entreprise survolé
            if detail_entreprise:
                self.afficher_entreprise(detail_entreprise)

            # Mettre à jour l'affichage
            
            pygame.display.flip()

            # Limiter la fréquence d'affichage
            clock.tick(60)

        # Quitter Pygame
        pygame.quit()


        self.save_to_csv()
        Graphique.plot_graphs()
    # METHODE : Génère les agents sur la carte (zone terrestre)
    def generer_point_en_france_selon_densite(self):
        while True:
            dx = random.randint(0, self.largeur_carte - 1)
            dy = random.randint(0, self.hauteur_carte - 1)
            
            if self.masque_france.get_at((dx, dy)):
                try:
                    if len(self.densite_array.shape) == 3:  # Si RGB
                        densite = self.densite_array[dy, dx, 0]  
                    else:  
                        densite = self.densite_array[dy, dx]
                    probabilite = (255 - densite) / 255.0  
                    if random.random() < probabilite * 1.2: 
                        x = dx + self.image_rect.left
                        y = dy + self.image_rect.top
                        
                        return x, y
                except IndexError:
                    continue

    # METHODE : Réalise la simulation permettant de determimner l'inflation annuelle du pays
    def draw_simulation(self):

        # Nettoie la surface
        self.map_cadre.fill((25,25,25))  # fond gris

        # Redimmensionne l'image par rapport au degre de zoom
        zoomed_width = int(self.largeur_carte * self.zoom)
        zoomed_height = int(self.hauteur_carte * self.zoom)
        zoomed_image = pygame.transform.scale(self.image, (zoomed_width, zoomed_height))

        # Détermine les coordonnées de l'image apres decalage
        dest_rect = zoomed_image.get_rect()
        dest_rect.x = (self.image_rect.left - self.decale_x)
        dest_rect.y = (self.image_rect.top - self.decale_y)

        self.map_cadre.blit(zoomed_image, dest_rect)

        # Dessiner les agents (habitants et entreprises)
        self.draw_agents()
        
        pygame.draw.rect(self.fenetre, BLANC, self.slider_rect)
        pygame.draw.circle(self.fenetre, ROUGE, self.handle_rect.center, self.handle_rect.width //2, 0)
        font = pygame.font.SysFont("Trebuchet Ms", 24)
        text = font.render(f"Vitesse: {int(self.vitesse)}x", True, BLANC)
        self.fenetre.blit(text, (self.slider_rect.right + 10, self.slider_rect.centery - 10))
        self.fenetre.blit(self.map_cadre, self.map_cadre_rect.topleft)
    

        # Dessine le cadre visuel (bordure)
        pygame.draw.rect(self.fenetre, BLANC, self.map_cadre_rect, 5)  # contour blanc

    # METHODE : Dessine les agents sur la carte de simulation
    def draw_agents(self):
        # Dessine les entreprises
        for entreprise in self.entreprises:
            # Ajuste ses coordonnées si deplacement/zoom de la carte
            x = entreprise.rect.centerx * self.zoom - self.decale_x
            y = entreprise.rect.centery * self.zoom - self.decale_y

            # Selectionne le secteur de l'entreprise ainsi que l'icone associé
            secteur = entreprise.secteur
            icone = self.icones_secteur.get(secteur)


            
            # Redimensionner l'icone en 20*20
            icone = pygame.transform.scale(icone, (25, 25))
            # Dessiner l'icône
            self.map_cadre.blit(icone, (x - 8, y - 8))


        #debug
        if self.select_entreprises and self.debug:
            x = self.select_entreprises.rect.centerx * self.zoom - self.decale_x
            y = self.select_entreprises.rect.centery * self.zoom - self.decale_y
            rayon = entreprise.distance_max * self.zoom
            pygame.draw.circle(self.map_cadre, ROUGE, (int(x), int(y)), int(rayon), 3)
            
            for entreprise_info in self.entreprises_proches:
                entreprise = entreprise_info[0]
                ex = entreprise.rect.centerx * self.zoom - self.decale_x
                ey = entreprise.rect.centery * self.zoom - self.decale_y
                pygame.draw.rect(self.map_cadre, VERT, (ex - 12, ey - 12, 25, 25), 2)

        # Dessine les habitants
        if not self.debug:
            for habitant in self.habitants:
                # Ajuste ses coordonnées si deplacement/zoom de la carte
                x = habitant.rect.centerx * self.zoom - self.decale_x
                y = habitant.rect.centery * self.zoom - self.decale_y
                # Dessine l'habitant sous forme d'un carré rouge
                if habitant.classe == 0:
                    pygame.draw.rect(self.map_cadre, ROUGE, pygame.Rect(x - 2, y - 2, 5, 5))
                elif habitant.classe == 1:
                    pygame.draw.rect(self.map_cadre, ORANGE, pygame.Rect(x - 2, y - 2, 5, 5))
                elif habitant.classe == 2:
                    pygame.draw.rect(self.map_cadre, VERT, pygame.Rect(x - 2, y - 2, 5, 5))
                elif habitant.classe == 3:
                    pygame.draw.rect(self.map_cadre, VIOLET, pygame.Rect(x - 2, y - 2, 5, 5))

    # METHODE : Effectue les opérations nécessaire durant chaque changement de mois
    def passage_mois_suivant(self):
        self.temps += 1  # Incrémenter le temps de 1 mois



        ###########################################################################


        #CODE A NE PAS EXECUTER DANS LA VERSION FINALE
        #SERT JUSTE A AVOIR UNE INFLATION "PLUS REALISTE"
        #MAIS SI EST ACTIVE, CE N'EST PLUS UN MODELE A AGENT.
        #Pour les correcteurs, merci de ne pas tenir compte de ce code

        evenement_aleatoire = True #Laissez à False.
        if evenement_aleatoire:
            #FAILLITE
            if random.random() < 0.05:  # 5% de chance par mois 
                secteur_impacte = random.choice(list(Secteur.SECTEURS.keys()))
                for e in self.entreprises_par_secteur[secteur_impacte]:
                    if random.random() < 0.3:
                        e.production = 0  # Arrêt temporaire
            #HAUSSE DES PRIX QUELCONQUES SUR UN SECTEUR
            if random.random() < 0.1:  # 10% de chance par mois
                secteur = random.choice(list(Secteur.SECTEURS.keys()))
                for e in self.entreprises_par_secteur[secteur]:
                    e.prix *= 1.20  # Hausse de 20% dans le secteur
        ##################################################################


        for entreprise in self.entreprises.sprites():
            entreprise.planifier_production_cournot(self.entreprises,self.habitants)
        for habitant in self.habitants.sprites():
            habitant.budget += habitant.revenu
            habitant.ajouter_besoins()

        # Calculer l'IPC du mois actuel
        ipc_actuel = self.calculer_ipc()

        # Calculer l'inflation annuelle tous les 12 mois
        if self.temps//12 > (self.temps-1)//12:
            self.calculer_inflation_annuelle()
            
            

    # METHODE : Affiche sur la fenetre le temps en année et mois
    def afficher_temps(self):
        # Convertir le temps en années et mois
        annees = self.temps // 12
        mois = self.temps % 12
        return f"Temps écoulé : {annees} an(s) et {mois} mois"

    # METHODE: Affiche les caractéristiques de l'entreprise
    def afficher_entreprise(self, entreprise):
        """Affiche les caractéristiques d'une entreprise dans une infobulle."""

        # Stocke les infos de l'entreprise sous forme de str
        font = pygame.font.SysFont("Lucida Console", 28)
        infos = [
            f"Type: {entreprise.TYPES[entreprise.type]}",
            f"Secteur: {entreprise.secteur}",
            f"Prix: {entreprise.prix:.2f}€",
            f"Capital: {entreprise.fond:.2f}€",
            f"Production: {int(entreprise.production)}",
            f"Coordonnées: {entreprise.x, entreprise.y}"
        ]

        # Calcul de la taille de l'infobulle par rapport au contenu
        width = max(font.size(info)[0] for info in infos) #détermine la largeur le plus grande parmi les infos
        height = len(infos) * font.get_linesize() # détermine la hauteur de la

        # Création de l'infobulle
        infobulle = pygame.Surface((width + 20, height + 20), pygame.SRCALPHA) # Création de la surface
        infobulle.fill((240, 240, 240, 200))  # Colore le fond (avec transparence)
        pygame.draw.rect(infobulle, (0, 0, 0, 100), (0, 0, width + 20, height + 20), 2)  # Dessine la bordure

        # Remplir l'infobulle des infos
        ligne_pixel = 10
        for info in infos:
            text = font.render(info, True, (0, 0, 0)) # Génère une surface avec le texte
            infobulle.blit(text, (10, ligne_pixel)) # Dessine le texte sur l'infobulle
            ligne_pixel += font.get_linesize() # on passe à la ligne suivante en rajoutant l'equivalent de 1 ligne de pixels

        # Positionne l'infobulle
        mouse_x, mouse_y = pygame.mouse.get_pos() # Récupère les coordonnées de la souris
        pos_x = min(mouse_x + 15, self.largeur - width - 30)  # Ne dépasse pas à droite
        pos_y = max(mouse_y - 10, 0)  # Ne dépasse pas en haut

        self.fenetre.blit(infobulle, (pos_x, pos_y))

    # METHODE : Calcule l'inflation annuelle
    def calculer_inflation_annuelle(self):
        if len(self.historique_ipc) < 13:
            return None  # pas assez de données pour 12 mois complets

        ipc_debut = self.historique_ipc[-13]
        ipc_fin   = self.historique_ipc[-1]
        inflation = ((ipc_fin - ipc_debut) / ipc_debut) * 100

        self.historique_inflation.append(inflation)
        return inflation

    # METHODE : Calcule l'IPC mensuelle
    def calculer_ipc(self):
        prix_moyens = self.calculer_prix_moyens()
        cout_actuel = self.calculer_cout_panier(prix_moyens)

        # Initialise le cout de base
        if self.cout_panier_base is None:
            self.cout_panier_base = cout_actuel

        # Détermine l'IPC du mois
        ipc = (cout_actuel / self.cout_panier_base) * 100

        # On enregistre l'ipc
        self.historique_ipc.append(ipc)
        return ipc

    # METHODE : Calcul le prix de vente moyen des entreprises dans chaque secteur
    def calculer_prix_moyens(self):
        prix_moyens = {}
        # On parcours tous les secteurs
        for secteur in Secteur.SECTEURS.keys():
            # Stocke les entreprises de meme secteur
            entreprises_secteur = [e for e in self.entreprises if e.secteur == secteur]
            # Vérifie s'il y a des entreprises dans ce secteur
            if entreprises_secteur:
                # Calcule le prix moyen du secteur
                prix_moyens[secteur] = sum(e.prix for e in entreprises_secteur) / len(entreprises_secteur)
            else:
                # Sinon le prix de vente est nulle
                prix_moyens[secteur] = 0
        return prix_moyens

    # METHODE : Somme des prix de ventes moyennes dans chaque secteur (prends en compte leurs pondérations)
    def calculer_cout_panier(self, prix_moyens):
        cout_total = 0
        for secteur, prix in prix_moyens.items():
            cout_total += prix * Secteur.PONDERATIONS[secteur]
        return cout_total

# Point d'entrée du programme
if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()