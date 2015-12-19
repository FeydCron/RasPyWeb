import sys
import traceback
import time
import threading
import queue
import traceback

from Globs import Globs

import SDK
from SDK import FastTask
from SDK import LongTask
from SDK import TaskSpeak

class FutureTask(FastTask):

	def __init__(self, oWorker):	
		super(FutureTask, self).__init__(oWorker)
		self.m_evtDone = threading.Event()
		self.m_evtDone.clear()
		return
		
	def __str__(self):
		strDesc = "Warten auf die Fertigstellung einer Aufgabe"
		return  strDesc
	
	def done(self, bResult = True):
		self.m_oWorker.m_oQueueFast.task_done()
		self.m_evtDone.set()
		return
		
	def wait(self):
		self.m_evtDone.wait()
		return

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
		Globs.s_strExitMode = self.m_strMode
		for oInstance in self.m_oWorker.m_dictModules.values():
			oInstance.moduleExit()
		self.m_oWorker.m_dictModules.clear()
		Globs.saveSettings()
		Globs.shutdown()
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
	s_bCpuTempWrn = False
	s_bHistory = False
	
	def __str__(self):
		strDesc = "Überwachen des Systems"
		return  strDesc

	def do(self):
		fCpuTemp = SDK.getCpuTemp()
		strCpuUse = SDK.getCpuUse().strip()
		lstRamInfo = SDK.getRamInfo()
		lstDiskSpace = SDK.getDiskSpace()
		try:
			fCpuUse = float(strCpuUse.replace(",", ".", 1))
		except:
			fCpuUse = 0.0
		# IP-Adresse ermitteln
		if not TaskSystemWatchDog.s_strIpAddr:
			TaskSystemWatchDog.s_strIpAddr = SDK.getNetworkInfo(
				Globs.getSetting("System", "strNetInfoName"))
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
		if "CPU" not in Globs.s_dictSystemValues:
			Globs.s_dictSystemValues.update({"CPU" : {}})
		if "RAM" not in Globs.s_dictSystemValues:
			Globs.s_dictSystemValues.update({"Arbeitsspeicher" : {}})
		if "MEM" not in Globs.s_dictSystemValues:
			Globs.s_dictSystemValues.update({"Speicherkapazität" : {}})
		if "Netzwerk" not in Globs.s_dictSystemValues:
			Globs.s_dictSystemValues.update({"Netzwerk" : {}})
		# Systemwerte eintragen
		Globs.s_dictSystemValues["CPU"].update({
			"Auslastung"		: "%s%%" % (strCpuUse),
			"Auslastung Min"	: "%0.2f%%" % (TaskSystemWatchDog.s_fCpuUseMin),
			"Auslastung Max"	: "%0.2f%%" % (TaskSystemWatchDog.s_fCpuUseMax),
			"Auslastung Avg"	: "%0.2f%%" % (TaskSystemWatchDog.s_fCpuUseAvg),
			"Temperatur"		: "%0.1f°C" % (fCpuTemp),
			"Temperatur Min"	: "%0.2f°C" % (TaskSystemWatchDog.s_fCpuTempMin),
			"Temperatur Max"	: "%0.2f°C" % (TaskSystemWatchDog.s_fCpuTempMax),
			"Temperatur Avg"	: "%0.2f°C" % (TaskSystemWatchDog.s_fCpuTempAvg),})
		Globs.s_dictSystemValues["Netzwerk"].update({
			"IP-Adresse"		: "%s" % (TaskSystemWatchDog.s_strIpAddr),})
		lstLabels = ["Gesamt", "Belegt", "Frei", "Geteilt", "Gepuffert", "Im Cache"]
		nIndex = 0
		for strData in lstRamInfo:
			Globs.s_dictSystemValues["RAM"].update({
			lstLabels[nIndex]	: strData + "K"})
			nIndex += 1
		lstLabels = ["Gesamt", "Belegt", "Verfügbar", "Belegung"]
		nIndex = 0
		for strData in lstDiskSpace:
			Globs.s_dictSystemValues["MEM"].update({
			lstLabels[nIndex]	: strData})
			nIndex += 1
		# Nächsten Durchlauf einplanen
		self.m_oWorker.runSystemWatchDog()
		# CPU-Temperatur auswerten
		strCpuTemp = ("%0.1f Grad" % (TaskSystemWatchDog.s_fCpuTempAvg)
			).replace(".", " Komma ")
		if TaskSystemWatchDog.s_fCpuTempAvg > Globs.getSetting("System", "fCpuTempA", "\\d{2,}\\.\\d+", 60.0):
			TaskSystemWatchDog.s_bCpuTempWrn = True
			TaskSystemWatchDog.s_nCpuTooHot += 1
			TaskSpeak(self.m_oWorker, "Achtung!").start()
			TaskSpeak(self.m_oWorker, "Temperaturüberschreitung mit %s!" % (
				strCpuTemp)).start()
			if (TaskSystemWatchDog.s_nCpuTooHot >= 10):
				TaskSpeak(self.m_oWorker, "Notabschaltung eingeleitet!").start()
				TaskExit(self.m_oWorker, "term").start()
				Globs.stop()
			else:
				TaskSpeak(self.m_oWorker,
					"Notabschaltung zu %s Prozent wahrscheinlich!" % (
					TaskSystemWatchDog.s_nCpuTooHot * 10)).start()
		elif TaskSystemWatchDog.s_fCpuTempAvg > Globs.getSetting("System", "fCpuTempB", "\\d{2,}\\.\\d+", 56.0):
			TaskSystemWatchDog.s_bCpuTempWrn = True
			if TaskSystemWatchDog.s_nCpuTooHot > 0:
				TaskSystemWatchDog.s_nCpuTooHot -= 1
			TaskSpeak(self.m_oWorker,
				"Die Temperatur ist mit %s zu hoch!" % (
				strCpuTemp)).start()
		elif TaskSystemWatchDog.s_fCpuTempAvg > Globs.getSetting("System", "fCpuTempC", "\\d{2,}\\.\\d+", 53.0):
			TaskSystemWatchDog.s_bCpuTempWrn = True
			TaskSystemWatchDog.s_nCpuTooHot = 0
			TaskSpeak(self.m_oWorker,
				"Die Temperatur ist mit %s relativ hoch" % (
				strCpuTemp)).start()
		elif TaskSystemWatchDog.s_bCpuTempWrn:
			TaskSystemWatchDog.s_bCpuTempWrn = False
			TaskSystemWatchDog.s_nCpuTooHot = 0
			TaskSpeak(self.m_oWorker,
				"Die Temperatur ist mit %s wieder im normalen Bereich" % (
				strCpuTemp)).start()
		elif not TaskSystemWatchDog.s_bHistory:
			pass
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
		Globs.loadSettings()
		self.m_oWorker.m_evtInit.set()
		for strComponent in Globs.s_dictSettings["dictModules"].keys():
			TaskModuleInit(self.m_oWorker, strComponent).start()
		return
		
