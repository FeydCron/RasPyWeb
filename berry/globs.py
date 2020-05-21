import datetime
import importlib
import json
import os
import pickle
import queue
import re
import socket
import sys
import threading
import traceback
from collections import OrderedDict, deque

from . import httpd
from .httpd import StartPage

# Defines test values for CPU temperatures for being used with
# a module test
s_oQueueTestCpuTempValues = queue.Queue()

# ------------------------------------------------
# Signalisierung der Art der  Programmterminierung
# ------------------------------------------------
# "term" - Programm beenden
# "boot" - System neu starten
# "halt" - System herunterfahren
s_strExitMode = ""

# ---------
# Log-Level
# ---------
# 0 - Exceptions
# 1 - Fehler
# 2 - Warnungen
# 3 - Meldungen
# 4 - Debugging
s_nLogLvl = 4

s_strBasePath = "/home/pi/berry"
s_strSoundPath = "/home/pi/berry/sounds"
s_strImagePath = "/home/pi/berry/images"
s_strModulePath = "/home/pi/berry/modules"
s_strConfigFile = "/home/pi/berry/config.json"
s_strLogMemFile = "/home/pi/berry/logmem.pickle"
s_strStartPageFile = "/home/pi/berry/startpage.pickle"
s_strStartPageUrl = "/system/startpage.html"

s_dictSettings = {
	# Registrierung der installierten Module
	# ["<Paket/Modul>", ...]
	"listModules" : [],
	# Auflistung der explizit deaktivierten Module
	# ["<Paket/Modul>", ...]
	"listInactiveModules" : [],
	# Systemeinstellungen
	# {"<Eigenschaft>" : "<Wert>"}
	"System" : {
		"strLogLvl" 			: "DBG",  # Aktuelles Log-Level
		"bTestMode" 			: False,  # Aktivierung des Testmodus
		"strHttpIp" 			: "0.0.0.0",  # IP-Adresse für den HTTP-Server
		"nHttpPort" 			: 8081,  # Portnummer für den HTTP-Server
		"strNetInfoName"		: "google.com",  # Computername zum ermitteln der eigenen IP-Adresse
		"fCpuTempA" 			: 60.0,  # Abschalt-Temperaturgrenze
		"fCpuTempB" 			: 56.0,  # Kritische Temperaturgrenze
		"fCpuTempC" 			: 53.0,  # Warn-Temperaturgrenze
		"fCpuTempH" 			: 1.0,  # Hysterese Temperaturgrenze
		"strSysSoundLocation"	: "/usr/share/scratch/Media/Sounds",
		"strUsrSoundLocation"	: s_strSoundPath,
		"strSysImageLocation"	: "/usr/share/icons/Adwaita/32x32",
		"strUsrImageLocation"	: s_strImagePath,
		"fVersion"				: 0.1,
		"strTimeSunrise"		: "06:00:00",
		"strTimeSunset"			: "22:00:00",
	},
	# Fehlende Python-Pakete, die optional mit Pip installiert werden können
	# {"<Paketname>" : "<Pip Installationskommando>"}
	"PIP" : {},
	# HTTP-Weiterleitungen
	# {"<ID>" : "<URL>"}
	"Redirects" : {
		"Zielseite" : "",
		"Startseite" : "/system/startpage.html"
	}
}

