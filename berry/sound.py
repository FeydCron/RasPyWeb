import os.path
import re
import subprocess

import globs

# Try to import from module "mutagen" which might not be installed on the target system
#
try:
	from mutagen.mp3 import MP3
except:
	pass

class Sound:
	
	###########################################################################
	# Konstruktor
	#
	def __init__(self):
		pass
		return

	# Sound abspielen
	def sound(self, strSound):
		strFile = None
		lstArgs = None
		strPlay = "aplay"
		fTimeout = None

		# >>> Critical Section
		globs.s_oSettingsLock.acquire()
		try:
			if "Sounds" in globs.s_dictSettings:
				# Direkte Übereinstimmung finden
				for (strCategory, dictSounds) in globs.s_dictSettings["Sounds"].items():
					if strSound in dictSounds:
						strFile = globs.s_dictSettings["Sounds"][strCategory][strSound]
						break
				if not strFile:
					# Partiellen Treffer finden
					for (strCategory, dictSounds) in sorted(globs.s_dictSettings["Sounds"].items()):
						for (strName, strPath) in dictSounds.items():
							if re.match(".*" + strSound + ".*", strName):
								globs.log("Sound '%s' für angeforderten Sound '%s' verwendet." % (
									strName, strSound))
								strFile = strPath
								break
		except:
			globs.exc("Sound '%s' finden" % (strSound))
		globs.s_oSettingsLock.release()
		# <<< Critical Section
		
		if not strFile:
			globs.wrn("Der angeforderte Sound konnte nicht gefunden werden: '%s'" % (strSound))
			print("\\a")
			return
	
		if os.path.isfile(strFile):
			if re.match(".*\\.[Ww][Aa][Vv]", strFile):
				#strPlay = "aplay"
				lstArgs = list(["aplay", strFile])
			elif re.match(".*\\.[Mm][Pp]3", strFile):
				#strPlay = "omxplayer -o both"
				lstArgs = list(["mpg321", strFile])
				if not globs.isMissingPipPackage("mutagen"):
					oAudio = MP3(strFile)
					fTimeout = globs.getWatchDogInterval() + oAudio.info.length
			else:
				globs.wrn("Das Format der Sound-Datei wird nicht unterstützt: '%s'" % (strFile))
				print("\\a")
				return
		else:
			globs.wrn("Die Datei des angeforderten Sounds ist ungültig: '%s'" % (strFile))
			print("\\a")
			return
			
		print("Now playing: '%r' --> '%s' <%s> with timeout %r" %(lstArgs, strSound, strFile, fTimeout))
		#os.system('%s "%s"' %(strPlay, strFile))
		subprocess.call(lstArgs, timeout=fTimeout)
		return
