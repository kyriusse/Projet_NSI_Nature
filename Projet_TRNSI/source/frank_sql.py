from __future__ import annotations
# sert à manipuler du texte HTML et les regex (recherche/remplacement de motifs)
import html
import re
# functions pour convertir du texte en int ou float avec une valeur par défaut en cas d'erreur
from outils_nsi import entier_ou_defaut, reel_ou_defaut


def colorer_code(texte):
    # Échappe les caractères spéciaux HTML
    resultat = html.escape(texte)
    # Colore les commentaires en rouge
    resultat = re.sub(r'(^|<br>)\s*#([^<]*)', lambda m: m.group(1) + "<span class='com'>#" + m.group(2) + '</span>', resultat) #ligne généré par l'IA
    mots = ['tab', 'col', 'obj', 'cp', 'evt', 'pat', 'map', 'sim', 'unite', 'ch', 'vd', 'obj=', 'col=', 'tab=', 'op=', 'change=', 'inv', 'act', 'dsc', 'lat=', 'long=', 'x=', 'y=', 't.', 'c.', 'o.'] # Liste des mots-clés à colorer
    for mot in mots:
        resultat = resultat.replace(mot, "<span class='kw'>" + mot + '</span>') # Colore les mots-clés en bleu
    resultat = re.sub(r'(?<![\w>])(\d+(?:[\.,]\d+)?)', r"<span class='num'>\1</span>", resultat) # Colore les nombres en vert #LIGNE GENERE PAR l'IA
    return resultat.replace('\n', '<br>') # On remplace les sauts de ligne par des balises <br>


def nettoyer_texte(texte):
    lignes = [] # Créé une liste vide
    for ligne in texte.splitlines():
        # Enlève les espaces au début et à la fin de la ligne
        propre = ligne.strip()
        # Si la ligne n'est pas vide et ne commence pas par # on la garde
        if propre and not propre.startswith('#'): 
            lignes.append(propre)
    # Retourne toutes les lignes valides rejointes avec des \n
    return '\n'.join(lignes)


def extraire_blocs(texte):
    # Enlève les commentaires et les espaces inutiles
    texte = nettoyer_texte(texte)
    blocs = [] # Liste pour stocker les blocs extraits
    indice = 0 # La position actuelle dans le texte
    while indice < len(texte):
        # Saute tous les espaces et retours à la ligne
        while indice < len(texte) and texte[indice].isspace():
            indice += 1
        if indice >= len(texte): # Si on a atteint la fin on sort de la boucle
            break
        # Marque le début du mot-clé
        debut = indice
        # Lis les caractères alphanumériques, les points et les underscores (mot-clé)
        while indice < len(texte) and (texte[indice].isalnum() or texte[indice] in '._'):
            indice += 1
        prefixe = texte[debut:indice].strip() # Extrait le mot-clé
        # Saute les espaces après le mot-clé
        while indice < len(texte) and texte[indice].isspace():
            indice += 1
        # Si pas de { (accolade), c'est un bloc simple d'une seule ligne
        if indice >= len(texte) or texte[indice] != '{':
            fin_ligne = texte.find('\n', debut)
            if fin_ligne == -1:
                fin_ligne = len(texte)
            blocs.append((prefixe, texte[debut:fin_ligne].strip())) # Ajoute le bloc simple
            indice = fin_ligne + 1
            continue
        # Sinon c'est un bloc avec accolades et donc cherche le contenu entre { et }
        profondeur = 0 # Compte les accolades ouvertes/fermées
        debut_contenu = indice + 1 # Début du contenu après la première accolade
        while indice < len(texte):
            if texte[indice] == '{':
                profondeur += 1
            elif texte[indice] == '}':
                profondeur -= 1
                if profondeur == 0: # Si on a fermé la première accolade on a trouvé la fin du bloc
                    # Extrait le contenu entre les accolades
                    contenu = texte[debut_contenu:indice]
                    blocs.append((prefixe, contenu.strip())) # Ajoute le bloc avec son contenu
                    indice += 1
                    break
            indice += 1
    return blocs # Retourne la liste de tous les blocs extraits sous forme de tuples (prefixe, contenu)

def traiter_inversion(element, base_donnees):  # Fonction qui traite une ligne du bloc inv{...}
    element = element.strip()  # Enleve les espaces inutiles au debut et a la fin
    if element.startswith('(') and element.endswith(')'):  # Verifie si l'inversion est ecrite entre parentheses
        element = element[1:-1]  # Retire la parenthese ouvrante et la parenthese fermante
    morceaux = [m.strip() for m in decouper_elements(element, ';') if m.strip()]  # Decoupe les 2 valeurs autour du ; puis nettoie
    if len(morceaux) >= 2:  # Verifie qu'on a bien au moins 2 valeurs
        base_donnees.ajouter_inversion(morceaux[0], morceaux[1])  # Ajoute l'inversion dans la base : valeur 1 <-> valeur 2

