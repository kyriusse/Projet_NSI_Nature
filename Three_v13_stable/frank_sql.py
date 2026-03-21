from __future__ import annotations

import html
import re

from outils_nsi import entier_ou_defaut, reel_ou_defaut


def colorer_code(texte):
    resultat = html.escape(texte)
    resultat = re.sub(r'(^|<br>)\s*#([^<]*)', lambda m: m.group(1) + "<span class='com'>#" + m.group(2) + '</span>', resultat)
    mots = ['tab', 'col', 'obj', 'cp', 'evt', 'pat', 'map', 'sim', 'unite', 'ch', 'vd', 'obj=', 'col=', 'tab=', 'op=', 'change=', 'inv', 'act', 'dsc', 'lat=', 'long=', 'x=', 'y=', 't.', 'c.', 'o.','unite']
    for mot in mots:
        resultat = resultat.replace(mot, "<span class='kw'>" + mot + '</span>')
    resultat = re.sub(r'(?<![\w>])(\d+(?:[\.,]\d+)?)', r"<span class='num'>\1</span>", resultat)#ligne généré avec une IA (Générée et Expliquée par Copilote)
    return resultat.replace('\n', '<br>')


def nettoyer_texte(texte):
    lignes = []
    for ligne in texte.splitlines():
        propre = ligne.strip()
        if propre and not propre.startswith('#'):
            lignes.append(propre)
    return '\n'.join(lignes)


def extraire_blocs(texte):
    texte = nettoyer_texte(texte)
    blocs = []
    indice = 0
    while indice < len(texte):
        while indice < len(texte) and texte[indice].isspace():
            indice += 1
        if indice >= len(texte):
            break
        debut = indice
        while indice < len(texte) and (texte[indice].isalnum() or texte[indice] in '._'):
            indice += 1
        prefixe = texte[debut:indice].strip()
        while indice < len(texte) and texte[indice].isspace():
            indice += 1
        if indice >= len(texte) or texte[indice] != '{':
            fin_ligne = texte.find('\n', debut)
            if fin_ligne == -1:
                fin_ligne = len(texte)
            blocs.append((prefixe, texte[debut:fin_ligne].strip()))
            indice = fin_ligne + 1
            continue
        profondeur = 0
        debut_contenu = indice + 1
        while indice < len(texte):
            if texte[indice] == '{':
                profondeur += 1
            elif texte[indice] == '}':
                profondeur -= 1
                if profondeur == 0:
                    contenu = texte[debut_contenu:indice]
                    blocs.append((prefixe, contenu.strip()))
                    indice += 1
                    break
            indice += 1
    return blocs

def traiter_fusion(element, table_cible, base_donnees):
    parent = element.split('(', 1)[0].strip()
    if parent == '':
        raise ValueError('Fusion invalide : ' + element)
    if base_donnees.objet_global_par_nom(parent) is None:
        ajouter_objet_rapide(parent, table_cible, base_donnees)
    contenu = element[element.find('(') + 1:-1]
    for morceau in decouper_elements(contenu, ';'):
        quantite = 1
        enfant = morceau.strip()
        if enfant == '':
            continue
        if '(' in enfant and enfant.endswith(')'):
            nom_enfant = enfant.split('(', 1)[0].strip()
            quantite = entier_ou_defaut(enfant[enfant.find('(') + 1:-1], 1)
            enfant = nom_enfant
        if base_donnees.objet_global_par_nom(enfant) is None:
            ajouter_objet_rapide(enfant, table_cible, base_donnees)
        base_donnees.ajouter_composition(parent, enfant, quantite)
        try:
            base_donnees.ajouter_liaison(enfant, parent, '=>', 1, 'n')
        except Exception:
            pass

