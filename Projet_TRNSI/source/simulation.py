from __future__ import annotations
# sert à générer des nombres aléatoires (pour les probabilités d'événements)
from random import random
# importe la fonction pour construire le graphe des liaisons entre objets
from graphe import construire_graphe
# importe les fonctions de conversion entre les unites creees par l'utilisateur
from conversions import convertir, dictionnaire_unites
# importe les classes utilisées pour représenter les données de la simulation
from modele import Evenement, ObjetSimulation, Paterne


def nombre_ou_zero(valeur):
    # Convertit une valeur en nombre décimal, retourne 0.0 si c'est impossible
    if valeur in (None, ''):
        return 0.0

    try:
        return float(valeur)

    except Exception:
        return 0.0


def objets_etat(objets):
    # Crée un dictionnaire d'objets de simulation à partir d'une liste de lignes de la base de données
    resultat = {}

    for ligne in objets:
        # Récupère le nom de la table d'origine de l'objet
        nom_table = ligne.get('nom_table', '')
        # Convertit la valeur en nombre (0.0 par défaut)
        valeur = nombre_ou_zero(ligne.get('valeur', 0))
        # Récupère l'état de l'objet (texte libre)
        etat = ligne.get('etat', '')
        # Crée un ObjetSimulation avec les données principales
        objet = ObjetSimulation(
            ligne['id'],
            ligne['nom'],
            nom_table,
            valeur,
            etat
        )
        # Copie toutes les colonnes supplémentaires dans l'objet (celles qui ne sont pas id, nom, etc.)
        for cle in ligne:
            if cle not in ['id', 'nom', 'nom_table', 'valeur', 'etat']:
                objet.colonnes[cle] = ligne[cle]
        # Stocke l'objet dans le dictionnaire, indexé par son id
        resultat[ligne['id']] = objet

    return resultat


def lire_cible(objet, colonne):
    # Lit la valeur d'une colonne spécifique d'un objet
    if colonne == 'valeur':
        return objet.valeur

    if colonne == 'etat':
        return objet.etat
    # Si c'est une autre colonne, on cherche dans le dictionnaire des colonnes supplémentaires
    return objet.colonnes.get(colonne, '')


def ecrire_cible(objet, colonne, valeur):
    # Écrit une valeur dans la colonne d'un objet
    if colonne == 'valeur':
        objet.valeur = nombre_ou_zero(valeur)

    elif colonne == 'etat':
        objet.etat = str(valeur)

    else:
        # Si c'est une autre colonne, on écrit dans le dictionnaire des colonnes supplémentaires
        objet.colonnes[colonne] = valeur


def condition_valide(objet, colonne, operateur, valeur):
    # Vérifie si une condition est remplie sur un objet (par exemple : valeur > 5)
    courant = lire_cible(objet, colonne)

    try:
        # Essaie de comparer en tant que nombres (convertit les virgules en points)
        gauche = float(str(courant).replace(',', '.'))
        droite = float(str(valeur).replace(',', '.'))

    except Exception:
        # Si ça échoue, compare en tant que texte
        gauche = str(courant)
        droite = str(valeur)
    # Applique l'opérateur de comparaison
    if operateur == '=':
        return gauche == droite

    if operateur == '<':
        return gauche < droite

    if operateur == '>':
        return gauche > droite
    # Si l'opérateur n'est pas reconnu, la condition est fausse
    return False


def parser_nombre_operation(valeur):
    # Extrait le signe (+, -, *, /) et le nombre d'une opération, par exemple "+3.5" donne ('+', 3.5)
    texte = str(valeur).strip()

    if len(texte) < 2:
        return '', 0

    return texte[0], float(texte[1:].replace(',', '.'))