# Parameterdefinitionen
# {"<Schlüssel>" : {"<Name>" : {"" : ""}}}
# 
# Die Initialisierung über ein normales dict, mit chaotischer Sortierung
# macht an dieser Stelle nur deshalb Sinn, weil das Dictionary auf
# oberster Ebene nur einen Schlüssel enthält.
#
s_dictUserSettings = {
	"System" : {
		"properties" : [
			"strHttpIp",
			"nHttpPort",
			"strNetInfoName",
			"bTestMode",
			"fCpuTempC",
			"fCpuTempB",
			"fCpuTempA",
			"fCpuTempH",
			"strSysSoundLocation",
			"strUsrSoundLocation",
			"strSysImageLocation",
			"strUsrImageLocation",
			"strTimeSunrise",
			"strTimeSunset",
		],

		"bTestMode" : {
			"title"			: "Testmodus",
			"description"	: ("Der Testmodus ist eine Eigenschaft, die von anderen Modulen " + 
								"oder Programmteilen für Testzwecke verwendet werden kann, " + 
								"um zum Beispiel spezielle Testfunktionen ein- oder auszuschalten."),
			"default"		: "Aus"
		},
		"strHttpIp" : {
			"title"			: "Web-Server IP-Adresse",
			"description"	: ("Wenn der Raspberry über mehrere Netzwerkschnittstellen " + 
								"verfügt, kann hier die IP-Adresse eingestellt werden, " + 
								"unter welcher das Web-Interface erreichbar sein soll. " + 
								"ACHTUNG: Eine falsche Einstellung kann das Web-Interface " + 
								"unerreichbar machen!"),
			"default"		: "0.0.0.0"
		},
		"nHttpPort" : {
			"title"			: "Web-Server TCP-Portnummer",
			"description"	: ("Die TCP-Portnummer, unter welcher das Web-Interface " + 
								"erreichbar sein soll, kann geändert werden, wenn die " + 
								"Standardeinstellung in Konflikt mit einem anderen Programm " + 
								"steht, welches die TCP-Portnummer für sich  beansprucht. " + 
								"ACHTUNG: Eine falsche Einstellung kann das Web-Interface " + 
								"unerreichbar machen!"),
			"default"		: "8081"
		},
		"strNetInfoName" : {
			"title"			: "Referenz-Computername",
			"description"	: ("Die Einstellung legt den Computernamen bzw. dessen " + 
								"IP-Adresse fest, um damit die eigene IP-Adresse " + 
								"ermitteln zu können. Bei vorhandener Internetverbindung " + 
								"kann der Standard beibehalten oder ein anderer " + 
								"namhafter Internet-Host verwendet werden. Steht kein " + 
								"Internet zur Verfügung, muss sich der betreffende " + 
								"Computer im gleichen Netzwerk befinden und erreichbar " + 
								"sein. Ist der Raspberry netzwerktechnisch eine einsame " + 
								"Insel, muss auf localhost bzw. 127.0.0.1 zurückgegriffen werden."),
			"default"		: "google.com"
		},
		"fCpuTempA" : {
			"title"			: "Temperaturgrenze Notabschaltung",
			"description"	: ("Legt die Temperaturgrenze für die CPU in Grad Celsius fest, " + 
								"bei deren Überschreitung über einen längeren Zeitraum " + 
								"die Notabschaltung des Systems zu veranlassen ist."),
			"default"		: "60.0"
		},
		"fCpuTempB" : {
			"title"			: "Temperaturgrenze Kritisch",
			"description"	: ("Legt die Temperaturgrenze für die CPU in Grad Celsius fest, " + 
								"bei deren Überschreitung jeweils Meldung über die kritische " + 
								"Betriebstemperatur der CPU zu veranlassen ist."),
			"default"		: "56.0"
		},
		"fCpuTempC" : {
			"title"			: "Temperaturgrenze Warnung",
			"description"	: ("Legt die Temperaturgrenze für die CPU in Grad Celsius fest, " + 
								"bei deren Überschreitung jeweils Meldung über die hohe " + 
								"Betriebstemperatur der CPU zu veranlassen ist."),
			"default"		: "53.0"
		},
		"fCpuTempH" : {
			"title"			: "Hysterese um Temperaturgrenzen",
			"description"	: ("Legt die Hysterese um die Temperaturgrenzen für die CPU in " + 
								"Grad Celsius fest, um ein zu häufiges Wechseln des erfassten " + 
								"Betriebstemperaturbereichs der CPU zu vermeiden."),
			"default"		: "1.0"
		},
		"strSysSoundLocation" : {
			"title"			: "Ablageort Systemklänge",
			"description"	: ("Legt den Ablageort von Klangdateien fest, die auf dem System " + 
								"standardmäßig zur Verfügung stehen. Dieser Ort wird bei der " + 
								"Installation oder Verwaltung von Klangdateien nicht verändert."),
			"default"		: "/usr/share/scratch/Media/Sounds"
		},
		"strUsrSoundLocation" : {
			"title"			: "Ablageort Klangdateien",
			"description"	: ("Legt den Ablageort von Klangdateien fest, die für das System " + 
								"zur Verfügung stehen sollen. Bei der Installation neuer Klänge " + 
								"werden diese dort abgelegt, gegebenenfalls auch kategorisiert in " + 
								"Unterordnern."),
			"default"		: s_strSoundPath
		},
		"strSysImageLocation" : {
			"title"			: "Ablageort System-Bilddateien",
			"description"	: ("Legt den Ablageort von Bilddateien fest, die auf dem System " + 
								"standardmäßig zur Verfügung stehen. Dieser Ort wird bei der " + 
								"Installation oder Verwaltung von Bilddateien nicht verändert."),
			"default"		: "/usr/share/icons/Adwaita/32x32"
		},
		"strUsrImageLocation" : {
			"title"			: "Ablageort Bilddateien",
			"description"	: ("Legt den Ablageort von Bilddateien fest, die für das System " + 
								"zur Verfügung stehen sollen. Bei der Installation neuer Bilder " + 
								"werden diese dort abgelegt, gegebenenfalls auch kategorisiert in " + 
								"Unterordnern."),
			"default"		: s_strImagePath
		},
		"strTimeSunrise" : {
			"title"			: "Sonnenaufgang",
			"description"	: ("Legt den Zeitpunkt des Sonnenaufgangs fest, sodass sich bestimmte " + 
								"Funktionen darauf beziehen können. Eine manuelle Einstellung legt " + 
								"einen Standardwert fest, welcher jedoch durch die Installation " + 
								"bestimmter Module automatisch angepasst und gepflegt werden kann."),
			"default"		: "06:00:00",
			"type"			: "time"
		},
		"strTimeSunset" : {
			"title"			: "Sonnenuntergang",
			"description"	: ("Legt den Zeitpunkt des Sonnenuntergangs fest, sodass sich bestimmte " + 
								"Funktionen darauf beziehen können. Eine manuelle Einstellung legt " + 
								"einen Standardwert fest, welcher jedoch durch die Installation " + 
								"bestimmter Module automatisch angepasst und gepflegt werden kann."),
			"default"		: "22:00:00",
			"type"			: "time"
		},
	},
}

