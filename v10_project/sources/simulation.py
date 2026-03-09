"""Simulation par tours avec evenements, paternes et propagation."""

from __future__ import annotations

from copy import deepcopy
from random import random

from conversions import dictionnaire_unites, convertir


def index_objets_par_id(objets):
    return {obj["id"]: {"nom": obj["nom"], "valeur": float(obj["valeur"]), "etat": obj["etat"]} for obj in objets}


def condition_verifiee(objet, type_cause, operateur, valeur_cause):
    if type_cause == "valeur_num":
        try:
            gauche = float(objet["valeur"])
            droite = float(str(valeur_cause).replace(",", "."))
        except ValueError:
            return False
    elif type_cause == "etat":
        gauche = str(objet["etat"])
        droite = str(valeur_cause)
    else:
        gauche = str(objet["valeur"])
        droite = str(valeur_cause)

    if operateur == "=":
        return gauche == droite
    if operateur == "<":
        return gauche < droite
    if operateur == ">":
        return gauche > droite
    return False


def appliquer_effet(objet, type_effet, valeur_effet, table_inversion):
    journal = ""
    if type_effet == "fixer_valeur":
        objet["valeur"] = float(str(valeur_effet).replace(",", "."))
        journal = f"valeur fixe a {objet['valeur']}"
    elif type_effet == "operation":
        operateur = str(valeur_effet)[0]
        nombre = float(str(valeur_effet)[1:].replace(",", "."))
        if operateur == "+":
            objet["valeur"] += nombre
        elif operateur == "-":
            objet["valeur"] -= nombre
        elif operateur == "*":
            objet["valeur"] *= nombre
        elif operateur == "/" and nombre != 0:
            objet["valeur"] /= nombre
        journal = f"operation {valeur_effet}, valeur devient {objet['valeur']}"
    elif type_effet == "fixer_etat":
        objet["etat"] = str(valeur_effet)
        journal = f"etat fixe a {objet['etat']}"
    elif type_effet == "inversion":
        etat_courant = str(objet["etat"])
        if etat_courant in table_inversion:
            objet["etat"] = table_inversion[etat_courant]
            journal = f"inversion, etat devient {objet['etat']}"
        else:
            journal = "inversion sans effet"
    return journal


def propagation_depuis(objets_etat, graphe, poids_aretes, nom_depart, profondeur_max, type_effet, valeur_effet, table_inversion):
    """
    Propagation simple et defendable :
    - on propage sur les voisins
    - si l'effet est numerique, l'intensite est reduite par le poids ou par 1/2 par defaut
    - si l'effet n'est pas numerique, on applique seulement au voisin choisi par le plus fort poids a chaque etape
    """
    journal = []
    if profondeur_max <= 0:
        return journal

    courant = nom_depart
    intensite = None
    if type_effet == "operation" and valeur_effet and valeur_effet[0] in "+-*/":
        try:
            intensite = float(valeur_effet[1:].replace(",", "."))
        except ValueError:
            intensite = None

    for niveau in range(1, profondeur_max + 1):
        voisins = graphe.get(courant, [])
        if not voisins:
            break

        meilleur = None
        meilleur_poids = -1
        for voisin in voisins:
            poids = float(poids_aretes.get((courant, voisin), 1))
            if poids > meilleur_poids:
                meilleur = voisin
                meilleur_poids = poids

        if meilleur is None:
            break

        if type_effet == "operation" and intensite is not None:
            intensite = intensite * (meilleur_poids if 0 <= meilleur_poids <= 1 else 0.5)
            if valeur_effet[0] == "+":
                objets_etat[meilleur]["valeur"] += intensite
            elif valeur_effet[0] == "-":
                objets_etat[meilleur]["valeur"] -= intensite
            elif valeur_effet[0] == "*":
                objets_etat[meilleur]["valeur"] *= intensite
            elif valeur_effet[0] == "/" and intensite != 0:
                objets_etat[meilleur]["valeur"] /= intensite
            journal.append(f"Propagation niveau {niveau} vers {meilleur} : effet numerique attenue")
        else:
            texte = appliquer_effet(objets_etat[meilleur], type_effet, valeur_effet, table_inversion)
            journal.append(f"Propagation niveau {niveau} vers {meilleur} : {texte}")

        courant = meilleur

    return journal


def frequence_par_tour(unites_lignes, frequence_valeur, frequence_unite, valeur_tour, unite_tour):
    unites = dictionnaire_unites(unites_lignes)
    duree_tour = convertir(unites, valeur_tour, unite_tour, frequence_unite)
    if duree_tour is None or frequence_valeur <= 0:
        return 0
    return duree_tour / frequence_valeur