def valeur_conservee(valeur_effet, expression, profondeur=1):
    # Calcule la valeur transmise lors de la propagation en fonction de l'expression de conservation
    # Par exemple "n/2" divise la valeur par 2 à chaque niveau de profondeur
    texte = str(expression).strip().lower().replace(' ', '')
    # Si l'expression est vide ou 'n', on garde la valeur telle quelle
    if texte in ('', 'n'):
        return valeur_effet

    signe, nombre = parser_nombre_operation(valeur_effet)
    # Si pas de signe valide, on retourne la valeur d'origine
    if signe == '':
        return valeur_effet
    # Format "n/X" : divise par X^profondeur (la valeur diminue avec la distance)
    if texte.startswith('n/'):
        diviseur = float(texte.split('/', 1)[1].replace(',', '.'))

        if diviseur != 0:
            return signe + str(nombre / (diviseur ** profondeur))
    # Format "X/n" : multiplie par X (la valeur est fixe peu importe la distance)
    if texte.endswith('/n'):
        multiplicateur = texte[:-2]

        try:
            coeff = float(multiplicateur.replace(',', '.')) if multiplicateur else 1
        except Exception:
            coeff = 1

        return signe + str(nombre * coeff)

    return valeur_effet


def appliquer_action(objet, colonne, action, valeur_effet, table_inversion):
    # Applique une action sur un objet (opération mathématique, changement de valeur, ou inversion)
    journal = ''
    # Lit la valeur actuelle de la colonne ciblée
    courant = lire_cible(objet, colonne)
    # Action "op" : opération mathématique (+, -, *, /)
    if action == 'op':
        # Sépare le signe (+, -, *, /) du nombre
        signe = str(valeur_effet)[0]
        nombre = float(str(valeur_effet)[1:].replace(',', '.'))
        base = nombre_ou_zero(courant)
        # Applique l'opération en fonction du signe
        if signe == '+':
            base += nombre
        elif signe == '-':
            base -= nombre
        elif signe == '*':
            base *= nombre
        elif signe == '/' and nombre != 0:
            base /= nombre
        # Écrit le nouveau résultat dans l'objet
        ecrire_cible(objet, colonne, base)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(base)
    # Action "change" : remplace la valeur directement
    elif action == 'change':

        ecrire_cible(objet, colonne, valeur_effet)
        journal = objet.nom + ' : ' + colonne + ' devient ' + str(valeur_effet)
    # Action "inv" : inverse la valeur selon la table d'inversion (par exemple "ouvert" <-> "ferme")
    elif action == 'inv':

        texte = str(courant).strip()
        # Cherche dans la table d'inversion la valeur correspondante
        if texte in table_inversion:
            nouvelle_valeur = table_inversion[texte]
            ecrire_cible(objet, colonne, nouvelle_valeur)
            journal = objet.nom + ' : ' + colonne + ' passe de ' + str(courant) + ' a ' + str(nouvelle_valeur)

    return journal


def profondeur_depuis_source(graphe, depart):
    # Parcours en largeur (BFS) du graphe pour calculer la distance de chaque nœud par rapport au nœud de départ
    # Utile pour la propagation : savoir à combien de "sauts" se trouve chaque voisin
    profondeurs = {depart: 0}
    file_attente = [depart]

    while file_attente:
        # Prend le premier élément de la file (FIFO = premier entré, premier sorti)
        courant = file_attente.pop(0)
        # Parcourt tous les voisins du nœud courant
        for voisin in graphe.get(courant, []):
            # Si le voisin n'a pas encore été visité, on calcule sa profondeur
            if voisin not in profondeurs:
                profondeurs[voisin] = profondeurs[courant] + 1
                file_attente.append(voisin)

    return profondeurs


def formater_temps(tour, valeur_tour, unite_tour):
    # Convertit le numéro de tour en temps lisible (par exemple tour 3 * 0.5 heure = "1.5 heure")
    total = tour * valeur_tour
    texte = str(total)
    # Enlève le ".0" à la fin si c'est un nombre entier (pour afficher "3" au lieu de "3.0")
    if texte.endswith('.0'):
        texte = texte[:-2]
    # Ajoute l'unité de temps si elle est définie
    if unite_tour:
        return texte + ' ' + unite_tour

    return texte

