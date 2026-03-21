from __future__ import annotations

from random import random
import math
import re

from conversions import convertir, dictionnaire_unites
from graphe import construire_graphe
from modele import Evenement, ObjetSimulation, Paterne


def nombre_ou_zero(valeur):

    if valeur in (None, ''):
        return 0.0

    try:
        return float(valeur)

    except Exception:
        return 0.0


def objets_etat(objets):

    resultat = {}

    for ligne in objets:

        nom_table = ligne.get('nom_table', '')

        valeur = nombre_ou_zero(ligne.get('valeur', 0))

        etat = ligne.get('etat', '')

        objet = ObjetSimulation(
            ligne['id'],
            ligne['nom'],
            nom_table,
            valeur,
            etat
        )

        for cle in ligne:
            if cle not in ['id', 'nom', 'nom_table', 'valeur', 'etat']:
                objet.colonnes[cle] = ligne[cle]

        resultat[ligne['id']] = objet

    return resultat


def lire_cible(objet, colonne):

    if colonne == 'valeur':
        return objet.valeur

    if colonne == 'etat':
        return objet.etat

    return objet.colonnes.get(colonne, '')


def ecrire_cible(objet, colonne, valeur):

    if colonne == 'valeur':
        objet.valeur = nombre_ou_zero(valeur)

    elif colonne == 'etat':
        objet.etat = str(valeur)

    else:
        objet.colonnes[colonne] = valeur


def condition_valide(objet, colonne, operateur, valeur):

    courant = lire_cible(objet, colonne)

    try:
        gauche = float(str(courant).replace(',', '.'))
        droite = float(str(valeur).replace(',', '.'))

    except Exception:
        gauche = str(courant)
        droite = str(valeur)

    if operateur == '=':
        return gauche == droite

    if operateur == '<':
        return gauche < droite

    if operateur == '>':
        return gauche > droite

    return False


def parser_nombre_operation(valeur):

    texte = str(valeur).strip()

    if len(texte) < 2:
        return '', 0

    return texte[0], float(texte[1:].replace(',', '.'))


def valeur_conservee(valeur_effet, expression, profondeur=1):

    texte = str(expression).strip().lower().replace(' ', '')

    if texte in ('', 'n'):
        return valeur_effet

    signe, nombre = parser_nombre_operation(valeur_effet)

    if signe == '':
        return valeur_effet

    if texte.startswith('n/'):
        diviseur = float(texte.split('/', 1)[1].replace(',', '.'))

        if diviseur != 0:
            return signe + str(nombre / (diviseur ** profondeur))

    if texte.endswith('/n'):
        multiplicateur = texte[:-2]

        try:
            coeff = float(multiplicateur.replace(',', '.')) if multiplicateur else 1
        except Exception:
            coeff = 1

        return signe + str(nombre * coeff)

    return valeur_effet


def appliquer_action(objet, colonne, action, valeur_effet, table_inversion):

    journal = ''

    courant = lire_cible(objet, colonne)

    if action == 'op':

        signe = str(valeur_effet)[0]
        nombre = float(str(valeur_effet)[1:].replace(',', '.'))
        base = nombre_ou_zero(courant)

        if signe == '+':
            base += nombre
        elif signe == '-':
            base -= nombre
        elif signe == '*':
            base *= nombre
        elif signe == '/' and nombre != 0:
            base /= nombre

        ecrire_cible(objet, colonne, base)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(base)

    elif action == 'change':

        ecrire_cible(objet, colonne, valeur_effet)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(valeur_effet)

    elif action == 'inv':

        texte = str(courant)

        if texte in table_inversion:
            nouvelle_valeur = table_inversion[texte]
            ecrire_cible(objet, colonne, nouvelle_valeur)
            journal = objet.nom + ' : ' + colonne + ' inverse vers ' + str(nouvelle_valeur)

    return journal


def profondeur_depuis_source(graphe, depart):

    profondeurs = {depart: 0}
    file_attente = [depart]

    while file_attente:

        courant = file_attente.pop(0)

        for voisin in graphe.get(courant, []):

            if voisin not in profondeurs:
                profondeurs[voisin] = profondeurs[courant] + 1
                file_attente.append(voisin)

    return profondeurs




def unite_de_base(dico_unites):

    for nom, infos in dico_unites.items():
        if not infos['dessous']:
            return nom

    return ''