def traiter_suppression(element, table_active, base_donnees):
    element = element.strip()
    if element == '':
        return
    parametres = {}
    morceaux = [m.strip() for m in decouper_elements(element, ',') if m.strip()]

    if len(morceaux) == 1 and '=' not in morceaux[0]:
        base_donnees.supprimer_objet_par_nom(morceaux[0])
        return

    for morceau in morceaux:
        if '=' in morceau:
            cle, valeur = morceau.split('=', 1)
            parametres[cle.strip().lower()] = valeur.strip()

    if 'obj' in parametres:
        base_donnees.supprimer_objet_par_nom(parametres['obj'])
        return

    if 'tab' in parametres:
        base_donnees.supprimer_table_nsi(normaliser_nom(parametres['tab']))
        return

    if 'ch' in parametres:
        nom = parametres['ch']
        for chemin in base_donnees.liste_chemins():
            if chemin['nom'] == nom:
                base_donnees.supprimer_chemin(chemin['id'])
                return
        return

    if 'inv' in parametres:
        valeur = parametres['inv'].strip()
        if valeur.startswith('(') and valeur.endswith(')'):
            contenu = valeur[1:-1]
            morceaux_inv = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
            if len(morceaux_inv) == 2:
                for ligne in base_donnees.liste_inversions():
                    a = str(ligne['valeur_0']).strip()
                    b = str(ligne['valeur_1']).strip()
                    if (a == morceaux_inv[0] and b == morceaux_inv[1]) or (a == morceaux_inv[1] and b == morceaux_inv[0]):
                        base_donnees.supprimer_inversion(ligne['id'])
                        return
        return

    if 'unite' in parametres:
        nom = normaliser_nom(parametres['unite'])
        raise ValueError('Suppression unite non activee pour le moment : ' + nom)

def decouper_elements(contenu, separateur=';'):
    elements = []
    courant = ''
    profondeur = 0
    for caractere in contenu:
        if caractere in '({':
            profondeur += 1
        elif caractere in ')}':
            profondeur -= 1
        if caractere == separateur and profondeur == 0:
            if courant.strip():
                elements.append(courant.strip())
            courant = ''
        else:
            courant += caractere
    if courant.strip():
        elements.append(courant.strip())
    return elements


def normaliser_nom(texte):
    return texte.strip().replace(' ', '_')


def type_depuis_valeur(valeur):
    texte = str(valeur).strip().replace(',', '.')
    try:
        int(texte)
        return 'int'
    except Exception:
        pass
    try:
        float(texte)
        return 'float'
    except Exception:
        return 'texte'

def traiter_inversion(element, base_donnees):
    element = element.strip()

    if element == '':
        return

    if not (element.startswith('(') and element.endswith(')')):
        raise ValueError('Syntaxe inv invalide : ' + element)

    contenu = element[1:-1]
    morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]

    if len(morceaux) != 2:
        raise ValueError('Une inversion doit contenir exactement 2 valeurs : ' + element)

    valeur_0 = morceaux[0]
    valeur_1 = morceaux[1]

    base_donnees.ajouter_inversion(valeur_0, valeur_1)


def traiter_unite(element, base_donnees):
    element = element.strip()
    if element == '':
        return
    if '(' not in element or not element.endswith(')'):
        raise ValueError('Syntaxe unite invalide : ' + element)
    nom_unite = normaliser_nom(element.split('(', 1)[0].strip())
    contenu = element[element.find('(') + 1:-1]
    morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
    if len(morceaux) != 2:
        raise ValueError('Une unite doit etre de la forme unite(facteur;unite_cible) : ' + element)
    facteur = reel_ou_defaut(morceaux[0], None)
    cible = normaliser_nom(morceaux[1])
    if facteur in (None, ''):
        raise ValueError('Facteur invalide pour l unite : ' + element)
    if cible == '':
        raise ValueError('Unite cible invalide : ' + element)
    if nom_unite == cible:
        base_donnees.ajouter_unite(nom_unite, None, facteur)
        return
    base_donnees.ajouter_unite(nom_unite, cible, facteur)


def executer_code(texte, base_donnees, nom_table_defaut):
    bilan = []
    configuration_sim = {}
    _executer_blocs(extraire_blocs(texte), base_donnees, nom_table_defaut, bilan, configuration_sim)
    return bilan