def extraire_frequence_et_unite(texte_frequence):
    # Cette fonction découpe la frequence en :
    # une partie numérique
    # une unité éventuelle
    # Exemple :
    # "2" → (2 , "")
    # "1s" → (1 , "s")
    # "5min" → (5 , "min")

    texte = str(texte_frequence).strip()  # securite : transforme en texte

    if texte == '':
        return 1.0, ''  # valeur par defaut

    position = 0

    # caracteres autorises pour la partie numerique
    caracteres_autorises = '0123456789.,'

    # on avance tant que ce sont des chiffres
    while position < len(texte) and texte[position] in caracteres_autorises:
        position += 1

    # partie nombre
    nombre = texte[:position].strip()

    # partie unite
    unite = texte[position:].strip()

    if nombre == '':
        return 1.0, ''

    # remplacement virgule pour float python
    return float(nombre.replace(',', '.')), unite


def repetitions_paterne_dans_le_tour(paterne, avancement_paternes, valeur_tour, unite_tour, dico_unites):
    # Cette fonction calcule combien de fois un paterne doit agir
    # pendant un tour de simulation
    # On récupère la quantité et l'unité
    quantite, unite_frequence = extraire_frequence_et_unite(paterne.frequence)
    if quantite <= 0:
        return 0  # sécurité
    # CAS 1 :
    # fréquence en tours (ancien comportement)
    # Exemple : frequence = 2 → tous les 2 tours
    if unite_frequence == '':
        frequence_tours = int(quantite)
        if frequence_tours <= 0:
            return 0
        # si le tour est divisible par la frequence
        if paterne.tour_courant % frequence_tours == 0:
            return 1
        return 0
    # CAS 2 :
    # fréquence avec unité utilisateur
    if unite_tour == '':
        return 0  # impossible sans unité du tour
    # On convertit la durée d'un tour dans l'unité du paterne
    # Exemple :
    # 1 min → 60 s
    duree_tour = convertir(
        dico_unites,
        valeur_tour,
        unite_tour,
        unite_frequence
    )
    if duree_tour is None:
        return 0  # unité non compatible
    # temps déjà accumulé
    deja = avancement_paternes.get(paterne.id, 0.0)
    # on ajoute la durée du tour
    deja += float(duree_tour)
    repetitions = 0
    # epsilon pour éviter erreurs 
    epsilon = 0.0000001
    # tant qu'on peut déclencher
    while deja + epsilon >= quantite:
        repetitions += 1
        deja -= quantite
    # on garde le reste pour le prochain tour
    avancement_paternes[paterne.id] = deja
    return repetitions

def analyser_observations(selection_objets, journal, etat):
    # Transforme la sélection utilisateur en dictionnaire d'observations
    # et mémorise aussi le mode :
    # - auto = l'utilisateur a juste clique sur un objet
    # - explicite = l'utilisateur a ecrit objet(col1 ; col2)

    observations = {}  # Dictionnaire final

    for entree in selection_objets:  # Parcourt chaque demande
        texte = str(entree).strip()  # Nettoie le texte

        if texte == '':
            continue  # Ignore les lignes vides

        # Cas 1 : l'utilisateur a juste choisi un objet
        if '(' not in texte or not texte.endswith(')'):
            nom_objet = texte  # Nom simple de l'objet
            colonnes = []  # Colonnes à observer

            # Cherche les vraies colonnes supplémentaires de l'objet
            for objet in etat.values():
                if objet.nom == nom_objet:
                    colonnes = list(objet.colonnes.keys())
                    break

            # Si aucune colonne supplémentaire, on retombe sur "valeur"
            if len(colonnes) == 0:
                colonnes = ['valeur']

            observations[nom_objet] = {
                'colonnes': colonnes,
                'mode': 'auto'
            }
            continue

        # Cas 2 : l'utilisateur a précisé des colonnes
        nom_objet = texte.split('(', 1)[0].strip()  # Nom avant parenthèse
        contenu = texte[texte.find('(') + 1:-1]  # Contenu entre parenthèses

        colonnes = []  # Colonnes demandées

        for morceau in contenu.split(';'):  # Découpe les colonnes sur ;
            nom_colonne = morceau.strip()  # Nettoie
            if nom_colonne != '':
                colonnes.append(nom_colonne)

        if len(colonnes) == 0:
            colonnes = ['valeur']  # Sécurité

        observations[nom_objet] = {
            'colonnes': colonnes,
            'mode': 'explicite'
        }

    return observations


