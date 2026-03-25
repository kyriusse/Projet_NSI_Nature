**Présentation du modèle**


***TREE***


**Présentation globale**

Ce projet a été réalisé par Armand Jardiller-Dexpert / Eguzki Bailli-ayrault / Romain Lacornette / Tom Anglade / en classe de NSI du Lycée Champollion avec l'aide de Mr Jalras enseignant. L’idée était de relier la nature et l'informatique en utilisant des graphes pour représenter des interactions entre différents éléments pour par la suite potentiellement prédire les conséquences de ceux-ci sur la nature.

Enfaite l'idée vient de quelque choses de beaucoup plus complexe. Depuis le début de l'année de NSI, nous associons le programme à des choses du quotidien un peu comme une blague. Après la réalisation d'un projet sur le SQL, Privealy, permettant d'obtenir le prix moyen de n'importe quel objet et de simuler son évolution sur 20 ans. Nous avons eu l'envie de pousser le projet plus loin en créant une vrai simulation économique. Nous nous sommes rendu compte que ceux qui impacter le plus l'économie était l'environnement. Aussi, cela est réciproque, alors apprenant le thèmes des trophées NSI, nous nous sommes lancés dans l'amélioration de cette simulation. Plus on avancé, plus on voulait être réaliste, plus le projet devenait un enfer. On a donc décidé, de tout généraliser. Avant ça nous avons beaucoup réfléchit sur nos observations des liens entre notre monde / quotidien et le programme de NSI, du lien entre l'économie et la nature et voici ceux que nous avons conclu :

Il n'y a pas de différence entre la nature et l'Homme car il en fait partie. Le point commun entre l'Homme et la nature, c'est cette capacité à détruire et construire, capacité régit par le temps. Ainsi, pour nous, la nature constitue cette enchaînement de cause et conséquence dans le temps. L'Homme s'inspire de l'environnement pour créer et détruire (ex : les avions en forme d'oiseaux). L'informatique n'échappe pas à cette inspiration. Alors nous, nous ferons de même avec cette simulation, et en l'honneur de cette nature, en l'honneur de l'informatique, en l'honneur de tout ces lien, nous avons décidé d'appeler ce projet, Tree (Arbre).



Les 3 premiers grands objectifs étaient:

\-créer des objets avec une valeur et un état

\-relier ces objets avec un graphe

\-simuler des interactions avec des événements

Ensuite 3 autres devaient venir :

\-Pouvoir partager nos simulation et avoir notre propre langage, le Frank SQL 

\-Pouvoir simuler et créer n'importe quelle BDD.

\-Avoir des résultats visuelles / Pouvoir positionner ces objets dans un espace simuler (on appelé ça, les objets réels).


**Présentation de l'équipe**

Nous sommes 4 élèves de terminal :

Armand Jardiller-Dexpert
Eguzki Bailli-ayrault 
Romain Lacornette 
Tom Anglade

Chaque membre a pu aider sur tous les points du projet mais se sont majoritairement occupés de:
deux personnes sur le développement de fonctions pour le site avec une tentative de créer une carte dynamique (en vain, mais finit 2 jours avant) ( Eguzki et Romain )
deux personne sur le site Flask ainsi que la présentation du site etc... ( Armand et Tom )

Le temps passé sur le projet sachant que chacun travail en classe ou à la maison s'élève à quelques dizaines de dizaines d'heures réparties sur presque 6 mois.
Rien n'était statique, tout le monde est intervenut sur le travail d'un autre. Si on simplifie on aurait à peu près ça :

- Vue d'ensemble / Théorique -> Armand
- Contraintes SGBD / Toutes les fonctions autour d'une BDD -> Eguzki
- Grammaire du code et code fonctionnelle / Page code -> Armand
- Page et HTML -> Tom
- Logo, design finale -> Romain
- Carte -> Romain (principalement) et Eguzki
- app.py / conversion.py -> Armand
- fonctions et fichiers utils -> Eguzki et Tom
- Documentation -> Eguzki, Tom, Armand, Romain

Vers la fin on corrigeait / modifiait nos fichiers à la chaine alors, on connait tous tout le code par coeur. Cette connaissance du code à permis une entraide exponentielle.

**Étapes / Historique du projet**


*Etape 1 : Origine de l'idée*

- Tout est partie d’un autre projet, Privealy nous permettant d’avoir le prix moyen de n’importe quelle objet. En voulant creuser on s’est demander comment simuler l’évolution de ses prix. Et on a découvert alors que ces prix évoluer en même temps que la nature. 

- On a alors voulu créer une simulation très réaliste montrant l'impacte de l'économie sur la nature. Autrement dit montrer l’impact environnementale d’une action économique.

