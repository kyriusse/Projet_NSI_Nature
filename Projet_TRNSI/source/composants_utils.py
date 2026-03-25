from __future__ import annotations

# Cette fonction génère l'affichage en escalier des composants dans la page HTML
def arbre_html(base_donnees, nom_parent, niveau=0, max_branches=6, deja_vus=None):
    # initialise le dictionnaire de sécurité pour éviter les boucles infinies
    if deja_vus is None:
        deja_vus = set()
    marge = 18 * niveau # Calcule le décalage à droite selon la profondeur
    lignes = []
    # Si l'objet a déjà été affiché plus haut, on arrête pour éviter de boucler
    if nom_parent in deja_vus:
        return f"<div style='margin-left:{marge}px'>↺ {nom_parent}</div>"
    deja_vus.add(nom_parent) # Marque l'objet comme "traité"
    # Récupère la liste des composants avec une requête SQL dans base_donnees.py
    enfants = list(base_donnees.enfants_de(nom_parent))[:max_branches]
    # Ajoute le nom de l'objet principal en gras
    lignes.append(f"<div style='margin-left:{marge}px'><strong>{nom_parent}</strong></div>")
    for enfant in enfants:
        # Affiche le nom du composant et sa quantité
        lignes.append(f"<div style='margin-left:{marge + 18}px'>├─ x{enfant['quantite']} {enfant['enfant_nom']}</div>")
        # La fonction s'appelle elle-même pour chercher les sous-composants (récursivité)
        lignes.append(arbre_html(base_donnees, enfant['enfant_nom'], niveau + 2, max_branches, deja_vus.copy()))
    return ''.join(lignes) # Fusionne toutes les balises HTML en un seul bloc
