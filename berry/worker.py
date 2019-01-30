import threading
import queue

from . import globs
from . import sdk
from .sdk import LongTask, FastTask, TaskSpeak

class TaskInit(LongTask):
	
	def __str__(self):
		strDesc = "Initialisieren des Systems"
		return  strDesc
		
	def do(self):
		TaskLoadSettings(self.m_oWorker).start()
		return

class TaskExit(FastTask):
	
	def __init__(self, oWorker, strMode):
		super(TaskExit, self).__init__(oWorker)
		self.m_strMode = strMode
		return
		
	def __str__(self):
		strDesc = "Beenden des Programms"
		if self.m_strMode == "halt":
			strDesc += " mit anschließendem Herunterfahren des Systems"
		if self.m_strMode == "boot":
			strDesc += " mit anschließendem Neustart des Systems"
		return  strDesc
	
	def do(self):
		globs.s_strExitMode = self.m_strMode
		for (oInstance, _) in self.m_oWorker.m_dictModules.values():
			if (oInstance):
				oInstance.moduleExit()
		self.m_oWorker.m_dictModules.clear()
		globs.saveSettings()
		globs.shutdown()
		return
		
class TaskSystemWatchDog(FastTask):

	s_fCpuTempMax = 0.0
	s_fCpuTempMin = 0.0
	s_fCpuTempAvg = 0.0
	s_fCpuUseMax = 0.0
	s_fCpuUseMin = 0.0
	s_fCpuUseAvg = 0.0
	s_strIpAddr = ""
	s_nCpuTooHot = 0
	s_nIpFailCnt = 0
	s_nCpuTempLvl = 0
	s_bHistory = False
	
	def __str__(self):
		strDesc = "Überwachen des Systems"
		return  strDesc

	def do(self):
		fCpuTemp = sdk.getCpuTemp()
		strCpuUse = sdk.getCpuUse().strip()
		lstRamInfo = sdk.getRamInfo()
		lstDiskSpace = sdk.getDiskSpace()

		fCpuTempA = globs.getSetting("System", "fCpuTempA", "\\d{2,}\\.\\d+", 60.0)
		fCpuTempB = globs.getSetting("System", "fCpuTempB", "\\d{2,}\\.\\d+", 56.0)
		fCpuTempC = globs.getSetting("System", "fCpuTempC", "\\d{2,}\\.\\d+", 53.0)
		fCpuTempH = globs.getSetting("System", "fCpuTempH", "\\d{2,}\\.\\d+", 1.0)

		try:
			fCpuUse = float(strCpuUse.replace(",", ".", 1))
		except:
			fCpuUse = 0.0
		# IP-Adresse ermitteln
		if not TaskSystemWatchDog.s_strIpAddr:
			TaskSystemWatchDog.s_strIpAddr = sdk.getNetworkInfo(
				globs.getSetting("System", "strNetInfoName"))
			if TaskSystemWatchDog.s_strIpAddr:
				TaskSpeak(self.m_oWorker,
				"Die aktuelle Netzwerkadresse ist: %s" % (
				TaskSystemWatchDog.s_strIpAddr.replace(".", " Punkt "))).start()
			elif TaskSystemWatchDog.s_nIpFailCnt < 4:
				TaskSystemWatchDog.s_nIpFailCnt += 1
				TaskSpeak(self.m_oWorker,
				"Die aktuelle Netzwerkadresse konnte nicht ermittelt werden.").start()
			else:
				TaskSystemWatchDog.s_strIpAddr = "127.0.0.1"
				TaskSpeak(self.m_oWorker,
				"Die Netzwerkadresse kann nicht ermittelt werden, daher wird %s angenommen." % (
				TaskSystemWatchDog.s_strIpAddr.replace(".", " Punkt "))).start()
		# CPU-Statistik erstellen
		if not TaskSystemWatchDog.s_bHistory:
			# Statistik initialisieren
			TaskSystemWatchDog.s_fCpuTempMin = fCpuTemp
			TaskSystemWatchDog.s_fCpuTempMax = fCpuTemp
			TaskSystemWatchDog.s_fCpuTempAvg = fCpuTemp
			TaskSystemWatchDog.s_fCpuUseMin = fCpuUse
			TaskSystemWatchDog.s_fCpuUseMax = fCpuUse
			TaskSystemWatchDog.s_fCpuUseAvg = fCpuUse
		else:
			# CPU-Temperaturen
			TaskSystemWatchDog.s_fCpuTempMin = min(
				TaskSystemWatchDog.s_fCpuTempMin,
				fCpuTemp)
			TaskSystemWatchDog.s_fCpuTempMax = max(
				TaskSystemWatchDog.s_fCpuTempMax,
				fCpuTemp)
			TaskSystemWatchDog.s_fCpuTempAvg += fCpuTemp
			TaskSystemWatchDog.s_fCpuTempAvg /= 2.0
			# CPU-Auslastungen
			TaskSystemWatchDog.s_fCpuUseMin = min(
				TaskSystemWatchDog.s_fCpuUseMin,
				fCpuUse)
			TaskSystemWatchDog.s_fCpuUseMax = max(
				TaskSystemWatchDog.s_fCpuUseMax,
				fCpuUse)
			TaskSystemWatchDog.s_fCpuUseAvg += fCpuUse
			TaskSystemWatchDog.s_fCpuUseAvg /= 2.0
		# Systemwerte vorbereiten
		if "CPU" not in globs.s_dictSystemValues:
			globs.s_dictSystemValues.update({"CPU" : {}})
		if "RAM" not in globs.s_dictSystemValues:
			globs.s_dictSystemValues.update({"RAM" : {}})
		if "MEM" not in globs.s_dictSystemValues:
			globs.s_dictSystemValues.update({"MEM" : {}})
		if "Netzwerk" not in globs.s_dictSystemValues:
			globs.s_dictSystemValues.update({"Netzwerk" : {}})
		# Systemwerte eintragen
		globs.s_dictSystemValues["CPU"].update({
			"Auslastung"		: "%s%%" % (strCpuUse),
			"Auslastung Min"	: "%0.2f%%" % (TaskSystemWatchDog.s_fCpuUseMin),
			"Auslastung Max"	: "%0.2f%%" % (TaskSystemWatchDog.s_fCpuUseMax),
			"Auslastung Avg"	: "%0.2f%%" % (TaskSystemWatchDog.s_fCpuUseAvg),
			"Temperatur"		: "%0.1f°C" % (fCpuTemp),
			"Temperatur Min"	: "%0.2f°C" % (TaskSystemWatchDog.s_fCpuTempMin),
			"Temperatur Max"	: "%0.2f°C" % (TaskSystemWatchDog.s_fCpuTempMax),
			"Temperatur Avg"	: "%0.2f°C" % (TaskSystemWatchDog.s_fCpuTempAvg),})
		globs.s_dictSystemValues["Netzwerk"].update({
			"IP-Adresse"		: "%s" % (TaskSystemWatchDog.s_strIpAddr),})
		lstLabels = ["Gesamt", "Belegt", "Frei", "Geteilt", "Gepuffert", "Im Cache"]
		nIndex = 0
		for strData in lstRamInfo:
			globs.s_dictSystemValues["RAM"].update({
			lstLabels[nIndex]	: strData + "K"})
			nIndex += 1
		lstLabels = ["Gesamt", "Belegt", "Verfügbar", "Belegung"]
		nIndex = 0
		for strData in lstDiskSpace:
			globs.s_dictSystemValues["MEM"].update({
			lstLabels[nIndex]	: strData})
			nIndex += 1
		# Nächsten Durchlauf einplanen
		self.m_oWorker.runSystemWatchDog()
		# CPU-Temperatur auswerten
		strCpuTemp = ("%0.1f Grad" % (TaskSystemWatchDog.s_fCpuTempAvg)
			).replace(".", " Komma ")
		if TaskSystemWatchDog.s_fCpuTempAvg > fCpuTempA:
			#
			# Warn-Level 3 - Notabschaltung
			#
			TaskSystemWatchDog.s_nCpuTooHot += 1
			if TaskSystemWatchDog.s_nCpuTempLvl != 3: 
				TaskSpeak(self.m_oWorker, "Achtung!").start()
				TaskSpeak(self.m_oWorker, "Temperaturüberschreitung mit %s!" % (
					strCpuTemp)).start()
			TaskSystemWatchDog.s_nCpuTempLvl = 3
			if (TaskSystemWatchDog.s_nCpuTooHot >= 10):
				TaskSpeak(self.m_oWorker, "Notabschaltung eingeleitet!").start()
				TaskExit(self.m_oWorker, "term").start()
				globs.stop()
			else:
				TaskSpeak(self.m_oWorker,
					"Für Abkühlung sorgen! Notabschaltung %s Prozent!" % (
					TaskSystemWatchDog.s_nCpuTooHot * 10)).start()
		elif (TaskSystemWatchDog.s_fCpuTempAvg > fCpuTempB
			and TaskSystemWatchDog.s_fCpuTempAvg < (fCpuTempA - fCpuTempH)):
			#
			# Warn-Level 2
			#
			TaskSystemWatchDog.s_nCpuTooHot = 0