def traiter_unite(element, base_donnees):  # Fonction qui traite une ligne du bloc unite{...}
    element = element.strip()  # Enleve les espaces inutiles
    if '(' not in element or not element.endswith(')'):  # Verifie que le format ressemble bien a M(30;J)
        return  # Si le format est incorrect, on sort sans rien faire
    nom = normaliser_nom(element.split('(', 1)[0])  # Recupere le nom de l'unite avant la parenthese, par exemple M
    contenu = element[element.find('(') + 1:-1]  # Recupere ce qu'il y a dans les parentheses, par exemple 30;J
    morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]  # Decoupe le contenu en morceaux propres
    if len(morceaux) >= 2:  # Verifie qu'on a bien un facteur et une unite inferieure
        facteur = reel_ou_defaut(morceaux[0], 1)  # Convertit le facteur en nombre, sinon met 1 par defaut
        unite_du_dessous = normaliser_nom(morceaux[1])  # Recupere le nom de l'unite inferieure, par exemple J
        base_donnees.ajouter_unite(nom, unite_du_dessous, facteur)  # Ajoute l'unite dans la base

def decouper_elements(contenu, separateur=';'):
    # Découpe le contenu par un séparateur en ignorant les séparateurs à l'intérieur de () ou {}
    elements = [] # Liste des éléments découpés
    courant = '' # Accumule les caractères de l'élément courant
    profondeur = 0 # Compte la profondeur des () et {}
    for caractere in contenu:
        # Si c'est une parenthèse/accolade est ouvrante on augmente la profondeur
        if caractere in '({':
            profondeur += 1
        # et si elle est fermante on la diminue
        elif caractere in ')}':
            profondeur -= 1
        # Si on trouve le séparateur et qu'on n'est pas à l'intérieur de () ou {}, c'est la fin d'un élément
        if caractere == separateur and profondeur == 0:
            if courant.strip(): # Si l'élément n'est pas vide on l'ajoute à la liste
                elements.append(courant.strip())
            courant = ''  # On réinitialise pour le prochain élément
        else:
            courant += caractere # Sinon on ajoute le caractère à l'élément courant
    # Ajoute le dernier élément s'il existe
    if courant.strip(): 
        elements.append(courant.strip())
    return elements # Retourne la liste des éléments découpés


def normaliser_nom(texte):
    # Enlève les espaces au début/fin et remplace les espaces internes par des underscores
    return texte.strip().replace(' ', '_')


def type_depuis_valeur(valeur):
    # Détermine le type d'une valeur (int, float ou texte)
    texte = str(valeur).strip().replace(',', '.') # Convertit en str et remplace les décimales
    try:
        int(texte) # Essaie de convertir en entier
        return 'int'
    except Exception:
        pass # Si ça échoue on continue
    try:
        float(texte) # Essaie de convertir en float
        return 'float'
    except Exception:
        return 'texte' # Si ça échoue c'est du texte


def executer_code(texte, base_donnees, nom_table_defaut):
    # Exécute le code de configuration
    bilan = [] # Liste pour vérifier ce qui a été créé/modifié
    configuration_sim = {} # Dictionnaire pour stocker les paramètres de simulation
    # Extrait les blocs du texte et les exécute
    _executer_blocs(extraire_blocs(texte), base_donnees, nom_table_defaut, bilan, configuration_sim)
    return bilan # Retourne le bilan des actions effectuées


