## 
#  Wetter Plug-In
#  
#  @file Weather.py
#  @brief Plug-In für die Bereitstellung von Wetterinformationen.
#
import re
import uuid
import time
from datetime import datetime
from datetime import timedelta

from collections import OrderedDict

from .. import globs
from .. import sdk
from ..sdk import ModuleBase, TaskSpeak, TaskDelegateLong, TaskModuleEvt

# Try to import from module "pyowm" which might not be installed on the target system
#
g_bPackageMissing = True
try:
	from pyowm import OWM

	globs.dbg("Modul <pyowm> scheint verfügbar zu sein")
	g_bPackageMissing = False
except:
	globs.exc("Modul <pyowm> scheint nicht verfügbar zu sein")

globs.registerPipPackage(
	g_bPackageMissing, "pyowm", "Python wrapper library for OpenWeatherMap web APIs",
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
			"lnkLocation" 		: "",
			"strLocation" 		: "",
			"nCityID"			: 0,
			"strLanguage"		: "de",
			"strVersion"		: "2.5",
			"strApiKey"			: "",
			
			"strReferenceTime"	: "",
			"strRequestedTime"	: "",
			"fTemperature"		: 0.0,
			"fTemperatureMin"	: 0.0,
			"fTemperatureMax"	: 0.0,
			"strRainVolume"		: "",
			"strSnowVolume"		: "",
			"nWindDirection"	: 0,
			"fWindSpeed"		: 0.0,
			"fPressure"			: 0.0,
			"fPressureSeaLevel"	: 0.0,
			"nCloudCoverage"	: 0,
			"nHumidity"			: 0,
			"nWeatherCode"		: 0,
			"strStatus"			: "",
			"strStatusDetailed"	: "",
			"strTimeSunrise"	: "",
			"strTimeSunset"		: "",
			"strWeatherIconUrl"	: "",
		}

		self.m_strSetupApiKeyToken = uuid.uuid4().hex
		self.m_strSetupSearchToken = uuid.uuid4().hex
		self.m_strSetupCityIdToken = uuid.uuid4().hex

		# Vorbelegung der Moduleigenschaften mit Default-Werten, sofern noch nicht verfügbar
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			# Zurücklesen der gespeicherten Konfiguration in eigene OrderedDict
			dictSettings.update(dictModCfg)
			# Zurücksetzen des gespeicherten OrderedDict
			dictModCfg.clear()
			# Gespeichertes OrderedDict entsprechend der Sortierungsreihenfolge initialisieren
			dictModCfg.update(dictSettings)
			# for (strName, strValue) in dictSettings.items():
			# 	if strName not in dictModCfg:
			# 		dictModCfg.update({strName : strValue})

		# Beschreibung der Konfigurationseinstellungen
		dictCfgUsr.update({
			"properties" : [
				"lnkLocation",
				"strLocation",
				"nCityID", 
				"strLanguage",
				"strVersion",	
				"strApiKey",

				"strReferenceTime",
				"strRequestedTime",
				"fTemperature",
				"fTemperatureMin",
				"fTemperatureMax",
				"strRainVolume",
				"strSnowVolume",
				"nWindDirection",
				"fWindSpeed",
				"fPressure",
				"fPressureSeaLevel",
				"nCloudCoverage",
				"nHumidity",
				"nWeatherCode",
				"strStatus",
				"strStatusDetailed",
				"strTimeSunrise",
				"strTimeSunset",
				"strWeatherIconUrl",
			],
			"strReferenceTime" : {
				"title"			: "Zeitstempel Wetterdaten",
				"default"		: "",
				"readonly"		: True,
			},
			"strRequestedTime" : {
				"title"			: "Letzte Aktualisierung",
				"default"		: "",
				"readonly"		: True,
			},
			"fTemperature" : {
				"title"			: "Aktuelle Temperatur",
				"default"		: "",
				"readonly"		: True,
			},
			"fTemperatureMin" : {
				"title"			: "Minimal-Temperatur",
				"default"		: "",
				"readonly"		: True,
			},
			"fTemperatureMax" : {
				"title"			: "Maximal-Temperatur",
				"default"		: "",
				"readonly"		: True,
			},
			"strRainVolume" : {
				"title"			: "Regen-Volumen",
				"default"		: "",
				"readonly"		: True,
			},
			"strSnowVolume" : {
				"title"			: "Schnee-Volumen",
				"default"		: "",
				"readonly"		: True,
			},
			"nWindDirection" : {
				"title"			: "Windrichtung",
				"default"		: "",
				"readonly"		: True,
			},
			"fWindSpeed" : {
				"title"			: "Windgeschwindigkeit",
				"default"		: "",
				"readonly"		: True,
			},
			"fPressure" : {
				"title"			: "Luftdruck",
				"default"		: "",
				"readonly"		: True,
			},
			"fPressureSeaLevel" : {
				"title"			: "Luftdruck auf Meereshöhe",
				"default"		: "",
				"readonly"		: True,
			},
			"nCloudCoverage" : {
				"title"			: "Bewölkungsgrad",
				"default"		: "",
				"readonly"		: True,
			},
			"nHumidity" : {
				"title"			: "Luftfeuchtigkeit",
				"default"		: "",
				"readonly"		: True,
			},
			"nWeatherCode" : {
				"title"			: "Wetterkennung",
				"default"		: "",
				"readonly"		: True,
			},
			"strStatus" : {
				"title"			: "Wetterstatus",
				"default"		: "",
				"readonly"		: True,
			},
			"strStatusDetailed" : {
				"title"			: "Detailierter Wetterstatus",
				"default"		: "",
				"readonly"		: True,
			},
			"strTimeSunrise" : {
				"title"			: "Sonnenaufgang",
				"default"		: "",
				"readonly"		: True,
			},
			"strTimeSunset" : {
				"title"			: "Sonnenuntergang",
				"default"		: "",
				"readonly"		: True,
			},
			"strWeatherIconUrl" : {
				"title"			: "URL für Wettersymbol",
				"default"		: "",
				"readonly"		: True,
			},

			"strApiKey" : {
				"title"			: "OpenWeatherMap API Key",
				"description"	: ("Ein kostenloser OpenWeatherMap.org API Key wird benötigt, um die Wetterinformationen abrufen zu können."),
				"default"		: "",
				"readonly"		: True,
			},
			"strLocation" : {
				"title"			: "Ort",
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
				"title"			: "Wettervorhersage",
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
				"default"		: "2.5",
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
		self.m_oWeather = None
		self.createWeatherApiObjects()

		self.m_lstCityIDs = []
		self.m_oTaskFindCityIDsForLocation = None

		self.m_nLastTemperature = None
		self.m_nLastWeatherCondition = None

		return True

	def createWeatherApiObjects(self, bRenew=False):
		if bRenew:
			self.m_oObservation = None
			self.m_oWeather = None
			self.m_oWeatherApi = None

		if (self.m_strApiKey and (not self.m_oWeatherApi)):
			self.m_oObservation = None
			self.m_oWeather = None
			self.m_oWeatherApi = OWM(
				API_key=self.m_strApiKey,
				language=self.m_strLangID,
				version=self.m_strVersion)

		if (self.m_oWeatherApi and self.m_nCityID and (not self.m_oObservation)):
			self.m_oWeather = None
			self.m_oObservation = self.m_oWeatherApi.weather_at_id(self.m_nCityID)

		if (self.m_oObservation and not self.m_oWeather):
			self.m_oWeather = self.m_oObservation.get_weather()
		
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
			and (not oHtmlPage == None)):
			return self.serveHtmlPage(oHtmlPage, dictQuery, dictForm)
			
		if (not dictQuery):
			return False

		for (strCmd, lstArg) in dictQuery.items():
			# Moduleinstellungen wurden geändert
			if (strCmd == "settings" and lstArg	and "Weather" in lstArg):
				for (strCmd, _) in dictForm.items():
					if (strCmd in ["strLanguage", "strVersion"]):
						self.createWeatherApiObjects(bRenew=True)
						continue
				continue
			# Systemeinstellungen wurden geändert
			if (strCmd == "system"):
				if ("date" in lstArg or "time" in lstArg):
					self.checkWeather()
					continue
				continue
			# Timer-Ereignisse
			if (strCmd == "timer"):
				if ("cron" in lstArg):
					self.checkWeather()
					continue
				continue

		bResult = False	

		# Unbekanntes Kommando
		return bResult
	
	def checkWeather(self):
		try:
			strRequestedTime = globs.getSetting("Weather", "strRequestedTime", ".+", "")
			bRenew = (((int(time.strftime("%M")) % 15) != 0)
				or (not strRequestedTime))
			
			self.createWeatherApiObjects(bRenew=bRenew)

			if (not self.m_oWeather):
				return

			strRequestedTime = time.strftime("%Y-%m-%d %H:%M:%S")
			strReferenceTime = self.m_oWeather.get_reference_time(timeformat='iso')[:-3]
			
			dictData = self.m_oWeather.get_temperature(unit="celsius")
			globs.dbg("Temperature information %r" % (dictData))
			fTemperature = 		float(dictData["temp"]) 		if "temp" 		in dictData and dictData["temp"] else -999.9
			fTemperatureMin = 	float(dictData["temp_min"])		if "temp_min" 	in dictData and dictData["temp_min"] else -999.9
			fTemperatureMax = 	float(dictData["temp_max"])		if "temp_max" 	in dictData and dictData["temp_max"] else -999.9

			dictData = self.m_oWeather.get_wind()
			globs.dbg("Wind information %r" % (dictData))
			nWindDirection = 	int(dictData["deg"]) 			if "deg" 		in dictData and dictData["deg"] else -999
			fWindSpeed = 		float(dictData["speed"])		if "speed" 		in dictData and dictData["speed"] else -999.9

			dictData = self.m_oWeather.get_pressure()
			globs.dbg("Atmospharic pressure information %r" % (dictData))
			fPressure =			float(dictData["press"]) 		if "press" 		in dictData and dictData["press"] else -999.9
			fPressureSeaLevel = float(dictData["sea_level"])	if "sea_level" 	in dictData and dictData["sea_level"] else -999.9

			dictData = self.m_oWeather.get_rain()
			globs.dbg("Rain volume information %r" % (dictData))
			strRainVolume = ""
			for (strTime, nVolume) in dictData.items():
				strRainVolume += ", " if strRainVolume else ""
				strRainVolume += "%s: %s" % (strTime, nVolume)

			dictData = self.m_oWeather.get_snow()
			globs.dbg("Snow volume information %r" % (dictData))
			strSnowVolume = ""
			for (strTime, nVolume) in dictData.items():
				strSnowVolume += ", " if strSnowVolume else ""
				strSnowVolume += "%s: %s" % (strTime, nVolume)

			nCloudCoverage = 	self.m_oWeather.get_clouds()
			nHumidity = 		self.m_oWeather.get_humidity()
			nWeatherCode = 		self.m_oWeather.get_weather_code()
			strStatus = 		self.m_oWeather.get_status()
			strStatusDetailed = self.m_oWeather.get_detailed_status()
			
			strSunriseTime = 	self.m_oWeather.get_sunrise_time("iso")[:-3]
			strSunsetTime = 	self.m_oWeather.get_sunset_time("iso")[:-3]
			strWeatherIconUrl = self.m_oWeather.get_weather_icon_url()

			globs.setSetting("Weather", "strRequestedTime", 	strRequestedTime)
			globs.setSetting("Weather", "strReferenceTime", 	strReferenceTime)
			globs.setSetting("Weather", "fTemperature", 		fTemperature)
			globs.setSetting("Weather", "fTemperatureMin", 		fTemperatureMin)
			globs.setSetting("Weather", "fTemperatureMax", 		fTemperatureMax)
			globs.setSetting("Weather", "strRainVolume", 		strRainVolume)
			globs.setSetting("Weather", "strSnowVolume", 		strSnowVolume)
			globs.setSetting("Weather", "nWindDirection", 		nWindDirection)
			globs.setSetting("Weather", "fWindSpeed",	 		fWindSpeed)
			globs.setSetting("Weather", "fPressure",	 		fPressure)
			globs.setSetting("Weather", "fPressureSeaLevel",	fPressureSeaLevel)
			globs.setSetting("Weather", "nCloudCoverage", 		nCloudCoverage)
			globs.setSetting("Weather", "nHumidity", 			nHumidity)
			globs.setSetting("Weather", "nWeatherCode", 		nWeatherCode)
			globs.setSetting("Weather", "strStatus", 			strStatus)
			globs.setSetting("Weather", "strStatusDetailed", 	strStatusDetailed)
			globs.setSetting("Weather", "strTimeSunrise", 		strSunriseTime)
			globs.setSetting("Weather", "strTimeSunset", 		strSunsetTime)
			globs.setSetting("Weather", "strWeatherIconUrl", 	strWeatherIconUrl)
			globs.setSetting("System", "strTimeSunrise", 		sdk.translateStrToLocalTimeStr(strSunriseTime, "%Y-%m-%d %H:%M:%S"))
			globs.setSetting("System", "strTimeSunset",			sdk.translateStrToLocalTimeStr(strSunsetTime, "%Y-%m-%d %H:%M:%S"))

			nTemperature = round(fTemperature)
			nWeatherCondition = self.normalizeWeatherCondition(nWeatherCode)

			if (not self.m_nLastWeatherCondition
				or not self.m_nLastTemperature
				or self.m_nLastWeatherCondition != nWeatherCondition
				or self.m_nLastTemperature != nTemperature):
				TaskModuleEvt(self.m_oWorker, "/int/evt.src",
					dictQuery={
						"temperature"	: ["%s" % (nTemperature)],
						"weather" 		: ["%s" % (nWeatherCondition)]
					}
				).start()

				strWeatherReport = "Das aktuelle Wetter: %s bei einer Temperatur von %d Grad Celsius" % (
					strStatusDetailed, nTemperature)
				TaskSpeak(self.m_oWorker, strWeatherReport).start()
			
			self.m_nLastTemperature = nTemperature
			self.m_nLastWeatherCondition = nWeatherCondition

		except:
			globs.exc("Abrufen von Wetterdaten")		
		return

	##
	# "sunny",					# 01 - sonnig				(sunny)
	# "cheerful",				# 02 - heiter				(cheerful)
	# "cloudy",					# 03 - bewölkt				(cloudy)
	# "covered",				# 04 - bedeckt				(covered)
	# "rainy",					# 05 - regnerisch			(rainy)
	# "changeable",				# 06 - wechselhaft			(changeable)
	# "thunderstorm",			# 07 - gewittrig			(thunderstorm)
	# "snowy",					# 08 - schneeig				(snowy)
	# "foggy",					# 09 - neblig				(foggy)
	#
	def normalizeWeatherCondition(self,
		nWeatherCode):

		if (nWeatherCode >= 200 and nWeatherCode < 300):
			# Thunderstorm -> thunderstorm
			return 7
		if (nWeatherCode >= 300 and nWeatherCode < 400):
			# Drizzle -> changeable
			return 6
		if (nWeatherCode >= 500 and nWeatherCode < 600):
			# Rain -> rainy
			return 5
		if (nWeatherCode >= 600 and nWeatherCode < 700):
			# Snow -> snowy
			return 8
		if (nWeatherCode >= 700 and nWeatherCode < 800):
			# Atmosphere -> foggy
			return 9
		if (nWeatherCode == 800):
			# Clear
			return 1
		if (nWeatherCode == 801):
			# Few clouds (11-25%) -> cheerful
			return 2
		if (nWeatherCode >= 802 and nWeatherCode <= 803):
			# Scattered clouds (25-50%) -> cloudy
			# Broken clouds (51-84%) -> cloudy
			return 3
		if (nWeatherCode == 804):
			# Overcast clouds (85-100%) -> covered
			return 4

		# Default
		return 1

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
		strLocation = ""

		globs.log("Weather::serveHtmlPage()")

		try:
			# Formulardaten verarbeiten
			if (dictForm and "token" in dictForm):
				
				# Formular für API-Key gespeichert
				if (self.m_strSetupApiKeyToken in dictForm["token"]
					and "OwmApiKey" in dictForm
					and dictForm["OwmApiKey"][0]):
					self.m_strSetupApiKeyToken = uuid.uuid4().hex
					
					self.m_strApiKey = dictForm["OwmApiKey"][0]
					globs.setSetting("Weather", "strApiKey", self.m_strApiKey)
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
							strClass="ym-save ym-success",
							strHRef="/modules/Weather.html")
						oHtmlPage.closeBox()
						return True
									
				# Formular für die Eingrenzung der Ortsnamen gespeichert
				elif (self.m_strSetupSearchToken in dictForm["token"]
					and "Location" in dictForm
					and dictForm["Location"][0]):
					self.m_strSetupSearchToken = uuid.uuid4().hex
					strLocation = dictForm["Location"][0]
					# self.m_strLocation = dictForm["Location"][0]
					# globs.setSetting("Weather", "strLocation", self.m_strLocation)
					# self.m_strLocation = globs.getSetting("Weather", "strLocation", r".+", "")
				
				# Formular für die City-ID gespeichert
				elif (self.m_strSetupCityIdToken in dictForm["token"]
					and "CityID" in dictForm
					and "Location" in dictForm
					and dictForm["CityID"][0]
					and dictForm["Location"][0]):
					self.m_strSetupCityIdToken = uuid.uuid4().hex
					
					self.m_nCityID = int(dictForm["CityID"][0])
					globs.setSetting("Weather", "nCityID", self.m_nCityID)
					self.m_nCityID = globs.getSetting("Weather", "nCityID", "[0-9]+", 0)
					
					self.m_oObservation = None
					self.createWeatherApiObjects()

					if (self.m_oObservation):
						self.m_strLocation = self.m_oObservation.get_location().get_name()
						globs.setSetting("Weather", "strLocation", self.m_strLocation)
						self.m_strLocation = globs.getSetting("Weather", "strLocation", r".+", "")

						oHtmlPage.createBox(
							"Wettervorhersage für einen Ort",
							"""Die Wettervorhersage wurde erfolgreich für den Ort %s eingerichtet.""" % (
								self.m_strLocation),
							strType="success", bClose=False)
						oHtmlPage.createButton(
							"OK",
							strClass="ym-save ym-success",
							strHRef="/modules/Weather.html")
						oHtmlPage.closeBox()
						return True
		except:
			globs.exc("Weather: Formulardaten verarbeiten")

		# Weather-API Objekte anlegen
		self.createWeatherApiObjects()

		try:
			if (dictQuery
				and "Location" in dictQuery
				and dictQuery["Location"][0]):
				strLocation = dictQuery["Location"][0]

			# Formular für die Registrierung eines API-Key aufbauen
			if ((dictQuery and "token" in dictQuery
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
				oHtmlPage.closeForm(strUrlCancel="/modules/Weather.html")
				oHtmlPage.closeBox()
				return True

			# Formular für die Eingrenzung möglicher Orte aufbauen
			if ((dictQuery and "token" in dictQuery
				and self.m_strSetupSearchToken in dictQuery["token"])):
				self.m_strSetupSearchToken = uuid.uuid4().hex
				oHtmlPage.createBox(
					"Wettervorhersage für einen Ort",
					("""Es wurde noch kein Ort für die Wettervorhersage festgelegt.
					Da die Wettervorhersage nur für bestimmte Orte zur Verfügung steht,
					sollte hier nach der Bezeichnung einer größeren Ortschaft oder Stadt
					in der näheren Umgebung gesucht werden."""
					if (not self.m_strLocation) or self.m_nCityID == 0 else
					"""Die Wettervorhersage kann jederzeit für einen anderen Ort vorgenommen werden."""),
					strType="info", bClose=False)
				oHtmlPage.openForm(
					dictTargets={"token" : self.m_strSetupSearchToken})
				oHtmlPage.appendForm("Location",
					strTitle="Ortsname",
					strTip="Wettervorhersage für einen Ort",
					strInput=globs.getSetting("Weather", "strLocation", r".*", ""),
					strTextType="text")
				oHtmlPage.closeForm(strUrlCancel="/modules/Weather.html")
				oHtmlPage.closeBox()
				return True

			# Formular für die Auswahl einer bestimmten City-ID aufbauen
			if (strLocation and self.m_oWeatherApi):
				self.m_strSetupCityIdToken = uuid.uuid4().hex
				self.m_strSetupSearchToken = uuid.uuid4().hex
				
				if (not self.m_oTaskFindCityIDsForLocation):
					self.m_oTaskFindCityIDsForLocation = TaskDelegateLong(self.m_oWorker,
						self.delegateFindCityIDsForLocation, 
						strLocation=strLocation)
					self.m_oTaskFindCityIDsForLocation.start()
				if (self.m_oTaskFindCityIDsForLocation):
					if (self.m_oTaskFindCityIDsForLocation.wait(0.0)):
						self.m_oTaskFindCityIDsForLocation = None
					else:
						oHtmlPage.createBox(
							"Wettervorhersage für einen Ort",
							"""Die Wettervorhersage wird für den Ort %s geprüft.
							Das kann einen Moment dauern. Bitte warten...""" % (
								strLocation),
							strType="info", bClose=False)
						oHtmlPage.createButton(
							"Abbrechen",
							strClass="ym-close",
							strHRef="/modules/Weather.html")
						oHtmlPage.closeBox()
						oHtmlPage.setAutoRefresh(nAutoRefresh=1, strUrl="/modules/Weather.html?Location=%s" % (
							strLocation))
						return True

				# oReg = self.m_oWeatherApi.city_id_registry()
				# lstCityIDs = oReg.ids_for(strLocation, matching="like")        # [ (123, 'London', 'GB'), (456, 'London', 'MA'), (789, 'London', 'WY')]

				# Mehrdeutige Ergebnisse
				if (len(self.m_lstCityIDs) > 1):
					dictCityIDs = {}
					for oLocationTuple in self.m_lstCityIDs:
						dictCityIDs.update(
							{"%s, %s (%s)" % (
								oLocationTuple[1],
								oLocationTuple[2],
								oLocationTuple[0]) : oLocationTuple[0]})
					oHtmlPage.createBox(
						"Wettervorhersage für einen Ort",
						"""Die Suche nach dem Ort %s hat mehrere Möglichkeiten ergeben.""" % (
							strLocation),
						strType="info", bClose=False)
					oHtmlPage.openForm(
						dictTargets={
							"token" : self.m_strSetupCityIdToken,
							"Location" : strLocation
						})
					oHtmlPage.appendForm("CityID",
						strTitle="Ortsname",
						strTip="Wettervorhersage für einen Ort",
						strInput="%s" % (self.m_nCityID),
						dictChoice=dictCityIDs)
					oHtmlPage.closeForm(strUrlCancel="/modules/Weather.html")
					oHtmlPage.closeBox()
					return True

				# Eindeutiges Ergebnis
				if (len(self.m_lstCityIDs) == 1):
					
					self.m_nCityID = int(self.m_lstCityIDs[0][0])
					globs.setSetting("Weather", "nCityID", self.m_nCityID)
					self.m_nCityID = globs.getSetting("Weather", "nCityID", "[0-9]+", 0)
					
					self.m_oObservation = None
					self.createWeatherApiObjects()
					
					if (self.m_oObservation):
						self.m_strLocation = self.m_oObservation.get_location().get_name()
						globs.setSetting("Weather", "strLocation", self.m_strLocation)
						self.m_strLocation = globs.getSetting("Weather", "strLocation", r".+", "")

						oHtmlPage.createBox(
							"Wettervorhersage für einen Ort",
							"""Die Wettervorhersage wurde erfolgreich für den Ort %s eingerichtet.""" % (
								self.m_strLocation),
							strType="success", bClose=False)
						oHtmlPage.createButton(
							"OK",
							strClass="ym-save ym-success",
							strHRef="/modules/Weather.html")
						oHtmlPage.closeBox()
						return True
				
				# Keine Ergebnisse (oder Fehler beim Anlegen des Observation-Objekts)
				oHtmlPage.createBox(
					"Wettervorhersage für einen Ort",
					"""Für den Ort %s steht keine Wettervorhersage zur Verfügung.
					Vielleicht ist für eine andere größere Ortschaft oder Stadt
					in der näheren Umgebung eine Wettervorhersage verfügbar.""" % (
						strLocation),
					strType="info", bClose=False)
				oHtmlPage.createButton(
					"Weiter",
					strClass="ym-next ym-success",
					strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupSearchToken))
				oHtmlPage.createButton(
					"Abbrechen",
					strClass="ym-close",
					strHRef="/modules/Weather.html")
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
				"API-Key anfordern (ext)",
				strClass="ym-reply ym-primary",
				strHRef="https://openweathermap.org/price",
				bExternal=True)
			oHtmlPage.createButton(
				"API-Key hinterlegen",
				strClass="ym-edit",
				strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupApiKeyToken))
			oHtmlPage.createButton(
				"Abbrechen",
				strClass="ym-close",
				strHRef="/system/settings.html")
			oHtmlPage.closeBox()
			return True
		# City-ID einstellen
		if ((not self.m_strLocation)
			or (not self.m_oObservation)):
			self.m_strSetupSearchToken = uuid.uuid4().hex
			oHtmlPage.createText(
				"""Derzeit ist noch kein Ort für die Wettervorhersage eingerichtet.""")
			oHtmlPage.openForm(
				dictTargets={"token" : self.m_strSetupSearchToken})
			oHtmlPage.appendForm("Location",
				strTitle="Ortsname",
				strTip="Bezeichnung einer größeren Ortschaft oder Stadt in der näheren Umgebung",
				strInput=globs.getSetting("Weather", "strLocation", r".*", ""),
				strTextType="text")
			oHtmlPage.closeForm(strUrlCancel="/system/settings.html")
			oHtmlPage.closeBox()
			return True
		# Verschiedene Einstellungen vornehmen
		self.checkWeather()
		self.m_strSetupApiKeyToken = uuid.uuid4().hex
		self.m_strSetupSearchToken = uuid.uuid4().hex
		oHtmlPage.createText(
			"Das Wetter wird derzeit für %s vorhergesagt." % (
				globs.getSetting("Weather", "strLocation", r".*", "einen namenlosen Ort")
			))
		oHtmlPage.createButton(
			"Ort ändern",
			strClass="ym-edit",
			strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupSearchToken))
		oHtmlPage.createButton(
			"Schließen",
			strClass="ym-close",
			strHRef="/system/settings.html")
		oHtmlPage.createText("")
		oHtmlPage.createText(
			"""Zusätzlich kann auch der für OpenWeatherMap.org zu verwendende API-Key
			verwaltet werden.""")
		oHtmlPage.createButton(
			"API-Key anfordern (ext)",
			strClass="ym-reply ym-primary",
			strHRef="https://openweathermap.org/price",
			bExternal=True)
		oHtmlPage.createButton(
			"API-Key hinterlegen",
			strClass="ym-edit",
			strHRef="/modules/Weather.html?token=%s" % (self.m_strSetupApiKeyToken))
		oHtmlPage.closeBox()
		return True

	def delegateFindCityIDsForLocation(self, strLocation, strMatching="like"):
		oReg = self.m_oWeatherApi.city_id_registry()
		self.m_lstCityIDs = oReg.ids_for(strLocation, matching="like")
		# [ (123, 'London', 'GB'), (456, 'London', 'MA'), (789, 'London', 'WY')]
		return
