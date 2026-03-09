from __future__ import annotations

import os

from flask import Flask, flash, redirect, render_template, request, url_for

import base_donnees
from analyse_liaisons import parser_expression
from conversions import convertir, dictionnaire_unites
from graphe import (
    composantes_connexes_orientees_simple,
    construire_graphe,
    matrice_adjacence,
    parcours_bfs,
    parcours_dfs,
    svg_graphe,
    trouver_chemin,
)
from outils_nsi import entier_ou_defaut, nom_objet_valide, poids_valide, reel_ou_defaut
from simulation import simuler, svg_graphique

app = Flask(__name__)
app.secret_key = "projet-nsi-v10"
base_donnees.creer_tables()


@app.context_processor
def contexte_global():
    return {"nom_app": "Projet NSI V10"}


def charger_donnees():
    objets = base_donnees.liste_objets()
    liaisons = base_donnees.liste_liaisons()
    inversions = base_donnees.liste_inversions()
    unites = base_donnees.liste_unites()
    evenements = base_donnees.liste_evenements()
    paternes = base_donnees.liste_paternes()
    graphe, poids_aretes = construire_graphe(objets, liaisons)
    return objets, liaisons, inversions, unites, evenements, paternes, graphe, poids_aretes


@app.route("/")
def accueil():
    return redirect(url_for("page_donnees"))


@app.route("/donnees")
def page_donnees():
    objets, liaisons, inversions, unites, evenements, paternes, graphe, poids_aretes = charger_donnees()
    return render_template(
        "donnees.html",
        objets=objets,
        inversions=inversions,
        unites=unites,
        evenements=evenements,
        paternes=paternes,
    )


@app.route("/objets/ajouter", methods=["POST"])
def ajouter_objet():
    nom = request.form.get("nom", "").strip()
    valeur = reel_ou_defaut(request.form.get("valeur", "0"), 0)
    etat = request.form.get("etat", "").strip()

    if not nom_objet_valide(nom):
        flash("Nom d'objet invalide. Exemple valide : A, B2, Objet_1.", "erreur")
        return redirect(url_for("page_donnees"))

    try:
        base_donnees.ajouter_objet(nom, valeur, etat)
        flash("Objet ajoute.", "succes")
    except Exception as exc:
        flash(f"Ajout impossible : {exc}", "erreur")
    return redirect(url_for("page_donnees"))


@app.route("/objets/ajout_rapide", methods=["POST"])
def ajout_rapide_objets():
    texte = request.form.get("bloc_objets", "")
    nb_ajoutes = 0
    for ligne in texte.splitlines():
        propre = ligne.strip()
        if not propre:
            continue
        if "=" in propre:
            gauche, droite = propre.split("=", 1)
            nom = gauche.strip()
            valeur = reel_ou_defaut(droite.strip(), 0)
            etat = ""
        else:
            nom = propre
            valeur = 0
            etat = ""
        if not nom_objet_valide(nom):
            continue
        try:
            base_donnees.ajouter_objet(nom, valeur, etat)
            nb_ajoutes += 1
        except Exception:
            pass
    flash(f"Ajout rapide termine : {nb_ajoutes} objet(s) ajoute(s).", "succes")
    return redirect(url_for("page_donnees"))


@app.route("/objets/<int:objet_id>/modifier", methods=["POST"])
def modifier_objet(objet_id):
    nom = request.form.get("nom", "").strip()
    valeur = reel_ou_defaut(request.form.get("valeur", "0"), 0)
    etat = request.form.get("etat", "").strip()
    if not nom_objet_valide(nom):
        flash("Nom d'objet invalide.", "erreur")
        return redirect(url_for("page_donnees"))
    try:
        base_donnees.modifier_objet(objet_id, nom, valeur, etat)
        flash("Objet modifie.", "succes")
    except Exception as exc:
        flash(f"Modification impossible : {exc}", "erreur")
    return redirect(url_for("page_donnees"))


@app.route("/objets/<int:objet_id>/supprimer", methods=["POST"])
def supprimer_objet(objet_id):
    base_donnees.supprimer_objet(objet_id)
    flash("Objet supprime.", "succes")
    return redirect(url_for("page_donnees"))


@app.route("/inversions/ajouter", methods=["POST"])
def ajouter_inversion():
    valeur_0 = request.form.get("valeur_0", "").strip()
    valeur_1 = request.form.get("valeur_1", "").strip()
    if valeur_0 and valeur_1:
        base_donnees.ajouter_inversion(valeur_0, valeur_1)
        flash("Ligne d'inversion ajoutee.", "succes")
    return redirect(url_for("page_donnees"))


