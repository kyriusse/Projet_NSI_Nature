from __future__ import annotations

# Three - application principale
# Cette application Flask sert uniquement d'interface.
# Le coeur du projet reste en Python et SQLite.

from flask import Flask, flash, redirect, render_template, request, session, url_for

import base_donnees
from conversions import convertir
from composants_utils import arbre_html
from frank_sql import colorer_code, executer_code
from graphe import construire_graphe, svg_graphe
from outils_nsi import entier_ou_defaut, nom_simple_valide, proba_valide, reel_ou_defaut
from simulation import simuler, svg_graphique

app = Flask(__name__)
app.secret_key = 'three-nsi-2026'


def initialiser_univers():
    univers = session.get('univers', 'univers_1')
    base_donnees.choisir_univers(univers)


@app.before_request
def avant_requete():
    initialiser_univers()


@app.context_processor
def contexte_global():
    return {'nom_app': 'Three', 'univers_actuel': session.get('univers', 'univers_1')}


def table_courante():
    return request.args.get('table', request.form.get('table', base_donnees.nom_table_principale()))


def vers_dicts(lignes):
    return [dict(ligne) for ligne in lignes]


def charger_graphe():
    objets_catalogue = base_donnees.liste_objets_catalogue()
    liaisons = base_donnees.liste_liaisons()
    return construire_graphe(objets_catalogue, liaisons)


def ajouter_liaisons_rapides(texte):
    compteur = 0
    for ligne in [x.strip() for x in texte.splitlines() if x.strip()]:
        type_liaison = '<=>'
        if '<=>' in ligne:
            morceaux = ligne.split('<=>')
            type_liaison = '<=>'
        elif '=>' in ligne:
            morceaux = ligne.split('=>')
            type_liaison = '=>'
        else:
            continue
        if len(morceaux) != 2:
            continue
        source = morceaux[0].strip()
        cible = morceaux[1].strip()
        if source == '' or cible == '':
            continue
        base_donnees.ajouter_liaison(source, cible, type_liaison, 1, 'n')
        compteur += 1
    return compteur


@app.route('/')
def index():
    return render_template('index.html', univers=base_donnees.liste_univers())


@app.route('/ouvrir/<nom_univers>')
def ouvrir_univers(nom_univers):
    session['univers'] = nom_univers
    base_donnees.choisir_univers(nom_univers)
    return redirect(url_for('page_donnees'))


@app.route('/reinitialiser/<nom_univers>', methods=['POST'])
def reinitialiser_univers(nom_univers):
    session['univers'] = nom_univers
    base_donnees.choisir_univers(nom_univers)
    base_donnees.reinitialiser_univers()
    flash('Univers reinitialise.', 'succes')
    return redirect(url_for('index'))