s_dictSystemValues = {
	"CPU" : {
		"Temperatur"	: "*****",
		"Auslastung"	: "*****",
	},
	"RAM" : {
		"Gesamt"		: "*****",
		"Belegt"		: "*****",
		"Frei"			: "*****",
		"Geteilt"		: "*****",
		"Gepuffert"		: "*****",
		"Im Cache"		: "*****",
	},
	"MEM" : {
		"Gesamt"		: "*****",
		"Belegt"		: "*****",
		"Verfügbar"		: "*****",
		"Belegung"		: "*****",
	}
}

s_oLogMem = deque([], 256)
s_oLogMemLock = threading.RLock()
s_oSettingsLock = threading.RLock()

s_oHttpd = None
s_lstSnapshot = None
s_oStartPage = StartPage()

s_evtShutdown = threading.Event()

def onDelayedShutdown():	
	if (s_evtShutdown.isSet()):
		log("No critical activity since last shutdown indication. Shutdown now.")
		stop()
		return
	wrn("Recognized critical activity since last shutdown indication.")
	shutdown()
	return
	
def signalCriticalActivity():
	s_evtShutdown.clear()
	
def shutdown():
	log("shutdown('%s')" % (s_strExitMode))
	print("Delaying shutdown ...")
	s_evtShutdown.set()
	threading.Timer(5.0, onDelayedShutdown).start()
	return

def stop():
	log("stop('%s')" % (s_strExitMode))
	if s_oHttpd:
		s_oHttpd.shutdown()
		s_oHttpd.server_close()
		try:
			s_oHttpd.socket.shutdown(socket.SHUT_RDWR)
			s_oHttpd.socket.close()
		except Exception as ex:
			print("Schließen des Sockets sicherstellen: %r" % (ex))
	return

def getVersion():
	return float(0.9)

def getWatchDogInterval():
	return float(10.0)

def getRedirect(strID, strDefault):
	if ("Redirects" in s_dictSettings
		and strID in s_dictSettings["Redirects"]):
		return s_dictSettings["Redirects"][strID]
	wrn("Keine Weiterleitung auf \"%s\" bekannt. Default: \"%s\"" % (
		strID, strDefault))
	return strDefault

def importComponent(
	strModuleName):
	oModule = None
	try:
		if strModuleName in sys.modules:
			log("Importieren des Moduls '%s' via Reload" % (strModuleName))
			oModule = importlib.reload(sys.modules[strModuleName])
		else:
			log("Importieren des Moduls '%s' via Import" % (strModuleName))
			oModule = importlib.import_module(strModuleName, __package__)
	except:
		exc("Importieren des Moduls '%s'" % (
			strModuleName))
		oModule = None
	log("Modul %r (%s) importiert" % (oModule, oModule.__name__))
	return oModule

