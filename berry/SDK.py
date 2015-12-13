## 
#  @mainpage
#  
#  RasPyWeb ist ein auf Python3 basierendes Basissystem für den Raspberry und stellt in erster Linie
#  ein Web-Frontend zur Verfügung. Das Basissystem kann durch die Installation Modulen beliebig
#  erweitert werden.
#  
#  @see
#  - @ref setup
#  - @ref commands
#  

## 
#  @page setup Installation
#  
#  @section installdir Installationsverzeichnis
#  
#  RasPyWeb kann in einem beliebigen Verzeichnis installiert werden, z.B. `/home/pi/raspyweb`.
#  
#  Darüber hinaus müssen noch einige administrative Einstellungen vorgenommen werden, damit
#  RasPyWeb seinen vollen Funktionsumfang entfalten kann.
#  
#  
#  @section crontab Cron-Job einrichten
#  
#  Für einige Konfigurationsschritte müssen sogenannte Cron-Jobs eingerichtet werden. Führen Sie
#  das folgende Kommando aus, um einen Texteditor für die Einrichtung eines Cron-Jobs zu öffnen:
#  
#  @verbatim
#  crontab -e
#  @endverbatim
#  
#  Möglicherweise befinden sich bereits Einträge in der Konfigurationsdatei. Fügen Sie dann die
#  neuen Zeilen am Ende der Datei ein, sofern die betreffenden Einträge noch nicht existieren.
#  
#  Die neue Version der Konfigurationsdatei wird nach dem Beenden des Texteditors installiert.
#  
#  
#  @section cronstart Automatischen Start einrichten
#  
#  RasPyWeb kann beim Hochlauf des Raspberry automatisch gestartet werden, indem ein entsprechender
#  Cron-Job eingerichtet wird.
#  
#  @ref crontab
#  
#  Fügen Sie die folgende Zeile hinzu, sofern diese noch nicht existiert:
#  
#  @verbatim
#  @reboot     python3 <directory>/Berry.py
#  @endverbatim
#  
#  @e @<directory@> entspricht dem @ref installdir von RasPyWeb.
#  
#  Beim nächsten Neustart des Raspberry sollte RasPyWeb automatisch gestartet werden. Falls dies
#  nicht der Fall ist, überprüfen Sie bitte die folgenden Einrichtungsschritte:
#  
#  - @ref installdir
#  - @ref cronstart
#  
#  
#  @section crontimer Externen Zeitgeber einrichten
#  
#  Viele Module benötigen für die korrekte Funktion einen Zeitgeber. Es ist wichtig, dass das
#  Zeitgeberereignis synchron zur aktuellen Systemzeit eintritt. Zu diesem Zweck wird ein
#  Cron-Job eingerichtet, welcher ein solches Ereignis in einem Raster von 5 Minuten auslöst.
#  
#  @ref crontab
#  
#  Fügen Sie die folgende Zeile hinzu, sofern diese noch nicht existiert:
#  
#  @verbatim
#  */5 * * * * wget --tries=1 -O - http://127.0.0.1:8081/ext/evt.src?timer=cron
#  @endverbatim
#  
#  Von nun an sollten im 5-Minuten-Takt entsprechende Zeitgebereignisse generiert werden.
#  Sollten Module, die auf Zeitgeberereignisse angewiesen sind, nicht funktionieren, überprüfen
#  Sie bitte die folgenden Einstellungen:
#  
#  - Portnummer der Web-Server Schnittstelle von RasPyWeb
#  - @ref crontimer
#  
#  @see
#  - @ref event_crontimer
#  