#			if TaskSystemWatchDog.s_nCpuTooHot > 0:
#				TaskSystemWatchDog.s_nCpuTooHot -= 1
			if TaskSystemWatchDog.s_nCpuTempLvl != 2:
				TaskSpeak(self.m_oWorker,
					"Die Temperatur ist mit %s zu hoch!" % (
					strCpuTemp)).start()
			TaskSystemWatchDog.s_nCpuTempLvl = 2
		elif (TaskSystemWatchDog.s_fCpuTempAvg > fCpuTempC
			and TaskSystemWatchDog.s_fCpuTempAvg < (fCpuTempB - fCpuTempH)):
			#
			# Warn-Level 1
			#
			TaskSystemWatchDog.s_nCpuTooHot = 0
			if TaskSystemWatchDog.s_nCpuTempLvl != 1:
				TaskSpeak(self.m_oWorker,
					"Die Temperatur ist mit %s erhöht!" % (
					strCpuTemp)).start()
			TaskSystemWatchDog.s_nCpuTempLvl = 1
		elif (TaskSystemWatchDog.s_nCpuTempLvl != 0
			and TaskSystemWatchDog.s_fCpuTempAvg < (fCpuTempC - fCpuTempH)):
			#
			# Warn-Level 0 - Normalbereich
			#
			TaskSystemWatchDog.s_nCpuTooHot = 0
			TaskSpeak(self.m_oWorker,
				"Die Temperatur ist mit %s wieder im normalen Bereich" % (
				strCpuTemp)).start()
			TaskSystemWatchDog.s_nCpuTempLvl = 0
		elif not TaskSystemWatchDog.s_bHistory:
			TaskSpeak(self.m_oWorker, 
				"Die Temperatur liegt mit %s im normalen Bereich" % (
				strCpuTemp)).start()
		# Es liegen jetzt Statistikwerte aus der Vergangenheit vor
		if not TaskSystemWatchDog.s_bHistory:
			TaskSystemWatchDog.s_bHistory = True
		return
		
