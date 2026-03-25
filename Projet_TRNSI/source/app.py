from __future__ import annotations

# Three - application principale
# Cette application Flask sert uniquement d'interface.
# Le coeur du projet reste en Python et SQLite.

# Importe les modules Flask nécessaires pour créer l'application web
from flask import Flask, flash, redirect, render_template, request, session, url_for

# Importe le module base de données pour interagir avec SQLite
import base_donnees
# Importe la fonction de conversion d'unités
from conversions import convertir
# Importe la fonction pour générer l'arbre HTML des composants
from composants_utils import arbre_html
# Importe les fonctions de coloration syntaxique et d'exécution du code frank_sql
from frank_sql import colorer_code, executer_code, decouper_elements
# Importe les fonctions pour construire et afficher le graphe des liaisons en SVG
from graphe import construire_graphe, svg_graphe, matrice_adjacence
# Importe les fonctions utilitaires : conversion en entier/réel avec valeur par défaut, validation de noms et probabilités
from outils_nsi import entier_ou_defaut, nom_simple_valide, proba_valide, reel_ou_defaut
# Importe les fonctions de simulation et de génération de graphique SVG
from simulation import simuler, svg_graphique

# Crée l'application Flask
app = Flask(__name__)
# Clé secrète pour signer les sessions (cookies sécurisés)
app.secret_key = 'tree-nsi-2026'


def initialiser_univers():
    # Récupère le nom de l'univers depuis la session, par défaut 'univers_1'
    univers = session.get('univers', 'univers_1')
    # Active cet univers dans le module base_donnees (sélectionne la bonne base SQLite)
    base_donnees.choisir_univers(univers)


# Décorateur Flask : cette fonction s'exécute automatiquement avant chaque requête HTTP
@app.before_request
def avant_requete():
    # Initialise l'univers pour que chaque requête utilise la bonne base de données
    initialiser_univers()


# Décorateur Flask : injecte des variables globales dans tous les templates Jinja2
@app.context_processor
def contexte_global():
    # Rend disponibles 'nom_app' et 'univers_actuel' dans tous les templates HTML
    return {'nom_app': 'Tree', 'univers_actuel': session.get('univers', 'univers_1')}


def table_courante():
    # Détermine la table active : d'abord dans les paramètres GET, puis POST, sinon la table principale par défaut
    return request.args.get('table', request.form.get('table', base_donnees.nom_table_principale()))


def vers_dicts(lignes):
    # Convertit les lignes SQLite (objets Row) en dictionnaires Python classiques
    return [dict(ligne) for ligne in lignes]


def charger_graphe():
    # Charge tous les objets du catalogue et les liaisons depuis la base de données
    objets_catalogue = base_donnees.liste_objets_catalogue()
    liaisons = base_donnees.liste_liaisons()
    # Construit et retourne le graphe (structure de données) à partir des objets et liaisons
    return construire_graphe(objets_catalogue, liaisons)


def ajouter_liaisons_rapides(texte):
    # Ajoute plusieurs liaisons à partir d'un texte multiligne (une liaison par ligne)
    compteur = 0
    # Boucle sur chaque ligne non vide du texte
    for ligne in [x.strip() for x in texte.splitlines() if x.strip()]:
        type_liaison = '<=>'
        # Détecte si c'est une liaison bidirectionnelle (<=>)
        if '<=>' in ligne:
            morceaux = ligne.split('<=>')
            type_liaison = '<=>'
        # Sinon détecte si c'est une liaison unidirectionnelle (=>)
        elif '=>' in ligne:
            morceaux = ligne.split('=>')
            type_liaison = '=>'
        else:
            continue  # Si aucun séparateur trouvé, on ignore la ligne
        # Vérifie qu'il y a exactement 2 morceaux (source et cible)
        if len(morceaux) != 2:
            continue
        source = morceaux[0].strip()  # Nom de l'objet source
        cible = morceaux[1].strip()  # Nom de l'objet cible
        # Vérifie que ni la source ni la cible ne sont vides
        if source == '' or cible == '':
            continue
        # Ajoute la liaison dans la base de données avec poids 1 et sans conservation
        base_donnees.ajouter_liaison(source, cible, type_liaison, 1, 'n')
        compteur += 1  # Incrémente le compteur de liaisons ajoutées
    return compteur  # Retourne le nombre total de liaisons ajoutées


