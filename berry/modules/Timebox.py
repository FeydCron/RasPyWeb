## 
#  Plug-In für die Anbindung einer Divoom Timebox an RasPyWeb
#  
#  @file Timebox.py
#  @brief Plug-In für Divoom Timebox.
#  

import threading
from threading import Thread
from datetime import datetime
from time import sleep

import socket
import re
import struct

import bluetooth
from bluetooth import BluetoothSocket, BluetoothError, RFCOMM
#from bluetooth import *

from .. import globs
from .. import sdk
from ..sdk import ModuleBase, FastTask, LongTask, TaskSpeak, TaskSound

# Try to import from module "pillow" which might not be installed on the target system
#
try:
	import PIL
	from PIL import Image, ImageSequence, ImageEnhance

	globs.dbg("Modul <pillow> scheint verfügbar zu sein")
except:
	globs.exc("Modul <pillow> scheint nicht verfügbar zu sein")
	globs.registerMissingPipPackage(
		"pillow", "Python Imaging Library",
		"""Das Paket wird verwendet, um Bilder für die Timebox vorzubereitung und herunter zuladen.
		Solange das Paket nicht installiert wird, steht nicht der volle Funktionsumfang zur Verfügung.""")

def createModuleInstance(
	oWorker):
	return Timebox(oWorker)

