## 
#  Plug-In für die Anbindung einer Divoom Timebox an RasPyWeb
#  
#  @file Timebox.py
#  @brief Plug-In für Divoom Timebox.
#  

import globs

import sdk
from sdk import ModuleBase
from sdk import TaskSpeak

import bluetooth
from bluetooth import *

def createModuleInstance(
	oWorker):
	return Timebox(oWorker)

class Timebox(ModuleBase):
	
	## 
	#  @copydoc sdk::ModuleBase::moduleInit
	#  
	def moduleInit(self, dictModCfg=None, dictCfgUsr=None):
		
		# Verfügbare Einstellungen mit Default-Werten festlegen
		dictSettings = {
			"strAddress" : "",
			"nPort" : 4,
			"bAutoConnect" : False
		}
		# Vorbelegung der Moduleigenschaften mit Default-Werten, sofern noch nicht verfügbar
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})

		# Beschreibung der Konfigurationseinstellungen
		dictCfgUsr.update({
			"strAddress" : {
				"title"			: "Adresse der Timebox",
				"description"	: ("Einstellung der Adresse einer Timebox, zu der eine Verbindung hergestellt werden soll."),
				"default"		: "",
				"choices"		: {
					"Keine Timebox verfügbar"		: ""
				}
			},
			"nPort" : {
				"title"			: "Portnummer für RFCOMM",
				"description"	: ("Einstellung der Portnummer für RFCOMM mit einer Timebox."),
				"default"		: 4
			},
			"bAutoConnect" : {
				"title"			: "Automatischer Verbindungsaufbau",
				"description"	: ("Automatischen oder manuellen Verbindungsaufbau aktivieren."),
				"default"		: False,
				"choices"		: {
					"Automatisch verbinden"	: True,
					"Manuell verbinden"		: False
				}
			},
			})

		# Auslesen der aktuellen Konfigurationseinstellungen
		self.m_strAddress = globs.getSetting("Timebox", "strAddress", "^([0-9a-fA-F]{2}[:]){5}([0-9A-F]{2})$", "")
		self.m_nPort = globs.getSetting("Timebox", "nPort", "\\d{1,5}", 4)
		self.m_bAutoConnect = globs.getSetting("Timebox", "bAutoConnect", "(True|False)", False)

		self.m_oTimeboxSocket = None

		# TODO
		# - Nach verfügbaren Bluetooth Geräten suchen (zyklisch, solange keine Timebox-Geräte gefunden wurden)
		# - Je nach Einstellung automatisch die Verbindung aufbauen

		return True
	
	## 
	#  @brief Brief
	#  
	#  @param [in] self Parameter_Description
	#  @return Return_Description
	#  
	#  @details Details
	#  	
	def moduleExit(self):

		if self.m_oTimeboxSocket:
			self.m_oTimeboxSocket.close()
			self.m_oTimeboxSocket = None

		return True
	
	
	#==============================================================================
	# moduleWidget
	#==============================================================================
	def moduleWidget(self):
		pass
	

	## 
	#  @brief Ausführung der Modulaktion.
	#  
	#  @param [in] self			Objektinstanz
	#  @param [in] strPath		die angeforderte Pfadangabe
	#  @param [in] oHtmlPage	die zu erstellende HTML-Seite
	#  @param [in] dictQuery	Dictionary der angeforderten Parameter und Werte als Liste
	#  @param [in] dictForm		Dictionary der angeforderten Formularparameter und Werte als Liste
	#  @return
	#  Liefert True, wenn die Aktion erfolgreich ausgeführt werden konnte oder
	#  False im Falle eines Fehlers.
	#  
	#  @details Details
	#  		
	def moduleExec(self,
		strPath,
		oHtmlPage,
		dictQuery,
		dictForm
		):
		print("%r::moduleExec(strPath=%s, oHtmlPage=%s, dictQuery=%r, dictForm=%r)" % (
			self, strPath, oHtmlPage, dictQuery, dictForm))

		if not dictQuery:
			return False

		bResult = False
		for (strCmd, lstArg) in dictQuery.items():
			if (strCmd == "discover"):
				for strArg in lstArg:
					# Suche nach Bluetooth-Geräten
					if (strArg == "start"):
						TaskSpeak(self.getWorker(), "Es wird nach Bluhtuhf Geräten gesucht").start()
						
						dictChoices = {
							"title"			: "Adresse der Timebox",
							"description"	: ("Einstellung der Adresse einer Timebox, zu der eine Verbindung hergestellt werden soll."),
							"default"		: "",
							"choices"		: {
								"Keine Timebox verfügbar"		: ""
							}
						}

						dictDiscovery = bluetooth.discover_devices(
							duration=8,
							lookup_names=True,
							flush_cache=True,
							lookup_class=False)

						if len(dictDiscovery) > 0:
							dictChoices["choices"].clear()

						print("dictDiscovery %r" % (dictDiscovery))

						for strAddr, strName in dictDiscovery:
							try:
								dictChoices["choices"].update({strName : strAddr})
							except:
								globs.exc("Fehler beim Auswerten der erreichbaren Bluetooth-Geräte")

						globs.updateModuleUserSetting("Timebox", "strAddress", dictChoices);

						TaskSpeak(self.getWorker(), "Die Suche nach Bluhtuhf Geräten ist abgeschlossen").start()
						continue
			if (strCmd == "timebox"):

				self.m_strAddress = globs.getSetting("Timebox", "strAddress", "^([0-9a-fA-F]{2}[:]){5}([0-9A-F]{2})$", "")
				self.m_nPort = globs.getSetting("Timebox", "nPort", "\\d{1,5}", 4)
				self.m_bAutoConnect = globs.getSetting("Timebox", "bAutoConnect", "(True|False)", False)

				for strArg in lstArg:
					# Verbindung herstellen
					if (strArg == "connect"
						and not self.m_oTimeboxSocket
						and self.m_strAddress
						and self.m_nPort != 0):

						self.m_oTimeboxSocket = BluetoothSocket(RFCOMM)
						self.m_oTimeboxSocket.connect((
							self.m_strAddress,
							self.m_nPort))

						continue
					# Verbindung abbrechen
					if (strArg == "disconnect"
						and self.m_oTimeboxSocket):

						self.m_oTimeboxSocket.close()
						self.m_oTimeboxSocket = None

						continue
		# Unbekanntes Kommando
		return bResult

