try:
	import ptvsd
	ptvsd.enable_attach("debug")
except:
	pass

import sys
import os
import re
import traceback
import time
import subprocess
from subprocess import call

from Sound import Sound
from Voice import Voice
from Globs import Globs
from Worker import Worker
from Httpd import Httpd

import SDK
from SDK import TaskSpeak

class Berry:
	
	def __init__(self):
		
		self.m_oWorker = Worker()
		self.m_oHttpd = Httpd(self.m_oWorker)
		self.m_oGlobs = Globs()
		
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
				Globs.exc("HTTP Server starten und laufen lassen")
				
				if not (strProgram and strPID):
					# Einmalig versuchen, den belegten Port freizugeben
					oLines = SDK.getShellCmdOutput("netstat -pant")
					for strLine in oLines:
						if re.match("tcp\\s+.*\\s+%s\\:%s\\s+%s\\s+LISTEN\\s+\\d+/dbus-daemon" % (
							re.escape(Globs.s_oHttpd.server_address[0]),
							Globs.s_oHttpd.server_address[1],
							re.escape("0.0.0.0:*"), strLine)):
							for strToken in re.split("\\s+", strLine):
								if (re.match("\\d+/dbus-daemon", strToken)):
									strPID, strProgram = re.split("/", strToken)
									break
							if (strProgram and strPID):
								break;
					if (strProgram and strPID):
						TaskSpeak(self.m_oWorker,
							"Das Program %s mit der Prozesskennung %s belegt den Port %s" % (
							strProgram, strPID, Globs.s_oHttpd.server_address[1])).start()
						TaskSpeak(self.m_oWorker,
							"Ich versuche, das Program %s mit der Prozesskennung %s zu beenden" % (
							strProgram, strPID)).start()
							
						SDK.getShellCmdOutput("sudo kill %s" % strPID)
						continue
						
				TaskSpeak(self.m_oWorker,
					"Hoppla! Es gibt wohl Probleme mit dem Webb-Sörver.").start()
				break

		print("HTTP Server STOPPED")
		
		if Globs.s_strExitMode == "halt":
			oSysCallCmd = "sudo halt"
			strGoodBye += " Das System wird jetzt heruntergefahren."
		if Globs.s_strExitMode == "boot":
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
