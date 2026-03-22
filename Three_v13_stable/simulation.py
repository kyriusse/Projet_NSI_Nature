from __future__ import annotations  #permet d'utiliser des annotations de type avancées

from random import random  #importe une fonction qui génère un nombre  entre 0 et 1
import math  #importe des fonctions mathématiques
import re  #importe les expressions régulières pour analyser du texte

from conversions import convertir, dictionnaire_unites  #fonctions pour gérer les conversions d'unités
from graphe import construire_graphe  #fonction pour créer un graphe
from modele import Evenement, ObjetSimulation, Paterne  #classes utilisées dans la simulation


def nombre_ou_zero(valeur):  # cette fonction convertit une valeur en nombre ou retourne 0

    if valeur in (None, ''):  #si la valeur est vide ou qu'elle n'éxiste pas 
        return 0.0  #retourne 0.0

    try:
        return float(valeur)  #essaye de convertir en nombre flottant

    except Exception:  #si la conversion échoue
        return 0.0  #retourne 0.0


def objets_etat(objets):  #transforme des données en objets utilisables

    resultat = {}  #dictionnaire qui contiendra les objets

    for ligne in objets:  #parcourt chaque ligne de données

        nom_table = ligne.get('nom_table', '')  #récupère le nom de la table ou un nom vide 

        valeur = nombre_ou_zero(ligne.get('valeur', 0))  #convertit la valeur en nombre

        etat = ligne.get('etat', '')  #récupère l'état de l'objet

        objet = ObjetSimulation(  #crée un objet de simulation
            ligne['id'],  #identifiant
            ligne['nom'],  #nom
            nom_table,  #table associée
            valeur,  #valeur numérique
            etat  #etat texte
        )

        for cle in ligne:  #parcourt toutes les clés de la ligne
            if cle not in ['id', 'nom', 'nom_table', 'valeur', 'etat']:  #si les clés sont déjà utilisées on les ignore 
                objet.colonnes[cle] = ligne[cle]  #ajoute les autres données comme colonnes

        resultat[ligne['id']] = objet  #ajoute l'objet au dictionnaire avec son id

    return resultat  #retourne tous les objets


def lire_cible(objet, colonne):  #lit une valeur dans un objet selon la colonne demandée

    if colonne == 'valeur':  #si on demande la valeur principale
        return objet.valeur  #retourne la valeur

    if colonne == 'etat':  #si on demande l'état
        return objet.etat  #retourne l'état

    return objet.colonnes.get(colonne, '')  #sinon on retourne une colonne personnalisée


def ecrire_cible(objet, colonne, valeur):  #modifie une valeur dans un objet

    if colonne == 'valeur':  #si on modifie la valeur principale
        objet.valeur = nombre_ou_zero(valeur)  # on convertit et on assigne

    elif colonne == 'etat':  #si on modifie l'état
        objet.etat = str(valeur)  #on convertit en texte

    else:
        objet.colonnes[colonne] = valeur  #sinon on modifie une colonne personnalisée


def condition_valide(objet, colonne, operateur, valeur):  #vérifie une condition par exemple: x > 5

    courant = lire_cible(objet, colonne)  #lit la valeur actuelle

    try:
        gauche = float(str(courant).replace(',', '.'))  #convertit la valeur actuelle en nombre
        droite = float(str(valeur).replace(',', '.'))  #convertit la valeur à comparer

    except Exception:  #si la conversion est impossible
        gauche = str(courant)  #on compare en texte
        droite = str(valeur)

    if operateur == '=':  #test égalité
        return gauche == droite

    if operateur == '<':  #test inférieur
        return gauche < droite

    if operateur == '>':  #test supérieur
        return gauche > droite

    return False  #si l'opérateur est inconnu


def parser_nombre_operation(valeur):  #analyse une opération comme +5 ou *2

    texte = str(valeur).strip() 

    if len(texte) < 2:  #si le texte est trop court
        return '', 0  #retourne rien

    return texte[0], float(texte[1:].replace(',', '.'))  #sépare le signe et le nombre