def _executer_blocs(blocs, base_donnees, table_active, bilan, configuration_sim):
    # Exécute chaque bloc extrait du texte et appelle des fonctions différentes selon le type de bloc
    for prefixe, contenu in blocs: # Pour chaque bloc (un préfixe et un contenu)
        prefixe = prefixe.strip()
        prefixe_normalise = normaliser_nom(prefixe)
        # Bloc Table
        if prefixe in ('tab', 't.'): # Si le bloc commence par 'tab' ou raccourci 't.'
            for element in decouper_elements(contenu, ';'):
                nom_table, colonnes = analyser_expression_table(element)
                # Vérifie si la table existe déjà dans la base de données
                if base_donnees.table_existe(nom_table):
                    table_active = nom_table
                    bilan.append('table deja presente : ' + nom_table)
                else:
                    # Crée la table avec ses colonnes dans la base de données
                    base_donnees.creer_table_nsi(nom_table, 0, colonnes)
                    table_active = nom_table
                    bilan.append('table creee : ' + nom_table)
            continue # Passe au bloc suivant
        # Bloc Colonne
        if prefixe == 'col' or prefixe.startswith('c.'): # Si le bloc commence par 'col' ou raccourci 'c.'
            # Détermine quelle table cibler
            table_cible = determiner_table_col(prefixe, table_active) 
            for element in decouper_elements(contenu, ';'):
                traiter_colonne(element, table_cible, base_donnees, bilan)
            continue
        # Bloc Objets
        if prefixe == 'obj' or prefixe.startswith('o.'): # Si le bloc commence par 'obj' ou raccourci 'o.'
            table_cible = determiner_table_obj(prefixe, table_active)
            for element in decouper_elements(contenu, ';'):
                element = element.strip()
                if element == '':
                    continue
                # Si c'est une liaison (=> ou <=>), on traite comme une liaison et pas comme un objet
                if '=>' in element or '<=>' in element:
                    total = ajouter_liaisons_texte(element, base_donnees, table_cible)
                    bilan.append('liaisons ajoutees : ' + str(total))
                else:
                    # Sinon on l'ajoute comme objet simple
                    ajouter_objet_rapide(element, table_cible, base_donnees)
                    bilan.append('objet ajoute : ' + element)
            continue
        # Bloc Composition
        if prefixe == 'cp': # Si le bloc commence par 'cp'
            table_cible = table_active # Par défaut on cible la table active
            for element in decouper_elements(contenu, ';'):
                traiter_composition(element, table_cible, base_donnees)
                bilan.append('composition ajoutee : ' + element)
            continue
        # Bloc Map
        if prefixe == 'map': # Pour ajouter des positions sur une carte
            for element in decouper_elements(contenu, ';'): # On peut ajouter plusieurs positions séparées par des ;
                traiter_position(element, base_donnees) # Traite la position et ajoute à la base de données
                bilan.append('position map : ' + element) # bilan de vérification
            continue
        # Bloc Chemin
        if prefixe == 'ch': # itinéraires ou chemins entre objets
            for element in decouper_elements(contenu, ';'):
                traiter_chemin(element, base_donnees)
                bilan.append('chemin ajoute : ' + element)
            continue
        # Bloc Evénement
        if prefixe == 'evt': # événements spéciaux utilisés dans la simulation
            for element in decouper_elements(contenu, ';'):
                traiter_evenement(element, base_donnees)
                bilan.append('evenement ajoute : ' + element)
            continue
        # Bloc Paterne
        if prefixe == 'pat': # comportement répétitif
            for element in decouper_elements(contenu, ';'):
                traiter_paterne(element, base_donnees)
                bilan.append('paterne ajoute : ' + element)
            continue
        # Bloc Simulation
        if prefixe == 'sim': # paramètres de simulation
            for element in decouper_elements(contenu, ';'):
                if '=' in element: # Récupère les paramètres clé=valeur
                    cle, valeur = element.split('=', 1) # Sépare la clé et la valeur
                    configuration_sim[normaliser_nom(cle)] = valeur.strip() # Stocke dans le dictionnaire de configuration
                    bilan.append('simulation : ' + cle.strip() + '=' + valeur.strip())
            continue
        if prefixe == 'inv':  # Verifie si le bloc courant est un bloc inv{...}
            for element in decouper_elements(contenu, ';'):  # Decoupe le contenu du bloc en plusieurs inversions
                traiter_inversion(element, base_donnees)  # Traite chaque inversion individuellement
                bilan.append('inversion ajoutee : ' + element)  # Ajoute une trace dans le bilan
            continue  # Passe directement au bloc suivant
        # Bloc imbriqué (si le contenu contient des blocs intérieurs)

        if prefixe == 'unite':  # Verifie si le bloc courant est un bloc unite{...}
            for element in decouper_elements(contenu, ';'):  # Decoupe le contenu du bloc en plusieurs definitions d'unites
                traiter_unite(element, base_donnees)  # Traite chaque unite individuellement
                bilan.append('unite ajoutee : ' + element)  # Ajoute une trace dans le bilan
            continue  # Passe directement au bloc suivant

        blocs_interieurs = []  # Par defaut, on considere qu'il n'y a pas de sous-blocs
        if '{' in contenu and '}' in contenu:  # On ne tente une extraction que si le texte contient vraiment des accolades
            blocs_interieurs = extraire_blocs(contenu)  # Extrait les sous-blocs seulement si c'est utile
        if blocs_interieurs and prefixe_normalise != '':
            table_cible = prefixe_normalise # Utilise le prefixe comme nouveau nom de table
            if not base_donnees.table_existe(table_cible): # Si la table n'existe pas on la crée
                base_donnees.creer_table_nsi(table_cible, 0, []) # On crée la table sans colonne
                bilan.append('table creee : ' + table_cible)
            # Exécute récursivement les blocs intérieurs
            _executer_blocs(blocs_interieurs, base_donnees, table_cible, bilan, configuration_sim) 
            table_active = table_cible
            continue


