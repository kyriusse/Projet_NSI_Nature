from __future__ import annotations  

import math  #pour les calculs trigonométriques (cos, sin, pi)
from structures_nsi import File, Pile  #import des structures de données File et Pile définies ailleurs


def construire_graphe(objets_catalogue, liaisons):  #construit un graphe à partir des objets et des liaisons
    graphe = {ligne['nom']: [] for ligne in objets_catalogue}  #initialise un dictionnaire avec chaque objet
    poids = {}  #dictionnaire pour stocker les poids des arcs
    conservations = {}  #dictionnaire pour stocker les règles de conservation
    for liaison in liaisons:  #parcourt chaque liaison
        source = liaison['source_nom']  #nom de l'objet source
        cible = liaison['cible_nom']  #nom de l'objet cible
        graphe.setdefault(source, []).append(cible)  #ajoute la cible à la liste des voisins de la source
        poids[(source, cible)] = float(liaison['poids'])  #stocke le poids de l'arc
        conservations[(source, cible)] = liaison['conservation']  #stocke la règle de conservation
        if liaison['type_liaison'] == '<=>':  #si la liaison a deux directions 
            graphe.setdefault(cible, []).append(source)  #ajoute la source comme voisin de la cible
            poids[(cible, source)] = float(liaison['poids'])  #même poids pour l'arc inverse
            conservations[(cible, source)] = liaison['conservation']  #même règle pour l'arc inverse
    for nom in graphe:  #tri des voisins pour chaque objet
        graphe[nom] = sorted(set(graphe[nom]))
    return graphe, poids, conservations  #retourne le graphe, les poids et les conservations


def matrice_adjacence(graphe, noms):  #crée la matrice d'adjacence du graphe
    lignes = []  #liste pour chaque ligne de la matrice
    for nom_ligne in noms:  #parcourt chaque ligne
        valeurs = []  #liste des valeurs de la ligne
        for nom_colonne in noms:  #parcourt chaque colonne
            valeurs.append(1 if nom_colonne in graphe.get(nom_ligne, []) else 0)  #1 si arc existe 0 sinon
        lignes.append({'nom': nom_ligne, 'valeurs': valeurs})  #ajoute la ligne à la matrice
    return {'noms': noms, 'lignes': lignes}  #retourne la matrice complète


def parcours_largeur(graphe, depart):  #parcours en largeur depuis un noeud
    file_attente = File()  #file pour le parcours
    vus = set()  #ensemble des noeuds déjà vus
    ordre = []  #liste pour stocker l'ordre de visite
    if depart not in graphe:  #si le noeud de départ n'existe pas
        return ordre
    file_attente.enfiler(depart)  #ajoute le départ à la file
    vus.add(depart)  #marque le départ comme vu
    while not file_attente.est_vide():  #tant que la file n'est pas vide
        courant = file_attente.defiler()  #défile un noeud
        ordre.append(courant)  #ajoute le noeud à l'ordre de visite
        for voisin in graphe.get(courant, []):  #parcourt les voisins
            if voisin not in vus:  #si le voisin n'a pas été vu
                vus.add(voisin)  #marque le voisin comme vu
                file_attente.enfiler(voisin)  #ajoute le voisin à la file
    return ordre  #retourne l'ordre de visite


def parcours_profondeur(graphe, depart):  #parcours en profondeur depuis un noeud
    pile = Pile()  #pile pour le parcours
    vus = set()  # ensemble des noeuds déjà vus
    ordre = []  # liste pour stocker l'ordre de visite
    if depart not in graphe:  #si le noeud de départ n'existe pas
        return ordre
    pile.empiler(depart)  # empile le départ
    while not pile.est_vide():  #tant que la pile n'est pas vide
        courant = pile.depiler()  #dépile un noeud
        if courant in vus:  # si déjà vu ignorer
            continue
        vus.add(courant)  # marque le noeud comme vu
        ordre.append(courant)  #ajoute le noeud à l'ordre de visite
        for voisin in reversed(graphe.get(courant, [])):  #parcourt les voisins en ordre inverse
            if voisin not in vus:  #si le voisin n'a pas été vu
                pile.empiler(voisin)  # empile le voisin
    return ordre  #retourne l'ordre de visite


def svg_graphe(objets_catalogue, graphe, poids):  #génère un SVG pour visualiser le graphe
    noms = [ligne['nom'] for ligne in objets_catalogue]  #liste des noms d'objets
    if not noms:  #si pas d'objet
        return "<svg width='640' height='220'></svg>"  #SVG vide
    largeur = 760  #largeur du SVG
    hauteur = 420  #hauteur du SVG
    centre_x = largeur // 2  #coordonnée X du centre
    centre_y = hauteur // 2  #coordonnée Y du centre
    rayon = 140  #rayon pour disposer les noeuds en cercle
    positions = {}  #dictionnaire des positions des noeuds
    for indice, nom in enumerate(noms):  #parcourt les objets
        angle = (2 * math.pi * indice) / len(noms)  #angle pour placer le noeud
        positions[nom] = (centre_x + int(math.cos(angle) * rayon), centre_y + int(math.sin(angle) * rayon))  #coordonnées
    lignes = [f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>"]  #balise SVG de départ
    lignes.append("<defs><marker id='fleche' markerWidth='10' markerHeight='10' refX='10' refY='3' orient='auto'><path d='M0,0 L10,3 L0,6 z' fill='#475569'/></marker></defs>")  #flèche pour les arcs
    for source, voisins in graphe.items():  #parcourt chaque arc
        for cible in voisins:
            x1, y1 = positions[source]  #coordonnées source
            x2, y2 = positions[cible]  #coordonnées cible
            lignes.append(f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='#94a3b8' stroke-width='2' marker-end='url(#fleche)'/>")  #trace l'arc
            lignes.append(f"<text x='{(x1+x2)/2}' y='{(y1+y2)/2}' font-size='12' fill='#334155'>{poids.get((source, cible), 1)}</text>")  #affiche le poids
    for nom, (x, y) in positions.items():  #parcourt chaque noeud
        lignes.append(f"<circle cx='{x}' cy='{y}' r='26' fill='#eff6ff' stroke='#2563eb' stroke-width='2'/>")  #dessine le cercle
        lignes.append(f"<text x='{x}' y='{y+4}' text-anchor='middle' font-size='13' fill='#0f172a'>{nom}</text>")  #étiquette du noeud
    lignes.append('</svg>')  #ferme la balise SVG
    return ''.join(lignes)  #retourne le SVG complet