def lire_observation(etat_tour, nom_objet, nom_colonne):
    # Lit une observation pour un objet donné
    # Retourne :
    # - une valeur numérique si possible
    # - une valeur texte pour le journal

    if nom_objet not in etat_tour:
        return None, None  # Objet introuvable

    infos = etat_tour[nom_objet]

    # Colonne spéciale "valeur"
    if nom_colonne == 'valeur':
        return nombre_ou_zero(infos['valeur']), str(infos['valeur'])

    # Colonne spéciale "etat"
    if nom_colonne == 'etat':
        return None, str(infos['etat'])

    # Colonnes supplémentaires
    if nom_colonne in infos['colonnes']:
        valeur = infos['colonnes'][nom_colonne]

        try:
            return float(str(valeur).replace(',', '.')), str(valeur)
        except Exception:
            return None, str(valeur)

    return None, None  # Colonne introuvable


def etiquette_observation(nom_objet, nom_colonne):
    # Crée une étiquette lisible pour le graphique
    return nom_objet + '.' + nom_colonne

def colonne_numerique(etat_source, nom_objet, nom_colonne):
    # Vérifie si une colonne peut être utilisée dans un graphique
    if nom_objet not in etat_source:
        return False
    infos = etat_source[nom_objet]
    # valeur est toujours numérique
    if nom_colonne == 'valeur':
        return True
    # etat est toujours texte
    if nom_colonne == 'etat':
        return False
    # colonne inexistante
    if nom_colonne not in infos['colonnes']:
        return False
    valeur = infos['colonnes'][nom_colonne]
    try:
        float(str(valeur).replace(',', '.'))
        return True
    except Exception:
        return False