def analyser_expression_table(element):
    # Analyse une expression de table pour en extraire le nom de la table et les colonnes à créer
    element = element.strip() # Enlève les espaces au début et à la fin
    # Si il n'y a pas de parenthèses, c'est juste un nom de table simple
    if '(' not in element:
        return normaliser_nom(element), []
    # Sinon on extrait le nom et les colonnes définies
    nom_table = normaliser_nom(element.split('(', 1)[0])
    # On récupère tout ce qui est entre les parenthèses
    contenu = element[element.find('(') + 1:-1]
    colonnes = []
    # Découpe par ';' pour avoir chaque colonne
    for morceau in decouper_elements(contenu, ';'):
        if '=' in morceau:
            # Avec un format, colonne=type
            nom_colonne, type_colonne = morceau.split('=', 1)
            colonnes.append((normaliser_nom(nom_colonne), type_colonne.strip().lower(), ''))
        else:
            # Si pas de type spécifié, par défaut c'est 'int'
            colonnes.append((normaliser_nom(morceau), 'int', ''))
    return nom_table, colonnes # Retourne le nom de table et la liste des colonnes


def determiner_table_col(prefixe, table_active):
    # Détermine quelle table cibler pour les colonnes selon le préfixe
    if prefixe.startswith('c.'): # Si le préfixe commence par 'c.', on utilise le nom qui suit comme table cible
        nom_table = normaliser_nom(prefixe[2:])
        # Si le nom est vide après 'c.', on garde la table active
        return nom_table if nom_table else table_active
    # Sinon on retourne la table active
    return table_active


def determiner_table_obj(prefixe, table_active):
    # Même logique que determiner_table_col mais pour les objets
    if prefixe.startswith('o.'): # Si le préfixe commence par 'o.', on utilise le nom qui suit comme table cible
        nom_table = normaliser_nom(prefixe[2:])
        # Si le nom est vide après 'o.', on garde la table active
        return nom_table if nom_table else table_active
    # Sinon on retourne la table active
    return table_active


def traiter_colonne(element, table_cible, base_donnees, bilan):
    # Traite l'ajout d'une colonne à une table
    # 2 formats, "col(val1; val2; val3)" ou "nom_col=type, vd=defaut"
    element = element.strip()
    if element == '':
        return
    # Format 1, (col(val1; val2; val3))
    if '(' in element and element.endswith(')'):
        nom_colonne = normaliser_nom(element.split('(', 1)[0])
        contenu = element[element.find('(') + 1:-1]
        # Extrait les valeurs en enlevant les guillemets
        valeurs = [m.strip().strip('"') for m in decouper_elements(contenu, ';') if m.strip()]
        # Crée la colonne si elle n'existe pas
        if not base_donnees.colonne_existe(table_cible, nom_colonne):
            base_donnees.ajouter_colonne_table(table_cible, nom_colonne, 'texte', '')
            bilan.append('colonne ajoutee : ' + table_cible + '.' + nom_colonne)
        # Remplit la colonne avec les valeurs
        base_donnees.remplir_colonne_depuis_liste(table_cible, nom_colonne, valeurs)
        bilan.append('valeurs ajoutees : ' + table_cible + '.' + nom_colonne)
        return
    # Format 2, (nom_col=type, vd=defaut)
    # Découpe par ',' pour séparer les différentes parties
    morceaux = [m.strip() for m in decouper_elements(element, ',') if m.strip()]
    if not morceaux:
        return
    # Détermine le nom et le type de la colonne
    premier = morceaux[0]
    if '=' in premier: # Si il y a un '=', on suppose que c'est "nom_col=type"
        nom_colonne, type_colonne = premier.split('=', 1)
        nom_colonne = normaliser_nom(nom_colonne)
        type_colonne = type_colonne.strip().lower() # On convertit le type en minuscules pour éviter les problèmes de casse
    else:
        nom_colonne = normaliser_nom(premier)
        type_colonne = 'int' # Par défaut c'est 'int'
    valeur_defaut = '' # Initialise la valeur par défaut
    # Cherche s'il y a un paramètre "vd=" (vd = valeur défaut)
    for morceau in morceaux[1:]:
        if morceau.startswith('vd='): # Si le morceau commence par 'vd=', on extrait la valeur par défaut
            valeur_defaut = morceau.split('=', 1)[1].strip()
    # Si la colonne n'existe pas déjà, on l'ajoute à la table
    if not base_donnees.colonne_existe(table_cible, nom_colonne):
        base_donnees.ajouter_colonne_table(table_cible, nom_colonne, type_colonne, valeur_defaut)
        bilan.append('colonne ajoutee : ' + table_cible + '.' + nom_colonne)


