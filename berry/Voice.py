import os
import os.path
import hashlib

class Voice:
	
	########################################################################
	# Konstruktor
	# param strLang
	#			zu verwendende Sprache, default ist "de-DE"
	#
	def __init__(self, strLang):
		
		if strLang is None or len(strLang) == 0:
			strLang = "de-DE"
			
		self.m_strLang = strLang
		return
		
	########################################################################
	# Sprachausgabe
	# param strSpeak
	#			zu sprechender Text als String
	# param strLang
	#			zu verwendende Sprache, default ist "de-DE"
	#
	def speak(self, strSpeak):
		
		hash = hashlib.md5(strSpeak.encode())
		strFile = "/tmp/" + self.m_strLang + "_" + hash.hexdigest() + ".wav"
		
		if not os.path.isfile(strFile):
			os.system('pico2wave --lang=%s --wave=%s "%s"' %(self.m_strLang, strFile, strSpeak))
		
		os.system('aplay %s' %strFile)
		return