def parser_duree(texte):

    contenu = str(texte).strip()

    if contenu == '':
        return None

    resultat = re.match(r'^([+-]?[0-9]+(?:[\.,][0-9]+)?)\s*([A-Za-z_][A-Za-z0-9_]*)?$', contenu)

    if resultat is None:
        return None

    valeur = float(resultat.group(1).replace(',', '.'))
    unite = resultat.group(2) or ''

    return valeur, unite


def duree_tour_en_base(valeur_tour, unite_tour, dico_unites):

    if unite_tour == '':
        return None

    base = unite_de_base(dico_unites)

    if base == '':
        return None

    return convertir(dico_unites, valeur_tour, unite_tour, base)


def frequence_paterne_en_base(frequence, dico_unites):

    resultat = parser_duree(frequence)

    if resultat is None:
        return None, ''

    valeur, unite = resultat

    if unite == '':
        return None, ''

    base = unite_de_base(dico_unites)

    if base == '':
        return None, unite

    return convertir(dico_unites, valeur, unite, base), unite


def nombre_declenchements_paterne(tour, frequence, valeur_tour, unite_tour, dico_unites):

    texte_frequence = str(frequence).strip()

    if texte_frequence == '':
        texte_frequence = '1'

    resultat = parser_duree(texte_frequence)

    if resultat is None:
        return 0, 'Frequence invalide : ' + texte_frequence

    valeur_frequence, unite_frequence = resultat

    if valeur_frequence <= 0:
        return 0, 'Frequence invalide : ' + texte_frequence

    if unite_frequence == '':
        frequence_tours = int(round(valeur_frequence))

        if frequence_tours <= 0:
            return 0, 'Frequence invalide : ' + texte_frequence

        if tour % frequence_tours == 0:
            return 1, ''

        return 0, ''

    duree_tour = duree_tour_en_base(valeur_tour, unite_tour, dico_unites)

    if duree_tour is None or duree_tour <= 0:
        return 0, 'Impossible de convertir le tour vers une unite de temps.'

    frequence_reelle = frequence_paterne_en_base(texte_frequence, dico_unites)[0]

    if frequence_reelle is None or frequence_reelle <= 0:
        return 0, 'Unite inconnue pour la frequence : ' + unite_frequence

    debut = (tour - 1) * duree_tour
    fin = tour * duree_tour
    epsilon = 1e-9

    total_fin = int(math.floor((fin + epsilon) / frequence_reelle))
    total_debut = int(math.floor((debut + epsilon) / frequence_reelle))

    return max(0, total_fin - total_debut), ''


def formater_temps(tour, valeur_tour, unite_tour):

    total = tour * valeur_tour
    texte = str(total)

    if texte.endswith('.0'):
        texte = texte[:-2]

    if unite_tour:
        return texte + ' ' + unite_tour

    return texte


def analyser_observations(selection_objets, journal):

    observations = {}

    for entree in selection_objets:

        texte = str(entree).strip()

        if texte == '':
            continue

        if '(' not in texte or not texte.endswith(')'):
            observations[texte] = ['valeur']
            continue

        nom_objet = texte.split('(', 1)[0].strip()
        contenu = texte[texte.find('(') + 1:-1]

        colonnes = []
        for morceau in contenu.split(';'):
            nom_colonne = morceau.strip()
            if nom_colonne != '':
                colonnes.append(nom_colonne)

        if len(colonnes) == 0:
            colonnes = ['valeur']

        observations[nom_objet] = colonnes

    return observations


def lire_observation(etat_tour, nom_objet, nom_colonne):

    if nom_objet not in etat_tour:
        return 0.0, ''

    infos = etat_tour[nom_objet]

    if nom_colonne == 'valeur':
        return nombre_ou_zero(infos['valeur']), str(infos['valeur'])

    if nom_colonne == 'etat':
        return 0.0, str(infos['etat'])

    if nom_colonne in infos['colonnes']:
        valeur = infos['colonnes'][nom_colonne]
        return nombre_ou_zero(valeur), str(valeur)

    return None, None


def etiquette_observation(nom_objet, nom_colonne):

    return nom_objet + '.' + nom_colonne