def simuler(objets, liaisons, evenements_lignes, paternes_lignes, inversions, nb_tours, objets_observes, valeur_tour=1, unite_tour='', unites_lignes=None):
    # Fonction principale de simulation
    # Elle prépare l'état initial, applique les paternes et événements,
    # construit le journal, puis prépare les courbes du graphique.

    etat = objets_etat(objets)  # transforme les lignes objets en objets de simulation

    table_inversion = {}  # dictionnaire des inversions texte -> texte
    for ligne in inversions:  # remplit la table des inversions dans les 2 sens
        table_inversion[ligne['valeur_0']] = ligne['valeur_1']
        table_inversion[ligne['valeur_1']] = ligne['valeur_0']

    catalogue = [{'nom': o.nom} for o in etat.values()]  # petit catalogue pour construire le graphe
    graphe, poids, conservations = construire_graphe(catalogue, liaisons)  # graphe + poids + regles de conservation
    evenements = [Evenement(x) for x in evenements_lignes]  # transforme les lignes de base en objets Evenement
    paternes = [Paterne(x) for x in paternes_lignes]  # transforme les lignes de base en objets Paterne
    # construction du dictionnaire des unites utilisateur
    # permet les conversions entre unites
    dico_unites = dictionnaire_unites(unites_lignes or [])
    # dictionnaire qui stocke le temps accumule
    # pour les paternes avec unite
    avancement_paternes = {}
    historique = []  # contiendra tous les tours
    journal_global = []  # garde une compatibilite avec le reste du code

    observations_demandees = analyser_observations(objets_observes, journal_global, etat)  # analyse ce que l'utilisateur veut observer

    courbes = {}  # dictionnaire : etiquette -> liste des valeurs numeriques
    colonnes_graphiques = {}  # dictionnaire : nom_objet -> colonnes a tracer
    nb_courbes_max = 6  # limite seulement pour la selection manuelle simple
    nb_courbes_auto = 0  # compteur de courbes du mode auto

    etat_depart = {}  # etat simplifie du depart pour tester quelles colonnes sont numeriques
    for obj in etat.values():
        etat_depart[obj.nom] = {
            'valeur': obj.valeur,
            'etat': obj.etat,
            'colonnes': dict(obj.colonnes)
        }

    # Preparation des courbes selon le mode d'observation
    for nom_objet, infos_observation in observations_demandees.items():
        colonnes = infos_observation['colonnes']  # liste des colonnes a observer
        mode = infos_observation['mode']  # "auto" ou "explicite"
        colonnes_graphiques[nom_objet] = []  # initialise la liste des colonnes du graphique pour cet objet

        # Mode explicite : si l'utilisateur ecrit Objet(col1 ; col2),
        # on garde seulement la premiere colonne pour le graphique.
        if mode == 'explicite':
            premiere_colonne = colonnes[0]
            if colonne_numerique(etat_depart, nom_objet, premiere_colonne):
                etiquette = etiquette_observation(nom_objet, premiere_colonne)
                courbes[etiquette] = []
                colonnes_graphiques[nom_objet].append(premiere_colonne)

        # Mode auto : si l'utilisateur clique juste sur un objet,
        # on trace toutes les colonnes numeriques, avec une limite de 6 courbes max.
        else:
            for nom_colonne in colonnes:
                if nb_courbes_auto >= nb_courbes_max:
                    break
                if colonne_numerique(etat_depart, nom_objet, nom_colonne):
                    etiquette = etiquette_observation(nom_objet, nom_colonne)
                    courbes[etiquette] = []
                    colonnes_graphiques[nom_objet].append(nom_colonne)
                    nb_courbes_auto += 1

    # Boucle principale de simulation
    for tour in range(nb_tours + 1):
        journal = []  # actions du tour courant

        # A partir du tour 1, on applique les effets
        if tour > 0:
            
            # Application des paternes
            for paterne in paternes:

                # ignore paternes desactives
                if paterne.actif != 1:
                    continue

                # on mémorise le tour courant
                # utile pour les frequences en tours
                paterne.tour_courant = tour

                #calcul combien de fois le paterne agit
                repetitions = repetitions_paterne_dans_le_tour(
                    paterne,
                    avancement_paternes,
                    valeur_tour,
                    unite_tour,
                    dico_unites
                    )

                if repetitions <= 0:
                    continue

                objet = etat.get(paterne.objet_effet_id)

                if objet is None:
                    continue

                # le paterne peut agir plusieurs fois
                # dans un seul tour
                for numero in range(repetitions):
                    txt = appliquer_action(
                        objet,
                        paterne.colonne_effet,
                        paterne.action,
                        paterne.valeur_effet,
                        table_inversion
                    )
                    if txt:
                    #affichage propre dans journal
                        if repetitions == 1:
                            journal.append('Paterne ' + paterne.nom + ' -> ' + txt)
                        else:
                            journal.append('Paterne ' + paterne.nom + ' (' + str(numero + 1) + '/' + str(repetitions) + ') -> ' + txt)

            # Application des événements
            for evenement in evenements:
                if evenement.actif != 1:
                    continue  # ignore les événements inactifs
                if tour < evenement.arrivee:
                    continue  # l'événement n'est pas encore arrivé

                cause = etat.get(evenement.objet_cause_id)  # objet qui sert de cause
                effet = etat.get(evenement.objet_effet_id)  # objet qui reçoit l'effet
                if cause is None or effet is None:
                    continue  # securite si un objet manque

                # Verifie la condition de declenchement
                if not condition_valide(cause, evenement.colonne_cause, evenement.operateur, evenement.valeur_cause):
                    continue

                # Verifie la probabilite de declenchement
                if random() > evenement.proba:
                    continue

                # Applique l'effet principal
                txt = appliquer_action(effet, evenement.colonne_effet, evenement.action, evenement.valeur_effet, table_inversion)
                if txt:
                    journal.append('Evenement ' + evenement.nom + ' -> ' + txt)

                # Gere la propagation si demandee
                if evenement.propagation != 0:
                    profondeurs = profondeur_depuis_source(graphe, effet.nom)  # calcule la distance des voisins a partir de l'objet effet
                    for nom_voisin, profondeur in profondeurs.items():
                        if profondeur == 0:
                            continue  # ignore l'objet source lui-meme
                        if evenement.propagation != -1 and profondeur > evenement.propagation:
                            continue  # ignore les voisins trop loin si propagation limitee

                        proba_liaison = poids.get((effet.nom, nom_voisin), 1)  # probabilite de passage sur la liaison
                        if random() > proba_liaison:
                            continue  # la propagation echoue sur cette liaison

                        voisin = None  # cherchera l'objet voisin dans l'etat
                        for obj in etat.values():
                            if obj.nom == nom_voisin:
                                voisin = obj
                                break
                        if voisin is None:
                            continue  # securite si voisin introuvable

                        conservation = conservations.get((effet.nom, nom_voisin), 'n')  # regle de conservation de la liaison
                        valeur_transmise = valeur_conservee(evenement.valeur_effet, conservation, profondeur)  # calcule la valeur transmise selon la distance

                        txt = appliquer_action(voisin, evenement.colonne_effet, evenement.action, valeur_transmise, table_inversion)  # applique l'effet propage
                        if txt:
                            journal.append('Propagation ' + effet.nom + ' -> ' + nom_voisin + ' (' + conservation + ') -> ' + txt)

        # Construit l'etat du tour courant
        etat_tour = {}
        for obj in etat.values():
            etat_tour[obj.nom] = {
                'valeur': obj.valeur,
                'etat': obj.etat,
                'colonnes': dict(obj.colonnes)
            }

        # Construit les observations lisibles pour le journal
        observations_tour = {}
        for nom_objet, infos_observation in observations_demandees.items():
            colonnes = infos_observation['colonnes']  # colonnes a afficher pour cet objet
            observations_tour[nom_objet] = {}

            # Lit toutes les colonnes demandees pour le journal
            for nom_colonne in colonnes:
                valeur_num, valeur_txt = lire_observation(etat_tour, nom_objet, nom_colonne)
                if valeur_num is None and valeur_txt is None:
                    observations_tour[nom_objet][nom_colonne] = '(n existe pas)'  # colonne demandee mais absente
                else:
                    observations_tour[nom_objet][nom_colonne] = valeur_txt  # valeur lisible pour l'utilisateur

            # Alimente les courbes du graphique
            for nom_colonne_graphique in colonnes_graphiques.get(nom_objet, []):
                etiquette = etiquette_observation(nom_objet, nom_colonne_graphique)  # nom de la courbe, ex : Petrole.prix
                valeur_num, valeur_txt = lire_observation(etat_tour, nom_objet, nom_colonne_graphique)
                if valeur_num is None:
                    valeur_num = 0.0  # securite si la valeur n'est plus lisible
                courbes[etiquette].append(valeur_num)  # ajoute le point a la courbe

        # Ajoute ce tour a l'historique
        historique.append({
            'tour': tour,
            'temps': formater_temps(tour, valeur_tour, unite_tour),
            'actions': journal,
            'etat': etat_tour,
            'observations': observations_tour
        })

    return historique, courbes  # renvoie l'historique complet et les courbes