def valeur_conservee(valeur_effet, expression, profondeur=1):  #calcule la valeur transmise lors d'une propagation

    texte = str(expression).strip().lower().replace(' ', '')  #nettoie l'expression exemple: n/2

    if texte in ('', 'n'):  #si aucune modification
        return valeur_effet  #retourne la valeur d'origine

    signe, nombre = parser_nombre_operation(valeur_effet)  #récupère le signe (+, -, etc) et le nombre

    if signe == '':  #si pas d'opération valide
        return valeur_effet

    if texte.startswith('n/'):  #cas où on divise selon la profondeur 
        diviseur = float(texte.split('/', 1)[1].replace(',', '.'))  #récupère le diviseur

        if diviseur != 0:
            return signe + str(nombre / (diviseur ** profondeur))  #applique division avec la profondeur

    if texte.endswith('/n'):  #cas où on multiplie
        multiplicateur = texte[:-2]  #récupère le multiplicateur

        try:
            coeff = float(multiplicateur.replace(',', '.')) if multiplicateur else 1  #convertit en nombre
        except Exception:
            coeff = 1  #valeur par défaut

        return signe + str(nombre * coeff)  #applique multiplication

    return valeur_effet  #sinon on retourne la valeur inchangée


def appliquer_action(objet, colonne, action, valeur_effet, table_inversion):  #applique une action sur un objet

    journal = ''  #texte de description de l'action

    courant = lire_cible(objet, colonne)  #lit la valeur actuelle

    if action == 'op':  #action mathématique (+, -, *, /)

        signe = str(valeur_effet)[0]  #récupère le signe
        nombre = float(str(valeur_effet)[1:].replace(',', '.'))  #récupère la valeur numérique
        base = nombre_ou_zero(courant)  #convertit la valeur actuelle

        if signe == '+':
            base += nombre  #addition
        elif signe == '-':
            base -= nombre  #soustraction
        elif signe == '*':
            base *= nombre  #multiplication
        elif signe == '/' and nombre != 0:
            base /= nombre  #division

        ecrire_cible(objet, colonne, base)  #met à jour la valeur
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(base)  #message descriptif

    elif action == 'change':  #remplace directement la valeur

        ecrire_cible(objet, colonne, valeur_effet)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(valeur_effet)

    elif action == 'inv':  #inverse une valeur selon une table

        texte = str(courant)

        if texte in table_inversion:
            nouvelle_valeur = table_inversion[texte]  #trouve la valeur inversée
            ecrire_cible(objet, colonne, nouvelle_valeur)
            journal = objet.nom + ' : ' + colonne + ' inverse vers ' + str(nouvelle_valeur)

    return journal  #retourne le résumé de l'action


def profondeur_depuis_source(graphe, depart):  #calcule la distance dans un graphe

    profondeurs = {depart: 0}  #initialise avec le point de départ
    file_attente = [depart]  #ffile pour parcours en largeur (BFS)

    while file_attente:  #tant qu'il reste des éléments à explorer

        courant = file_attente.pop(0)  #prend le premier élément

        for voisin in graphe.get(courant, []):  #parcourt les voisins

            if voisin not in profondeurs:  #si pas encore visité
                profondeurs[voisin] = profondeurs[courant] + 1  #calcule profondeur
                file_attente.append(voisin)  #ajoute à la file

    return profondeurs  #retourne toutes les profondeurs


def unite_de_base(dico_unites):  #trouve l'unité de base

    for nom, infos in dico_unites.items():  #parcourt les unités
        if not infos['dessous']:  #si aucune unité en dessous
            return nom  #c'est l'unité de base

    return ''  #sinon rien


def parser_duree(texte):  #analyse une durée exemple: 5s 10 min

    contenu = str(texte).strip()  #nettoie le texte

    if contenu == '':
        return None  #rien à analyser

    resultat = re.match(r'^([+-]?[0-9]+(?:[\.,][0-9]+)?)\s*([A-Za-z_][A-Za-z0-9_]*)?$', contenu)  

    if resultat is None:
        return None  #format invalide

    valeur = float(resultat.group(1).replace(',', '.'))  #récupère le nombre
    unite = resultat.group(2) or ''  #récupère l'unité

    return valeur, unite  # retourne les deux


def duree_tour_en_base(valeur_tour, unite_tour, dico_unites):  # convertit la durée d'un tour en unité de base

    if unite_tour == '':
        return None  # pas d'unité

    base = unite_de_base(dico_unites)  #trouve l'unité de base

    if base == '':
        return None  #impossible

    return convertir(dico_unites, valeur_tour, unite_tour, base)  #convertit