@app.route('/donnees', methods=['GET', 'POST'])
def page_donnees():
    nom_table = table_courante()
    if request.method == 'POST':
        action = request.form.get('action', '')
        try:
            if action == 'creer_table':
                nom_table_nouvelle = request.form.get('nom_table_nouvelle', '').strip().replace(' ', '_')
                if not nom_simple_valide(nom_table_nouvelle.replace('_', 'a')):
                    raise ValueError('Nom de table invalide')
                base_donnees.creer_table_nsi(nom_table_nouvelle, 0, [])
                nom_table = nom_table_nouvelle
                flash('Table creee.', 'succes')

            elif action == 'ajouter_colonne':
                base_donnees.ajouter_colonne_table(
                    nom_table,
                    request.form.get('nom_colonne', '').strip().replace(' ', '_'),
                    request.form.get('type_colonne', 'texte'),
                    request.form.get('valeur_defaut', '')
                )
                flash('Colonne ajoutee.', 'succes')

            elif action == 'supprimer_colonne':
                base_donnees.supprimer_colonne_table(
                    nom_table,
                    request.form.get('nom_colonne', '').strip()
                )
                flash('Colonne supprimee.', 'succes')

            elif action == 'ajouter_objet':
                donnees = {
                    'nom': request.form.get('nom', '').strip(),
                    'valeur': reel_ou_defaut(request.form.get('valeur', '0'), 0),
                    'etat': request.form.get('etat', '').strip()
                }

                for ligne in base_donnees.liste_colonnes_table(nom_table):
                    donnees[ligne['nom_colonne']] = request.form.get(
                        ligne['nom_colonne'],
                        ligne['valeur_defaut']
                    )

                base_donnees.ajouter_objet_table(nom_table, donnees)
                flash('Objet ajoute.', 'succes')

            elif action == 'ajout_rapide':
                from frank_sql import ajouter_liaisons_texte, ajouter_objet_rapide, decouper_elements

                bloc = request.form.get('bloc_objets', '')
                bilan_liaisons = 0
                elements = []

                for ligne in bloc.splitlines():
                    ligne = ligne.strip()
                    if ligne == '':
                        continue
                    elements.extend(decouper_elements(ligne, ';'))

                for ligne in [x.strip() for x in elements if x.strip()]:
                    if '=>' in ligne or '<=>' in ligne:
                        bilan_liaisons += ajouter_liaisons_texte(ligne, base_donnees, nom_table)
                        continue
                    ajouter_objet_rapide(ligne, nom_table, base_donnees)

                if bilan_liaisons > 0:
                    flash(
                        'Ajout rapide termine : objets et ' + str(bilan_liaisons) + ' liaison(s).',
                        'succes'
                    )
                else:
                    flash('Ajout rapide termine.', 'succes')

            elif action == 'ajouter_unite':
                base_donnees.ajouter_unite(
                    request.form.get('nom_unite', '').strip(),
                    request.form.get('unite_dessous', '').strip(),
                    reel_ou_defaut(request.form.get('facteur', '0'), 0)
                )
                flash('Unite ajoutee.', 'succes')

            elif action == 'ajouter_inversion':
                base_donnees.ajouter_inversion(
                    request.form.get('valeur_0', ''),
                    request.form.get('valeur_1', '')
                )
                flash('Inversion ajoutee.', 'succes')

            elif action == 'supprimer_objet':
                base_donnees.supprimer_objet_par_nom(request.form.get('nom_objet', '').strip())
                flash('Objet supprime.', 'succes')

            elif action == 'supprimer_table':
                base_donnees.supprimer_table_nsi(request.form.get('nom_table', '').strip())
                nom_table = base_donnees.nom_table_principale()
                flash('Table supprimee.', 'succes')

            elif action == 'supprimer_inversion':
                base_donnees.supprimer_inversion(
                    entier_ou_defaut(request.form.get('id_inversion', '0'), 0)
                )
                flash('Inversion supprimee.', 'succes')

        except Exception as exc:
            flash(str(exc), 'erreur')

        return redirect(url_for('page_donnees', table=nom_table))

    tables = vers_dicts(base_donnees.liste_tables_nsi())
    objets = vers_dicts(base_donnees.liste_objets(nom_table))
    colonnes = vers_dicts(base_donnees.liste_colonnes_table(nom_table))
    colonnes_physiques = list(base_donnees.colonnes_physiques(nom_table))
    unites = vers_dicts(base_donnees.liste_unites())
    inversions = vers_dicts(base_donnees.liste_inversions())

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


