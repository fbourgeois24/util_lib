""" Utilitaires divers 
	- timer : timer multifonction
	- ping : ping une adresse et renvoie un booléen avec le résultat
	- log : effectue un print vers la sortie choisie (stdout ou fichier)
	"""

import time
import os, sys
from datetime import datetime as dt
from datetime import timedelta
import platform
import yaml # Install with "pip install PyYAML"
import socket
import logging
from pythonping import ping as pyping #Installer avec 'pip install pythonping'
import struct

class timer:
	""" Timer multifonctions basé sur le timestamp
		Renvoie vrai ou faux
		Paramètres : 
		- time : temps entre chaque "débordement" du timer
		- bascule_mode : si vrai, le timer devient une bascule (change d'état (vrai / faux) à chaque "débordement" du timer)
						si faux, le timer renvoie vrai une seule fois à chaque "débordement" du timer sinon il renvoie faux
		- initial_state : utile si bascule_mode est à vrai, définit l'état de départ de la bascule (vrai ou faux)
	"""
	def __init__(self, time, bascule_mode=False, initial_state = True):
		self.time = time
		self.old_timestamp = 0.0
		self.bascule_mode = bascule_mode
		if initial_state:
			self.bascule = True
		else:
			self.bascule = False

	def eval(self):
		""" Evalue le timer, renvoie vrai ou faux suivant la configuration"""
		# récupération du timestamp actuel
		now = time.time()

		# Bascule est un mode qui change la valeur renvoyée à chaque débordement du timer
		if not self.bascule_mode:	
			# Evaluation du timer
			if now > self.time + self.old_timestamp:
				self.old_timestamp = now
				return True
			else:
				return False

		else:
			if now > self.time + self.old_timestamp:
				self.old_timestamp = now
				self.bascule = not self.bascule
			if self.bascule:
				# print("bascule ON")
				return True
			else:
				# print("bascule OFF")
				return False

def ping(address):
	""" Ping une adresse, renvoie vrai si ping réussi et faux si non"""
	result = pyping(address, count=1)
	if "Request timed out" in str(result):
		util_lib_log.debug("ping échoué")
		return False
	else:
		util_lib_log.debug("ping réussi")
		return True


class Loader(yaml.SafeLoader):
	""" Custom loader, permet d'inclure des fichiers yaml depuis d'autres via !include """

	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		try:
			with open(filename, 'r') as f:
				return yaml.load(f, Loader)
		except FileNotFoundError:
			return ""

Loader.add_constructor('!include', Loader.include)

class yaml_parametres():
	""" Gestion des paramètres dans un fichier yaml externe
		Lors de l'initialisation de la fonction, read permet de directement lire les valeurs qui seront stockées dans self.content
		Dans ce cas les valeurs ne sont évidemment pas renvoyés sous forme de dictionnaire !
	 """
	def __init__(self, path, read=False):
		self.path = path
		self.content = {}
		if read:
			self.content = self.read()

	def read(self):
		""" Lire les paramètres et les stocker dans un dictionnaire
			Lors de l'exécution de cette fonction, les paramètres sont stockés dans self.content et sont renvoyés
		 """
		yaml_file = open(self.path, "r")	
		dict_parameters = yaml.load(yaml_file, Loader=Loader)
		yaml_file.close()
		self.content = dict_parameters
		return dict_parameters

	def write(self, dict_parameters=None):
		""" Ecrire les paramètres dans le fichier yaml 
			Sauve les paramètres stockés.
			Si un dictionnaire est passé en paramètre, c'est lui qui est stocké sinon ce sera self.content qui sera stocké
		"""
		yaml_file = open(self.path, "w")
		if dict_parameters is not None:
			yaml.dump(dict_parameters, yaml_file)
		else:
			yaml.dump(self.content, yaml_file)
		yaml_file.close()

		return self.read()


def get_ip(inteface_name="eth0"):
	""" Récupérer l'ip de la carte ethernet de la machine"""
	return str(os.popen('ifconfig').read().split(inteface_name)[1].split('inet')[1].split('netmask')[0].replace(" ",""))

