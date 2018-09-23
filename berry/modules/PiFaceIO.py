import pifacedigitalio as piface

import re

import globs

from sdk import ModuleBase
from sdk import TaskModuleEvt

def createModuleInstance(
	oWorker):
	return PiFaceIO(oWorker)

class PiFaceIO(ModuleBase):
	
	## 
	#  @copydoc sdk::ModuleBase::moduleInit
	#  
	def moduleInit(self, dictModCfg={}, dictCfgUsr={}):
		dictSettings = {
			"strBoard" : "PIFACE_BOARD",
			"strPinDI" : "PIFACE_PIN_DI",
			"strPinDO" : "PIFACE_PIN_DO",
			"strState" : "PIFACE_STATE",
			"nEventDI1" : 0,
			"nEventDI2" : 0,
			"nEventDI3" : 0,
			"nEventDI4" : 0,
			"nEventDI5" : 0,
			"nEventDI6" : 0,
			"nEventDI7" : 0,
			"nEventDI8" : 0
		}

		self.m_strBoard = "PIFACE_BOARD"
		self.m_strPinDI = "PIFACE_PIN_DI"
		self.m_strPinDO = "PIFACE_PIN_DO"
		self.m_strState = "PIFACE_STATE"

		self.m_nEventDI1 = 0
		self.m_nEventDI2 = 0
		self.m_nEventDI3 = 0
		self.m_nEventDI4 = 0
		self.m_nEventDI5 = 0
		self.m_nEventDI6 = 0
		self.m_nEventDI7 = 0
		self.m_nEventDI8 = 0

		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})

		dictCfgUsr.update({
			"strBoard" : {
				"title"			: "Board-Kennung",
				"description"	: ("Die Einstellung legt die Bezeichnung für die Angabe der "+
									"Board-Kennung bei Ereignissen fest."),
				"default"		: "PIFACE_BOARD"
			},
			"strPinDI" : {
				"title"			: "Digitaleingang",
				"description"	: ("Die Einstellung legt die Bezeichnung für die Angabe des "+
									"Digitaleingangs bei Ereignissen fest."),
				"default"		: "PIFACE_PIN_DI"
			},
			"strPinDO" : {
				"title"			: "Digitalausgang",
				"description"	: ("Die Einstellung legt die Bezeichnung für die Angabe des "+
									"Digitalausgangs bei Ereignissen fest."),
				"default"		: "PIFACE_PIN_DO"
			},
			"strState" : {
				"title"			: "Zustand",
				"description"	: ("Die Einstellung legt die Bezeichnung für die Angabe des "+
									"Zustands eines Ein- oder Ausgangs bei Ereignissen fest."),
				"default"		: "PIFACE_VALUE"
			},
			"nEventDI1" : {
				"title"			: "Ereignis Digitaleingang 1",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 1 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI2" : {
				"title"			: "Ereigniskennung Eingang 2",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 2 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI3" : {
				"title"			: "Ereigniskennung Eingang 3",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 3 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI4" : {
				"title"			: "Ereigniskennung Eingang 4",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 4 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI5" : {
				"title"			: "Ereigniskennung Eingang 5",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 5 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI6" : {
				"title"			: "Ereigniskennung Eingang 6",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 6 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI7" : {
				"title"			: "Ereigniskennung Eingang 7",
				"description"	: ("Die Einstellung legt das Auslösen eines Ereignisses am "+
									"Digitaleingang 7 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
			"nEventDI8" : {
				"title"			: "Ereigniskennung Eingang 8",
				"description"	: ("Die Einstellung legt die Ereigniskennung für den "+
									"Digitaleingang 8 fest."),
				"default"		: 0,
				"choices"		: {
					"Deaktiviert"		: "0",
					"Nur Einschalten"	: "1",
					"Nur Ausschalten"	: "2",
					"Immer"				: "3"
				}
			},
		})
		self.updateContext()
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
		return True

	## 
	#  @brief Ausf�hrung der Modulaktion.
	#  
	#  @param [in] self			Objektinstanz
	#  @param [in] strPath		die angeforderte Pfadangabe
	#  @param [in] oHtmlPage	die zu erstellende HTML-Seite
	#  @param [in] dictQuery	Dictionary der angeforderten Parameter und Werte als Liste
	#  @param [in] dictForm		Dictionary der angeforderten Formularparameter und Werte als Liste
	#  @return
	#  Liefert True, wenn die Aktion erfolgreich ausgef�hrt werden konnte oder
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
		
		dictQueryKeys = None
		dictFormKeys = None
		
		if (dictQuery):
			dictQueryKeys = dictQuery.keys()
		if (dictForm):
			dictFormKeys = dictForm.keys()
		
		print("%r::moduleExec(strPath=%s, oHtmlPage=%s, dictQuery=%s, dictForm=%s)" % (
			self, strPath, oHtmlPage, dictQueryKeys, dictFormKeys))
		
		if (not re.match("/modules/PiFaceIO\\.cmd", strPath)
			or not dictQuery):
			return False

		self.updateContext()

		if (self.m_strEventDO1 in dictQuery):
			pass
				
		return True

	# Konfigurationseinstellungen holen
	def updateContext(self):
				
		self.m_nUpdateHour = globs.getSetting("Updater", "nUpdateHour", "\\d{1,2}", 1)
		self.m_bAutoUpdate = globs.getSetting("Updater", "bAutoUpdate", "True|False", False)
		self.m_bAutoReboot = globs.getSetting("Updater", "bAutoReboot", "True|False", False)
		self.m_strSystemUrl = globs.getSetting("Updater", "strSystemUrl",
			"[Hh][Tt][Tt][Pp][Ss]+\\://.+/.+", "")
		self.m_strChkUpdUrl = globs.getSetting("Updater", "strChkUpdUrl",
			"[Hh][Tt][Tt][Pp][Ss]+\\://.+/.+", "")
			
		globs.setSetting("Updater", "fChkVersion", self.m_fChkVersion)
		return