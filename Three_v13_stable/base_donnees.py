from __future__ import annotations  

import os  
import sqlite3  #module pour manipuler des bases de données SQLite

DOSSIER = os.path.dirname(os.path.abspath(__file__))  #récupère le dossier courant du script
DOSSIER_DATA = os.path.join(DOSSIER, 'data')  #définit le chemin du dossier 'data' dans le projet
UNIVERS_ACTUEL = 'univers_1'  #définit l'univers actif par défaut

def choisir_univers(nom_univers):
    global UNIVERS_ACTUEL  #on modifie la variable globale univers actuelle
    if nom_univers not in ('univers_1', 'univers_2', 'univers_3'):  #vérifie que le nom est valide
        nom_univers = 'univers_1'  #si non valide, on choisit l'univers par défaut
    UNIVERS_ACTUEL = nom_univers  #on met à jour l'univers actuel
    creer_tables()  #crée les tables de la base pour ce nouvel univers

def chemin_bdd():
    os.makedirs(DOSSIER_DATA, exist_ok=True)  #crée le dossier 'data' s'il n'existe pas
    return os.path.join(DOSSIER_DATA, UNIVERS_ACTUEL + '.db')  #retourne le chemin complet de la base de l'univers actuel

def connexion():
    con = sqlite3.connect(chemin_bdd())  #ouvre une connexion à la base SQLite
    con.row_factory = sqlite3.Row  #permet d'accéder aux colonnes par nom
    con.execute('PRAGMA foreign_keys = ON')  #active les clés étrangères pour la base
    return con  #retourne la connexion à utiliser

def executer(requete, parametres=()):
    with connexion() as con:  #ouvre une connexion à la base
        con.execute(requete, tuple(parametres))  #exécute la requête avec les paramètres donnés
        con.commit()  #valide les modifications dans la base

def lire_tout(requete, parametres=()):
    with connexion() as con:  #ouvre une connexion
        return con.execute(requete, tuple(parametres)).fetchall()  #exécute la requête et retourne toutes les lignes

def lire_un(requete, parametres=()):
    with connexion() as con:  #ouvre une connexion
        return con.execute(requete, tuple(parametres)).fetchone()  #exécute la requête et retourne la première ligne

def nom_sql_valide(nom):
    if not nom:  #vérifie que le nom n'est pas vide
        return False
    premier = nom[0]  #prend le premier caractère du nom
    if not (premier.isalpha() or premier == '_'):  #érifie que le premier caractère est une lettre ou un tirets du bas 
        return False
    for caractere in nom:  #parcourt chaque caractère
        if not (caractere.isalnum() or caractere == '_'):  #vérifie que chaque caractère est une lettre ou un tirets du bas 
            return False
    return True  #si toutes les vérifications passent, le nom est valide

def type_sql_pour_nsi(type_colonne):
    if type_colonne == 'int':  #si le type NSI est int
        return 'INTEGER'  #retourne le type SQL correspondant
    if type_colonne == 'float':  #si le type NSI est float
        return 'REAL'  #retourne le type SQL correspondant
    return 'TEXT'  #sinon par défaut retourne TEXT

def valeur_defaut_nsi(type_colonne, valeur_defaut=''):
    if valeur_defaut not in ('', None):  #si une valeur par défaut est donnée
        return valeur_defaut  #on la retourne
    if type_colonne in ('int', 'float'):  #si le type est numérique
        return 0  #valeur par défaut = 0
    return ''  # sinon valeur par défaut = chaîne vide