def get_network_infos(inteface_name="eth0"):
	""" Récupérer les infos réseau de la machine 
		Si interface inconnue, renvoi None
		Si interface non-connectée, renvoie False
		Si connecté, renvoie un dict avec les infos
	"""
	data = {}
	raw_data = str(os.popen('ip a').read())
	if inteface_name not in raw_data:
		return None
	raw_data = raw_data.split(inteface_name)[1]
	if not "inet" in raw_data:
		return False
	raw_data = raw_data.split("inet ")[1]
	# IP
	data["ip"] = raw_data.split("/")[0]
	# Masque
	msk_ln = int(raw_data.split("/")[1].split(" brd")[0])
	# On déduit le masque complet
	msk = (1<<32) - (1<<32>>msk_ln)
	data["msk"] = socket.inet_ntoa(struct.pack(">L", msk))
	# Broadcast
	data["brd"] = raw_data.split("brd ")[1].split(" ")[0]

	raw_data = str(os.popen("ip route | grep default").read())
	data["gtw"] = raw_data.split(inteface_name)[0].split("default via ")[-1].split(" ")[0]

	return data


def get_hostname():
	""" Récupérer le nom de la machine """
	return str(socket.gethostname())

def get_username():
	""" Récupérer le nom d'utilisteur courant de la machine """
	return os.getlogin()

def get_os():
	""" Récupérer l'os sur lequel le script est exécuté """
	return platform.system()

def get_uptime():
	""" Récupération du uptime du raspberry """
	raw = float(os.popen("cat /proc/uptime").read().split()[0])
	return str(timedelta(seconds=raw)).split(".")[0]

def supervisor_status():
	""" Affiche le statut du superviseur (renvoie un dictionnaire avec le nom du script comme clé et un autre dictionnaire contenenant les infos comme valeur) 
	exemple de retour de la commande de statut du superviseur:
	automate_telegram                RUNNING   pid 20523, uptime 1 day, 8:09:27
	cpu_fan                          RUNNING   pid 20519, uptime 1 day, 8:09:27
	gestion_signaux                  RUNNING   pid 20520, uptime 1 day, 8:09:27
	"""

	dict_scripts = {}
	supervisor_status = os.popen("sudo supervisorctl status").read().split("\n")[:-1]
	for script in supervisor_status:
		# rstrip permet de supprimer les espaces à la fin de la chaine de caractère
		try:
			dict_scripts[script[:33].rstrip()] = {"status": script[33:43].rstrip(), "pid": script[47:].split(",")[0], "uptime": timedelta(days=int(script[61:].split("day, ")[0]),hours=int(script[61:].split("day,")[1].split(":")[0]) , minutes=int(script[61:].split("day,")[1].split(":")[2]), seconds=int(script[61:].split("day,")[1].split(":")[2]))}
		except ValueError:
			# Si la lecture échoue c'est que le script ne tourne pas et il n'y a donc pas plus d'infos
			dict_scripts[script[:33].rstrip()] = {"status": script[33:43].rstrip()}
		
	return dict_scripts