# ROUTES
# Affiche la page d'index avec la liste des univers disponibles
@app.route('/')
def index():
    return render_template('index.html', univers=base_donnees.liste_univers())


# Route pour ouvrir/sélectionner un univers spécifique
@app.route('/ouvrir/<nom_univers>')
def ouvrir_univers(nom_univers):
    # Sauvegarde le nom de l'univers dans la session
    session['univers'] = nom_univers
    # Active l'univers dans le module base_donnees
    base_donnees.choisir_univers(nom_univers)
    # Redirige vers la page des données
    return redirect(url_for('page_donnees'))


# Route pour réinitialiser un univers (remet la base de données à zéro)
@app.route('/reinitialiser/<nom_univers>', methods=['POST'])
def reinitialiser_univers(nom_univers):
    session['univers'] = nom_univers
    base_donnees.choisir_univers(nom_univers)
    # Supprime toutes les données de l'univers
    base_donnees.reinitialiser_univers()
    # Affiche un message de confirmation
    flash('Univers reinitialise.', 'succes')
    return redirect(url_for('index'))


# Route principale pour gérer les données (tables, colonnes, objets, unités, inversions)
@app.route('/donnees', methods=['GET', 'POST'])
def page_donnees():
    # Récupère le nom de la table actuellement sélectionnée
    nom_table = table_courante()
    # Si c'est une requête POST, on traite l'action demandée
    if request.method == 'POST':
        # Récupère le type d'action à effectuer depuis le formulaire
        action = request.form.get('action', '')
        try:
            # Créer une nouvelle table
            if action == 'creer_table':
                # Récupère et nettoie le nom de la nouvelle table (remplace les espaces par des underscores)
                nom_table_nouvelle = request.form.get('nom_table_nouvelle', '').strip().replace(' ', '_')
                # Vérifie que le nom de table est valide (caractères alphanumériques)
                if not nom_simple_valide(nom_table_nouvelle.replace('_', 'a')):
                    raise ValueError('Nom de table invalide')
                # Crée la table dans la base de données (sans colonnes initiales)
                base_donnees.creer_table_nsi(nom_table_nouvelle, 0, [])
                nom_table = nom_table_nouvelle  # Met à jour la table active
                flash('Table creee.', 'succes')

            # Ajouter une colonne à la table
            elif action == 'ajouter_colonne':
                base_donnees.ajouter_colonne_table(
                    nom_table,
                    request.form.get('nom_colonne', '').strip().replace(' ', '_'),  # Nom de la colonne nettoyé
                    request.form.get('type_colonne', 'texte'),  # Type de la colonne (texte par défaut)
                    request.form.get('valeur_defaut', '')  # Valeur par défaut (vide)
                )
                flash('Colonne ajoutee.', 'succes')

            # Supprimer une colonne de la table
            elif action == 'supprimer_colonne':
                base_donnees.supprimer_colonne_table(
                    nom_table,
                    request.form.get('nom_colonne', '').strip()  # Nom de la colonne à supprimer
                )
                flash('Colonne supprimee.', 'succes')

            # Ajouter un objet à la table
            elif action == 'ajouter_objet':
                # Prépare les données de base de l'objet (nom, valeur, état)
                donnees = {
                    'nom': request.form.get('nom', '').strip(),
                    'valeur': reel_ou_defaut(request.form.get('valeur', '0'), 0),  # Convertit en nombre réel
                    'etat': request.form.get('etat', '').strip()
                }

                # Récupère les valeurs des colonnes personnalisées de la table
                for ligne in base_donnees.liste_colonnes_table(nom_table):
                    donnees[ligne['nom_colonne']] = request.form.get(
                        ligne['nom_colonne'],
                        ligne['valeur_defaut']  # Utilise la valeur par défaut si non rempli
                    )

                # Ajoute l'objet dans la table
                base_donnees.ajouter_objet_table(nom_table, donnees)
                flash('Objet ajoute.', 'succes')

            # Ajout rapide d'objets et liaisons via texte
            elif action == 'ajout_rapide':
                # Importe les fonctions nécessaires depuis frank_sql
                from frank_sql import ajouter_liaisons_texte, ajouter_objet_rapide, decouper_elements

                # Récupère le bloc de texte saisi par l'utilisateur
                bloc = request.form.get('bloc_objets', '')
                bilan_liaisons = 0  # Compteur de liaisons ajoutées
                elements = []  # Liste des éléments à traiter

                # Découpe chaque ligne du bloc en éléments séparés par ;
                for ligne in bloc.splitlines():
                    ligne = ligne.strip()
                    if ligne == '':
                        continue  # Ignore les lignes vides
                    elements.extend(decouper_elements(ligne, ';'))

                # Traite chaque élément : soit comme liaison, soit comme objet
                for ligne in [x.strip() for x in elements if x.strip()]:
                    # Si l'élément contient => ou <=>, c'est une liaison
                    if '=>' in ligne or '<=>' in ligne:
                        bilan_liaisons += ajouter_liaisons_texte(ligne, base_donnees, nom_table)
                        continue
                    # Sinon c'est un objet simple à ajouter
                    ajouter_objet_rapide(ligne, nom_table, base_donnees)

                # Affiche le bilan de l'ajout rapide
                if bilan_liaisons > 0:
                    flash(
                        'Ajout rapide termine : objets et ' + str(bilan_liaisons) + ' liaison(s).',
                        'succes'
                    )
                else:
                    flash('Ajout rapide termine.', 'succes')

            # Ajouter une unité de mesure
            elif action == 'ajouter_unite':
                base_donnees.ajouter_unite(
                    request.form.get('nom_unite', '').strip(),  # Nom de l'unité
                    request.form.get('unite_dessous', '').strip(),  # Unité inférieure (pour la conversion)
                    reel_ou_defaut(request.form.get('facteur', '0'), 0)  # Facteur de conversion
                )
                flash('Unite ajoutee.', 'succes')

            # Ajouter une inversion (paire de valeurs inversées)
            elif action == 'ajouter_inversion':
                base_donnees.ajouter_inversion(
                    request.form.get('valeur_0', ''),  # Première valeur de la paire
                    request.form.get('valeur_1', '')  # Deuxième valeur de la paire
                )
                flash('Inversion ajoutee.', 'succes')

            # Supprimer un objet par son nom
            elif action == 'supprimer_objet':
                base_donnees.supprimer_objet_par_nom(request.form.get('nom_objet', '').strip())
                flash('Objet supprime.', 'succes')

            # Supprimer une table entière
            elif action == 'supprimer_table':
                base_donnees.supprimer_table_nsi(request.form.get('nom_table', '').strip())
                nom_table = base_donnees.nom_table_principale()  # Revient à la table principale
                flash('Table supprimee.', 'succes')

            # Supprimer une inversion
            elif action == 'supprimer_inversion':
                base_donnees.supprimer_inversion(
                    entier_ou_defaut(request.form.get('id_inversion', '0'), 0)  # ID de l'inversion à supprimer
                )
                flash('Inversion supprimee.', 'succes')

        except Exception as exc:
            # En cas d'erreur, affiche le message d'erreur
            flash(str(exc), 'erreur')

        # Redirige vers la page des données avec la table active
        return redirect(url_for('page_donnees', table=nom_table))

    # Charge toutes les données pour l'affichage
    tables = vers_dicts(base_donnees.liste_tables_nsi())  # Liste de toutes les tables
    objets = vers_dicts(base_donnees.liste_objets(nom_table))  # Objets de la table active
    colonnes = vers_dicts(base_donnees.liste_colonnes_table(nom_table))  # Colonnes personnalisées
    colonnes_physiques = list(base_donnees.colonnes_physiques(nom_table))  # Noms des colonnes réelles dans SQLite
    unites = vers_dicts(base_donnees.liste_unites())  # Liste des unités de mesure
    inversions = vers_dicts(base_donnees.liste_inversions())  # Liste des inversions

    # Envoie toutes les données au template HTML pour affichage
    return render_template(
        'donnees.html',
        tables=tables,
        table_active=nom_table,
        objets=objets,
        colonnes=colonnes,
        colonnes_physiques=colonnes_physiques,
        unites=unites,
        inversions=inversions
    )


