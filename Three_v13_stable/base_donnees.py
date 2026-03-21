from __future__ import annotations

import os
import sqlite3

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(DOSSIER, 'data')
UNIVERS_ACTUEL = 'univers_1'


def choisir_univers(nom_univers):
    global UNIVERS_ACTUEL
    if nom_univers not in ('univers_1', 'univers_2', 'univers_3'):
        nom_univers = 'univers_1'
    UNIVERS_ACTUEL = nom_univers
    creer_tables()


def chemin_bdd():
    os.makedirs(DOSSIER_DATA, exist_ok=True)
    return os.path.join(DOSSIER_DATA, UNIVERS_ACTUEL + '.db')


def connexion():
    con = sqlite3.connect(chemin_bdd())
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def executer(requete, parametres=()):
    with connexion() as con:
        con.execute(requete, tuple(parametres))
        con.commit()


def lire_tout(requete, parametres=()):
    with connexion() as con:
        return con.execute(requete, tuple(parametres)).fetchall()


def lire_un(requete, parametres=()):
    with connexion() as con:
        return con.execute(requete, tuple(parametres)).fetchone()


def nom_sql_valide(nom):
    if not nom:
        return False
    premier = nom[0]
    if not (premier.isalpha() or premier == '_'):
        return False
    for caractere in nom:
        if not (caractere.isalnum() or caractere == '_'):
            return False
    return True


def type_sql_pour_nsi(type_colonne):
    if type_colonne == 'int':
        return 'INTEGER'
    if type_colonne == 'float':
        return 'REAL'
    return 'TEXT'


def valeur_defaut_nsi(type_colonne, valeur_defaut=''):
    if valeur_defaut not in ('', None):
        return valeur_defaut
    if type_colonne in ('int', 'float'):
        return 0
    return ''


def creer_tables():
    executer('CREATE TABLE IF NOT EXISTS tables_nsi(id INTEGER PRIMARY KEY AUTOINCREMENT, nom_table TEXT UNIQUE, est_principale INTEGER DEFAULT 0)')
    executer('CREATE TABLE IF NOT EXISTS colonnes_nsi(id INTEGER PRIMARY KEY AUTOINCREMENT, nom_table TEXT, nom_colonne TEXT, type_colonne TEXT, position INTEGER, valeur_defaut TEXT DEFAULT "", UNIQUE(nom_table, nom_colonne))')
    executer('CREATE TABLE IF NOT EXISTS objets_catalogue(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, nom_table TEXT, id_local INTEGER)')
    executer('CREATE TABLE IF NOT EXISTS liaisons(id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER, cible_id INTEGER, type_liaison TEXT, poids REAL DEFAULT 1, conservation TEXT DEFAULT "n")')
    executer('CREATE TABLE IF NOT EXISTS composants(id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER, enfant_id INTEGER, quantite INTEGER DEFAULT 1, UNIQUE(parent_id, enfant_id))')
    executer('CREATE TABLE IF NOT EXISTS inversions(id INTEGER PRIMARY KEY AUTOINCREMENT, valeur_0 TEXT, valeur_1 TEXT)')
    executer('CREATE TABLE IF NOT EXISTS unites(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, unite_du_dessous TEXT, facteur REAL, rang INTEGER)')
    executer('CREATE TABLE IF NOT EXISTS evenements(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, objet_cause_id INTEGER, colonne_cause TEXT DEFAULT "valeur", operateur TEXT DEFAULT "=", valeur_cause TEXT DEFAULT "0", objet_effet_id INTEGER, colonne_effet TEXT DEFAULT "valeur", action TEXT DEFAULT "op", valeur_effet TEXT DEFAULT "+1", proba REAL DEFAULT 1, arrivee INTEGER DEFAULT 0, propagation INTEGER DEFAULT 0, actif INTEGER DEFAULT 1)')
    executer('CREATE TABLE IF NOT EXISTS paternes(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, objet_effet_id INTEGER, colonne_effet TEXT DEFAULT "valeur", action TEXT DEFAULT "op", valeur_effet TEXT DEFAULT "+1", frequence TEXT DEFAULT "1", actif INTEGER DEFAULT 1)')
    executer('CREATE TABLE IF NOT EXISTS carte(id INTEGER PRIMARY KEY AUTOINCREMENT, objet_id INTEGER UNIQUE, latitude REAL, longitude REAL, lieu TEXT DEFAULT "")')
    executer('CREATE TABLE IF NOT EXISTS chemins(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)')
    executer('CREATE TABLE IF NOT EXISTS chemin_points(id INTEGER PRIMARY KEY AUTOINCREMENT, chemin_id INTEGER, ordre_point INTEGER, type_point TEXT, nom_point TEXT, x REAL, y REAL)')

    if lire_un('SELECT COUNT(*) AS total FROM tables_nsi')['total'] == 0:
        creer_table_nsi('Objets', 1, [])
    if lire_un('SELECT COUNT(*) AS total FROM unites')['total'] == 0:
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('s', None, None, 1))
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('min', 's', 60, 2))
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('h', 'min', 60, 3))
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('J', 'h', 24, 4))