- On sait dit alors qu'on diviserait le projet en trois partie : Un partie observation (consultation du prix moyen d'un objet), une partie simulation éco-environnementale et partie simulation générale. Faire cette simulation nous paraissait vraiment complexe, alors nous avons préférée, créer une simulation générale pour pouvoir créer cette simulation précise. 

- Cependant à force de rajouter des idées et de vouloir généraliser, on à identifier une forme de patherne dans nos idées de simulations, et nous avons alors pris la décisions de créer un moteur de simulation générale avec son propre langage. On afficherait ça sous forme de site. Avant ça il y a même eu une discussions philosophique sur la nature, et pourquoi notre projet représentait le mieux notre vision de celle-ci. C'est là que nous avons eu l'idée du nom : Tree (explication plus haut sur pourquoi)

*Etape 2 : Concrétisation*

- On a commencé à définir rigoureusement le modèle, en excluant les idées trop vagues, trop précises (trop cibler) ou encore trop complexe à réaliser. 
En voulant associer ce système à des notions du programme on a dédcouvert que l'ensemble des idées de cette simulation le suivait de près ou de loin. Nous avons cependant établis la grammaire complète de Frank SQL, avant de séléctionner les fonctions plus acceccible et de simplifier *75% la synthaxe.

- Le modèle définit (objets, liaisons, événements...), nous avons hierarchisez les conceptes du plus essentiels au moins essentiels à fin de procéder de manière évolutif => Cette à dire que définir des sortes d'étapes où le projet pourrait s'arrêter. On a appellé ces étapes des "checkpoint". Cette méthode nous a beaucoup aidée.

- Une fois, les Checkpoint définis, nous avons une nouvelle fois hierarchiser les tâches à l'intérieur de ce checkpoint et nous avons calculer pour chaque tâches 2 facteurs : 

la durées estimée (DE)
la dépendance (DP)

- Ensuite nous avons rétablit les tâches à l'intérieure de l'équipe, en prenant en compte de l'envie, des compétences et disponibilités de chacun.

- Enfin nous avons établit des dates favorables et limites pour réaliser chaque tâches.

*Etape 3 : Développement*

- Création de l'architecture modulaire + nomanclature des fichiers.

- développement du graphe et des algorithmes simple / intuitif.

- Création du site avec Flask => Toute les pages sont créer, tout les boutons existent, mais le code n'agit pas encore.

- création de la simulations (+ Donées, Affichage du Graphe, Ajouts rapides)

- Finition de toute les pages et affichage (Journale de bord simulation, composition, Courbe)

- Création de la page Code, et mise en place du code SQL Frank pilotant tout le site.

- tentative de créer une carte dynamique (Echec sans JS)

- Ajout de fonction pour le Frank SQL

- Ajout du JS pour la carte (placement sur la carte qui donne des des coordonnées (x;y))

- Création de nombreux test.

- Création de test et exemple plus complexe, entièrement codé en Frank SQL (FSQL).

- Longue phase de vérifications et de corrections.

- Ajout d'une page Help, renseignant l'utilisateur. 



**Validation de l’opérationnalité et du fonctionnement**

Nous avons donc créer le moteur et son langage pour pouvoir créer notre simulation rêvé. 

L'outil du projet ( le site web) est terminé, il suffit maintenant d'y entrer des informations comme les matières premières simples ainsi que de réelles statistiques afin d'en remplir la BDD créer par les fonctions.

Pour valider le projet, nous testions tout, et le langage Frank SQL nous a rendu cela très rapide.

Nous avons tester sur d'autre machines. 

Nous faisions donc des tests réguliers et des observation rigoureuse sur des simulations. On a lancé des projets de simulations complexe pour mettre le projet à l'épreuve. 
    Ex : Voir les prédictions d'évolutions des prix et qui était le plus impacté avec la guerre actuelle. 

Nous avons rencontré beaucoup de Difficultés Mais nous avons trouvés aussi Beaucoup de solutions :

- propagation dans le graphe -> ajout d’une profondeur et d'une conservations (à quel point la valeur et conserver dans le graphe) et pas tout en une liaison. 
autrement dit on a diviser la propagation en 2 (nombre de sommets ; conservations)
- Positionnement de points sur la carte -> JS 
- Evénement périodique -> Création des paternes qui associent une action à une certaines fréquences.
- organisation du code -> séparation en fichiers, POO, fichier_utils ect...
- créer des simulations manuelles ou recréer des bases de données existantes = très longs -> Ajout rapide. (ex : A ; B ; C ; D pour rajouter ces objets)
    - Implique nouvelle contrainte -> Respect des contraintes SGBD -> prévoire des synthaxe que l'utilisateur pourrait rentrer pour lui éviter des erreurs.