# Route pour gérer les liaisons entre objets
@app.route('/liaisons', methods=['GET', 'POST'])
def page_liaisons():
    if request.method == 'POST':
        action = request.form.get('action', 'ajouter')
        try:
            # Ajout rapide de liaisons via texte multiligne
            if action == 'ajout_rapide':
                compteur = ajouter_liaisons_rapides(request.form.get('bloc_liaisons', ''))
                flash(str(compteur) + ' liaison(s) ajoutee(s).', 'succes')

            # Supprimer une liaison par son ID
            elif action == 'supprimer_liaison':
                base_donnees.supprimer_liaison(
                    entier_ou_defaut(request.form.get('id_liaison', '0'), 0)
                )
                flash('Liaison supprimee.', 'succes')

            # Par défaut on ajoute une liaison simple
            else:
                base_donnees.ajouter_liaison(
                    request.form.get('source_nom', ''),  # Nom de l'objet source
                    request.form.get('cible_nom', ''),  # Nom de l'objet cible
                    request.form.get('type_liaison', '=>'),  # Type : => ou <=>
                    reel_ou_defaut(request.form.get('poids', '1'), 1),  # Poids de la liaison (probabilité)
                    request.form.get('conservation', 'n')  # Conservation : oui ou non
                )
                flash('Liaison ajoutee.', 'succes')

        except Exception as exc:
            flash(str(exc), 'erreur')

        return redirect(url_for('page_liaisons'))

    # Charge les données pour l'affichage
    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())  # Tous les objets
    liaisons = vers_dicts(base_donnees.liste_liaisons())  # Toutes les liaisons
    graphe, poids, _ = charger_graphe()  # Construit le graphe pour la visualisation
    graphe, poids, conservations = construire_graphe(objets_catalogue, liaisons)

    # Liste des noms pour la matrice
    noms = [o['nom'] for o in objets_catalogue]

    # Matrice d'adjacence
    matrice = matrice_adjacence(graphe, noms)

    # Objet de départ pour les parcours
    depart = request.args.get("depart")

    if not depart and noms:
        depart = noms[0]

    # Affiche la page avec le graphe SVG des liaisons
    return render_template(
        'liaisons.html',
        objets_catalogue=objets_catalogue,
        liaisons=liaisons,
        svg=svg_graphe(objets_catalogue, graphe, poids),  # Génère le SVG du graphe
        depart=depart,
        matrice=matrice
    )