def _executer_blocs(blocs, base_donnees, table_active, bilan, configuration_sim):
    for prefixe, contenu in blocs:
        prefixe = prefixe.strip()
        prefixe_normalise = normaliser_nom(prefixe)

        if prefixe in ('tab', 't.'):
            for element in decouper_elements(contenu, ';'):
                nom_table, colonnes = analyser_expression_table(element)
                if base_donnees.table_existe(nom_table):
                    table_active = nom_table
                    bilan.append('table deja presente : ' + nom_table)
                else:
                    base_donnees.creer_table_nsi(nom_table, 0, colonnes)
                    table_active = nom_table
                    bilan.append('table creee : ' + nom_table)
            continue

        if prefixe == 'col' or prefixe.startswith('c.'):
            table_cible = determiner_table_col(prefixe, table_active)
            for element in decouper_elements(contenu, ';'):
                traiter_colonne(element, table_cible, base_donnees, bilan)
            continue

        if prefixe == 'obj' or prefixe.startswith('o.'):
            table_cible = determiner_table_obj(prefixe, table_active)
            for element in decouper_elements(contenu, ';'):
                element = element.strip()
                if element == '':
                    continue
                if '=>' in element or '<=>' in element:
                    total = ajouter_liaisons_texte(element, base_donnees, table_cible)
                    bilan.append('liaisons ajoutees : ' + str(total))
                else:
                    ajouter_objet_rapide(element, table_cible, base_donnees)
                    bilan.append('objet ajoute : ' + element)
            continue

        if prefixe == 'cp':
            table_cible = table_active
            for element in decouper_elements(contenu, ';'):
                traiter_composition(element, table_cible, base_donnees)
                bilan.append('composition ajoutee : ' + element)
            continue

        if prefixe == 'fus':
            table_cible = table_active
            for element in decouper_elements(contenu, ';'):
                traiter_fusion(element, table_cible, base_donnees)
                bilan.append('fusion ajoutee : ' + element)
            continue

        if prefixe == 'del':
            for element in decouper_elements(contenu, ';'):
                traiter_suppression(element, table_active, base_donnees)
                bilan.append('suppression : ' + element)
            continue

        if prefixe == 'map':
            for element in decouper_elements(contenu, ';'):
                traiter_position(element, base_donnees)
                bilan.append('position map : ' + element)
            continue

        if prefixe == 'ch':
            for element in decouper_elements(contenu, ';'):
                traiter_chemin(element, base_donnees)
                bilan.append('chemin ajoute : ' + element)
            continue

        if prefixe == 'evt':
            for element in decouper_elements(contenu, ';'):
                traiter_evenement(element, base_donnees)
                bilan.append('evenement ajoute : ' + element)
            continue

        if prefixe == 'pat':
            for element in decouper_elements(contenu, ';'):
                traiter_paterne(element, base_donnees)
                bilan.append('paterne ajoute : ' + element)
            continue

        if prefixe == 'sim':
            for element in decouper_elements(contenu, ';'):
                if '=' in element:
                    cle, valeur = element.split('=', 1)
                    configuration_sim[normaliser_nom(cle)] = valeur.strip()
                    bilan.append('simulation : ' + cle.strip() + '=' + valeur.strip())
            continue

        if prefixe == 'inv':
            for element in decouper_elements(contenu, ';'):
                traiter_inversion(element, base_donnees)
                bilan.append('inversion ajoutee : ' + element)
            continue

        if prefixe == 'unite':
            for element in decouper_elements(contenu, ';'):
                traiter_unite(element, base_donnees)
                bilan.append('unite ajoutee : ' + element)
            continue

        blocs_interieurs = extraire_blocs(contenu)
        if blocs_interieurs and prefixe_normalise != '':
            table_cible = prefixe_normalise
            if not base_donnees.table_existe(table_cible):
                base_donnees.creer_table_nsi(table_cible, 0, [])
                bilan.append('table creee : ' + table_cible)
            _executer_blocs(blocs_interieurs, base_donnees, table_cible, bilan, configuration_sim)
            table_active = table_cible
            continue


def analyser_expression_table(element):
    element = element.strip()
    if '(' not in element:
        return normaliser_nom(element), []
    nom_table = normaliser_nom(element.split('(', 1)[0])
    contenu = element[element.find('(') + 1:-1]
    colonnes = []
    for morceau in decouper_elements(contenu, ';'):
        if '=' in morceau:
            nom_colonne, type_colonne = morceau.split('=', 1)
            colonnes.append((normaliser_nom(nom_colonne), type_colonne.strip().lower(), ''))
        else:
            colonnes.append((normaliser_nom(morceau), 'int', ''))
    return nom_table, colonnes


def determiner_table_col(prefixe, table_active):
    if prefixe.startswith('c.'):
        nom_table = normaliser_nom(prefixe[2:])
        return nom_table if nom_table else table_active
    return table_active


