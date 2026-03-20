from __future__ import annotations

import math
from structures_nsi import File, Pile


def construire_graphe(objets_catalogue, liaisons):
    graphe = {ligne['nom']: [] for ligne in objets_catalogue}
    poids = {}
    conservations = {}
    for liaison in liaisons:
        source = liaison['source_nom']
        cible = liaison['cible_nom']
        graphe.setdefault(source, []).append(cible)
        poids[(source, cible)] = float(liaison['poids'])
        conservations[(source, cible)] = liaison['conservation']
        if liaison['type_liaison'] == '<=>':
            graphe.setdefault(cible, []).append(source)
            poids[(cible, source)] = float(liaison['poids'])
            conservations[(cible, source)] = liaison['conservation']
    for nom in graphe:
        graphe[nom] = sorted(set(graphe[nom]))
    return graphe, poids, conservations


def matrice_adjacence(graphe, noms):
    lignes = []
    for nom_ligne in noms:
        valeurs = []
        for nom_colonne in noms:
            valeurs.append(1 if nom_colonne in graphe.get(nom_ligne, []) else 0)
        lignes.append({'nom': nom_ligne, 'valeurs': valeurs})
    return {'noms': noms, 'lignes': lignes}


def parcours_largeur(graphe, depart):
    file_attente = File()
    vus = set()
    ordre = []
    if depart not in graphe:
        return ordre
    file_attente.enfiler(depart)
    vus.add(depart)
    while not file_attente.est_vide():
        courant = file_attente.defiler()
        ordre.append(courant)
        for voisin in graphe.get(courant, []):
            if voisin not in vus:
                vus.add(voisin)
                file_attente.enfiler(voisin)
    return ordre


def parcours_profondeur(graphe, depart):
    pile = Pile()
    vus = set()
    ordre = []
    if depart not in graphe:
        return ordre
    pile.empiler(depart)
    while not pile.est_vide():
        courant = pile.depiler()
        if courant in vus:
            continue
        vus.add(courant)
        ordre.append(courant)
        for voisin in reversed(graphe.get(courant, [])):
            if voisin not in vus:
                pile.empiler(voisin)
    return ordre


def svg_graphe(objets_catalogue, graphe, poids):
    noms = [ligne['nom'] for ligne in objets_catalogue]
    if not noms:
        return "<svg width='640' height='220'></svg>"
    largeur = 760
    hauteur = 420
    centre_x = largeur // 2
    centre_y = hauteur // 2
    rayon = 140
    positions = {}
    for indice, nom in enumerate(noms):
        angle = (2 * math.pi * indice) / len(noms)
        positions[nom] = (centre_x + int(math.cos(angle) * rayon), centre_y + int(math.sin(angle) * rayon))
    lignes = [f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>"]
    lignes.append("<defs><marker id='fleche' markerWidth='10' markerHeight='10' refX='10' refY='3' orient='auto'><path d='M0,0 L10,3 L0,6 z' fill='#475569'/></marker></defs>")
    for source, voisins in graphe.items():
        for cible in voisins:
            x1, y1 = positions[source]
            x2, y2 = positions[cible]
            lignes.append(f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='#94a3b8' stroke-width='2' marker-end='url(#fleche)'/>")
            lignes.append(f"<text x='{(x1+x2)/2}' y='{(y1+y2)/2}' font-size='12' fill='#334155'>{poids.get((source, cible), 1)}</text>")
    for nom, (x, y) in positions.items():
        lignes.append(f"<circle cx='{x}' cy='{y}' r='26' fill='#eff6ff' stroke='#2563eb' stroke-width='2'/>")
        lignes.append(f"<text x='{x}' y='{y+4}' text-anchor='middle' font-size='13' fill='#0f172a'>{nom}</text>")
    lignes.append('</svg>')
    return ''.join(lignes)
