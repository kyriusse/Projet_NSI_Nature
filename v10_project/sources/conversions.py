"""Conversions d'unites avec une logique simple et tres NSI."""

from __future__ import annotations


def dictionnaire_unites(lignes):
    unites = {}
    for ligne in lignes:
        unites[ligne["unite"]] = {
            "dessous": ligne["unite_du_dessous"],
            "facteur": ligne["facteur"],
            "rang": ligne["rang"],
        }
    return unites


def vers_unite_minimale(unites, unite_depart, valeur):
    if unite_depart not in unites:
        return None

    resultat = float(valeur)
    unite = unite_depart
    while unites[unite]["dessous"] is not None:
        facteur = float(unites[unite]["facteur"])
        resultat *= facteur
        unite = unites[unite]["dessous"]
    return resultat, unite


def convertir(unites, valeur, unite_depart, unite_arrivee):
    if unite_depart not in unites or unite_arrivee not in unites:
        return None

    valeur_base, unite_base_1 = vers_unite_minimale(unites, unite_depart, valeur)
    valeur_cible, unite_base_2 = vers_unite_minimale(unites, unite_arrivee, 1)

    if unite_base_1 != unite_base_2 or valeur_cible == 0:
        return None

    return valeur_base / valeur_cible