def simuler(objets, liaisons, evenements_lignes, paternes_lignes, inversions, nb_tours, objets_observes, valeur_tour=1, unite_tour='', unites=None):

    etat = objets_etat(objets)

    table_inversion = {}

    for ligne in inversions:
        table_inversion[ligne['valeur_0']] = ligne['valeur_1']
        table_inversion[ligne['valeur_1']] = ligne['valeur_0']

    catalogue = [{'nom': o.nom} for o in etat.values()]

    graphe, poids, conservations = construire_graphe(catalogue, liaisons)

    evenements = [Evenement(x) for x in evenements_lignes]
    paternes = [Paterne(x) for x in paternes_lignes]
    dico_unites = dictionnaire_unites(unites or [])

    historique = []

    journal_global = []
    observations_demandees = analyser_observations(objets_observes, journal_global)

    courbes = {}
    premiere_colonne_graphique = {}

    for nom_objet, colonnes in observations_demandees.items():
        premiere_colonne_graphique[nom_objet] = colonnes[0]
        etiquette = etiquette_observation(nom_objet, colonnes[0])
        courbes[etiquette] = []

    for tour in range(nb_tours + 1):

        journal = []

        if tour > 0:

            for paterne in paternes:

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
                            if nombre_declenchements == 1:
                                journal.append('Paterne ' + paterne.nom + ' -> ' + txt)
                            else:
                                journal.append('Paterne ' + paterne.nom + ' (' + str(occurrence + 1) + '/' + str(nombre_declenchements) + ') -> ' + txt)

            for evenement in evenements:

                if evenement.actif != 1:
                    continue

                if tour < evenement.arrivee:
                    continue

                cause = etat.get(evenement.objet_cause_id)
                effet = etat.get(evenement.objet_effet_id)

                if cause is None or effet is None:
                    continue

                if not condition_valide(
                    cause,
                    evenement.colonne_cause,
                    evenement.operateur,
                    evenement.valeur_cause
                ):
                    continue

                if random() > evenement.proba:
                    continue

                txt = appliquer_action(
                    effet,
                    evenement.colonne_effet,
                    evenement.action,
                    evenement.valeur_effet,
                    table_inversion
                )

                if txt:
                    journal.append('Evenement ' + evenement.nom + ' -> ' + txt)

                if evenement.propagation != 0:

                    profondeurs = profondeur_depuis_source(graphe, effet.nom)

                    for nom_voisin, profondeur in profondeurs.items():

                        if profondeur == 0:
                            continue

                        if evenement.propagation != -1 and profondeur > evenement.propagation:
                            continue

                        proba_liaison = poids.get((effet.nom, nom_voisin), 1)

                        if random() > proba_liaison:
                            continue

                        voisin = None

                        for obj in etat.values():
                            if obj.nom == nom_voisin:
                                voisin = obj
                                break

                        if voisin is None:
                            continue

                        conservation = conservations.get((effet.nom, nom_voisin), 'n')

                        valeur_transmise = valeur_conservee(
                            evenement.valeur_effet,
                            conservation,
                            profondeur
                        )

                        txt = appliquer_action(
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

        etat_tour = {}

        for obj in etat.values():
            etat_tour[obj.nom] = {
                'valeur': obj.valeur,
                'etat': obj.etat,
                'colonnes': dict(obj.colonnes)
            }

        observations_tour = {}

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

            courbes[etiquette].append(valeur_num)

        observations_txt = []
        for nom_objet, valeurs in observations_tour.items():
            morceaux = []
            for nom_colonne, valeur in valeurs.items():
                morceaux.append(nom_colonne + '=' + str(valeur))
            observations_txt.append(
                nom_objet + '(' + ' ; '.join(morceaux) + ')'
            )
        texte_observations = ' | '.join(observations_txt)
        historique.append({
            'tour': tour,
            'temps': formater_temps(tour, valeur_tour, unite_tour),
            'actions': journal,
            'etat': etat_tour,
            'observations': texte_observations
        })

    return historique, courbes


def svg_graphique(courbes, unite_temps='tour', unite_valeur='valeur'):

    largeur = 760
    hauteur = 320

    if not courbes:
        return "<svg width='760' height='80'></svg>"

    courbes_numeriques = {}

    for nom, valeurs in courbes.items():
        courbes_numeriques[nom] = [nombre_ou_zero(v) for v in valeurs]

    maxi = max([max(valeurs) if valeurs else 0 for valeurs in courbes_numeriques.values()] + [1])
    mini = min([min(valeurs) if valeurs else 0 for valeurs in courbes_numeriques.values()] + [0])

    amplitude = maxi - mini if maxi != mini else 1
    nb_points = max([len(valeurs) for valeurs in courbes_numeriques.values()] + [1])

    couleurs = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#ea580c', '#0891b2']

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

    return ''.join(lignes)