def determiner_table_obj(prefixe, table_active):
    if prefixe.startswith('o.'):
        nom_table = normaliser_nom(prefixe[2:])
        return nom_table if nom_table else table_active
    return table_active


def traiter_colonne(element, table_cible, base_donnees, bilan):
    element = element.strip()
    if element == '':
        return
    if '(' in element and element.endswith(')'):
        nom_colonne = normaliser_nom(element.split('(', 1)[0])
        contenu = element[element.find('(') + 1:-1]
        valeurs = [m.strip().strip('"') for m in decouper_elements(contenu, ';') if m.strip()]
        if not base_donnees.colonne_existe(table_cible, nom_colonne):
            base_donnees.ajouter_colonne_table(table_cible, nom_colonne, 'texte', '')
            bilan.append('colonne ajoutee : ' + table_cible + '.' + nom_colonne)
        base_donnees.remplir_colonne_depuis_liste(table_cible, nom_colonne, valeurs)
        bilan.append('valeurs ajoutees : ' + table_cible + '.' + nom_colonne)
        return

    morceaux = [m.strip() for m in decouper_elements(element, ',') if m.strip()]
    if not morceaux:
        return
    premier = morceaux[0]
    if '=' in premier:
        nom_colonne, type_colonne = premier.split('=', 1)
        nom_colonne = normaliser_nom(nom_colonne)
        type_colonne = type_colonne.strip().lower()
    else:
        nom_colonne = normaliser_nom(premier)
        type_colonne = 'int'
    valeur_defaut = ''
    for morceau in morceaux[1:]:
        if morceau.startswith('vd='):
            valeur_defaut = morceau.split('=', 1)[1].strip()
    if not base_donnees.colonne_existe(table_cible, nom_colonne):
        base_donnees.ajouter_colonne_table(table_cible, nom_colonne, type_colonne, valeur_defaut)
        bilan.append('colonne ajoutee : ' + table_cible + '.' + nom_colonne)


def ajouter_objet_rapide(texte_objet, table_active, base_donnees):
    texte_objet = texte_objet.strip()
    if texte_objet == '':
        return

    donnees = {'nom': ''}

    if '(' not in texte_objet and '=' in texte_objet:
        gauche, droite = texte_objet.split('=', 1)
        donnees['nom'] = gauche.strip()
        if 'valeur' in base_donnees.colonnes_physiques(table_active):
            donnees['valeur'] = reel_ou_defaut(droite, 0)
        else:
            remplissables = base_donnees.colonnes_remplissables(table_active)
            if remplissables:
                donnees[remplissables[0]] = droite.strip().strip('"')
        base_donnees.ajouter_objet_table(table_active, donnees)
        return

    if '(' in texte_objet and texte_objet.endswith(')'):
        nom = texte_objet.split('(', 1)[0].strip()
        donnees['nom'] = nom
        contenu = texte_objet[texte_objet.find('(') + 1:-1]
        morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
        positionnels = []
        for morceau in morceaux:
            if '=' in morceau:
                cle, valeur = morceau.split('=', 1)
                nom_colonne = normaliser_nom(cle)
                valeur = valeur.strip().strip('"')
                if nom_colonne not in base_donnees.colonnes_physiques(table_active):
                    base_donnees.ajouter_colonne_table(table_active, nom_colonne, type_depuis_valeur(valeur), '')
                donnees[nom_colonne] = valeur
            else:
                positionnels.append(morceau.strip().strip('"'))
        colonnes_cibles = base_donnees.colonnes_remplissables(table_active)
        for index, valeur in enumerate(positionnels):
            if index >= len(colonnes_cibles):
                break
            donnees[colonnes_cibles[index]] = valeur
    else:
        donnees['nom'] = texte_objet
    base_donnees.ajouter_objet_table(table_active, donnees)


def developper_groupes(texte):
    texte = texte.strip()
    if texte.startswith('(') and texte.endswith(')'):
        interieur = texte[1:-1].replace(' ', ';').replace(',', ';')
        return [m.strip() for m in decouper_elements(interieur, ';') if m.strip()]
    return [texte]