@app.route('/liaisons', methods=['GET', 'POST'])
def page_liaisons():
    if request.method == 'POST':
        action = request.form.get('action', 'ajouter')
        try:
            if action == 'ajout_rapide':
                compteur = ajouter_liaisons_rapides(request.form.get('bloc_liaisons', ''))
                flash(str(compteur) + ' liaison(s) ajoutee(s).', 'succes')

            elif action == 'supprimer_liaison':
                base_donnees.supprimer_liaison(
                    entier_ou_defaut(request.form.get('id_liaison', '0'), 0)
                )
                flash('Liaison supprimee.', 'succes')

            else:
                base_donnees.ajouter_liaison(
                    request.form.get('source_nom', ''),
                    request.form.get('cible_nom', ''),
                    request.form.get('type_liaison', '=>'),
                    reel_ou_defaut(request.form.get('poids', '1'), 1),
                    request.form.get('conservation', 'n')
                )
                flash('Liaison ajoutee.', 'succes')

        except Exception as exc:
            flash(str(exc), 'erreur')

        return redirect(url_for('page_liaisons'))

    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())
    liaisons = vers_dicts(base_donnees.liste_liaisons())
    graphe, poids, _ = charger_graphe()

    return render_template(
        'liaisons.html',
        objets_catalogue=objets_catalogue,
        liaisons=liaisons,
        svg=svg_graphe(objets_catalogue, graphe, poids)
    )