@app.route("/inversions/<int:inversion_id>/supprimer", methods=["POST"])
def supprimer_inversion(inversion_id):
    base_donnees.supprimer_inversion(inversion_id)
    flash("Ligne d'inversion supprimee.", "succes")
    return redirect(url_for("page_donnees"))


@app.route("/unites/ajouter", methods=["POST"])
def ajouter_unite():
    unite = request.form.get("unite", "").strip()
    unite_du_dessous = request.form.get("unite_du_dessous", "").strip() or None
    facteur = reel_ou_defaut(request.form.get("facteur", "1"), 1)
    rang = entier_ou_defaut(request.form.get("rang", "1"), 1)
    if unite:
        try:
            base_donnees.ajouter_unite(unite, unite_du_dessous, facteur, rang)
            flash("Unite ajoutee dans l'echelle.", "succes")
        except Exception as exc:
            flash(f"Ajout unite impossible : {exc}", "erreur")
    return redirect(url_for("page_donnees"))


@app.route("/unites/<int:unite_id>/supprimer", methods=["POST"])
def supprimer_unite(unite_id):
    base_donnees.supprimer_unite(unite_id)
    flash("Unite supprimee.", "succes")
    return redirect(url_for("page_donnees"))


@app.route("/graphe")
def page_graphe():
    objets, liaisons, inversions, unites, evenements, paternes, graphe, poids_aretes = charger_donnees()
    depart = request.args.get("depart", "")
    arrivee = request.args.get("arrivee", "")
    bfs = parcours_bfs(graphe, depart) if depart else []
    dfs = parcours_dfs(graphe, depart) if depart else []
    chemin = trouver_chemin(graphe, depart, arrivee) if depart and arrivee else []
    composantes = composantes_connexes_orientees_simple(graphe)
    noms, matrice = matrice_adjacence(objets, graphe)
    dessin = svg_graphe(objets, graphe, poids_aretes)
    return render_template(
        "graphe.html",
        objets=objets,
        liaisons=liaisons,
        graphe=graphe,
        composantes=composantes,
        noms=noms,
        matrice=matrice,
        dessin=dessin,
        depart=depart,
        arrivee=arrivee,
        bfs=bfs,
        dfs=dfs,
        chemin=chemin,
    )


@app.route("/liaisons/ajouter", methods=["POST"])
def ajouter_liaison():
    source_id = entier_ou_defaut(request.form.get("source_id", "0"), 0)
    cible_id = entier_ou_defaut(request.form.get("cible_id", "0"), 0)
    type_liaison = request.form.get("type_liaison", "=>").strip()
    poids = reel_ou_defaut(request.form.get("poids", "1"), 1)

    if source_id == cible_id:
        flash("Une liaison doit relier deux objets differents.", "erreur")
        return redirect(url_for("page_graphe"))
    if not poids_valide(poids):
        flash("Le poids doit etre positif ou nul.", "erreur")
        return redirect(url_for("page_graphe"))
    base_donnees.ajouter_liaison(source_id, cible_id, type_liaison, poids)
    flash("Liaison ajoutee.", "succes")
    return redirect(url_for("page_graphe"))


@app.route("/liaisons/rapides", methods=["POST"])
def liaisons_rapides():
    expression = request.form.get("expression_liaisons", "")
    poids = reel_ou_defaut(request.form.get("poids_rapide", "1"), 1)
    objets = base_donnees.liste_objets()
    noms_vers_ids = {obj["nom"]: obj["id"] for obj in objets}
    triplets = parser_expression(expression)
    ajouts = 0
    for source, type_liaison, cible in triplets:
        if source in noms_vers_ids and cible in noms_vers_ids and source != cible:
            base_donnees.ajouter_liaison(noms_vers_ids[source], noms_vers_ids[cible], type_liaison, poids)
            ajouts += 1
    flash(f"Ajout rapide termine : {ajouts} liaison(s) ajoutee(s).", "succes")
    return redirect(url_for("page_graphe"))


@app.route("/liaisons/<int:liaison_id>/supprimer", methods=["POST"])
def supprimer_liaison(liaison_id):
    base_donnees.supprimer_liaison(liaison_id)
    flash("Liaison supprimee.", "succes")
    return redirect(url_for("page_graphe"))


