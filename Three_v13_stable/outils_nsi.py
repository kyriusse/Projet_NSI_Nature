from __future__ import annotations


def entier_ou_defaut(texte, defaut):
    try:
        return int(str(texte).strip())
    except Exception:
        return defaut


def reel_ou_defaut(texte, defaut):
    try:
        return float(str(texte).strip().replace(',', '.'))
    except Exception:
        return defaut


def proba_valide(valeur):
    return 0 <= float(valeur) <= 1


def nom_simple_valide(nom):
    if not nom:
        return False
    premier = nom[0]
    if not (premier.isalpha() or premier == '_'):
        return False
    for caractere in nom:
        if not (caractere.isalnum() or caractere in '_ -'):
            return False
    return True
