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
import zipfile
import uuid

from datetime import datetime
from zipfile import ZipFile
from io import BytesIO
from collections import OrderedDict

import globs

from sdk import ModuleBase
from sdk import WebClient
from sdk import TaskSpeak
from sdk import TaskModuleEvt

from worker import TaskExit

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
			"lnkManUpdate" : "/modules/Updater.html",
			"bAutoUpdate" : False,
			"bAutoReboot" : False,
			"nUpdateHour" : 0,
			"fChkVersion" : float(0.0)
		}
		
		self.m_strDownloadToken = uuid.uuid4().hex
		self.m_strUploadToken = uuid.uuid4().hex
		self.m_strUpdateToken = uuid.uuid4().hex
		self.m_strCheckToken = uuid.uuid4().hex
		
		self.m_oSystemUpdateIO = None
		self.m_bUpdateComplete = False
		self.m_bUpdateOffline = False
		self.m_fUpdVersion = float(0.0)
		self.m_fChkVersion = float(0.0)
		
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})
		
		dictCfgUsr.update({
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
				"default"		: 1,
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
				"description"	: ("Anzeigen"),
				"default"		: None,
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
		
		if (re.match("/modules/Updater\\.html", strPath)
			and not oHtmlPage == None):
			return self.serveHtmlPage(oHtmlPage, dictQuery, dictForm)
			
		self.updateContext()
			
		if not dictQuery:
			return False
			
		# Zyklische Prüfung
		bCheck = False
		bFetch = False
		bSetup = False
		for (strCmd, lstArg) in dictQuery.items():
			if (strCmd == "timer" and lstArg and lstArg[0] == "cron"):
				# Aktualisierungszeitpunkt erreicht?
				if (not self.m_nHour24h == self.m_nUpdateHour or not self.m_nMinutes == 0):
					return True
				bCheck = True
				break
			if (strCmd == "token" and self.m_strDownloadToken in lstArg):
				if (self.m_fChkVersion <= globs.getVersion()):
					# Jetzt auf Aktualisierung prüfen!
					globs.log("Jetzt auf Aktualisierung prüfen.")
					bCheck = True
					break
				if (self.m_fChkVersion > globs.getVersion()):
					# Jetzt Aktualisierung herunterladen!
					globs.log("Jetzt Aktualisierung herunterladen.")
					bFetch = True
					break
			if (strCmd == "token" and self.m_strUpdateToken in lstArg):
				# Jetzt ausstehende Installation ausführen!
				globs.log("Jetzt ausstehende Installation ausführen.")
				bSetup = True
				break
			globs.log("Keine Funktion mit Cmd=%s und Arg=%s" % (strCmd, lstArg))

		if bCheck or bFetch or bSetup:
			# Aktualisierung verfügbar?
			if (not self.doCheckUpdate()):
				return True
			# Automatische Aktualisierung aktiviert?
			if (not self.m_bAutoUpdate and not bFetch and not bSetup):
				TaskSpeak(self.getWorker(),
				"Eine neue Version steht zur Verfügung und kann heruntergeladen werden.").start()
				return True
			if (not self.doDownloadUpdate()):
				TaskSpeak(self.getWorker(),
				"Beim Herunterladen der neuen Version sind Probleme aufgetreten.").start()
				return False
			if (not self.m_bAutoReboot and not bSetup):
				TaskSpeak(self.getWorker(),
				"Eine neue Version steht zur Verfügung und kann installiert werden.").start()
				return True
			if (not self.doInstallUpdate()):
				TaskSpeak(self.getWorker(),
				"Beim Installieren der neuen Version sind Probleme aufgetreten.").start()
				return False
				
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
		
		if (dictQuery and "token" in dictQuery):
			if (self.m_strUploadToken in dictQuery["token"]):
				self.m_strUploadToken = uuid.uuid4().hex
				
				if (dictForm and "SystemFile" in dictForm):
					oSystemFile = dictForm["SystemFile"][0]
					if not oSystemFile.filename or not oSystemFile.file:
						oHtmlPage.createBox(
							"Systemaktualisierung",
							"Es konnte keine gültige Aktualisierungsdatei hochgeladen werden.",
							strType="warning")
						return True						
					self.m_oSystemUpdateIO = BytesIO(oSystemFile.file.read())
					self.m_strUpdateToken = uuid.uuid4().hex
					self.m_bUpdateOffline = True
					TaskModuleEvt(self.getWorker(),
						"/modules/Updater.cmd",
						dictQuery={"token" : self.m_strUpdateToken}).start()
					oHtmlPage.createBox(
						"Systemaktualisierung",
						"Die Aktualisierung wird jetzt durchgeführt. Danach wird das System neu "+
						"gestartet. Dieser Vorgang kann einige Zeit in Anspruch nehmen.",
						strType="info")
					return True
				
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
				
			if (self.m_strDownloadToken in dictQuery["token"]):
				self.m_strDownloadToken = uuid.uuid4().hex
				
				TaskModuleEvt(self.getWorker(),
					"/modules/Updater.cmd",
					dictQuery={"token" : self.m_strDownloadToken}).start()
				oHtmlPage.createBox(
					"Systemaktualisierung",
					"Es wird nach einer Aktualisierung gesucht. Dieser Vorgang kann einige Zeit "+
					"in Anspruch nehmen.",
					strType="info")
				return True
				
			if (self.m_strUpdateToken in dictQuery["token"]):
				self.m_strUpdateToken = uuid.uuid4().hex
				
				TaskModuleEvt(self.getWorker(),
					"/modules/Updater.cmd",
					dictQuery={"token" : self.m_strUpdateToken}).start()
				oHtmlPage.createBox(
					"Systemaktualisierung",
					"Die Installation der Aktualisierung wurde angefordert. Dieser Vorgang kann "+
					"einige Zeit in Anspruch nehmen.",
					strType="info")
				return True
			
		# Wenn die automatische Installation von Aktualisierungen deaktiviert wurde und eine neuere
		# Version bereitgestellt wurde, dann anbieten, die Installation anzufordern.
		if ((not self.m_bAutoReboot) and (self.m_fUpdVersion > globs.getVersion())):
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Die automatische Installation von Aktualisierungen ist ausgeschaltet aber es "+
				"steht eine neuere Version zur Installation bereit.",
				strType="warning", bClose=False)
			oHtmlPage.createText(
				"Derzeit ist die Version %s installiert und Version %s steht bereit" % (
					globs.getVersion(), self.m_fUpdVersion))
			oHtmlPage.createButton(
				"Jetzt installieren",
				strClass="ym-warning",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strUpdateToken))
			oHtmlPage.closeBox()
			return True
		
		# Wenn das automatische Herunterladen von Aktualisierungen deaktiviert wurde und online
		# eine neuere Version zur Verfügung steht, dann anbieten, das Herunterladen anzufordern. 
		if ((not self.m_bAutoUpdate) and (self.m_fChkVersion > globs.getVersion())):
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Das automatische Herunterladen von Aktualisierungen ist ausgeschaltet aber es "+
				"steht eine neuere Version zum Herunterladen bereit.",
				strType="warning", bClose=False)
			oHtmlPage.createText(
				"Derzeit ist die Version %s installiert und Version %s ist verfügbar." % (
					globs.getVersion(), self.m_fChkVersion))
			oHtmlPage.createButton(
				"Jetzt herunterladen",
				strClass="ym-warning",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strDownloadToken))
			oHtmlPage.closeBox()
			return True
			
		# Wenn eine neuere Version bereitsteht, die Versionsinformationen anzeigen
		if (self.m_fUpdVersion > globs.getVersion()):
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Es steht eine neuere Version zur Installation bereit, die zum nächsten "+
				"Aktualisierungszeitpunkt automatisch installiert wird.",
				strType="info", bClose=False)
			oHtmlPage.createText(
				"Derzeit ist die Version %s installiert und Version %s steht bereit" % (
					globs.getVersion(), self.m_fUpdVersion))
			oHtmlPage.createButton(
				"Aktualisierung hochladen",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strUploadToken))
			oHtmlPage.closeBox()
			return True
		
		# Wenn eine neuere Version gefunden wurde, die Versionsinformationen anzeigen
		if (self.m_fChkVersion > globs.getVersion()):
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Es steht eine neuere Version zum Herunterladen bereit, die zum nächsten "+
				"Aktualisierungszeitpunkt automatisch heruntergeladen wird.",
				strType="info", bClose=False)
			oHtmlPage.createText(
				"Derzeit ist die Version %s installiert und Version %s ist verfügbar." % (
					globs.getVersion(), self.m_fChkVersion))
			oHtmlPage.createButton(
				"Aktualisierung hochladen",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strUploadToken))
			oHtmlPage.closeBox()
			return True
		
		# Es ist keine Aktualisierung verfügbar
		if (self.m_fChkVersion == globs.getVersion()):
			oHtmlPage.createBox(
				"Systemaktualisierung",
				"Das System ist auf dem aktuellen Stand. Es sind keine Aktualisierungen verfügbar.",
				strType="success", bClose=False)
			oHtmlPage.createText(
				"Derzeit ist die Version %s installiert." % (globs.getVersion()))
			oHtmlPage.createButton(
				"Aktualisierung suchen",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strDownloadToken))
			oHtmlPage.createButton(
				"Aktualisierung hochladen",
				strHRef="/modules/Updater.html?token=%s" % (self.m_strUploadToken))
			oHtmlPage.closeBox()
			return True
		
		# Default, noch nicht nach Aktualisierungen gesucht oder keine Aktualisierungen verfügbar.
		oHtmlPage.createBox(
			"Systemaktualisierung",
			"Es wurde noch nicht nach Aktualisierungen gesucht.",
			strType="info", bClose=False)
		oHtmlPage.createText(
			"Derzeit ist die Version %s installiert." % (globs.getVersion()))
		oHtmlPage.createButton(
			"Aktualisierung suchen",
			strHRef="/modules/Updater.html?token=%s" % (self.m_strDownloadToken))
		oHtmlPage.createButton(
			"Aktualisierung hochladen",
			strHRef="/modules/Updater.html?token=%s" % (self.m_strUploadToken))
		oHtmlPage.closeBox()
		return True
		
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
		
	def doCheckUpdate(self):
		oClient = WebClient()
		
		if (not self.m_strChkUpdUrl):
			globs.err("Die URL für die Aktualisierungsinformation ('%s') ist ungültig" % (
				self.m_strChkUpdUrl))
			if (not self.m_oSystemUpdateIO):
				return False
			
		oResp = oClient.GET(self.m_strChkUpdUrl)
		if (not oResp or not oResp.m_bOK):
			globs.err("Fehler (%s) beim Herunterladen der Aktualisierungsinformation '%s'" % (
				oResp, self.m_strChkUpdUrl))
			if (not self.m_oSystemUpdateIO):
				return False
			
		strUpdInf = oResp.m_oData.decode()
		
		try:
			strUpdInf = strUpdInf[:10] + (strUpdInf[10:] and "..")
			self.m_fChkVersion = float(strUpdInf)
			globs.setSetting("Updater", "fChkVersion", self.m_fChkVersion)
		except:
			globs.exc("Fehler beim Auswerten der Aktualisierungsinformation '%s'" % (
				strUpdInf))
			globs.setSetting("Updater", "strChkUpdUrl", Updater.s_strChkUpdUrl)
			if (not self.m_oSystemUpdateIO):
				return False
			
		if (self.m_oSystemUpdateIO):
			if (self.m_fChkVersion > self.m_fUpdVersion):
				globs.log("Neuere Aktualisierung '%s' als bereitgestellte '%s' verfügbar" % (
					self.m_fChkVersion, self.m_fUpdVersion))
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
		oClient = WebClient()
		oRespSys = None
		
		if (not self.m_strSystemUrl):
			globs.err("Die URL für die Systemaktualisierung ist ungültig")
			globs.setSetting("Updater", "strSystemUrl", Updater.s_strSystemUrl)
			if (not self.m_oSystemUpdateIO):
				return False
		
		if (not self.m_oSystemUpdateIO
			or (self.m_fChkVersion > self.m_fUpdVersion and not self.m_bUpdateOffline)):
			oRespSys = oClient.GET(self.m_strSystemUrl)
			if (not oRespSys or not oRespSys.m_bOK):
				globs.err("Fehler (%s) beim Herunterladen der Systemaktualisierungsdatei '%s'" % (
					oRespSys, self.m_strSystemUrl))
				globs.setSetting("Updater", "strSystemUrl", Updater.s_strSystemUrl)
				return False
			
			self.m_oSystemUpdateIO = BytesIO(oRespSys.m_oData)
			self.m_fUpdVersion = self.m_fChkVersion
			return True
		
		if (self.m_oSystemUpdateIO):
			globs.log("Eine Aktualisierung wurde bereitgestellt.")
			return True
		
		return False
		
	def doInstallUpdate(self):
		
		if (not self.m_oSystemUpdateIO):
			self.m_fUpdVersion = float(0.0)
			self.m_bUpdateOffline = False
			return False
		
		if (not zipfile.is_zipfile(self.m_oSystemUpdateIO)):
			globs.err("Die Systemaktualisierungsdatei ist keine gültige Zip-Datei")
			del self.m_oSystemUpdateIO
			self.m_oSystemUpdateIO = None
			self.m_fUpdVersion = float(0.0)
			self.m_bUpdateOffline = False
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
						del self.m_oSystemUpdateIO
						self.m_oSystemUpdateIO = None
						self.m_fUpdVersion = float(0.0)
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
						del self.m_oSystemUpdateIO
						self.m_oSystemUpdateIO = None
						self.m_fUpdVersion = float(0.0)
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
				del self.m_oSystemUpdateIO
				self.m_oSystemUpdateIO = None
				self.m_fUpdVersion = float(0.0)
				self.m_bUpdateOffline = False
				TaskExit(self.getWorker(), "boot").start()
		except:
			globs.exc("Ausnahmefall während der Aktualisierung - Wiederherstellung ausführen")
			del self.m_oSystemUpdateIO
			self.m_oSystemUpdateIO = None
			self.m_fUpdVersion = float(0.0)
			self.m_bUpdateOffline = False
		
		try:
			if (not bUpdateComplete):
				for (strDstFile, strDstFileBak) in dictBackup.items():
					os.rename(strDstFileBak, strDstFile)
					globs.wrn("Das Element '%s' wurde wiederhergestellt" % (strDstFile))
				globs.err("Die Aktualisierung ist fehlgeschlagen - Wiederherstellung erfolgreich")
		except:
			globs.exc("Ausnahmefall während der Wiederherstellung nach Fehler bei Aktualisierung")
			del self.m_oSystemUpdateIO
			self.m_oSystemUpdateIO = None
			self.m_fUpdVersion = float(0.0)
			self.m_bUpdateOffline = False
		
		return True
		
	def installFile(self, foSource, strFilename):
		foFile = open(strFilename, "w+b")
		oData = foSource.read()
		foFile.write(oData)
		foFile.close()
		del oData
		return
