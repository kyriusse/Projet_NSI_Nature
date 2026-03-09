"""Fonctions utilitaires simples et pedagogiques."""

from __future__ import annotations

import re


def nom_objet_valide(nom: str) -> bool:
    """
    Un nom d'objet doit commencer par une lettre.
    Ensuite on autorise lettres, chiffres et underscore.
    Exemples valides : A, B2, Objet_1.
    """
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", nom.strip()))


def reel_ou_defaut(texte: str, defaut: float = 0.0) -> float:
    try:
        return float(str(texte).replace(",", "."))
    except ValueError:
        return defaut


def entier_ou_defaut(texte: str, defaut: int = 0) -> int:
    try:
        return int(str(texte).strip())
    except ValueError:
        return defaut


def poids_valide(poids: float) -> bool:
    return poids >= 0


def est_nombre(texte: str) -> bool:
    try:
        float(str(texte).replace(",", "."))
        return True
    except ValueError:
        return False