def loadSettings():
	global s_strBasePath
	global s_strModulePath
	global s_strConfigFile
	global s_strLogMemFile
	global s_strStartPageFile
	global s_oStartPage
	
	# >>> Critical Section
	with s_oSettingsLock:
		# Einstellungen lesen
		
		s_strBasePath = ("%s" % os.path.dirname(__file__))		
		# print("BasePath=%s" % s_strBasePath)
		
		s_strModulePath = os.path.join(s_strBasePath, "modules")
		# print("ModulePath=%s" % s_strModulePath)
		s_strConfigFile = os.path.join(s_strBasePath, "config.json")
		# print("ConfigFile=%s" % s_strConfigFile)
		s_strLogMemFile = os.path.join(s_strBasePath, "logmem.pickle")
		# print("LogMemFile=%s" % s_strLogMemFile)
		s_strStartPageFile = os.path.join(s_strBasePath, "startpage.pickle")
		# print("StartPageFile=%s" % s_strStartPageFile)
		
		dbg("Laden der Konfigurationseinstellungen von '%s'" % (
			s_strConfigFile))
		try:
			foFile = open(s_strConfigFile, "r")
			oObj = json.load(foFile)
			foFile.close()
			for (strKey, varVal) in oObj.items():
				if (strKey in ["System", "PIP", "Redirects"]
					and strKey in s_dictSettings):
					s_dictSettings[strKey].update(oObj[strKey])
				else:
					s_dictSettings.update({strKey : varVal})
		except:
			exc("Laden der Einstellungen von '%s'" % (
				s_strConfigFile))
	# <<< Critical Section
	
	dbg("Wiederherstellen des Fehlerspeichers von '%s'" % (
		s_strLogMemFile))
	# Fehlerspeicher wiederherstellen
	oLogMem = None
	bRetry = os.path.isfile(s_strLogMemFile)
	if not bRetry:
		log("Fehlerspeicher nicht vorhanden: '%s'" % (
			s_strLogMemFile))
	while bRetry and os.path.isfile(s_strLogMemFile):
		bRetry = False
		try:
			with open(s_strLogMemFile, "rb") as f:
				oLogMem = pickle.load(f)
		except:
			exc("Laden des Fehlerspeichers von '%s'" % (
				s_strLogMemFile))
			bRetry = migrateFile(s_strLogMemFile)
	
	# Aktuellen und gelesenen Fehlerspeicher konsistent zusammenführen
	if oLogMem:
		dbg("Zusammenführen des aktuellen und wiederhergestellten Fehlerspeichers")
		# >>> Critical Section
		with s_oLogMemLock:
			oBackup = list(s_oLogMem)
			s_oLogMem.clear()
			s_oLogMem.extendleft(reversed(oLogMem))
			s_oLogMem.extendleft(reversed(oBackup))
		# <<< Critical Section
		del oLogMem
		del oBackup
	
	bRetry = os.path.isfile(s_strStartPageFile)
	if not bRetry:
		log("Startseite nicht vorhanden: '%s'" % (
			s_strLogMemFile))
	while bRetry and os.path.isfile(s_strStartPageFile):
		bRetry = False
		try:
			with open(s_strStartPageFile, "rb") as f:
				s_oStartPage = pickle.load(f)
		except:
			exc("Laden der Startseite von '%s'" % (
				s_strStartPageFile))
			bRetry = migrateFile(s_strStartPageFile)
	
	dbg("Klangdateien erfassen")
	# Sounds einmalig scannen
	scanSoundFiles()

	dbg("Bilddateien erfassen")
	# Bilder einmalig scannen
	scanImageFiles()
	
	dbg("Konfigurationsparameter synchronisieren")
	# Konfigurationsparameter synchronisieren
	if ("System" in s_dictSettings):
		if ("strLogLvl" in s_dictSettings["System"]):
			setLogLvl(s_dictSettings["System"]["strLogLvl"])

	# Modulkonfiguration migrieren
	if ("dictModules" in s_dictSettings
		and "listModules"  in s_dictSettings):
		s_dictSettings["listModules"].extend(s_dictSettings["dictModules"].keys())
		s_dictSettings.pop("dictModules")
			
	dbg("Konfiguration: %r" % (s_dictSettings))
	dbg("Startseite: %r" % (s_oStartPage))
	return

def migrateFile(strFilename):
	# Migration step: Replace old references to 'HTTPD.' with 'httpd.'
	#
	oData = None
	bOld = bytes("Httpd\n", "UTF-8")
	bNew = bytes("httpd\n", "UTF-8")
	bResult = False
	try:
		with open(strFilename, "rb") as f:
			oData = f.read()
		if bOld in oData:
			with open(strFilename, "wb") as f:
				f.write(oData.replace(bOld, bNew))
			log("Migration der Datei '%s' erfolgreich" % (
				strFilename))
			bResult = True
		else:
			wrn("Migration auf Datei '%s' nicht anwendbar" % (
				strFilename))
		if oData:
			del oData
	except:
		exc("Migration der Datei '%s' fehlgeschlagen" % (
			strFilename))
	return bResult
	