def scale(value, from_min, from_max, to_min, to_max):
	""" Fonction qui fait une mise à l'échelle flottante d'une plage à une autre """
	return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def logger(name="Main", existing=None, global_level=None, file_handler_level=logging.WARNING, stream_handler_level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s', stream_handler = True, file_handler = True, filename = ""):
	""" configurer un logger et renvoyer l'objet configuré
		name = nom du nouveau logger à créer
		existing = logger existant à configurer
		Niveaux de log (DEBUG, INFO, WARNING, ERROR ou CRITICAL)
			file_handler_level : niveau de log du fichier, par défaut WARNING
			stream_handler_level : niveau de log de la console, par défaut DEBUG
			global_level = s'il est spécifié, il écrase les 2 précédents
		format = format des messages de log
		stream_handler = Vrai s'il faut l'activer
		file_handler = Vrai s'il faut l'activer
		filename = Nom du fichier de sortie (utilisé par exemple pour renvoyer la sortie des logger de différents modules vers le même fichier)
	"""

	if existing is not None:
		# Si un logger existant a été passé, on reprend son nom
		name = existing.name
	elif name == "":
		# Si pas de nom et pas de logger existant on lève une erreur
		raise TypeError("Au moins un nom (pour un nouveau logger) ou un logger existant doivent être passés en paramètre")
	
	if existing is None:
		# Si aucun logger existant n'a été passé, on en crée un nouveau
		log = logging.getLogger(name)
	else:
		# Si un logger existant a été passé on l'utilise
		log = existing
	# On définit le niveau de log du logger principal, il doit être égal au plus bas niveau tout handlers confondus
	if global_level is not None:
		level = global_level
	else:
		level = 1000 # Si pas définit il est mis très haut pour être sur qu'il ne soit pas le min
	log.setLevel(min((stream_handler_level, file_handler_level, level)))
	# Format des messages
	formatter = logging.Formatter(format)
	if filename == "" and name != "":
		# Si pas de nom de fichier fourni on utilise le nom
		filename = name + ".log"
	elif filename == "" and name == "":
		# Si pas de nom et pas de nom de fichier
		raise TypeError("Aucun nom ou nom de fichier fourni")
	elif len(filename.split(".")) < 2:
		# Si le nom de fichier n'a pas encore d'extension
		filename += ".log"
	if file_handler:	
		# Si un file_handler doit être ajouté
		file_handler = logging.FileHandler(filename)
		file_handler.setFormatter(formatter)
		if global_level is not None:
			file_handler.setLevel(global_level)
		else:
			file_handler.setLevel(file_handler_level)
		log.addHandler(file_handler)
	if stream_handler:	
		# Si un stream_handler doit être ajouté
		stream_handler = logging.StreamHandler()
		stream_handler.setFormatter(formatter)
		if global_level is not None:
			stream_handler.setLevel(global_level)
		else:
			stream_handler.setLevel(stream_handler_level)
		log.addHandler(stream_handler)
	return log

class ip_configuration():
	""" Gestion de la configuration ip de la machine """
	def __init__(self, interface="eth0"):
		# Contructeur
		self.interface = interface

	def read(self, interface=None):
		''' Lecture de la configuration réseau
			On renvoi un dict avec les infos
		'''

		if interface is None:
			# Si pas d'interface spécifiée, interface par défaut
			interface = self.interface

		# On lit le fichier dhcpcd.conf pour regarder s'il y a déjà une config ip fixe (précédée du commentaire ip_fixe)
		if not os.path.exists("/etc/dhcpcd.conf"):
			# Si pas raspberry
			return {"dhcp": True, "ip": "", "msk": "", "gtw": ""}

		with open("/etc/dhcpcd.conf", 'r') as ip_file:
			ip_file_content = ip_file.read()

		if '# ip_fixe' in ip_file_content:
			ip_data = {"dhcp": False}
			# Il y a déjà une config ip fixe
			config_ip = ip_file_content.split("# ip_fixe\n")[1].split("\n")
			for line in config_ip:
				if "ip_address=" in line:
					# On en déduit l'ip et le masque
					ip_data["ip"] = line.split("ip_address=")[1].split("/")[0]
					msk = (1<<32) - (1<<32>>int(line.split("/")[1]))
					ip_data["msk"] = socket.inet_ntoa(struct.pack(">L", msk))
				elif "routers=" in line:
					# Gatewxay
					ip_data["gtw"] = line.split("routers=")[1]
				elif "domain_name_servers=" in line:
					# DNS
					ip_data["dns"] = line.split("domain_name_servers=")[1]

			return ip_data
			
		else:
			# Il n'y a pas de config ip fixe, on va chercher l'ip actuelle
			config_ip = get_network_infos(interface)
			return {"dhcp": True, "ip": config_ip["ip"], "msk": config_ip["msk"], "gtw": config_ip["gtw"]}

	def write(self, config_ip, interface=None):
		""" Ecrire une configuration ip fixe """
		if interface is None:
			# Si pas d'interface spécifiée, interface par défaut
			interface = self.interface

		# On lit le fichier
		with open("/etc/dhcpcd.conf", 'r') as ip_file:
			ip_file_content = ip_file.read()
		
		# Si une config existe déjà, on la supprime
		if "# ip_fixe" in ip_file_content:
			# On supprime la config existante
			ip_file_content = ip_file_content.split("# ip_fixe")[0]

		if not config_ip["dhcp"]:
			# On ajoute la nouvelle config si pas dhcp
			ip_file_content += f"\n\n# ip_fixe\ninterface {interface}\n"
			# On compte le nombre de bits à 1 dans le masque
			msk_len = 0
			for byte in config_ip["msk"].split("."):
				msk_len += str(bin(int(byte))[2:]).count("1")
			ip_file_content += f"static ip_address={config_ip['ip']}/{msk_len}\n"
			ip_file_content += f"static routers={config_ip['gtw']}\n"
			ip_file_content += "static domain_name_servers=1.1.1.1\n"

		# On réécrit le fichier
		with open("/etc/dhcpcd.conf", 'w') as ip_file:
			ip_file.write(ip_file_content)

		# NE PAS OUBLIER DE REDEMARRER LA MACHINE POUR APPLIIQUER LA CONFIG

		return True

		

util_lib_log = logger("util_lib", file_handler=False)