def ajouter_objet_rapide(texte_objet, table_active, base_donnees):
    # Ajoute rapidement un objet à la table, avec 3 formats différents
    texte_objet = texte_objet.strip()
    if texte_objet == '':
        return

    donnees = {'nom': ''} # Initiailise les données de l'objet
    # Format 1, clé=valeur
    if '(' not in texte_objet and '=' in texte_objet:
        gauche, droite = texte_objet.split('=', 1)
        donnees['nom'] = gauche.strip()
        # Si la table a une colonne "valeur", met le nombre
        if 'valeur' in base_donnees.colonnes_physiques(table_active):
            donnees['valeur'] = reel_ou_defaut(droite, 0) # fonction importée de outils_nsi
        else:
            # Sinon, met le texte dans la première colonne remplissable
            remplissables = base_donnees.colonnes_remplissables(table_active)
            if remplissables:
                donnees[remplissables[0]] = droite.strip().strip('"')
        base_donnees.ajouter_objet_table(table_active, donnees)
        return
    # Format 2, variable(x=valeur, y=valeur)
    if '(' in texte_objet and texte_objet.endswith(')'):
        nom = texte_objet.split('(', 1)[0].strip()
        donnees['nom'] = nom
        contenu = texte_objet[texte_objet.find('(') + 1:-1]
        morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
        positionnels = [] # Pour les valeurs sans nom de colonne, on les met dans une liste pour les traiter après
        # Pour chaque morceau, on vérifie s'il a un format clé=valeur ou s'il est positionnel
        for morceau in morceaux:
            if '=' in morceau:
                # C'est un paramètre clé=valeur
                cle, valeur = morceau.split('=', 1)
                nom_colonne = normaliser_nom(cle)
                valeur = valeur.strip().strip('"')
                # Si la colonne n'existe pas, on la crée
                if nom_colonne not in base_donnees.colonnes_physiques(table_active):
                    base_donnees.ajouter_colonne_table(table_active, nom_colonne, type_depuis_valeur(valeur), '')
                donnees[nom_colonne] = valeur
            else:
                # Sinon c'est une valeur positionnelle (sans nom de colonne)
                positionnels.append(morceau.strip().strip('"'))
        # Remplit les valeurs positionnelles dans les colonnes remplissables
        colonnes_cibles = base_donnees.colonnes_remplissables(table_active)
        for index, valeur in enumerate(positionnels):
            if index >= len(colonnes_cibles):
                break
            donnees[colonnes_cibles[index]] = valeur
    else:
        # Format 3, juste un nom d'objet simple
        donnees['nom'] = texte_objet
    # Ajoute l'objet à la table
    base_donnees.ajouter_objet_table(table_active, donnees)


def developper_groupes(texte):
    # Convertit un groupe en liste d'éléments
    texte = texte.strip()
    # Si le texte est entre parenthèses, c'est un groupe
    if texte.startswith('(') and texte.endswith(')'):
        interieur = texte[1:-1].replace(' ', ';').replace(',', ';') # Normalise les séparateurs
        # Découpe et retourne comme liste
        return [m.strip() for m in decouper_elements(interieur, ';') if m.strip()]
    # Sinon c'est un élément unique
    return [texte]


def lire_conservation(element):
    # Lit les paramètres de conservation et de poids dans une expression d'objet ou de liaison, "A, p=0.5, c=y" > ("A", 0.5, "y")
    morceaux = [m.strip() for m in decouper_elements(element, ',') if m.strip()]
    conservation = 'n' # Par défaut, pas de conservation 
    poids = 1 # Par défaut, probabilité de 100%
    # Cherche les paramètres optionnels
    for morceau in morceaux[1:]:
        # p = probabilité
        if morceau.startswith('p='):
            poids = reel_ou_defaut(morceau.split('=', 1)[1], 1)
             # Valide que la probabilité est entre 0 et 1
            if poids < 0 or poids > 1:
                raise ValueError('La probabilite doit etre entre 0 et 1')
        elif morceau.startswith('c=') or morceau.startswith('n=') or morceau.startswith('conservation='):
            # c/n/conservation = type de conservation
            conservation = morceau.split('=', 1)[1].strip()
    # Retourne le 1er élément, son poids, et le type de conservation
    return morceaux[0], poids, conservation