def saveSettings():
	dbg("Einstellungen für Speichern vorbereiten")
	# >>> Critical Section
	with s_oSettingsLock:
		# Einstellungen vorbereiten
		if (not "System" in s_dictSettings):
			s_dictSettings.update({"System" : {}})
		# Konfigurationsparameter synchronisieren
		s_dictSettings["System"].update({
			"strLogLvl" : getLogLvl()
		})
		
		# Einstellungen speichern
		dbg("Speichern der Einstellungen")
		try:
			foFile = open(s_strConfigFile, "w")
			json.dump(s_dictSettings, foFile, sort_keys=True)
			foFile.close()
		except:
			exc("Speichern der Einstellungen in %s" % (
				s_strConfigFile))
	# <<< Critical Section
	
	# Startseite speichern
	dbg("Speichern der Startseite")
	if s_oStartPage:
		try:
			with open(s_strStartPageFile, "wb") as f:
				pickle.dump(s_oStartPage, f, pickle.HIGHEST_PROTOCOL)
		except:
			exc("Speichern der Startseite in %s" % (
				s_strStartPageFile))
	
	# Snapshot des Fehlerspeichers sichern
	dbg("Abbild des Fehlerspeichers speichern")
	# >>> Critical Section
	with s_oLogMemLock:
		oSnapshot = list(s_oLogMem)
	# <<< Critical Section	
	if oSnapshot:
		try:
			with open(s_strLogMemFile, "wb") as f:
				pickle.dump(oSnapshot, f, pickle.HIGHEST_PROTOCOL)
		except:
			exc("Speichern des Fehlerspeichers in %s" % (
				s_strLogMemFile))				
		del oSnapshot
		
	return
	
def scanSoundFiles(bRescan=False, bClear=False):
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if "Sounds" not in s_dictSettings:
				bRescan = True
			elif bClear:
				s_dictSettings["Sounds"].clear()
				bRescan = True
		except:
			exc("Erfassen von Klangdateien")
	# <<< Critical Section
	if not bRescan:
		return
	
	lstDir = (
		getSetting("System", "strSysSoundLocation",
			varDefault="/usr/share/scratch/Media/Sounds"),
		getSetting("System", "strUsrSoundLocation",
			varDefault=s_strSoundPath))
		
	for strDir in lstDir:
		# Verzeichnisstruktur scannen (Kategorie, Datei)
		try:
			for strCategory in os.listdir(strDir):
				strFile = None
				strPath = os.path.join(strDir, strCategory)
				if os.path.isdir(strPath):
					for strEntry in os.listdir(strPath):
						strFile = os.path.join(strPath, strEntry)
						if os.path.isfile(strFile):
							registerSoundFile(strFile, strCategory)
				elif os.path.isfile(strPath):
					strFile = strPath
					registerSoundFile(strFile)
		except:
			exc("Erfassen von Klangdateien aus: '%s'" % (strDir))
	return
	
def registerSoundFile(strFile, strCategory="Default"):
	_, strTail = os.path.split(strFile)
	if not strTail:
		return
	strName, strExt = os.path.splitext(strTail)
	if not strExt or not strName:
		return
	if not re.match("\\.([Ww][Aa][Vv]|[Mm][Pp]3)", strExt):
		return
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if "Sounds" not in s_dictSettings:
				s_dictSettings.update({"Sounds" : {}})
			if not strCategory in s_dictSettings["Sounds"]:
				s_dictSettings["Sounds"].update({strCategory : {}})
			s_dictSettings["Sounds"][strCategory].update({strName : strFile})
		except:
			exc("Klangdatei erfassen: '%s'" % (strFile))
	# <<< Critical Section
	return

def scanImageFiles(bRescan=False, bClear=False):
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if "Images" not in s_dictSettings:
				bRescan = True
			elif bClear:
				s_dictSettings["Images"].clear()
				bRescan = True
		except:
			exc("Erfassen von Bilddateien")
	# <<< Critical Section
	if not bRescan:
		return
	
	lstDir = (
		getSetting("System", "strSysImageLocation",
			varDefault="/usr/share/icons/Adwaita/32x32"),
		getSetting("System", "strUsrImageLocation",
			varDefault=s_strImagePath))
		
	for strDir in lstDir:
		# Verzeichnisstruktur scannen (Kategorie, Datei)
		try:
			for strCategory in os.listdir(strDir):
				strFile = None
				strPath = os.path.join(strDir, strCategory)
				if os.path.isdir(strPath):
					for strEntry in os.listdir(strPath):
						strFile = os.path.join(strPath, strEntry)
						if os.path.isfile(strFile):
							registerImageFile(strFile, strCategory)
				elif os.path.isfile(strPath):
					strFile = strPath
					registerImageFile(strFile)
		except:
			exc("Erfassen von Bilddateien aus: '%s'" % (strDir))
	return
	