class TaskModuleInit(FastTask):
	
	def __init__(self, oWorker, strComponent):
		super(TaskModuleInit, self).__init__(oWorker)
		self.m_strComponent = strComponent
		return
		
	def __str__(self):
		strDesc = "Verwalten des Moduls %s" % (self.m_strComponent)
		return  strDesc
	
	def do(self):
		# Gegebenenfalls die alte Instanz des Moduls entladen
		bUnloaded = False
		if (self.m_strComponent in self.m_oWorker.m_dictModules):
			oInstance = self.m_oWorker.m_dictModules.pop(self.m_strComponent)
			oInstance.moduleExit()
			del oInstance
			bUnloaded = True
		if (self.m_strComponent in Globs.s_dictSettings["dictModules"] and
			self.m_strComponent not in Globs.s_dictSettings["listInactiveModules"]):
			# Klasse des Moduls laden
			clsModule = Globs.importComponent("modules." + self.m_strComponent,
				Globs.s_dictSettings["dictModules"][self.m_strComponent])
			if not clsModule:
				strMsg = "Das Modul %s kann nicht geladen werden. Wahrscheinlich sind die Einstellungen falsch." % (
					self.m_strComponent)
				Globs.wrn(strMsg)
				TaskSpeak(self.m_oWorker, strMsg).start()
				return
			# Module instanziieren
			oInstance = clsModule(self.m_oWorker)
			del clsModule
			# >>> Critical Section
			Globs.s_oSettingsLock.acquire()
			if self.m_strComponent not in Globs.s_dictSettings:
				Globs.s_dictSettings.update({self.m_strComponent : {}})
			dictModCfg = Globs.s_dictSettings[self.m_strComponent]
			Globs.s_oSettingsLock.release()
			# <<< Critical Section
			dictCfgUsr = {}
			try:
				if not oInstance.moduleInit(dictModCfg=dictModCfg, dictCfgUsr=dictCfgUsr):
					strMsg = "Das Modul %s konnte nicht initialisiert werden." % (self.m_strComponent)
					Globs.wrn(strMsg)
					TaskSpeak(self.m_oWorker, strMsg).start()
					return
			except:
				Globs.exc("Verwalten des Moduls %s" % (self.m_strComponent))
				strMsg = "Das Modul %s konnte nicht initialisiert werden. Wahrscheinlich ist es veraltet und nicht mehr kompatibel." % (
					self.m_strComponent)
				Globs.wrn(strMsg)
				TaskSpeak(self.m_oWorker, strMsg).start()
				return
			# Module registrieren
			self.m_oWorker.m_dictModules.update({self.m_strComponent : oInstance})
			Globs.s_dictUserSettings.update({self.m_strComponent : dictCfgUsr})
			return
		if (self.m_strComponent not in Globs.s_dictSettings["dictModules"]):
			# >>> Critical Section
			Globs.s_oSettingsLock.acquire()
			if self.m_strComponent in Globs.s_dictSettings:
				Globs.s_dictSettings.pop(self.m_strComponent)
			if self.m_strComponent in Globs.s_dictUserSettings:
				Globs.s_dictUserSettings.pop(self.m_strComponent)
			Globs.s_oSettingsLock.release()
			# <<< Critical Section
			strMsg = "Das Modul %s wurde dauerhaft entfernt." % (self.m_strComponent)
			Globs.log(strMsg)
			TaskSpeak(self.m_oWorker, strMsg).start()
			return
		strMsg = "Das Modul %s wurde ausgeschaltet" % (self.m_strComponent)
		if (bUnloaded):
			strMsg += " und entladen"
		strMsg += "."
		Globs.log(strMsg)
		TaskSpeak(self.m_oWorker, strMsg).start()
		Globs.log(strMsg)
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
			10.0, self.onRunSystemWatchDog).start()
		Globs.dbg("Systemüberwachung: Nächste Prüfung eingeplant (%s)" % (
			self.m_oWatchDogTimer))
		return
	
	def fastThreadProc(self):
		self.m_bIsQueueFastShutdown = False
		Globs.log("Leichte Aufgabenbearbeitung: Gestartet")
		while True:
			bDone = False
			try:
				oTask = self.m_oQueueFast.get(
					block = not self.m_bIsQueueFastShutdown)
			except:
				# Abbruchbedingung für "do-while"
				Globs.log("Leichte Aufgabenbearbeitung: Abbruchbedingung")
				break
			Globs.dbg("Leichte Aufgabenbearbeitung: %s" % (oTask))
			try:
				oTask.do()
				bDone = True
			except:
				Globs.exc("Leichte Aufgabenbearbeitung: %s" % (oTask))
			oTask.done(bResult = bDone)
		Globs.log("Leichte Aufgabenbearbeitung: Beendet")
		return
		
	def longThreadProc(self):
		self.m_bIsQueueLongShutdown = False
		Globs.log("Schwere Aufgabenbearbeitung: Gestartet")
		while True:
			bDone = False
			try:
				oTask = self.m_oQueueLong.get(
					block = not self.m_bIsQueueLongShutdown)
			except:
				# Abbruchbedingung für "do-while"
				Globs.log("Schwere Aufgabenbearbeitung: Abbruchbedingung")
				break
			Globs.dbg("Schwere Aufgabenbearbeitung: %s" % (oTask))
			try:
				oTask.do()
				bDone = True
			except:
				Globs.exc("Schwere Aufgabenbearbeitung: %s" % (oTask))
			oTask.done()
		Globs.log("Schwere Aufgabenbearbeitung: Beendet")
		return
	
	def startQueue(self):
		Globs.dbg("Start Aufgabenbearbeitung: Warten auf Freigabe")
		# >>> Critical Section
		self.m_oLock.acquire()
		Globs.dbg("Start Aufgabenbearbeitung: Freigabe erhalten")
		self.m_oThreadFast = threading.Thread(target=self.fastThreadProc)
		self.m_oThreadFast.daemon = True
		self.m_oThreadLong = threading.Thread(target=self.longThreadProc)
		self.m_oThreadLong.daemon = True
		self.m_oQueueFast = queue.Queue()
		self.m_oQueueLong = queue.Queue()
		self.m_oThreadFast.start()
		self.m_oThreadLong.start()
		self.m_evtRunning.set()
		Globs.dbg("Start Aufgabenbearbeitung: Freigabe abgeben")
		self.m_oLock.release()
		# <<< Critical Section
		TaskInit(self).start()
		# Synchronization Point (Initialisation)
		Globs.dbg("Start Aufgabenbearbeitung: Warten auf Initialisierung")
		self.m_evtInit.wait()
		Globs.dbg("Start Aufgabenbearbeitung: Initialisierung abgeschlossen")
		# Set up cyclic monitoring of system values
		Globs.dbg("Start Aufgabenbearbeitung: Systemüberwachung starten")
		TaskSystemWatchDog(self).start()
		return
	
	def stopQueue(self):
		bResult = True
		if not self.m_evtRunning.isSet:
			Globs.log("Stop Aufgabenbearbeitung: Wurde bereits angefordert")
			return bResult
		Globs.dbg("Stop Aufgabenbearbeitung: Warten auf Freigabe")
		# >>> Critical Section
		self.m_oLock.acquire()
		Globs.dbg("Stop Aufgabenbearbeitung: Freigabe erhalten")
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
		Globs.dbg("Stop Aufgabenbearbeitung: Freigabe abgegeben")
		if (self.m_oThreadFast):
			# Synchronization Point (Fast Thread Termination)
			Globs.dbg("Stop Aufgabenbearbeitung: Warten auf leichte Bearbeitung")
			self.m_oThreadFast.join(20.0)
			if self.m_oThreadFast.is_alive():
				Globs.err("Stop Aufgabenbearbeitung: Leichte Bearbeitung nicht beendet")
				bResult = False
			else:
				Globs.dbg("Stop Aufgabenbearbeitung: Leichte Bearbeitung beendet")
				self.m_oQueueFast = None
			self.m_oThreadFast = None
		if (self.m_oThreadLong):
			# Synchronization Point (Long Thread Termination)
			Globs.dbg("Stop Aufgabenbearbeitung: Warten auf schwere Bearbeitung")
			self.m_oThreadLong.join(60.0)
			if self.m_oThreadLong.is_alive():
				Globs.err("Stop Aufgabenbearbeitung: Schwere Bearbeitung nicht beendet")
				bResult = False
			else:
				Globs.dbg("Stop Aufgabenbearbeitung: Schwere Bearbeitung beendet")
				self.m_oQueueLong = None
			self.m_oThreadLong = None
		Globs.dbg("Stop Aufgabenbearbeitung: Abgeschlossen (%r)" % (bResult))
		return bResult
	