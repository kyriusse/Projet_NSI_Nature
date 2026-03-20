from __future__ import annotations

from random import random

from graphe import construire_graphe, parcours_largeur
from modele import Evenement, ObjetSimulation, Paterne


def objets_etat(objets):
    resultat = {}
    for ligne in objets:
        nom_table = ligne.get('nom_table', '')
        valeur = ligne.get('valeur', 0)
        etat = ligne.get('etat', '')
        objet = ObjetSimulation(
            ligne['id'],
            ligne['nom'],
            nom_table,
            valeur,
            etat
        )
        for cle in ligne:
            if cle not in ['id', 'nom', 'nom_table', 'valeur', 'etat']:
                objet.colonnes[cle] = ligne[cle]
        resultat[ligne['id']] = objet
    return resultat


def lire_cible(objet, colonne):
    if colonne == 'valeur':
        return objet.valeur
    if colonne == 'etat':
        return objet.etat
    return objet.colonnes.get(colonne, '')


def ecrire_cible(objet, colonne, valeur):
    if colonne == 'valeur':
        objet.valeur = float(valeur)
    elif colonne == 'etat':
        objet.etat = str(valeur)
    else:
        objet.colonnes[colonne] = valeur


def condition_valide(objet, colonne, operateur, valeur):
    courant = lire_cible(objet, colonne)
    try:
        gauche = float(str(courant).replace(',', '.'))
        droite = float(str(valeur).replace(',', '.'))
    except Exception:
        gauche = str(courant)
        droite = str(valeur)
    if operateur == '=':
        return gauche == droite
    if operateur == '<':
        return gauche < droite
    if operateur == '>':
        return gauche > droite
    return False


def parser_nombre_operation(valeur_effet):
    texte = str(valeur_effet).strip()
    if len(texte) < 2:
        return '', 0
    return texte[0], float(texte[1:].replace(',', '.'))


def valeur_conservee(valeur_effet, expression, profondeur=1):
    texte = str(expression).strip().lower().replace(' ', '')
    if texte in ('', 'n'):
        return valeur_effet
    signe, nombre = parser_nombre_operation(valeur_effet)
    if signe == '':
        return valeur_effet
    if texte.startswith('n/'):
        diviseur = float(texte.split('/', 1)[1].replace(',', '.'))
        if diviseur != 0:
            return signe + str(nombre / (diviseur ** profondeur))
    if texte.endswith('/n'):
        multiplicateur = texte[:-2]
        try:
            coeff = float(multiplicateur.replace(',', '.')) if multiplicateur else 1
        except Exception:
            coeff = 1
        return signe + str(nombre * coeff)
    return valeur_effet


def appliquer_action(objet, colonne, action, valeur_effet, table_inversion):
    journal = ''
    courant = lire_cible(objet, colonne)
    if action == 'op':
        signe = str(valeur_effet)[0]
        nombre = float(str(valeur_effet)[1:].replace(',', '.'))
        base = float(courant)
        if signe == '+':
            base += nombre
        elif signe == '-':
            base -= nombre
        elif signe == '*':
            base *= nombre
        elif signe == '/' and nombre != 0:
            base /= nombre
        ecrire_cible(objet, colonne, base)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(base)
    elif action == 'change':
        ecrire_cible(objet, colonne, valeur_effet)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(valeur_effet)
    elif action == 'inv':
        texte = str(courant)
        if texte in table_inversion:
            ecrire_cible(objet, colonne, table_inversion[texte])
            journal = objet.nom + ' : inversion vers ' + str(table_inversion[texte])
    return journal


def formater_temps(tour, valeur_tour, unite_tour):
    total = tour * valeur_tour
    texte = str(total)
    if texte.endswith('.0'):
        texte = texte[:-2]
    return texte + ' ' + unite_tour


def profondeur_depuis_source(graphe, depart):
    profondeurs = {depart: 0}
    file_attente = [depart]
    while file_attente:
        courant = file_attente.pop(0)
        for voisin in graphe.get(courant, []):
            if voisin not in profondeurs:
                profondeurs[voisin] = profondeurs[courant] + 1
                file_attente.append(voisin)
    return profondeurs


