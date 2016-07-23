import time
from datetime import datetime

from Globs import Globs

from SDK import ModuleBase
from SDK import TaskSound
from SDK import TaskSpeak

class Clock(ModuleBase):
	
	def moduleInit(self, dictModCfg={}, dictCfgUsr={}):
		dictSettings = {
			"nSilenceFrom" : 19,
			"nSilenceTo" : 6,
			"nTellTimeInt" : 30,
			"strSoundHour" : "BellToll",
		}
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})
		
		dictCfgUsr.update({
			"nSilenceFrom" : {
				"title"			: "Beginn der Ruhezeit",
				"description"	: ("Der Beginn der Ruhezeit gibt an, ab welcher Stunde (0..23) "+
									"keine Glockenschläge und keine Zeitansagen ausgegeben werden "+
									"sollen. Zusammen mit dem Ende der Ruhezeit kann so ein "+
									"Zeitfenster der Stille festgelegt werden, um Ruhestörungen "+
									"zu vermeiden."),
				"default"		: "19"
			},
			"nSilenceTo" : {
				"title"			: "Ende der Ruhezeit",
				"description"	: ("Das Ende der Ruhezeit gibt an, ab welcher Stunde (0..23) "+
									"Glockenschläge und Zeitansagen ausgegeben werden dürfen "+
									"Zusammen mit dem Beginn der Ruhezeit kann so ein Zeitfenster "+
									"der Stille festgelegt werden, um Ruhestörungen zu vermeiden."),
				"default"		: "19"
			},
			"nTellTimeInt" : {
				"title"			: "Uhrzeitansage",
				"description"	: ("Die Uhrzeit kann in einem festen Raster von stündlich bis "+
									"alle 5 Minuten angesagt werden."),
				"default"		: "30",
				"choices"		: {
					"Jede volle Stunde"		: "60",
					"Jede halbe Stunde" 	: "30",
					"Jede viertel Stunde"	: "15",
					"Alle 5 Minuten"		: "5"
				}
			},
			"strSoundHour" : {
				"title"			: "Klang Stundenschlag",
				"description"	: ("Die akustische Anzeige der Uhrzeit erfolgt durch den "+
									"angegebenen Klang."),
				"default"		: "BellToll",
				"choices"		: Globs.s_dictSettings["Sounds"],
				"keyIsValue" 	: True
			},
			})
		self.m_nSilenceFrom = Globs.getSetting("Clock", "nSilenceFrom", "\\d{1,2}", 19)
		self.m_nSilenceTo = Globs.getSetting("Clock", "nSilenceTo", "\\d{1,2}", 6)
		self.m_nTellTimeInt = Globs.getSetting("Clock", "nTellTimeInt", "\\d{1,2}", 30)
		return True
		
	def moduleExec(self,
		strPath,
		oHtmlPage,
		dictQuery,
		dictForm
		):
		print("%r::moduleExec(strPath=%s, dictQuery=%s, dictForm=%s) [%s]" % (
			self, strPath, dictQuery, dictForm, datetime.today().strftime("%X")))
		
		if not dictQuery:
			return False
			
		# Akustische Uhrzeitanzeige
		bResult = False
		for (strCmd, lstArg) in dictQuery.items():
			if (strCmd == "timer" and lstArg and lstArg[0] == "cron"):
				self.updateTime()
				# Default: Aktustische Zeitanzeige
				if Globs.getSetting("System", "bTestMode", "True|False", False):
					TaskSpeak(self.getWorker(), "Entschuldigung. Test.").start()
					self.gong()
					self.speakTime()
				elif (self.isAllowed() and (self.m_nMinutes % self.m_nTellTimeInt) == 0):
					self.gong()
					self.speakTime()
				bResult = True
			elif (strCmd == "clock"):
				for strArg in lstArg:
					self.updateTime()
					# Nur Glockenschlag ausführen
					if (strArg == "gong"):
						self.gong()
						bResult = True
						continue
					# Nur Zeitansage ausführen
					if (strArg == "speak"):
						self.speakTime()
						bResult = True
						continue
					# Modultest ausführen
					if (strArg == "test"):
						TaskSpeak(self.getWorker(), "Der Modultest für die Uhr wird jetzt gestartet").start()
						nHour = 1
						nMinute = 0
						while (nHour <= 12):
							self.m_nHour12h = nHour
							TaskSpeak(self.getWorker(), "Stunde " + str(self.m_nHour12h)).start()
							while (nMinute <= 59):
								self.m_nMinutes = nMinute
								TaskSpeak(self.getWorker(), "Minute " + str(self.m_nMinutes)).start()
								self.speakTime()
								self.m_nTimeSpoken = 0
								nMinute += 1
							nMinute = 0
							nHour += 1
						TaskSpeak(self.getWorker(), "Der Modultest für die Uhr ist jetzt beendet").start()
		# Unbekanntes Kommando
		return bResult

	# Bereichsprüfung
	def isAllowed(self):
		if self.m_nSilenceFrom > self.m_nSilenceTo:
			# Inside-Range
			return (self.m_nHour24h < self.m_nSilenceFrom and self.m_nHour24h > self.m_nSilenceTo)
		elif self.m_nSilenceFrom < self.m_nSilenceTo:
			# Outside-Range
			return (self.m_nHour24 < self.m_nSilenceFrom or self.m_nHour24h > self.m_nSilenceTo)

		# No range
		return True
	
	# Aktuelle Zeit holen und in globalen Variablen speichern
	def updateTime(self):
		self.m_strMonName = time.strftime("%B")
		self.m_strDayName = time.strftime("%A")
		self.m_nMonYear = int(time.strftime("%m"))
		self.m_nDayWeek = int(time.strftime("%w"))
		self.m_nYear4xY = int(time.strftime("%Y"))
		self.m_nYear2xY = int(time.strftime("%y"))
		self.m_nWeekOfY = int(time.strftime("%W"))
		self.m_nHour24h = int(time.strftime("%H"))
		self.m_nHour12h = int(time.strftime("%I"))
		self.m_nMinutes = int(time.strftime("%M"))
		self.m_nTimeSpoken = 0
		self.m_nSilenceFrom = Globs.getSetting("Clock", "nSilenceFrom", "\\d{1,2}", 19)
		self.m_nSilenceTo = Globs.getSetting("Clock", "nSilenceTo", "\\d{1,2}", 6)
		self.m_nTellTimeInt = Globs.getSetting("Clock", "nTellTimeInt", "\\d{1,2}", 30)
		return
	
	# Glockenschlag
	def gong(self):		
		nCount = 0
		if (self.m_nMinutes % self.m_nTellTimeInt) == 0:
			if self.m_nMinutes == 0:
				nCount = self.m_nHour12h
			elif self.m_nTellTimeInt == 30 or self.m_nTellTimeInt == 5:
				nCount = 1
			else:
				nCount = int(self.m_nMinutes / 15)
		# Testmodus berücksichtigen
		if (nCount == 0 and Globs.getSetting("System", "bTestMode", "True|False", False)):
			nCount = 1
		# Ggf. Sound abspielen
		if (nCount >= 1):
			TaskSound(self.getWorker(),
				Globs.getSetting("Clock", "strSoundHour", ".+", "BellToll"),
				nLoops = nCount).start()
		return
	
	# Akustische Zeitansage
	def speakTime(self):
		if self.m_nTimeSpoken > 0:
			return
		self.m_nTimeSpoken += 1
		
		# Zeitansage in Bezug auf nächste volle Stunde zusammenbasteln
		strHour = ""
		nHour = self.m_nHour12h
		if self.m_nMinutes >= 45:
			strPart = "drei-viertel"
			strNext = ""
			nHour += 1
		elif self.m_nMinutes >= 30:
			strPart = "halb"
			strNext = "drei-viertel"
			nHour += 1
		elif self.m_nMinutes >= 15:
			strPart = "viertel"
			strNext = "halb"
			nHour += 1
		else:
			strPart = ""
			strNext = "viertel"
			if self.m_nMinutes >= 8:
				nHour += 1
		
		# Ansage "Uhr" nur um die volle Stunde herum
		if self.m_nMinutes >= 53 or self.m_nMinutes < 8:
			strHour = "Uhr"
			
		# Nächste volle Stunde innerhalb des 12h-Intervalls beachten
		if nHour == 13:
			nHour = 1
			
		# Angabe der Minuten in Bezug auf die Viertelstunde natürlicher formulieren
		nMinutesPast = self.m_nMinutes % 15
		if not nMinutesPast == 0:
			if nMinutesPast < 8:
				strPart = "nach " + strPart
			else:
				strPart = "vor " + strNext
			
		# Komplette Zeitansage zusammensetzen und aussprechen
		strSpeech = "Es ist jetzt " + strPart + " " + str(nHour) + " " + strHour
		TaskSpeak(self.getWorker(), strSpeech).start()
		return
