import time
from datetime import datetime

from Globs import Globs

from SDK import ModuleBase
from SDK import TaskSound
from SDK import TaskSpeak

class Clock(ModuleBase):
	
	def moduleExec(self, strPath, strCmd, strArg):
		print("%r::moduleExec(strPath=%s, strCmd=%s, strArg=%s) [%s]" % (
			self, strPath, strCmd, strArg, datetime.today().strftime("%X")))
		# Akustische Uhrzeitanzeige
		if (strCmd == "clock"):
			self.updateTime()
			# Nur Glockenschlag ausführen
			if (strArg == "gong"):
				self.gong()
				return True
			# Nur Zeitansage ausführen
			if (strArg == "speak"):
				self.speakTime()
				return True
			# Default: Aktustische Zeitanzeige
			if Globs.s_bTestMode:
				TaskSpeak(self.getWorker(), "Entschuldigung. Test.").start()
				self.gong()
				self.speakTime()
			elif (self.m_nHour24h < Globs.s_nSilenceFrom
				and self.m_nHour24h > Globs.s_nSilenceTo):
				if (self.m_nMinutes % Globs.s_nTellTimeInt) == 0:
					self.gong()
					self.speakTime()
			return True
		# Unbekanntes Kommando
		return False
	
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
		return
	
	# Glockenschlag
	def gong(self):		
		nCount = 0
		if (self.m_nMinutes % Globs.s_nTellTimeInt) == 0:
			if self.m_nMinutes == 0:
				nCount = self.m_nHour12h
			elif Globs.s_nTellTimeInt == 30:
				nCount = 1
			else:
				nCount = self.m_nMinutes / Globs.s_nTellTimeInt
		# Testmodus berücksichtigen
		if (nCount == 0 and Globs.s_bTestMode):
			nCount = 1
		# Ggf. Sound abspielen
		if (nCount >= 1):
			TaskSound(self.getWorker(), "BellToll", nLoops = nCount).start()
		return
	
	# Akustische Zeitansage
	def speakTime(self):
		if self.m_nTimeSpoken > 0:
			return
		self.m_nTimeSpoken += 1
		# Zeitansage in Bezug auf nächste volle Stunde zusammenbasteln
		strPart = "um"
		strNext = "viertel"
		nHour = self.m_nHour12h
		if self.m_nMinutes >= 45:
			strPart = "drei-viertel"
			strNext = "um"
			nHour += 1
		elif self.m_nMinutes >= 30:
			strPart = "halb"
			strNext = "drei-viertel"
			nHour += 1
		elif self.m_nMinutes >= 15:
			strPart = "viertel"
			strNext = "halb"
			nHour += 1
		# Nächste volle Stunde innerhalb des 12h-Intervalls beachten
		if nHour == 13:
			nHour = 1
		# Angabe der Minuten etwas natürlicher formulieren
		nMinutesPast = self.m_nMinutes % 15
		if nMinutesPast > 1 and nMinutesPast <= 5:
			strPart = "kurz nach " + strPart
		elif nMinutesPast > 5 and nMinutesPast <= 10:
			strPart = "nach " + strPart
		elif nMinutesPast > 10:
			strPart = "kurz vor " + strNext
		# Komplette Zeitansage zusammensetzen und aussprechen
		strSpeech = "Es ist jetzt " + strPart + " " + str(nHour)
		TaskSpeak(self.getWorker(), strSpeech).start()
		return
