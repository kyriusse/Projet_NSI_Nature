"""Analyse simple de l'ajout rapide des liaisons."""

from __future__ import annotations


def decouper_choix(texte: str) -> list[str]:
    contenu = texte.strip()
    if contenu.startswith("(") and contenu.endswith(")"):
        contenu = contenu[1:-1]
    return [element.strip() for element in contenu.split(",") if element.strip()]


def parser_expression(expression: str) -> list[tuple[str, str, str]]:
    """
    Gere des formes pedagogiques simples :
    - A => B
    - A <=> B
    - A => (B,C,D)
    - A <=> (B,C)
    - A => (B,C) => Z
    - A => (B,C) ; C => Z

    Retour : liste de triplets (source, type_liaison, cible)
    """
    resultat = []
    morceaux = [m.strip() for m in expression.replace("\n", ";").split(";") if m.strip()]

    for morceau in morceaux:
        if "<=>" in morceau:
            operateur = "<=>"
            parties = [p.strip() for p in morceau.split("<=>") if p.strip()]
        elif "=>" in morceau:
            operateur = "=>"
            parties = [p.strip() for p in morceau.split("=>") if p.strip()]
        else:
            continue

        if len(parties) < 2:
            continue

        groupes = []
        for partie in parties:
            groupes.append(decouper_choix(partie))

        for indice in range(len(groupes) - 1):
            groupe_gauche = groupes[indice]
            groupe_droite = groupes[indice + 1]
            for source in groupe_gauche:
                for cible in groupe_droite:
                    resultat.append((source, operateur, cible))

    return resultat
