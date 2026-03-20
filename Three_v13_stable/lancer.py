import os
import sys

python = sys.executable
try:
    import flask
    print('[OK] Flask est installe.')
except ImportError:
    print('[!] Flask manque, installation en cours...')
    os.system('"' + python + '" -m pip install flask')

print('Ouvrir http://127.0.0.1:5000')
os.system('"' + python + '" app.py')