def registerImageFile(strFile, strCategory="Default"):
	_, strTail = os.path.split(strFile)
	if not strTail:
		return
	strName, strExt = os.path.splitext(strTail)
	if not strExt or not strName:
		return
	# if not re.match("\\.([Ww][Aa][Vv]|[Mm][Pp]3)", strExt):
	# 	return
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if "Images" not in s_dictSettings:
				s_dictSettings.update({"Images" : {}})
			if not strCategory in s_dictSettings["Images"]:
				s_dictSettings["Images"].update({strCategory : {}})
			s_dictSettings["Images"][strCategory].update({strName : strFile})
		except:
			exc("Bilddatei erfassen: '%s'" % (strFile))
	# <<< Critical Section
	return

def findMatchingImageFile(strImage):
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if "Images" in s_dictSettings:
				# Direkte Übereinstimmung finden
				strFile = None
				for (strCategory, dictSounds) in s_dictSettings["Images"].items():
					if strImage in dictSounds:
						strFile = s_dictSettings["Images"][strCategory][strImage]
						break
				if not strFile:
					# Partiellen Treffer finden
					for (strCategory, dictSounds) in sorted(s_dictSettings["Images"].items()):
						for (strName, strPath) in dictSounds.items():
							if re.match(strImage + ".*", strName):
								log("Bild '%s' für angefordertes Bild '%s' verwendet." % (
									strName, strImage))
								strFile = strPath
								break
							if re.match(".*" + strImage + ".*", strName):
								log("Bild '%s' für angefordertes Bild '%s' verwendet." % (
									strName, strImage))
								strFile = strPath
								break
		except:
			exc("Bilddatei '%s' finden" % (strImage))
	# <<< Critical Section
	return strFile

def registerPipPackage(
	bMissing,
	strPackage,
	strTitle,
	strDescription):
	if not strPackage or not strTitle or not strDescription:
		err("Ungültige Parameter '%s', '%s', '%s' für optionale Installation von Python-Packages" % (
			strPackage, strTitle, strDescription))
		return
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if "PIP" not in s_dictSettings:
				s_dictSettings.update({"PIP" : {}})
			if "PIP" not in s_dictUserSettings:
				s_dictUserSettings.update({"PIP" : {}})
			s_dictSettings["PIP"].update({strPackage : "install" if bMissing else "uninstall"})
			s_dictUserSettings["PIP"].update(
				{strPackage : {
					"title"			: "%s (%s)" % (strTitle, strPackage),
					"description"	: strDescription,
					"default"		: "install",
					"choices"		: {
						"Paket hinzufügen"	: "install",
						"Paket entfernen" 	: "uninstall"
					}
				}})
			log("Optional installierbares Python-Paket erfasst: '%s'" % (strPackage))
		except:
			exc("Optional installierbares Python-Paket erfassen: '%s'" % (strPackage))
	# <<< Critical Section
	return

def isMissingPipPackage(strPackage):
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if ("PIP" in s_dictSettings
				and s_dictSettings["PIP"]
				and strPackage in s_dictSettings["PIP"].keys()
				and s_dictSettings["PIP"][strPackage] == "uninstall"):
				return False
		except:
			exc("Optional installierbares Python-Paket abfragen: '%s'" % (strPackage))
	# <<< Critical Section
	return True

def unregisterPipPackage(
	strPackage):
	if not strPackage:
		err("Ungültiger Parameter '%s' für das Verwerfen von Python-Packages" % (
			strPackage))
		return
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if ("PIP" in s_dictSettings
				and strPackage in s_dictSettings["PIP"]):
				s_dictSettings["PIP"].pop(strPackage)
			if ("PIP" in s_dictUserSettings
				and strPackage in s_dictUserSettings["PIP"]):
				s_dictUserSettings["PIP"].pop(strPackage)
			log("Optional installierbares Python-Paket verworfen: '%s'" % (strPackage))
		except:
			exc("Optional installierbares Python-Paket verwerfen: '%s'" % (strPackage))
	# <<< Critical Section
	return

