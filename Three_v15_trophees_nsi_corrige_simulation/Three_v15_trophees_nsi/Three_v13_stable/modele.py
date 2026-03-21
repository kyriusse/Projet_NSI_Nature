from __future__ import annotations


class ObjetSimulation:
    def __init__(self, identifiant, nom, table, valeur=0.0, etat=''):
        self.identifiant = identifiant
        self.nom = nom
        self.table = table
        self.valeur = float(valeur)
        self.etat = etat
        self.colonnes = {}

    def copier(self):
        copie = ObjetSimulation(self.identifiant, self.nom, self.table, self.valeur, self.etat)
        copie.colonnes = dict(self.colonnes)
        return copie


class Evenement:
    def __init__(self, ligne):
        self.id = ligne['id']
        self.nom = ligne['nom']
        self.objet_cause_id = ligne['objet_cause_id']
        self.colonne_cause = ligne['colonne_cause']
        self.operateur = ligne['operateur']
        self.valeur_cause = ligne['valeur_cause']
        self.objet_effet_id = ligne['objet_effet_id']
        self.colonne_effet = ligne['colonne_effet']
        self.action = ligne['action']
        self.valeur_effet = ligne['valeur_effet']
        self.proba = float(ligne['proba'])
        self.arrivee = int(ligne['arrivee'])
        self.propagation = int(ligne['propagation'])
        self.actif = int(ligne['actif'])


class Paterne:
    def __init__(self, ligne):
        self.id = ligne['id']
        self.nom = ligne['nom']
        self.objet_effet_id = ligne['objet_effet_id']
        self.colonne_effet = ligne['colonne_effet']
        self.action = ligne['action']
        self.valeur_effet = ligne['valeur_effet']
        self.frequence = int(ligne['frequence'])
        self.actif = int(ligne['actif'])