class Timebox(ModuleBase):
	
	## 
	#  @copydoc sdk::ModuleBase::moduleInit
	#  
	def moduleInit(self, dictModCfg=None, dictCfgUsr=None):
		
		# Verfügbare Einstellungen mit Default-Werten festlegen
		dictSettings = {
			"bAutoConnect" 				: False,
			"bTime24Hours"				: True,
			"bUnitCelsius"				: True,
			"bMute"						: False,
			"bPowerSafe"				: False,
			"bOnOffByClap"				: False,
			"nPort" 					: 4,
			"nBrightness"				: 100,
			"nVolume"					: 7,
			"nAutoOffDelay"				: 0,
			"nImageResizeFilter"		: 0,
			"nImageEnhanceColor"		: 100,
			"nImageEnhanceContrast"		: 100,
			"nImageEnhanceBrightness"	: 100,
			"nImageEnhanceSharpness"	: 100,
			"strAddress" 				: "",
			"strColorTime"				: "#FFFFFF",
			"strColorTemp"				: "#FFFFFF",
			"strColorAmbient"			: "#FFFFFF",
			"strColorPrimary"			: "#00FF00",
			"strColorSecondary"			: "#FF0000",
			"strTestCommand"			: "",
			# "fFmFrequency"			: 90.7,
		}
		# Vorbelegung der Moduleigenschaften mit Default-Werten, sofern noch nicht verfügbar
		if (not dictModCfg):
			dictModCfg.update(dictSettings)
		else:
			for (strName, strValue) in dictSettings.items():
				if strName not in dictModCfg:
					dictModCfg.update({strName : strValue})

		# Beschreibung der Konfigurationseinstellungen
		dictCfgUsr.update({
			"bAutoConnect" : {
				"title"			: "Automatischer Verbindungsaufbau",
				"description"	: ("Automatischen oder manuellen Verbindungsaufbau aktivieren."),
				"default"		: False,
				"choices"		: {
					"Automatisch verbinden"	: True,
					"Manuell verbinden"		: False
				}
			},
			"bTime24Hours" : {
				"title"			: "Uhrzeitformat (24h)",
				"description"	: ("Darstellung der Uhrzeit in 12/24-Stunden einstellen."),
				"default"		: True,
				"type"			: "radio",
				"choices"		: {
					"24-Stundenanzeige"		: True,
					"12-Stundenanzeige"		: False
				}
			},
			"bUnitCelsius" : {
				"title"			: "Temperatureinheit (°C)",
				"description"	: ("Darstellung der Temperatur in °C (Celsius) oder °F (Fahrenheit) einstellen."),
				"default"		: True,
				"type"			: "radio",
				"choices"		: {
					"°C (Celsius)"			: True,
					"°F (Fahrenheit)"		: False
				}
			},
			"bMute" : {
				"title"			: "Stummschaltung",
				"description"	: ("Stummschaltung ein- oder ausschalten."),
				"default"		: False,
				"type"			: "radio"
			},
			"bPowerSafe" : {
				"title"			: "Energiesparmodus",
				"description"	: ("Schaltet das Gerät nach 5 Minuten in Standby."),
				"default"		: False,
				"type"			: "radio"
			},
			"bOnOffByClap" : {
				"title"			: "Klatsch-Befehl",
				"description"	: ("Aktiviert oder Deaktiviert das Ein- und Ausschalten des Displays durch Klatschen."),
				"default"		: False,
				"type"			: "radio"
			},
			"nPort" : {
				"title"			: "Portnummer für RFCOMM",
				"description"	: ("Einstellung der Portnummer für RFCOMM mit einer Timebox."),
				"default"		: 4
			},
			"nBrightness" : {
				"title"			: "LED-Helligkeit",
				"description"	: ("Helligkeit der LED-Anzeige einstellen."),
				"default"		: 100,
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"100\" step=\"10\""
			},
			"nVolume" : {
				"title"			: "Lautstärke",
				"description"	: ("Lautstärke einstellen."),
				"default"		: 7,
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"15\" step=\"1\""
			},
			"nAutoOffDelay" : {
				"title"			: "Automatische Abschaltung",
				"description"	: ("Schaltet das Gerät nach der eingestellten Verzögerung aus, wenn das Gerät nicht verwendet wird."),
				"default"		: 0,
				"type"			: "radio",
				"choices"		: {
					"Niemals"			: 0,
					"30 Minuten"		: 30,
					"1 Stunde"			: 60,
					"3 Stunden"			: 180,
					"6 Stunden"			: 360,
					"12 Stunden"		: 720
				}
			},
			"nImageResizeFilter" : {
				"title"			: "Größenanpassungsfilter",
				"description"	: ("Auswahl eines Filters, mit dem die Größenanpassung von Bildern vorgenommen werden soll."),
				"default"		: 0,
				"type"			: "radio",
				"choices"		: {
					"0 - NEAREST"		: 0,
					"1 - BOX"			: 1	,
					"2 - BILINEAR"		: 2,
					"3 - HAMMING"		: 3,
					"4 - BICUBIC"		: 4,
					"5 - LANCZOS"		: 5
				}
			},
			"nImageEnhanceColor" : {
				"title"			: "Farbkorrektur Größenanpassung",
				"description"	: ("Einstellung einer Farbkorrektur, welche bei der Größenanpassung von Bildern angewendet werden soll."),
				"default"		: 100,
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"200\" step=\"1\""
			},
			"nImageEnhanceContrast" : {
				"title"			: "Kontrast Größenanpassung",
				"description"	: ("Einstellung eines Kontrasts, welcher bei der Größenanpassung von Bildern angewendet werden soll."),
				"default"		: 100,
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"200\" step=\"1\""
			},
			"nImageEnhanceBrightness" : {
				"title"			: "Helligkeit Größenanpassung",
				"description"	: ("Einstellung einer Helligkeit, welche bei der Größenanpassung von Bildern angewendet werden soll."),
				"default"		: 100,
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"200\" step=\"1\""
			},
			"nImageEnhanceSharpness" : {
				"title"			: "Schärfe Größenanpassung",
				"description"	: ("Einstellung einer Schärfe, welche bei der Größenanpassung von Bildern angewendet werden soll."),
				"default"		: 100,
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"200\" step=\"1\""
			},
			"strAddress" : {
				"title"			: "Adresse der Timebox",
				"description"	: ("Einstellung der Adresse einer Timebox, zu der eine Verbindung hergestellt werden soll."),
				"default"		: "",
				"choices"		: {
					"Keine Timebox verfügbar"		: ""
				}
			},
			"strColorTime" : {
				"title"			: "Uhrzeitfarbe",
				"description"	: ("Farbeinstellung der Uhrzeitanzeige."),
				"default"		: "#FFFFFF",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strColorTemp" : {
				"title"			: "Temperaturfarbe",
				"description"	: ("Farbeinstellung der Temperaturanzeige."),
				"default"		: "#FFFFFF",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strColorAmbient" : {
				"title"			: "Umgebungslicht",
				"description"	: ("Farbeinstellung für das Umgebungslicht."),
				"default"		: "#FFFFFF",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strColorPrimary" : {
				"title"			: "Primärfarbe",
				"description"	: ("Einstellung einer Primärfarbe für verschiedene Anwendung, z.B. die Darstellung von Wellenformen."),
				"default"		: "#00FF00",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strColorSecondary" : {
				"title"			: "Sekundärfarbe",
				"description"	: ("Einstellung einer Sekundärfarbe für verschiedene Anwendung, z.B. die Darstellung von Wellenformen."),
				"default"		: "#FF0000",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strTestCommand" : {
				"title"			: "Test-Kommando",
				"description"	: ("Vorgabe einer Byte-Sequenz für Testzwecke."),
				"default"		: "",
				"type"			: "text",
				"pattern"		: r"^([A-Fa-f0-9]{2}\s?){1,}$"
			},
			# "fFmFrequency" : {
			# 	"title"			: "FM Radio Frequenz",
			# 	"description"	: ("Frequenz (MHz) eines Senders für das FM Radio einstellen, z.B. 88.1 oder 100.3."),
			# 	"default"		: 90.7
			# },
		})

		# Auslesen der aktuellen Konfigurationseinstellungen
		self.m_bAutoConnect = globs.getSetting("Timebox", "bAutoConnect", "(True|False)", False)

		self.m_bProtocolPending = False
		self.m_oTimeboxProtocol = None

		self.m_nScoreLower = 0
		self.m_nScoreUpper = 0

		self.m_nWeatherCond = 0x00
		self.m_nWeatherTemp = 0

		self.m_nSelectedDisplay = 0
		self.m_nSelectedAnimation = 0
		self.m_nSelectedWaveForm = 0
		self.m_nSelectedAmbientPattern = 0

		# TODO
		# - Nach verfügbaren Bluetooth Geräten suchen (zyklisch, solange keine Timebox-Geräte gefunden wurden)
		# - Je nach Einstellung automatisch die Verbindung aufbauen

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

		self.disconnectTimebox()

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
			# Moduleinstellungen wurden geändert
			if (strCmd == "settings" and lstArg	and "Timebox" in lstArg):
				for (strCmd, _) in dictForm.items():
					if (strCmd in ["bTime24Hours", "strColorTime"]):
						self.displayClock()
						continue
					if (strCmd in ["bUnitCelsius", "strColorTemp"]):
						self.displayWeather()
						continue
					if (strCmd in ["nBrightness"]):
						self.changeDisplayBrightness()
						continue
					if (strCmd in ["nVolume"]):
						self.synchronizeVolume()
						continue
					if (strCmd in ["bMute"]):
						self.synchronizeMute()
						continue
					if (strCmd in ["bOnOffByClap", "bPowerSafe", "nAutoOffDelay"]):
						self.synchronizeBasicSettings(
							bOnOffByClap=True if strCmd == "bOnOffByClap" else False,
							bPowerSafe=True if strCmd == "bPowerSafe" else False,
							bAutoOffDelay=True if strCmd == "nAutoOffDelay" else False
						)
						continue
					if (strCmd in ["strTestCommand"]):
						self.sendGenericCommand()
						continue
					# if (strCmd in ["fFmFrequency"]):
					# 	self.getFmFrequency()
					# 	continue
				continue
			# Systemeinstellungen wurden geändert
			if (strCmd == "system" and lstArg and self.m_oTimeboxProtocol):
				if ("date" in lstArg or "time" in lstArg):
					self.changeDateAndTime()
					continue
				continue
			if (strCmd == "picture" and lstArg and self.m_oTimeboxProtocol):
				for strArg in lstArg:
					self.displayImage(strArg)
					break
				continue
			# Timer-Ereignisse
			if (strCmd == "timer" and lstArg and self.m_oTimeboxProtocol):
				if ("cron" in lstArg):
					self.changeDateAndTime()
					continue
				continue
			# Gerätekommandos
			if (strCmd == "device" and lstArg):
				# Suche nach erreichbaren Geräten
				if ("discover" in lstArg):
					TaskSpeak(self.getWorker(), "Es wird nach Bluhtuhf Geräten gesucht").start()
					TaskTimeboxLong(self.getWorker(), self.doTimeboxDiscovery).start()
					continue
				# Verbindung zu ausgewähltem Gerät herstellen
				if ("connect" in lstArg):
					self.connectTimebox()
					continue
				# Verbindung zu aktuellem Gerät trennen
				if ("disconnect" in lstArg):
					self.disconnectTimebox()
					continue
				continue
			# Stopwatch-Kommandos
			if (strCmd == "stopwatch" and lstArg):
				if ("stop" in lstArg):
					self.displayStopwatch(bStop=True)
					continue
				if ("reset" in lstArg):
					self.displayStopwatch(bReset=True)
					continue
				self.displayStopwatch()
				continue
			# Scoreboard-Kommandos
			if (strCmd == "scoreboard" and lstArg):
				if ("upper" in lstArg):
					self.displayScoreboard(bIncUpper=True)
					continue
				if ("lower" in lstArg):
					self.displayScoreboard(bIncLower=True)
					continue
				if ("reset" in lstArg):
					self.displayScoreboard(bReset=True)
					continue
				self.displayScoreboard()
				continue
			# Display-Kommandos
			if (strCmd == "display" and lstArg):
				if ("clock" in lstArg):
					self.displayClock()
					continue
				if ("weather" in lstArg):
					self.displayWeather()
					continue
				if ("image" in lstArg):
					self.m_oTimeboxProtocol.send([0x45, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00])
					continue
				if ("stopwatch" in lstArg):
					self.displayStopwatch()
					continue
				if ("scoreboard" in lstArg):
					self.displayScoreboard()
					continue
				continue
			# Ambient-Kommandos
			if (strCmd == "ambient" and lstArg):
				for strArg in lstArg:
					self.displayAmbientLight(strColor=strArg)
					break
				continue
			# Built-In Animation-Kommandos
			if (strCmd == "animation" and lstArg):
				for strArg in lstArg:
					self.displayBuiltInAnimation(strType=strArg)
					break
				continue
			# Built-In Waveform-Kommandos
			if (strCmd == "waveform" and lstArg):
				for strArg in lstArg:
					self.displayBuiltInWaveforms(strType=strArg)
					break
				continue
			# Vorgabe Temperatur/Wetterbedingungen
			if (strCmd == "temperature" and lstArg):
				for strArg in lstArg:
					self.changeTemperature(strTemp=strArg)
					break
				continue
			if (strCmd == "weather" and lstArg):
				for strArg in lstArg:
					self.changeWeatherCondition(strType=strArg)
					break
				continue
			# Vorgabe/Auslesen Lautstärke und Stummschaltung
			if (strCmd == "volume" and lstArg):
				try:
					if ("on" in lstArg):
						globs.setSetting("Timebox", "bMute", True)
						self.synchronizeMute()
						continue
					if ("off" in lstArg):
						globs.setSetting("Timebox", "bMute", False)
						self.synchronizeMute()
						continue
					if ("min" in lstArg):
						globs.setSetting("Timebox", "nVolume", 0)
						self.synchronizeVolume()
						continue
					if ("low" in lstArg):
						globs.setSetting("Timebox", "nVolume", 3)
						self.synchronizeVolume()
						continue
					if ("med" in lstArg):
						globs.setSetting("Timebox", "nVolume", 7)
						self.synchronizeVolume()
						continue
					if ("high" in lstArg):
						globs.setSetting("Timebox", "nVolume", 11)
						self.synchronizeVolume()
						continue
					if ("max" in lstArg):
						globs.setSetting("Timebox", "nVolume", 15)
						self.synchronizeVolume()
						continue
					for strArg in lstArg:
						globs.setSetting("Timebox", "nVolume", int(strArg))
						self.synchronizeVolume()
						globs.setSetting("Timebox", "bMute", False)
						self.synchronizeMute()
						break
				except:
					globs.exc("Vorgabe Lautstärke oder Stummschaltung")
				continue
			# Spiel auswählen
			if (strCmd == "game" and lstArg):
				try:
					if ("off" in lstArg):
						self.displayBuiltInGame(bState=False)
						continue
					if ("start" in lstArg):
						self.displayBuiltInGame(bStart=True)
						continue
					for strArg in lstArg:
						self.displayBuiltInGame(bState=True, strType=strArg)
						break
				except:
					globs.exc("Vorgabe Lautstärke oder Stummschaltung")
				continue
			# Bild auswählen
			if (strCmd == "picture" and lstArg):
				try:
					for strArg in lstArg:
						self.displayImage(strArg)
						break
				except:
					globs.exc("Bild einstellen")
				continue

		# Unbekanntes Kommando
		return bResult

	def sendGenericCommand(self, strCommand=None):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			if not strCommand:
				strCommand = globs.getSetting("Timebox", "strTestCommand", r"^([A-Fa-f0-9]{2}\s?){1,}$", "")
			
			print("Test-Kommando: %r" % (strCommand))

			if not strCommand:
				return None

			lyData = bytearray.fromhex(strCommand)

			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Test-Kommando absetzen")
		return None

	def convertImageToTimeboxRGB(self, oImage):
		return

	def convertImageToTimeboxFormat(self, strFile, strFormat):
		return

	def displayImage(self, strName):
		lstFilters = [
			Image.NEAREST,
			Image.BOX,
			Image.BILINEAR,
			Image.HAMMING,
			Image.BICUBIC,
			Image.LANCZOS
		]
		try:
			if not self.m_oTimeboxProtocol or globs.isMissingPipPackage("pillow"):
				return None

			strFile = globs.findMatchingImageFile(strName)
			if not strFile:
				return None
			
			oFilter = lstFilters[0]
			nFilter = globs.getSetting("Timebox", "nImageResizeFilter", r"[0-5]", 0)
			nColor = globs.getSetting("Timebox", "nImageEnhanceColor", r"[0-9]{1,3}", 100)
			nContrast = globs.getSetting("Timebox", "nImageEnhanceContrast", r"[0-9]{1,3}", 100)
			nBrightness = globs.getSetting("Timebox", "nImageEnhanceBrightness", r"[0-9]{1,3}", 100)
			nSharpness = globs.getSetting("Timebox", "nImageEnhanceSharpness", r"[0-9]{1,3}", 100)
			if (nFilter >= 0 and nFilter < len(lstFilters)):
				oFilter = lstFilters[nFilter]
			
			with Image.open(strFile) as oImage:
				lstData = []
				nDuration = 0
				nFrame = 0
				
				try:
					
					if ("duration" in oImage.info.keys()):
						nDuration = int(oImage.info["duration"])

					print("--------------------------------------------------")
					print("Version    : %s" % (PIL.__version__))
					print("--------------------------------------------------")
					print("Format     : %r" % (oImage.format))
					print("Mode       : %r" % (oImage.mode))
					print("Width      : %r" % (oImage.width))
					print("Height     : %r" % (oImage.height))
					print("Palette    : %r" % (oImage.palette))
					print("Info       : %r" % (oImage.info))
					print("Duration   : %r" % (nDuration))
					#print("Colors     : %r" % (oImage.getcolors()))
					print("--------------------------------------------------")
					print("Filter     : %r" % (oFilter))
					print("Color      : %r" % (nColor))
					print("Contrast   : %r" % (nContrast))
					print("Brightness : %r" % (nBrightness))
					print("Sharpness  : %r" % (nSharpness))
					print("--------------------------------------------------")
				except:
					globs.exc("displayImage(%s)" % (strName))

				for oImg in ImageSequence.Iterator(oImage):
					
					# Preparations to get a RGB image from images with Alpha channel
					oImg = oImg.convert('RGBA')
					oBg = Image.new('RGBA', oImg.size, (255,255,255))
					oImg = Image.alpha_composite(oBg, oImg)
					oImg = oImg.convert(mode="RGB")

					# Improvements to apply to the image
					if (nColor != 100):
						oImg = ImageEnhance.Color(oImg).enhance(nColor / 100)
					if (nContrast != 100):
						oImg = ImageEnhance.Contrast(oImg).enhance(nContrast / 100)
					if (nBrightness != 100):
						oImg = ImageEnhance.Brightness(oImg).enhance(nBrightness / 100)
					if (nSharpness != 100):
						oImg = ImageEnhance.Sharpness(oImg).enhance(nSharpness / 100)

					if (oImg.width != 11 or oImg.height != 11):
						if (oImg.width != oImg.height):
							nMinSize = min(oImg.width, oImg.height)
							nMaxSize = max(oImg.width, oImg.height)
							nOffset = round((nMaxSize - nMinSize) / 2)

							if (nMaxSize == oImg.width):
								oBox = (nOffset, 0, oImg.width - nOffset, oImg.height)
								oImg = oImg.crop(oBox)
							else:
								oBox = (0, nOffset, oImg.width, oImg.height - nOffset)
								oImg = oImg.crop(oBox)
						oImg = oImg.resize(size=(11, 11),  resample=oFilter)
					
					lyData = [0xB1, 0x00, nFrame, max(round(nDuration / 100), 1)]
					nFrame += 1
					lstR = list(oImg.getdata(band=0))
					lstG = list(oImg.getdata(band=1))
					lstB = list(oImg.getdata(band=2))
					bContinue = False
					nByte = 0
					for i in range(11*11):
						if not bContinue:
							#nByte = (lstR[i] & 0x0F) 			# (round(lstR[i] / 16) & 0x0F)
							#nByte |= ((lstG[i] << 4) & 0xF0) 	# ((round(lstG[i] / 16) << 4) & 0xF0)
							nByte = (int(lstR[i] / 16) & 0x0F)
							nByte |= ((int(lstG[i] / 16) << 4) & 0xF0)
							lyData.append(nByte)
							#nByte = (lstB[i] & 0x0F)			# (round(lstB[i] / 16) & 0x0F)
							nByte = (int(lstB[i] / 16) & 0x0F)
							bContinue = True
						else:
							#nByte |= ((lstR[i] << 4) & 0xF0)	# ((round(lstR[i] / 16) << 4) & 0xF0)
							nByte |= ((int(lstR[i] / 16) << 4) & 0xF0)
							lyData.append(nByte)
							#nByte = (lstG[i] & 0x0F)			# (round(lstG[i] / 16) & 0x0F)
							#nByte |= ((lstB[i] << 4) & 0xF0)	# ((round(lstB[i] / 16) << 4) & 0xF0)
							nByte = (int(lstG[i] / 16) & 0x0F)
							nByte |= ((int(lstB[i] / 16) << 4) & 0xF0)
							lyData.append(nByte)
							bContinue = False
					if bContinue:
						lyData.append(nByte)
					lstData.append(lyData)

				for lyData in lstData:
					lyData[1] = len(lstData)
					self.m_oTimeboxProtocol.send(lyData)

			return None
		except:
			globs.exc("Bild darstellen")
		return None

	def displayBuiltInGame(self, bState=False, bStart=False, strType=None):
		lstGames = [
			"one-armed-bandit",
			"roll-the-dice",
			"yes-or-no",
			"car-racing"]

		try:
			if not self.m_oTimeboxProtocol:
				return None
			nType = 0
			try:
				if strType.isdigit():
					nType = min(max(int(strType), 0), 256)
				elif strType in lstGames:
					nType = lstGames.index(strType)
				else:
					nType = 0
					bState = False
			except:
				nType = 0
				bState = False

			if bStart:
				# Spiel starten
				lyData = [0x88]	
			else:
				# Spiel auswählen
				lyData = [0xA0,
					0x01 if bState else 0x00,
					nType]
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Spiel auswählen")
		return None
	
	def fetchDisplaySettings(self):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			# Display-Einstellungen abrufen
			lyData = [0x46]
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Display-Einstellungen abrufen")
		return None
	
	def notifyDisplaySettings(self, command, data):
		if (command == 0x46 and len(data) >= 26):
			# Ausgewählte Anzeige (0...7)
			self.m_nSelectedDisplay = min(max(int.from_bytes(data[3:4], byteorder='big', signed=False), 0), 7)
			globs.log("Eingestellte Anzeige abgerufen: %r" % (self.m_nSelectedDisplay))
			# Ausgewählte Temperatureinheit (0/1)
			nUnitCelsius = min(max(int.from_bytes(data[4:5], byteorder='big', signed=False), 0), 1)
			globs.setSetting("Timebox", "bUnitCelsius", True if nUnitCelsius == 0x01 else False)
			globs.log("Temperatureinheit abgerufen (°C): %r (%r)" % (True if nUnitCelsius == 0x01 else False, nUnitCelsius))
			# Ausgewählte Animation (0...7)
			self.m_nSelectedAnimation = min(max(int.from_bytes(data[5:6], byteorder='big', signed=False), 0), 7)
			# Ausgewählte Umgebungslichtfarbe (RGB)
			strColor = "#{:02X}{:02X}{:02X}".format(
				min(max(int.from_bytes(data[6:7], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[7:8], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[8:9], byteorder='big', signed=False), 0), 255)
			)
			globs.setSetting("Timebox", "strColorAmbient", strColor)
			globs.log("Umgebungslichtfarbe abgerufen: %r" % (strColor))
			# Ausgewählte Umgebungslichthelligkeit (0...100)
			nBrightness = min(max(int.from_bytes(data[9:10], byteorder='big', signed=False), 0), 100)
			globs.setSetting("Timebox", "nBrightness", nBrightness)
			globs.log("Umgebungslichthelligkeit abgerufen: %r" % (nBrightness))
			# Ausgewählte Wellenform (0...6)
			self.m_nSelectedWaveForm = min(max(int.from_bytes(data[10:11], byteorder='big', signed=False), 0), 6)
			globs.log("Eingestellte Wellenform abgerufen: %r" % (self.m_nSelectedWaveForm))
			# 2. Ausgewählte Helligkeit ignorieren
			# Ausgewähltes Uhrzeitformat
			nTime24Hours = min(max(int.from_bytes(data[12:13], byteorder='big', signed=False), 0), 1)
			globs.setSetting("Timebox", "bTime24Hours", True if nTime24Hours == 0x01 else False)
			globs.log("Uhrzeitformat abgerufen (24h): %r (%r)" % (True if nTime24Hours == 0x01 else False, nTime24Hours))
			# Ausgewählte Uhrzeitfarbe (RGB)
			strColor = "#{:02X}{:02X}{:02X}".format(
				min(max(int.from_bytes(data[13:14], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[14:15], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[14:16], byteorder='big', signed=False), 0), 255)
			)
			globs.setSetting("Timebox", "strColorTime", strColor)
			globs.log("Uhrzeitfarbe abgerufen: %r" % (strColor))
			# Ausgewählte Temperaturfarbe (RGB)
			strColor = "#{:02X}{:02X}{:02X}".format(
				min(max(int.from_bytes(data[16:17], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[17:18], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[18:19], byteorder='big', signed=False), 0), 255)
			)
			globs.setSetting("Timebox", "strColorTemp", strColor)
			globs.log("Temperaturfarbe abgerufen: %r" % (strColor))
			# Ausgewählte Sekundärfarbe (RGB)
			strColor = "#{:02X}{:02X}{:02X}".format(
				min(max(int.from_bytes(data[19:20], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[20:21], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[21:22], byteorder='big', signed=False), 0), 255)
			)
			globs.setSetting("Timebox", "strColorSecondary", strColor)
			globs.log("Sekundärfarbe abgerufen: %r" % (strColor))
			# Ausgewählte Primärfarbe (RGB)
			strColor = "#{:02X}{:02X}{:02X}".format(
				min(max(int.from_bytes(data[22:23], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[23:24], byteorder='big', signed=False), 0), 255),
				min(max(int.from_bytes(data[24:25], byteorder='big', signed=False), 0), 255)
			)
			globs.setSetting("Timebox", "strColorPrimary", strColor)
			globs.log("Primärfarbe abgerufen: %r" % (strColor))
			# Ausgewähltes Umgebungslichtmuster (0...4)
			self.m_nSelectedAmbientPattern = min(max(int.from_bytes(data[25:26], byteorder='big', signed=False), 0), 4)
			globs.log("Eingestelltes Umgebungslichtmuster abgerufen: %r" % (self.m_nSelectedAmbientPattern))

		return

	def fetchAudioSource(self):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			# Audio-Quelle abrufen
			lyData = [0x13]
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Audio-Quelle abrufen")
		return None

	def notifyAudioSource(self, command, data):
		if (command == 0x13 and len(data) >= 4):
			nAudioSource = int.from_bytes(data[3:4], byteorder='big', signed=False)
			globs.log("Audio-Quelle abgerufen: %r" % (nAudioSource))
		return

	def synchronizeVolume(self, bReadback=False):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			if bReadback:
				# Lautstärke abrufen
				lyData = [0x09]
			else:
				# Lautstärke einstellen
				lyData = [0x08,
					min(max(globs.getSetting("Timebox", "nVolume", r"\d{1,2}", 7), 0), 15)]
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Lautstärke %s" % ("abrufen" if bReadback else "einstellen"))
		return None

	def notifyVolume(self, command, data):
		if (command == 0x08 and len(data) >= 4):
			nVolume = int.from_bytes(data[3:4], byteorder='big', signed=False)
			globs.log("Lautstärke eingestellt: %r" % (nVolume))
			globs.setSetting("Timebox", "nVolume", nVolume)
		elif (command == 0x09 and len(data) >= 4):
			nVolume = int.from_bytes(data[3:4], byteorder='big', signed=False)
			globs.log("Lautstärke abgerufen: %r" % (nVolume))
			globs.setSetting("Timebox", "nVolume", nVolume)
		elif (command != 0x09):
			self.synchronizeVolume(bReadback=True)
		return

	def synchronizeMute(self, bReadback=False):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			if bReadback:
				# Stummschaltung abrufen
				lyData = [0x0B]
			else:
				# Stummschaltung einstellen
				lyData = [0x0A,
					0x00 if globs.getSetting("Timebox", "bMute", r"(True|False)", False) else 0x01]

			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Stummschaltung %s" % ("abrufen" if bReadback else "einstellen"))
		return None

	def notifyMute(self, command, data):
		if (command == 0x0A):
			self.synchronizeMute(bReadback=True)
		elif (command == 0x0B and len(data) >= 4):
			bMute = True if data[3] == 0x00 else False
			globs.log("Stummschaltung abgerufen: %r" % (bMute))
			globs.setSetting("Timebox", "bMute", bMute)
		return

	def synchronizeBasicSettings(self, bReadback=False,
		bAll = False,
		bOnOffByClap = False,
		bPowerSafe = False,
		bAutoOffDelay = False):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			lyData = []
			if bReadback:
				if bOnOffByClap or bAll:
					lyData.append(0xA8)
					self.m_oTimeboxProtocol.send(lyData[-1:])
				if bPowerSafe or bAll:
					lyData.append(0xB3)
					self.m_oTimeboxProtocol.send(lyData[-1:])
				if bAutoOffDelay or bAll:
					lyData.append(0xAC)
					self.m_oTimeboxProtocol.send(lyData[-1:])
			else:
				if bOnOffByClap:
					lyData.append(0xA7)
					self.m_oTimeboxProtocol.send([
						lyData[-1],
						0x01 if globs.getSetting("Timebox", "bOnOffByClap", r"(True|False)", False) else 0x00
					])
				if bPowerSafe:
					lyData.append(0xB2)
					self.m_oTimeboxProtocol.send([
						lyData[-1],
						0x01 if globs.getSetting("Timebox", "bPowerSafe", r"(True|False)", False) else 0x00
					])
				if bAutoOffDelay:
					# Keine Quittung für dieses Kommando
					nAutoOffDelay = globs.getSetting("Timebox", "nAutoOffDelay", r"\d+", 0)
					self.m_oTimeboxProtocol.send([
						0xAB,
						nAutoOffDelay & 0xFF,
						(nAutoOffDelay >> 8) & 0xFF
					])
					# Eingestellten Wert explizit abrufen
					self.synchronizeBasicSettings(bReadback=True, bAutoOffDelay=True)
			return lyData
		except:
			globs.exc("Stummschaltung %s" % ("abrufen" if bReadback else "einstellen"))
		return None

	def notifyBasicSettings(self, command, data):
		if (command == 0xA8 and len(data) >= 4):
			bOnOffByClap = True if data[3] == 0x01 else False
			globs.log("Klatsch-Befehl abgerufen: %r" % (bOnOffByClap))
			globs.setSetting("Timebox", "bOnOffByClap", bOnOffByClap)
		elif (command == 0xB3 and len(data) >= 4):
			bPowerSafe = True if data[3] == 0x01 else False
			globs.log("Energiesparmodus abgerufen: %r" % (bPowerSafe))
			globs.setSetting("Timebox", "bPowerSafe", bPowerSafe)
		elif (command == 0xAC and len(data) >= 5):
			nAutoOffDelay = int.from_bytes(data[3:5], byteorder='little', signed=False)
			globs.log("Automatische Abschaltung abgerufen: %r" % (nAutoOffDelay))
			globs.setSetting("Timebox", "nAutoOffDelay", nAutoOffDelay)
		elif (command == 0xA7):
			self.synchronizeBasicSettings(bReadback=True, bOnOffByClap=True)
		elif (command == 0xB2):
			self.synchronizeBasicSettings(bReadback=True, bPowerSafe=True)
		return

	def changeTemperature(self, strTemp=None):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			self.m_nWeatherTemp = min(max(int(strTemp), -99), +127)
			lyData = [0x5F,
				int.from_bytes(struct.pack('b', self.m_nWeatherTemp), byteorder='big', signed=False),
				self.m_nWeatherCond]

			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Temperatur einstellen: %s" % (strTemp))
		return None

	def changeWeatherCondition(self, strType=None):
		lstConditions = [
			"sunny",					# 0x01 - sonnig				(sunny)
			"cheerful",					# 0x02 - heiter				(cheerful)
			"cloudy",					# 0x03 - bewölkt			(cloudy)
			"covered",					# 0x04 - bedeckt			(covered)
			"rainy",					# 0x05 - regnerisch			(rainy)
			"changeable",				# 0x06 - wechselhaft		(changeable)
			"thunderstorm",				# 0x07 - gewittrig			(thunderstorm)
			"snowy",					# 0x08 - schneeig			(snowy)
			"foggy",					# 0x09 - neblig				(foggy)
			"clear-at-night",			# 0x10 - nachts klar		(clear-at-night)
			"cloudy-at-night",			# 0x11 - nachts wolkig		(cloudy-at-night)
			"covered-at-night",			# 0x12 - nachts bedeckt		(covered-at-night)
			"rainy-at-night",			# 0x13 - nachts regnerisch	(rainy-at-night)
			"changeable-at-night",		# 0x14 - nachts wechselhaft	(changeable-at-night)
			"thunderstorm-at-night",	# 0x15 - nachts gewittrig	(thunderstorm-at-night)
			"snowy-at-night",			# 0x16 - nachts schneeig	(snowy-at-night)
			"foggy-at-night",			# 0x17 - nachts neblig		(foggy-at-night)
			# "clock-change",			# 0x18 - Zeitumstellung		(clock-change)
		]	

		try:
			if not self.m_oTimeboxProtocol:
				return None
			if strType.isdigit():
				self.m_nWeatherCond = min(max(int(strType), 1), 17)
			elif strType in lstConditions:
				self.m_nWeatherCond = lstConditions.index(strType) + 1
			
			lyData = [0x5F,
				int.from_bytes(struct.pack('b', self.m_nWeatherTemp), byteorder='big', signed=False),
				self.m_nWeatherCond]

			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Wetterbedingungen einstellen: %s" % (strType))
		return None

	def displayBuiltInWaveforms(self, strType="0"):
		lstAnimations = [
			"common",
			"stickman",
			"vertical",
			"horizontal",
			"seewaves",
			"campfire",
			"face"]

		try:
			if not self.m_oTimeboxProtocol:
				return None
			nType = 0
			try:
				if strType.isdigit():
					nType = min(max(int(strType), 0), 6)
				elif strType in lstAnimations:
					nType = lstAnimations.index(strType)
				else:
					nType = 0
			except:
				nType = 0
			
			lyData = [0x45, 0x04, nType]
			# Spitzen - Sekundärfarbe RGB
			strRGB = globs.getSetting("Timebox", "strColorSecondary", r"^#([A-Fa-f0-9]{6})$", "#FF0000")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
			# Balken - Primärfarbe RGB
			strRGB = globs.getSetting("Timebox", "strColorPrimary", r"^#([A-Fa-f0-9]{6})$", "#00FF00")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Audio-Wellenform anzeigen: %s" % (strType))
		return None

	def displayBuiltInAnimation(self, strType="0"):
		lstAnimations = [
			"diagonal",
			"expanding",
			"horizontal",
			"confetti",
			"arrows",
			"countdown",
			"spinning",
			"colors"
			]

		try:
			if not self.m_oTimeboxProtocol:
				return None
			nType = 0
			try:
				if strType.isdigit():
					nType = min(max(int(strType), 0), 7)
				elif strType in lstAnimations:
					nType = lstAnimations.index(strType)
				else:
					nType = 0
			except:
				nType = 0
			
			lyData = [0x45, 0x03, nType]
			# Spitzen - Sekundärfarbe RGB
			strRGB = globs.getSetting("Timebox", "strColorSecondary", r"^#([A-Fa-f0-9]{6})$", "#FF0000")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
			# Balken - Primärfarbe RGB
			strRGB = globs.getSetting("Timebox", "strColorPrimary", r"^#([A-Fa-f0-9]{6})$", "#00FF00")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Built-In-Animation anzeigen: %s" % (strType))
		return None

	def displayAmbientLight(self, strColor=None):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			lyData = [0x45, 0x02]
			if re.match(r"^([A-Fa-f0-9]{6})$", strColor):
				lyData.extend(bytes.fromhex(strColor))
			else:
				strRGB = globs.getSetting("Timebox", "strColorAmbient", r"^#([A-Fa-f0-9]{6})$", "#FFFFFF")
				lyData.extend(bytes.fromhex(str(strRGB[1:])))
			nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
			nAlpha %= 0x100
			lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
			lyData.append(0x03 if strColor and strColor == "flower" else 0x00)
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Stimmungslicht anzeigen: %s" % (strColor))
		return None
	
	def displayClock(self):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			lyData = [0x45, 0x00]
			# 12/24 (0x00/0x01)
			lyData.append(
				0x01 if globs.getSetting("Timebox", "bTime24Hours", r"(True|False)", True) else
				0x00)
			# Farbe RGB
			strRGB = globs.getSetting("Timebox", "strColorTime", r"^#([A-Fa-f0-9]{6})$", "#FFFFFF")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
			# Farbe Alpha
			nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
			nAlpha %= 0x100
			lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Uhrzeit anzeigen")
		return None

	def displayWeather(self):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			lyData = [0x45, 0x01]
			# °F/°C (0x00/0x01)
			lyData.append(
				0x00 if globs.getSetting("Timebox", "bUnitCelsius", r"(True|False)", True) else
				0x01)
			# Farbe RGB
			strRGB = globs.getSetting("Timebox", "strColorTemp", r"^#([A-Fa-f0-9]{6})$", "#FFFFFF")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
			# Farbe Alpha
			nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
			nAlpha %= 0x100
			lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Wetter anzeigen")
		return None

	def displayStopwatch(self, bStop=False, bReset=False):
		try:
			if not self.m_oTimeboxProtocol:
				return None
			
			lyData = [0x45, 0x06]
			if (bReset):
				lyData.append(0x02)
			elif (bStop):
				lyData.append(0x00)
			else:
				lyData.append(0x01)
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Stoppuhr %s" % ("stoppen" if bStop else "zurücksetzen" if bReset else "anzeigen/starten"))
		return None

	def displayScoreboard(self, bIncLower=False, bIncUpper=False, bReset=False):
		try:
			if (bReset):
				self.m_nScoreLower = 0
				self.m_nScoreUpper = 0
			if (bIncLower):
				self.m_nScoreLower += 1
			if (bIncUpper):
				self.m_nScoreUpper += 1
			if not self.m_oTimeboxProtocol:
				return None
			globs.setSetting("Timebox", "nScoreLower", self.m_nScoreLower)
			globs.setSetting("Timebox", "nScoreUpper", self.m_nScoreUpper)
			
			lyData = [0x45, 0x07, 0x01]
			lyData.append(self.m_nScoreLower & 0x00FF)
			lyData.append((self.m_nScoreLower >> 8) & 0x00FF)
			lyData.append(self.m_nScoreUpper & 0x00FF)
			lyData.append((self.m_nScoreUpper >> 8) & 0x00FF)
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Punktzahl setzen, Oben=%d, Unten=%d" % (self.m_nScoreUpper, self.m_nScoreLower))
		return None

	def changeDisplayBrightness(self):
		try:
			if not self.m_oTimeboxProtocol:
				return None

			lyData = [0x74]
			# Farbe Alpha
			nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
			nAlpha %= 0x100
			lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Helligkeit einstellen")
		return None

	def changeDateAndTime(self):
		try:
			if not self.m_oTimeboxProtocol:
				return None
		
			lyData = [0x18]
			dt = datetime.today()		
			lyData.extend([
				int(dt.strftime("%Y")) % 100,
				int(int(dt.strftime("%Y")) / 100),
				int(dt.strftime("%m")),
				int(dt.strftime("%d")),
				int(dt.strftime("%H")),
				int(dt.strftime("%M")),
				int(dt.strftime("%S"))
			])
			
			self.m_oTimeboxProtocol.send(lyData)
			return lyData[0:1]
		except:
			globs.exc("Datum und Uhrzeit einstellen")
		return None

	# def getFmRadio(self, bOn):
	# 	lyData = [0x05, 0x01 if bOn else 0x00]
	# 	if bOn:
	# 		nFreq = int(globs.getSetting("Timebox", "fFmFrequency", r"\d+\.\d", 90.7) * 10)
	# 		lyData.append(int(nFreq % 100))
	# 		lyData.append(int(nFreq / 100))
	# 	return bytearray(lyData)

	# def getFmFrequency(self):
	# 	lyData = [0x61, 0x0A, 0x03]
	# 	# if bOn:
	# 	# 	nFreq = int(globs.getSetting("Timebox", "fFmFrequency", r"\d+\.\d", 90.7) * 10)
	# 	# 	lyData.append(int(nFreq % 100))
	# 	# 	lyData.append(int(nFreq / 100))
	# 	return bytearray(lyData)

	def onConnect(self, protocol):
		if (not self.m_oTimeboxProtocol and protocol):
			self.m_oTimeboxProtocol = protocol
			self.m_bProtocolPending = False
			
			TaskSpeak(self.getWorker(), "Verbindung zur Teimbox hergestellt").start()

			self.fetchAudioSource()
			self.fetchDisplaySettings()
			self.synchronizeBasicSettings(bReadback=True, bAll=True)
			self.synchronizeMute(bReadback=True)
			self.synchronizeVolume()

		return

	def onData(self, data):
		globs.log("Verarbeite Daten [%s], %d Bytes, %r" % (
			"".join("{:02X} ".format(a) for a in data),
			len(data),
			data
		))
		try:
			if (self.m_oTimeboxProtocol and len(data) >= 3
				and data[0] == 0x04 and data[2] == 0x55):	# Quittungen mit Ausführungsergebnis OK
				
				if (data[1] in [0x08, 0x09]):
					# Lautstärke eingestellt bzw. abgerufen
					self.notifyVolume(data[1], data)
				elif (data[1] in [0x0A, 0x0B]):
					# Stummschaltung eingestellt bzw. abgerufen
					self.notifyMute(data[1], data)
				elif (data[1] == 0x13):
					# Audio-Quelle abgerufen
					self.notifyAudioSource(data[1], data)
				elif (data[1] in [0xA7, 0xA8, 0xB2, 0xB3, 0xAB, 0xAC]):
					# Grundeinstellungen abgerufen
					self.notifyBasicSettings(data[1], data)
				elif (data[1] == 0x46):
					# Anzeigeeinstellungen abgerufen
					self.notifyDisplaySettings(data[1], data)

		except:
			globs.exc("Daten verarbeiten [%s], %d Bytes" % (
				"".join("{:02X} ".format(a) for a in data),
				len(data),
			))
			TaskSound(self.getWorker(), "AlienCreak2").start()
		else:
			TaskSound(self.getWorker(), "Pop").start()

		return

	def onDisconnect(self, protocol):
		if (self.m_oTimeboxProtocol is protocol
			or not self.m_oTimeboxProtocol):
			self.m_oTimeboxProtocol = None
			self.m_bProtocolPending = False
			TaskSpeak(self.getWorker(), "Verbindung zur Teimbox getrennt").start()
		return

	##
	# Suche nach Bluetooth-Geräten
	#
	def doTimeboxDiscovery(self):

		dictChoices = {
			"title"			: "Adresse der Timebox",
			"description"	: ("Einstellung der Adresse einer Timebox, zu der eine Verbindung hergestellt werden soll."),
			"default"		: "",
			"choices"		: {
				"Keine Timebox verfügbar"		: ""
			}
		}

		dictDiscovery = bluetooth.discover_devices(
			duration=16,
			lookup_names=True,
			flush_cache=False,
			lookup_class=False)

		if len(dictDiscovery) > 0:
			dictChoices["choices"].clear()

		print("dictDiscovery %r" % (dictDiscovery))

		for strAddr, strName in dictDiscovery:
			try:
				dictChoices["choices"].update({strName : strAddr})
			except:
				globs.exc("Fehler beim Auswerten der erreichbaren Bluetooth-Geräte")

		globs.updateModuleUserSetting("Timebox", "strAddress", dictChoices)

		TaskSpeak(self.getWorker(), "Die Suche nach Bluhtuhf Geräten ist abgeschlossen").start()

		return
	
	##
	# Verbindung herstellen
	#
	def connectTimebox(self):
		# Verbindung nur herstellen, wenn noch keine Verbindung besteht
		if (not self.m_oTimeboxProtocol
			and not self.m_bProtocolPending):
			self.m_bProtocolPending = True
			TimeboxClientProtocol(
				globs.getSetting("Timebox", "strAddress", r"^([0-9a-fA-F]{2}[:]){5}([0-9A-F]{2})$", ""),
				globs.getSetting("Timebox", "nPort", r"\d{1,5}", 4),
				self.cbConnect,
				self.cbDisconnect,
				self.cbData
			)
		return

	##
	# Verbindung trennen
	#
	def disconnectTimebox(self):
		# Verbindung trennen, sofern eine Verbindung besteht
		if (self.m_oTimeboxProtocol):
			self.m_oTimeboxProtocol.close()
		return

	##
	# Protokoll-Callback für den Verbindungsaufbau
	#
	def cbConnect(self, obj):
		# Ereignis in die Verarbeitungsqueue einhängen
		TaskTimeboxFast(self.getWorker(), self.onConnect, obj).start()
		return

	##
	# Protokoll-Callback für den Verbindungsabbruch
	#
	def cbDisconnect(self, obj):
		# Ereignis in die Verarbeitungsqueue einhängen
		TaskTimeboxFast(self.getWorker(), self.onDisconnect, obj).start()
		return

	##
	# Protokoll-Callback für den Datenempfang
	#
	def cbData(self, obj):
		# Ereignis in die Verarbeitungsqueue einhängen
		TaskTimeboxFast(self.getWorker(), self.onData, obj).start()
		return