def creer_tables():
    #crée toutes les tables nécessaires à l'application si elles n'existent pas encore
    executer('CREATE TABLE IF NOT EXISTS tables_nsi(id INTEGER PRIMARY KEY AUTOINCREMENT, nom_table TEXT UNIQUE, est_principale INTEGER DEFAULT 0)')
    #table qui garde la liste des colonnes de chaque table NSI
    executer('CREATE TABLE IF NOT EXISTS colonnes_nsi(id INTEGER PRIMARY KEY AUTOINCREMENT, nom_table TEXT, nom_colonne TEXT, type_colonne TEXT, position INTEGER, valeur_defaut TEXT DEFAULT "", UNIQUE(nom_table, nom_colonne))')
    #table qui référence tous les objets globaux du catalogue
    executer('CREATE TABLE IF NOT EXISTS objets_catalogue(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, nom_table TEXT, id_local INTEGER)')
    #table qui gère les liaisons entre objets
    executer('CREATE TABLE IF NOT EXISTS liaisons(id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER, cible_id INTEGER, type_liaison TEXT, poids REAL DEFAULT 1, conservation TEXT DEFAULT "n")')
    #table qui gère les compositions parent/enfant
    executer('CREATE TABLE IF NOT EXISTS composants(id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER, enfant_id INTEGER, quantite INTEGER DEFAULT 1, UNIQUE(parent_id, enfant_id))')
    #table pour stocker les inversions
    executer('CREATE TABLE IF NOT EXISTS inversions(id INTEGER PRIMARY KEY AUTOINCREMENT, valeur_0 TEXT, valeur_1 TEXT)')
    #table pour gérer les unités (s, min, h, J, etc.)
    executer('CREATE TABLE IF NOT EXISTS unites(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, unite_du_dessous TEXT, facteur REAL, rang INTEGER)')
    #table pour gérer les événements
    executer('CREATE TABLE IF NOT EXISTS evenements(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, objet_cause_id INTEGER, colonne_cause TEXT DEFAULT "valeur", operateur TEXT DEFAULT "=", valeur_cause TEXT DEFAULT "0", objet_effet_id INTEGER, colonne_effet TEXT DEFAULT "valeur", action TEXT DEFAULT "op", valeur_effet TEXT DEFAULT "+1", proba REAL DEFAULT 1, arrivee INTEGER DEFAULT 0, propagation INTEGER DEFAULT 0, actif INTEGER DEFAULT 1)')
    #table pour gérer les paternes
    executer('CREATE TABLE IF NOT EXISTS paternes(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, objet_effet_id INTEGER, colonne_effet TEXT DEFAULT "valeur", action TEXT DEFAULT "op", valeur_effet TEXT DEFAULT "+1", frequence TEXT DEFAULT "1", actif INTEGER DEFAULT 1)')
    #table pour gérer les positions des objets sur la carte
    executer('CREATE TABLE IF NOT EXISTS carte(id INTEGER PRIMARY KEY AUTOINCREMENT, objet_id INTEGER UNIQUE, latitude REAL, longitude REAL, lieu TEXT DEFAULT "")')
    #table pour gérer les chemins
    executer('CREATE TABLE IF NOT EXISTS chemins(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)')
    #table pour stocker les points des chemins
    executer('CREATE TABLE IF NOT EXISTS chemin_points(id INTEGER PRIMARY KEY AUTOINCREMENT, chemin_id INTEGER, ordre_point INTEGER, type_point TEXT, nom_point TEXT, x REAL, y REAL)')

    #si aucune table NSI n'existe, crée une table par défaut "Objets"
    if lire_un('SELECT COUNT(*) AS total FROM tables_nsi')['total'] == 0:
        creer_table_nsi('Objets', 1, [])
    #si aucune unité n'existe, ajoute les unités de base
    if lire_un('SELECT COUNT(*) AS total FROM unites')['total'] == 0:
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('s', None, None, 1))
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('min', 's', 60, 2))
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('h', 'min', 60, 3))
        executer('INSERT INTO unites(nom, unite_du_dessous, facteur, rang) VALUES (?,?,?,?)', ('J', 'h', 24, 4))

def reinitialiser_univers():
    #supprime toutes les tables d'un univers pour repartir à zéro
    with connexion() as con:
        tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()  #récupère toutes les tables existantes
        for table in tables:
            nom = table['name'] if isinstance(table, sqlite3.Row) else table[0]  #récupère le nom de la table
            if nom != 'sqlite_sequence':  #ignore la table de séquences automatique de SQLite
                con.execute('DROP TABLE IF EXISTS ' + nom)  #supprime la table
        con.commit()
    creer_tables()  #recrée les tables de base

def liste_univers():
    #retourne la liste des univers disponibles et s'ils existent
    resultats = []
    for indice in range(1, 4):
        nom = f'univers_{indice}'  #génère le nom de l'univers
        chemin = os.path.join(DOSSIER_DATA, nom + '.db')  #chemin vers la base de cet univers
        existe = os.path.exists(chemin)  #vérifie si la base existe
        resultats.append({'nom': nom, 'existe': existe})  #ajoute le résultat à la liste
    return resultats