*Un des vrai défit a surtout été de tout généraliser -> Faire comprendre de choses à la simulations sans être trop précis :*
    
    
- Nous avons découvert que l'état d'un objet, marchait par opposition, la données et son inverse. Un raisonnement binaire que nous avons traduit par la table d'inversion. On part d'un principe initiale, valeur 0 et la valeur 1 sont opposées. Ainsi, pour inverser une valeur il suffit de faire -1 ou +1. Valeur0 transforme en valeur 1 et valeur 1 en valeur 0. On peut ainsi définir des inversions tel que : "ON/OFF" ; "Bon/Mauvais" ; "Intacte/Cassé" ; "Vivant / Mort" ; "Vrai/Faux"....
C'est la table d'inversion.

- Dans la simualation, il y a des paternes qui agissent selon une fréquence (ex : une entrepise qui gagne 5$/seconde). Il fallait donc que la simulation comprenne ces fréquences et plus globalement la temporalitée. Pour ça on a dans un premier temps redéfinit l'interface de la simulation, l'utilisateur doit désormer définir le nombre de tour et la valeur d'un tour (Ex : "5tours, durées 8s"). Ensuite nous avons créer la table des unitées, l'utilisateur peut créer des unités à partir de celles déjà présente, en rentrant un coef. (Ex : Mois = 4*Semaines). La simulation peut ainsi effectuer des conversions. Elle applique c'est facteurs et c'est conversions pour calculer l'action des paterne.


**Ouverture**