def frequence_paterne_en_base(frequence, dico_unites):  #convertit une fréquence en unité de base

    resultat = parser_duree(frequence)  #analyse la fréquence

    if resultat is None:
        return None, ''  #erreur

    valeur, unite = resultat

    if unite == '':
        return None, ''  #pas d'unité

    base = unite_de_base(dico_unites)

    if base == '':
        return None, unite  #impossible de convertir

    return convertir(dico_unites, valeur, unite, base), unite  #retourne valeur convertit


def nombre_declenchements_paterne(tour, frequence, valeur_tour, unite_tour, dico_unites):  #calcule combien de fois un paterne se déclenche

    texte_frequence = str(frequence).strip()  #nettoie la fréquence

    if texte_frequence == '':
        texte_frequence = '1'  #par défaut la fréquence = 1

    resultat = parser_duree(texte_frequence)  #analyse la fréquence

    if resultat is None:
        return 0, 'Frequence invalide : ' + texte_frequence  #erreur si invalide

    valeur_frequence, unite_frequence = resultat

    if valeur_frequence <= 0:
        return 0, 'Frequence invalide : ' + texte_frequence  #fréquence négative interdite

    if unite_frequence == '':  #cas sans unité en nombre de tours
        frequence_tours = int(round(valeur_frequence))

        if frequence_tours <= 0:
            return 0, 'Frequence invalide : ' + texte_frequence

        if tour % frequence_tours == 0:  #si divisible -> déclenchement
            return 1, ''

        return 0, ''

    duree_tour = duree_tour_en_base(valeur_tour, unite_tour, dico_unites)  #convertit durée du tour

    if duree_tour is None or duree_tour <= 0:
        return 0, 'Impossible de convertir le tour vers une unite de temps.'

    frequence_reelle = frequence_paterne_en_base(texte_frequence, dico_unites)[0]  #convertit fréquence

    if frequence_reelle is None or frequence_reelle <= 0:
        return 0, 'Unite inconnue pour la frequence : ' + unite_frequence

    debut = (tour - 1) * duree_tour  #début du tour
    fin = tour * duree_tour  #fin du tour
    epsilon = 1e-9  #marge pour éviter erreurs de calcul

    total_fin = int(math.floor((fin + epsilon) / frequence_reelle))  #n ombre d'événements jusqu'à fin
    total_debut = int(math.floor((debut + epsilon) / frequence_reelle))  #jusqu'au début

    return max(0, total_fin - total_debut), ''  #nombre de déclenchements


def formater_temps(tour, valeur_tour, unite_tour):  #transforme un tour en texte lisible

    total = tour * valeur_tour  #calcule le temps total
    texte = str(total)

    if texte.endswith('.0'):
        texte = texte[:-2]  #enlève .0 inutile

    if unite_tour:
        return texte + ' ' + unite_tour  #ajoute unité

    return texte


def analyser_observations(selection_objets, journal):  #analyse ce qu'on doit observer

    observations = {}

    for entree in selection_objets:

        texte = str(entree).strip()

        if texte == '':
            continue

        if '(' not in texte or not texte.endswith(')'):  #format simple
            observations[texte] = ['valeur']
            continue

        nom_objet = texte.split('(', 1)[0].strip()  #nom objet
        contenu = texte[texte.find('(') + 1:-1]  #contenu entre parenthèses

        colonnes = []
        for morceau in contenu.split(';'):
            nom_colonne = morceau.strip()
            if nom_colonne != '':
                colonnes.append(nom_colonne)

        if len(colonnes) == 0:
            colonnes = ['valeur']

        observations[nom_objet] = colonnes  #associe objet -> colonnes

    return observations


