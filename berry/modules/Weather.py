## 
#  Wetter Plug-In
#  
#  @file Weather.py
#  @brief Plug-In für die Bereitstellung von Wetterinformationen.
#
import re
import uuid

from .. import globs
from .. import sdk
from ..sdk import ModuleBase, TaskSpeak

# Try to import from module "pyowm" which might not be installed on the target system
#
try:
	from pyowm import OWM

	globs.dbg("Modul <pyowm> scheint verfügbar zu sein")
except:
	globs.exc("Modul <pyowm> scheint nicht verfügbar zu sein")
	globs.registerMissingPipPackage(
		"pyowm", "Python wrapper library for OpenWeatherMap web APIs",
		"""Das Paket wird verwendet, um aktuelle Wetterdaten von OpenWeatherMap.org zu beziehen.
		Solange das Paket nicht installiert wird, kann das Modul Weather nicht verwendet werden.""")

def createModuleInstance(
	oWorker):
	if (globs.isMissingPipPackage("pyowm")):
		return None
	return Weather(oWorker)

class Weather(ModuleBase):
	
	## 
	#  @copydoc sdk::ModuleBase::moduleInit
	#  
	def moduleInit(self, dictModCfg=None, dictCfgUsr=None):
		# Verfügbare Einstellungen mit Default-Werten festlegen
		dictSettings = {
			"strApiKey"	 	: "",
			"strLocation" 	: "",
			"strLanguage"	: "de",
			"strVersion"	: "2.5",
			"nCityID"		: 0,
			"lnkLocation" 	: "",
		}

		self.m_strSetupApiKeyToken = uuid.uuid4().hex
		self.m_strSetupSearchToken = uuid.uuid4().hex
		self.m_strSetupCityIdToken = uuid.uuid4().hex

		# Vorbelegung der Moduleigenschaften mit Default-Werten, sofern noch nicht verfügbar
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})

		# Beschreibung der Konfigurationseinstellungen
		dictCfgUsr.update({
			"strApiKey" : {
				"title"			: "OpenWeatherMap API Key",
				"description"	: ("Ein kostenloser OpenWeatherMap.org API Key wird benötigt, um die Wetterinformationen abrufen zu können."),
				"default"		: "",
			},
			"strLocation" : {
				"title"			: "Aktueller Ort",
				"description"	: ("Die Wetterinformationen werden für diesen Ort abgerufen."),
				"default"		: "",
				"readonly"		: True,
			},
			"nCityID" : {
				"title"			: "City-ID",
				"description"	: ("City-ID des Orts, für den Wetterinformationen abzurufen sind."),
				"default"		: 0,
				"readonly"		: True,
			},
			"lnkLocation" : {
				"title"			: "Ort",
				"description"	: ("Einrichten"),
				"default"		: "/modules/Weather.html",
				"showlink"		: True
			},
			"strLanguage" : {
				"title"			: "Sprache",
				"description"	: ("Angabe der Sprache, in der die Wetterinformationen bereitzustellen sind."),
				"default"		: "",
				"choices"		: {
					"Arabic" : "ar",
					"Bulgarian" : "bg",
					"Catalan" : "ca",
					"Czech" : "cz",
					"German" : "de",
					"Greek" : "el",
					"English" : "en",
					"Persian (Farsi)" : "fa",
					"Finnish" : "fi",
					"French" : "fr",
					"Galician" : "gl",
					"Croatian" : "hr",
					"Hungarian" : "hu",
					"Italian" : "it",
					"Japanese" : "ja",
					"Korean" : "kr",
					"Latvian" : "la",
					"Lithuanian" : "lt",
					"Macedonian" : "mk",
					"Dutch" : "nl",
					"Polish" : "pl",
					"Portuguese" : "pt",
					"Romanian" : "ro",
					"Russian" : "ru",
					"Swedish" : "se",
					"Slovak" : "sk",
					"Slovenian" : "sl",
					"Spanish" : "es",
					"Turkish" : "tr",
					"Ukrainian" : "ua",
					"Vietnamese" : "vi",
					"Chinese Simplified" : "zh_cn",
					"Chinese Traditional" : "zh_tw"
				}
			},
			"strVersion" : {
				"title"			: "Version",
				"description"	: ("Optionale Angabe einer Version des zu verwendenden APIs zum Abrufen der Wetterinformationen."),
				"default"		: "",
				"choices"		: {
					"Default"		: ""
				}
			},
		})

		# Auslesen der aktuellen Konfigurationseinstellungen
		self.m_strApiKey = globs.getSetting("Weather", "strApiKey", r".+", "")
		self.m_strLangID = globs.getSetting("Weather", "strLanguage", r"[a-z]{2}(_[a-z]{2})?", "de")
		self.m_strLocation = globs.getSetting("Weather", "strLocation", r".+", "")
		self.m_strVersion = globs.getSetting("Weather", "strVersion", r"[0-9]+\.[0-9]+", "2.5")
		self.m_nCityID = globs.getSetting("Weather", "nCityID", "[0-9]+", 0)

		self.m_oWeatherApi = None
		self.m_oObservation = None

		self.createWeatherApiObjects()

		return True

	def createWeatherApiObjects(self):
		if (self.m_strApiKey and not self.m_oWeatherApi):
			self.m_oWeatherApi = OWM(
				API_key=self.m_strApiKey,
				language=self.m_strLangID,
				version=self.m_strVersion)
		if (self.m_oWeatherApi and not self.m_oObservation and self.m_nCityID):
			self.m_oObservation = self.m_oWeatherApi.weather_at_id(self.m_nCityID)
		return
	
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
		
		if (re.match(r"/modules/Weather\.html", strPath)
			and not oHtmlPage == None):
			return self.serveHtmlPage(oHtmlPage, dictQuery, dictForm)
			
		if not dictQuery:
			return False

		bResult = False	

		# Unbekanntes Kommando
		return bResult
	
	## 
	#  @brief Bereitstellung der HTML-Seite für eine manuelle Aktualisierung.
	#  
	#  @param [in] self Verweis auf die eigene Instanz
	#  @param [in] oHtmlPage Verweis auf die Instanz der HTML-Seite
	#  @param [in] dictQuery Query-Daten
	#  @param [in] dictForm Formulardaten
	#  @return Liefert @c True wenn die HTML-Seite bereitgestellt werden konnte oder @c False
	#  im Fehlerfall.
	#  
	#  @details Details
	#  
	def serveHtmlPage(self,
		oHtmlPage,
		dictQuery,
		dictForm):
		
		globs.log("Weather::serveHtmlPage()")

		try:
			# Formulardaten verarbeiten
			if (dictForm and "token" in dictForm):
				
				# Formular für API-Key gespeichert
				if (self.m_strSetupApiKeyToken in dictForm["token"]
					and "OwmApiKey" in dictForm
					and dictForm["OwmApiKey"][0]):
					self.m_strSetupApiKeyToken = uuid.uuid4().hex
					globs.setSetting("Weather", "strApiKey", dictForm["OwmApiKey"][0])
					self.m_strApiKey = globs.getSetting("Weather", "strApiKey", r".+", "")
					if (self.m_oWeatherApi):
						self.m_oWeatherApi.set_API_key(self.m_strApiKey)
					if (self.m_oWeatherApi and self.m_oObservation):
						oHtmlPage.createBox(
							"API-Key hinterlegen",
							"""Der registrierte API-Key wurde erfolgreich geändert.""",
							strType="success", bClose=False)
						oHtmlPage.createButton(
							"OK",
							strHRef="/system/settings.html")
						oHtmlPage.closeBox()
						return True
									
				# Formular für die Eingrenzung der Ortsnamen gespeichert
				elif (self.m_strSetupSearchToken in dictForm["token"]
					and "Location" in dictForm
					and dictForm["Location"][0]):
					self.m_strSetupSearchToken = uuid.uuid4().hex
					globs.setSetting("Weather", "strLocation", dictForm["Location"][0])
					self.m_strLocation = globs.getSetting("Weather", "strLocation", r".+", "")
				
				# Formular für die City-ID gespeichert
				elif (self.m_strSetupCityIdToken in dictForm["token"]
					and "CityID" in dictForm
					and dictForm["CityID"][0]):
					self.m_strSetupCityIdToken = uuid.uuid4().hex
					globs.setSetting("Weather", "nCityID", int(dictForm["CityID"][0]))
					self.m_nCityID = globs.getSetting("Weather", "nCityID", "[0-9]+", 0)
					self.m_oObservation = None
					self.createWeatherApiObjects()
					if (self.m_oObservation):
						oLocation = self.m_oObservation.get_location()
						self.m_strLocation = oLocation.get_name()
						oHtmlPage.createBox(
							"Wettervorhersage für einen Ort",
							"""Die Wettervorhersage wurde erfolgreich für den Ort %s eingerichtet.""" % (self.m_strLocation),
							strType="success", bClose=False)
						oHtmlPage.createButton(
							"OK",
							strHRef="/system/settings.html")
						oHtmlPage.closeBox()
						return True
		except:
			globs.exc("Weather: Formulardaten verarbeiten")

		# Weather-API Objekte anlegen
		self.createWeatherApiObjects()

		try:
			# Formular für die Registrierung eines API-Key aufbauen
			if (not self.m_strApiKey
				or (dictQuery and "token" in dictQuery
					and self.m_strSetupApiKeyToken in dictQuery["token"])):
				self.m_strSetupApiKeyToken = uuid.uuid4().hex
				oHtmlPage.createBox(
					"API-Key hinterlegen",
					("""Damit die Wettervorhersage verwendet werden kann, muss ein gültiger,
					von OpenWeatherMap.org bezogener API-Key hinterlegt werden."""
					if not self.m_strApiKey else
					"""Der bereits hinterlegte API-Key kann jederzeit durch einen anderen,
					gültigen und von OpenWeatherMap.org bezogenen API-Key ersetzt werden."""),
					strType="info", bClose=False)
				oHtmlPage.openForm(
					dictTargets={"token" : self.m_strSetupApiKeyToken})
				oHtmlPage.appendForm("OwmApiKey",
					strTitle="API-Key",
					strTip="API-Key für OpenWeatherMap.org",
					strInput=self.m_strApiKey,
					strTextType="text")
				oHtmlPage.closeForm(strUrlCancel="/system/settings.html")
				oHtmlPage.closeBox()
				return True

			# Formular für die Eingrenzung möglicher Orte aufbauen
			if (not self.m_strLocation
				or (dictQuery and "token" in dictQuery
					and self.m_strSetupSearchToken in dictQuery["token"])):
				self.m_strSetupSearchToken = uuid.uuid4().hex
				oHtmlPage.createBox(
					"Wettervorhersage für einen Ort",
					("""Es wurde noch kein Ort für die Wettervorhersage festgelegt.
					Da die Wettervorhersage nur für bestimmte Orte zur Verfügung steht,
					sollte hier nach der Bezeichnung einer größeren Ortschaft oder Stadt
					in der näheren Umgebung gesucht werden."""
					if not self.m_strLocation or self.m_nCityID == 0 else
					"""Die Wettervorhersage kann jederzeit für einen anderen Ort vorgenommen werden."""),
					strType="info", bClose=False)
				oHtmlPage.openForm(
					dictTargets={"token" : self.m_strSetupSearchToken})
				oHtmlPage.appendForm("Location",
					strTitle="Ortsname",
					strTip="Wettervorhersage für einen Ort",
					strInput=globs.getSetting("Weather", "strLocation", r".*", ""),
					strTextType="text")
				oHtmlPage.closeForm(strUrlCancel="/system/settings.html")
				oHtmlPage.closeBox()
				return True

			# Formular für die Auswahl einer bestimmten City-ID aufbauen
			if (self.m_strLocation and self.m_oWeatherApi):
				self.m_strSetupCityIdToken = uuid.uuid4().hex
				oReg = self.m_oWeatherApi.city_id_registry()
				lstCityIDs = oReg.ids_for(self.m_strLocation)        # [ (123, 'London', 'GB'), (456, 'London', 'MA'), (789, 'London', 'WY')]
				# Keine Ergebnisse
				if (len(lstCityIDs) == 0):
					oHtmlPage.createBox(
						"Wettervorhersage für einen Ort",
						"""Für den Ort %s steht keine Wettervorhersage zur Verfügung.
						Vielleicht ist für eine andere größere Ortschaft oder Stadt
						in der näheren Umgebung eine Wettervorhersage verfügbar.""" % (self.m_strLocation),
						strType="info", bClose=False)
					oHtmlPage.createButton(
						"Weiter",
						strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupSearchToken))
					oHtmlPage.createButton(
						"Abbrechen",
						strHRef="/system/settings.html")
					oHtmlPage.closeBox()
					self.m_strLocation = ""
					return True
				# Eindeutiges Ergebnis
				if (len(lstCityIDs) == 1):
					self.m_nCityID = lstCityIDs[0][0]
					self.m_strLocation = "%s, %s" % (lstCityIDs[0][1], lstCityIDs[0][2])
					oHtmlPage.createBox(
						"Wettervorhersage für einen Ort",
						"""Die Wettervorhersage wurde erfolgreich für den Ort %s eingerichtet.""" % (self.m_strLocation),
						strType="success", bClose=False)
					oHtmlPage.createButton(
						"OK",
						strHRef="/system/settings.html")
					oHtmlPage.closeBox()
					self.createWeatherApiObjects()
					return True
				# Mehrdeutige Ergebnisse
				dictCityIDs = {}
				for oLocationTuple in lstCityIDs:
					dictCityIDs.update(
						{"%s, %s (%s)" % (
							oLocationTuple[0][1],
							oLocationTuple[0][2],
							oLocationTuple[0][0]) : oLocationTuple[0][0]})
				oHtmlPage.createBox(
					"Wettervorhersage für einen Ort",
					"""Die Suche nach dem Ort %s hat mehrere Möglichkeiten ergeben.""" % (self.m_strLocation),
					strType="info", bClose=False)
				oHtmlPage.openForm(
					dictTargets={"token" : self.m_strSetupCityIdToken})
				oHtmlPage.appendForm("CityId",
					strTitle="Ortsname",
					strTip="Wettervorhersage für einen Ort",
					strInput="%s" % (self.m_nCityID),
					strTextType="text")
				oHtmlPage.closeForm(strUrlCancel="/system/settings.html")
				oHtmlPage.closeBox()
				return True
		except:
			globs.exc("Weather: Formulare aufbauen")
		


		# Default, Startseite für Einrichtung der Wettervorhersage
		oHtmlPage.createBox(
			"Wettervorhersage einrichten",
			"""Die Wettervorhersage kann in wenigen Schritten eingerichtet werden.
			Für die Einrichtung ist eine Internet-Verbindung erforderlich.""",
			strType="info", bClose=False)
		# App-Key anfordern bzw. hinterlegen
		if (not globs.getSetting("Weather", "strApiKey", r".+", "")):
			self.m_strSetupApiKeyToken = uuid.uuid4().hex
			oHtmlPage.createText(
				"""Derzeit ist noch kein API-Key eingestellt. Ein kostenloser API-Key
				kann bei OpenWeatherMap.org bezogen werden.""")
			oHtmlPage.createButton(
				"Neuen API-Key anfordern (ext)",
				strHRef="https://openweathermap.org/price",
				bExternal=True)
			oHtmlPage.createButton(
				"Vorhandenen API-Key verwenden",
				strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupApiKeyToken))
			oHtmlPage.createButton(
				"Abbrechen",
				strHRef="/system/settings.html")
			oHtmlPage.closeBox()
			return True
		# City-ID einstellen
		if (globs.getSetting("Weather", "nCityID", r".+", 0) == 0):
			self.m_strSetupCityIdToken = uuid.uuid4().hex
			oHtmlPage.createText(
				"""Derzeit ist noch kein Ort für die Wettervorhersage eingerichtet.""")
			oHtmlPage.openForm(
				dictQueries={"token" : self.m_strSetupCityIdToken})
			oHtmlPage.appendForm("Location",
				strTitle="Ortsname",
				strTip="Bezeichnung einer größeren Ortschaft oder Stadt in der näheren Umgebung",
				strInput=globs.getSetting("Weather", "strLocation", r".*", ""),
				strTextType="text")
			oHtmlPage.closeForm(strUrlCancel="/system/settings.html")
			oHtmlPage.closeBox()
			return True
		# Verschiedene Einstellungen vornehmen
		self.m_strSetupApiKeyToken = uuid.uuid4().hex
		self.m_strSetupCityIdToken = uuid.uuid4().hex
		oHtmlPage.createText(
			"Das Wetter wird derzeit für %s vorhergesagt." % (
				globs.getSetting("Weather", "strLocation", r".*", "einen namenlosen Ort")
			))
		oHtmlPage.createButton(
			"Neuen API-Key anfordern (ext)",
			strHRef="https://openweathermap.org/price",
			bExternal=True)
		oHtmlPage.createButton(
			"Anderen API-Key hinterlegen",
			strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupApiKeyToken))
		oHtmlPage.createButton(
			"Ort ändern",
			strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupCityIdToken))
		oHtmlPage.createButton(
			"Abbrechen",
			strHRef="/system/settings.html")		
		oHtmlPage.closeBox()
		return True