def lire_conservation(element):
    morceaux = [m.strip() for m in decouper_elements(element, ',') if m.strip()]
    conservation = 'n'
    poids = 1
    for morceau in morceaux[1:]:
        if morceau.startswith('p='):
            poids = reel_ou_defaut(morceau.split('=', 1)[1], 1)
            if poids < 0 or poids > 1:
                raise ValueError('La probabilite doit etre entre 0 et 1')
        elif morceau.startswith('c=') or morceau.startswith('n=') or morceau.startswith('conservation='):
            conservation = morceau.split('=', 1)[1].strip()
    return morceaux[0], poids, conservation


def ajouter_liaisons_texte(texte, base_donnees, table_active):
    texte = texte.strip()
    type_liaison = '<=>'
    separateur = '<=>'
    if '<=>' not in texte:
        type_liaison = '=>'
        separateur = '=>'
    chaines = [m.strip() for m in texte.split(separateur) if m.strip()]
    compteur = 0
    for i in range(len(chaines) - 1):
        sources = developper_groupes(lire_conservation(chaines[i])[0])
        cible_brute, poids, conservation = lire_conservation(chaines[i + 1])
        cibles = developper_groupes(cible_brute)
        for source in sources:
            if base_donnees.objet_global_par_nom(source) is None:
                ajouter_objet_rapide(source, table_active, base_donnees)
            for cible in cibles:
                if base_donnees.objet_global_par_nom(cible) is None:
                    ajouter_objet_rapide(cible, table_active, base_donnees)
                base_donnees.ajouter_liaison(source, cible, type_liaison, poids, conservation)
                compteur += 1
    return compteur


def traiter_composition(element, table_cible, base_donnees):
    parent = element.split('(', 1)[0].strip()
    if base_donnees.objet_global_par_nom(parent) is None:
        ajouter_objet_rapide(parent, table_cible, base_donnees)
    contenu = element[element.find('(') + 1:-1]
    for morceau in decouper_elements(contenu, ','):
        quantite = 1
        enfant = morceau.strip()
        if '(' in enfant and enfant.endswith(')'):
            nom_enfant = enfant.split('(', 1)[0].strip()
            quantite = entier_ou_defaut(enfant[enfant.find('(') + 1:-1], 1)
            enfant = nom_enfant
        if base_donnees.objet_global_par_nom(enfant) is None:
            ajouter_objet_rapide(enfant, table_cible, base_donnees)
        base_donnees.ajouter_composition(parent, enfant, quantite)
        try:
            base_donnees.ajouter_liaison(enfant, parent, '=>', 1, 'n')
        except Exception:
            pass


def traiter_position(element, base_donnees):
    nom_objet = element.split('(', 1)[0].strip()
    if base_donnees.objet_global_par_nom(nom_objet) is None:
        return
    objet = base_donnees.objet_global_par_nom(nom_objet)
    contenu = element[element.find('(') + 1:-1]
    x = 0
    y = 0
    for morceau in decouper_elements(contenu, ','):
        if '=' in morceau:
            cle, valeur = morceau.split('=', 1)
            cle = cle.strip().lower()
            if cle == 'x':
                x = reel_ou_defaut(valeur, 0)
            elif cle == 'y':
                y = reel_ou_defaut(valeur, 0)
    base_donnees.enregistrer_position(objet['id'], y, x, '')


def traiter_chemin(element, base_donnees):
    nom = element.split('(', 1)[0].strip()
    contenu = element[element.find('(') + 1:-1]
    etapes = []
    index_point = 1
    for morceau in decouper_elements(contenu, ';'):
        morceau = morceau.strip()
        if morceau == '':
            continue
        if (morceau.startswith('px(') or morceau.startswith('pt(')) and morceau.endswith(')'):
            interieur = morceau[morceau.find('(') + 1:-1]
            x = None
            y = None
            morceaux_interieurs = [m.strip() for m in re.split(r'[;,]', interieur) if m.strip()]
            if any('=' in m for m in morceaux_interieurs):
                for valeur in morceaux_interieurs:
                    if '=' in valeur:
                        cle, contenu_valeur = valeur.split('=', 1)
                        cle = cle.strip().lower()
                        if cle == 'x':
                            x = reel_ou_defaut(contenu_valeur, 0)
                        elif cle == 'y':
                            y = reel_ou_defaut(contenu_valeur, 0)
            elif len(morceaux_interieurs) >= 2:
                x = reel_ou_defaut(morceaux_interieurs[0], 0)
                y = reel_ou_defaut(morceaux_interieurs[1], 0)
            if x is not None and y is not None:
                etapes.append({'type': 'point', 'nom': 'px' + str(index_point), 'x': x, 'y': y})
                index_point += 1
            continue
        objet = base_donnees.objet_global_par_nom(morceau)
        if objet is not None:
            position = base_donnees.position_par_objet(objet['id'])
            if position is not None:
                etapes.append({'type': 'objet', 'nom': morceau, 'x': float(position['longitude']), 'y': float(position['latitude'])})
    if len(etapes) < 2:
        raise ValueError('Le chemin doit contenir au moins deux points ou objets deja positionnes')
    base_donnees.ajouter_chemin(nom, etapes)


