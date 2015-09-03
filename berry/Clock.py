import os
import os.path
import time
import hashlib

from Globs import Globs
from Sound import Sound
from Voice import Voice

class Clock:
	
	def __init__(self):
		self.updateTime()
		
		self.m_nTimeSpoken = 0
		
		self.m_oGlobs = Globs()
		self.m_oVoice = Voice("de-DE")
		self.m_oSound = Sound()
		return
	
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
		
		if (self.m_nMinutes % self.m_oGlobs.s_nTellTimeInt) == 0:
			if self.m_nMinutes == 0:
				nCount = self.m_nHour24
			elif self.m_oGlobs.s_nTellTimeInt == 30:
				nCount = 1
			else:
				nCount = self.m_nMinutes / self.m_oGlobs.s_nTellTimeInt
		
		for i in range(nCount):
			self.m_oSound.sound("BellToll")
		
		if nCount == 0 and self.m_oGlobs.s_bTestMode:
			self.m_oSound.sound("BellToll")
		return
	
	# Akustische Zeitansage
	def speakTime(self):
		
		if self.m_nTimeSpoken > 0:
			return
	
		self.m_nTimeSpoken += 1
	
		strPart = "um"
		strNext = "viertel"
		nHour = self.m_nHour12h
	
		if self.m_nMinutes >= 45:
			strPart = "drei - viertel"
			strNext = "um"
			nHour += 1
		elif self.m_nMinutes >= 30:
			strPart = "halb"
			strNext = "drei - viertel"
			nHour += 1
		elif self.m_nMinutes >= 15:
			strPart = "viertel"
			strNext = "halb"
			nHour += 1
	
		if nHour == 13:
			nHour = 1
	
		nMinutesPast = self.m_nMinutes % 15
		if nMinutesPast > 1 and nMinutesPast <= 5:
			strPart = "kurz nach " + strPart
		elif nMinutesPast > 5 and nMinutesPast <= 10:
			strPart = "nach " + strPart
		elif nMinutesPast > 10:
			strPart = "kurz vor " + strNext
	
		strSpeech = "Es ist jetzt " + strPart + " " + str(nHour)
		self.m_oVoice.speak(strSpeech)
		return
	
	# Ausführung der Uhr
	def run(self):
		self.updateTime()
		
		if self.m_oGlobs.s_bTestMode:
			self.m_oVoice.speak("Entschuldigung. Test.")
			self.gong()
			self.speakTime()
		elif self.m_nHour24h < nSilenceFrom and nHour24h > nSilenceTo:
			if (self.m_nMinutes % self.s_nTellTimeInt) == 0:
				self.gong()
				self.speakTime()
		return
