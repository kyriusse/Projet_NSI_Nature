from __future__ import annotations


def arbre_html(base_donnees, nom_parent, niveau=0, max_branches=6, deja_vus=None):
    if deja_vus is None:
        deja_vus = set()
    marge = 18 * niveau
    lignes = []
    if nom_parent in deja_vus:
        return f"<div style='margin-left:{marge}px'>↺ {nom_parent}</div>"
    deja_vus.add(nom_parent)
    enfants = list(base_donnees.enfants_de(nom_parent))[:max_branches]
    lignes.append(f"<div style='margin-left:{marge}px'><strong>{nom_parent}</strong></div>")
    for enfant in enfants:
        lignes.append(f"<div style='margin-left:{marge + 18}px'>├─ x{enfant['quantite']} {enfant['enfant_nom']}</div>")
        lignes.append(arbre_html(base_donnees, enfant['enfant_nom'], niveau + 2, max_branches, deja_vus.copy()))
    return ''.join(lignes)
