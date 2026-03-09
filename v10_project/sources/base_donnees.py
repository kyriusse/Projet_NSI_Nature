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


def liste_objets() -> list[sqlite3.Row]:
    return lire_tout("SELECT * FROM objets ORDER BY nom")


def lire_objet_par_id(objet_id: int) -> sqlite3.Row | None:
    return lire_un("SELECT * FROM objets WHERE id = ?", (objet_id,))


def ajouter_objet(nom: str, valeur: float, etat: str) -> None:
    executer("INSERT INTO objets(nom, valeur, etat) VALUES(?,?,?)", (nom, valeur, etat))


def modifier_objet(objet_id: int, nom: str, valeur: float, etat: str) -> None:
    executer(
        "UPDATE objets SET nom = ?, valeur = ?, etat = ? WHERE id = ?",
        (nom, valeur, etat, objet_id),
    )


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
