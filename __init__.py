import os

# On installe les dépendances
os.popen("pip install --no-cache-dir -r ./util_lib/requirements.txt").read()

# On importe tout
from util_lib.util_lib import *