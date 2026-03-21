from __future__ import annotations


def dictionnaire_unites(lignes):
    resultat = {}
    for ligne in lignes:
        resultat[ligne['nom']] = {
            'rang': int(ligne['rang']),
            'dessous': ligne['unite_du_dessous'],
            'facteur': float(ligne['facteur']) if ligne['facteur'] not in (None, '') else None,
        }
    return resultat


def convertir(dico, valeur, depart, arrivee):
    if depart == arrivee:
        return valeur
    if depart not in dico or arrivee not in dico:
        return None

    valeurs_base = {depart: float(valeur)}

    courant = depart
    quantite = float(valeur)
    while dico[courant]['dessous']:
        dessous = dico[courant]['dessous']
        quantite = quantite * dico[courant]['facteur']
        valeurs_base[dessous] = quantite
        courant = dessous

    courant = arrivee
    pile = []
    while dico[courant]['dessous']:
        pile.append(courant)
        courant = dico[courant]['dessous']

    if courant not in valeurs_base:
        return None

    resultat = valeurs_base[courant]
    while pile:
        unite = pile.pop()
        resultat = resultat / dico[unite]['facteur']

    return resultat