class TaskLoadSettings(FastTask):
	
	def __str__(self):
		strDesc = "Laden der Systemkonfiguration"
		return  strDesc

	def do(self):
		globs.loadSettings()
		self.m_oWorker.m_evtInit.set()
		for strComponent in globs.s_dictSettings["listModules"]:
			TaskModuleInit(self.m_oWorker, strComponent).start()
		return
		
class TaskModuleInit(FastTask):
	
	def __init__(self, oWorker, strModule):
		super(TaskModuleInit, self).__init__(oWorker)
		self.m_strModule = strModule
		return
		
	def __str__(self):
		strDesc = "Verwalten des Moduls %s" % (self.m_strModule)
		return  strDesc
	
	def do(self):
		# Gegebenenfalls die alte Instanz des Moduls entladen
		bUnloaded = False

		# Solange das Modul noch nicht geladen worden ist, ist es u.U. nur
		# unter einem relativen Namen bekannt. Erst nach dem Laden des Moduls
		# ist sein absoluter Name bekannt, sodass über diesen Namen ein
		# Reload des Moduls initiiert werden kann.
		strKnownModuleName = ".modules." + self.m_strModule

		globs.log("m_dictModules: %r" % (self.m_oWorker.m_dictModules))
		
		if (self.m_strModule in self.m_oWorker.m_dictModules.keys()):
			(oInstance, strKnownModuleName) = self.m_oWorker.m_dictModules[self.m_strModule]
			globs.log("KnownModuleName: '%s'" % (strKnownModuleName))
			if (oInstance):
				self.m_oWorker.m_dictModules.update({self.m_strModule : (None, strKnownModuleName)})
				oInstance.moduleExit()
				del oInstance
				bUnloaded = True
		
		if (self.m_strModule in globs.s_dictSettings["listModules"] and
			self.m_strModule not in globs.s_dictSettings["listInactiveModules"]):
			# Modul importieren bzw. neu laden (via Reload)
			oModule = globs.importComponent(strKnownModuleName)
			if not oModule:
				strMsg = "Das Modul %s kann nicht geladen werden. Wahrscheinlich sind die Einstellungen falsch." % (
					strKnownModuleName)
				globs.wrn(strMsg)
				TaskSpeak(self.m_oWorker, strMsg).start()
				return
			
			# >>> Critical Section
			globs.s_oSettingsLock.acquire()

			if self.m_strModule not in globs.s_dictSettings:
				globs.s_dictSettings.update({self.m_strModule : {}})
			dictModCfg = globs.s_dictSettings[self.m_strModule]
			dictCfgUsr = {}
			try:
				oInstance = oModule.createModuleInstance(self.m_oWorker)
				if (not oInstance
					or not oInstance.moduleInit(dictModCfg=dictModCfg, dictCfgUsr=dictCfgUsr)):
					strMsg = "Das Modul %s konnte nicht initialisiert werden. Möglicherweise müssen zusätzliche Pakete installiert werden." % (self.m_strModule)
					globs.wrn(strMsg)
					TaskSpeak(self.m_oWorker, strMsg).start()
					oInstance = None
			except:
				globs.exc("Verwalten des Moduls %s" % (self.m_strModule))
				strMsg = "Das Modul %s konnte nicht initialisiert werden. Möglicherweise ist es veraltet und muss aktualisiert werden." % (
					self.m_strModule)
				globs.wrn(strMsg)
				TaskSpeak(self.m_oWorker, strMsg).start()
				oInstance = None

			if oInstance:
				self.m_oWorker.m_dictModules.update({self.m_strModule : (oInstance, oModule.__name__)})
				globs.s_dictUserSettings.update({self.m_strModule : dictCfgUsr})

			globs.s_oSettingsLock.release()
			# <<< Critical Section

			return
		
		if (self.m_strModule not in globs.s_dictSettings["listModules"]):
			# >>> Critical Section
			globs.s_oSettingsLock.acquire()
			if self.m_strModule in globs.s_dictSettings:
				globs.s_dictSettings.pop(self.m_strModule)
			if self.m_strModule in globs.s_dictUserSettings:
				globs.s_dictUserSettings.pop(self.m_strModule)
			globs.s_oSettingsLock.release()
			# <<< Critical Section
			strMsg = "Das Modul %s wurde dauerhaft entfernt." % (self.m_strModule)
			globs.log(strMsg)
			TaskSpeak(self.m_oWorker, strMsg).start()
			return
		strMsg = "Das Modul %s wurde ausgeschaltet" % (self.m_strModule)
		if (bUnloaded):
			strMsg += " und entladen"
		strMsg += "."
		globs.log(strMsg)
		TaskSpeak(self.m_oWorker, strMsg).start()
		globs.log(strMsg)
		return
		
