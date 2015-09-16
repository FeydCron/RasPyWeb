import io
import os
import sys
import json
import re
import traceback
import pickle
import threading
import socket

from collections import deque
from collections import OrderedDict
from datetime import datetime

class LogEntry:
	
	def __init__(self,
		strType = "",
		strText = "",
		lstTB = None):
		self.m_strType = strType
		self.m_strDate = datetime.today().strftime("%d.%m.%Y  %H:%M:%S.%f")
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

class Globs:
	
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
	
	s_dictSettings = {
		# Registrierung der installierten Module
		# {"<Paket/Modul>" : "<Klasse>"}
		"dictModules" : {},
		# Auflistung der explizit deaktivierten Module
		# ["<Paket/Modul>", ...]
		"listInactiveModules" : [],
		# Systemeinstellungen
		# {"<Eigenschaft>" : "<Wert>"}
		"System" : {
			"strLogLvl" 		: "DBG",		# Aktuelles Log-Level
			"bTestMode" 		: False,		# Aktivierung des Testmodus
			"strHttpIp" 		: "0.0.0.0",	# IP-Adresse für den HTTP-Server
			"nHttpPort" 		: 8081,			# Portnummer für den HTTP-Server
			"strNetInfoName"	: "google.com",	# Computername zum ermitteln der eigenen IP-Adresse
			"fCpuTempA" 		: 60.0,			# Abschalt-Temperaturgrenze
			"fCpuTempB" 		: 56.0,			# Kritische Temperaturgrenze
			"fCpuTempC" 		: 53.0,			# Warn-Temperaturgrenze
			"strSoundLocation"	: "/usr/share/scratch/Media/Sounds",
		},
		# HTTP-Weiterleitungen
		# {"<ID>" : "<URL>"}
		"Redirects" : {
			"startpage" : "/system/startpage.html"
		}
	}
	
	# Parameterdefinitionen
	# {"<Schlüssel>" : {"<Name>" : {"" : ""}}}
	# 
	# Die Initialisierung über ein normales dict, mit chaotischer Sortierung
	# macht an dieser Stelle nur deshalb Sinn, weil das Dictionary auf
	# oberster Ebene nur einen Schlüssel enthält.
	#
	s_dictUserSettings = OrderedDict({
		"System" : {
			"bTestMode" : {
				"title"			: "Testmodus",
				"description"	: ("Der Testmodus ist eine Eigenschaft, die von anderen Modulen "+
									"oder Programmteilen für Testzwecke verwendet werden kann, "+
									"um zum Beispiel spezielle Testfunktionen ein- oder auszuschalten."),
				"default"		: "Aus"
			},
			"strHttpIp" : {
				"title"			: "Web-Server IP-Adresse",
				"description"	: ("Wenn der Raspberry über mehrere Netzwerkschnittstellen "+
									"verfügt, kann hier die IP-Adresse eingestellt werden, "+
									"unter welcher das Web-Interface erreichbar sein soll. "+
									"ACHTUNG: Eine falsche Einstellung kann das Web-Interface "+
									"unerreichbar machen!"),
				"default"		: "0.0.0.0"
			},
			"nHttpPort" : {
				"title"			: "Web-Server TCP-Portnummer",
				"description"	: ("Die TCP-Portnummer, unter welcher das Web-Interface "+
									"erreichbar sein soll, kann geändert werden, wenn die "+
									"Standardeinstellung in Konflikt mit einem anderen Programm "+
									"steht, welches die TCP-Portnummer für sich  beansprucht. "+
									"ACHTUNG: Eine falsche Einstellung kann das Web-Interface "+
									"unerreichbar machen!"),
				"default"		: "8081"
			},
			"strNetInfoName" : {
				"title"			: "Referenz-Computername",
				"description"	: ("Die Einstellung legt den Computernamen bzw. dessen "+
									"IP-Adresse fest, um damit die eigene IP-Adresse "+
									"ermitteln zu können. Bei vorhandener Internetverbindung "+
									"kann der Standard beibehalten oder ein anderer "+
									"namhafter Internet-Host verwendet werden. Steht kein "+
									"Internet zur Verfügung, muss sich der betreffende "+
									"Computer im gleichen Netzwerk befinden und erreichbar "+
									"sein. Ist der Raspberry netzwerktechnisch eine einsame "+
									"Insel, muss auf localhost bzw. 127.0.0.1 zurückgegriffen werden."),
				"default"		: "google.com"
			},
			"fCpuTempA" : {
				"title"			: "Temperaturgrenze Notabschaltung",
				"description"	: ("Legt die Temperaturgrenze für die CPU in Grad Celsius fest, "+
									"bei deren Überschreitung über einen längeren Zeitraum "+
									"die Notabschaltung des Systems zu veranlassen ist."),
				"default"		: "60.0"
			},
			"fCpuTempB" : {
				"title"			: "Temperaturgrenze Kritisch",
				"description"	: ("Legt die Temperaturgrenze für die CPU in Grad Celsius fest, "+
									"bei deren Überschreitung jeweils Meldung über die kritische "+
									"Betriebstemperatur der CPU zu veranlassen ist."),
				"default"		: "56.0"
			},
			"fCpuTempC" : {
				"title"			: "Temperaturgrenze Warnung",
				"description"	: ("Legt die Temperaturgrenze für die CPU in Grad Celsius fest, "+
									"bei deren Überschreitung jeweils Meldung über die hohe "+
									"Betriebstemperatur der CPU zu veranlassen ist."),
				"default"		: "53.0"
			},
			"strSoundLocation" : {
				"title"			: "Sound-Datei Ablageort",
				"description"	: ("Legt den Ablageort der Sound-Dateien fest, die für das System, "+
									"zur Verfügung stehen sollen. Beim Installieren neuer Sounds "+
									"werden diese dort abgelegt, gegebenenfalls auch in neuen "+
									"Unterordnern zur Kategorisierung."),
				"default"		: "/usr/share/scratch/Media/Sounds"
			}
		},
	})
	
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
	
	s_oLogMem = deque([], 255)
	s_oLogMemLock = threading.RLock()
	s_oSettingsLock = threading.RLock()
	
	s_strModulePath = "/home/pi/berry/modules"
	s_strConfigFile = "/home/pi/berry/config.json"
	s_strLogMemFile = "/home/pi/berry/logmem.pickle"
	s_strStartPageFile = "/home/pi/berry/startpage.pickle"
	s_strStartPageUrl = "/system/startpage.html"
	
	s_oHttpd = None
	s_lstSnapshot = None
	s_oStartPage = None
	
	def getRedirect(strID, strDefault):
		if ("Redirects" in Globs.s_dictSettings
			and strID in Globs.s_dictSettings["Redirects"]):
			return Globs.s_dictSettings["Redirects"][strID]
		Globs.wrn("Keine Weiterleitung auf \"%s\" bekannt. Default: \"%s\"" % (
			strID, strDefault))
		return strDefault
	
	def stop():
		if Globs.s_oHttpd:
			Globs.s_oHttpd.shutdown()
			Globs.s_oHttpd.server_close()
			try:
				Globs.s_oHttpd.socket.shutdown(socket.SHUT_RDWR)
				Globs.s_oHttpd.socket.close()
			except Exception as ex:
				print("Schließen des Sockets sicherstellen: %r" % (ex))
		return
	
	def importComponent(strModuleName, strComponentName):
		try:
			Globs.log("Importieren des Moduls '%s'" % (strModuleName))
			oComponent = __import__(strModuleName)
			strFullName = strModuleName + "." +  strComponentName
			lstComponents = strFullName.split(".")
			for strComponent in lstComponents[1:]:
				Globs.log("Laden des Attributes '%s' aus dem Objekt '%r'" % (
					strComponent, oComponent))
				oComponent = getattr(oComponent, strComponent)
		except:
			Globs.exc("Importieren der Komponente %s aus dem Modul %s" % (
				strComponentName, strModuleName))
			oComponent = None
		return oComponent
	
	def loadSettings():
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		# Einstellungen lesen
		try:
			foFile = open(Globs.s_strConfigFile, "r")
			oObj = json.load(foFile)
			foFile.close()
			for (strKey, varVal) in oObj.items():
				if (strKey == "System"
					and strKey in Globs.s_dictSettings):
					Globs.s_dictSettings[strKey].update(oObj[strKey])
				else:
					Globs.s_dictSettings.update({strKey : varVal})
		except:
			Globs.exc("Laden der Einstellungen von %s" % (
				Globs.s_strConfigFile))
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
				
		# Fehlerspeicher wiederherstellen
		oLogMem = None
		try:
			with open(Globs.s_strLogMemFile, "rb") as f:
				oLogMem = pickle.load(f)
		except:
			Globs.exc("Laden des Fehlerspeichers von %s" % (
				Globs.s_strLogMemFile))
		# Aktuellen und gelesenen Fehlerspeicher konsistent zusammenführen
		if oLogMem:
			# >>> Critical Section
			Globs.s_oLogMemLock.acquire()
			oBackup = list(Globs.s_oLogMem)
			Globs.s_oLogMem.clear()
			Globs.s_oLogMem.extendleft(reversed(oLogMem))
			Globs.s_oLogMem.extendleft(reversed(oBackup))
			Globs.s_oLogMemLock.release()
			# <<< Critical Section
			del oLogMem
			del oBackup
			
		# Konfigurationsparameter synchronisieren
		if ("System" in Globs.s_dictSettings):
			if ("strLogLvl" in Globs.s_dictSettings["System"]):
				Globs.setLogLvl(Globs.s_dictSettings["System"]["strLogLvl"])
				
		# Startseite lesen
		try:
			with open(Globs.s_strStartPageFile, "rb") as f:
				Globs.s_oStartPage = pickle.load(f)
		except:
			Globs.exc("Laden der Startseite von %s" % (
				Globs.s_strStartPageFile))
				
		# Sounds einmalig scannen
		Globs.scanSoundFiles()
				
		Globs.log("Konfiguration: %r" % (Globs.s_dictSettings))
		Globs.log("Startseite: %r" % (Globs.s_oStartPage))
		return
		
	def saveSettings():
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		# Einstellungen vorbereiten
		if (not "System" in Globs.s_dictSettings):
			Globs.s_dictSettings.update({"System" : {}})
		# Konfigurationsparameter synchronisieren
		Globs.s_dictSettings["System"].update({
			"strLogLvl" : Globs.getLogLvl()
		})
		# Einstellungen speichern
		try:
			foFile = open(Globs.s_strConfigFile, "w")
			strDump = json.dump(Globs.s_dictSettings, foFile, sort_keys=True)
			foFile.close()
		except:
			Globs.exc("Speichern der Einstellungen in %s" % (
				Globs.s_strConfigFile))
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		
		# Fehlerspeicher speichern
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		oSnapshot = list(Globs.s_oLogMem)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		try:
			with open(Globs.s_strLogMemFile, "wb") as f:
				pickle.dump(oSnapshot, f, pickle.HIGHEST_PROTOCOL)
		except:
			Globs.exc("Speichern des Fehlerspeichers in %s" % (
				Globs.s_strLogMemFile))				
		del oSnapshot
		
		# Startseite speichern
		if Globs.s_oStartPage:
			try:
				with open(Globs.s_strStartPageFile, "wb") as f:
					pickle.dump(Globs.s_oStartPage, f, pickle.HIGHEST_PROTOCOL)
			except:
				Globs.exc("Speichern der Startseite in %s" % (
					Globs.s_strStartPageFile))
			
		return
		
	def scanSoundFiles(strDir=None, bRescan=False, bClear=False):
		if not strDir:
			strDir = Globs.getSetting("System", "strSoundLocation",
				varDefault="/usr/share/scratch/Media/Sounds")
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		try:
			if "Sounds" not in Globs.s_dictSettings:
				bRescan = True
			elif bClear:
				Globs.s_dictSettings["Sounds"].clear()
				bRescan = True
		except:
			Globs.exc("Sound-Dateien in '%s' scannen" % (strDir))
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		if not bRescan:
			return
		# Verzeichnisstruktur scannen (Kategorie, Datei)
		for strCategory in os.listdir(strDir):
			strFile = None
			strPath = os.path.join(strDir, strCategory)
			if os.path.isdir(strPath):
				for strEntry in os.listdir(strPath):
					strFile = os.path.join(strPath, strEntry)
					if os.path.isfile(strFile):
						Globs.registerSoundFile(strFile, strCategory)
			elif os.path.isfile(strPath):
				strFile = strPath
				Globs.registerSoundFile(strFile)
		return
		
	def registerSoundFile(strFile, strCategory="Default"):
		strHead, strTail = os.path.split(strFile)
		if not strTail:
			return
		strName, strExt = os.path.splitext(strTail)
		if not strExt or not strName:
			return
		if not re.match("\\.([Ww][Aa][Vv]|[Mm][Pp]3)", strExt):
			return
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		try:
			if "Sounds" not in Globs.s_dictSettings:
				Globs.s_dictSettings.update({"Sounds" : {}})
			if not strCategory in Globs.s_dictSettings["Sounds"]:
				Globs.s_dictSettings["Sounds"].update({strCategory : {}})
			Globs.s_dictSettings["Sounds"][strCategory].update({strName : strFile})
		except:
			Globs.exc("Sound-Datei '%s' registrieren" % (strFile))
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		return
		
	def dbg(strText):
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		if Globs.s_nLogLvl >= 4:
			oEntry = LogEntry(
				strType = "DBG",
				strText = strText,
				lstTB = traceback.extract_stack())
			print("%s" % (oEntry))
			Globs.s_oLogMem.appendleft(oEntry)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return
	
	def log(strText):
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		if Globs.s_nLogLvl >= 3:
			oEntry = LogEntry(
				strType = "INF",
				strText = strText,
				lstTB = traceback.extract_stack())
			print("%s" % (oEntry))
			Globs.s_oLogMem.appendleft(oEntry)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return
	
	def wrn(strText):
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		if Globs.s_nLogLvl >= 2:
			oEntry = LogEntry(
				strType = "WRN",
				strText = strText,
				lstTB = traceback.extract_stack())
			print("%s" % (oEntry))
			Globs.s_oLogMem.appendleft(oEntry)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return
	
	def err(strText):
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		if Globs.s_nLogLvl >= 1:
			oEntry = LogEntry(
				strType = "ERR",
				strText = strText,
				lstTB = traceback.extract_stack())
			print("%s" % (oEntry))
			Globs.s_oLogMem.appendleft(oEntry)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return
	
	def exc(strText):
		exType, exValue, exTraceback = sys.exc_info()
		oEntry = LogEntry(
			strType = "EXC",
			strText = "%s: %s (%s)" % (strText, exValue, exType),
			lstTB = traceback.extract_tb(exTraceback))
		print("%s" % (oEntry))
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		Globs.s_oLogMem.appendleft(oEntry)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return
	
	# Liefert einen Snapshot des Fehlerspeichers zurück.
	# Nur wenn bUpdate True ist, wird der Inhalt des
	# Snapshots auf den augenblicklichen Zustand des
	# Fehlerspeichers angeglichen.
	def getLogMem(bUpdate = False):
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		if bUpdate or not Globs.s_lstSnapshot:
			Globs.s_lstSnapshot = list(Globs.s_oLogMem)
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return Globs.s_lstSnapshot
	
	# Verändert die aktuelle Detail-Tiefe für den Trace.
	def setLogLvl(strLogLvl):
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
		Globs.s_oLogMemLock.acquire()
		Globs.s_nLogLvl = nLogLvl
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return
	
	# Liefert die aktuelle Detail-Tiefe für den Trace	
	def getLogLvl():
		strLogLvl = "EXC"
		# >>> Critical Section
		Globs.s_oLogMemLock.acquire()
		if Globs.s_nLogLvl == 4:
			strLogLvl = "DBG"
		elif Globs.s_nLogLvl == 3:
			strLogLvl = "INF"
		elif Globs.s_nLogLvl == 2:
			strLogLvl = "WRN"
		elif Globs.s_nLogLvl == 1:
			strLogLvl = "ERR"
		else:
			Globs.s_nLogLvl = 0
			strLogLvl = "EXC"
		Globs.s_oLogMemLock.release()
		# <<< Critical Section
		return strLogLvl
		
	def getSetting(
		strKeyName,
		strValName,
		strRegEx = ".*",
		varDefault = None
		):
		varValue = varDefault
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		try:
			if (strKeyName in Globs.s_dictSettings
				and strValName in Globs.s_dictSettings[strKeyName]
				and re.match(strRegEx, "%s" % (Globs.s_dictSettings[strKeyName][strValName]))):
				if varDefault == None:
					varValue = Globs.s_dictSettings[strKeyName][strValName]
				elif (isinstance(Globs.s_dictSettings[strKeyName][strValName], type(varDefault))):
					varValue = Globs.s_dictSettings[strKeyName][strValName]
				else:
					Globs.err("Konfigurationseinstellung holen: \"%s\".\"%s\"=\"%s\" (RexEx \"%s\", Default: \"%r\") - Erwartet wurde Typ \"%s\" jedoch liegt Typ \"%s\" vor" % (
						strKeyName, strValName, 
						Globs.s_dictSettings[strKeyName][strValName],
						strRegEx, varDefault,
						type(varDefault),						
						type(Globs.s_dictSettings[strKeyName][strValName])))
		except:
			Globs.exc("Konfigurationseinstellung holen: \"%s\".\"%s\" (RexEx \"%s\", Default: \"%r\")" % (
				strKeyName, strValName, strRegEx, varDefault))
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		return varValue
		
	def setSetting(
		strKeyName,
		strValName,
		varValue
		):
		bResult = False
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		try:
			primitives = (bool, int, float, str)
			if strKeyName in Globs.s_dictSettings:
				if strValName in Globs.s_dictSettings[strKeyName]:
					varOldVal = Globs.s_dictSettings[strKeyName][strValName]
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
						Globs.err("Konfiguration \"%s\".\"%s\" von \"%s\" %r auf \"%s\" %r ändern: Unverträgliche Datentypen!" % (
							strKeyName, strValName, varOldVal, oOldType, varValue, oSetType))
					else:
						Globs.s_dictSettings[strKeyName][strValName] = varNewVal
						bResult = True
						Globs.log("Konfiguration \"%s\".\"%s\" von \"%s\" %r auf \"%s\" %r geändert." % (
							strKeyName, strValName, varOldVal, oOldType, varNewVal, oNewType))
				else:
					Globs.err("Konfigurationseinstellung setzen: \"%s\".\"%s\" -> \"%s\" - Adressierter Wert existiert nicht" % (
						strKeyName, strValName, varValue))
			else:
				Globs.err("Konfigurationseinstellung setzen: \"%s\".\"%s\" -> \"%s\" - Adressierter Schlüssel existiert nicht" % (
					strKeyName, strValName, varValue))
		except:
			Globs.exc("Konfigurationseinstellung setzen: \"%s\".\"%s\" -> \"%s\"" % (
				strKeyName, strValName, varValue))
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		return bResult