## 
#  @page commands Modulkommandos
#  
#  Das Konzept der Modulkommandos stellt eine standardisierte Form für den Austausch von Daten
#  bzw. Informationen zwischen dem Web-Frontend und einem konkret angesprochenen installierten
#  Modul dar. Modulkommandos sind zwangsläufig modulspezifisch und werden durch das jeweilige
#  Modul festgelegt. Eine Beschreibung der verfügbaren Kommandos ist daher der Dokumentation des
#  jeweiligen Moduls zu entnehmen.
#  
#  Jedes Modul kann aufgrund eines Kommandos, eine eigene HTML-Seite für die Anzeige im Web-Frontend
#  generieren. Falls das Modul keine HTML-Seiten generiert, muss für die Kommandobearbeitung die
#  Weiterleitung auf eine existierende HTML-Seite des Web-Frontends berücksichtigt werden.
#  
#  @see
#  - @ref command_redirect2
#  
#  
#  @section special_commands Spezialkommandos
#  
#  Es gibt spezielle Kommandos, die durch die Infrastruktur des Basissystems (RasPyWeb) direkt
#  verarbeitet werden, ohne dass dafür ein spezielles Modul notwendig wäre. Es handelt sich dabei
#  jedoch nicht um reservierte Kommandos. Wenn ein konkretes Modul für die Verarbeitung von diesen
#  Spezialkommandos adressiert wird (oder beispielsweise eine Namensüberlappung vorliegt), werden
#  diese Kommandos unabhängig von der Verarbeitung durch das Basissystem an das jeweilige Modul
#  weitergeleitet, damit zusätzlich eine modulspezifische Verarbeitung stattfinden kann.
#  
#  
#  @subsection command_redirect2 Weiterleitung
#  
#  Dieses Kommando veranlasst den Web-Server dazu, anstelle der angeforderten URL die angegebene
#  Seite für die Darstellung im Web-Frontend zurückzuliefern. Das Kommando dient in erster Linie
#  dazu, modulspezifische Kommandos unabhängig von der im Web-Frontend darzustellenden Seite
#  anzufordern. Beispielsweise soll beim Klicken einer Schaltfläche, die mit einem Modulkommando
#  verknüpft ist, die Startseite nicht verlassen werden.
#  
#  Kontext		| Eigenschaft 	| Wert
#  ------------	| -------------	| ---------------
#  Kommando		| @c strPath	| @e beliebig
#  Query		| @c redirect2	| `startpage`
#  
#  @remark
#  Derzeit ist als Wert für das `redirect2` Kommando nur der Wert `startpage` zulässig.
#  
#  
#  @subsection command_sound Klangausgabe
#  
#  Dieses Kommando spielt den angegebenen Klang ab, sofern eine Übereinstimmung mit einer
#  installierten Klangdatei besteht. Eine Übereinstimmung mit einer Klangdatei besteht dann, wenn
#  der angegebene Bezeichner komplett oder mit einem Teil des Dateinamens einer Klangdatei
#  übereinstimmt. Falls der Bezeichner als Teil für mehrere Klangdateien einen Treffer ergeben
#  würde, wird immer dem ersten Treffer der Vorzug gegeben.
#  
#  Kontext		| Eigenschaft 	| Wert
#  ------------	| -------------	| ---------------
#  Kommando		| @c strPath	| @e beliebig
#  Query		| @c sound		| @e Bezeichner
#  Form			| @c sound		| @e Bezeichner
#  
#  @remark
#  @c Bezeichner muss komplett oder mit einem Teil des Dateinamens einer installierten Klangdatei
#  übereinstimmen, damit der angeforderte Klang angespielt werden kann.
#  
#  
#  @subsection command_speak Sprachausgabe
#  
#  Dieses Kommando macht eine 'text-to-speech' Umsetzung und spricht den angeforderten Text aus.
#  
#  Kontext		| Eigenschaft 	| Wert
#  ------------	| -------------	| -----------------
#  Kommando		| @c strPath	| @e beliebig
#  Query		| @c speak		| @e Text-to-Speech
#  Form			| @c speak		| @e Text-to-Speech
#  

## 
#  @page events Modulereignisse
#  
#  Das Konzept der Modulereignisse stellt eine standardisierte Form für den ereignisgesteuerten
#  Austausch von Informationen zwischen der Infrastruktur des Basissystems (RasPyWeb) und den
#  installierten Modulen sowie zwischen installierten Modulen untereinander dar.
#  
#  
#  @section external_events Externe Ereignisse
#  
#  Externe Ereignisse werden von Quellen ausserhalb des Basissystem generiert. Diese Ereignisse
#  treffen üblicherweise über die Web-Server Schnittstelle ein und können von einer anderen
#  RasPyWeb-Instanz oder einem anderen Programm bzw. System ausgehen.
#  
#  
#  @subsection event_crontimer Externer Zeitgeber
#  
#  Bei korrekter Installation generiert dieser externe Zeitgeber alle 5 Minuten ein Ereignis
#  synchron zur Systemzeit:
#  
#  Kontext		| Eigenschaft 	| Wert
#  ------------	| -------------	| ---------------
#  Ereignis		| @c strPath	| `/ext/evt.src`
#  Query		| @c timer		| `cron`
#  
#  @see
#  - @ref crontimer
#  


import os
import subprocess
import re
import threading
import socket
import html
import urllib.parse
import http.client

from datetime import datetime

from Voice import Voice
from Sound import Sound
from Globs import Globs