def liste_tables_nsi():
    #retourne toutes les tables NSI existantes, triées par principale puis par nom
    return lire_tout('SELECT * FROM tables_nsi ORDER BY est_principale DESC, nom_table')

def table_existe(nom_table):
    #vérifie si une table existe dans la base SQL
    return lire_un("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (nom_table,)) is not None

def colonne_existe(nom_table, nom_colonne):
    #vérifie si une colonne existe dans une table NSI
    return lire_un('SELECT id FROM colonnes_nsi WHERE nom_table = ? AND nom_colonne = ?', (nom_table, nom_colonne)) is not None

def nom_table_principale():
    #retourne le nom de la table principale par défaut "Objets" si aucune n'est définie
    ligne = lire_un('SELECT nom_table FROM tables_nsi WHERE est_principale = 1')
    return ligne['nom_table'] if ligne else 'Objets'

def info_colonnes_physiques(nom_table):
    #récupère les informations sur les colonnes physiques d'une table SQL
    return lire_tout('PRAGMA table_info(' + nom_table + ')')

def colonnes_physiques(nom_table):
    #retourne la liste des noms des colonnes physiques d'une table
    return [ligne['name'] for ligne in info_colonnes_physiques(nom_table)]

def colonnes_remplissables(nom_table):
    #retourne les colonnes où on peut ajouter/modifier des données mais exclut 
    resultat = []
    for nom in colonnes_physiques(nom_table):
        if nom not in ('id', 'nom'):
            resultat.append(nom)
    return resultat


def type_nsi_colonne(nom_table, nom_colonne):
    #retourne le type NSI d'une colonne d'une table donnée
    ligne = lire_un('SELECT type_colonne FROM colonnes_nsi WHERE nom_table = ? AND nom_colonne = ?', (nom_table, nom_colonne))
    if ligne:
        return ligne['type_colonne']  #si la colonne est trouvée dans colonnes_nsi on retourne son type
    if nom_colonne == 'valeur':
        return 'float'  #si colonne spéciale 'valeur', type float
    if nom_colonne == 'etat':
        return 'texte'  #si colonne spéciale 'etat', type texte
    return 'texte'  #sinon type par défaut = texte

def creer_table_nsi(nom_table, est_principale=0, colonnes=None):
    #crée une table NSI avec des colonnes définies
    if not nom_sql_valide(nom_table):
        raise ValueError('Nom de table invalide')  #vérifie que le nom est valide
    if lire_un('SELECT id FROM tables_nsi WHERE nom_table = ?', (nom_table,)):
        raise ValueError('Cette table existe deja')  #vérifie que la table n'existe pas déjà

    colonnes = colonnes or []  #si aucune colonne n'est donnée on prend une liste vide
    morceaux = ['id INTEGER PRIMARY KEY AUTOINCREMENT', 'nom TEXT UNIQUE']  #colonnes de base pour toutes les tables
    if len(colonnes) == 0:
        morceaux.append('valeur REAL DEFAULT 0')  #ajoute colonne 'valeur' par défaut si aucune autre
        morceaux.append('etat TEXT DEFAULT ""')  #ajoute colonne 'etat' par défaut
    for nom_colonne, type_colonne, valeur_defaut in colonnes:
        morceaux.append(f'{nom_colonne} {type_sql_pour_nsi(type_colonne)}')  #ajoute chaque colonne donnée avec type SQL correspondant

    with connexion() as con:
        if est_principale == 1:
            con.execute('UPDATE tables_nsi SET est_principale = 0')  #si c'est la table principale, désactive les autres
        con.execute('INSERT INTO tables_nsi(nom_table, est_principale) VALUES (?, ?)', (nom_table, est_principale))  #ajoute la table dans tables_nsi
        con.execute('CREATE TABLE ' + nom_table + '(' + ', '.join(morceaux) + ')')  #crée la table SQLite
        position = 1
        for nom_colonne, type_colonne, valeur_defaut in colonnes:
            #insère chaque colonne dans colonnes_nsi avec sa position et valeur par défaut
            con.execute(
                'INSERT INTO colonnes_nsi(nom_table, nom_colonne, type_colonne, position, valeur_defaut) VALUES (?,?,?,?,?)',
                (nom_table, nom_colonne, type_colonne, position, str(valeur_defaut_nsi(type_colonne, valeur_defaut)))
            )
            position += 1
        con.commit()  #valide toutes les opérations

def liste_colonnes_table(nom_table):
    #retourne la liste de toutes les colonnes d'une table NSI triées par position
    return lire_tout('SELECT * FROM colonnes_nsi WHERE nom_table = ? ORDER BY position, nom_colonne', (nom_table,))

def ajouter_colonne_table(nom_table, nom_colonne, type_colonne='texte', valeur_defaut=''):
    #ajoute une nouvelle colonne à une table NSI existante
    if not nom_sql_valide(nom_colonne):
        raise ValueError('Nom de colonne invalide')  #vérifie que le nom est valide
    if colonne_existe(nom_table, nom_colonne):
        raise ValueError('Cette colonne existe deja')  #vérifie que la colonne n'existe pas
    if nom_colonne in ('id', 'nom'):
        raise ValueError('Cette colonne ne peut pas etre ajoutee')  #ne peut pas ajouter les colonnes de base

    type_sql = type_sql_pour_nsi(type_colonne)  #convertit le type NSI en type SQL
    valeur_sql = valeur_defaut_nsi(type_colonne, valeur_defaut)  #détermine la valeur par défaut
    definition = type_sql
    if type_colonne in ('int', 'float'):
        definition += ' DEFAULT ' + str(valeur_sql)  #définit la valeur par défaut pour numérique
    elif str(valeur_sql) != '':
        definition += ' DEFAULT ' + repr(str(valeur_sql))  #définit la valeur par défaut pour texte

    position = 1 + len(liste_colonnes_table(nom_table))  #position de la nouvelle colonne
    with connexion() as con:
        con.execute('ALTER TABLE ' + nom_table + ' ADD COLUMN ' + nom_colonne + ' ' + definition)  #ajoute la colonne à la table SQL
        con.execute(
            'INSERT INTO colonnes_nsi(nom_table, nom_colonne, type_colonne, position, valeur_defaut) VALUES (?,?,?,?,?)',
            (nom_table, nom_colonne, type_colonne, position, str(valeur_sql))  #enregistre la colonne dans colonnes_nsi
        )
        con.commit()  #valide les changements

def remplir_colonne_depuis_liste(nom_table, nom_colonne, valeurs):
    #remplit une colonne d'une table avec une liste de valeurs dans l'ordre de ID 
    with connexion() as con:
        lignes = con.execute('SELECT id FROM ' + nom_table + ' ORDER BY id').fetchall()  #récupère tous les ID
        for index, valeur in enumerate(valeurs):
            if index >= len(lignes):
                break  #on arrête si la liste est plus longue que les lignes
            con.execute('UPDATE ' + nom_table + ' SET ' + nom_colonne + ' = ? WHERE id = ?', (valeur, lignes[index]['id']))  # Met à jour chaque ligne
        con.commit()  #valide les changements

def supprimer_colonne_table(nom_table, nom_colonne):
    #supprime une colonne d'une table NSI
    if nom_colonne in ('id', 'nom'):
        raise ValueError('Cette colonne ne peut pas etre supprimee')  #les colonnes de base sont non supprimables
    if nom_colonne not in colonnes_physiques(nom_table):
        raise ValueError('Colonne introuvable')  #vérifie que la colonne existe

    colonnes_a_garder = [col for col in colonnes_physiques(nom_table) if col != nom_colonne]  #colonnes à conserver
    definitions = []
    for ligne in info_colonnes_physiques(nom_table):
        nom = ligne['name']
        if nom == nom_colonne:
            continue
        definition = nom + ' ' + ligne['type']  #définit le type SQL
        if ligne['pk']:
            definition += ' PRIMARY KEY'
            if ligne['type'].upper() == 'INTEGER':
                definition += ' AUTOINCREMENT'  #ajoute AUTOINCREMENT si la clé primaire est entière
        if ligne['dflt_value'] is not None and not ligne['pk']:
            definition += ' DEFAULT ' + str(ligne['dflt_value'])  #définit la valeur par défaut si elle existe
        definitions.append(definition)

    nom_temp = nom_table + '_temp_rebuild'  #nom temporaire pour reconstruction
    with connexion() as con:
        con.execute('CREATE TABLE ' + nom_temp + '(' + ', '.join(definitions) + ')')  #crée table temporaire sans la colonne
        con.execute('INSERT INTO ' + nom_temp + '(' + ','.join(colonnes_a_garder) + ') SELECT ' + ','.join(colonnes_a_garder) + ' FROM ' + nom_table)  #copie les données
        con.execute('DROP TABLE ' + nom_table)  #supprime l'ancienne table
        con.execute('ALTER TABLE ' + nom_temp + ' RENAME TO ' + nom_table)  #renomme temporaire en original
        con.execute('DELETE FROM colonnes_nsi WHERE nom_table = ? AND nom_colonne = ?', (nom_table, nom_colonne))  #supprime colonne de colonnes_nsi
        positions = con.execute('SELECT id FROM colonnes_nsi WHERE nom_table = ? ORDER BY position, nom_colonne', (nom_table,)).fetchall()
        position = 1
        for ligne in positions:
            con.execute('UPDATE colonnes_nsi SET position = ? WHERE id = ?', (position, ligne['id']))  #réajuste positions des colonnes
            position += 1
        con.commit()  #valide tous les changements


def liste_objets(nom_table=None):
    #retourne la liste des objets d'une table donnée ou de la table principale si None
    if nom_table is None:
        nom_table = nom_table_principale()  #utilise la table principale par défaut
    if not lire_un("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (nom_table,)):
        return []  #si la table n'existe pas, retourne une liste vide
    return lire_tout('SELECT * FROM ' + nom_table + ' ORDER BY id')  #retourne tous les objets triés par ID

def objet_global_par_nom(nom):
    #retourne un objet du catalogue par son nom
    return lire_un('SELECT * FROM objets_catalogue WHERE nom = ?', (nom,))

def objet_global_par_id(identifiant):
    #retourne un objet du catalogue par son ID
    return lire_un('SELECT * FROM objets_catalogue WHERE id = ?', (identifiant,))

def objet_existe_dans_table(nom_table, nom_objet):
    #vérifie si un objet existe dans une table spécifique
    return lire_un('SELECT id FROM ' + nom_table + ' WHERE nom = ?', (nom_objet,)) is not None

def ajouter_objet_table(nom_table, donnees):
    #ajoute un nouvel objet à une table NSI
    nom_objet = donnees.get('nom', '').strip()  #récupère le nom de l'objet et supprime les espaces
    if nom_objet == '':
        raise ValueError('Le nom de l\'objet est obligatoire')  #nom obligatoire
    if objet_existe_dans_table(nom_table, nom_objet):
        raise ValueError('Cet objet existe deja dans la table')  #vérifie que le nom est unique 

    colonnes = []
    valeurs = []
    for nom_colonne in colonnes_physiques(nom_table):
        if nom_colonne == 'id':
            continue  #ignore la colonne ID
        colonnes.append(nom_colonne)
        if nom_colonne == 'nom':
            valeurs.append(nom_objet)  #remplit la colonne 'nom'
            continue
        type_colonne = type_nsi_colonne(nom_table, nom_colonne)  #récupère le type NSI
        valeur = donnees.get(nom_colonne, valeur_defaut_nsi(type_colonne, ''))  #récupère la valeur ou défaut
        if valeur in ('', None):
            valeur = valeur_defaut_nsi(type_colonne, '')  #assure valeur par défaut
        valeurs.append(valeur)  #ajoute la valeur à la liste

    emplacements = ','.join(['?'] * len(colonnes))  #crée une chaîne de placeholders pour SQL
    with connexion() as con:
        cur = con.execute('INSERT INTO ' + nom_table + '(' + ','.join(colonnes) + ') VALUES (' + emplacements + ')', tuple(valeurs))  #insère l'objet
        identifiant_local = cur.lastrowid  #récupère l'ID local SQL
        #ajoute l'objet au catalogue global
        con.execute('INSERT OR REPLACE INTO objets_catalogue(nom, nom_table, id_local) VALUES (?,?,?)', (nom_objet, nom_table, identifiant_local))
        con.commit()  #valide la transaction

def mettre_a_jour_valeur_objet(nom_table, nom_objet, nom_colonne, valeur):
    #met à jour la valeur d'une colonne d'un objet existant
    if nom_colonne not in colonnes_physiques(nom_table):
        raise ValueError('Colonne introuvable : ' + nom_colonne)  #vérifie que la colonne existe
    with connexion() as con:
        con.execute('UPDATE ' + nom_table + ' SET ' + nom_colonne + ' = ? WHERE nom = ?', (valeur, nom_objet))  #met à jour la valeur
        con.commit()  #valide la transaction

def supprimer_objet(identifiant_catalogue):
    #supprime un objet du catalogue et de toutes les tables associées
    objet = objet_global_par_id(identifiant_catalogue)  #récupère l'objet par ID
    if objet is None:
        return  #si l'objet n'existe pas rien à faire
    with connexion() as con:
        #supprime toutes les liaisons liées à cet objet
        con.execute('DELETE FROM liaisons WHERE source_id = ? OR cible_id = ?', (objet['id'], objet['id']))
        #supprime toutes les compositions liées
        con.execute('DELETE FROM composants WHERE parent_id = ? OR enfant_id = ?', (objet['id'], objet['id']))
        #supprime tous les événements impliquant cet objet
        con.execute('DELETE FROM evenements WHERE objet_cause_id = ? OR objet_effet_id = ?', (objet['id'], objet['id']))
        #supprime tous les paternes affectant cet objet
        con.execute('DELETE FROM paternes WHERE objet_effet_id = ?', (objet['id'],))
        #supprime sa position sur la carte
        con.execute('DELETE FROM carte WHERE objet_id = ?', (objet['id'],))
        #supprime l'objet de sa table locale
        con.execute('DELETE FROM ' + objet['nom_table'] + ' WHERE id = ?', (objet['id_local'],))
        #ssupprime l'objet du catalogue global
        con.execute('DELETE FROM objets_catalogue WHERE id = ?', (objet['id'],))
        con.commit()  #valide toutes les suppressions

def supprimer_objet_par_nom(nom_objet):
    #supprime un objet du catalogue par son nom
    objet = objet_global_par_nom(nom_objet)
    if objet is not None:
        supprimer_objet(objet['id'])  #appelle la fonction précédente pour la suppression complète

def supprimer_table_nsi(nom_table):
    #supprime une table NSI et tous ses objets
    if nom_table == nom_table_principale():
        raise ValueError('La table principale ne peut pas etre supprimee')  #ne peut pas supprimer la table principale
    if not table_existe(nom_table):
        return  #si la table n'existe pas rien à faire
    objets = lire_tout('SELECT id FROM objets_catalogue WHERE nom_table = ?', (nom_table,))
    for objet in objets:
        supprimer_objet(objet['id'])  #supprime tous les objets de cette table
    with connexion() as con:
        con.execute('DELETE FROM colonnes_nsi WHERE nom_table = ?', (nom_table,))  #supprime colonnes NSI associées
        con.execute('DELETE FROM tables_nsi WHERE nom_table = ?', (nom_table,))  #supprime table NSI du registre
        con.execute('DROP TABLE IF EXISTS ' + nom_table)  #supprime la table SQL
        con.commit()  #valide la transaction

def liste_objets_catalogue():
    #retourne tous les objets du catalogue global triés par nom
    return lire_tout('SELECT * FROM objets_catalogue ORDER BY nom')


def ajouter_liaison(source_nom,cible_nom,type_liaison='=>',poids=1,conservation='n'):
    source = objet_global_par_nom(source_nom) #récupère l'objet source dans le catalogue
    cible = objet_global_par_nom(cible_nom) #récupère l'objet cible dans le catalogue
    if source is None or cible is None:
        raise ValueError('Objet introuvable pour la liaison') #erreur si un objet n'existe pas
    proba = float(poids) #convertit le poids en float
    if proba < 0 or proba > 1:
        raise ValueError('La probabilite d une liaison doit etre entre 0 et 1') #vérifie que la probabilité est entre 0 et 1
    executer(
        'INSERT INTO liaisons(source_id,cible_id,type_liaison,poids,conservation) VALUES (?,?,?,?,?)',
        (source['id'],cible['id'],type_liaison,proba,conservation) #insère la liaison dans la table
    )

def supprimer_liaison(identifiant):
    executer('DELETE FROM liaisons WHERE id = ?',(int(identifiant),)) #supprime une liaison par son id

def liste_liaisons():
    return lire_tout('''SELECT l.id,s.nom AS source_nom,c.nom AS cible_nom,l.type_liaison,l.poids,l.conservation FROM liaisons l JOIN objets_catalogue s ON s.id=l.source_id JOIN objets_catalogue c ON c.id=l.cible_id ORDER BY l.id DESC''')#retourne toutes les liaisons avec noms source/cible

def ajouter_composition(parent_nom,enfant_nom,quantite=1):
    parent = objet_global_par_nom(parent_nom) #récupère l'objet parent
    enfant = objet_global_par_nom(enfant_nom) #récupère l'objet enfant
    if parent is None or enfant is None:
        raise ValueError('Objet introuvable pour la composition') #erreur si un objet n'existe pas
    executer('INSERT OR REPLACE INTO composants(parent_id,enfant_id,quantite) VALUES (?,?,?)',(parent['id'],enfant['id'],int(quantite))) #ajoute la composition

def supprimer_composition(identifiant):
    executer('DELETE FROM composants WHERE id = ?',(int(identifiant),)) #supprime une composition par id

def liste_compositions():
    return lire_tout('''SELECT c.id,p.nom AS parent_nom,e.nom AS enfant_nom,c.quantite FROM composants c JOIN objets_catalogue p ON p.id=c.parent_id JOIN objets_catalogue e ON e.id=c.enfant_id ORDER BY p.nom,e.nom''') #retourne toutes les compositions avec noms parent/enfant

def enfants_de(parent_nom):
    return lire_tout('''SELECT e.nom AS enfant_nom,c.quantite FROM composants c JOIN objets_catalogue p ON p.id=c.parent_id JOIN objets_catalogue e ON e.id=c.enfant_id WHERE p.nom=? ORDER BY e.nom''',(parent_nom,)) #retourne tous les enfants d'un parent donné

def ajouter_evenement(nom,objet_cause_id,colonne_cause,operateur,valeur_cause,objet_effet_id,colonne_effet,action,valeur_effet,proba=1,arrivee=0,propagation=0):
    executer('INSERT INTO evenements(nom,objet_cause_id,colonne_cause,operateur,valeur_cause,objet_effet_id,colonne_effet,action,valeur_effet,proba,arrivee,propagation) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(nom,objet_cause_id,colonne_cause,operateur,valeur_cause,objet_effet_id,colonne_effet,action,valeur_effet,float(proba),int(arrivee),int(propagation)))#ajoute un événement

def liste_evenements():
    return lire_tout('''SELECT e.*,oc.nom AS objet_cause_nom,oe.nom AS objet_effet_nom FROM evenements e JOIN objets_catalogue oc ON oc.id=e.objet_cause_id JOIN objets_catalogue oe ON oe.id=e.objet_effet_id ORDER BY e.nom''') #retourne tous les événements avec noms objets cause/effet

def changer_etat_evenement(identifiant,actif):
    executer('UPDATE evenements SET actif=? WHERE id=?',(int(actif),int(identifiant))) #change l'état actif d'un événement

def supprimer_evenement(identifiant):
    executer('DELETE FROM evenements WHERE id=?',(int(identifiant),)) #supprime un événement par id

def ajouter_paterne(nom,objet_effet_id,colonne_effet,action,valeur_effet,frequence=1):
    executer('INSERT INTO paternes(nom,objet_effet_id,colonne_effet,action,valeur_effet,frequence) VALUES (?,?,?,?,?,?)',(nom,objet_effet_id,colonne_effet,action,valeur_effet,str(frequence).strip() or '1')) #ajoute un paterne

def liste_paternes():
    return lire_tout('''SELECT p.*,oe.nom AS objet_effet_nom FROM paternes p JOIN objets_catalogue oe ON oe.id=p.objet_effet_id ORDER BY p.nom''') #retourne tous les paternes avec nom de l'objet effet

def changer_etat_paterne(identifiant,actif):
    executer('UPDATE paternes SET actif=? WHERE id=?',(int(actif),int(identifiant))) #change l'état actif d'un paterne

def supprimer_paterne(identifiant):
    executer('DELETE FROM paternes WHERE id=?',(int(identifiant),)) #supprime un paterne par id

def liste_unites():
    return lire_tout('SELECT * FROM unites ORDER BY rang')  #retourne toutes les unités triées par rang

def ajouter_unite(nom,dessous,facteur):
    lignes = liste_unites() #récupère la liste des unités existantes
    rang = 1
    dessous_reel = None
    if dessous:
        dessous_ligne = lire_un('SELECT * FROM unites WHERE nom=?',(dessous,)) #récupère l'unité en dessous
        if dessous_ligne:
            rang = int(dessous_ligne['rang'])+1 #détermine le rang de la nouvelle unité
            dessous_reel = dessous #enregistre l'unité en dessous
            executer('UPDATE unites SET rang=rang+1 WHERE rang>=?',(rang,)) #décale les rangs existants
    else:
        if lignes:
            executer('UPDATE unites SET rang=rang+1') #décale tous les rangs si aucune unité en dessous
        rang = 1
    executer('INSERT INTO unites(nom,unite_du_dessous,facteur,rang) VALUES (?,?,?,?)',(nom,dessous_reel,facteur if facteur not in ('',None) else None,rang)) #ajoute la nouvelle unité


def ajouter_inversion(valeur_0,valeur_1):
    executer('INSERT INTO inversions(valeur_0,valeur_1) VALUES (?,?)',(valeur_0,valeur_1)) #ajoute une inversion

def supprimer_inversion(identifiant):
    executer('DELETE FROM inversions WHERE id = ?',(int(identifiant),)) #supprime une inversion par id

def liste_inversions():
    return lire_tout('SELECT * FROM inversions ORDER BY id DESC') #retourne toutes les inversions

def enregistrer_position(objet_id,latitude,longitude,lieu=''):
    executer('INSERT OR REPLACE INTO carte(objet_id,latitude,longitude,lieu) VALUES (?,?,?,?)',(int(objet_id),float(latitude),float(longitude),lieu)) #enregistre la position d'un objet

def supprimer_position(identifiant):
    executer('DELETE FROM carte WHERE id = ?',(int(identifiant),)) #supprime une position par id

def liste_positions():
    return lire_tout('''SELECT c.*,o.nom FROM carte c JOIN objets_catalogue o ON o.id=c.objet_id ORDER BY o.nom''') #retourne toutes les positions avec nom des objets

def position_par_objet(objet_id):
    return lire_un('SELECT * FROM carte WHERE objet_id = ?',(objet_id,)) #retourne la position d'un objet par id

def ajouter_chemin(nom,points):
    with connexion() as con:
        con.execute('INSERT OR REPLACE INTO chemins(nom) VALUES (?)',(nom,)) #ajoute ou remplace un chemin
        chemin = con.execute('SELECT id FROM chemins WHERE nom = ?',(nom,)).fetchone() #récupère l'id du chemin
        con.execute('DELETE FROM chemin_points WHERE chemin_id = ?',(chemin['id'],)) #supprime les points existants
        ordre = 1
        for point in points:
            con.execute('INSERT INTO chemin_points(chemin_id,ordre_point,type_point,nom_point,x,y) VALUES (?,?,?,?,?,?)',(chemin['id'],ordre,point.get('type','point'),point.get('nom',''),float(point.get('x',0)),float(point.get('y',0)))) #ajoute chaque point
            ordre += 1
        con.commit() #valide la transaction

def supprimer_chemin(identifiant):
    with connexion() as con:
        con.execute('DELETE FROM chemin_points WHERE chemin_id = ?',(int(identifiant),)) #supprime les points d'un chemin
        con.execute('DELETE FROM chemins WHERE id = ?',(int(identifiant),)) #supprime le chemin
        con.commit() #valide la transaction

def liste_chemins():
    return lire_tout('SELECT * FROM chemins ORDER BY nom') #retourne tous les chemins triés par nom

def points_chemin(chemin_id):
    return lire_tout('SELECT * FROM chemin_points WHERE chemin_id = ? ORDER BY ordre_point',(chemin_id,)) #retourne tous les points d'un chemin

def liste_objets_simulation():
    tables = liste_tables_nsi() #récupère toutes les tables NSI
    resultat = [] #initialise la liste finale

    for table in tables:
        nom_table = table['nom_table'] #nom de la table
        lignes = liste_objets(nom_table) #récupère tous les objets de la table

        for ligne in lignes:
            copie = dict(ligne) #crée une copie de la ligne
            copie['nom_table'] = nom_table #ajoute le nom de la table à la copie

            if 'valeur' not in copie:
                copie['valeur'] = 0 #ajoute valeur 0 si absent

            if 'etat' not in copie:
                copie['etat'] = '' #ajoute état vide si absent

            resultat.append(copie) #ajoute la copie à la liste finale

    return resultat #retourne tous les objets simulés