def updateModuleUserSetting(
	strModule,
	strSettingsName,
	dictSettingsDesc):

	if not strModule or not strSettingsName or not dictSettingsDesc:
		err("Ungültiger Parameter '%s', '%s', %r für das Aktualisieren von Benutzereinstellungen" % (
			strModule, strSettingsName, dictSettingsDesc))
		return

	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if (strModule in s_dictUserSettings
				and strModule in s_dictSettings
				and strSettingsName in s_dictUserSettings[strModule]
				and strSettingsName in s_dictSettings[strModule]):

				s_dictUserSettings[strModule].update({strSettingsName : dictSettingsDesc})		
				log("Benutzereinstellungen aktualisiert: '%s', '%s', %r" % (strModule, strSettingsName, dictSettingsDesc))
			else:
				err("Benutzereinstellungen aktualisiert: '%s', '%s', %r" % (strModule, strSettingsName, dictSettingsDesc))
		except:
			exc("Benutzereinstellungen aktualisieren: '%s', '%s', %r" % (strModule, strSettingsName, dictSettingsDesc))
	# <<< Critical Section

	return
	
def dbg(strText):
	# >>> Critical Section
	with s_oLogMemLock:
		if s_nLogLvl >= 4:
			oEntry = LogEntry(
				strType="DBG",
				strText=strText,
				lstTB=traceback.extract_stack())
			print("%s" % (oEntry))
			s_oLogMem.appendleft(oEntry)
	# <<< Critical Section
	return

def log(strText):
	# >>> Critical Section
	with s_oLogMemLock:
		if s_nLogLvl >= 3:
			oEntry = LogEntry(
				strType="INF",
				strText=strText,
				lstTB=traceback.extract_stack())
			print("%s" % (oEntry))
			s_oLogMem.appendleft(oEntry)
	# <<< Critical Section
	return

def wrn(strText):
	# >>> Critical Section
	with s_oLogMemLock:
		if s_nLogLvl >= 2:
			oEntry = LogEntry(
				strType="WRN",
				strText=strText,
				lstTB=traceback.extract_stack())
			print("%s" % (oEntry))
			s_oLogMem.appendleft(oEntry)
	# <<< Critical Section
	return

def err(strText):
	# >>> Critical Section
	with s_oLogMemLock:
		if s_nLogLvl >= 1:
			oEntry = LogEntry(
				strType="ERR",
				strText=strText,
				lstTB=traceback.extract_stack())
			print("%s" % (oEntry))
			s_oLogMem.appendleft(oEntry)
	# <<< Critical Section
	return

def exc(strText):
	exType, exValue, exTraceback = sys.exc_info()
	oEntry = LogEntry(
		strType="EXC",
		strText="%s: %s (%s)" % (strText, exValue, exType),
		lstTB=traceback.extract_tb(exTraceback))
	print("%s" % (oEntry))
	# >>> Critical Section
	with s_oLogMemLock:
		s_oLogMem.appendleft(oEntry)
	# <<< Critical Section
	return

# Liefert einen Snapshot des Fehlerspeichers zurück.
# Nur wenn bUpdate True ist, wird der Inhalt des
# Snapshots auf den augenblicklichen Zustand des
# Fehlerspeichers angeglichen.
def getLogMem(bUpdate=False):
	global s_lstSnapshot
	
	# >>> Critical Section
	with s_oLogMemLock:
		if bUpdate or not s_lstSnapshot:
			s_lstSnapshot = list(s_oLogMem)
	# <<< Critical Section
	return s_lstSnapshot

# Verändert die aktuelle Detail-Tiefe für den Trace.
def setLogLvl(strLogLvl):
	global s_nLogLvl
	
	nLogLvl = 0
	if strLogLvl and strLogLvl == "DBG":
		nLogLvl = 4
	elif strLogLvl and strLogLvl == "INF":
		nLogLvl = 3
	elif strLogLvl and strLogLvl == "WRN":
		nLogLvl = 2
	elif strLogLvl and strLogLvl == "ERR":
		nLogLvl = 1
	else:
		nLogLvl = 0
	# >>> Critical Section
	with s_oLogMemLock:
		s_nLogLvl = nLogLvl
	# <<< Critical Section
	return

# Liefert die aktuelle Detail-Tiefe für den Trace	
def getLogLvl():
	global s_nLogLvl
	
	strLogLvl = "EXC"
	# >>> Critical Section
	with s_oLogMemLock:
		if s_nLogLvl == 4:
			strLogLvl = "DBG"
		elif s_nLogLvl == 3:
			strLogLvl = "INF"
		elif s_nLogLvl == 2:
			strLogLvl = "WRN"
		elif s_nLogLvl == 1:
			strLogLvl = "ERR"
		else:
			s_nLogLvl = 0
			strLogLvl = "EXC"
	# <<< Critical Section
	return strLogLvl
	