## 
#  @brief Werkzeug zum Erstellen von einfach strukturieren HTML-Seiten.
#  
class HtmlPage(list):

	## 
	#  @brief Erzeugt eine Instanz zum Erstellen einer HTML-Seite.
	#  
	#  @param [in] self
	#  Instanzverweis
	#  
	#  @param [in] strPath
	#  Pfad der HTML-Seite. Dies kann entweder ein virtueller Pfad oder eine Pfadangabe im
	#  Dateisystem sein, die von der Web-Server-Komponente bedient werden kann.
	#  
	#  @param [in] strTitle
	#  Optionaler Titel der HTML-Seite
	#  
	#  @param [in] nAutoRefresh
	#  Numerische Angabe eines Aktualisierungsintervalls für die HTML-Seite in Sekunden oder 0,
	#  wenn kein Aktualisierungsintervall aktiviert werden soll (standard). Aus Gründen der
	#  Performance muss die Angabe des Intervalls mindestens 5 Sekunden betragen, ansonsten wird
	#  kein Aktualisierungsintervall aktiviert.
	#  
	#  @return
	#  Kein Rückgabewert
	#  
	#  @details Details
	#  
	def __init__(self, strPath, strTitle=None, nAutoRefresh=0):
		list.__init__([])
		
		if (not strTitle):
			strTitle = ""
		
		self.m_strPath = strPath
		self.m_strTitle = strTitle
		self.m_bPageEnded = False
		self.m_bChk = False
		self.m_bAct = False
		self.m_strQueries = ""
		self.m_strAutoRefresh = ""
		self.m_nId = 0
		
		self.setAutoRefresh(nAutoRefresh)
		return
		
	## 
	#  @brief Brief
	#  
	#  @param [in] self
	#  Instanzverweis
	#  
	#  @param [in] strTitle
	#  Titel der HTML-Seite
	#  
	#  @return
	#  Kein Rückgabewert
	#  
	#  @details Details
	#  
	def setTitle(self, strTitle):
		self.m_strTitle = strTitle
		return
	
	## 
	#  @brief Ändert das Aktualisierungsintervall der HTML-Seite.
	#  
	#  @param [in] self
	#  Instanzverweis
	#  
	#  @param [in] nAutoRefresh
	#  Numerische Angabe eines Aktualisierungsintervalls für die HTML-Seite in Sekunden oder 0,
	#  wenn kein Aktualisierungsintervall aktiviert werden soll (standard). Aus Gründen der
	#  Performance muss die Angabe des Intervalls mindestens 5 Sekunden betragen, ansonsten wird
	#  kein Aktualisierungsintervall aktiviert.
	#  
	#  @return
	#  Liefert @c True, wenn das Aktualisierungsintervall aktiviert werden konnte oder @c False,
	#  falls nicht.
	#  
	#  @details Details
	#  	
	def setAutoRefresh(self, nAutoRefresh=0):
		if nAutoRefresh >= 5:
			self.m_strAutoRefresh = "<meta http-equiv=\"refresh\" content=\"%s\">" % (
				nAutoRefresh)
			return True
		self.m_strAutoRefresh = ""
		return False
	
	## 
	#  @brief Liefert den Inhalt der HTML-Seite als Bytes in Standardkodierung zurück.
	#  
	#  @param [in] self
	#  Instanzverweis
	#  
	#  @return
	#  Liefert den Inhalt der HTML-Seite als Bytes in Standardkodierung zurück.
	#  
	#  @details
	#  Die HTML-Seite wird durch den Aufruf abgeschlossen und darf anschließend nicht weiter
	#  bearbeitet werden.
	#  
	def getContent(self):
		if not self.m_bPageEnded:
			self.extend([
				"</body>",
				"</html>",
			])
		self.m_bPageEnded = True
		
		return (("<!DOCTYPE html>" +
			"<html lang=\"en\" xmlns=\"http://www.w3.org/1999/xhtml\">" +
			"<head>" +
			"<meta charset=\"utf-8\"/>" +
			"<title>%s</title>" % (html.escape(self.m_strTitle)) +
			"%s" % (self.m_strAutoRefresh) +
			"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">" +
			"<link href=\"../css/flexible-columns.css\" rel=\"stylesheet\" type=\"text/css\"/>" +
			"<!--[if lte IE 7]>" +
			"<link href=\"../../yaml/core/iehacks.css\" rel=\"stylesheet\" type=\"text/css\" />" +
			"<![endif]-->" +
			"<!--[if lt IE 9]>" +
			"<script src=\"../../lib/html5shiv/html5shiv.js\"></script>" +
			"<![endif]-->" +
			"</head>" +
			"<body>" +
			("\n".join(self))).encode())
	
	## 
	#  @brief Eröffnet ein tabellarisch angelegtes Formular.
	#  
	#  @param [in] self
	#  Instanzverweis
	#  
	#  @param [in] strCaption
	#  Titel des tabellarischen Formulars
	#  
	#  @param [in] lstHeader
	#  Liste der zu verwendenden Spaltenköpfe
	#  
	#  @param [in] strChk
	#  Legt den Titel für die Auswahlspalte fest. Wird kein Titel festgelegt, wird die Spalte nicht
	#  dargestellt. Wird ein Leerstring angegeben, wird die Spalte ohne Titel dargestellt.
	#  
	#  @param [in] strAct
	#  Legt den Titel für die Aktionsspalte fest. Wird kein Titel festgelegt, wird die Spalte nicht
	#  dargestellt. Wird ein Leerstring angegeben, wird die Spalte ohne Titel dargestellt.
	#  
	#  @param [in] bBorder
	#  Legt fest, ob die Tabelle mit (@c True) oder ohne (@c False) Rahmen dargestellt werden soll.
	#  
	#  @return
	#  Kein Rückgabewert
	#  
	#  @details
	#  Das tabellarische Formular wird optional zu den angegebenen Spaltenköpfen mit einer
	#  Auswahlspalte und einer Aktionsspalte versehen.
	#  
	#  Auswahlspalte	| benutzerdef. Spaltenköpfe | Aktionsspalte
	#  ---------------- | ------------------------- | -------------
	#  Check-Boxen		| Spaltenkopfbezeichnungen	| Schaltflächen
	#  
	#  Die Auswahl der Check-Boxen wird unter der Parameterbezeichnung `target` geführt und erhält
	#  jeweils den beim Einfügen eines Datensatzes angegebenen Referenzwert.
	#  
	def openTableForm(self, strCaption, lstHeader, strChk = None, strAct = None, bBorder = False):
		self.m_bChk = False
		self.m_bAct = False
		strClass = None
		if (strChk == ""):
			strChk = "&nbsp;"
		if (strAct == ""):
			strAct = "&nbsp;"
		if (strChk):
			self.m_bChk = True
		if (strAct):
			self.m_bAct = True
		if (bBorder):
			strClass = " class=\"bordertable"
		if (strClass):
			strClass += "\""
		else:
			strClass = ""
		self.extend([
			"<form class=\"%s\" method=\"%s\" enctype=\"%s\" action=\"%s\">" % (
				"ym-form ym-full", "post", "multipart/form-data", self.m_strPath),
			"<div class=\"ym-fbox\">",
			"<table%s>" % (strClass),
			"<caption>%s</caption>" % (html.escape(strCaption)),
			"<thead>",
			"<tr>",
		])
		if self.m_bChk:
			self.append("<th>%s</th>" % (html.escape(strChk)))
		for strHead in lstHeader:
			self.append("<th>%s</th>" % (html.escape(strHead)))
		if self.m_bAct:
			self.append("<th>%s</th>" % (html.escape(strAct)))
		self.extend([
			"</tr>",
			"</thead>",
			"<tbody>",
		])
		return
		
	# dictAct = {
	# 	"name" : {
	#		"title" : "",
	#		"query" : "",
	#		"content" : "",
	#		"type" : "primary|success|warning|danger",
	#	},
	# }
	
	## 
	#  @brief Erweitert ein eröffnetes tabellarisches Formular um einen Datensatz.
	#  
	#  @param [in] self 
	#  Instanzverweis
	#  
	#  @param [in] strRef 
	#  Referenzwert, der bei Auswahl der Auswahl-Check-Box unter der Parameterbezeichnung `target`
	#  angegeben wird.
	#  
	#  @param [in] lstData
	#  Datensatz, dessen Länge und Reihenfolge der Werte mit dem Spaltenkopf bei der Eröffnung des
	#  Formulars zusammenpassen muss.
	#  
	#  @param [in] bChk
	#  Gibt an, ob die Auswahl-Check-Box für diesen Datensatz vorausgewählt dargestellt werden soll.
	#  
	#  @param [in] dictAct
	#  Beschreibung der für den Datensatz anzulegenden Aktionsschaltflächen
	#  
	#  @param [in] bEscape
	#  Gibt an, ob die Funktion selbst die Konvertierung von Sonderzeichen in ein HTML-konformes
	#  Format durchführen soll.
	#  
	#  @return
	#  Kein Rückgabewert
	#  
	#  @details
	#  Für jeden Datensatz kann eine individuelle Anzahl an Aktionsschaltflächen festgelegt werden:
	#  
	#  @code
	#  	dictAct = {
	#  		"name" : {
	#  			"query" : "",
	#  			"content" : "",
	#  			"type" : "(primary|success|warning|danger)",
	#  		},
	#  	}
	#  @endcode
	#  
	#  Für jede Schaltfläche wird unter einem individuellen schlüssel @e name ein Dictionary für
	#  die Beschreibung der Schaltfläche angelegt:
	#  - `"query"`: Angabe eines Query-String, dessen Elemente durch `&` getrennt sind
	#  - `"content"`: Legt den Titel der Schaltfläche fest
	#  - `"type"`: Legt den Typ der Schaltfläche fest, wobei die folgenden Typen definiert sind:
	#  		- `primary`: Blaue Schaltfläche
	#  		- `success`: Grüne Schaltfläche
	#  		- `warning`: Gelbe Schaltfläche
	#  		- `danger`: Rote Schaltfläche
	#  - Alle weiteren Attribute werden als CSS-Klassenattribute in den HTML-Link eingepflegt.
	# 
	def appendTableForm(self, strRef, lstData, bChk=False, dictAct=None, bEscape=True):
		strChecked = ""
		self.extend([
			"<tr>",
		])
		
		if (not dictAct):
			dictAct = {}
		
		if bChk:
			strChecked = "checked"
		if self.m_bChk:
			self.append("<td>")
			self.append(
				"<input type=\"checkbox\" name=\"target\" value=\"%s\" %s/>" % (
				strRef, strChecked))
			self.append("</td>")
		for strData in lstData:
			if bEscape:
				strData = html.escape(strData)
			self.append("<td>%s</td>" % (strData))
		if self.m_bAct:
			self.append("<td style=\"white-space:nowrap\">")
			for (strName, dictParam) in sorted(dictAct.items()):
				strType = ""
				strContent = ""
				strAttr = ""
				strHRef = self.m_strPath
				for (strParam, strValue) in sorted(dictParam.items()):
					if strParam == "type":
						strType = "ym-%s" % (strValue)
					elif strParam == "content":
						strContent = strValue
						if bEscape:
							strContent = html.escape(strContent)
					elif strParam == "query":
						strHRef += "?" + strValue
					else:
						strAttr += " %s=\"%s\"" % (strParam, strValue)
				self.append(
					"<a class=\"ym-button %s\" name=\"%s\" value=\"%s\" href=\"%s\" %s>%s</a>" % (
					strType, strName, strRef, strHRef, strAttr, strContent))
			self.append("</td>")
		self.append("</tr>")
		return
	
	# dictAct = {
	# 	"name" : {
	#		"value" : "",
	#		"title" : "",
	#		"content" : "",
	#		"type" : "primary|success|warning|danger",
	#	},
	# }
	def closeTableForm(self, dictAct = {}, bReset = True, bSave = False):
		self.extend([
			"</tbody>",
			"</table>",
			"</div>",
		])
		if self.m_bChk:
			self.extend([
				"<div class=\"ym-fbox-footer\">",
			])
			for (strName, dictParam) in sorted(dictAct.items()):
				strType = ""
				strContent = ""
				strAttr = ""
				for (strParam, strValue) in sorted(dictParam.items()):
					if strParam == "type":
						strType = "ym-%s" % (strValue)
					elif strParam == "content":
						strContent = strValue
					else:
						strAttr += " %s=\"%s\"" % (strParam, strValue)
				self.append(
					"<button class=\"%s\" name=\"submit\" value=\"%s\" type=\"submit\" style=\"margin-top:10px;\" %s>%s</button>"  % (
					strType, strName, strAttr, html.escape(strContent)))
			if bReset:
				self.append(
					"<button type=\"reset\" class=\"reset ym-delete ym-warning\" style=\"margin-top:10px;\">Zurücksetzen</button>")
			if bSave:
				self.append(
					"<button name=\"submit\" value=\"save\" type=\"submit\" class=\"save ym-save ym-success\" style=\"margin-top:10px;\">Speichern</button>")
			self.append("</div>")
		self.append("</form>")
		return
		
	def openTable(self, strCaption, lstHeader, bBorder = False, bCondensed = False):
		strClass = None
		if (bBorder):
			strClass = " class=\"bordertable"
		if (bCondensed):
			if (strClass):
				strClass += " narrow"
			else:
				strClass = " class=\"narrow"
		if (strClass):
			strClass += "\""
		else:
			strClass = ""
		self.extend([
			"<table%s>" % (strClass),
			"<caption>%s</caption>" % (html.escape(strCaption)),
			"<thead>",
			"<tr>",
		])
		for strHead in lstHeader:
			self.append("<th>%s</th>" % (html.escape(strHead)))
		self.extend([
			"</tr>",
			"</thead>",
			"<tbody>",
		])
		return
		
	def appendTable(self, lstData, bFirstIsHead=False, bEscape=True):
		self.extend([
			"<tr>",
		])
		for strData in lstData:
			if bEscape:
				strData = html.escape(strData)
			if bFirstIsHead:
				bFirstIsHead = False
				self.append("<th>%s</th>" % (strData))
			else:
				self.append("<td>%s</td>" % (strData))
		self.append("</tr>")
		return
		
	def appendHeader(self, lstData, bEscape=True):
		self.extend([
			"</tbody>",
			"<thead><tr>",
		])
		for strData in lstData:
			if bEscape:
				strData = html.escape(strData)
			self.append("<th>%s</th>" % (strData))
		self.extend([
			"</tr></thead>",
			"<tbody>"
		])
		return
		
	def closeTable(self):
		self.extend([
			"</tbody>",
			"</table>",
		])
		return
		
	def openForm(self,
		dictTargets={},	# {<name> : <value>}
		dictQueries={}	# {<name> : <value>}
		):
		self.m_strQueries = ""
		for (strName, strValue) in dictQueries.items():
			if self.m_strQueries:
				self.m_strQueries += "&"
			else:
				self.m_strQueries += "?"
			self.m_strQueries += "%s=%s" % (strName, strValue)
		self.append(
			"<form class=\"%s\" method=\"%s\" enctype=\"%s\" action=\"%s%s\">" % (
				"ym-form ym-full", "post", "multipart/form-data", self.m_strPath, self.m_strQueries))
		for (strName, strTarget) in dictTargets.items():
			self.append(
				"<input type=\"hidden\" name=\"%s\" value=\"%s\"/>" % (
					strName, strTarget))
		return
		
	def closeForm(self,
		dictButtons={},	# {name : (value, title, class)}
		strUrlCancel=None
		):
		if not strUrlCancel:
			strUrlCancel = self.m_strPath
		self.append("<div class=\"ym-fbox-footer\">")
		self.extend([
			"<a class=\"ym-button ym-primary\" href=\"%s%s\">Abbrechen</a>" % (
				strUrlCancel, self.m_strQueries),
			"<button type=\"reset\" class=\"reset ym-delete ym-warning\">Zurücksetzen</button>",
			"<button name=\"submit\" value=\"save\" type=\"submit\" class=\"save ym-save ym-success\">Speichern</button>",
			"</div>"
		])
		if dictButtons:
			self.append("<div class=\"ym-fbox-footer\">")
			for (strName, lstProps) in dictButtons.items():
				self.append(
					"<button name=\"%s\" value=\"%s\" type=\"submit\" class=\"%s\">%s</button>" % (
						strName, lstProps[0], lstProps[2], html.escape(lstProps[1])))
			self.append("</div>")
		return
		
	def appendForm(self, strName, strInput="", strTitle="", bSelected=False,
		dictChoice=None, nLines=None, bCheck=False, bRadio=False, bButton=False,
		strTip="", strClass="", strTextType="text", strTypePattern="",
		bEscape=True, bUseKeyAsValue=False):
		strSelected = ""
		if bEscape:
			if strTitle:
				strTitle = html.escape(strTitle)
			if strTip:
				strTip = html.escape(strTip)
		if dictChoice:
			if bCheck or bRadio:
				strType = "checkbox"
				if bRadio:
					strType = "radio"
					bSelected = False
				# Gruppe von Check- oder Radio-Boxen
				if strTitle:
					self.extend([
						"<fieldset>",
						"<legend>%s</legend>" % (strTitle)
					])
				self.append("<div class=\"ym-fbox-wrap\">")
				for (oName, oValue) in sorted(dictChoice.items()):
					if bEscape:
						oName = html.escape("%s" % (oName))
					if (type(oValue) is list or type(oValue) is tuple):
						self.append("<p>%s</p>" % (oName))
						for oItem in sorted(oValue):
							self.m_nId += 1
							if (bSelected or strInput == oItem):
								strSelected = "checked"
							else:
								strSelected = ""
							self.extend([
								"<div class=\"ym-fbox-check\">",
								"<input type=\"%s\" name=\"%s\" value=\"%s\" id=\"%s\" %s/>" % (
									strType, strName, oItem, self.m_nId, strSelected),
								"<label for=\"%s\">%s</label>" % (
									self.m_nId, html.escape(oItem)),
								"</div>"
							])
					else:
						self.m_nId += 1
						if (bSelected or strInput == oValue):
							strSelected = "checked"
						else:
							strSelected = ""
						self.extend([
							"<div class=\"ym-fbox-check\">",
							"<input type=\"%s\" name=\"%s\" value=\"%s\" id=\"%s\" %s/>" % (
								strType, strName, oValue, self.m_nId, strSelected),
							"<label for=\"%s\">%s</label>" % (
								self.m_nId, oName),
							"</div>"
						])
				self.append("</div>")
				if strTitle:
					self.append("</fieldset>")
			else:
				# Auswahlliste
				self.append("<div class=\"ym-fbox ym-fbox-select\">")
				nSize = 1
				if nLines:
					nSize = nLines
				if strTitle:
					self.m_nId += 1
					self.append(
						"<label for=\"%s\">%s</label>" % (
						self.m_nId, strTitle))
				self.append(
					"<select name=\"%s\" size=\"%s\" id=\"%s\">" % (
						strName, nSize, self.m_nId))
				for (oName, oValue) in sorted(dictChoice.items()):
					if bEscape:
						oName = html.escape(oName)
					self.m_nId += 1
					if (isinstance(oValue, dict)):
						self.append("<optgroup label=\"%s\">" % (oName))
						for (oName, oItem) in sorted(oValue.items()):
							if ((bUseKeyAsValue and strInput == oName) or
								(not bUseKeyAsValue and strInput == oItem)):
								strSelected = "selected=\"selected\""
							else:
								strSelected = ""
							if bUseKeyAsValue:
								oItem = oName
							if bEscape:
								oItem = html.escape(oItem)
							self.append(
								"<option value=\"%s\" %s>%s</option>" % (
									oItem, strSelected, oName))
						self.append("</optgroup>")
					else:
						if ((bUseKeyAsValue and strInput == oName) or
							(not bUseKeyAsValue and strInput == oValue)):
							strSelected = "selected=\"selected\""
						else:
							strSelected = ""
						if bUseKeyAsValue:
							oValue = oName
						if bEscape:
							oValue = html.escape(oValue)
						self.append(
							"<option value=\"%s\" %s>%s</option>" % (
								oValue, strSelected, oName))
				self.append("</select></div>")
		elif nLines:
			# Textarea
			self.append("<div class=\"ym-fbox ym-fbox-text\">")
			if strTitle:
				self.m_nId += 1
				self.append(
					"<label for=\"%s\">%s</label>" % (
					self.m_nId, strTitle))
			self.append(
				"<textarea id=\"%s\" rows=\"%s\" name=\"%s\">%s</textarea>" % (
				self.m_nId, nLines, strName, html.escape(strInput)))
			self.append("</div>")
		elif bCheck:
			# Einzelne Check-Box
			self.append("<div class=\"ym-fbox ym-fbox-check\">")
			if (bSelected):
				strSelected = "checked"
			else:
				strSelected = ""
			if not strTitle:
				strTitle = strInput
				if strTitle and bEscape:
					strTitle = html.escape(strTitle)
			self.m_nId += 1
			self.extend([
				"<input type=\"checkbox\" name=\"%s\" value=\"%s\" id=\"%s\" %s/>" % (
					strName, strInput, self.m_nId, strSelected),
				"<label for=\"%s\">%s</label>" % (
					self.m_nId, strTitle),
				"</div>"
			])
		elif bButton:
			# Submit-Button
			self.append("<div class=\"ym-fbox ym-fbox-button\">")
			self.append(
				"<button name=\"%s\" value=\"%s\" type=\"submit\" class=\"%s\">%s</button>" % (
					strName, strInput, strClass, strTitle))
			self.append("</div>")
		else:
			# Textfeld
			self.append("<div class=\"ym-fbox ym-fbox-text\">")
			self.m_nId += 1
			self.extend([
				"<label for=\"%s\">%s</label>" % (
					self.m_nId, strTitle),
				"<input type=\"%s\" name=\"%s\" value=\"%s\" id=\"%s\" %s placeholder=\"%s\"/>" % (
					strTextType, strName, strInput, self.m_nId, strTypePattern, html.escape(strInput)),
				"</div>"
			])
		return
		
	def createText(self, strText):
		self.extend([
			"<p>%s</p>" % (html.escape(strText))
		])
		return
	
	def createBox(self,
		strTitle,
		strMsg,
		strType="",	# info|error|warning|success
		bClose=True):
		
		self.extend([
			"<div class=\"box %s\">" % (strType),
			"<h3>%s</h3>" % (html.escape(strTitle)),
			"<p>%s</p>" % (html.escape(strMsg)),
		])
		if bClose:
			self.append(
				"<a class=\"ym-button\" href=\"%s\">OK</a>" % (
					self.m_strPath))
			self.append("</div>")
		return
		
	def createButton(self, strTitle, strHRef="", strClass=""):
		if not strHRef:
			strHRef = self.m_strPath
		self.append("<a class=\"ym-button %s\" style=\"margin-top:10px;\" href=\"%s\">%s</a>" % (
			strClass, strHRef, html.escape(strTitle)))
		return
		
	def closeBox(self):
		self.extend([
			"</div>",
		])
		return