@app.route('/composants', methods=['GET', 'POST'])
def page_composants():
    if request.method == 'POST':
        action = request.form.get('action', '')
        try:
            if action == 'ajouter_composant':
                base_donnees.ajouter_composition(
                    request.form.get('parent_nom', ''),
                    request.form.get('enfant_nom', ''),
                    entier_ou_defaut(request.form.get('quantite', '1'), 1)
                )
                try:
                    base_donnees.ajouter_liaison(
                        request.form.get('enfant_nom', ''),
                        request.form.get('parent_nom', ''),
                        '=>',
                        1,
                        'n'
                    )
                except Exception:
                    pass
                flash('Composition ajoutee.', 'succes')

            elif action == 'ajout_rapide_cp':
                parent = request.form.get('parent_rapide', '').strip()
                bloc = request.form.get('bloc_cp', '')
                morceaux = [m.strip() for m in bloc.split(';') if m.strip()]

                for morceau in morceaux:
                    quantite = 1
                    enfant = morceau

                    if '(' in morceau and morceau.endswith(')'):
                        enfant = morceau.split('(', 1)[0].strip()
                        quantite = entier_ou_defaut(
                            morceau[morceau.find('(') + 1:-1],
                            1
                        )

                    base_donnees.ajouter_composition(parent, enfant, quantite)

                    try:
                        base_donnees.ajouter_liaison(enfant, parent, '=>', 1, 'n')
                    except Exception:
                        pass

                flash('Ajout rapide des composants termine.', 'succes')

            elif action == 'supprimer_composition':
                base_donnees.supprimer_composition(
                    entier_ou_defaut(request.form.get('id_composition', '0'), 0)
                )
                flash('Composition supprimee.', 'succes')

            elif action == 'fusion':
                nom_resultat = request.form.get('nom_resultat', '').strip()
                table = base_donnees.nom_table_principale()

                if base_donnees.objet_global_par_nom(nom_resultat) is None:
                    base_donnees.ajouter_objet_table(
                        table,
                        {'nom': nom_resultat, 'valeur': 0, 'etat': ''}
                    )

                texte_fusion = request.form.get('fusion', '')

                for morceau in [m.strip() for m in texte_fusion.split('+') if m.strip()]:
                    quantite = 1
                    nom = morceau

                    if len(morceau) > 1 and morceau[0].isdigit():
                        prefixe = ''
                        for caractere in morceau:
                            if caractere.isdigit():
                                prefixe += caractere
                            else:
                                break
                        quantite = entier_ou_defaut(prefixe, 1)
                        nom = morceau[len(prefixe):].strip()

                    if base_donnees.objet_global_par_nom(nom) is not None:
                        base_donnees.ajouter_composition(nom_resultat, nom, quantite)

                flash('Fusion enregistree.', 'succes')

        except Exception as exc:
            flash(str(exc), 'erreur')

        return redirect(url_for('page_composants'))

    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())
    compositions = vers_dicts(base_donnees.liste_compositions())
    racine = request.args.get('racine', objets_catalogue[0]['nom'] if objets_catalogue else '')
    max_branches = entier_ou_defaut(request.args.get('max_branches', '6'), 6)
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
    objets = vers_dicts(base_donnees.liste_objets_simulation())
    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())
    evenements = vers_dicts(base_donnees.liste_evenements())
    paternes = vers_dicts(base_donnees.liste_paternes())
    liaisons = vers_dicts(base_donnees.liste_liaisons())
    inversions = vers_dicts(base_donnees.liste_inversions())
    unites = vers_dicts(base_donnees.liste_unites())

    resultat = None
    selection_objets = []
    nb_tours = 8
    valeur_tour = 1
    unite_tour = unites[0]['nom'] if unites else ''

    if request.method == 'POST':
        action = request.form.get('action', 'simuler')

        try:
            if action == 'ajouter_evenement':
                proba = reel_ou_defaut(request.form.get('proba', '1'), 1)

                if not proba_valide(proba):
                    raise ValueError('La probabilite doit etre entre 0 et 1')

                propagation_texte = request.form.get('propagation', '0').strip().lower()
                propagation = -1 if propagation_texte == 'all' else entier_ou_defaut(propagation_texte, 0)

                base_donnees.ajouter_evenement(
                    request.form.get('nom', ''),
                    entier_ou_defaut(request.form.get('objet_cause_id', '0'), 0),
                    request.form.get('colonne_cause', 'valeur'),
                    request.form.get('operateur', '='),
                    request.form.get('valeur_cause', '0'),
                    entier_ou_defaut(request.form.get('objet_effet_id', '0'), 0),
                    request.form.get('colonne_effet', 'valeur'),
                    request.form.get('action_effet', 'op'),
                    request.form.get('valeur_effet', '+1'),
                    proba,
                    entier_ou_defaut(request.form.get('arrivee', '0'), 0),
                    propagation
                )

                flash('Evenement ajoute.', 'succes')
                return redirect(url_for('page_simulation'))

            if action == 'ajouter_paterne':
                base_donnees.ajouter_paterne(
                    request.form.get('nom', ''),
                    entier_ou_defaut(request.form.get('objet_effet_id', '0'), 0),
                    request.form.get('colonne_effet', 'valeur'),
                    request.form.get('action_effet', 'op'),
                    request.form.get('valeur_effet', '+1'),
                    entier_ou_defaut(request.form.get('frequence', '1'), 1)
                )

                flash('Paterne ajoute.', 'succes')
                return redirect(url_for('page_simulation'))

            if action == 'changer_etat_evenement':
                base_donnees.changer_etat_evenement(
                    entier_ou_defaut(request.form.get('id', '0'), 0),
                    entier_ou_defaut(request.form.get('actif', '1'), 1)
                )
                return redirect(url_for('page_simulation'))

            if action == 'supprimer_evenement':
                base_donnees.supprimer_evenement(
                    entier_ou_defaut(request.form.get('id', '0'), 0)
                )
                flash('Evenement supprime.', 'succes')
                return redirect(url_for('page_simulation'))

            if action == 'changer_etat_paterne':
                base_donnees.changer_etat_paterne(
                    entier_ou_defaut(request.form.get('id', '0'), 0),
                    entier_ou_defaut(request.form.get('actif', '1'), 1)
                )
                return redirect(url_for('page_simulation'))

            if action == 'supprimer_paterne':
                base_donnees.supprimer_paterne(
                    entier_ou_defaut(request.form.get('id', '0'), 0)
                )
                flash('Paterne supprime.', 'succes')
                return redirect(url_for('page_simulation'))

            if action == 'simuler':
                nb_tours = entier_ou_defaut(request.form.get('nb_tours', '8'), 8)
                valeur_tour = reel_ou_defaut(request.form.get('valeur_tour', '1'), 1)
                unite_tour = request.form.get('unite_tour', unite_tour)
                selection_objets = request.form.getlist('objets_observes')
                objets_rapides = request.form.get('objets_rapides', '')

                for nom in [x.strip() for x in objets_rapides.splitlines() if x.strip()]:
                    if nom not in selection_objets:
                        selection_objets.append(nom)

                if not selection_objets:
                    for objet in objets:
                        selection_objets.append(objet['nom'] + '(valeur)')

                historique, courbes = simuler(
                    objets,
                    liaisons,
                    evenements,
                    paternes,
                    inversions,
                    nb_tours,
                    selection_objets,
                    valeur_tour,
                    unite_tour
                )

                resultat = {
                    'historique': historique,
                    'graphique': svg_graphique(courbes, unite_tour, 'valeur')
                }

        except Exception as exc:
            flash(str(exc), 'erreur')

    return render_template(
        'simulation.html',
        objets=objets,
        objets_catalogue=objets_catalogue,
        evenements=evenements,
        paternes=paternes,
        unites=unites,
        resultat=resultat,
        selection_objets=selection_objets,
        nb_tours=nb_tours,
        valeur_tour=valeur_tour,
        unite_tour=unite_tour
    )