def simuler(objets, liaisons, evenements_lignes, paternes_lignes, inversions, nb_tours, objets_observes, valeur_tour=1, unite_tour='', unites=None):
    #fonction principale qui lance toute la simulation

    etat = objets_etat(objets)  #initialise les objets

    table_inversion = {}  #table pour inverser certaines valeurs

    for ligne in inversions:
        table_inversion[ligne['valeur_0']] = ligne['valeur_1']
        table_inversion[ligne['valeur_1']] = ligne['valeur_0']

    catalogue = [{'nom': o.nom} for o in etat.values()]  #liste des objets

    graphe, poids, conservations = construire_graphe(catalogue, liaisons)  #construit les relations

    evenements = [Evenement(x) for x in evenements_lignes]  #crée les événements
    paternes = [Paterne(x) for x in paternes_lignes]  #crée les paternes
    dico_unites = dictionnaire_unites(unites or [])  #prépare les unités

    historique = []  #stocke tous les résultats
    journal_global = []  #historique des actions

    observations_demandees = analyser_observations(objets_observes, journal_global)  #ce qu'on observe

    courbes = {}  #données pour graphique
    premiere_colonne_graphique = {}

    for nom_objet, colonnes in observations_demandees.items():
        premiere_colonne_graphique[nom_objet] = colonnes[0]
        etiquette = etiquette_observation(nom_objet, colonnes[0])
        courbes[etiquette] = []

    for tour in range(nb_tours + 1):  #boucle principale de simulation

        journal = []  #actions du tour

        if tour > 0:  #on ne fait rien au tour 0

            for paterne in paternes:  #parcourt les paternes

                if paterne.actif != 1:
                    continue

                nombre_declenchements, erreur_frequence = nombre_declenchements_paterne(
                    tour,
                    paterne.frequence,
                    valeur_tour,
                    unite_tour,
                    dico_unites
                )

                if erreur_frequence:
                    journal.append('Paterne ' + paterne.nom + ' ignore : ' + erreur_frequence)
                    continue

                if nombre_declenchements <= 0:
                    continue

                objet = etat.get(paterne.objet_effet_id)

                if objet:

                    for occurrence in range(nombre_declenchements):

                        txt = appliquer_action(
                            objet,
                            paterne.colonne_effet,
                            paterne.action,
                            paterne.valeur_effet,
                            table_inversion
                        )

                        if txt:
                            journal.append('Paterne ' + paterne.nom + ' -> ' + txt)
                            else:
                                journal.append('Paterne ' + paterne.nom + ' (' + str(occurrence + 1) + '/' + str(nombre_declenchements) + ') -> ' + txt)

                        for evenement in evenements:  #parcourt tous les événements

                if evenement.actif != 1:  #ignore si l'événement est désactivé
                    continue

                if tour < evenement.arrivee:  #vérifie si le tour est atteint
                    continue

                cause = etat.get(evenement.objet_cause_id)  #récupère l'objet cause
                effet = etat.get(evenement.objet_effet_id)  #récupère l'objet effet

                if cause is None or effet is None:  #vérifie l'existence des objets
                    continue

                if not condition_valide(  #vérifie si la condition est respectée
                    cause,
                    evenement.colonne_cause,
                    evenement.operateur,
                    evenement.valeur_cause
                ):
                    continue

                if random() > evenement.proba:  #applique la probabilité
                    continue

                txt = appliquer_action(  #applique l'effet de l'événement
                    effet,
                    evenement.colonne_effet,
                    evenement.action,
                    evenement.valeur_effet,
                    table_inversion
                )

                if txt:
                    journal.append('Evenement ' + evenement.nom + ' -> ' + txt)  #ajoute au journal

                if evenement.propagation != 0:  #vérifie si propagation active

                    profondeurs = profondeur_depuis_source(graphe, effet.nom)  #calcule les distances

                    for nom_voisin, profondeur in profondeurs.items():  #parcourt les voisins

                        if profondeur == 0:  #ignore l'objet source
                            continue

                        if evenement.propagation != -1 and profondeur > evenement.propagation:
                            continue  #limite la propagation

                        proba_liaison = poids.get((effet.nom, nom_voisin), 1)  #probabilité du lien

                        if random() > proba_liaison:
                            continue  #test probabilité

                        voisin = None  #initialise le voisin

                        for obj in etat.values():  #recherche de l'objet voisin
                            if obj.nom == nom_voisin:
                                voisin = obj
                                break

                        if voisin is None:
                            continue

                        conservation = conservations.get((effet.nom, nom_voisin), 'n')  #règle de conservation

                        valeur_transmise = valeur_conservee(  #calcule la valeur propagée
                            evenement.valeur_effet,
                            conservation,
                            profondeur
                        )

                        txt = appliquer_action(  #applique sur le voisin
                            voisin,
                            evenement.colonne_effet,
                            evenement.action,
                            valeur_transmise,
                            table_inversion
                        )

                        if txt:
                            journal.append(
                                'Propagation ' + effet.nom +
                                ' -> ' + nom_voisin +
                                ' (' + conservation + ') -> ' + txt
                            )

        etat_tour = {}  #stocke l'état à ce tour

        for obj in etat.values():  #parcourt tous les objets
            etat_tour[obj.nom] = {  #sauvegarde leurs données
                'valeur': obj.valeur,
                'etat': obj.etat,
                'colonnes': dict(obj.colonnes)
            }

        observations_tour = {}  #stocke les observations

        for nom_objet, colonnes in observations_demandees.items():

            observations_tour[nom_objet] = {}

            for nom_colonne in colonnes:

                valeur_num, valeur_txt = lire_observation(etat_tour, nom_objet, nom_colonne)

                if valeur_num is None and valeur_txt is None:
                    observations_tour[nom_objet][nom_colonne] = '(n existe pas)'
                    continue

                observations_tour[nom_objet][nom_colonne] = valeur_txt

            nom_colonne_graphique = premiere_colonne_graphique[nom_objet]
            etiquette = etiquette_observation(nom_objet, nom_colonne_graphique)
            valeur_num, valeur_txt = lire_observation(etat_tour, nom_objet, nom_colonne_graphique)

            if valeur_num is None:
                valeur_num = 0.0

            courbes[etiquette].append(valeur_num)  #ajoute au graphique

        observations_txt = []
        for nom_objet, valeurs in observations_tour.items():
            morceaux = []
            for nom_colonne, valeur in valeurs.items():
                morceaux.append(nom_colonne + '=' + str(valeur))
            observations_txt.append(
                nom_objet + '(' + ' ; '.join(morceaux) + ')'
            )

        texte_observations = ' | '.join(observations_txt)

        historique.append({  #ajoute les données du tour
            'tour': tour,
            'temps': formater_temps(tour, valeur_tour, unite_tour),
            'actions': journal,
            'etat': etat_tour,
            'observations': texte_observations
        })

    return historique, courbes  #résultat final