def ajouter_liaisons_texte(texte, base_donnees, table_active):
    # Ajoute des liaisons entre objets
    texte = texte.strip()
    type_liaison = '<=>' # Par défaut bidirectionnel
    separateur = '<=>'
    # Détecte si c'est unidirectionnel (=>) ou bidirectionnel (<=>)
    if '<=>' not in texte:
        type_liaison = '=>'
        separateur = '=>'
    # Découpe par le séparateur pour avoir les paires d'éléments
    chaines = [m.strip() for m in texte.split(separateur) if m.strip()]
    compteur = 0
    # Crée les liaisons entre chaque paire d'éléments
    for i in range(len(chaines) - 1):
        # Récupère la source (1er élément de la paire)
        sources = developper_groupes(lire_conservation(chaines[i])[0])
        # Récupère la cible et ses paramètres (2ème élément)
        cible_brute, poids, conservation = lire_conservation(chaines[i + 1])
        cibles = developper_groupes(cible_brute)
        # Crée une liaison entre chaque source et chaque cible
        for source in sources:
            # Si la source n'existe pas, on la crée
            if base_donnees.objet_global_par_nom(source) is None:
                ajouter_objet_rapide(source, table_active, base_donnees)
            for cible in cibles:
                # Si la cible n'existe pas, on la crée
                if base_donnees.objet_global_par_nom(cible) is None:
                    ajouter_objet_rapide(cible, table_active, base_donnees)
                # Ajoute la liaison
                base_donnees.ajouter_liaison(source, cible, type_liaison, poids, conservation)
                compteur += 1
    return compteur # Retourne le nombre de liaisons ajoutées


def traiter_composition(element, table_cible, base_donnees):
    # Traite la composition, un objet parent contient des objets enfants, parent(enfant1, enfant2(3), enfant3)
    parent = element.split('(', 1)[0].strip()
    # Crée le parent s'il n'existe pas
    if base_donnees.objet_global_par_nom(parent) is None:
        ajouter_objet_rapide(parent, table_cible, base_donnees)
    # Extrait le contenu entre parenthèses pour avoir les enfants
    contenu = element[element.find('(') + 1:-1]
    # Boucle sur chaque enfant
    for morceau in decouper_elements(contenu, ','):
        quantite = 1
        enfant = morceau.strip()
        # Vérifie si la quantité est spécifiée (enfant(3) signifie 3 unités de cet enfant)
        if '(' in enfant and enfant.endswith(')'):
            nom_enfant = enfant.split('(', 1)[0].strip()
            quantite = entier_ou_defaut(enfant[enfant.find('(') + 1:-1], 1)
            enfant = nom_enfant
        # Crée l'enfant s'il n'existe pas
        if base_donnees.objet_global_par_nom(enfant) is None:
            ajouter_objet_rapide(enfant, table_cible, base_donnees)
        # Ajoute la composition
        base_donnees.ajouter_composition(parent, enfant, quantite)
        # Essaie aussi d'ajouter une liaison de l'enfant vers le parent
        try:
            base_donnees.ajouter_liaison(enfant, parent, '=>', 1, 'n')
        except Exception:
            pass # Si ça échoue, on ignore


def traiter_position(element, base_donnees):
    # Positionne un objet sur une carte avec des coordonnées x,y, format: objet(x=valeur, y=valeur)
    nom_objet = element.split('(', 1)[0].strip()
    # Cherche l'objet dans la base de données
    if base_donnees.objet_global_par_nom(nom_objet) is None:
        return # L'objet n'existe pas, on sort
    objet = base_donnees.objet_global_par_nom(nom_objet)
    # Extrait les paramètres entre parenthèses
    contenu = element[element.find('(') + 1:-1]
    x = 0
    y = 0
    # Boucle sur les paramètres pour trouver x et y
    for morceau in decouper_elements(contenu, ','):
        if '=' in morceau:
            cle, valeur = morceau.split('=', 1)
            cle = cle.strip().lower()
            if cle == 'x':
                x = reel_ou_defaut(valeur, 0)
            elif cle == 'y':
                y = reel_ou_defaut(valeur, 0)
    # Enregistre la position (noter l'ordre: id, latitude, longitude, ...)
    base_donnees.enregistrer_position(objet['id'], y, x, '')


