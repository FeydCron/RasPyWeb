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
			"strAddress" 		: "",
			"nPort" 			: 4,
			"bAutoConnect" 		: False,
			"bTime24Hours"		: True,
			"strTimeColor"		: "#FFFFFF",
			"bTempCelsius"		: True,
			"strTempColor"		: "#FFFFFF",
			"nBrightness"		: 100,
			"strAmbientColor"	: "#FFFFFF",
			"strPrimaryColor"	: "#00FF00",
			"strSecondaryColor"	: "#FF0000",
			# "fFmFrequency"	: 90.7,
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
			"strAddress" : {
				"title"			: "Adresse der Timebox",
				"description"	: ("Einstellung der Adresse einer Timebox, zu der eine Verbindung hergestellt werden soll."),
				"default"		: "",
				"choices"		: {
					"Keine Timebox verfügbar"		: ""
				}
			},
			"nPort" : {
				"title"			: "Portnummer für RFCOMM",
				"description"	: ("Einstellung der Portnummer für RFCOMM mit einer Timebox."),
				"default"		: 4
			},
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
				"title"			: "Uhrzeitdarstellung",
				"description"	: ("Darstellung der Uhrzeit in 12/24-Stunden einstellen."),
				"default"		: True,
				"type"			: "radio",
				"choices"		: {
					"24-Stundenanzeige"		: True,
					"12-Stundenanzeige"		: False
				}
			},
			"strTimeColor" : {
				"title"			: "Uhrzeitfarbe",
				"description"	: ("Farbeinstellung der Uhrzeitanzeige."),
				"default"		: "#FFFFFF",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"bTempCelsius" : {
				"title"			: "Temperaturdarstellung",
				"description"	: ("Darstellung der Temperatur in °C (Celsius) oder °F (Fahrenheit) einstellen."),
				"default"		: True,
				"type"			: "radio",
				"choices"		: {
					"°C (Celsius)"			: True,
					"°F (Fahrenheit)"		: False
				}
			},
			"strTempColor" : {
				"title"			: "Temperaturfarbe",
				"description"	: ("Farbeinstellung der Temperaturanzeige."),
				"default"		: "#FFFFFF",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"nBrightness" : {
				"title"			: "Helligkeit",
				"description"	: ("Helligkeit der LED-Anzeige einstellen."),
				"default"		: "100",
				"type"			: "range",
				"pattern"		: "min=\"0\" max=\"100\" step=\"10\""
			},
			"strAmbientColor" : {
				"title"			: "Umgebungslicht",
				"description"	: ("Farbeinstellung für das Umgebungslicht."),
				"default"		: "#FFFFFF",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strPrimaryColor" : {
				"title"			: "Primärfarbe",
				"description"	: ("Einstellung einer Primärfarbe für verschiedene Anwendung, z.B. die Darstellung von Wellenformen."),
				"default"		: "#00FF00",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
			},
			"strSecondaryColor" : {
				"title"			: "Sekundärfarbe",
				"description"	: ("Einstellung einer Sekundärfarbe für verschiedene Anwendung, z.B. die Darstellung von Wellenformen."),
				"default"		: "#FF0000",
				"type"			: "color",
				"pattern"		: r"^#([A-Fa-f0-9]{6})$"
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
			if (strCmd == "settings" and lstArg and self.m_oTimeboxProtocol
				and "Timebox" in lstArg):
				for (strCmd, _) in dictForm.items():
					if (strCmd in ["bTime24Hours", "strTimeColor"]):
						self.m_oTimeboxProtocol.send(self.displayClock())
						continue
					if (strCmd in ["bTempCelsius", "strTempColor"]):
						self.m_oTimeboxProtocol.send(self.displayWeather())
						continue
					if (strCmd in ["nBrightness"]):
						self.m_oTimeboxProtocol.send(self.changeDisplayBrightness())
						continue
					# if (strCmd in ["fFmFrequency"]):
					# 	self.m_oTimeboxProtocol.send(self.getFmFrequency())
					# 	continue
				continue
			# Systemeinstellungen wurden geändert
			if (strCmd == "system" and lstArg and self.m_oTimeboxProtocol):
				if ("date" in lstArg or "time" in lstArg):
					self.m_oTimeboxProtocol.send(self.changeDateAndTime())
					continue
				continue
			# Timer-Ereignisse
			if (strCmd == "timer" and lstArg and self.m_oTimeboxProtocol):
				if ("cron" in lstArg):
					self.m_oTimeboxProtocol.send(self.changeDateAndTime())
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
			if (strCmd == "stopwatch" and lstArg and self.m_oTimeboxProtocol):
				if ("stop" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayStopwatch(bStop=True))
					continue
				if ("reset" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayStopwatch(bReset=True))
					continue
				self.m_oTimeboxProtocol.send(self.displayStopwatch())
				continue
			# Scoreboard-Kommandos
			if (strCmd == "scoreboard" and lstArg and self.m_oTimeboxProtocol):
				if ("upper" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayScoreboard(bIncUpper=True))
					continue
				if ("lower" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayScoreboard(bIncLower=True))
					continue
				if ("reset" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayScoreboard(bReset=True))
					continue
				self.m_oTimeboxProtocol.send(self.displayScoreboard())
				continue
			# Display-Kommandos
			if (strCmd == "display" and lstArg and self.m_oTimeboxProtocol):
				if ("clock" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayClock())
					continue
				if ("weather" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayWeather())
					continue
				if ("image" in lstArg):
					self.m_oTimeboxProtocol.send([0x45, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00])
					continue
				if ("stopwatch" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayStopwatch())
					continue
				if ("scoreboard" in lstArg):
					self.m_oTimeboxProtocol.send(self.displayScoreboard())
					continue
				continue
			# Ambient-Kommandos
			if (strCmd == "ambient" and lstArg and self.m_oTimeboxProtocol):
				for strArg in lstArg:
					self.m_oTimeboxProtocol.send(self.displayAmbientLight(strColor=strArg))
					break
				continue
			# Built-In Animation-Kommandos
			if (strCmd == "animation" and lstArg and self.m_oTimeboxProtocol):
				for strArg in lstArg:
					self.m_oTimeboxProtocol.send(self.displayBuiltInAnimation(strType=strArg))
					break
				continue
			# Built-In Waveform-Kommandos
			if (strCmd == "waveform" and lstArg and self.m_oTimeboxProtocol):
				for strArg in lstArg:
					self.m_oTimeboxProtocol.send(self.displayBuiltInWaveforms(strType=strArg))
					break
				continue
			# Vorgabe Temperatur/Wetterbedingungen
			if (strCmd == "temperature" and lstArg and self.m_oTimeboxProtocol):
				for strArg in lstArg:
					self.m_oTimeboxProtocol.send(self.changeTemperature(strTemp=strArg))
					break
				continue
			if (strCmd == "weather" and lstArg and self.m_oTimeboxProtocol):
				for strArg in lstArg:
					self.m_oTimeboxProtocol.send(self.changeWeatherCondition(strType=strArg))
					break
				continue

			# Radio-Kommandos
			# if (strCmd == "radio" and lstArg and self.m_oTimeboxProtocol):
			# 	if ("frequency" in lstArg):
			# 		self.m_oTimeboxProtocol.send([0x60])
			#		continue
			# 	elif ("on" in lstArg):
			# 		self.m_oTimeboxProtocol.send([0x05, 0x01])
			#		continue
			# 	self.m_oTimeboxProtocol.send([0x05, 0x00])
			# 	continue

		# Unbekanntes Kommando
		return bResult

	def changeTemperature(self, strTemp=None):
		lyData = [0x5F]

		try:
			self.m_nWeatherTemp = min(max(int(strTemp), -99), +127)
		except:
			pass

		lyData.append(int.from_bytes(struct.pack('b', self.m_nWeatherTemp), byteorder='big', signed=False))
		lyData.append(self.m_nWeatherCond)
		return bytearray(lyData)

	def changeWeatherCondition(self, strType=None):
		lyData = [0x5F]
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
			if strType.isdigit():
				self.m_nWeatherCond = min(max(int(strType), 1), 17)
			elif strType in lstConditions:
				self.m_nWeatherCond = lstConditions.index(strType) + 1
		except:
			pass

		lyData.append(int.from_bytes(struct.pack('b', self.m_nWeatherTemp), byteorder='big', signed=False))
		lyData.append(self.m_nWeatherCond)
		return bytearray(lyData)

	def displayBuiltInWaveforms(self, strType="0"):
		lyData = [0x45, 0x04]
		nType = 0
		lstAnimations = [
			"common",
			"stickman",
			"vertical",
			"horizontal",
			"seewaves",
			"campfire",
			"face"]

		try:
			if strType.isdigit():
				nType = min(max(int(strType), 0), 6)
			elif strType in lstAnimations:
				nType = lstAnimations.index(strType)
			else:
				nType = 0
		except:
			nType = 0

		lyData.append(nType)
		# Spitzen - Sekundärfarbe RGB
		strRGB = globs.getSetting("Timebox", "strSecondaryColor", r"^#([A-Fa-f0-9]{6})$", "#FF0000")
		lyData.extend(bytes.fromhex(str(strRGB[1:])))
		# Balken - Primärfarbe RGB
		strRGB = globs.getSetting("Timebox", "strPrimaryColor", r"^#([A-Fa-f0-9]{6})$", "#00FF00")
		lyData.extend(bytes.fromhex(str(strRGB[1:])))
		return bytearray(lyData)

	def displayBuiltInAnimation(self, strType="0"):
		lyData = [0x45, 0x03]
		nType = 0
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
			if strType.isdigit():
				nType = min(max(int(strType), 0), 7)
			elif strType in lstAnimations:
				nType = lstAnimations.index(strType)
			else:
				nType = 0
		except:
			nType = 0

		lyData.append(nType)
		return bytearray(lyData)

	def displayAmbientLight(self, strColor=None):
		lyData = [0x45, 0x02]
		if re.match(r"^([A-Fa-f0-9]{6})$", strColor):
			lyData.extend(bytes.fromhex(strColor))
		else:
			strRGB = globs.getSetting("Timebox", "strAmbientColor", r"^#([A-Fa-f0-9]{6})$", "#FFFFFF")
			lyData.extend(bytes.fromhex(str(strRGB[1:])))
		nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
		nAlpha %= 0x100
		lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
		lyData.append(0x03 if strColor and strColor == "flower" else 0x00)
		return bytearray(lyData)
	
	def displayClock(self):
		lyData = [0x45, 0x00]
		# 12/24 (0x00/0x01)
		lyData.append(
			0x01 if globs.getSetting("Timebox", "bTime24Hours", r"(True|False)", True) else
			0x00)
		# Farbe RGB
		strRGB = globs.getSetting("Timebox", "strTimeColor", r"^#([A-Fa-f0-9]{6})$", "#FFFFFF")
		lyData.extend(bytes.fromhex(str(strRGB[1:])))
		# Farbe Alpha
		nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
		nAlpha %= 0x100
		lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
		return bytearray(lyData)

	def displayWeather(self):
		lyData = [0x45, 0x01]
		# °F/°C (0x00/0x01)
		lyData.append(
			0x00 if globs.getSetting("Timebox", "bTempCelsius", r"(True|False)", True) else
			0x01)
		# Farbe RGB
		strRGB = globs.getSetting("Timebox", "strTempColor", r"^#([A-Fa-f0-9]{6})$", "#FFFFFF")
		lyData.extend(bytes.fromhex(str(strRGB[1:])))
		# Farbe Alpha
		nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
		nAlpha %= 0x100
		lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
		return bytearray(lyData)

	def displayStopwatch(self, bStop=False, bReset=False):
		lyData = [0x45, 0x06]
		if (bReset):
			lyData.append(0x02)
		elif (bStop):
			lyData.append(0x00)
		else:
			lyData.append(0x01)
		return bytearray(lyData)

	def displayScoreboard(self, bIncLower=False, bIncUpper=False, bReset=False):
		lyData = [0x45, 0x07, 0x01]
		if (bReset):
			self.m_nScoreLower = 0
			self.m_nScoreUpper = 0
		if (bIncLower):
			self.m_nScoreLower += 1
		if (bIncUpper):
			self.m_nScoreUpper += 1
		lyData.append(self.m_nScoreLower & 0x00FF)
		lyData.append((self.m_nScoreLower >> 8) & 0x00FF)
		lyData.append(self.m_nScoreUpper & 0x00FF)
		lyData.append((self.m_nScoreUpper >> 8) & 0x00FF)
		return bytearray(lyData)

	def changeDisplayBrightness(self):
		lyData = [0x74]
		# Farbe Alpha
		nAlpha = globs.getSetting("Timebox", "nBrightness", r"\d{1,3}", 0xFF)
		nAlpha %= 0x100
		lyData.extend(bytes.fromhex("{:02X}".format(nAlpha)))
		return bytearray(lyData)

	def changeDateAndTime(self):
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
		return bytearray(lyData)

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

	def onConnect(self, protocol):
		if (not self.m_oTimeboxProtocol and protocol):
			self.m_oTimeboxProtocol = protocol
			self.m_bProtocolPending = False
			TaskSpeak(self.getWorker(), "Verbindung zur Teimbox hergestellt").start()

			# for i in range(0x00, 0xFF, 1):
			# 	self.m_oTimeboxProtocol.send([
			# 		i+1
			# 	])

			# self.m_oTimeboxProtocol.send([
			# 	0x59
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0x15
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0x13
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0x18,
			# 	0x13,
			# 	0x14,
			# 	0x01,
			# 	0x05,
			# 	0x00,
			# 	0x00,
			# 	0x00,
			# 	0x00
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0xb0
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0x42
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0xa2
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0x57, 0x00
			# ])
			# self.m_oTimeboxProtocol.send([
			# 	0x46
			# ])
		return

	def onDisconnect(self, protocol):
		if (self.m_oTimeboxProtocol is protocol
			or not self.m_oTimeboxProtocol):
			self.m_oTimeboxProtocol = None
			self.m_bProtocolPending = False
			TaskSpeak(self.getWorker(), "Verbindung zur Teimbox getrennt").start()
		return

	def onData(self, data):
		globs.log("Verarbeiten Daten [%s], %d Bytes" % (
			"".join("{:02X} ".format(a) for a in data),
			len(data),
		))
		TaskSound(self.getWorker(), "Pop").start()
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
			globs.log("Empfang Daten [%s], %d Bytes aus Frame {%s}, %d Bytes" % (
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
				globs.err("Unerwartete Anfangs-/Endkennungen in Timebox-Handshake (%r)" % (telegram))
				return lyPayload
			# Handshake nach Verbindungsaufbau abgeschlossen
			globs.log("Handshake abgeschlossen")
			self.m_nMinMsgSize = 6
			return lyRawData
		elif (len(lyRawData) < 2
			or lyRawData.pop(0) != 0x01
			or lyRawData.pop(len(lyRawData) - 1) != 0x02):
			# Fehler: Telegramm zu kurz oder ungültige Anfangs-/Endekennungen
			globs.err("Unerwartete oder fehlende Anfangs-/Endkennungen in Timebox-Telegramm (%r)" % (telegram))
			return lyPayload
		# Längeninformation, Payload und Checksumme demaskieren
		while (len(lyRawData) > 0):
			yByte = lyRawData.pop(0)
			if (yByte == 0x03):
				if (len(lyRawData) == 0):
					# Error: Unexpected end of telegram
					globs.err("Unerwartetes Ende von Timebox-Telegramm (%r)" % (telegram))
					return []
				yByte = lyRawData.pop(0) - 0x03
			lyPayload.append(yByte)
		# Checksumme prüfen
		nChecksum = sum(lyPayload[:-2])
		if (len(lyPayload) < 2
			or lyPayload.pop() != ((nChecksum >> 8) & 0x00FF)	# Checksum High Value
			or lyPayload.pop() != (nChecksum & 0x00FF)):	# Checksum Low Value
			# Error: Ungültige Checksumme
			globs.err("Ungültige oder fehlende Checksumme in Timebox-Telegramm (%r)" % (telegram))
			return []
		# Längeninformation prüfen
		nLen = len(lyPayload)
		if (nLen < 2
			or lyPayload.pop(0) != (nLen & 0x00FF)
			or lyPayload.pop(0) != ((nLen >> 8) & 0x00FF)):
			# Fehler: Inkonsistente Telegrammlänge
			globs.err("Inkonsistente oder fehlende Längeninformation in Timebox-Telegramm (%r)" % (telegram))
			return []
		return lyPayload