*Améliorations possibles :*

 - interface plus jolie, plus facile et accessible. 

 - Frank SQL plus rigoureux, plus puissants, et plus complet. (Nottament pouvoir directement exécuter la simulation dans le "sim{}" qui agit pour l'instant comme un simple commentaire pour que les utilisateurs puissent communiquer leur paramètres en envoyant le code)

- plus d’interactions

- plus de types d’événements, notamment l'ajout malheureusement trop tardif du "faire chemin" ou "commande" qui permetrait à un objet de se déplacer sur un chemin. Ceux qui aurait permis encore plus de possibilité comme les déplacements, les calcules d'impacte environnementaux des marchandises et des déplacements, des calcules de distance en fonction du temps et de la distance. Les simulations d'écosystèmes seraient encore plus impressionnantes avec des espèces qui bouge, migre, vivent. De même pour les simulation de commerce, mathématique ou simple. Cela traduirait le mouvements. 

- Paterne plus rigoureux, et plus rapproché d'un événement.

- Probabilité moins défaillante et plus utiles.

- Evénement d'événement, paterne de paternes.

- Ajout du "système" un module qu'on avait pensé permettant de faire une action qui déclanche 5 autre. Ou une action qui déclenche 1 des 5 autres selon leur probas. il serait noté sys{brc1=... ; brc2=...}

- Ajout d'autres fonction pour le Frank SQL que l'on trouve tout aussi pertinent comme :

        - rul{} : Définit un registre de règle pour votre simulation (exemple : loi physique)
        - univ{} : L'univers, ses règles, son fonctionnement, ses données, les simulations s'adaptent à lui.
        - mvt{} : Un peu dans la même idée que le "faire chemin / commande" mais encore plus tourné mouvements. Simplifiant la création de ceux ci et séparant l'affichage d'un mouvement et d'un chemin sur la carte.
        - cart{} : Création de carte, figuré ("fig{}") et bordure brd{}. On pourrait tout dessiner.
        - calc{} : permet d'ajouter des calcules / formule sur le même principe que les unités,calcule_A(colonne_x * colonne_B). Et maintenant A(objet) renvoie le résultat de calcule_A avec l'objet.


=> Amélioration du Frank SQL

- Pouvoir intepréter des matrix d'adj, à fin que les utilisateurs puissent partager leur liaisons directements avec la matrix, ou la liste d'adj.
- Pouvoir obtenire des dictionnaires de liste d'adj.
- Finale : Faire des tables dans des tables (une vrai programation objets améliorant cp{} et la page composition). Les tables dans des tables serait enfaite d'autre table et le site les afficherais comme des tables de tables avec un système de pointeur ou de liaison "=>", soit des tables "composants" d'autre tables. ((On se rapproche de plus en plus de la fractale, forme de la nature ;) )



*Analyse critique*

Le projet est intéressant mais améliorable et il faudrait aussi rendre le SQL Frank encore plus puissant et rigoureux.
Le projet n'est peut être pas assez solide sur certains points.
Le projet n'est pas très compréhensible sans la page help et les différentes descriptions.



*Compétences développées*


Python
Flask
graphes
HTML
Repère dans un code Long / Repère et maniement d'une grande quantité de fichiers.
Parcing
Compilateur / interpréteur
Gestion d'erreur
SQL (SQlite)
travail en groupe
Logique / Conceptualisation / Projection 
Gestion de crise / Gestion de stress
Création de choses abstraites
POO / Récursivitée
Rapidité
Prise de décisions / ajouts et suppressions d'idées. 

*Point de vue*

Eguzki : 
Au départ j'ai eu un peu peur quand on a commencé à parler théorie. Heureusement j'ai su poser les limites avec eux. Cependant, je n'ai jamais eu une aussi bonne entente dans un groupe. J'ai était motivé tout au long du projet, avoir tout ses responsabilité au niveau de la faisabilité n'était pas une mince à faire mais j'étais content que l'on met choisit cela m'a fait apprendre beaucoup de choses, surtout au niveau de la gestion de groupe, de demandes, et d'erreurs potentielle. Peut importe les résultats, ce projet m'a beaucoup appris, et cela ma apporté beaucoup d'expérience.

Défaut => Mauvaise décisions en situation de crise, conceptualiser avant de coder.

Tom :
Quand Armand m'a dit qu'on va faire un site, je me suis directement mis à apprendre du HTML. C'est un langage que j'apprends depuis ma découverte de celui-ci en Première par M. Carolo. La gestion d'autant de fichier est un peu stressante, mais le cadre du groupe et surtout les fonction et rôles distribuer à chacun ainsi que le système complexe d'organisation que l'on a mis en place est vraiment rassurant. J'ai appris de ce systèmes, j'ai appris le HTML comme jamais au par avant. J'ai eu beaucoup d'erreur mais avec le recul, leur correction à permis à mon code de devenir beaucoup plus rigoureux mais surtout libre. En effet je peux maintenant faire un projet sans consulter la documentation toute les 5 min ou reprendre des exemples types.

Défaut => Organisation / les code type pile, file ou encore la POO. Aussi l'écoute, j'ai appris à écouter tout le monde.

Armand :
Conceptualiser un projet était déjà fascinant mais le rendre réel ce n’était pas une mince à faire. Avoir un groupe à l'écoute aide beaucoup. Je n'ai jamais autant appris et fait de lien logique avec le programme de NSI que durant ce projet (sincèrement). Imaginer un langage de programmation, et le faire ça m'a ouvert les portes de choses encore plus complexes. Gérer un groupe ou une équipe ce n’était pas évident mais celui-ci était vraiment sympas, la gestion de crise, et l'organisation rigoureuse m'ont beaucoup appris. Trouver des solutions logique au problèmatique était un exellent entraînement. Savoir reconaitre ses erreures, est très important pour faire avancer le projet et pour apprendre, c'est l'une des choses que j'ai apprises.

défaut => Organisation et communication d'idées, programation type et non brouillon.

Romain :
C'était tellement compliqué, la carte tout ça. Mais travaillait avec Armand et les autres c'était plutôt facile. L'organisation était très spéciale (hyper bien définis) et les membres du groupes m'ont poussé vers le haut. J'ai appris sur le JS (ce n'était pas le but mais je souhaite le soulignés). J'ai aussi appris à conceptualiser des choses hyper abstraites comme un repère dans un espace sans représentation visuelle. Travailler sur un code aussi gros, se rappeler de ce qu'on à fait le mois dernier ect... C'était vraiment dure mais avec une bonne communication (j'ai appris à utiliser GitHub !) sa marche super bien. Pour être honnête au début je pensais que j'allais utiliser l'IA, mais je ne suis pas peu fière de vous dire que 0% de mon travaille l’utilise. Aussi, quand quelqu'un finissait un code il faisait un dossier cours de toute les fonctions qu'il avait utilisé et pourquoi, même si je n'étais pas concerné par ce code je lisais à chaque fois, et j'ai appris énormément de chose. Sincèrement je pense avoir fait un évolution fulgurante en programmation, surtout c'est dernier jours. Et non je n'exagère pas.

Défaut avant => Programation en générale, compréhension des concepts

**Inclusion**

Parmis les membres de l'équipe, il y avait un membres bénéficiant d'un GEVASCO et un autre d'un PAP. Cela n'a pas était impactant pour le projet car difficulté prisent en compte dans notre organisation. 

**Conclusion**

Nous attendons les simulations que les utilisateurs vont créer avec impatience, et nous comptons améliorer et partager le projet à fin de l'améliorer avec peut être de nouvelles personnes en cours de route. L'aventure n'est pas fini.

C'est un honneur pour nous de participer (vraiment) et encore plus qu'on utilise ou joue avec notre projet. Nous avons vécut des moments difficiles comme très drôles.
Merci d'avoir lu, en espérant être retenu par les trophées NSI et de ainsi, prolonger cette aventure. FRANK !

Armand, Tom, Eguzki, Romain.