@app.route('/code', methods=['GET', 'POST'])
def page_code():
    code = ''
    bilan = []
    code_colore = ''

    if request.method == 'POST':
        code = request.form.get('code_frank', '')
        nom_table = base_donnees.nom_table_principale()

        try:
            bilan = executer_code(code, base_donnees, nom_table)
            flash('Code execute.', 'succes')
        except Exception as exc:
            flash(str(exc), 'erreur')

        code_colore = colorer_code(code)

    return render_template(
        'code.html',
        code=code,
        bilan=bilan,
        code_colore=code_colore
    )


@app.route('/help')
def page_help():
    return render_template('help.html')


@app.route('/map', methods=['GET', 'POST'])
def page_map():
    chemin_id = request.args.get('chemin_id', request.form.get('chemin_id', ''))

    if request.method == 'POST':
        try:
            action = request.form.get('action', 'enregistrer_position')

            if action == 'enregistrer_position':
                base_donnees.enregistrer_position(
                    entier_ou_defaut(request.form.get('objet_id', '0'), 0),
                    reel_ou_defaut(request.form.get('latitude', '0'), 0),
                    reel_ou_defaut(request.form.get('longitude', '0'), 0),
                    request.form.get('lieu', '')
                )
                flash('Position enregistree.', 'succes')

            elif action == 'supprimer_position':
                base_donnees.supprimer_position(
                    entier_ou_defaut(request.form.get('id_position', '0'), 0)
                )
                flash('Position supprimee.', 'succes')

            elif action == 'supprimer_chemin':
                base_donnees.supprimer_chemin(
                    entier_ou_defaut(request.form.get('id_chemin', '0'), 0)
                )
                flash('Chemin supprime.', 'succes')
                chemin_id = ''

        except Exception as exc:
            flash(str(exc), 'erreur')

        return redirect(url_for('page_map', chemin_id=chemin_id))

    objets_catalogue = vers_dicts(base_donnees.liste_objets_catalogue())
    positions = vers_dicts(base_donnees.liste_positions())
    chemins = vers_dicts(base_donnees.liste_chemins())
    points = []

    for ligne in positions:
        x = float(ligne['longitude'])
        y = float(ligne['latitude'])
        points.append({
            'nom': ligne['nom'],
            'x': x,
            'y': y,
            'lieu': ligne['lieu']
        })

    chemin_selectionne = None
    points_chemin = []

    if chemin_id:
        points_chemin = vers_dicts(
            base_donnees.points_chemin(entier_ou_defaut(chemin_id, 0))
        )
        if points_chemin:
            chemin_selectionne = entier_ou_defaut(chemin_id, 0)

    return render_template(
        'map.html',
        objets_catalogue=objets_catalogue,
        positions=positions,
        points=points,
        chemins=chemins,
        chemin_selectionne=chemin_selectionne,
        points_chemin=points_chemin
    )


@app.route('/graphe')
def page_graphe():
    return redirect(url_for('page_liaisons'))


if __name__ == '__main__':
    app.run(debug=True)