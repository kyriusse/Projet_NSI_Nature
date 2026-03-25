from __future__ import annotations


def dictionnaire_unites(lignes):
    resultat = {} # On crée un dictionnaire vide pour stocker nos unités
    for ligne in lignes:
        # On utilise le nom de l'unité comme clé pour la retrouver instantanément
        resultat[ligne['nom']] = {
            'rang': int(ligne['rang']), # Le niveau dans la hiérarchie
            'dessous': ligne['unite_du_dessous'], # Le nom de l'unité plus petite
            # On convertit le facteur en nombre décimal si il existe
            'facteur': float(ligne['facteur']) if ligne['facteur'] not in (None, '') else None,
        }
    return resultat


def convertir(dico, valeur, depart, arrivee):
    if depart == arrivee: # Si on convertit des heures en heures on renvoie la valeur telle quelle
        return valeur
    if depart not in dico or arrivee not in dico: # si l'unité est inconnue, on arrête tout (pour la sécurité)
        return None

    valeurs_base = {depart: float(valeur)} # On mémorise la valeur de départ

    courant = depart
    quantite = float(valeur)
    while dico[courant]['dessous']: # Tant qu'il existe une unité plus petite
        dessous = dico[courant]['dessous']
        # On multiplie par le facteur (2h*60=120 min)
        quantite = quantite * dico[courant]['facteur']
        valeurs_base[dessous] = quantite # On stocke le résultat pour chaque palier
        courant = dessous # On descend d'un cran

    courant = arrivee
    pile = [] # On crée une Pile
    while dico[courant]['dessous']: 
        pile.append(courant) # On empile les unités jusqu'à arriver à la plus petite
        courant = dico[courant]['dessous']
    # Si l'unité de base trouvée à la fin n'est pas la même ca veux dire que les unités ne sont pas compatibles
    if courant not in valeurs_base:
        return None
    # On part de la valeur de base et on dépile
    resultat = valeurs_base[courant]
    while pile:
        unite = pile.pop() # On récupère l'unité au sommet de la pile
        # On divise pour remonter
        resultat = resultat / dico[unite]['facteur']

    return resultat