# Route pour gérer les compositions (relations parent-enfant entre objets)
@app.route('/composants', methods=['GET', 'POST'])
def page_composants():
    if request.method == 'POST':
        action = request.form.get('action', '')
        try:
            # Ajouter une composition parent-enfant
            if action == 'ajouter_composant':
                base_donnees.ajouter_composition(
                    request.form.get('parent_nom', ''),  # Nom de l'objet parent
                    request.form.get('enfant_nom', ''),  # Nom de l'objet enfant
                    entier_ou_defaut(request.form.get('quantite', '1'), 1)  # Quantité de l'enfant
                )
                # Essaie aussi d'ajouter une liaison enfant => parent automatiquement
                try:
                    base_donnees.ajouter_liaison(
                        request.form.get('enfant_nom', ''),
                        request.form.get('parent_nom', ''),
                        '=>',
                        1,
                        'n'
                    )
                except Exception:
                    pass  # Si la liaison existe déjà, on ignore l'erreur
                flash('Composition ajoutee.', 'succes')

            # Ajout rapide de composants via texte
            elif action == 'ajout_rapide_cp':
                parent = request.form.get('parent_rapide', '').strip()  # Nom du parent
                bloc = request.form.get('bloc_cp', '')  # Texte avec les enfants séparés par ;
                morceaux = [m.strip() for m in bloc.split(';') if m.strip()]

                # Boucle sur chaque enfant
                for morceau in morceaux:
                    quantite = 1  # Quantité par défaut
                    enfant = morceau

                    # Vérifie si la quantité est spécifiée entre parenthèses, par ex: "bois(3)"
                    if '(' in morceau and morceau.endswith(')'):
                        enfant = morceau.split('(', 1)[0].strip()  # Extrait le nom de l'enfant
                        quantite = entier_ou_defaut(
                            morceau[morceau.find('(') + 1:-1],  # Extrait le nombre entre parenthèses
                            1
                        )

                    # Ajoute la composition parent-enfant
                    base_donnees.ajouter_composition(parent, enfant, quantite)

                    # Essaie d'ajouter une liaison enfant => parent
                    try:
                        base_donnees.ajouter_liaison(enfant, parent, '=>', 1, 'n')
                    except Exception:
                        pass  # Si la liaison existe déjà, on ignore

                flash('Ajout rapide des composants termine.', 'succes')

            # Supprimer une composition par son ID
            elif action == 'supprimer_composition':
                base_donnees.supprimer_composition(
                    entier_ou_defaut(request.form.get('id_composition', '0'), 0)
                )
                flash('Composition supprimee.', 'succes')

            # Fusion d'objets (crée un objet résultat composé de plusieurs objets)
            elif action == 'fusion':
                nom_resultat = request.form.get('nom_resultat', '').strip()  # Nom de l'objet résultat
                table = base_donnees.nom_table_principale()

                # Si l'objet résultat n'existe pas encore, on le crée
                if base_donnees.objet_global_par_nom(nom_resultat) is None:
                    base_donnees.ajouter_objet_table(
                        table,
                        {'nom': nom_resultat, 'valeur': 0, 'etat': ''}
                    )

                # Récupère la formule de fusion (ex: "2bois + 3pierre + fer")
                texte_fusion = request.form.get('fusion', '')

                # Découpe la formule par le signe + pour avoir chaque composant
                for morceau in [m.strip() for m in texte_fusion.split('+') if m.strip()]:
                    quantite = 1
                    nom = morceau

                    # Détecte si un nombre précède le nom (ex: "2bois" => quantite=2, nom="bois")
                    if len(morceau) > 1 and morceau[0].isdigit():
                        prefixe = ''
                        for caractere in morceau:
                            if caractere.isdigit():
                                prefixe += caractere
                            else:
                                break  # Arrête dès qu'on trouve un caractère non-numérique
                        quantite = entier_ou_defaut(prefixe, 1)
                        nom = morceau[len(prefixe):].strip()  # Le reste est le nom de l'objet

                    # Si l'objet existe, on l'ajoute comme composant de la fusion
                    if base_donnees.objet_global_par_nom(nom) is not None:
                        base_donnees.ajouter_composition(nom_resultat, nom, quantite)

                flash('Fusion enregistree.', 'succes')

        except Exception as exc:
            flash(str(exc), 'erreur')

        return redirect(url_for('page_composants'))

    # Charge les données pour l'affichage
    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())  # Tous les objets
    compositions = vers_dicts(base_donnees.liste_compositions())  # Toutes les compositions
    # Récupère l'objet racine pour l'arbre (premier objet par défaut)
    racine = request.args.get('racine', objets_catalogue[0]['nom'] if objets_catalogue else '')
    # Nombre maximum de branches à afficher dans l'arbre
    max_branches = entier_ou_defaut(request.args.get('max_branches', '6'), 6)
    # Génère l'arbre HTML des compositions à partir de la racine
    arbre = arbre_html(base_donnees, racine, 0, max_branches) if racine else ''

    return render_template(
        'composants.html',
        objets_catalogue=objets_catalogue,
        compositions=compositions,
        arbre=arbre,
        racine=racine,
        max_branches=max_branches
    )