def traiter_chemin(element, base_donnees):
    # Crée un chemin/itinéraire avec une séquence de points ou d'objets, format: chemin1(px(10, 20); mon_objet; pt(x=5, y=15))
    nom = element.split('(', 1)[0].strip() # Récupère le nom du chemin
    contenu = element[element.find('(') + 1:-1] # Extrait le contenu entre parenthèses
    etapes = [] # Liste des points du chemin
    index_point = 1 # Compteur pour nommer les points générés
    # Boucle sur chaque étape du chemin
    for morceau in decouper_elements(contenu, ';'):
        morceau = morceau.strip()
        if morceau == '':
            continue
        # Vérifie si c'est un point explicite: px() ou pt()
        if (morceau.startswith('px(') or morceau.startswith('pt(')) and morceau.endswith(')'):
            # Extrait les coordonnées à l'intérieur des parenthèses
            interieur = morceau[morceau.find('(') + 1:-1]
            x = None
            y = None
            # Découpe les coordonnées (séparées par ; ou ,)
            morceaux_interieurs = [m.strip() for m in re.split(r'[;,]', interieur) if m.strip()]
            # Vérifie si les coordonnées sont nommées (x=valeur, y=valeur)
            if any('=' in m for m in morceaux_interieurs):
                for valeur in morceaux_interieurs:
                    if '=' in valeur:
                        cle, contenu_valeur = valeur.split('=', 1)
                        cle = cle.strip().lower()
                        if cle == 'x':
                            x = reel_ou_defaut(contenu_valeur, 0)
                        elif cle == 'y':
                            y = reel_ou_defaut(contenu_valeur, 0)
            # Sinon c'est des valeurs positionnelles, première = x, deuxième = y
            elif len(morceaux_interieurs) >= 2:
                x = reel_ou_defaut(morceaux_interieurs[0], 0)
                y = reel_ou_defaut(morceaux_interieurs[1], 0)
            # Si on a trouvé x et y, l'ajoute à la liste des étapes  
            if x is not None and y is not None:
                etapes.append({'type': 'point', 'nom': 'px' + str(index_point), 'x': x, 'y': y})
                index_point += 1
            continue
        # Sinon, c'est le nom d'un objet dont on doit récupérer la position
        objet = base_donnees.objet_global_par_nom(morceau)
        if objet is not None:
            # Cherche la position de l'objet dans la base de données
            position = base_donnees.position_par_objet(objet['id'])
            if position is not None:
                # Ajoute l'objet comme étape (utilise sa position)
                etapes.append({'type': 'objet', 'nom': morceau, 'x': float(position['longitude']), 'y': float(position['latitude'])})
    # Valide qu'il y a au moins 2 points
    if len(etapes) < 2:
        raise ValueError('Le chemin doit contenir au moins deux points ou objets deja positionnes')
    # Enregistre le chemin dans la base de données
    base_donnees.ajouter_chemin(nom, etapes)


