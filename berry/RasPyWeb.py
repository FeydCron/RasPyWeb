from . import globs

# Try to import from module "ptvsd" which might not be installed on the target system
#
g_bPackageMissing = True
try:
	import ptvsd
	ptvsd.enable_attach(address=("192.168.1.123", 5678))

	globs.dbg("Modul <ptvsd> scheint verfügbar zu sein")
	g_bPackageMissing = False

	#ptvsd.wait_for_attach()
except:
	globs.exc("Modul <ptvsd> scheint nicht verfügbar zu sein")

globs.registerPipPackage(
	g_bPackageMissing, "ptvsd", "Python Visual Studio Debugger engine",
	"""Das Paket kann verwendet werden, um Python-Programme mit Visual Studio oder
	Visual Studio Code zu debuggen.""")

import re
import traceback
import subprocess

from .voice import Voice
from .worker import Worker
from .httpd import Httpd

from . import sdk
from .sdk import TaskSpeak

# Try to import from module "mutagen" which might not be installed on the target system
#
g_bPackageMissing = True
try:
	from mutagen.mp3 import MP3

	globs.dbg("Modul <mutagen> scheint verfügbar zu sein")
	g_bPackageMissing = False
except:
	globs.exc("Modul <mutagen> scheint nicht verfügbar zu sein")

globs.registerPipPackage(
	g_bPackageMissing, "mutagen", "Python Multimedia Tagging Library",
	"""Das Paket wird verwendet, um die maximale Abspieldauer von MP3-Dateien zu ermitteln.
	Anhand der Abspieldauer wird die Laufzeit des MP3-Players begrenzt, sodass dieser nicht
	mehr Zeit als notwendig in Anspruch nehmen kann. Damit kann ein Problem mit dem omxplayer
	behoben werden, welcher sich gelegentlich nicht beendet und damit das Abspielen weiterer
	Klänge blockiert. Solange keine Probleme mit dem omxplayer beobachtet werden, besteht keine
	Notwendigkeit, das Paket zu installieren.""")

class Berry:
	
	def __init__(self):
		
		self.m_oWorker = Worker()
		self.m_oHttpd = Httpd(self.m_oWorker)
		
		return
	
	def run(self):
		
		strProgram = None
		strPID = None
		oSysCallCmd = False
		strGoodBye = "Tschüssikovski!"
		
		print("Attempt to start message queue ...")
		self.m_oWorker.startQueue()
		print("OK")
		
		TaskSpeak(self.m_oWorker, "Servus!").start()
		
		while True:
			
			print("Attempt to start HTTP Server ...")
			try:
				self.m_oHttpd.run()
				break
			except:
				globs.exc("HTTP Server starten und laufen lassen")
				
				if not (strProgram and strPID):
					# Einmalig versuchen, den belegten Port freizugeben
					oLines = sdk.getShellCmdOutput("netstat -pant")
					for strLine in oLines:
						if re.match(r"tcp\s+.*\s+%s\:%s\s+%s\s+LISTEN\s+\d+/dbus-daemon" % (
							re.escape(globs.s_oHttpd.server_address[0]),
							globs.s_oHttpd.server_address[1],
							re.escape("0.0.0.0:*")), strLine):
							for strToken in re.split(r"\s+", strLine):
								if (re.match(r"\d+/dbus-daemon", strToken)):
									strPID, strProgram = re.split(r"/", strToken)
									break
							if (strProgram and strPID):
								break
					if (strProgram and strPID):
						TaskSpeak(self.m_oWorker,
							"Das Program %s mit der Prozesskennung %s belegt den Port %s" % (
							strProgram, strPID, globs.s_oHttpd.server_address[1])).start()
						TaskSpeak(self.m_oWorker,
							"Ich versuche, das Program %s mit der Prozesskennung %s zu beenden" % (
							strProgram, strPID)).start()
							
						sdk.getShellCmdOutput("sudo kill %s" % strPID)
						continue
						
				TaskSpeak(self.m_oWorker,
					"Hoppla! Es gibt wohl Probleme mit dem Webb-Sörver.").start()
				break

		print("HTTP Server STOPPED")
		
		if globs.s_strExitMode == "halt":
			oSysCallCmd = "sudo halt"
			strGoodBye += " Das System wird jetzt heruntergefahren."
		if globs.s_strExitMode == "boot":
			oSysCallCmd = "sudo reboot"
			strGoodBye += " Das System wird jetzt neu gestartet."
		
		TaskSpeak(self.m_oWorker, strGoodBye).start()
		
		print("Attempt to stop message queue ...")
		if not self.m_oWorker.stopQueue():
			print("FAILED")
		else:
			print("OK")
		
		if oSysCallCmd:
			print("Executing final syscall: " + oSysCallCmd)
			subprocess.Popen(oSysCallCmd, shell=True)
		
		return

def main():
	oBerry = Berry()
	oBerry.run()
	return

# Ausführung des Hauptprogramms
if __name__ == '__main__':
	
	oVoiceDe = Voice("de-DE")
	oVoiceEn = Voice("en-US")
	
	try:
		
		main()
	
	except:
	
		strTalk = "Marco? \n"
		strTalk += "In meinem Programm ist ein unerwarteter Fehler aufgetreten. \n"
		strTalk += "Es wäre schön, wenn Du Dich zeitnah darum kümmern könntest. \n"
		strTalk += "Hier sind die Details: \n"
		
		strExc = "{0}".format(traceback.format_exc())
		
		print(strTalk + strExc)
		
		
#		oVoiceDe.speak(strTalk)
		
#		oVoiceEn.speak(strExc)
