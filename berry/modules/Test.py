## 
#  Test Plug-In
#  
#  @file Test.py
#  @brief Plug-In für Testzwecke.
#  

import globs

import sdk
from sdk import ModuleBase
from sdk import TaskSpeak

class Test(ModuleBase):
	
	## 
	#  @copydoc sdk::ModuleBase::moduleInit
	#  
	def moduleInit(self, dictModCfg=None, dictCfgUsr=None):
		print("%r::moduleInit(%s) Version 5" % (self, sdk.getCpuTemp()))
		return True
	
	## 
	#  @brief Brief
	#  
	#  @param [in] self Parameter_Description
	#  @return Return_Description
	#  
	#  @details Details
	#  	
	def moduleExit(self):
		print("%r::moduleExit()" % (self))
		return True
	
	
	#==============================================================================
	# moduleWidget
	#==============================================================================
	def moduleWidget(self):
		pass
	

	## 
	#  @brief Ausführung der Modulaktion.
	#  
	#  @param [in] self			Objektinstanz
	#  @param [in] strPath		die angeforderte Pfadangabe
	#  @param [in] oHtmlPage	die zu erstellende HTML-Seite
	#  @param [in] dictQuery	Dictionary der angeforderten Parameter und Werte als Liste
	#  @param [in] dictForm		Dictionary der angeforderten Formularparameter und Werte als Liste
	#  @return
	#  Liefert True, wenn die Aktion erfolgreich ausgeführt werden konnte oder
	#  False im Falle eines Fehlers.
	#  
	#  @details Details
	#  		
	def moduleExec(self,
		strPath,
		oHtmlPage,
		dictQuery,
		dictForm
		):
		print("%r::moduleExec(strPath=%s, oHtmlPage=%s, dictQuery=%r, dictForm=%r)" % (
			self, strPath, oHtmlPage, dictQuery, dictForm))

		if not dictQuery:
			return False

		bResult = False
		for (strCmd, lstArg) in dictQuery.items():
			if (strCmd == "cputemp"):
				for strArg in lstArg:
					# Modultest für die CPU-Temperaturüberwachung
					if (strArg == "hysterese"):
						TaskSpeak(self.getWorker(), "Der Modultest für die Temperaturüberwachung der CPU wird vorbereitet").start()
						
						fCpuTempA = globs.getSetting("System", "fCpuTempA", "\\d{2,}\\.\\d+", 60.0)
						fCpuTempB = globs.getSetting("System", "fCpuTempB", "\\d{2,}\\.\\d+", 56.0)
						fCpuTempC = globs.getSetting("System", "fCpuTempC", "\\d{2,}\\.\\d+", 53.0)
						fCpuTempH = globs.getSetting("System", "fCpuTempH", "\\d{2,}\\.\\d+", 1.0)

						fCpuTempStep = fCpuTempH / 2.0
						fCpuTempDir = 1.0
						fCpuTempBase = sdk.getCpuTemp()
						fCpuTemp = fCpuTempBase
						fCpuTempHyst = fCpuTempH * 2.0
						nHysTest = 0

						globs.s_oQueueTestCpuTempValues.put(fCpuTemp, block=False)

						# Erst steigende, dann sinkende Temperaturen
						while (fCpuTemp >= (fCpuTempC - (fCpuTempHyst * 2.0))):
							fCpuTemp += (fCpuTempStep * fCpuTempDir)
							globs.s_oQueueTestCpuTempValues.put(fCpuTemp, block=False)
							
							# Erste Hysterese testen
							if (fCpuTemp > (fCpuTempC + fCpuTempHyst) and nHysTest == 0):
								while (fCpuTemp > (fCpuTempC - fCpuTempHyst)):
									fCpuTemp -= fCpuTempStep
									globs.s_oQueueTestCpuTempValues.put(fCpuTemp, block=False)
								nHysTest += 1

							# Zweite Hysterese testen
							if (fCpuTemp > (fCpuTempB + fCpuTempHyst) and nHysTest == 1):
								while (fCpuTemp > (fCpuTempB - fCpuTempHyst)):
									fCpuTemp -= fCpuTempStep
									globs.s_oQueueTestCpuTempValues.put(fCpuTemp, block=False)
								nHysTest += 1

							# Dritte Hysterese testen
							if (fCpuTemp > (fCpuTempA + fCpuTempHyst) and nHysTest == 2):
								while (fCpuTemp > (fCpuTempA - fCpuTempHyst)):
									fCpuTemp -= fCpuTempStep
									globs.s_oQueueTestCpuTempValues.put(fCpuTemp, block=False)
								nHysTest += 1

							# Temperaturrichtung umkehren
							if (fCpuTemp >= (fCpuTempA + (fCpuTempHyst * 0.75)) and nHysTest == 3):
								fCpuTempDir *= (-1.0)
								nHysTest += 1

						bResult = True
						TaskSpeak(self.getWorker(), "Der Modultest für die Temperaturüberwachung der CPU ist jetzt bereit").start()
						continue
		# Unbekanntes Kommando
		return bResult