def traiter_evenement(element, base_donnees):
    # Quand un objet change, ça déclenche une action sur un autre objet, format: evt1(obj1=source, col=valeur, test=>, si=5, obj2=cible, col_effet=valeur, action=op, op=+1, p=0.8)
    nom = element.split('(', 1)[0].strip() # Récupère le nom de l'événement
    contenu = element[element.find('(') + 1:-1] # Extrait le contenu entre parenthèses
    parametres = {} # Dictionnaire pour stocker les paramètres de l'événement
    morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
    index_obj = 0 # Compteur pour les objets nommés (obj1, obj2, obj3...)
    # Boucle sur les morceaux pour extraire les paramètres clé=valeur
    for morceau in morceaux:
        if '=' not in morceau:
            continue
        cle, valeur = morceau.split('=', 1)
        cle = cle.strip().lower()
        valeur = valeur.strip()
        # Les paramètres "obj=" se numérotent automatiquement en obj1, obj2...
        if cle == 'obj':
            index_obj += 1
            parametres['obj' + str(index_obj)] = valeur
        else:
            parametres[cle] = valeur
    # Récupère l'objet cause (celui dont on regarde le changement), cherche d'abord obj1 sinon cause
    nom_cause = parametres.get('obj1', parametres.get('cause', ''))
    # Récupère l'objet effet (celui sur lequel on agit), cherche d'abord obj2 sinon effet
    nom_effet = parametres.get('obj2', parametres.get('effet', ''))
    # Cherche les objets dans la base de données
    objet_cause = base_donnees.objet_global_par_nom(nom_cause)
    objet_effet = base_donnees.objet_global_par_nom(nom_effet)
    # Vérifie que les deux objets existent dans la base de données, sinon on ne peut pas créer l'événement
    if objet_cause is None or objet_effet is None:
        raise ValueError("Objet introuvable pour l'evenement : " + element)
    # CONDITION (qu'est-ce qui déclenche l'événement ?)
    # Colonne à surveiller (par défaut "valeur")
    colonne_cause = parametres.get('col', parametres.get('col_cause', 'valeur'))
    # Opérateur de comparaison (par défaut "=")
    operateur = parametres.get('test', parametres.get('operateur', '='))
    # Valeur de condition (par défaut "0")
    valeur_cause = parametres.get('si', parametres.get('valeur_cause', parametres.get('condition', '0')))
    # ACTION (qu'est-ce qui se passe quand l'événement se déclenche ?)
    # Colonne à modifier (par défaut la même que celle surveillée)
    colonne_effet = parametres.get('col_effet', colonne_cause if colonne_cause in ('valeur', 'etat') else 'valeur')
    # Type d'action (par défaut "op" = opération)
    action = parametres.get('action', parametres.get('change', 'op'))
    # # Si "change" est présent en paramètre, on considère que c'est une action de type "change" même si le paramètre "action" est à "op"
    if 'change' in parametres and action == 'op':
        action = 'change'
    # Valeur/opération à appliquer (par défaut "+1")
    valeur_effet = parametres.get('op', parametres.get('change', parametres.get('valeur_effet', '+1')))
    # PARAMÈTRES ADDITIONNELS, probabilité que l'événement se déclenche (par défaut 100%)
    proba = reel_ou_defaut(parametres.get('p', parametres.get('proba', '1')), 1)
    if proba < 0 or proba > 1:
        raise ValueError('La probabilite doit etre entre 0 et 1')
    # Délai avant le déclenchement (par défaut 0)
    arrivee = entier_ou_defaut(parametres.get('arrivee', '0'), 0)
    # Propagation: "all" = affecte tous les objets connectés, ou un nombre
    propagation_texte = parametres.get('propagation', '0').strip().lower()
    propagation = -1 if propagation_texte == 'all' else entier_ou_defaut(propagation_texte, 0)
    # Enregistre l'événement dans la base de données
    base_donnees.ajouter_evenement(nom, objet_cause['id'], colonne_cause, operateur, valeur_cause, objet_effet['id'], colonne_effet, action, valeur_effet, proba, arrivee, propagation)


def traiter_paterne(element, base_donnees):
    # Cette fonction lit une definition de paterne en Frank SQL
    # Exemple attendu :
    # HaussePetrole(objet=Petrole,colonne=prix,action=op,valeur=+1,frequence=1s)
    element = element.strip()  # nettoie le texte
    if element == '':
        return 'Paterne vide.'
    # verifie qu'on a bien des parentheses
    if '(' not in element or ')' not in element:
        return 'Syntaxe paterne invalide : ' + element
    # recupere le nom du paterne
    position_ouv = element.find('(')
    position_ferm = element.rfind(')')
    nom = element[:position_ouv].strip()  # nom du paterne
    contenu = element[position_ouv + 1:position_ferm].strip()  # texte entre parentheses
    if nom == '':
        return 'Nom du paterne manquant.'
    # transforme le contenu en dictionnaire de parametres
    # exemple :
    # objet=Petrole,colonne=prix,action=op,valeur=+1,frequence=1s
    # devient :
    # {
    #   'objet': 'Petrole',
    #   'colonne': 'prix',
    #   'action': 'op',
    #   'valeur': '+1',
    #   'frequence': '1s'
    # }
    parametres = {}
    morceaux = contenu.split(',')
    for morceau in morceaux:
        morceau = morceau.strip()
        if morceau == '':
            continue
        if '=' not in morceau:
            continue
        cle, valeur = morceau.split('=', 1)
        cle = cle.strip().lower()
        valeur = valeur.strip()
        parametres[cle] = valeur
    # recupere les champs principaux
    nom_objet = parametres.get('objet', parametres.get('cible', '')).strip()
    colonne_effet = parametres.get('colonne', parametres.get('champ', 'valeur')).strip()
    action = parametres.get('action', 'op').strip()
    valeur_effet = parametres.get('valeur', '+1').strip()
    frequence = parametres.get('frequence', parametres.get('f', '1')).strip() or '1'
    if nom_objet == '':
        return 'Objet manquant pour le paterne : ' + element
    # recherche de l'objet par son nom
    # cherche l'objet dans le catalogue global (comme les liaisons)
    objet = base_donnees.objet_global_par_nom(nom_objet)
    if objet is None:
        return 'Objet introuvable pour le paterne : ' + nom_objet
    # ajoute le paterne en base
    base_donnees.ajouter_paterne(
        nom,
        objet['id'],
        colonne_effet,
        action,
        valeur_effet,
        frequence
    )

    return 'Paterne ajoute : ' + nom