class ModuleBase:
	def __init__(self, oWorker):
		self.m_oWorker = oWorker
		return
	
	def getWorker(self):
		return self.m_oWorker
		
	## Modulinitialisierung
	# @param self This-Pointer
	# @param dictModCfg Modulkonfiguration {<"Param"> : <Value>}
	# @param dictCfgUsr Konfigurationsbeschreibung {<"Param"> : {<"(title|description|default|choice)"> : <"Value"|{<"Choice"> : <"Value">}>}}
	def moduleInit(self, dictModCfg={}, dictCfgUsr={}):
		return True
		
	def moduleExit(self):
		return True
		
	def moduleExec(self, strPath, strCmd, strArg):
		return True

class QueueTask:
	
	def __init__(self, oWorker):
		self.m_oWorker = oWorker
		return
		
	def __str__(self):
		strDesc = "Ausführen einer Aufgabe"
		return  strDesc
	
	def do(self):
		return
		
	def done(self, bResult = True):
		return
		
class FastTask(QueueTask):
	
	def __str__(self):
		strDesc = "Ausführen einer leichten Aufgabe"
		return  strDesc
	
	def start(self):
		bResult = False
		Globs.dbg("'%s' (leicht) starten: Warten auf Freigabe" % (self))
		# >>> Critical Section
		self.m_oWorker.m_oLock.acquire()
		Globs.dbg("'%s' (leicht) starten: Freigabe erhalten" % (self))
		if (self.m_oWorker.m_evtRunning.isSet()):
			Globs.dbg("'%s' (leicht) starten: In Warteschlange" % (self))
			self.m_oWorker.m_oQueueFast.put(self)
			bResult = True
		else:
			Globs.wrn("'%s' (leicht) starten: Bearbeitung verweigert" % (self))
		self.m_oWorker.m_oLock.release()
		# <<< Critical Section
		Globs.dbg("'%s' (leicht) starten: Freigabe abgegeben (%r)" % (self, bResult))
		return bResult
		
	def done(self, bResult = True):
		Globs.dbg("'%s' (leicht): Bearbeitung abgeschlossen (%r)" % (self, bResult))
		self.m_oWorker.m_oQueueFast.task_done()
		return
		