@app.route("/simulation", methods=["GET", "POST"])
def page_simulation():
    objets, liaisons, inversions, unites, evenements, paternes, graphe, poids_aretes = charger_donnees()

    resultat = None
    journal_visible = True
    graphique_visible = True
    selection_objets = []
    conversion_resultat = None

    if request.method == "POST":
        action = request.form.get("action", "simuler")

        if action == "ajouter_evenement":
            try:
                base_donnees.ajouter_evenement(
                    request.form.get("nom", ""),
                    entier_ou_defaut(request.form.get("objet_cause_id", "0"), 0),
                    request.form.get("type_cause", "valeur_num"),
                    request.form.get("operateur", "="),
                    request.form.get("valeur_cause", "0"),
                    reel_ou_defaut(request.form.get("poids", "1"), 1),
                    entier_ou_defaut(request.form.get("arrivee_tour", "0"), 0),
                    entier_ou_defaut(request.form.get("objet_effet_id", "0"), 0),
                    request.form.get("type_effet", "operation"),
                    request.form.get("valeur_effet", "+1"),
                    1 if request.form.get("propagation_active") == "on" else 0,
                    entier_ou_defaut(request.form.get("propagation_profondeur", "1"), 1),
                )
                flash("Evenement ajoute.", "succes")
            except Exception as exc:
                flash(f"Ajout evenement impossible : {exc}", "erreur")
            return redirect(url_for("page_simulation"))

        if action == "ajouter_paterne":
            try:
                base_donnees.ajouter_paterne(
                    request.form.get("nom", ""),
                    entier_ou_defaut(request.form.get("objet_effet_id", "0"), 0),
                    request.form.get("type_effet", "operation"),
                    request.form.get("valeur_effet", "+1"),
                    reel_ou_defaut(request.form.get("frequence_valeur", "1"), 1),
                    request.form.get("frequence_unite", "min"),
                )
                flash("Paterne ajoute.", "succes")
            except Exception as exc:
                flash(f"Ajout paterne impossible : {exc}", "erreur")
            return redirect(url_for("page_simulation"))

        if action == "supprimer_evenement":
            base_donnees.supprimer_evenement(entier_ou_defaut(request.form.get("evenement_id", "0"), 0))
            flash("Evenement supprime.", "succes")
            return redirect(url_for("page_simulation"))

        if action == "supprimer_paterne":
            base_donnees.supprimer_paterne(entier_ou_defaut(request.form.get("paterne_id", "0"), 0))
            flash("Paterne supprime.", "succes")
            return redirect(url_for("page_simulation"))

        if action == "verifier_conversion":
            valeur = reel_ou_defaut(request.form.get("conversion_valeur", "1"), 1)
            unite_depart = request.form.get("conversion_depart", "")
            unite_arrivee = request.form.get("conversion_arrivee", "")
            conversion_resultat = convertir(dictionnaire_unites(unites), valeur, unite_depart, unite_arrivee)

        if action == "simuler":
            nb_tours = entier_ou_defaut(request.form.get("nb_tours", "10"), 10)
            valeur_tour = reel_ou_defaut(request.form.get("valeur_tour", "1"), 1)
            unite_tour = request.form.get("unite_tour", "min")
            selection_objets = request.form.getlist("objets_observes")
            journal_visible = request.form.get("voir_journal") == "on"
            graphique_visible = request.form.get("voir_graphique") == "on"
            historique, courbes = simuler(
                objets,
                liaisons,
                evenements,
                paternes,
                inversions,
                unites,
                graphe,
                poids_aretes,
                nb_tours,
                valeur_tour,
                unite_tour,
                selection_objets,
            )
            graphique = svg_graphique(courbes, unite_tour) if graphique_visible else ""
            resultat = {
                "historique": historique,
                "graphique": graphique,
                "selection_objets": selection_objets,
            }

    return render_template(
        "simulation.html",
        objets=objets,
        unites=unites,
        evenements=evenements,
        paternes=paternes,
        resultat=resultat,
        selection_objets=selection_objets,
        journal_visible=journal_visible,
        graphique_visible=graphique_visible,
        conversion_resultat=conversion_resultat,
    )


if __name__ == "__main__":
    print("FICHIER LANCE =", __file__)
    print("DOSSIER COURANT =", os.getcwd())
    app.run(debug=True, use_reloader=False)
