## 
#  Test Plug-In
#  
#  @file Test.py
#  @brief Plug-In für Testzwecke.
#  
import os
import re
import tempfile
import time
import uuid
import zipfile
from collections import OrderedDict
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from .. import globs
from ..sdk import ModuleBase, TaskDelegateFast, TaskDelegateLong, TaskModuleEvt, TaskSpeak, WebClient
from ..worker import TaskExit


def createModuleInstance(
	oWorker):
	return Updater(oWorker)

class Updater(ModuleBase):
	
	s_strSystemUrl = "https://github.com/FeydCron/RasPyWeb/archive/latest.zip"
	s_strChkUpdUrl = "https://github.com/FeydCron/RasPyWeb/releases/download/latest/version"
	s_strPrefix = "RasPyWeb-latest/berry/"
	
	## 
	#  @copydoc sdk::ModuleBase::moduleInit
	#  
	def moduleInit(self, dictModCfg={}, dictCfgUsr={}):
		dictSettings = {
			"strSystemUrl" : Updater.s_strSystemUrl,
			"strChkUpdUrl" : Updater.s_strChkUpdUrl,
			"lnkManUpdate" : "",
			"bAutoUpdate" : False,
			"bAutoReboot" : False,
			"nUpdateHour" : 0,
			"fChkVersion" : float(0.0)
		}
		
		self.m_strDownloadToken = uuid.uuid4().hex
		self.m_strUploadToken = uuid.uuid4().hex
		self.m_strUpdateToken = uuid.uuid4().hex
		self.m_strCheckToken = uuid.uuid4().hex
		
		self.m_oManualUpdateIO = None
		self.m_oOnlineUpdateIO = None
		self.m_oSystemUpdateIO = None

		self.m_bUpdateOffline = False
		self.m_bUpdInProgress = False
		
		self.m_fUpdVersion = float(0.0)
		self.m_fChkVersion = float(0.0)
		
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})
		
		dictCfgUsr.update({
			"properties" : [
				"bAutoUpdate",
				"bAutoReboot",
				"nUpdateHour",
				"lnkManUpdate",
				"fChkVersion",
				"strSystemUrl",
				"strChkUpdUrl",
			],
			"strSystemUrl" : {
				"title"			: "URL für Systemaktualisierung",
				"description"	: ("Die Einstellung legt die URL zur Quell-Datei für die "+
									"Systemaktualisierung fest."),
				"default"		: Updater.s_strSystemUrl
			},
			"strChkUpdUrl" : {
				"title"			: "URL für Aktualisierungsinformation",
				"description"	: ("Die Einstellung legt die URL zur Informationsdatei für die "+
									"Aktualisierung fest."),
				"default"		: Updater.s_strChkUpdUrl
			},
			"bAutoUpdate" : {
				"title"			: "Automatisch herunterladen",
				"description"	: ("Schaltet das automatische Herunterladen von Aktualisierungen "+
									"ein oder aus. Nur wenn die Einstellung eingeschaltet ist, "+
									"wird automatisch zum Aktualisierungszeitpunkt eine verfügbare "+
									"Aktualisierung gesucht und gegebenenfalls heruntergeladen."),
				"default"		: False
			},
			"bAutoReboot" : {
				"title"			: "Automatisch installieren",
				"description"	: ("Schaltet die automatische Installation und den Neustart nach "+
									"der Aktualisierung ein oder aus. Nur wenn automatische "+
									"Installation und Neustart eingeschaltet ist, wird eine "+
									"heruntergeladene Aktualisierung installiert und anschließend "+
									"das System automatisch neu gestartet, um die Aktualisierung "+
									"sofort wirksam werden zu lassen. Andernfalls muss die "+
									"Installation der Aktualisierung von Hand gestartet werden."),
				"default"		: False
			},
			"nUpdateHour" : {
				"title"			: "Aktualisierungszeitpunkt",
				"description"	: ("Der Aktualisierungszeitpunkt gibt an, zu welcher Zeit "+
									"täglich nach einer verfügbaren Aktualisierung gesucht "+
									"und diese gegebenenfalls installiert werden soll."),
				"default"		: 0,
				"choices"		: {
					"nachts"		: "0",
					"früh morgens"	: "3",
					"morgens" 		: "6",
					"vormittags"	: "9",
					"mittags"		: "12",
					"nachmittags"	: "15",
					"abends"		: "18",
					"spät abends"	: "21"
				}
			},
			"fChkVersion" : {
				"title"			: "Verfügbare Version",
				"description"	: ("Diese Anzeige stellt die verfügbare Version dar."),
				"default"		: float(0.0),
				"readonly"		: True
			},
			"lnkManUpdate" : {
				"title"			: "Manuelle Aktualisierung",
				"description"	: ("Anzeigen..."),
				"default"		: "/modules/Updater.html",
				"showlink"		: True
			},
		})
		self.updateContext()
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
		return True

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
		
		dictQueryKeys = None
		dictFormKeys = None
		
		if (dictQuery):
			dictQueryKeys = dictQuery.keys()
		if (dictForm):
			dictFormKeys = dictForm.keys()
		
		print("%r::moduleExec(strPath=%s, oHtmlPage=%s, dictQuery=%s, dictForm=%s) [%s]" % (
			self, strPath, oHtmlPage, dictQueryKeys, dictFormKeys, datetime.today().strftime("%X")))
		
		self.updateContext()
		
		if (re.match(r"/modules/Updater\.html", strPath)
			and not oHtmlPage == None):
			return self.serveHtmlPage(oHtmlPage, dictQuery, dictForm)
			
		if not dictQuery:
			return False
			
		# Zyklische Prüfung
		for (strCmd, lstArg) in dictQuery.items():
			if (strCmd == "timer" and "cron" in lstArg):
				# Aktualisierungszeitpunkt erreicht?
				if (not self.m_nHour24h == self.m_nUpdateHour
					or not self.m_nMinutes == 0
					or self.m_bUpdInProgress):
					return True

				if (TaskDelegateLong(self.getWorker(),
					self.doUpdateSequence, bFetch=False, bSetup=False).start()):
					return True

				TaskSpeak(self.getWorker(),
					"Die automatische Aktualisierung konnte nicht gestartet werden.").start()

				return False

		return True

	def doUpdateSequence(self,
		bFetch,
		bSetup):

		# Auf Aktualisierung prüfen
		if (not self.doCheckUpdate()):
			self.m_bUpdInProgress = False
			return
		
		# Schrittkette beenden?
		if (not self.m_bAutoUpdate and not bFetch and not bSetup):
			TaskSpeak(self.getWorker(),
				"Eine neue Version steht zur Verfügung und kann heruntergeladen werden.").start()
			self.m_bUpdInProgress = False
			return

		# Aktualisierung herunterladen
		if (not self.doDownloadUpdate()):
			TaskSpeak(self.getWorker(),
				"Beim Herunterladen der neuen Version sind Probleme aufgetreten.").start()
			self.m_bUpdInProgress = False
			return
		
		# Schrittkette beenden?
		if (not self.m_bAutoReboot and not bSetup):
			TaskSpeak(self.getWorker(),
				"Eine neue Version steht zur Verfügung und kann installiert werden.").start()
			self.m_bUpdInProgress = False
			return

		# Aktualisierung installieren
		if (not self.doInstallUpdate()):
			TaskSpeak(self.getWorker(),
				"Beim Installieren der neuen Version sind Probleme aufgetreten.").start()
			self.m_bUpdInProgress = False
			return

		self.m_bUpdInProgress = False
		return

	def serveUpdaterCommand(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		globs.log("Updater::serveUpdaterCommand()")

		if (self.m_bUpdInProgress):
			# Updater-Status aufbereiten lassen
			return False

		if (self.m_strUploadToken in dictQuery["token"]):
			return self.serveCommandUpload(oHtmlPage, dictQuery, dictForm)

		if (self.m_strDownloadToken in dictQuery["token"]):
			return self.serveCommandDownload(oHtmlPage, dictQuery, dictForm)
		
		if (self.m_strUpdateToken in dictQuery["token"]):
			return self.serveCommandUpdate(oHtmlPage, dictQuery, dictForm)

		# Updater-Status aufbereiten lassen
		return False
	
	def serveCommandUpload(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		self.m_strUploadToken = uuid.uuid4().hex

		# Hochgeladene manuelle Aktualisierungsdatei entgegen nehmen
		if (dictForm and "SystemFile" in dictForm):
			oSystemFile = dictForm["SystemFile"][0]
			if not oSystemFile.filename or not oSystemFile.file:
				
				oHtmlPage.createBox(
					"Systemaktualisierung",
					"Die Aktualisierungsdatei konnte nicht hochgeladen werden.",
					strType="warning")
				oHtmlPage.setAutoRefresh(
					nAutoRefresh=5,
					strUrl="/modules/Updater.html")
				
				return True

			self.m_oManualUpdateIO = BytesIO(oSystemFile.file.read())
			self.m_strUpdateToken = uuid.uuid4().hex
			self.m_bUpdateOffline = True
			self.m_bUpdInProgress = True

			if (TaskDelegateLong(self.getWorker(),
				self.doUpdateSequence, bFetch=False, bSetup=True).start()):
				
				# Updater-Status aufbereiten lassen
				return False
				
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Die manuelle Aktualisierung konnte nicht gestartet werden.",
				strType="error")
			oHtmlPage.setAutoRefresh(
				nAutoRefresh=5,
				strUrl="/modules/Updater.html")

			self.m_bUpdInProgress = False

			return True
		
		# Hochladen einer manuellen Aktualisierungsdatei anbieten
		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Über diese Funktion kann eine manuelle Aktualisierung durchgeführt werden.",
			bClose=False)
		oHtmlPage.openForm(
			dictQueries={"token" : self.m_strUploadToken})
		oHtmlPage.appendForm("SystemFile",
			strTitle="Datei für Systemaktualisierung",
			strTip="Zip-Datei für die Systemaktualisierung angeben",
			strTextType="file",
			strTypePattern="accept=\"application/zip\"")
		oHtmlPage.closeForm(strUrlCancel="/system/settings.html")
		oHtmlPage.closeBox()

		return True

	def serveCommandDownload(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		bFetch = self.m_fChkVersion > globs.getVersion()

		self.m_strDownloadToken = uuid.uuid4().hex
		self.m_fChkVersion = 0.0
		self.m_bUpdInProgress = True

		if (TaskDelegateLong(self.getWorker(),
			self.doUpdateSequence, bFetch=bFetch, bSetup=False).start()):
			# Updater-Status aufbereiten lassen
			return False
			
		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Das Herunterladen der Aktualisierung konnte nicht gestartet werden.",
			strType="error")
		oHtmlPage.setAutoRefresh(
			nAutoRefresh=5,
			strUrl="/modules/Updater.html")

		self.m_bUpdInProgress = False

		return True

	def serveCommandUpdate(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		self.m_strUpdateToken = uuid.uuid4().hex
		self.m_bUpdInProgress = True
		
		if (TaskDelegateLong(self.getWorker(),
			self.doUpdateSequence, bFetch=False, bSetup=True).start()):
			# Updater-Status aufbereiten lassen
			return False
			
		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Die Installation der Aktualisierung konnte nicht gestartet werden.",
			strType="error")
		oHtmlPage.setAutoRefresh(
			nAutoRefresh=5,
			strUrl="/modules/Updater.html")

		self.m_bUpdInProgress = False

		return True

	def serveUpdaterStatus(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		# Eine Systemaktualisierung ist aktiv
		if (self.m_bUpdInProgress
			or globs.s_strExitMode):
			return self.serveStatusBusy(oHtmlPage, dictQuery, dictForm)
		
		# Eine neuere Version ist zur Installation bereit
		if (self.m_fUpdVersion > globs.getVersion()):
			return self.serveStatusCanInstall(oHtmlPage, dictQuery, dictForm)
		
		# Eine neuere Version ist verfügbar
		if (self.m_fChkVersion > globs.getVersion()):
			return self.serveStatusCanDownload(oHtmlPage, dictQuery, dictForm)
		
		# Default
		return self.serveStatusCanCheck(oHtmlPage, dictQuery, dictForm)

	def serveStatusBusy(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		if (globs.s_strExitMode):

			if (globs.s_strExitMode == "boot"):

				oHtmlPage.createBox(
					"Systemaktualisierung",
					"Das System wird neu gestartet - Bitte warten Sie bis es wieder online ist.",
					strType="warning")
				oHtmlPage.setAutoRefresh(
					nAutoRefresh=60,
					strUrl="/modules/Updater.html")

			else:

				oHtmlPage.createBox(
					"Systemaktualisierung",
					"Das System wird beendet bzw. heruntergefahren - Bitte starten Sie es anschließend neu.",
					strType="warning")

			return True

		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Derzeit ist die Version %s installiert." % (
				globs.getVersion()),
			strType="warning", bClose=False)

		if (self.m_bUpdateOffline and self.m_oSystemUpdateIO):
			oHtmlPage.createText(
				"Die manuelle Installation läuft ...")
		elif (self.m_fUpdVersion != 0.0 and self.m_oSystemUpdateIO):
			oHtmlPage.createText(
				"Die Aktualisierung auf die Version %s läuft ..." % (
					self.m_fUpdVersion))
		elif (self.m_bUpdateOffline and self.m_oManualUpdateIO):
			oHtmlPage.createText(
				"Die manuelle Installation wird vorbereitet ...")
		elif (self.m_fUpdVersion != 0.0 and self.m_oOnlineUpdateIO):
			oHtmlPage.createText(
				"Die Aktualisierung auf die Version %s wird vorbereitet ..." % (
					self.m_fUpdVersion))
		elif (self.m_fChkVersion > self.m_fUpdVersion):
			oHtmlPage.createText(
				"Die Aktualisierung auf die Version %s wird heruntergeladen ..." % (
					self.m_fChkVersion))
		else:
			oHtmlPage.createText(
				"Es wird nach einer Aktualisierung gesucht ...")

		oHtmlPage.closeBox()
		oHtmlPage.setAutoRefresh(
			nAutoRefresh=1,
			strUrl="/modules/Updater.html")

		return True

	def serveStatusCanInstall(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Derzeit ist die Version %s installiert." % (
				globs.getVersion()),
			strType="warning", bClose=False)

		if (self.m_fUpdVersion != 0.0 and self.m_oOnlineUpdateIO):
			oHtmlPage.createText(
				"Eine Aktualisierung auf die Version %s wurde heruntergeladen und kann installiert werden." % (
					self.m_fUpdVersion))

		if (self.m_bAutoReboot):
			oHtmlPage.createText(
				"Die automatische Aktualisierung erfolgt um %s Uhr." % (
					self.m_nUpdateHour))
		else:
			oHtmlPage.createText(
				"Die automatische Aktualisierung ist ausgeschaltet.")
		
		oHtmlPage.createButton(
			"Jetzt aktualisieren",
			strClass="ym-warning",
			strHRef="/modules/Updater.html?token=%s" % (self.m_strUpdateToken))
		oHtmlPage.closeBox()

		return True

	def serveStatusCanDownload(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Derzeit ist die Version %s installiert." % (
				globs.getVersion()),
			strType="warning", bClose=False)

		if (self.m_fChkVersion > self.m_fUpdVersion):
			oHtmlPage.createText(
				"Eine Aktualisierung auf die Version %s ist verfügbar und kann heruntergeladen werden." % (
					self.m_fChkVersion))

		if (self.m_bAutoReboot):
			oHtmlPage.createText(
				"Die automatische Aktualisierung erfolgt um %s Uhr." % (
					self.m_nUpdateHour))
			oHtmlPage.createButton(
				"Jetzt aktualisieren",
				strClass="ym-warning",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strDownloadToken))
		else:
			if (self.m_bAutoUpdate):
				oHtmlPage.createText(
					"Die Aktualisierung wird um %s Uhr automatisch heruntergeladen und kann dann installiert werden." % (
						self.m_nUpdateHour))
			else:
				oHtmlPage.createText(
					"Die automatische Aktualisierung ist ausgeschaltet.")

			oHtmlPage.createButton(
				"Jetzt herunterladen",
				strClass="ym-warning",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strDownloadToken))
		
		oHtmlPage.closeBox()
		return True

	def serveStatusCanCheck(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		if (self.m_fChkVersion == globs.getVersion()):
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Derzeit ist die Version %s installiert." % (globs.getVersion()),
				strType="success", bClose=False)
			oHtmlPage.createText(
				"Das System ist auf dem aktuellen Stand. Es sind keine Aktualisierungen verfügbar.")
		else:
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Derzeit ist die Version %s installiert." % (globs.getVersion()),
				strType="info", bClose=False)
		
		oHtmlPage.createButton(
			"Aktualisierung suchen",
			strHRef="/modules/Updater.html?token=%s" % (self.m_strDownloadToken))
		oHtmlPage.createButton(
			"Aktualisierung hochladen",
			strHRef="/modules/Updater.html?token=%s" % (self.m_strUploadToken))

		oHtmlPage.closeBox()
		return True

	## 
	#  @brief Bereitstellung der HTML-Seite für eine manuelle Aktualisierung.
	#  
	#  @param [in] self Verweis auf die eigene Instanz
	#  @param [in] oHtmlPage Verweis auf die Instanz der HTML-Seite
	#  @param [in] dictQuery Query-Daten
	#  @param [in] dictForm Formulardaten
	#  @return Liefert @c True wenn die HTML-Seite bereitgestellt werden konnte oder @c False
	#  im Fehlerfall.
	#  
	#  @details Details
	#  
	def serveHtmlPage(self,
		oHtmlPage,
		dictQuery,
		dictForm):

		globs.log("Updater::serveHtmlPage()")

		# Anforderung einer Seite mit Kommando-Token
		if (dictQuery and "token" in dictQuery):
			if (self.serveUpdaterCommand(oHtmlPage, dictQuery, dictForm)):
				return True
		
		# Updater-Status aufbereiten
		return self.serveUpdaterStatus(oHtmlPage, dictQuery, dictForm)
		
	# Aktuelle Zeit holen und in globalen Variablen speichern
	def updateContext(self):
		self.m_nHour24h = int(time.strftime("%H"))
		self.m_nMinutes = int(time.strftime("%M"))
		
		self.m_nUpdateHour = globs.getSetting("Updater", "nUpdateHour", "\\d{1,2}", 1)
		self.m_bAutoUpdate = globs.getSetting("Updater", "bAutoUpdate", "True|False", False)
		self.m_bAutoReboot = globs.getSetting("Updater", "bAutoReboot", "True|False", False)
		self.m_strSystemUrl = globs.getSetting("Updater", "strSystemUrl",
			"[Hh][Tt][Tt][Pp][Ss]+\\://.+/.+", "")
		self.m_strChkUpdUrl = globs.getSetting("Updater", "strChkUpdUrl",
			"[Hh][Tt][Tt][Pp][Ss]+\\://.+/.+", "")
			
		globs.setSetting("Updater", "fChkVersion", self.m_fChkVersion)
		return

	def resetPendingUpdate(self):

		self.m_bUpdInProgress = False
		if (self.m_bUpdateOffline):
			# Manuelle Aktualisierung zurücksetzen
			self.m_bUpdateOffline = False
			if (self.m_oManualUpdateIO):
				del self.m_oManualUpdateIO
			self.m_oManualUpdateIO = None
		else:
			# Online Aktualisierung zurücksetzen
			self.m_fChkVersion = float(0.0)
			self.m_fUpdVersion = float(0.0)
			if (self.m_oOnlineUpdateIO):
				del self.m_oOnlineUpdateIO
			self.m_oOnlineUpdateIO = None
		
			globs.wrn("Wiederherstellung der Standardeinstellungen für die Aktualisierung")
			globs.setSetting("Updater", "strChkUpdUrl", Updater.s_strChkUpdUrl)
			globs.setSetting("Updater", "strSystemUrl", Updater.s_strSystemUrl)

		if (self.m_oSystemUpdateIO):
			del self.m_oSystemUpdateIO
		self.m_oSystemUpdateIO = None

		return
		
	def doCheckUpdate(self):

		# Offline oder manuelle Aktualisierung
		if (self.m_bUpdateOffline):
			if (not self.m_oManualUpdateIO):
				globs.err("Fehler bei der Bereitstellung der manuellen Aktualisierungsdatei")
				self.resetPendingUpdate()
				return False
			return True

		# Online Aktualisierung
		oClient = WebClient()

		# Aktualisierungs-URL prüfen		
		if (not self.m_strChkUpdUrl):
			globs.err("Die URL für die Aktualisierungsinformation ('%s') ist ungültig - Wiederherstellung der Standardeinstellung" % (
				self.m_strChkUpdUrl))
			self.resetPendingUpdate()
			return False

		# Aktualisierungsinformation herunterladen	
		oResp = oClient.GET(self.m_strChkUpdUrl)
		if (not oResp or not oResp.m_bOK):
			globs.err("Fehler (%s) beim Herunterladen der Aktualisierungsinformation '%s'" % (
				oResp, self.m_strChkUpdUrl))
			self.resetPendingUpdate()
			return False
		
		# Aktualisierungsinformation auswerten
		strUpdInf = oResp.m_oData.decode()		
		try:
			strUpdInf = strUpdInf[:10] + (strUpdInf[10:] and "..")
			self.m_fChkVersion = float(strUpdInf)
			globs.setSetting("Updater", "fChkVersion", self.m_fChkVersion)
		except:
			globs.exc("Fehler beim Auswerten der Aktualisierungsinformation '%s'" % (
				strUpdInf))
			self.resetPendingUpdate()
			return False

		# Gültigkeit einer bereits heruntergeladenen Aktualisierung überprüfen
		if (self.m_oOnlineUpdateIO):
			if (self.m_fChkVersion > self.m_fUpdVersion):
				globs.log("Neuere Aktualisierung '%s' als bereitgestellte '%s' verfügbar" % (
					self.m_fChkVersion, self.m_fUpdVersion))
				self.m_fUpdVersion = float(0.0)
				del self.m_oOnlineUpdateIO
				self.m_oOnlineUpdateIO = None
			else:
				globs.log("Eine Aktualisierung '%s' wurde bereitgestellt." % (
					self.m_fUpdVersion))
				return True
		
		if (self.m_fChkVersion <= globs.getVersion()):
			globs.log("Keine Aktualisierung für Version '%s' verfügbar" % (
				globs.getVersion()))
			return False
			
		globs.log("Neuere Aktualisierung von Version '%s' auf '%s' verfügbar" % (
			globs.getVersion(), self.m_fChkVersion))
		
		return True
		
	def doDownloadUpdate(self):

		if (self.m_bUpdateOffline):
			if (not self.m_oManualUpdateIO):
				self.resetPendingUpdate()
				return False
			return True

		oClient = WebClient()
		oResp = None
		
		if (not self.m_strSystemUrl):
			globs.err("Die URL für die Systemaktualisierung ist ungültig")
			self.resetPendingUpdate()
			return False
		
		if (not self.m_oOnlineUpdateIO):

			oResp = oClient.GET(self.m_strSystemUrl)
			if (not oResp or not oResp.m_bOK):
				globs.err("Fehler (%s) beim Herunterladen der Systemaktualisierungsdatei '%s'" % (
					oResp, self.m_strSystemUrl))
				globs.setSetting("Updater", "strSystemUrl", Updater.s_strSystemUrl)
				return False
			
			self.m_oOnlineUpdateIO = BytesIO(oResp.m_oData)
			self.m_fUpdVersion = self.m_fChkVersion
			return True
		
		if (self.m_oOnlineUpdateIO):
			globs.log("Eine Aktualisierung wurde bereitgestellt.")
			return True
		
		return False
		
	def doInstallUpdate(self):
		
		if (self.m_bUpdateOffline):
			if (self.m_oManualUpdateIO):
				self.m_oSystemUpdateIO = self.m_oManualUpdateIO
				self.m_oManualUpdateIO = None
		elif (self.m_oOnlineUpdateIO):
			self.m_oSystemUpdateIO = self.m_oOnlineUpdateIO
			self.m_oOnlineUpdateIO = None
		
		if (not self.m_oSystemUpdateIO):
			self.resetPendingUpdate()
			return False
		
		if (not zipfile.is_zipfile(self.m_oSystemUpdateIO)):
			globs.err("Die Systemaktualisierungsdatei ist keine gültige Zip-Datei")
			self.resetPendingUpdate()
			return False
		
		dictSysUpdate = OrderedDict()
		dictModUpdate = OrderedDict()
		dictBackup = OrderedDict()
		bUpdateComplete = False
		
		try:
			with \
				tempfile.TemporaryDirectory() as oTmpDir,\
				ZipFile(self.m_oSystemUpdateIO, "r") as oSysZipFile:
				# Aktualisierung vorbereiten
				for oZipInfo in (oSysZipFile.infolist()):
					if (os.path.isabs(oZipInfo.filename)):
						globs.err("Absolute Pfadangabe in Zip-Datei: '%s'" % (
							oZipInfo.filename))
						self.resetPendingUpdate()
						return False
					if (not re.match("\\A" + re.escape(Updater.s_strPrefix) + "\\w+.+", oZipInfo.filename)):
						continue
					strEntryName = oZipInfo.filename.replace(Updater.s_strPrefix, "")
					oSysZipFile.extract(oZipInfo, oTmpDir)
					globs.dbg("Extrahieren von '%s' nach '%s'" % (oZipInfo.filename, oTmpDir))
					strFilename = os.path.join(oTmpDir, oZipInfo.filename)
					if (os.path.isdir(strFilename)):
						continue
					if (not os.path.isfile(strFilename)):
						globs.err("Die extrahierte Systemdatei '%s' wurde nicht gefunden" % (
							strFilename))
						self.resetPendingUpdate()
						return False
					globs.dbg("Das extrahierte Element '%s' liegt unter '%s'" % (
						strEntryName, strFilename))
					if (re.match("\\Amodules/\\w+\\.[Pp][Yy]\\Z", strEntryName)):
						dictModUpdate.update({strEntryName : strFilename})
					elif (re.match(".+\\.([Pp][Yy]|[Pp][Nn][Gg]|[Hh][Tt][Mm][Ll]?|[Cc][Ss][Ss])\\Z", strEntryName)):
						dictSysUpdate.update({strEntryName : strFilename})
					else:
						globs.dbg("Das element '%s' wird nicht installiert" % (strEntryName))
				# Systemaktualisierung durchführen
				for (strRelDst, strSrcFile) in dictSysUpdate.items():
					strDstFile = os.path.join(globs.s_strBasePath, strRelDst)
					strDstPath, _ = os.path.split(strDstFile)
					if (os.path.isfile(strDstFile)):
						strDstFileBak = "%s.bak" % strDstFile
						os.rename(strDstFile, strDstFileBak)
						dictBackup.update({strDstFile : strDstFileBak})
						globs.dbg("Backup von Datei '%s' ('%s') erstellt." % (strDstFile, strDstFileBak))
					elif (not os.path.isdir(strDstPath)):
						os.makedirs(strDstPath)
					foSource = open(strSrcFile, "r+b")
					self.installFile(foSource, strDstFile)
					foSource.close()
					globs.dbg("Update von Datei '%s' installiert." % (strDstFile))
				# Modulaktualisierung durchführen
				for (strRelDst, strSrcFile) in dictModUpdate.items():
					strDstFile = os.path.join(globs.s_strBasePath, strRelDst)
					if (os.path.isfile(strDstFile)):
						strDstFileBak = "%s.bak" % strDstFile
						os.rename(strDstFile, strDstFileBak)
						dictBackup.update({strDstFile : strDstFileBak})
						globs.dbg("Backup von Modul '%s' ('%s') erstellt." % (strDstFile, strDstFileBak))
						foSource = open(strSrcFile, "r+b")
						self.installFile(foSource, strDstFile)
						foSource.close()
						globs.dbg("Update von Modul '%s' installiert." % (strDstFile))
				bUpdateComplete = True
				self.resetPendingUpdate()
				TaskExit(self.getWorker(), "boot").start()
		except:
			globs.exc("Ausnahmefall während der Aktualisierung - Wiederherstellung ausführen")
			self.resetPendingUpdate()
		
		try:
			if (not bUpdateComplete):
				for (strDstFile, strDstFileBak) in dictBackup.items():
					os.rename(strDstFileBak, strDstFile)
					globs.wrn("Das Element '%s' wurde wiederhergestellt" % (strDstFile))
				globs.err("Die Aktualisierung ist fehlgeschlagen - Wiederherstellung erfolgreich")
		except:
			globs.exc("Ausnahmefall während der Wiederherstellung nach Fehler bei Aktualisierung")
			self.resetPendingUpdate()
		
		return True
		
	def installFile(self, foSource, strFilename):
		foFile = open(strFilename, "w+b")
		oData = foSource.read()
		foFile.write(oData)
		foFile.close()
		del oData
		return