def getSetting(
	strKeyName,
	strValName,
	strRegEx=".*",
	varDefault=None
	):
	varValue = varDefault
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			if (strKeyName in s_dictSettings
				and strValName in s_dictSettings[strKeyName]
				and re.match(strRegEx, "%s" % (s_dictSettings[strKeyName][strValName]))):
				if varDefault == None:
					varValue = s_dictSettings[strKeyName][strValName]
				elif (isinstance(s_dictSettings[strKeyName][strValName], type(varDefault))):
					varValue = s_dictSettings[strKeyName][strValName]
				else:
					err("Konfigurationseinstellung holen: \"%s\".\"%s\"=\"%s\" (RexEx \"%s\", Default: \"%r\") - Erwartet wurde Typ \"%s\" jedoch liegt Typ \"%s\" vor" % (
						strKeyName, strValName,
						s_dictSettings[strKeyName][strValName],
						strRegEx, varDefault,
						type(varDefault), 						
						type(s_dictSettings[strKeyName][strValName])))
		except:
			exc("Konfigurationseinstellung holen: \"%s\".\"%s\" (RexEx \"%s\", Default: \"%r\")" % (
				strKeyName, strValName, strRegEx, varDefault))
	# <<< Critical Section
	return varValue
	
def setSetting(
	strKeyName,
	strValName,
	varValue
	):
	global s_dictSettings
	
	bResult = False
	# >>> Critical Section
	with s_oSettingsLock:
		try:
			primitives = (bool, int, float, str)
			if strKeyName in s_dictSettings:
				if strValName in s_dictSettings[strKeyName]:
					varOldVal = s_dictSettings[strKeyName][strValName]
					oOldType = type(varOldVal)
					oSetType = type(varValue)
					varNewVal = None					
					oNewType = oSetType
					if isinstance(varValue, oOldType):
						varNewVal = varValue
					elif isinstance(varValue, primitives):
						if isinstance(varOldVal, bool):
							varNewVal = (("%s" % (varValue)) == "True")
							oNewType = type(varNewVal)
						else:
							varNewVal = oOldType("%s" % (varValue))
							oNewType = type(varNewVal)
					if varNewVal == None:
						err("Konfiguration \"%s\".\"%s\" von \"%s\" %r auf \"%s\" %r ändern: Unverträgliche Datentypen!" % (
							strKeyName, strValName, varOldVal, oOldType, varValue, oSetType))
					else:
						s_dictSettings[strKeyName][strValName] = varNewVal
						bResult = True
						dbg("Konfiguration \"%s\".\"%s\" von \"%s\" %r auf \"%s\" %r geändert." % (
							strKeyName, strValName, varOldVal, oOldType, varNewVal, oNewType))
				else:
					err("Konfigurationseinstellung setzen: \"%s\".\"%s\" -> \"%s\" - Adressierter Wert existiert nicht" % (
						strKeyName, strValName, varValue))
			else:
				err("Konfigurationseinstellung setzen: \"%s\".\"%s\" -> \"%s\" - Adressierter Schlüssel existiert nicht" % (
					strKeyName, strValName, varValue))
		except:
			exc("Konfigurationseinstellung setzen: \"%s\".\"%s\" -> \"%s\"" % (
				strKeyName, strValName, varValue))
	# <<< Critical Section
	return bResult

class LogEntry:
	
	def __init__(self,
		strType="",
		strText="",
		lstTB=None):
		self.m_strType = strType
		self.m_strDate = datetime.datetime.today().strftime("%d.%m.%Y  %H:%M:%S.%f")
		self.m_strText = strText
		# Liste von 4-Tuples (filename, line number, function name, text)
		if not lstTB:
			lstTB = traceback.extract_stack()
		lstTB = list(reversed(lstTB))
		if (len(lstTB) > 1) and (not strType == "EXC"):
			self.m_lstTB = lstTB[1:]
		else:
			self.m_lstTB = lstTB
		return
		
	def __str__(self):
		strDesc = "[%s] %s - %s" % (self.m_strType, self.m_strDate, self.m_strText)
		if (self.m_lstTB and self.m_strType == "EXC"):
			strDesc += "\n"
			for (filename, line, function, text) in self.m_lstTB:
				strDesc += "  File \"%s\", line %s, in %s\n    %s\n" % (
					filename, line, function, text)
		return strDesc
