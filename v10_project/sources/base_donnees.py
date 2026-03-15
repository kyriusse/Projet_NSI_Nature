"""
Module SQLite du projet.

Le code reste simple pour etre relu facilement.
On utilise des fonctions courtes et un chemin fixe vers la base.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Iterable

DOSSIER_COURANT = os.path.dirname(os.path.abspath(__file__))
CHEMIN_BDD = os.path.join(DOSSIER_COURANT, "data", "simulation_nsi_v10.db")


def connexion() -> sqlite3.Connection:
    """Ouvre une connexion SQLite avec quelques protections utiles."""
    con = sqlite3.connect(CHEMIN_BDD, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def executer(requete: str, parametres: Iterable = ()) -> None:
    with connexion() as con:
        con.execute(requete, tuple(parametres))
        con.commit()


def executer_plusieurs(requete: str, lignes: list[tuple]) -> None:
    with connexion() as con:
        con.executemany(requete, lignes)
        con.commit()


def lire_tout(requete: str, parametres: Iterable = ()) -> list[sqlite3.Row]:
    with connexion() as con:
        cur = con.execute(requete, tuple(parametres))
        return cur.fetchall()


def lire_un(requete: str, parametres: Iterable = ()) -> sqlite3.Row | None:
    with connexion() as con:
        cur = con.execute(requete, tuple(parametres))
        return cur.fetchone()


def creer_tables() -> None:
    os.makedirs(os.path.dirname(CHEMIN_BDD), exist_ok=True)

    executer(
        """
        CREATE TABLE IF NOT EXISTS objets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            valeur REAL DEFAULT 0,
            etat TEXT DEFAULT ''
        )
        """
    )
    
    executer(
        """
        CREATE TABLE IF NOT EXISTS colonnes_objets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_colonne TEXT NOT NULL UNIQUE,
            type_colonne TEXT NOT NULL,
            position_affichage INTEGER NOT NULL
        )
        """
    )
    
    executer(
        """
        CREATE TABLE IF NOT EXISTS liaisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            cible_id INTEGER NOT NULL,
            type_liaison TEXT NOT NULL,
            poids REAL NOT NULL DEFAULT 1,
            FOREIGN KEY(source_id) REFERENCES objets(id) ON DELETE CASCADE,
            FOREIGN KEY(cible_id) REFERENCES objets(id) ON DELETE CASCADE
        )
        """
    )

    executer(
        """
        CREATE TABLE IF NOT EXISTS inversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valeur_0 TEXT NOT NULL,
            valeur_1 TEXT NOT NULL
        )
        """
    )

    executer(
        """
        CREATE TABLE IF NOT EXISTS echelle_unites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unite TEXT NOT NULL UNIQUE,
            unite_du_dessous TEXT,
            facteur REAL,
            rang INTEGER NOT NULL
        )
        """
    )

    executer(
        """
        CREATE TABLE IF NOT EXISTS evenements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            objet_cause_id INTEGER NOT NULL,
            type_cause TEXT NOT NULL,
            operateur TEXT NOT NULL,
            valeur_cause TEXT NOT NULL,
            poids REAL NOT NULL DEFAULT 1,
            arrivee_tour INTEGER NOT NULL DEFAULT 0,
            objet_effet_id INTEGER NOT NULL,
            type_effet TEXT NOT NULL,
            valeur_effet TEXT NOT NULL,
            propagation_active INTEGER NOT NULL DEFAULT 1,
            propagation_profondeur INTEGER NOT NULL DEFAULT 1,
            actif INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(objet_cause_id) REFERENCES objets(id) ON DELETE CASCADE,
            FOREIGN KEY(objet_effet_id) REFERENCES objets(id) ON DELETE CASCADE
        )
        """
    )

    executer(
        """
        CREATE TABLE IF NOT EXISTS paternes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            objet_effet_id INTEGER NOT NULL,
            type_effet TEXT NOT NULL,
            valeur_effet TEXT NOT NULL,
            frequence_valeur REAL NOT NULL,
            frequence_unite TEXT NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(objet_effet_id) REFERENCES objets(id) ON DELETE CASCADE
        )
        """
    )

    inserer_unites_par_defaut()


def inserer_unites_par_defaut() -> None:
    lignes = lire_tout("SELECT COUNT(*) AS total FROM echelle_unites")
    if lignes and lignes[0]["total"] > 0:
        return

    donnees = [
        ("s", None, None, 1),
        ("min", "s", 60, 2),
        ("h", "min", 60, 3),
        ("J", "h", 24, 4),
        ("S", "J", 7, 5),
    ]
    executer_plusieurs(
        "INSERT INTO echelle_unites(unite, unite_du_dessous, facteur, rang) VALUES(?,?,?,?)",
        donnees,
    )

#-----------------
# Ici, on gère les colonnes
# Fonction : mettre les fonctions svp...
#---------------------------

def nom_colonne_valide(nom_colonne: str) -> bool:
    if not nom_colonne:
        return False
    premier = nom_colonne[0]
    if not (premier.isalpha() or premier == "_"):
        return False
    for caractere in nom_colonne:
        if not (caractere.isalnum() or caractere == "_"):
            return False
    noms_interdits = {
        "id",
        "nom",
        "etat",
        "valeur",
    }
    return nom_colonne not in noms_interdits

def definition_sql_pour_type(type_site: str) -> str:
    correspondances = {
        "int": "INTEGER DEFAULT 0",
        "float": "REAL DEFAULT 0",
        "texte": "TEXT DEFAULT ''",
    }
    return correspondances.get(type_site, "INTEGER DEFAULT 0")

def colonnes_objets_sql() -> list[str]:
    with connexion() as con:
        lignes = con.execute("PRAGMA table_info(objets)").fetchall()
        return [ligne["name"] for ligne in lignes]

def liste_colonnes_personnalisees() -> list[sqlite3.Row]:
    return lire_tout(
        """
        SELECT * FROM colonnes_objets
        ORDER BY position_affichage, nom_colonne
        """
    )

def prochaine_position_colonne() -> int:
    ligne = lire_un("SELECT COALESCE(MAX(position_affichage), 0) AS maxi FROM colonnes_objets")
    return int(ligne["maxi"]) + 1 if ligne else 1

def ajouter_colonne(nom_colonne: str, type_site: str = "int") -> None:
    if not nom_colonne_valide(nom_colonne):
        raise ValueError("Nom de colonne invalide.")

    if nom_colonne in colonnes_objets_sql():
        raise ValueError("Cette colonne existe deja.")

    definition_sql = definition_sql_pour_type(type_site)

    executer(f"ALTER TABLE objets ADD COLUMN {nom_colonne} {definition_sql}")

    executer(
        """
        INSERT INTO colonnes_objets(nom_colonne, type_colonne, position_affichage)
        VALUES(?,?,?)
        """,
        (nom_colonne, type_site, prochaine_position_colonne()),
    )

def renommer_colonne_table_objets(ancien_nom: str, nouveau_nom: str) -> None:
    executer(f"ALTER TABLE objets RENAME COLUMN {ancien_nom} TO {nouveau_nom}")

def modifier_colonne(ancien_nom: str, nouveau_nom: str) -> None:
    if not nom_colonne_valide(nouveau_nom):
        raise ValueError("Nouveau nom invalide.")

    if ancien_nom not in [ligne["nom_colonne"] for ligne in liste_colonnes_personnalisees()]:
        raise ValueError("Seules les colonnes personnalisees peuvent etre renommees.")

    if nouveau_nom in colonnes_objets_sql():
        raise ValueError("Ce nom existe deja.")

    renommer_colonne_table_objets(ancien_nom, nouveau_nom)

    executer(
        """
        UPDATE colonnes_objets
        SET nom_colonne = ?
        WHERE nom_colonne = ?
        """,
        (nouveau_nom, ancien_nom),
    )

#commande pour supprimer une colonne, pour s'assurer de bien respecté les contraintes SGBD, ici on recréer la BDD sans la colonne supprimées.
def supprimer_colonne(nom_colonne: str) -> None: 
    colonnes_personnalisees = [ligne["nom_colonne"] for ligne in liste_colonnes_personnalisees()]

    if nom_colonne not in colonnes_personnalisees:
        raise ValueError("Seules les colonnes personnalisees peuvent etre supprimees.")

    colonnes_a_garder = []
    for colonne in colonnes_objets_sql():
        if colonne != nom_colonne:
            colonnes_a_garder.append(colonne)

    definitions = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nom": "TEXT NOT NULL UNIQUE",
        "valeur": "REAL DEFAULT 0",
        "etat": "TEXT DEFAULT ''",
    }

    for ligne in liste_colonnes_personnalisees():
        nom = ligne["nom_colonne"]
        if nom == nom_colonne:
            continue
        definitions[nom] = definition_sql_pour_type(ligne["type_colonne"])

    morceaux_creation = []
    for colonne in colonnes_a_garder:
        morceaux_creation.append(f"{colonne} {definitions[colonne]}")

    requete_creation = "CREATE TABLE objets_nouvelle (" + ", ".join(morceaux_creation) + ")"
    morceaux_selection = ", ".join(colonnes_a_garder)

    with connexion() as con:
        con.execute("PRAGMA foreign_keys = OFF")
        con.execute("BEGIN")
        con.execute(requete_creation)
        con.execute(
            f"INSERT INTO objets_nouvelle ({morceaux_selection}) "
            f"SELECT {morceaux_selection} FROM objets"
        )
        con.execute("DROP TABLE objets")
        con.execute("ALTER TABLE objets_nouvelle RENAME TO objets")
        con.execute("PRAGMA foreign_keys = ON")
        con.commit()

    executer("DELETE FROM colonnes_objets WHERE nom_colonne = ?", (nom_colonne,))


def liste_objets() -> list[sqlite3.Row]:
    return lire_tout("SELECT * FROM objets ORDER BY nom")

def lire_objet_par_id(objet_id: int) -> sqlite3.Row | None:
    return lire_un("SELECT * FROM objets WHERE id = ?", (objet_id,))


def preparer_valeur(type_colonne, valeur):
    if type_colonne == "int":
        if valeur == "":
            return 0
        return int(float(valeur))

    if type_colonne == "float":
        if valeur == "":
            return 0
        return float(valeur)

    return valeur


def ajouter_objet(donnees_formulaire):
    colonnes = []
    valeurs = []

    colonnes.append("nom")
    valeurs.append(donnees_formulaire.get("nom", ""))

    colonnes_personnalisees = liste_colonnes_personnalisees()

    for colonne in colonnes_personnalisees:
        nom_colonne = colonne["nom_colonne"]
        type_colonne = colonne["type_colonne"]
        valeur = donnees_formulaire.get(nom_colonne, "")
        valeur = preparer_valeur(type_colonne, valeur)

        colonnes.append(nom_colonne)
        valeurs.append(valeur)

    colonnes.append("etat")
    valeurs.append(donnees_formulaire.get("etat", ""))

    colonnes.append("valeur")
    valeurs.append(donnees_formulaire.get("valeur", 0))

    texte_colonnes = ", ".join(colonnes)
    texte_questions = ", ".join(["?"] * len(valeurs))

    requete = "INSERT INTO objets (" + texte_colonnes + ") VALUES (" + texte_questions + ")"
    executer(requete, valeurs)

def modifier_objet(objet_id, donnees_formulaire):
    morceaux = []
    valeurs = []

    morceaux.append("nom = ?")
    valeurs.append(donnees_formulaire.get("nom", ""))
    colonnes_personnalisees = liste_colonnes_personnalisees()

    for colonne in colonnes_personnalisees:
        nom_colonne = colonne["nom_colonne"]
        type_colonne = colonne["type_colonne"]
        valeur = donnees_formulaire.get(nom_colonne, "")
        valeur = preparer_valeur(type_colonne, valeur)
        morceaux.append(nom_colonne + " = ?")
        valeurs.append(valeur)
        
    morceaux.append("etat = ?")
    valeurs.append(donnees_formulaire.get("etat", ""))
    morceaux.append("valeur = ?")
    valeurs.append(donnees_formulaire.get("valeur", 0))
    valeurs.append(objet_id)
    requete = "UPDATE objets SET " + ", ".join(morceaux) + " WHERE id = ?"
    executer(requete, valeurs)

def supprimer_objet(objet_id: int) -> None:
    executer("DELETE FROM objets WHERE id = ?", (objet_id,))

def liste_liaisons() -> list[sqlite3.Row]:
    return lire_tout(
        """
        SELECT l.id, s.nom AS source_nom, c.nom AS cible_nom,
               l.source_id, l.cible_id, l.type_liaison, l.poids
        FROM liaisons l
        JOIN objets s ON s.id = l.source_id
        JOIN objets c ON c.id = l.cible_id
        ORDER BY s.nom, c.nom
        """
    )

def ajouter_liaison(source_id: int, cible_id: int, type_liaison: str, poids: float) -> None:
    executer(
        "INSERT INTO liaisons(source_id, cible_id, type_liaison, poids) VALUES(?,?,?,?)",
        (source_id, cible_id, type_liaison, poids),
    )


def supprimer_liaison(liaison_id: int) -> None:
    executer("DELETE FROM liaisons WHERE id = ?", (liaison_id,))


def liste_inversions() -> list[sqlite3.Row]:
    return lire_tout("SELECT * FROM inversions ORDER BY valeur_0, valeur_1")


def ajouter_inversion(valeur_0: str, valeur_1: str) -> None:
    executer("INSERT INTO inversions(valeur_0, valeur_1) VALUES(?,?)", (valeur_0, valeur_1))


def supprimer_inversion(inversion_id: int) -> None:
    executer("DELETE FROM inversions WHERE id = ?", (inversion_id,))


def liste_unites() -> list[sqlite3.Row]:
    return lire_tout("SELECT * FROM echelle_unites ORDER BY rang")


def ajouter_unite(unite: str, unite_du_dessous: str, facteur: float, rang: int) -> None:
    executer(
        "INSERT INTO echelle_unites(unite, unite_du_dessous, facteur, rang) VALUES(?,?,?,?)",
        (unite, unite_du_dessous, facteur, rang),
    )


def supprimer_unite(unite_id: int) -> None:
    executer("DELETE FROM echelle_unites WHERE id = ?", (unite_id,))


def liste_evenements() -> list[sqlite3.Row]:
    return lire_tout(
        """
        SELECT e.*, oc.nom AS objet_cause_nom, oe.nom AS objet_effet_nom
        FROM evenements e
        JOIN objets oc ON oc.id = e.objet_cause_id
        JOIN objets oe ON oe.id = e.objet_effet_id
        ORDER BY e.nom
        """
    )


def ajouter_evenement(
    nom: str,
    objet_cause_id: int,
    type_cause: str,
    operateur: str,
    valeur_cause: str,
    poids: float,
    arrivee_tour: int,
    objet_effet_id: int,
    type_effet: str,
    valeur_effet: str,
    propagation_active: int,
    propagation_profondeur: int,
) -> None:
    executer(
        """
        INSERT INTO evenements(
            nom, objet_cause_id, type_cause, operateur, valeur_cause, poids,
            arrivee_tour, objet_effet_id, type_effet, valeur_effet,
            propagation_active, propagation_profondeur, actif
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)
        """,
        (
            nom,
            objet_cause_id,
            type_cause,
            operateur,
            valeur_cause,
            poids,
            arrivee_tour,
            objet_effet_id,
            type_effet,
            valeur_effet,
            propagation_active,
            propagation_profondeur,
        ),
    )


def supprimer_evenement(evenement_id: int) -> None:
    executer("DELETE FROM evenements WHERE id = ?", (evenement_id,))


def liste_paternes() -> list[sqlite3.Row]:
    return lire_tout(
        """
        SELECT p.*, o.nom AS objet_effet_nom
        FROM paternes p
        JOIN objets o ON o.id = p.objet_effet_id
        ORDER BY p.nom
        """
    )


def ajouter_paterne(
    nom: str,
    objet_effet_id: int,
    type_effet: str,
    valeur_effet: str,
    frequence_valeur: float,
    frequence_unite: str,
) -> None:
    executer(
        """
        INSERT INTO paternes(
            nom, objet_effet_id, type_effet, valeur_effet,
            frequence_valeur, frequence_unite, actif
        ) VALUES(?,?,?,?,?,?,1)
        """,
        (nom, objet_effet_id, type_effet, valeur_effet, frequence_valeur, frequence_unite),
    )


def supprimer_paterne(paterne_id: int) -> None:
    executer("DELETE FROM paternes WHERE id = ?", (paterne_id,))