def svg_graphique(courbes, unite_temps='tour', unite_valeur='valeur'):  #génère un graphique en SVG

    largeur = 760  #largeur du graphique
    hauteur = 320  #hauteur du graphique

    if not courbes:
        return "<svg width='760' height='80'></svg>"  #cas vide

    courbes_numeriques = {}

    for nom, valeurs in courbes.items():
        courbes_numeriques[nom] = [nombre_ou_zero(v) for v in valeurs]  #conversion en nombres

    maxi = max([max(valeurs) if valeurs else 0 for valeurs in courbes_numeriques.values()] + [1])  #max
    mini = min([min(valeurs) if valeurs else 0 for valeurs in courbes_numeriques.values()] + [0])  #min

    amplitude = maxi - mini if maxi != mini else 1  #évite division par zéro
    nb_points = max([len(valeurs) for valeurs in courbes_numeriques.values()] + [1])  #nombre de points

    couleurs = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#ea580c', '#0891b2']  #liste de couleurs

    lignes = [
        f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>",
        "<rect x='0' y='0' width='100%' height='100%' fill='white'/>",
        "<line x1='40' y1='260' x2='720' y2='260' stroke='black'/>",
        "<line x1='40' y1='40' x2='40' y2='260' stroke='black'/>"
    ]

    for i in range(nb_points):
        x = 40 + (680 * i / max(1, nb_points - 1))
        lignes.append(f"<line x1='{x}' y1='260' x2='{x}' y2='265' stroke='black'/>")
        lignes.append(f"<text x='{x - 5}' y='278' font-size='10'>{i}</text>")

    for i in range(6):
        y = 260 - (220 * i / 5)
        val = mini + (amplitude * i / 5)
        lignes.append(f"<line x1='35' y1='{y}' x2='40' y2='{y}' stroke='black'/>")
        lignes.append(f"<text x='5' y='{y + 4}' font-size='10'>{round(val, 1)}</text>")

    lignes.append(f"<text x='340' y='298' font-size='13'>Temps ({unite_temps})</text>")
    lignes.append(f"<text x='5' y='20' font-size='13'>{unite_valeur}</text>")

    index = 0

    for nom, valeurs in courbes_numeriques.items():

        couleur = couleurs[index % len(couleurs)]
        index += 1

        points = []

        for i, valeur in enumerate(valeurs):
            x = 40 + (680 * i / max(1, nb_points - 1))
            y = 240 - (180 * ((valeur - mini) / amplitude))
            points.append(f'{x},{y}')

        lignes.append(
            f"<polyline fill='none' stroke='{couleur}' stroke-width='2' points='{' '.join(points)}'/>"
        )

        lignes.append(
            f"<text x='40' y='{25 + 18 * index}' fill='{couleur}' font-size='13'>{nom}</text>"
        )

    lignes.append('</svg>')

    return ''.join(lignes)  #retourne le SVG final