def simuler(objets, liaisons, evenements_lignes, paternes_lignes, inversions, nb_tours, objets_observes, valeur_tour=1, unite_tour='', dico_unites=None):
    etat = objets_etat(objets)
    table_inversion = {}
    for ligne in inversions:
        table_inversion[ligne['valeur_0']] = ligne['valeur_1']
        table_inversion[ligne['valeur_1']] = ligne['valeur_0']
    catalogue = [{'nom': objet.nom} for objet in etat.values()]
    graphe, poids, conservations = construire_graphe(catalogue, liaisons)
    evenements = [Evenement(ligne) for ligne in evenements_lignes]
    paternes = [Paterne(ligne) for ligne in paternes_lignes]
    historique = []
    courbes = {nom: [] for nom in objets_observes}

    for tour in range(nb_tours + 1):
        journal = []
        if tour > 0:
            for paterne in paternes:
                if paterne.actif == 1 and paterne.frequence > 0 and tour % paterne.frequence == 0:
                    objet = etat.get(paterne.objet_effet_id)
                    if objet:
                        texte = appliquer_action(objet, paterne.colonne_effet, paterne.action, paterne.valeur_effet, table_inversion)
                        if texte:
                            journal.append('Paterne ' + paterne.nom + ' -> ' + texte)

            for evenement in evenements:
                if evenement.actif != 1 or tour < evenement.arrivee:
                    continue
                objet_cause = etat.get(evenement.objet_cause_id)
                objet_effet = etat.get(evenement.objet_effet_id)
                if objet_cause is None or objet_effet is None:
                    continue
                if not condition_valide(objet_cause, evenement.colonne_cause, evenement.operateur, evenement.valeur_cause):
                    continue
                if random() > evenement.proba:
                    continue
                texte = appliquer_action(objet_effet, evenement.colonne_effet, evenement.action, evenement.valeur_effet, table_inversion)
                if texte:
                    journal.append('Evenement ' + evenement.nom + ' -> ' + texte)
                if evenement.propagation != 0:
                    profondeurs = profondeur_depuis_source(graphe, objet_effet.nom)
                    for nom, profondeur in profondeurs.items():
                        if profondeur == 0:
                            continue
                        if evenement.propagation != -1 and profondeur > evenement.propagation:
                            continue
                        voisin = None
                        for candidat in etat.values():
                            if candidat.nom == nom:
                                voisin = candidat
                                break
                        if voisin is None:
                            continue
                        precedent = objet_effet.nom
                        for cle in profondeurs:
                            if cle != nom and profondeurs[cle] == profondeur - 1 and nom in graphe.get(cle, []):
                                precedent = cle
                                break
                        conservation = conservations.get((precedent, nom), conservations.get((objet_effet.nom, nom), 'n'))
                        valeur_transmise = valeur_conservee(evenement.valeur_effet, conservation, profondeur)
                        texte = appliquer_action(voisin, evenement.colonne_effet, evenement.action, valeur_transmise, table_inversion)
                        if texte:
                            journal.append('Propagation ' + precedent + ' -> ' + nom + ' (' + conservation + ') -> ' + texte)

        etat_tour = {}
        for objet in etat.values():
            etat_tour[objet.nom] = {'valeur': objet.valeur, 'etat': objet.etat, 'colonnes': dict(objet.colonnes)}
        historique.append({'tour': tour, 'temps': formater_temps(tour, valeur_tour, unite_tour), 'actions': journal, 'etat': etat_tour})
        for nom in objets_observes:
            if nom in etat_tour:
                valeur = etat_tour[nom]['valeur']
                if valeur is None:
                    valeur = 0
                courbes[nom].append(valeur)
    return historique, courbes


def svg_graphique(courbes):
    largeur = 760
    hauteur = 280
    if not courbes:
        return "<svg width='760' height='80'></svg>"
    maxi = max([max(valeurs) if valeurs else 0 for valeurs in courbes.values()] + [1])
    mini = min([min(valeurs) if valeurs else 0 for valeurs in courbes.values()] + [0])
    amplitude = maxi - mini if maxi != mini else 1
    nb_points = max([len(valeurs) for valeurs in courbes.values()] + [1])
    couleurs = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#ea580c', '#0891b2']
    lignes = [f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>", "<rect x='0' y='0' width='100%' height='100%' fill='white'/>"]
    index = 0
    for nom, valeurs in courbes.items():
        couleur = couleurs[index % len(couleurs)]
        index += 1
        points = []
        for i, valeur in enumerate(valeurs):
            x = 40 + (680 * i / max(1, nb_points - 1))
            y = 240 - (180 * ((valeur - mini) / amplitude))
            points.append(f'{x},{y}')
        lignes.append(f"<polyline fill='none' stroke='{couleur}' stroke-width='2' points='{' '.join(points)}'/>")
        lignes.append(f"<text x='40' y='{25 + 18 * index}' fill='{couleur}' font-size='13'>{nom}</text>")
    lignes.append('</svg>')
    return ''.join(lignes)
