from __future__ import annotations  


class ObjetSimulation:
    def __init__(self, identifiant, nom, table, valeur=0.0, etat=''):  #initialise un objet de simulation
        self.identifiant = identifiant  #identifiant unique de l'objet
        self.nom = nom  #nom de l'objet
        self.table = table  #nom de la table associée 
        self.valeur = float(valeur)  #valeur numérique initiale
        self.etat = etat  #état textuel initial
        self.colonnes = {}  #dictionnaire pour stocker d'autres colonnes ou attributs

    def copier(self):  #crée une copie complète de l'objet
        copie = ObjetSimulation(self.identifiant, self.nom, self.table, self.valeur, self.etat)  #copie les attributs de base
        copie.colonnes = dict(self.colonnes)  #copie le dictionnaire des colonnes
        return copie  #retourne l'objet copié


class Evenement:
    def __init__(self, ligne):  #initialise un événement à partir d'une ligne de données
        self.id = ligne['id']  #identifiant unique
        self.nom = ligne['nom']  #nom de l'événement
        self.objet_cause_id = ligne['objet_cause_id']  #ID de l'objet qui déclenche l'événement
        self.colonne_cause = ligne['colonne_cause']  #colonne à tester sur l'objet cause
        self.operateur = ligne['operateur']  #opérateur de comparaison (=, <, >)
        self.valeur_cause = ligne['valeur_cause']  #valeur attendue pour la cause
        self.objet_effet_id = ligne['objet_effet_id']  #ID de l'objet affecté
        self.colonne_effet = ligne['colonne_effet']  #colonne affectée
        self.action = ligne['action']  #type d'action (op, change, inv)
        self.valeur_effet = ligne['valeur_effet']  #valeur de l'effet
        self.proba = float(ligne['proba'])  #probabilité de déclenchement
        self.arrivee = int(ligne['arrivee'])  #tour d'arrivée de l'événement
        self.propagation = int(ligne['propagation'])  #distance de propagation dans le graphe
        self.actif = int(ligne['actif'])  #indique si l'événement est actif (1) ou désactivé (0)


class Paterne:
    def __init__(self, ligne):  #niitialise un paterne 
        self.id = ligne['id']  #identifiant unique
        self.nom = ligne['nom']  #nom du paterne
        self.objet_effet_id = ligne['objet_effet_id']  #ID de l'objet affecté
        self.colonne_effet = ligne['colonne_effet']  #colonne affectée
        self.action = ligne['action']  #type d'action (op, change, inv)
        self.valeur_effet = ligne['valeur_effet']  # valeur appliquée par le paterne
        self.frequence = str(ligne['frequence']).strip()  #fréquence du paterne
        self.actif = int(ligne['actif'])  #indique si le paterne est actif (1) ou désactivé (0)