class LongTask(QueueTask):
	
	def __str__(self):
		strDesc = "Ausführen einer schweren Aufgabe"
		return  strDesc
		
	def start(self):
		bResult = False
		Globs.dbg("'%s' (schwer) starten: Warten auf Freigabe" % (self))
		# >>> Critical Section
		self.m_oWorker.m_oLock.acquire()
		Globs.dbg("'%s' (schwer) starten: Freigabe erhalten" % (self))
		if (self.m_oWorker.m_evtRunning.isSet()):
			Globs.dbg("'%s' (schwer) starten: In Warteschlange" % (self))
			self.m_oWorker.m_oQueueLong.put(self)
			bResult = True
		else:
			Globs.wrn("'%s' (schwer) starten: Bearbeitung verweigert" % (self))
		self.m_oWorker.m_oLock.release()
		# <<< Critical Section
		Globs.dbg("'%s' (schwer) starten: Freigabe abgegeben (%r)" % (self, bResult))
		return bResult
		
	def done(self, bResult = True):
		Globs.dbg("'%s' (schwer): Bearbeitung abgeschlossen (%r)" % (self, bResult))
		self.m_oWorker.m_oQueueLong.task_done()
		return

class TaskSpeak(LongTask):
	
	s_oVoice = Voice("de-DE")
	
	def __init__(self, oWorker, strSpeak):
		super(TaskSpeak, self).__init__(oWorker)
		self.m_strSpeak = strSpeak
		return
		
	def __str__(self):
		strDesc = "Sprechen"
		return  strDesc
	
	def do(self):
		self.s_oVoice.speak(self.m_strSpeak)
		return

