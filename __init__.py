import os

try:
	# On importe tout
	from util_lib.util_lib import *
except ModuleNotFoundError:
	# Si module non trouvé, on installe les dépendances
	os.popen("pip install --no-cache-dir -r ./util_lib/requirements.txt").read()
	from util_lib.util_lib import *