def reinitialiser_univers():
    with connexion() as con:
        tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table in tables:
            nom = table['name'] if isinstance(table, sqlite3.Row) else table[0]
            if nom != 'sqlite_sequence':
                con.execute('DROP TABLE IF EXISTS ' + nom)
        con.commit()
    creer_tables()


def liste_univers():
    resultats = []
    for indice in range(1, 4):
        nom = f'univers_{indice}'
        chemin = os.path.join(DOSSIER_DATA, nom + '.db')
        existe = os.path.exists(chemin)
        resultats.append({'nom': nom, 'existe': existe})
    return resultats


def liste_tables_nsi():
    return lire_tout('SELECT * FROM tables_nsi ORDER BY est_principale DESC, nom_table')


def table_existe(nom_table):
    return lire_un("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (nom_table,)) is not None


def colonne_existe(nom_table, nom_colonne):
    return lire_un('SELECT id FROM colonnes_nsi WHERE nom_table = ? AND nom_colonne = ?', (nom_table, nom_colonne)) is not None


def nom_table_principale():
    ligne = lire_un('SELECT nom_table FROM tables_nsi WHERE est_principale = 1')
    return ligne['nom_table'] if ligne else 'Objets'


def info_colonnes_physiques(nom_table):
    return lire_tout('PRAGMA table_info(' + nom_table + ')')


def colonnes_physiques(nom_table):
    return [ligne['name'] for ligne in info_colonnes_physiques(nom_table)]


def colonnes_remplissables(nom_table):
    resultat = []
    for nom in colonnes_physiques(nom_table):
        if nom not in ('id', 'nom'):
            resultat.append(nom)
    return resultat


def type_nsi_colonne(nom_table, nom_colonne):
    ligne = lire_un('SELECT type_colonne FROM colonnes_nsi WHERE nom_table = ? AND nom_colonne = ?', (nom_table, nom_colonne))
    if ligne:
        return ligne['type_colonne']
    if nom_colonne == 'valeur':
        return 'float'
    if nom_colonne == 'etat':
        return 'texte'
    return 'texte'


def creer_table_nsi(nom_table, est_principale=0, colonnes=None):
    if not nom_sql_valide(nom_table):
        raise ValueError('Nom de table invalide')
    if lire_un('SELECT id FROM tables_nsi WHERE nom_table = ?', (nom_table,)):
        raise ValueError('Cette table existe deja')

    colonnes = colonnes or []
    morceaux = ['id INTEGER PRIMARY KEY AUTOINCREMENT', 'nom TEXT UNIQUE']
    if len(colonnes) == 0:
        morceaux.append('valeur REAL DEFAULT 0')
        morceaux.append('etat TEXT DEFAULT ""')
    for nom_colonne, type_colonne, valeur_defaut in colonnes:
        morceaux.append(f'{nom_colonne} {type_sql_pour_nsi(type_colonne)}')

    with connexion() as con:
        if est_principale == 1:
            con.execute('UPDATE tables_nsi SET est_principale = 0')
        con.execute('INSERT INTO tables_nsi(nom_table, est_principale) VALUES (?, ?)', (nom_table, est_principale))
        con.execute('CREATE TABLE ' + nom_table + '(' + ', '.join(morceaux) + ')')
        position = 1
        for nom_colonne, type_colonne, valeur_defaut in colonnes:
            con.execute(
                'INSERT INTO colonnes_nsi(nom_table, nom_colonne, type_colonne, position, valeur_defaut) VALUES (?,?,?,?,?)',
                (nom_table, nom_colonne, type_colonne, position, str(valeur_defaut_nsi(type_colonne, valeur_defaut)))
            )
            position += 1
        con.commit()


def liste_colonnes_table(nom_table):
    return lire_tout('SELECT * FROM colonnes_nsi WHERE nom_table = ? ORDER BY position, nom_colonne', (nom_table,))


def ajouter_colonne_table(nom_table, nom_colonne, type_colonne='texte', valeur_defaut=''):
    if not nom_sql_valide(nom_colonne):
        raise ValueError('Nom de colonne invalide')
    if colonne_existe(nom_table, nom_colonne):
        raise ValueError('Cette colonne existe deja')
    if nom_colonne in ('id', 'nom'):
        raise ValueError('Cette colonne ne peut pas etre ajoutee')

    type_sql = type_sql_pour_nsi(type_colonne)
    valeur_sql = valeur_defaut_nsi(type_colonne, valeur_defaut)
    definition = type_sql
    if type_colonne in ('int', 'float'):
        definition += ' DEFAULT ' + str(valeur_sql)
    elif str(valeur_sql) != '':
        definition += ' DEFAULT ' + repr(str(valeur_sql))

    position = 1 + len(liste_colonnes_table(nom_table))
    with connexion() as con:
        con.execute('ALTER TABLE ' + nom_table + ' ADD COLUMN ' + nom_colonne + ' ' + definition)
        con.execute(
            'INSERT INTO colonnes_nsi(nom_table, nom_colonne, type_colonne, position, valeur_defaut) VALUES (?,?,?,?,?)',
            (nom_table, nom_colonne, type_colonne, position, str(valeur_sql))
        )
        con.commit()


def remplir_colonne_depuis_liste(nom_table, nom_colonne, valeurs):
    with connexion() as con:
        lignes = con.execute('SELECT id FROM ' + nom_table + ' ORDER BY id').fetchall()
        for index, valeur in enumerate(valeurs):
            if index >= len(lignes):
                break
            con.execute('UPDATE ' + nom_table + ' SET ' + nom_colonne + ' = ? WHERE id = ?', (valeur, lignes[index]['id']))
        con.commit()


def supprimer_colonne_table(nom_table, nom_colonne):
    if nom_colonne in ('id', 'nom'):
        raise ValueError('Cette colonne ne peut pas etre supprimee')
    if nom_colonne not in colonnes_physiques(nom_table):
        raise ValueError('Colonne introuvable')

    colonnes_a_garder = [col for col in colonnes_physiques(nom_table) if col != nom_colonne]
    definitions = []
    for ligne in info_colonnes_physiques(nom_table):
        nom = ligne['name']
        if nom == nom_colonne:
            continue
        definition = nom + ' ' + ligne['type']
        if ligne['pk']:
            definition += ' PRIMARY KEY'
            if ligne['type'].upper() == 'INTEGER':
                definition += ' AUTOINCREMENT'
        if ligne['dflt_value'] is not None and not ligne['pk']:
            definition += ' DEFAULT ' + str(ligne['dflt_value'])
        definitions.append(definition)

    nom_temp = nom_table + '_temp_rebuild'
    with connexion() as con:
        con.execute('CREATE TABLE ' + nom_temp + '(' + ', '.join(definitions) + ')')
        con.execute('INSERT INTO ' + nom_temp + '(' + ','.join(colonnes_a_garder) + ') SELECT ' + ','.join(colonnes_a_garder) + ' FROM ' + nom_table)
        con.execute('DROP TABLE ' + nom_table)
        con.execute('ALTER TABLE ' + nom_temp + ' RENAME TO ' + nom_table)
        con.execute('DELETE FROM colonnes_nsi WHERE nom_table = ? AND nom_colonne = ?', (nom_table, nom_colonne))
        positions = con.execute('SELECT id FROM colonnes_nsi WHERE nom_table = ? ORDER BY position, nom_colonne', (nom_table,)).fetchall()
        position = 1
        for ligne in positions:
            con.execute('UPDATE colonnes_nsi SET position = ? WHERE id = ?', (position, ligne['id']))
            position += 1
        con.commit()


def liste_objets(nom_table=None):
    if nom_table is None:
        nom_table = nom_table_principale()
    if not lire_un("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (nom_table,)):
        return []
    return lire_tout('SELECT * FROM ' + nom_table + ' ORDER BY id')


def objet_global_par_nom(nom):
    return lire_un('SELECT * FROM objets_catalogue WHERE nom = ?', (nom,))


def objet_global_par_id(identifiant):
    return lire_un('SELECT * FROM objets_catalogue WHERE id = ?', (identifiant,))


def objet_existe_dans_table(nom_table, nom_objet):
    return lire_un('SELECT id FROM ' + nom_table + ' WHERE nom = ?', (nom_objet,)) is not None


def ajouter_objet_table(nom_table, donnees):
    nom_objet = donnees.get('nom', '').strip()
    if nom_objet == '':
        raise ValueError('Le nom de l\'objet est obligatoire')
    if objet_existe_dans_table(nom_table, nom_objet):
        raise ValueError('Cet objet existe deja dans la table')

    colonnes = []
    valeurs = []
    for nom_colonne in colonnes_physiques(nom_table):
        if nom_colonne == 'id':
            continue
        colonnes.append(nom_colonne)
        if nom_colonne == 'nom':
            valeurs.append(nom_objet)
            continue
        type_colonne = type_nsi_colonne(nom_table, nom_colonne)
        valeur = donnees.get(nom_colonne, valeur_defaut_nsi(type_colonne, ''))
        if valeur in ('', None):
            valeur = valeur_defaut_nsi(type_colonne, '')
        valeurs.append(valeur)

    emplacements = ','.join(['?'] * len(colonnes))
    with connexion() as con:
        cur = con.execute('INSERT INTO ' + nom_table + '(' + ','.join(colonnes) + ') VALUES (' + emplacements + ')', tuple(valeurs))
        identifiant_local = cur.lastrowid
        con.execute('INSERT OR REPLACE INTO objets_catalogue(nom, nom_table, id_local) VALUES (?,?,?)', (nom_objet, nom_table, identifiant_local))
        con.commit()


def mettre_a_jour_valeur_objet(nom_table, nom_objet, nom_colonne, valeur):
    if nom_colonne not in colonnes_physiques(nom_table):
        raise ValueError('Colonne introuvable : ' + nom_colonne)
    with connexion() as con:
        con.execute('UPDATE ' + nom_table + ' SET ' + nom_colonne + ' = ? WHERE nom = ?', (valeur, nom_objet))
        con.commit()


def supprimer_objet(identifiant_catalogue):
    objet = objet_global_par_id(identifiant_catalogue)
    if objet is None:
        return
    with connexion() as con:
        con.execute('DELETE FROM liaisons WHERE source_id = ? OR cible_id = ?', (objet['id'], objet['id']))
        con.execute('DELETE FROM composants WHERE parent_id = ? OR enfant_id = ?', (objet['id'], objet['id']))
        con.execute('DELETE FROM evenements WHERE objet_cause_id = ? OR objet_effet_id = ?', (objet['id'], objet['id']))
        con.execute('DELETE FROM paternes WHERE objet_effet_id = ?', (objet['id'],))
        con.execute('DELETE FROM carte WHERE objet_id = ?', (objet['id'],))
        con.execute('DELETE FROM ' + objet['nom_table'] + ' WHERE id = ?', (objet['id_local'],))
        con.execute('DELETE FROM objets_catalogue WHERE id = ?', (objet['id'],))
        con.commit()




def supprimer_objet_par_nom(nom_objet):
    objet = objet_global_par_nom(nom_objet)
    if objet is not None:
        supprimer_objet(objet['id'])

def supprimer_table_nsi(nom_table):
    if nom_table == nom_table_principale():
        raise ValueError('La table principale ne peut pas etre supprimee')
    if not table_existe(nom_table):
        return
    objets = lire_tout('SELECT id FROM objets_catalogue WHERE nom_table = ?', (nom_table,))
    for objet in objets:
        supprimer_objet(objet['id'])
    with connexion() as con:
        con.execute('DELETE FROM colonnes_nsi WHERE nom_table = ?', (nom_table,))
        con.execute('DELETE FROM tables_nsi WHERE nom_table = ?', (nom_table,))
        con.execute('DROP TABLE IF EXISTS ' + nom_table)
        con.commit()


def liste_objets_catalogue():
    return lire_tout('SELECT * FROM objets_catalogue ORDER BY nom')


def ajouter_liaison(source_nom, cible_nom, type_liaison='=>', poids=1, conservation='n'):
    source = objet_global_par_nom(source_nom)
    cible = objet_global_par_nom(cible_nom)
    if source is None or cible is None:
        raise ValueError('Objet introuvable pour la liaison')
    proba = float(poids)
    if proba < 0 or proba > 1:
        raise ValueError('La probabilite d une liaison doit etre entre 0 et 1')
    executer(
        'INSERT INTO liaisons(source_id, cible_id, type_liaison, poids, conservation) VALUES (?,?,?,?,?)',
        (source['id'], cible['id'], type_liaison, proba, conservation)
    )


def supprimer_liaison(identifiant):
    executer('DELETE FROM liaisons WHERE id = ?', (int(identifiant),))


def liste_liaisons():
    return lire_tout('''
        SELECT l.id, s.nom AS source_nom, c.nom AS cible_nom, l.type_liaison, l.poids, l.conservation
        FROM liaisons l
        JOIN objets_catalogue s ON s.id = l.source_id
        JOIN objets_catalogue c ON c.id = l.cible_id
        ORDER BY l.id DESC
    ''')


def ajouter_composition(parent_nom, enfant_nom, quantite=1):
    parent = objet_global_par_nom(parent_nom)
    enfant = objet_global_par_nom(enfant_nom)
    if parent is None or enfant is None:
        raise ValueError('Objet introuvable pour la composition')
    executer('INSERT OR REPLACE INTO composants(parent_id, enfant_id, quantite) VALUES (?,?,?)', (parent['id'], enfant['id'], int(quantite)))


def supprimer_composition(identifiant):
    executer('DELETE FROM composants WHERE id = ?', (int(identifiant),))


def liste_compositions():
    return lire_tout('''
        SELECT c.id, p.nom AS parent_nom, e.nom AS enfant_nom, c.quantite
        FROM composants c
        JOIN objets_catalogue p ON p.id = c.parent_id
        JOIN objets_catalogue e ON e.id = c.enfant_id
        ORDER BY p.nom, e.nom
    ''')


def enfants_de(parent_nom):
    return lire_tout('''
        SELECT e.nom AS enfant_nom, c.quantite
        FROM composants c
        JOIN objets_catalogue p ON p.id = c.parent_id
        JOIN objets_catalogue e ON e.id = c.enfant_id
        WHERE p.nom = ?
        ORDER BY e.nom
    ''', (parent_nom,))


def ajouter_evenement(nom, objet_cause_id, colonne_cause, operateur, valeur_cause, objet_effet_id, colonne_effet, action, valeur_effet, proba=1, arrivee=0, propagation=0):
    executer('INSERT INTO evenements(nom, objet_cause_id, colonne_cause, operateur, valeur_cause, objet_effet_id, colonne_effet, action, valeur_effet, proba, arrivee, propagation) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (nom, objet_cause_id, colonne_cause, operateur, valeur_cause, objet_effet_id, colonne_effet, action, valeur_effet, float(proba), int(arrivee), int(propagation)))


def liste_evenements():
    return lire_tout('''
        SELECT e.*, oc.nom AS objet_cause_nom, oe.nom AS objet_effet_nom
        FROM evenements e
        JOIN objets_catalogue oc ON oc.id = e.objet_cause_id
        JOIN objets_catalogue oe ON oe.id = e.objet_effet_id
        ORDER BY e.nom
    ''')


def changer_etat_evenement(identifiant, actif):
    executer('UPDATE evenements SET actif = ? WHERE id = ?', (int(actif), int(identifiant)))


def supprimer_evenement(identifiant):
    executer('DELETE FROM evenements WHERE id = ?', (int(identifiant),))


def ajouter_paterne(nom, objet_effet_id, colonne_effet, action, valeur_effet, frequence=1):
    executer('INSERT INTO paternes(nom, objet_effet_id, colonne_effet, action, valeur_effet, frequence) VALUES (?,?,?,?,?,?)', (nom, objet_effet_id, colonne_effet, action, valeur_effet, str(frequence).strip() or '1'))


def liste_paternes():
    return lire_tout('''
        SELECT p.*, oe.nom AS objet_effet_nom
        FROM paternes p
        JOIN objets_catalogue oe ON oe.id = p.objet_effet_id
        ORDER BY p.nom
    ''')


def changer_etat_paterne(identifiant, actif):
    executer('UPDATE paternes SET actif = ? WHERE id = ?', (int(actif), int(identifiant)))


def supprimer_paterne(identifiant):
    executer('DELETE FROM paternes WHERE id = ?', (int(identifiant),))


def liste_unites():
    return lire_tout('SELECT * FROM unites ORDER BY rang')


def ajouter_unite(nom, dessous, facteur):
    lignes = liste_unites()
    rang = 1
    dessous_reel = None
    if dessous:
        dessous_ligne = lire_un('SELECT * FROM unites WHERE nom = ?', (dessous,))
        if dessous_ligne:
            rang = int(dessous_ligne['rang']) + 1
            dessous_reel = dessous
            executer('UPDATE unites SET rang = rang + 1 WHERE rang >= ?', (rang,))
    else:
        if lignes:
            executer('UPDATE unites SET rang = rang + 1')
        rang = 1
    executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', (nom, dessous_reel, facteur if facteur not in ('', None) else None, rang))


def ajouter_inversion(valeur_0, valeur_1):
    executer('INSERT INTO inversions(valeur_0, valeur_1) VALUES (?,?)', (valeur_0, valeur_1))


def supprimer_inversion(identifiant):
    executer('DELETE FROM inversions WHERE id = ?', (int(identifiant),))


def liste_inversions():
    return lire_tout('SELECT * FROM inversions ORDER BY id DESC')


def enregistrer_position(objet_id, latitude, longitude, lieu=''):
    executer('INSERT OR REPLACE INTO carte(objet_id, latitude, longitude, lieu) VALUES (?,?,?,?)', (int(objet_id), float(latitude), float(longitude), lieu))


def supprimer_position(identifiant):
    executer('DELETE FROM carte WHERE id = ?', (int(identifiant),))


def liste_positions():
    return lire_tout('''
        SELECT c.*, o.nom
        FROM carte c
        JOIN objets_catalogue o ON o.id = c.objet_id
        ORDER BY o.nom
    ''')


def position_par_objet(objet_id):
    return lire_un('SELECT * FROM carte WHERE objet_id = ?', (objet_id,))


def ajouter_chemin(nom, points):
    with connexion() as con:
        con.execute('INSERT OR REPLACE INTO chemins(nom) VALUES (?)', (nom,))
        chemin = con.execute('SELECT id FROM chemins WHERE nom = ?', (nom,)).fetchone()
        con.execute('DELETE FROM chemin_points WHERE chemin_id = ?', (chemin['id'],))
        ordre = 1
        for point in points:
            con.execute('INSERT INTO chemin_points(chemin_id, ordre_point, type_point, nom_point, x, y) VALUES (?,?,?,?,?,?)', (chemin['id'], ordre, point.get('type', 'point'), point.get('nom', ''), float(point.get('x', 0)), float(point.get('y', 0))))
            ordre += 1
        con.commit()


def supprimer_chemin(identifiant):
    with connexion() as con:
        con.execute('DELETE FROM chemin_points WHERE chemin_id = ?', (int(identifiant),))
        con.execute('DELETE FROM chemins WHERE id = ?', (int(identifiant),))
        con.commit()


def liste_chemins():
    return lire_tout('SELECT * FROM chemins ORDER BY nom')


def points_chemin(chemin_id):
    return lire_tout('SELECT * FROM chemin_points WHERE chemin_id = ? ORDER BY ordre_point', (chemin_id,))

def liste_objets_simulation():
    tables = liste_tables_nsi()
    resultat = []

    for table in tables:
        nom_table = table['nom_table']
        lignes = liste_objets(nom_table)

        for ligne in lignes:
            copie = dict(ligne)
            copie['nom_table'] = nom_table

            if 'valeur' not in copie:
                copie['valeur'] = 0

            if 'etat' not in copie:
                copie['etat'] = ''

            resultat.append(copie)

    return resultat