class TaskSound(LongTask):
	
	s_oSound = Sound()
	
	def __init__(self, oWorker, strSound, nLoops = 1):
		super(TaskSound, self).__init__(oWorker)
		self.m_strSound = strSound
		self.m_nLoops = nLoops
		return
		
	def __str__(self):
		strDesc = "Abspielen"
		return  strDesc
	
	def do(self):
		for i in range(self.m_nLoops):
			self.s_oSound.sound(self.m_strSound)
		return

class TaskSaveSettings(FastTask):
	
	def __str__(self):
		strDesc = "Speichern der Systemkonfiguration"
		return  strDesc
		
	def do(self):
		Globs.saveSettings()
		return
		
## 
#  @brief Weiterleitung von Modulereignissen an alle aktiven Module.
#  		
class TaskModuleEvt(FastTask):
	
	def __init__(self,
		oWorker,
		strPath,
		dictForm=None,
		dictQuery=None
		):
		super(TaskModuleEvt, self).__init__(oWorker)
		self.m_strPath = strPath
		self.m_dictForm = dictForm
		self.m_dictQuery = dictQuery
		return
		
	def __str__(self):
		strDesc = "Ausführen von Modulereignissen"
		return  strDesc
	
	def do(self):
		for (strName, oInstance) in self.m_oWorker.m_dictModules.items():
			self.m_oResult = oInstance.moduleExec(self.m_strPath,
				None, self.m_dictQuery, self.m_dictForm)
		return
		