@app.route('/simulation', methods=['GET', 'POST'])
def page_simulation():
    # Charge toutes les donnees necessaires a la simulation
    objets = vers_dicts(base_donnees.liste_objets_simulation())  # Objets avec leurs valeurs de simulation
    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())  # Catalogue complet des objets
    evenements = vers_dicts(base_donnees.liste_evenements())  # Liste des evenements configures
    paternes = vers_dicts(base_donnees.liste_paternes())  # Liste des paternes
    liaisons = vers_dicts(base_donnees.liste_liaisons())  # Liaisons entre objets
    inversions = vers_dicts(base_donnees.liste_inversions())  # Paires d'inversions
    unites = vers_dicts(base_donnees.liste_unites())  # Unites disponibles

    resultat = None  # Resultat de la simulation
    selection_objets = []  # Objets/observations a suivre
    nb_tours = 8  # Valeur par defaut
    valeur_tour = 1  # Valeur d'un tour par defaut
    unite_tour = unites[0]['nom'] if unites else ''  # Premiere unite par defaut

    if request.method == 'POST':
        action = request.form.get('action', 'simuler')  # Action demandee

        try:
            # Ajouter un evenement
            if action == 'ajouter_evenement':
                proba = reel_ou_defaut(request.form.get('proba', '1'), 1)  # Probabilite de l'evenement

                if not proba_valide(proba):
                    raise ValueError('La probabilite doit etre entre 0 et 1')

                propagation_texte = request.form.get('propagation', '0').strip().lower()  # Texte saisi
                propagation = -1 if propagation_texte == 'all' else entier_ou_defaut(propagation_texte, 0)  # all -> -1

                base_donnees.ajouter_evenement(
                    request.form.get('nom', ''),  # Nom
                    entier_ou_defaut(request.form.get('objet_cause_id', '0'), 0),  # Objet cause
                    request.form.get('colonne_cause', 'valeur'),  # Colonne cause
                    request.form.get('operateur', '='),  # Operateur
                    request.form.get('valeur_cause', '0'),  # Valeur cause
                    entier_ou_defaut(request.form.get('objet_effet_id', '0'), 0),  # Objet effet
                    request.form.get('colonne_effet', 'valeur'),  # Colonne effet
                    request.form.get('action_effet', 'op'),  # Action
                    request.form.get('valeur_effet', '+1'),  # Valeur effet
                    proba,  # Probabilite
                    entier_ou_defaut(request.form.get('arrivee', '0'), 0),  # Tour d'arrivee
                    propagation  # Propagation
                )

                flash('Evenement ajoute.', 'succes')
                return redirect(url_for('page_simulation'))

            # Ajouter un paterne
            if action == 'ajouter_paterne':
                base_donnees.ajouter_paterne(
                    request.form.get('nom', ''),  # Nom
                    entier_ou_defaut(request.form.get('objet_effet_id', '0'), 0),  # Objet cible
                    request.form.get('colonne_effet', 'valeur'),  # Colonne effet
                    request.form.get('action_effet', 'op'),  # Action
                    request.form.get('valeur_effet', '+1'),  # Valeur effet
                    request.form.get('frequence', '1').strip() or '1'  # Frequence : 2, 1s, 5min, etc.
                )

                flash('Paterne ajoute.', 'succes')
                return redirect(url_for('page_simulation'))

            # Activer / desactiver un evenement
            if action == 'changer_etat_evenement':
                base_donnees.changer_etat_evenement(
                    entier_ou_defaut(request.form.get('id', '0'), 0),
                    entier_ou_defaut(request.form.get('actif', '1'), 1)
                )
                return redirect(url_for('page_simulation'))

            # Supprimer un evenement
            if action == 'supprimer_evenement':
                base_donnees.supprimer_evenement(
                    entier_ou_defaut(request.form.get('id', '0'), 0)
                )
                flash('Evenement supprime.', 'succes')
                return redirect(url_for('page_simulation'))

            # Activer / desactiver un paterne
            if action == 'changer_etat_paterne':
                base_donnees.changer_etat_paterne(
                    entier_ou_defaut(request.form.get('id', '0'), 0),
                    entier_ou_defaut(request.form.get('actif', '1'), 1)
                )
                return redirect(url_for('page_simulation'))

            # Supprimer un paterne
            if action == 'supprimer_paterne':
                base_donnees.supprimer_paterne(
                    entier_ou_defaut(request.form.get('id', '0'), 0)
                )
                flash('Paterne supprime.', 'succes')
                return redirect(url_for('page_simulation'))

            # Lancer la simulation
            if action == 'simuler':
                nb_tours = entier_ou_defaut(request.form.get('nb_tours', '8'), 8)  # Nombre de tours
                valeur_tour = reel_ou_defaut(request.form.get('valeur_tour', '1'), 1)  # Valeur d'un tour
                unite_tour = request.form.get('unite_tour', unite_tour)  # Unite choisie
                selection_objets = request.form.getlist('objets_observes')  # Objets coches
                objets_rapides = request.form.get('objets_rapides', '')  # Texte saisi manuellement

                # Ajoute les observations saisies manuellement
                # Ici on accepte :
                # - une observation par ligne
                # - ou plusieurs observations sur une ligne separees par ;
                # Exemple :
                # Petrole(prix ; stock) ; Gaz(prix ; stock)
                elements_rapides = []  # Contiendra toutes les observations rapides

                for ligne in objets_rapides.splitlines():  # Parcourt les lignes du textarea
                    texte = ligne.strip()  # Nettoie
                    if texte == '':
                        continue  # Ignore les lignes vides

                    for element in decouper_elements(texte, ';'):  # Decoupe au bon niveau sans casser les parentheses
                        observation = element.strip()  # Nettoie chaque observation
                        if observation != '':
                            elements_rapides.append(observation)  # Ajoute l'observation

                for nom in elements_rapides:  # Ajoute les observations rapides a la selection
                    if nom not in selection_objets:
                        selection_objets.append(nom)

                # Si rien n'est selectionne, on observe tous les objets sur "valeur"
                if not selection_objets:
                    for objet in objets:
                        selection_objets.append(objet['nom'] + '(valeur)')

                # Lance la simulation
                historique, courbes = simuler(
                    objets,
                    liaisons,
                    evenements,
                    paternes,
                    inversions,
                    nb_tours,
                    selection_objets,
                    valeur_tour,
                    unite_tour,
                    unites
                )

                # Prepare le resultat a afficher
                resultat = {
                    'historique': historique,
                    'graphique': svg_graphique(courbes, unite_tour, 'valeur')
                }

        except Exception as e:
            flash(str(e), 'erreur')

    return render_template(
        'simulation.html',
        objets=objets,
        objets_catalogue=objets_catalogue,
        evenements=evenements,
        paternes=paternes,
        liaisons=liaisons,
        inversions=inversions,
        unites=unites,
        resultat=resultat,
        selection_objets=selection_objets,
        nb_tours=nb_tours,
        valeur_tour=valeur_tour,
        unite_tour=unite_tour
    )