class TaskQueueFastStop(FastTask):
	
	def __str__(self):
		strDesc = "Beenden der Ausführung von schnellen Aufgaben"
		return  strDesc
	
	def do(self):
		self.m_oWorker.m_bIsQueueFastShutdown = True
		return
		
class TaskQueueLongStop(LongTask):
	
	def __str__(self):
		strDesc = "Beenden der Ausführung von umfangreichen Aufgaben"
		return  strDesc
		
	def do(self):
		self.m_oWorker.m_bIsQueueLongShutdown = True
		return

class Worker:
	
	def __init__(self):
		self.m_oLock = threading.RLock()
		self.m_oLock.acquire()
		self.m_evtRunning = threading.Event()
		self.m_evtInit = threading.Event()
		self.m_evtRunning.clear()
		self.m_evtInit.clear()
		self.m_oWatchDogTimer = None
		self.m_oThreadFast = None
		self.m_oThreadLong = None
		self.m_oQueueFast = None
		self.m_oQueueLong = None
		self.m_bIsQueueFastShutdown = True
		self.m_bIsQueueLongShutdown = True
		self.m_dictModules = {}
		self.m_oLock.release()
		return
		
	def onRunSystemWatchDog(self):
		TaskSystemWatchDog(self).start()
		return

	def runSystemWatchDog(self):
		self.m_oWatchDogTimer = threading.Timer(
			globs.getWatchDogInterval(),
			self.onRunSystemWatchDog)
		self.m_oWatchDogTimer.start()
		globs.dbg("Systemüberwachung: Nächste Prüfung eingeplant (%s)" % (
			self.m_oWatchDogTimer))
		return
	
	def fastThreadProc(self):
		self.m_bIsQueueFastShutdown = False
		globs.log("Leichte Aufgabenbearbeitung: Gestartet")
		while True:
			bDone = False
			try:
				oTask = self.m_oQueueFast.get(
					block = not self.m_bIsQueueFastShutdown)
			except:
				# Abbruchbedingung für "do-while"
				globs.log("Leichte Aufgabenbearbeitung: Abbruchbedingung")
				break
			globs.dbg("Leichte Aufgabenbearbeitung: %s" % (oTask))
			try:
				oTask.do()
				bDone = True
			except:
				globs.exc("Leichte Aufgabenbearbeitung: %s" % (oTask))
			oTask.done(bResult = bDone)
		globs.log("Leichte Aufgabenbearbeitung: Beendet")
		return
		
	def longThreadProc(self):
		self.m_bIsQueueLongShutdown = False
		globs.log("Schwere Aufgabenbearbeitung: Gestartet")
		while True:
			bDone = False
			try:
				oTask = self.m_oQueueLong.get(
					block = not self.m_bIsQueueLongShutdown)
			except:
				# Abbruchbedingung für "do-while"
				globs.log("Schwere Aufgabenbearbeitung: Abbruchbedingung")
				break
			globs.dbg("Schwere Aufgabenbearbeitung: %s" % (oTask))
			try:
				oTask.do()
				bDone = True
			except:
				globs.exc("Schwere Aufgabenbearbeitung: %s" % (oTask))
			oTask.done(bResult = bDone)
		globs.log("Schwere Aufgabenbearbeitung: Beendet")
		return
	
	def startQueue(self):
		globs.dbg("Start Aufgabenbearbeitung: Warten auf Freigabe")
		# >>> Critical Section
		self.m_oLock.acquire()
		globs.dbg("Start Aufgabenbearbeitung: Freigabe erhalten")
		self.m_oThreadFast = threading.Thread(target=self.fastThreadProc)
		self.m_oThreadFast.daemon = True
		self.m_oThreadLong = threading.Thread(target=self.longThreadProc)
		self.m_oThreadLong.daemon = True
		self.m_oQueueFast = queue.Queue()
		self.m_oQueueLong = queue.Queue()
		self.m_oThreadFast.start()
		self.m_oThreadLong.start()
		self.m_evtRunning.set()
		globs.dbg("Start Aufgabenbearbeitung: Freigabe abgeben")
		self.m_oLock.release()
		# <<< Critical Section
		TaskInit(self).start()
		# Synchronization Point (Initialisation)
		globs.dbg("Start Aufgabenbearbeitung: Warten auf Initialisierung")
		self.m_evtInit.wait()
		globs.dbg("Start Aufgabenbearbeitung: Initialisierung abgeschlossen")
		# Set up cyclic monitoring of system values
		globs.dbg("Start Aufgabenbearbeitung: Systemüberwachung starten")
		TaskSystemWatchDog(self).start()
		return
	
	def stopQueue(self):
		bResult = True
		if not self.m_evtRunning.isSet:
			globs.log("Stop Aufgabenbearbeitung: Wurde bereits angefordert")
			return bResult
		globs.dbg("Stop Aufgabenbearbeitung: Warten auf Freigabe")
		# >>> Critical Section
		self.m_oLock.acquire()
		globs.dbg("Stop Aufgabenbearbeitung: Freigabe erhalten")
		if self.m_oWatchDogTimer:
			self.m_oWatchDogTimer.cancel()
			self.m_oWatchDogTimer = None
		if not TaskQueueFastStop(self).start():
			bResult = False
		if not TaskQueueLongStop(self).start():
			bResult = False		
		self.m_evtRunning.clear()
		self.m_oLock.release()
		# <<< Critical Section
		globs.dbg("Stop Aufgabenbearbeitung: Freigabe abgegeben")
		if (self.m_oThreadFast):
			# Synchronization Point (Fast Thread Termination)
			globs.dbg("Stop Aufgabenbearbeitung: Warten auf leichte Bearbeitung")
			self.m_oThreadFast.join(20.0)
			if self.m_oThreadFast.is_alive():
				globs.err("Stop Aufgabenbearbeitung: Leichte Bearbeitung nicht beendet")
				bResult = False
			else:
				globs.dbg("Stop Aufgabenbearbeitung: Leichte Bearbeitung beendet")
				self.m_oQueueFast = None
			self.m_oThreadFast = None
		if (self.m_oThreadLong):
			# Synchronization Point (Long Thread Termination)
			globs.dbg("Stop Aufgabenbearbeitung: Warten auf schwere Bearbeitung")
			self.m_oThreadLong.join(60.0)
			if self.m_oThreadLong.is_alive():
				globs.err("Stop Aufgabenbearbeitung: Schwere Bearbeitung nicht beendet")
				bResult = False
			else:
				globs.dbg("Stop Aufgabenbearbeitung: Schwere Bearbeitung beendet")
				self.m_oQueueLong = None
			self.m_oThreadLong = None
		globs.dbg("Stop Aufgabenbearbeitung: Abgeschlossen (%r)" % (bResult))
		return bResult
	