class WebResponse:
	
	def __init__(self,
		nStatus,
		oReason,
		oHeader,
		oData
		):
		self.m_bOK = (nStatus == http.client.OK)
		self.m_nStatus = nStatus
		self.m_strReason = ("%s" % oReason)
		self.m_dictHeader = dict(oHeader)
		self.m_oData = oData
		return
		
	def __str__(self):
		strDesc = "Status=%s, Reason=%s, Headers=%s" % (
			self.m_nStatus, self.m_strReason, self.m_dictHeader)
		return  strDesc

class WebClient:
	
	def GET(self,
		strUrl,
		bFollowRedirects = True
		):
		
		lstRedirect = (
			http.client.MOVED_PERMANENTLY,
			http.client.FOUND,
			http.client.SEE_OTHER,
			http.client.TEMPORARY_REDIRECT)
		oConn = None
		oResp = None
		oUrlSplit = urllib.parse.urlsplit(strUrl)
		
		if (re.match("[Hh][Tt][Tt][Pp][Ss]", oUrlSplit.scheme)):
			oConn = http.client.HTTPSConnection(oUrlSplit.netloc)
		else:
			oConn = http.client.HTTPConnection(oUrlSplit.netloc)
		
		oConn.request("GET", strUrl)
		oResp = oConn.getresponse()
		
		if (oResp.status == http.client.OK):
			oWebResponse = WebResponse(
				nStatus=oResp.status,
				oReason=oResp.reason,
				oHeader=oResp.getheaders(),
				oData=oResp.read())
		elif (oResp.status in lstRedirect
			and oResp.getheader("Location")
			and bFollowRedirects):
			Globs.wrn("Weiterleitung von '%s' nach '%s'" % (
				strUrl, oResp.getheader("Location")))
			oWebResponse = self.GET(oResp.getheader("Location"))
		else:
			Globs.wrn("Fehler beim Abrufen von '%s' (Weiterleitung=%s, Location=%s)" % (
				strUrl, bFollowRedirects, oResp.getheader("Location")))
			oWebResponse = WebResponse(
				nStatus=oResp.status,
				oReason=oResp.reason,
				oHeader=oResp.getheaders(),
				oData=oResp.read())
				
		oConn.close()
		
		return oWebResponse
		