def simuler(
    objets,
    liaisons,
    evenements,
    paternes,
    inversions,
    unites_lignes,
    graphe,
    poids_aretes,
    nb_tours,
    valeur_tour,
    unite_tour,
    objets_observes,
):
    etat = index_objets_par_id(objets)
    table_inversion = {}
    for ligne in inversions:
        table_inversion[ligne["valeur_0"]] = ligne["valeur_1"]
        table_inversion[ligne["valeur_1"]] = ligne["valeur_0"]

    historique = []
    courbes = {nom: [] for nom in objets_observes}

    for tour in range(nb_tours + 1):
        journal_tour = []

        if tour > 0:
            # On trie par poids decroissant. Si poids > 1, cela joue comme une priorite.
            evenements_tries = sorted(evenements, key=lambda e: float(e["poids"]), reverse=True)

            for evenement in evenements_tries:
                if int(evenement["actif"]) != 1 or tour < int(evenement["arrivee_tour"]):
                    continue

                objet_cause = etat[evenement["objet_cause_id"]]
                if not condition_verifiee(
                    objet_cause,
                    evenement["type_cause"],
                    evenement["operateur"],
                    evenement["valeur_cause"],
                ):
                    continue

                poids = float(evenement["poids"])
                if 0 <= poids <= 1 and random() > poids:
                    continue

                objet_effet = etat[evenement["objet_effet_id"]]
                texte = appliquer_effet(
                    objet_effet,
                    evenement["type_effet"],
                    evenement["valeur_effet"],
                    table_inversion,
                )
                journal_tour.append(
                    f"Evenement {evenement['nom']} sur {objet_effet['nom']} : {texte}"
                )

                if int(evenement["propagation_active"]) == 1:
                    journal_tour.extend(
                        propagation_depuis(
                            etat,
                            graphe,
                            poids_aretes,
                            objet_effet["nom"],
                            int(evenement["propagation_profondeur"]),
                            evenement["type_effet"],
                            evenement["valeur_effet"],
                            table_inversion,
                        )
                    )

            for paterne in paternes:
                if int(paterne["actif"]) != 1:
                    continue

                nb_applications = frequence_par_tour(
                    unites_lignes,
                    float(paterne["frequence_valeur"]),
                    paterne["frequence_unite"],
                    valeur_tour,
                    unite_tour,
                )
                if nb_applications <= 0:
                    continue

                nombre_entier = int(nb_applications)
                reste = nb_applications - nombre_entier
                total = nombre_entier
                if random() < reste:
                    total += 1

                if total > 0:
                    objet_effet = etat[paterne["objet_effet_id"]]
                    for _ in range(total):
                        texte = appliquer_effet(
                            objet_effet,
                            paterne["type_effet"],
                            paterne["valeur_effet"],
                            table_inversion,
                        )
                    journal_tour.append(
                        f"Paterne {paterne['nom']} applique {total} fois sur {objet_effet['nom']} : {texte}"
                    )

        etat_tour = {}
        for objet_id, contenu in etat.items():
            etat_tour[contenu["nom"]] = {
                "valeur": contenu["valeur"],
                "etat": contenu["etat"],
            }

        historique.append({"tour": tour, "actions": deepcopy(journal_tour), "etat": etat_tour})

        for nom in objets_observes:
            if nom in etat_tour:
                courbes[nom].append(etat_tour[nom]["valeur"])

    return historique, courbes


def svg_graphique(courbes, unite_tour):
    largeur = 860
    hauteur = 360
    marge = 50
    if not courbes:
        return "<svg width='860' height='360'></svg>"

    toutes_les_valeurs = []
    nb_points = 0
    for serie in courbes.values():
        toutes_les_valeurs.extend(serie)
        nb_points = max(nb_points, len(serie))

    if not toutes_les_valeurs or nb_points == 0:
        return "<svg width='860' height='360'></svg>"

    minimum = min(toutes_les_valeurs)
    maximum = max(toutes_les_valeurs)
    if minimum == maximum:
        maximum = minimum + 1

    couleurs = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]
    lignes = [f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>"]
    lignes.append(f"<line x1='{marge}' y1='{hauteur-marge}' x2='{largeur-marge}' y2='{hauteur-marge}' stroke='#111827' />")
    lignes.append(f"<line x1='{marge}' y1='{marge}' x2='{marge}' y2='{hauteur-marge}' stroke='#111827' />")

    for i in range(5):
        y = marge + i * ((hauteur - 2 * marge) / 4)
        valeur = round(maximum - i * ((maximum - minimum) / 4), 2)
        lignes.append(f"<line x1='{marge}' y1='{y}' x2='{largeur-marge}' y2='{y}' stroke='#e5e7eb' />")
        lignes.append(f"<text x='8' y='{y+4}' font-size='12' fill='#374151'>{valeur}</text>")

    for i in range(nb_points):
        x = marge + i * ((largeur - 2 * marge) / max(1, nb_points - 1))
        lignes.append(f"<line x1='{x}' y1='{marge}' x2='{x}' y2='{hauteur-marge}' stroke='#f3f4f6' />")
        lignes.append(f"<text x='{x}' y='{hauteur-18}' text-anchor='middle' font-size='12' fill='#374151'>T{i}</text>")
        lignes.append(f"<text x='{x}' y='{hauteur-4}' text-anchor='middle' font-size='11' fill='#6b7280'>{unite_tour}</text>")

    for indice, (nom, serie) in enumerate(courbes.items()):
        couleur = couleurs[indice % len(couleurs)]
        points = []
        for i, valeur in enumerate(serie):
            x = marge + i * ((largeur - 2 * marge) / max(1, nb_points - 1))
            y = hauteur - marge - ((valeur - minimum) / (maximum - minimum)) * (hauteur - 2 * marge)
            points.append(f"{x},{y}")
            lignes.append(f"<circle cx='{x}' cy='{y}' r='3' fill='{couleur}' />")
            lignes.append(f"<text x='{x+5}' y='{y-5}' font-size='11' fill='{couleur}'>{round(valeur,2)}</text>")
        lignes.append(f"<polyline fill='none' stroke='{couleur}' stroke-width='2' points='{' '.join(points)}' />")
        lignes.append(f"<text x='{largeur-150}' y='{20 + indice*20}' font-size='13' fill='{couleur}'>{nom}</text>")

    lignes.append("</svg>")
    return "".join(lignes)