def svg_graphique(courbes, unite_temps='tour', unite_valeur='valeur'):
    # Génère un graphique SVG pour afficher les courbes de la simulation

    # Dimensions du SVG en pixels
    largeur = 760
    hauteur = 320
    # Si pas de courbes, retourne un SVG vide
    if not courbes:
        return "<svg width='760' height='80'></svg>"

    # Convertit toutes les valeurs en nombres (au cas où certaines sont du texte)
    courbes_numeriques = {}

    for nom, valeurs in courbes.items():
        courbes_numeriques[nom] = [nombre_ou_zero(v) for v in valeurs]

    # Calcule les valeurs min et max pour définir l'échelle du graphique
    maxi = max([max(valeurs) if valeurs else 0 for valeurs in courbes_numeriques.values()] + [1])
    mini = min([min(valeurs) if valeurs else 0 for valeurs in courbes_numeriques.values()] + [0])
    # Amplitude = différence entre max et min, sert à normaliser les valeurs
    amplitude = maxi - mini if maxi != mini else 1
    # Nombre maximum de points sur l'axe X
    nb_points = max([len(valeurs) for valeurs in courbes_numeriques.values()] + [1])

    # Palette de 6 couleurs pour différencier les courbes
    couleurs = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#ea580c', '#0891b2']

    # Début du SVG : fond blanc et axes
    lignes = [
        f"<svg width='{largeur}' height='{hauteur}' viewBox='0 0 {largeur} {hauteur}'>",
        "<rect x='0' y='0' width='100%' height='100%' fill='white'/>",
        # Axe horizontal (X)
        "<line x1='40' y1='260' x2='720' y2='260' stroke='black'/>",
        # Axe vertical (Y)
        "<line x1='40' y1='40' x2='40' y2='260' stroke='black'/>"
    ]

    # Dessine les graduations sur l'axe X (un trait + un numéro par point)
    for i in range(nb_points):
        x = 40 + (680 * i / max(1, nb_points - 1))
        lignes.append(f"<line x1='{x}' y1='260' x2='{x}' y2='265' stroke='black'/>")
        lignes.append(f"<text x='{x - 5}' y='278' font-size='10'>{i}</text>")

    # Dessine les graduations sur l'axe Y (6 niveaux du min au max)
    for i in range(6):
        y = 260 - (220 * i / 5)
        val = mini + (amplitude * i / 5)
        lignes.append(f"<line x1='35' y1='{y}' x2='40' y2='{y}' stroke='black'/>")
        lignes.append(f"<text x='5' y='{y + 4}' font-size='10'>{round(val, 1)}</text>")

    # Ajoute les légendes des axes
    lignes.append(f"<text x='340' y='298' font-size='13'>Temps ({unite_temps})</text>")
    lignes.append(f"<text x='5' y='20' font-size='13'>{unite_valeur}</text>")

    index = 0
    # Dessine chaque courbe avec une couleur différente
    for nom, valeurs in courbes_numeriques.items():
        # Choisit la couleur (boucle sur les 6 couleurs disponibles)
        couleur = couleurs[index % len(couleurs)]
        index += 1
        # Calcule les coordonnées de chaque point de la courbe
        points = []

        for i, valeur in enumerate(valeurs):
            # Calcule la position X (répartition uniforme sur la largeur)
            x = 40 + (680 * i / max(1, nb_points - 1))
            # Calcule la position Y (normalisée entre le min et le max)
            y = 240 - (180 * ((valeur - mini) / amplitude))
            points.append(f'{x},{y}')

        # Dessine la courbe en reliant tous les points
        lignes.append(
            f"<polyline fill='none' stroke='{couleur}' stroke-width='2' points='{' '.join(points)}'/>"
        )

        # Ajoute le nom de la courbe en légende (en haut à gauche, dans sa couleur)
        lignes.append(
            f"<text x='40' y='{25 + 18 * index}' fill='{couleur}' font-size='13'>{nom}</text>"
        )

    lignes.append('</svg>')
    # Retourne le SVG complet en une seule chaîne de caractères
    return ''.join(lignes)