# Route pour la page d'exécution de code frank_sql
@app.route('/code', methods=['GET', 'POST'])
def page_code():
    code = ''  # Code saisi par l'utilisateur
    bilan = []  # Bilan de l'exécution (liste des actions effectuées)
    code_colore = ''  # Version colorée du code pour l'affichage

    if request.method == 'POST':
        # Récupère le code frank_sql saisi dans le formulaire
        code = request.form.get('code_frank', '')
        # Récupère le nom de la table principale comme table par défaut
        nom_table = base_donnees.nom_table_principale()

        try:
            # Exécute le code frank_sql sur la base de données
            bilan = executer_code(code, base_donnees, nom_table)
            flash('Code execute.', 'succes')
        except Exception as exc:
            flash(str(exc), 'erreur')

        # Colore le code pour l'affichage avec coloration syntaxique
        code_colore = colorer_code(code)

    # Affiche la page avec le code, le bilan et la version colorée
    return render_template(
        'code.html',
        code=code,
        bilan=bilan,
        code_colore=code_colore
    )


# Route pour la page d'aide
@app.route('/help')
def page_help():
    return render_template('help.html')


# Route pour la page de carte (map) : positions d'objets et chemins/itinéraires
@app.route('/map', methods=['GET', 'POST'])
def page_map():
    # Récupère l'ID du chemin sélectionné (depuis GET ou POST)
    chemin_id = request.args.get('chemin_id', request.form.get('chemin_id', ''))

    if request.method == 'POST':
        try:
            action = request.form.get('action', 'enregistrer_position')

            # Enregistrer la position d'un objet sur la carte
            if action == 'enregistrer_position':
                base_donnees.enregistrer_position(
                    entier_ou_defaut(request.form.get('objet_id', '0'), 0),  # ID de l'objet
                    reel_ou_defaut(request.form.get('latitude', '0'), 0),  # Latitude (coordonnée y)
                    reel_ou_defaut(request.form.get('longitude', '0'), 0),  # Longitude (coordonnée x)
                    request.form.get('lieu', '')  # Nom du lieu (optionnel)
                )
                flash('Position enregistree.', 'succes')

            # Supprimer une position
            elif action == 'supprimer_position':
                base_donnees.supprimer_position(
                    entier_ou_defaut(request.form.get('id_position', '0'), 0)
                )
                flash('Position supprimee.', 'succes')

            # Supprimer un chemin
            elif action == 'supprimer_chemin':
                base_donnees.supprimer_chemin(
                    entier_ou_defaut(request.form.get('id_chemin', '0'), 0)
                )
                flash('Chemin supprime.', 'succes')
                chemin_id = ''  # Réinitialise le chemin sélectionné

        except Exception as exc:
            flash(str(exc), 'erreur')

        # Redirige vers la page map avec le chemin sélectionné
        return redirect(url_for('page_map', chemin_id=chemin_id))

    # Charge les données pour l'affichage de la carte
    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())  # Tous les objets
    positions = vers_dicts(base_donnees.liste_positions())  # Toutes les positions enregistrées
    chemins = vers_dicts(base_donnees.liste_chemins())  # Tous les chemins/itinéraires
    points = []  # Liste des points formatés pour l'affichage sur la carte

    # Convertit chaque position en un point avec coordonnées x, y pour la carte
    for ligne in positions:
        x = float(ligne['longitude'])  # Coordonnée x (longitude)
        y = float(ligne['latitude'])  # Coordonnée y (latitude)
        points.append({
            'nom': ligne['nom'],
            'x': x,
            'y': y,
            'lieu': ligne['lieu']
        })

    chemin_selectionne = None  # ID du chemin actuellement sélectionné
    points_chemin = []  # Points du chemin sélectionné

    # Si un chemin est sélectionné, charge ses points
    if chemin_id:
        points_chemin = vers_dicts(
            base_donnees.points_chemin(entier_ou_defaut(chemin_id, 0))
        )
        if points_chemin:
            chemin_selectionne = entier_ou_defaut(chemin_id, 0)

    # Affiche la page de la carte avec toutes les données
    return render_template(
        'map.html',
        objets_catalogue=objets_catalogue,
        positions=positions,
        points=points,
        chemins=chemins,
        chemin_selectionne=chemin_selectionne,
        points_chemin=points_chemin
    )


# Point d'entrée : lance le serveur Flask en mode debug si le fichier est exécuté directement
if __name__ == '__main__':
    app.run(debug=True)