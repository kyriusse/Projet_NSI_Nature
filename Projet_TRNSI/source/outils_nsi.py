from __future__ import annotations  #permet d'utiliser des annotations de type avancées 


def entier_ou_defaut(texte, defaut):  #convertit une valeur en entier sinon retourne une valeur par défaut
    try:
        return int(str(texte).strip())  #essaie de convertir le texte en entier après avoir supprimé les espaces
    except Exception:
        return defaut  #en cas d'erreur on retourne la valeur par défaut


def reel_ou_defaut(texte, defaut):  #convertit une valeur en float sinon retourne une valeur par défaut
    try:
        return float(str(texte).strip().replace(',', '.'))  #nettoie le texte et remplace ',' par '.' pour conversion
    except Exception:
        return defaut  #retourne la valeur par défaut si conversion impossible


def proba_valide(valeur):  #vérifie si une valeur est une probabilité valide entre 0 et 1
    return 0 <= float(valeur) <= 1  #retourne True si compris dans [0,1]  sinon False


def nom_simple_valide(nom):  #vérifie si un nom est "simple" et autorisé (lettres, chiffres, _, - et espace)
    if not nom:  #si le nom est vide ou None
        return False  #nom invalide
    premier = nom[0]  #récupère le premier caractère
    if not (premier.isalpha() or premier == '_'):  #premier caractère doit être lettre ou '_'
        return False  #sinon invalide
    for caractere in nom:  #parcourt chaque caractère du nom
        if not (caractere.isalnum() or caractere in '_ -'):  #caractère doit être une lettre ou _, - ou espace
            return False  #sinon invalide
    return True  #si toutes les vérifications passent le nom est valide
