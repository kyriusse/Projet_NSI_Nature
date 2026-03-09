"""Outils de graphe : liste d'adjacence, matrice, BFS, DFS, SVG."""

from __future__ import annotations

import math
from collections import deque


def construire_graphe(objets, liaisons):
    graphe = {obj["nom"]: [] for obj in objets}
    poids_aretes = {}

    for liaison in liaisons:
        source = liaison["source_nom"]
        cible = liaison["cible_nom"]
        poids = float(liaison["poids"])
        type_liaison = liaison["type_liaison"]

        graphe[source].append(cible)
        poids_aretes[(source, cible)] = poids

        if type_liaison == "<=>":
            graphe[cible].append(source)
            poids_aretes[(cible, source)] = poids

    for nom in graphe:
        graphe[nom] = sorted(set(graphe[nom]))

    return graphe, poids_aretes


def parcours_bfs(graphe, depart):
    if depart not in graphe:
        return []

    visites = []
    vus = {depart}
    file_attente = deque([depart])

    while file_attente:
        sommet = file_attente.popleft()
        visites.append(sommet)
        for voisin in graphe.get(sommet, []):
            if voisin not in vus:
                vus.add(voisin)
                file_attente.append(voisin)

    return visites


def parcours_dfs(graphe, depart, visites=None):
    if depart not in graphe:
        return []

    if visites is None:
        visites = []

    visites.append(depart)
    for voisin in graphe.get(depart, []):
        if voisin not in visites:
            parcours_dfs(graphe, voisin, visites)
    return visites


def trouver_chemin(graphe, depart, arrivee):
    if depart not in graphe or arrivee not in graphe:
        return []

    file_attente = deque([(depart, [depart])])
    vus = {depart}

    while file_attente:
        sommet, chemin = file_attente.popleft()
        if sommet == arrivee:
            return chemin
        for voisin in graphe.get(sommet, []):
            if voisin not in vus:
                vus.add(voisin)
                file_attente.append((voisin, chemin + [voisin]))

    return []


def composantes_connexes_orientees_simple(graphe):
    """
    Ici on regarde surtout les reseaux visibles :
    on considere une version non orientee pour regrouper les objets lies.
    """
    graphe_non_oriente = {sommet: set() for sommet in graphe}
    for sommet, voisins in graphe.items():
        for voisin in voisins:
            graphe_non_oriente[sommet].add(voisin)
            graphe_non_oriente[voisin].add(sommet)

    composantes = []
    vus = set()

    for sommet in graphe_non_oriente:
        if sommet in vus:
            continue
        composante = []
        file_attente = deque([sommet])
        vus.add(sommet)
        while file_attente:
            courant = file_attente.popleft()
            composante.append(courant)
            for voisin in sorted(graphe_non_oriente[courant]):
                if voisin not in vus:
                    vus.add(voisin)
                    file_attente.append(voisin)
        composantes.append(sorted(composante))

    return composantes


def matrice_adjacence(objets, graphe):
    noms = [obj["nom"] for obj in objets]
    matrice = []
    for source in noms:
        ligne = []
        for cible in noms:
            ligne.append(1 if cible in graphe.get(source, []) else 0)
        matrice.append(ligne)
    return noms, matrice


def svg_graphe(objets, graphe, poids_aretes, reseau_index=None):
    noms = [obj["nom"] for obj in objets]
    if not noms:
        return "<svg width='700' height='300'></svg>"

    largeur = 760
    hauteur = 420
    cx = largeur // 2
    cy = hauteur // 2
    rayon = min(largeur, hauteur) // 3

    positions = {}
    total = len(noms)
    for indice, nom in enumerate(noms):
        angle = 2 * math.pi * indice / total
        x = cx + int(rayon * math.cos(angle))
        y = cy + int(rayon * math.sin(angle))
        positions[nom] = (x, y)

    lignes = [f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>"]
    lignes.append("<defs><marker id='fleche' markerWidth='10' markerHeight='10' refX='10' refY='3' orient='auto'><path d='M0,0 L10,3 L0,6 z' fill='#374151' /></marker></defs>")

    for source, voisins in graphe.items():
        x1, y1 = positions[source]
        for cible in voisins:
            x2, y2 = positions[cible]
            lignes.append(
                f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='#64748b' stroke-width='2' marker-end='url(#fleche)' />"
            )
            poids = poids_aretes.get((source, cible), 1)
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            lignes.append(f"<text x='{mx}' y='{my}' font-size='12' fill='#334155'>{poids}</text>")

    for nom in noms:
        x, y = positions[nom]
        lignes.append(f"<circle cx='{x}' cy='{y}' r='24' fill='#dbeafe' stroke='#1d4ed8' stroke-width='2' />")
        lignes.append(f"<text x='{x}' y='{y+4}' text-anchor='middle' font-size='14' fill='#0f172a'>{nom}</text>")

    lignes.append("</svg>")
    return "".join(lignes)