def getShellCmdOutput(strShellCmd):
	strOutput = ""
	strOutput = subprocess.check_output(
		strShellCmd,
		stderr = subprocess.STDOUT,
		shell = True,
		universal_newlines = True)
	return strOutput.splitlines()

# Return RAM information (unit=kb) in a list                                       
# Index 0: total RAM                                                               
# Index 1: used RAM                                                                 
# Index 2: free RAM  
# Index 3: shared RAM
# Index 4: buffered RAM
# Index 5: cached RAM
def getRamInfo():
	strRamInfo = "n/a"
	regexSep = r"\s\s*"
	parts = [[1, 7],]
	strRamInfo = subprocess.check_output(
		"free",
		stderr = subprocess.STDOUT,
		shell = True,
		universal_newlines = True)
	nLine = 0
	for strLine in strRamInfo.splitlines():
		nLine += 1
		if nLine == 2:
			return partList(re.split(regexSep, strLine), parts)

# Return information about disk space as a list (unit included)                     
# Index 0: total disk space                                                         
# Index 1: used disk space                                                         
# Index 2: remaining disk space                                                     
# Index 3: percentage of disk used                                                 
def getDiskSpace():
	strDiskSpace = "n/a"
	regexSep = r"\s\s*"
	parts = [[1, 5],]
	strDiskSpace = subprocess.check_output(
		"df -h",
		stderr = subprocess.STDOUT,
		shell = True,
		universal_newlines = True)
	nLine = 0
	for strLine in strDiskSpace.splitlines():
		nLine += 1
		if nLine == 2:
			return partList(re.split(regexSep, strLine), parts)

# Return current CPU temperature in °C as a floating point value.
# In case of an error a value of -273.15 is returned
def getCpuTemp():
	fResult = 273.15
	fResult *= -1
	regexSep = r"[\=\']"
	parts = [[1, 2],]
	strResult = subprocess.check_output(
		"vcgencmd measure_temp",
		stderr = subprocess.STDOUT,
		shell = True,
		universal_newlines = True)
	temp = partList(re.split(regexSep, strResult), parts)[0]
	fResult = float(temp)
	return fResult

# Return current CPU usage in percent as a string value
def getCpuUse():
	strResult = "n/a"
	strResult = subprocess.check_output(
		"top -b -n1 | awk '/Cpu\(s\):/ {print $2}'",
		stderr = subprocess.STDOUT,
		shell = True,
		universal_newlines = True)
	return strResult
	
# Liefert die aktuelle IP-Adresse zurück
def getNetworkInfo(strComputerName="google.com"):
	strIpAddr = ""
	try:
		oSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		oSocket.connect((strComputerName, 0))
		strIpAddr = oSocket.getsockname()[0]
		oSocket.close()
	except:
		Globs.exc("Ermitteln der IP-Adresse")
	return strIpAddr
	
def setDate(strDate, strFormat):
	strResult = ""
	oDate = datetime.strptime(strDate, strFormat).date()
	oTime = datetime.today().time()
	oDateTime = datetime.combine(oDate, oTime)
	return setDateTime(oDateTime)

def setTime(strTime, strFormat):
	strResult = ""
	oDate = datetime.today().date()
	oTime = datetime.strptime(strTime, strFormat).time()
	oDateTime = datetime.combine(oDate, oTime)
	return setDateTime(oDateTime)

def setDateTime(oDateTime):
	strResult = ""
	strResult = subprocess.check_output(
		"sudo date -s \"%s\"" % (oDateTime.strftime("%c")),
		stderr = subprocess.STDOUT,
		shell = True,
		universal_newlines = True)
	return strResult

# Extracts partitions from the given list and returns them as a new list
def partList(list, indices):
	output = []
	for nStart, nStop in indices:
		output.extend(list[nStart:nStop])
	return output
		