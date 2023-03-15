import os

try:
	# On importe tout
	from util_lib.util_lib import timer, ping, yaml_parametres, get_ip, get_network_infos, get_hostname, get_username, get_os, supervisor_status, scale, logger, \
		present_in_list, get_item_in_list
except ModuleNotFoundError:
	# Si module non trouvé, on installe les dépendances
	os.popen(f"pip install --no-cache-dir -r {os.path.dirname(os.path.realpath(__file__))}/requirements.txt").read()
	from util_lib.util_lib import timer, ping, yaml_parametres, get_ip, get_network_infos, get_hostname, get_username, get_os, supervisor_status, scale, logger, \
		present_in_list, get_item_in_list