def traiter_evenement(element, base_donnees):
    nom = element.split('(', 1)[0].strip()
    contenu = element[element.find('(') + 1:-1]
    parametres = {}
    morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
    index_obj = 0
    for morceau in morceaux:
        if '=' not in morceau:
            continue
        cle, valeur = morceau.split('=', 1)
        cle = cle.strip().lower()
        valeur = valeur.strip()
        if cle == 'obj':
            index_obj += 1
            parametres['obj' + str(index_obj)] = valeur
        else:
            parametres[cle] = valeur
    nom_cause = parametres.get('obj1', parametres.get('cause', ''))
    nom_effet = parametres.get('obj2', parametres.get('effet', ''))
    objet_cause = base_donnees.objet_global_par_nom(nom_cause)
    objet_effet = base_donnees.objet_global_par_nom(nom_effet)
    if objet_cause is None or objet_effet is None:
        raise ValueError("Objet introuvable pour l'evenement : " + element)
    colonne_cause = parametres.get('col', parametres.get('col_cause', 'valeur'))
    operateur = parametres.get('test', parametres.get('operateur', '='))
    valeur_cause = parametres.get('si', parametres.get('valeur_cause', parametres.get('condition', '0')))
    colonne_effet = parametres.get('col_effet', colonne_cause if colonne_cause in ('valeur', 'etat') else 'valeur')
    action = parametres.get('action', parametres.get('change', 'op'))
    if 'change' in parametres and action == 'op':
        action = 'change'
    valeur_effet = parametres.get('op', parametres.get('change', parametres.get('valeur_effet', '+1')))
    proba = reel_ou_defaut(parametres.get('p', parametres.get('proba', '1')), 1)
    if proba < 0 or proba > 1:
        raise ValueError('La probabilite doit etre entre 0 et 1')
    arrivee = entier_ou_defaut(parametres.get('arrivee', '0'), 0)
    propagation_texte = parametres.get('propagation', '0').strip().lower()
    propagation = -1 if propagation_texte == 'all' else entier_ou_defaut(propagation_texte, 0)
    base_donnees.ajouter_evenement(nom, objet_cause['id'], colonne_cause, operateur, valeur_cause, objet_effet['id'], colonne_effet, action, valeur_effet, proba, arrivee, propagation)


def traiter_paterne(element, base_donnees):
    nom = element.split('(', 1)[0].strip()
    contenu = element[element.find('(') + 1:-1]
    parametres = {}
    morceaux = [m.strip() for m in decouper_elements(contenu, ';') if m.strip()]
    for morceau in morceaux:
        if '=' in morceau:
            cle, valeur = morceau.split('=', 1)
            parametres[cle.strip().lower()] = valeur.strip()
    nom_objet = parametres.get('obj', '')
    objet = base_donnees.objet_global_par_nom(nom_objet)
    if objet is None:
        raise ValueError('Objet introuvable pour le paterne : ' + element)
    colonne_effet = parametres.get('col', parametres.get('col_effet', 'valeur'))
    action = parametres.get('action', 'op')
    if 'change' in parametres and action == 'op':
        action = 'change'
    valeur_effet = parametres.get('op', parametres.get('change', parametres.get('valeur_effet', '+1')))
    frequence = parametres.get('f', parametres.get('frequence', '1')).strip()
    if frequence == '':
        frequence = '1'
    base_donnees.ajouter_paterne(nom, objet['id'], colonne_effet, action, valeur_effet, frequence)
