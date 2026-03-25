import os  #permet d'interagir avec le système 
import sys  #permet d'accéder aux informations système 

python = sys.executable  #récupère le chemin de l'exécutable Python utilisé
try:
    import flask  #essaie d'importer le module Flask
    print('[OK] Flask est installe.')  #message si Flask est déjà présent
except ImportError:  #si Flask n'est pas trouvé
    print('[!] Flask manque, installation en cours...')  #avertissement
    os.system('"' + python + '" -m pip install flask')  #installe Flask via pip

print('Ouvrir http://127.0.0.1:5000')  #indique à l'utilisateur l'adresse du serveur local
os.system('"' + python + '" app.py')  #lance le fichier app.py avec l'interpréteur Python