class TaskTimeboxLong(LongTask):
	
	def __init__(self, oWorker, oFxn, oObj=None):
		super(TaskTimeboxLong, self).__init__(oWorker)
		self.m_oFxn = oFxn
		self.m_oObj = oObj
		return
		
	def __str__(self):
		strDesc = "Timebox-Aufgabe ausführen (%r, Fxn=%r, Obj=%r)" % (
			self,
			self.m_oFxn,
			self.m_oObj
		)
		return  strDesc
	
	def do(self):
		if (self.m_oObj):
			self.m_oFxn(self.m_oObj)
		else:
			self.m_oFxn()
		return

class TaskTimeboxFast(FastTask):
	
	def __init__(self, oWorker, oFxn, oObj=None):
		super(TaskTimeboxFast, self).__init__(oWorker)
		self.m_oFxn = oFxn
		self.m_oObj = oObj
		return
		
	def __str__(self):
		strDesc = "Timebox-Aufgabe ausführen (%r, Fxn=%r, Obj=%r)" % (
			self,
			self.m_oFxn,
			self.m_oObj
		)
		return  strDesc
	
	def do(self):
		if (self.m_oObj):
			self.m_oFxn(self.m_oObj)
		else:
			self.m_oFxn()
		return

class TimeboxClientProtocol:

	def __init__(self,
		strAddr,
		nPort,
		fxnConnect=None,
		fxnDisconnect=None,
		fxnData=None):
		self.m_fxnConnect = fxnConnect
		self.m_fxnDisconnect = fxnDisconnect
		self.m_fxnData = fxnData

		self.m_oTimeboxSocket = None
		self.m_lyRcvBuffer = []
		self.m_nMinMsgSize = 0

		self.m_oThread = Thread(
			target=self.threadProc,
			kwargs={
				"address" 	: strAddr,
				"port"		: nPort
			},
			daemon=1
		)
		self.m_oThread.start()
		return

	def send(self, data):
		lyToSend = self.wrap(data)
		globs.log("Senden Frame {%s}, %d Bytes aus Daten [%s], %d Bytes" % (
			"".join("{:02X} ".format(a) for a in lyToSend),
			len(lyToSend),
			"".join("{:02X} ".format(a) for a in data),
			len(data),
		))
		while (self.m_oTimeboxSocket and lyToSend):
			nSent = self.m_oTimeboxSocket.send(bytes(lyToSend))
			lyToSend = lyToSend[nSent:]
		return

	def close(self):
		if (not self.m_oTimeboxSocket):
			return
		self.m_oTimeboxSocket.shutdown(2)
		self.m_oThread.join()
		return

	def threadProc(self, address=None, port=0):
		# Verbindung herstellen
		if (address and port != 0):
			try:
				self.m_oTimeboxSocket = BluetoothSocket(RFCOMM)
				self.m_oTimeboxSocket.connect((address, port))
				globs.log("Bluetooth-Verbindung zu %s:%s hergestellt" % (
					address, port
				))
				# Verbindungsaufbau signalisieren
				if (self.m_fxnConnect):
					self.m_fxnConnect(self)
			except:
				self.m_oTimeboxSocket = None
				globs.exc("Ausnahmefehler beim Herstellen der Bluetooth-Verbindung")
		# Empfangsroutine
		while (self.m_oTimeboxSocket):
			try:
				data = self.m_oTimeboxSocket.recv(1024)
			except:
				globs.exc("Ausnahmefehler beim Empfangen über Bluetooth-Verbindung")
				data = None
			if (data):
				self.dataReceived(data)
			else:
				self.m_oTimeboxSocket.close()
				self.m_oTimeboxSocket = None
		# Verbindungsabbruch signalisieren
		if (self.m_fxnDisconnect):
			self.m_fxnDisconnect(self)
		return

	def dataReceived(self, data):
		# Empfangene Daten im Empfangspuffer sammeln
		self.m_lyRcvBuffer.extend(data)
		nRcvBufferSize = len(self.m_lyRcvBuffer)
		# Telegramm-Frames im Empfangspuffer verarbeiten
		while (nRcvBufferSize > self.m_nMinMsgSize):
			# Anfangs- und Endekennungen der Telegramm-Frames festlegen
			if (self.m_nMinMsgSize == 0):
				# Handshake-Telegramm nach Verbindungsaufbau
				yFrameStart = 0x00
				yFrameEnd = 0x00
			else:
				# Reguläre Telegramm-Frames
				yFrameStart = 0x01
				yFrameEnd = 0x02
			# Anfangskennung eines Telegramm-Frames finden
			try:
				nSliceStart = self.m_lyRcvBuffer.index(yFrameStart)
			except:
				# Wenn keine Anfangskennung existiert, alle bisher empfangenen Daten verwerfen
				self.m_lyRcvBuffer = []
				break
			# Endekennung eines Telegramm-Frames finden
			try:
				nSliceEnd = self.m_lyRcvBuffer[nSliceStart+1 :].index(yFrameEnd) + nSliceStart+1 + 1
			except:
				# Wenn keine Endekennung existiert, auf den Empfang weiterer Daten warten
				break
			# Telegramm-Frame verarbeiten
			lyFrame = self.m_lyRcvBuffer[nSliceStart : nSliceEnd]
			lyPayload = self.unwrap(lyFrame)
			globs.dbg("Empfang Daten [%s], %d Bytes aus Frame {%s}, %d Bytes" % (
				"".join("{:02X} ".format(a) for a in lyPayload),
				len(lyPayload),
				"".join("{:02X} ".format(a) for a in lyFrame),
				len(lyFrame),
			))
			if (lyPayload and self.m_fxnData):
				self.m_fxnData(lyPayload)
			# Emfpangene Daten bis zum Ende des Telegramm-Frames vom Empfangspuffer entfernen
			self.m_lyRcvBuffer = self.m_lyRcvBuffer[nSliceEnd:]
			nRcvBufferSize = len(self.m_lyRcvBuffer)
		return
	
	##
	# Konvertiert Telegrammdaten von Anwenderdarstellung in Protokolldarstellung.
	#
	# @param telegram
	# Telegrammdaten in Anwenderdarstellung
	#
	# @return
	# Liefert eine Liste der Telegrammdaten in Protokolldarstellung zurück.
	#
	def wrap(self, payload):
		lyFrame = []
		lyRawData = []
		if (payload):
			# Längeninformation des Telegramm-Frame festlegen
			nLen = len(payload) + 2
			lyFrame.append(nLen & 0x00FF)
			lyFrame.append((nLen >> 8) & 0x00FF)
			# Telegrammdaten in den Telegramm-Frame einfügen
			lyFrame.extend(payload)
			# Checksumme über den Telegramm-Frame erstellen und einfügen
			nChk = sum(lyFrame)
			lyFrame.append(nChk & 0x00FF)
			lyFrame.append((nChk >> 8) & 0x00FF)
			# Telegramm-Frame mit Anfangskennung begrenzen
			lyRawData.append(0x01)
			# Telegramm-Frame mit Länge und Checksumme erstellen und maskieren
			for yByte in lyFrame:
				if (yByte >= 0x01 and yByte <= 0x03):
					lyRawData.extend([0x03, 0x03 + yByte])
				else:
					lyRawData.append(yByte)
			# Telegramm-Frame mit Endekennung begrenzen
			lyRawData.append(0x02)
		return lyRawData

	##
	# Konvertiert Telegrammdaten von Protokolldarstellung in Anwenderdarstellung.
	#
	# @param telegram
	# Telegrammdaten in Protokolldarstellung
	#
	# @return
	# Liefert ein bytearry der Telegrammdaten in Anwenderdarstellung zurück.
	#
	def unwrap(self, telegram):
		lyTelegram = list(telegram) 
		lyRawData = list(telegram)
		lyPayload = []
		nLen = 0
		# Anfangs-/Endekennungen für Handshake Telegramm-Frame prüfen
		if (self.m_nMinMsgSize == 0):
			if (len(lyRawData) != 8
				or lyRawData.pop(0) != 0x00
				or lyRawData.pop(0) != 0x05
				or lyRawData.pop(len(lyRawData) - 1) != 0x00):
				# Fehler: Unerwartete Anfangs-/Endekennungen
				globs.err("Unerwartete Anfangs-/Endkennungen in Timebox-Handshake (%r) - [%s], %d Bytes" % (
					telegram,
					"".join("{:02X} ".format(a) for a in lyTelegram),
					len(lyTelegram)
				))
				return lyPayload
			# Handshake nach Verbindungsaufbau abgeschlossen
			globs.log("Handshake abgeschlossen")
			self.m_nMinMsgSize = 6
			return lyRawData
		elif (len(lyRawData) < 2
			or lyRawData.pop(0) != 0x01
			or lyRawData.pop(len(lyRawData) - 1) != 0x02):
			# Fehler: Telegramm zu kurz oder ungültige Anfangs-/Endekennungen
			globs.err("Unerwartete oder fehlende Anfangs-/Endkennungen in Timebox-Telegramm (%r) - [%s], %d Bytes" % (
				telegram,
				"".join("{:02X} ".format(a) for a in lyTelegram),
				len(lyTelegram)
			))
			return lyPayload
		# Längeninformation, Payload und Checksumme demaskieren
		while (len(lyRawData) > 0):
			yByte = lyRawData.pop(0)
			if (yByte == 0x03):
				if (len(lyRawData) == 0):
					# Error: Unexpected end of telegram
					globs.err("Unerwartetes Ende von Timebox-Telegramm (%r) - [%s], %d Bytes" % (
						telegram,
						"".join("{:02X} ".format(a) for a in lyTelegram),
						len(lyTelegram)
					))
					return []
				yByte = lyRawData.pop(0) - 0x03
			lyPayload.append(yByte)
		# Checksumme prüfen
		nChecksum = sum(lyPayload[:-2])
		if (len(lyPayload) < 2
			or lyPayload.pop() != ((nChecksum >> 8) & 0x00FF)	# Checksum High Value
			or lyPayload.pop() != (nChecksum & 0x00FF)):	# Checksum Low Value
			# Error: Ungültige Checksumme
			globs.err("Ungültige oder fehlende Checksumme in Timebox-Telegramm (%r) - [%s], %d Bytes" % (
				telegram,
				"".join("{:02X} ".format(a) for a in lyTelegram),
				len(lyTelegram)
			))
			return []
		# Längeninformation prüfen
		nLen = len(lyPayload)
		if (nLen < 2
			or lyPayload.pop(0) != (nLen & 0x00FF)
			or lyPayload.pop(0) != ((nLen >> 8) & 0x00FF)):
			# Fehler: Inkonsistente Telegrammlänge
			globs.err("Inkonsistente oder fehlende Längeninformation in Timebox-Telegramm (%r) - [%s], %d Bytes" % (
				telegram,
				"".join("{:02X} ".format(a) for a in lyTelegram),
				len(lyTelegram)
			))
			return []
		return lyPayload
