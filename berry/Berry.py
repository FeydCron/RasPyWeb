import sys
import os
import traceback
import time
import subprocess
from subprocess import call

from Sound import Sound
from Voice import Voice
from Globs import Globs
from Worker import Worker
from Httpd import Httpd
from SDK import TaskSpeak

class Berry:
	
	def __init__(self):
		
		self.m_oWorker = Worker()
		self.m_oHttpd = Httpd(self.m_oWorker)
		self.m_oGlobs = Globs()
		
		return
	
	def run(self):
		
		oSysCallCmd = False
		strGoodBye = "Tschüssikovski!"
		
		print("Attempt to start message queue ...")
		self.m_oWorker.startQueue()
		print("OK")
		
		TaskSpeak(self.m_oWorker, "Servus!").start()
		
		print("Attempt to start HTTP Server ...")
		try:
			self.m_oHttpd.run()
		except:
			Globs.exc("HTTP Server starten und laufen lassen")
			TaskSpeak(self.m_oWorker, "Hoppla! Scheinbar gibt es ein Problem mit der Webb Sörver Schnittstelle.").start()
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
