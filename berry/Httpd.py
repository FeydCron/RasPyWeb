import cgi
import os
import subprocess
import re
import threading
import traceback
import uuid
import html
import zipfile

from http.server import BaseHTTPRequestHandler
from http.server import SimpleHTTPRequestHandler
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
from urllib.parse import parse_qsl
from datetime import datetime
from collections import OrderedDict
from zipfile import ZipFile

from Sound import Sound
from Globs import Globs
from Worker import TaskModuleInit

import SDK
from SDK import TaskSpeak
from SDK import TaskSound
from SDK import FastTask
from SDK import LongTask
from SDK import HtmlPage
from SDK import TaskModuleEvt
from SDK import TaskSaveSettings

from Worker import FutureTask
from Worker import TaskExit

g_oHttpdWorker = None
	
# {<name> : <Section>}
class StartPage(OrderedDict):

	def writeToPage(self,
		oHtmlPage,		# HTML-Seite, in welche zu schreiben ist
		bEdit=False,	# True, um die Startseite zu editieren
		secEdt="",		# Name der zu editierenden Sektion
		artEdt="",		# Name des zu editierenden Artikels
		btnEdt=""		# Name des zu editierenden Buttons
		):
		
		Globs.dbg(
			"StartPage::writeToPage(bEdit=%r, secEdt=\"%s\", artEdt=\"%s\", btnEdt=\"%s\")" % (
			bEdit, secEdt, artEdt, btnEdt))
		
		if bEdit:
			self.editStartPage(oHtmlPage)
			return
		if self.editTarget(oHtmlPage, secEdt, artEdt, btnEdt):
			return
		bIsEmpty = True
		for (strSecName, oSection) in self.items():
			bSecEdt = (strSecName == secEdt)
			oSection.writeToPage(oHtmlPage)
			bIsEmpty = False
			
		if bIsEmpty:
			oHtmlPage.append(
				"<p class=\"center\"><a href=\"%s?edit=startpage\">&#x1F527; Die Startseite ist noch leer. Jetzt bearbeiten.</a></p>" % (
				Globs.s_strStartPageUrl))
		return
		
	def editStartPage(self,
		oHtmlPage
		):
		oHtmlPage.createBox("Startseite bearbeiten",
			"Ein Element aus der Strukturansicht auswählen und bearbeiten " +
			"oder ein neues Element hinzufügen.", bClose=False)
		oHtmlPage.extend([
			"<div class=\"nav-wrapper\">",
			"<nav class=\"ym-vlist\">",
			"<h6 class=\"ym-vtitle\">Strukturansicht</h6>"
		])
		oHtmlPage.append("<ul>")
		for (strSecName, oSection) in self.items():
			strType = "Nebenaufgaben"
			if oSection.m_bPrimary:
				strType = "Hauptaufgaben"
			oHtmlPage.append(
				"<li><a href=\"%s?secEdt=%s\">%s Abschnitt \"%s\"</a>" % (
					Globs.s_strStartPageUrl, strSecName, "&#x0270E;", strType))
			oHtmlPage.append("<ul>")
			for (strArtName, oArticle) in oSection.items():
				oHtmlPage.append(
					"<li><a href=\"%s?sec=%s&artEdt=%s\">%s Aufgabe \"%s\"</a></li>" % (
						Globs.s_strStartPageUrl, strSecName, strArtName, "&#x0270E;", oArticle.m_strTitle))
			oHtmlPage.append(
				"<li><a href=\"%s?sec=%s&artAdd=%s\">%s Neue Aufgabe erstellen</a></li>" % (
					Globs.s_strStartPageUrl, strSecName, uuid.uuid1().hex, "&#x0271A;"))
			oHtmlPage.append("</ul>")
			oHtmlPage.append("</li>")
		oHtmlPage.append(
			"<li><a href=\"%s?secAdd=%s\">%s Neuen Abschnitt anlegen</a></li>" % (
				Globs.s_strStartPageUrl, uuid.uuid1().hex, "&#x0271A;"))
		oHtmlPage.extend([
			"</ul>",
			"</nav>",
			"</div>"
		])
		oHtmlPage.createButton("Fertig", strClass="ym-save")
		oHtmlPage.closeBox()
		return
		
	def editTarget(self,
		oHtmlPage,
		secEdt,		# Name der zu editierenden Sektion
		artEdt,		# Name des zu editierenden Artikels
		btnEdt		# Name des zu editierenden Buttons
		):
		# Targets vorbereiten
		dictTargets = {}
		dictQueries = {}
		dictButtons = {}
		oSection = None
		oArticle = None
		oButton = None
		oTarget = None
		# Bearbeitungshierarchie prüfen
		if secEdt and secEdt in self:
			oSection = self[secEdt]
			dictTargets.update({"sec" 	: secEdt})
		if artEdt and oSection and artEdt in oSection:
			oArticle = oSection[artEdt]
			dictTargets.update({"art" 	: artEdt})
		if btnEdt and oArticle and btnEdt in oArticle:
			oButton = oArticle[btnEdt]
			dictTargets.update({"btn" 	: btnEdt})
			dictQueries.update({
				"sec" 		: oSection.m_strName,
				"artEdt" 	: oArticle.m_strName
				})
		# Target identifizieren
		if oButton != None:
			oHtmlPage.createBox("Schaltfläche",
				"Schaltfläche bearbeiten", bClose=False)
			oTarget = oButton
			dictButtons.update({
				"del" : ["btn", "Schaltfläche löschen", "ym-delete ym-danger"]
			})
		elif oArticle != None:
			dictQueries.update({"edit" 	: "startpage"})
			oHtmlPage.createBox("Aufgabe",
				"Aufgabe bearbeiten", bClose=False)
			oTarget = oArticle
			dictButtons.update({
				"del" 		: ["art", "Aufgabe löschen", "ym-delete ym-danger"],
				"btnAdd"	: [uuid.uuid1().hex, "Neue Schaltfläche", "ym-add"]
			})
		elif oSection != None:
			dictQueries.update({"edit" 	: "startpage"})
			oHtmlPage.createBox("Abschnitt",
				"Abschnitt bearbeiten", bClose=False)
			oTarget = oSection
			dictButtons.update({
				"del" : ["sec", "Abschnitt löschen", "ym-delete ym-danger"]
			})
		
		Globs.dbg(
			"StartPage::editTarget(secEdt=%r, artEdt=%r, btnEdt=%r): oTarget=%r, oSection=%r, oArticle=%r, oButton=%r, dictTargets=%r, dictQueries=%r, StartPage=%r" % (
			secEdt, artEdt, btnEdt, oTarget, oSection, oArticle, oButton, dictTargets, dictQueries, Globs.s_oStartPage))		
		
		# Target bearbeiten
		if oTarget != None:
			oHtmlPage.openForm(
				dictTargets=dictTargets,
				dictQueries=dictQueries)
			oTarget.writeToPage(oHtmlPage, bEdit=True)
			oHtmlPage.closeForm(dictButtons=dictButtons)
			oHtmlPage.closeBox()
			return True
		return False

# {<name> : <Article>}
class Section(OrderedDict):

	def setSection(self,
		strName,
		bPrimary=True
		):
		self.m_strName = strName
		self.m_bPrimary = bPrimary
		return
	
	def writeToPage(self,
		oHtmlPage,		# HTML-Seite, in welche zu schreiben ist
		bEdit=False		# True, um den Aufgabentyp zu editieren
		):
		if bEdit:
			oHtmlPage.appendForm("secPrimary", strInput="primary",
				strTitle="Hauptaufgaben", bCheck=True,
				bSelected=self.m_bPrimary)
			return
		strClass = "" # Alternating "ym-gl" and "ym-gr"
		if self.m_bPrimary:
			oHtmlPage.append("<section>")
		else:
			oHtmlPage.append("<section class=\"ym-grid linearize-level-2\">")
		for (strArtName, oArticle) in self.items():
			bIsEmpty = False
			if self.m_bPrimary:
				oHtmlPage.append(
					"<article>")
			else:
				if strClass == "ym-gl":
					strClass = "ym-gr"
				else:
					strClass = "ym-gl"
				oHtmlPage.extend([
					"<article class=\"ym-g50 %s\">" % (strClass),
					"<div class=\"ym-gbox\">"])
			oArticle.writeToPage(oHtmlPage)
			if self.m_bPrimary:
				oHtmlPage.append("</article>")
			else:
				oHtmlPage.extend([
					"</div>",
					"</article>"
				])
		oHtmlPage.append("</section>")
		return

# {<name> : <Button>}		
class Article(OrderedDict):

	def setArticle(self,
		strName,
		strTitle="",
		strMsg="",
		strType=""
		):
		self.m_strName = strName
		self.m_strTitle = strTitle
		self.m_strMsg = strMsg
		self.m_strType = strType
		return

	def writeToPage(self,
		oHtmlPage,		# HTML-Seite, in welche zu schreiben ist
		bEdit=False		# True, um den Artikel zu editieren
		):
		if bEdit:
			oHtmlPage.appendForm("artTitle",
				strInput=self.m_strTitle, strTitle="Titelzeile")
			oHtmlPage.appendForm("artContent",
				strInput=self.m_strMsg, strTitle="Inhalt", nLines=3)
			oHtmlPage.appendForm("artType",
				strInput=self.m_strType, strTitle="Hintergrund", dictChoice = {
					"Grün" 		: "success",
					"Rot" 		: "error",
					"Gelb" 		: "warning",
					"Info" 		: "info",
					"Neutral"	: ""})
			oHtmlPage.append("<div class=\"ym-fbox\"><span class=\"ym-label\">Schaltflächen bearbeiten</span></div>")
			for (btnName, oButton) in self.items():
				oHtmlPage.appendForm("btnEdt",
					strInput=btnName,
					strTitle=(oButton.m_strTitle),
					bButton=True,
					strClass=("%s %s" % (oButton.m_strIcon, oButton.m_strColor)))
		else:
			oHtmlPage.createBox(self.m_strTitle, self.m_strMsg,
				strType=self.m_strType, bClose = False)
			for (btnName, oButton) in self.items():
				oButton.writeToPage(oHtmlPage)
			oHtmlPage.closeBox()
		return
		
class Button:

	def setButton(self,
		strName,
		strTitle="Ohne Titel",
		strHRef="",
		strIcon="",
		strColor="",
		strRedirect="startpage"
		):
		self.m_strName = strName
		self.m_strTitle = strTitle
		self.m_strHRef = strHRef
		self.m_strIcon = strIcon
		self.m_strColor = strColor
		self.m_strRedirect = strRedirect
		return
		
	def writeToPage(self,
		oHtmlPage,		# HTML-Seite, in welche zu schreiben ist
		bEdit=False		# True, um die Schaltfläche zu editieren
		):
		if bEdit:
			oHtmlPage.appendForm("btnTitle",
				strInput=self.m_strTitle, strTitle="Titel der Schaltfläche")
			oHtmlPage.appendForm("btnHRef",
				strInput=self.m_strHRef, strTitle="URL mit Abfrage")
			oHtmlPage.appendForm("btnRedirect",
				strInput=self.m_strRedirect,
				strTitle="Zu dieser Seite navigieren",
				bUseKeyAsValue=True,
				bEscape=True,
				dictChoice = Globs.s_dictSettings["Redirects"])
			oHtmlPage.appendForm("btnIcon",
				strInput=self.m_strIcon,
				strTitle="Icon",
				bEscape=False,
				dictChoice = {
					"" : "",
					"&#x1F6AB; Verboten" 				: "ym-forbid",
					"&#x1F197; OK" 						: "ym-ok",
					"&#x026D4; Gesperrt" 				: "ym-noentry",
					"&#x02705; Check" 					: "ym-check",
					"&#x1F501; Aktualisieren" 			: "ym-refresh",
					"&#x1F502; Aktualisieren einmal"	: "ym-refresh1",
					"&#x1F500; Austauschen" 			: "ym-exchange",
					"&#x1F6AE; Abfall" 					: "ym-trash",
					"&#x1F50A; Lautstärke laut" 		: "ym-volumemax",
					"&#x1F509; Lautstärke mittel" 		: "ym-volumemid",
					"&#x1F508; Lautstärke leise" 		: "ym-volumemin",
					"&#x1F507; Lautstärke aus" 			: "ym-volumeoff",
					"&#x1F514; Alarm" 					: "ym-bell",
					"&#x1F515; Alarm aus" 				: "ym-belloff",
					"&#x1F50D; Details" 				: "ym-details",
					"&#x1F506; Helligkeit max" 			: "ym-brightmax",
					"&#x1F505; Helligkeit min" 			: "ym-brightmin",
					"&#x1F527; Schraubenschlüssel" 		: "ym-wrench",
					"&#x1F4E5; Posteingang" 			: "ym-inbox",
					"&#x1F4E4; Postausgang" 			: "ym-outbox",
					"&#x1F4C4; Seite" 					: "ym-page",
					"&#x1F4C3; Seite gerollt" 			: "ym-curl",
					"&#x1F4DC; Schriftrolle" 			: "ym-scroll",
					"&#x1F4C5; Kalender" 				: "ym-calendar",
					"&#x1F345; Tomate" 					: "ym-tomato",
					"&#x1F34C; Banane" 					: "ym-banana",
					"&#x1F350; Birne" 					: "ym-pear",
					"&#x1F351; Pfirsicht" 				: "ym-peach",
					"&#x1F353; Erdbeere" 				: "ym-strawberry",
					"&#x1F347; Grapefruit" 				: "ym-grapes",
					"&#x1F352; Kirschen" 				: "ym-cherries",
					"&#x1F34B; Lemone" 					: "ym-lemon",
					"&#x1F34E; Apfel rot" 				: "ym-redapple",
					"&#x1F34F; Apfel grün" 				: "ym-greenapple",
					"&#x1F4A4; Schlafen" 				: "ym-sleep",
					"&#x0271A; Hinzufügen" 				: "ym-add",
					"&#x02718; Entfernen" 				: "ym-delete",
					"&#x02715; Schließen" 				: "ym-close",
					"&#x0270E; Ändern" 					: "ym-edit",
					"&#x02709; E-Mail" 					: "ym-email",
					"&#x02764; Herz" 					: "ym-like",
					"&#x0279C; Weiter" 					: "ym-next",
					"&#x025B6; Abspielen" 				: "ym-play",
					"&#x027A5; Antworten" 				: "ym-reply",
					"&#x02714; Speichern" 				: "ym-save",
					"&#x0270D; Unterschreiben" 			: "ym-sign",
					"&#x02737; Funken" 					: "ym-spark",
					"&#x02706; Telefon" 				: "ym-support",
					"&#x02605; Stern" 					: "ym-star",
					"&#x026A0; Warnzeichen" 			: "ym-warnsign",
					"&#x0270B; Hand (Stop)" 			: "ym-handstop"})
			oHtmlPage.appendForm("btnColor",
				strInput=self.m_strColor, strTitle="Farbe", dictChoice = {
					"Grün" 		: "ym-success",
					"Rot" 		: "ym-danger",
					"Gelb" 		: "ym-warning",
					"Blau" 		: "ym-primary",
					"Neutral"	: ""})
		else:
			strRedirect = ""
			if "?" in self.m_strHRef:
				strRedirect = "&redirect2="
			else:
				strRedirect = "?redirect2="
			strRedirect += self.m_strRedirect
			oHtmlPage.createButton(
				self.m_strTitle,
				"%s%s" % (self.m_strHRef, strRedirect),
				"%s %s" % (self.m_strIcon, self.m_strColor))
		return
		
class TaskModuleCmd(FutureTask):
	
	def __init__(self,
		oWorker,
		strPath,
		oHtmlPage,
		dictForm=None,
		dictQuery=None
		):
		super(TaskModuleCmd, self).__init__(oWorker)
		self.m_strPath = strPath
		self.m_dictForm = dictForm
		self.m_dictQuery = dictQuery
		self.m_oHtmlPage = oHtmlPage
		return
		
	def __str__(self):
		strDesc = "Ausführen von Modulkommandos"
		return  strDesc
	
	def do(self):
		for (strName, oInstance) in self.m_oWorker.m_dictModules.items():
			if (re.match("/modules/%s\\..+" % (strName), self.m_strPath)):
				self.m_oResult = oInstance.moduleExec(self.m_strPath,
					self.m_oHtmlPage, self.m_dictQuery, self.m_dictForm)
				return
		return
		
class TaskInstallModule(FastTask):
	
	def __init__(self, oWorker, strComponent, strName):
		super(TaskInstallModule, self).__init__(oWorker)
		self.m_strComponent = strComponent
		self.m_strName = strName
		return
		
	def __str__(self):
		strDesc = "Installieren des Moduls %s mit der Hauptklasse %s" % (
			self.m_strComponent, self.m_strName)
		return  strDesc
	
	def do(self):
		Globs.s_dictSettings["dictModules"].update({self.m_strComponent : self.m_strName})
		return
		
class TaskRemoveModule(FastTask):
	
	def __init__(self, oWorker, strComponent):
		super(TaskRemoveModule, self).__init__(oWorker)
		self.m_strComponent = strComponent
		return
	
	def __str__(self):
		strDesc = "Entfernen des Moduls %s" % (self.m_strComponent)
		return  strDesc
	
	def do(self):
		if self.m_strComponent in Globs.s_dictSettings["listInactiveModules"]:
			Globs.s_dictSettings["listInactiveModules"].remove(self.m_strComponent)
		if self.m_strComponent in Globs.s_dictSettings["dictModules"]:
			Globs.s_dictSettings["dictModules"].pop(self.m_strComponent)
		return
		
class TaskEnableModule(FastTask):
	
	def __init__(self, oWorker, strComponent, bEnable):
		super(TaskEnableModule, self).__init__(oWorker)
		self.m_strComponent = strComponent
		self.m_bEnable = bEnable
		return
		
	def __str__(self):
		strDesc = ""
		if self.m_bEnable:
			strDesc += "Einschalten"
		else:
			strDesc += "Ausschalten"
		strDesc += " des Moduls %s" % (self.m_strComponent)
		return  strDesc
	
	def do(self):
		if self.m_bEnable:
			if self.m_strComponent in Globs.s_dictSettings["listInactiveModules"]:
				Globs.s_dictSettings["listInactiveModules"].remove(self.m_strComponent)
				Globs.saveSettings()
		elif self.m_strComponent not in Globs.s_dictSettings["listInactiveModules"]:
				Globs.s_dictSettings["listInactiveModules"].append(self.m_strComponent)
				Globs.saveSettings()
		return
		
class TaskDisplayModules(FutureTask):
	
	def __init__(self, oWorker, oHtmlPage, dictQuery=None):
		super(TaskDisplayModules, self).__init__(oWorker)
		self.m_oHtmlPage = oHtmlPage
		self.m_dictQuery = dictQuery
		self.m_oTargetEdit = None
		return
		
	def __str__(self):
		strDesc = ""
		if self.m_oTargetEdit:
			strDesc += "Ändern"
		else:
			strDesc += "Darstellen"
		strDesc += " der Modulkonfiguration"
		return  strDesc
		
	def do(self):
		self.m_oTargetEdit = None
		
		if self.m_dictQuery and "edit" in self.m_dictQuery:
			self.m_oTargetEdit = self.m_dictQuery["edit"][0]
		
		if self.m_oTargetEdit and self.m_oTargetEdit in Globs.s_dictSettings["dictModules"]:
			self.createForm()
		else:
			self.displayModules()
		return
		
	def createForm(self):
		self.m_oHtmlPage.createBox(
			"Moduleinstellungen %s" % (self.m_oTargetEdit),
			"Der Name der Hauptklasse kann hier geändert werden.",
			bClose = False)
		self.m_oHtmlPage.openForm(dictTargets={"target" : "%s" % (self.m_oTargetEdit)})
		self.m_oHtmlPage.appendForm(
			"ModuleClass",
			strInput = Globs.s_dictSettings["dictModules"][self.m_oTargetEdit],
			strTitle = "Hauptklasse")
		self.m_oHtmlPage.closeForm()
		self.m_oHtmlPage.closeBox()
		return
		
	def displayModules(self):
		self.m_oHtmlPage.openTableForm(
			"Installierte Module",
			["Modul"],
			strChk = "Auswahl", strAct = "Status/Aktion")
		for (strComponent, strName) in sorted(Globs.s_dictSettings["dictModules"].items()):
			strStatus = "primary"
			strContent = "N/A"
			if strComponent in Globs.s_dictSettings["listInactiveModules"]:
				strStatus = "warning ym-forbid"
				strContent = "Ausgeschaltet"
			elif strComponent not in self.m_oWorker.m_dictModules:
				strStatus = "danger ym-noentry"
				strContent = "Fehlerhaft"
			else:
				strStatus = "success ym-play"
				strContent = "Eingeschaltet"
			self.m_oHtmlPage.appendTableForm(
				strComponent,
				["%s (%s)" % (strComponent, strName)],
				bChk = False, dictAct = {
					"edit" : {
						"type" 		: "%s ym-xsmall" % (strStatus),
						"content" 	: strContent,
						"title" 	: "Installationseinstellungen ändern",
						"query"		: "edit=%s" % (strComponent)
					}
				}, bEscape=False) 
		self.m_oHtmlPage.closeTableForm(
			dictAct = {
				"disable" : {
					"type" 		: "forbid ym-warning",
					"content" 	: "Ausschalten",
					"title" 	: "Alle ausgewählten Module ausschalten",
				},
				"enable" : {
					"type" 		: "play ym-success",
					"content" 	: "Einschalten",
					"title" 	: "Alle ausgewählten Module einschalten",
				},
				"delete" : {
					"type" 		: "close ym-danger",
					"content" 	: "Löschen",
					"title" 	: "Alle ausgewählten Module entfernen",
				}
			})
		return
		
class TaskDisplaySystem(FutureTask):
	
	def __init__(self, oWorker, oHtmlPage, dictForm=None, dictQuery=None):
		super(TaskDisplaySystem, self).__init__(oWorker)
		self.m_oHtmlPage = oHtmlPage
		self.m_dictForm = dictForm
		self.m_dictQuery = dictQuery
		self.m_strFxn = ""
		self.m_strArg = ""
		return
		
	def __str__(self):
		strDesc = "Darstellen der Systemwerte"
		return  strDesc
		
	def do(self):
		self.m_strFxn = ""
		self.m_strArg = ""
		
		self.m_oHtmlPage.setTitle("Systemwerte")
		
		if self.m_dictQuery:
			for strVal in ("edit", "date", "time"):
				if strVal in self.m_dictQuery:
					self.m_strFxn = "%s" % (strVal)
					self.m_strArg = self.m_dictQuery[self.m_strFxn][0]
					break;		
			if (self.m_strFxn
				and self.m_strFxn == "edit"
				and self.m_strArg):
				if self.createForm():
					return
					
		if self.m_dictForm:
			if "target" in self.m_dictForm:
				self.m_strFxn = self.m_dictForm["target"][0]
			if self.m_strFxn and self.m_strFxn in self.m_dictForm:
				self.m_strArg = self.m_dictForm[self.m_strFxn][0]
				
		if (self.m_strFxn and self.m_strArg):
			if not self.updateValue():
				return
				
		self.displayValues()
		return
		
	def displayValues(self):
		dt = datetime.today()
		# Tabelle öffnen und Systeminformationen eintragen
		self.m_oHtmlPage.openTable(
			"Aktuelle Systemwerte",
			["System", ""], True, True)
		self.m_oHtmlPage.appendTable([
			"Datum", "<a href=\"%s\">&#x0270E; %s</a>" % (
				"/system/values.html?edit=date",
				dt.strftime("%d.%m.%Y"))],
				bFirstIsHead=True, bEscape=False)
		self.m_oHtmlPage.appendTable([
			"Uhrzeit", "<a href=\"%s\">&#x0270E; %s</a>" % (
				"/system/values.html?edit=time",
				dt.strftime("%H:%M:%S"))],
				bFirstIsHead=True, bEscape=False)
		# Alle Sektionen durchgehen
		for (strHeader, dictSection) in sorted(Globs.s_dictSystemValues.items()):
			# Tabelle mit dem nächsten Tabellenkopf fortsetzen
			self.m_oHtmlPage.appendHeader([strHeader, ""])
			# Alle Werte durchgehen
			for (strName, strValue) in sorted(dictSection.items()):
				self.m_oHtmlPage.appendTable(
					[strName, strValue],
					bFirstIsHead=True)
		# Tabelle schließen
		self.m_oHtmlPage.closeTable()
		self.m_oHtmlPage.setAutoRefresh(10)
		return
		
	def createForm(self):
		dt = datetime.today()
		varVal = None
		strTitle = self.m_strArg
		if self.m_strArg == "date":
			varVal = "%s" % (dt.strftime("%Y-%m-%d"))
			strTitle = "Datum"
			self.m_oHtmlPage.createBox(
				strTitle,
				"Das Datum kann unabhängig von der Uhrzeit eingestellt werden, wobei " +
				"die Angabe im Format YYYY.MM.DD (Jahr, Monat, Tag, z.B. %s) erwartet wird." % (varVal),
				bClose=False)
		elif self.m_strArg == "time":
			varVal = "%s" % (dt.strftime("%H:%M:%S"))
			strTitle = "Uhrzeit"
			self.m_oHtmlPage.createBox(
				strTitle,
				"Die Uhrzeit kann unabhängig vom Datum eingestellt werden, wobei " +
				"die Angabe im Format HH:MM:SS (Stunde, Minute, Sekunde, z.B. %s) erwartet wird." % (varVal),
				bClose=False)
		else:
			return False
		
		self.m_oHtmlPage.openForm(dictTargets={"target" : self.m_strArg})
		self.m_oHtmlPage.appendForm(self.m_strArg,
			strInput="%s" % (varVal),
			strTitle=strTitle, strTextType=self.m_strArg)	
		self.m_oHtmlPage.closeForm()
		self.m_oHtmlPage.closeBox()
		return True
		
	def updateValue(self):
		strResult = ""
		if (self.m_strFxn == "date"):
			try:
				strResult = SDK.setDate(self.m_strArg, "%d.%m.%Y")
				self.m_oHtmlPage.createBox("Datum",
					"Das Datum \"%s\" wurde übernommen und mit folgendem Ergebnis angewendet: %s" % (
						self.m_strArg, strResult))
				return False
			except Exception as ex:
				strResult = " %s" % (ex)
				Globs.wrn("Datum einstellen: %s" % (strResult))
			try:
				strResult = SDK.setDate(self.m_strArg, "%Y-%m-%d")
				self.m_oHtmlPage.createBox("Datum",
					"Das Datum \"%s\" wurde übernommen und mit folgendem Ergebnis angewendet: %s" % (
						self.m_strArg, strResult))
				return False
			except Exception as ex:
				Globs.exc("Datum einstellen")
				strResult = " %s" % (ex)
		elif (self.m_strFxn == "time"):
			try:
				strResult = SDK.setTime(self.m_strArg, "%H:%M:%S")
				self.m_oHtmlPage.createBox("Uhrzeit",
					"Die Uhrzeit \"%s\" wurde übernommen und mit folgendem Ergebnis angewendet: %s" % (
						self.m_strArg, strResult))
				return False
			except Exception as ex:
				Globs.exc("Uhrzeit einstellen")
				strResult = " %s" % (ex)
		self.m_oHtmlPage.createBox(self.m_strFxn,
			"Die Einstellung \"%s\" konnte nicht auf den Wert \"%s\" geändert werden.%s" % (
			self.m_strFxn, self.m_strArg, strResult),
			strType="warning")
		return False
		
class TaskDisplaySettings(FutureTask):
	
	def __init__(self, oWorker, oHtmlPage, dictForm=None, dictQuery=None):
		super(TaskDisplaySettings, self).__init__(oWorker)
		self.m_oHtmlPage = oHtmlPage
		self.m_dictForm = dictForm
		self.m_dictQuery = dictQuery
		self.m_strFxn = ""
		self.m_strVal = ""
		self.m_strKey = ""
		return
		
	def __str__(self):
		strDesc = "Darstellen der Konfiguration"
		return  strDesc
		
	def do(self):
		self.m_strFxn = ""
		self.m_strVal = ""
		self.m_strKey = ""
		
		self.m_oHtmlPage.setTitle("Konfigurationseinstellungen")
		
		if (self.m_dictQuery
			and "edit" in self.m_dictQuery
			and "key" in self.m_dictQuery):
			self.m_strFxn = "edit"
			self.m_strVal = self.m_dictQuery[self.m_strFxn][0]
			self.m_strKey = self.m_dictQuery["key"][0]
			if self.createForm():
				return
				
		if (self.m_dictForm
			and "target" in self.m_dictForm
			and "key" in self.m_dictForm):
			self.m_strFxn = self.m_dictForm["target"][0]
			self.m_strKey = self.m_dictForm["key"][0]
			self.m_strVal = ""
			if self.m_strFxn in self.m_dictForm:
				self.m_strVal = self.m_dictForm[self.m_strFxn][0]
				if not self.updateValue():
					return
			
		self.displayValues()
		return
		
	def displayValues(self):
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		try:
			bOpened = False
			for (strKey, dictValues) in Globs.s_dictUserSettings.items():
				
				if (strKey not in Globs.s_dictSettings or not Globs.s_dictSettings[strKey]):
					continue
				if (strKey not in ("System") and strKey not in Globs.s_dictSettings["dictModules"]):
					continue
				if (strKey in Globs.s_dictSettings["listInactiveModules"]):
					continue
				
				if bOpened:
					self.m_oHtmlPage.appendHeader([strKey, ""])
				else:
					bOpened = True
					self.m_oHtmlPage.openTable("Konfigurationseinstellungen",
						[strKey, ""], True, True)
				for (strValueName, dictProperties) in sorted(dictValues.items()):
					if strValueName in Globs.s_dictSettings[strKey]:
						strTitle = strValueName
						if ("title" in dictProperties):
							strTitle = dictProperties["title"]
						if ("readonly" in dictProperties and dictProperties["readonly"]):
							self.m_oHtmlPage.appendTable([
								strTitle,
								"%s" % (Globs.s_dictSettings[strKey][strValueName])
								], bFirstIsHead=True, bEscape=False)
						elif ("showlink" in dictProperties and dictProperties["showlink"]
							and "description" in dictProperties
							and dictProperties["description"]):
							self.m_oHtmlPage.appendTable([
								strTitle,
								"<a href=\"%s\">&#x027A5; %s</a>" % (
									Globs.s_dictSettings[strKey][strValueName],
									dictProperties["description"])
								], bFirstIsHead=True, bEscape=False)
						else:
							self.m_oHtmlPage.appendTable([
								strTitle,
								"<a href=\"%s?edit=%s&key=%s\">&#x0270E; %s</a>" % (
									"/system/settings.html", strValueName, strKey,
									Globs.s_dictSettings[strKey][strValueName])
								], bFirstIsHead=True, bEscape=False)
			if bOpened:
				self.m_oHtmlPage.closeTable()
		except:
			Globs.exc("Darstellen der Konfiguration")
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		return
		
	def createForm(self):
		dictValue = None
		dictProperties = None
		dictChoices = {}
		strTitle = self.m_strVal
		strDesc = ""
		strDefault = ""
		varVal = None
		bUseKeyAsValue = False
		# >>> Critical Section
		Globs.s_oSettingsLock.acquire()
		try:
			if (self.m_strKey in Globs.s_dictUserSettings
				and self.m_strKey in Globs.s_dictSettings
				and self.m_strVal in Globs.s_dictSettings[self.m_strKey]
				and self.m_strKey not in (
				"dictModules", "listInactiveModules", "Redirects")):
				dictValues = Globs.s_dictUserSettings[self.m_strKey]
				varVal = Globs.s_dictSettings[self.m_strKey][self.m_strVal]
				strDefault = "%s" % (varVal)
			if dictValues and self.m_strVal in dictValues:
				dictProperties = dictValues[self.m_strVal]
			if dictProperties:
				if "title" in dictProperties:
					strTitle = dictProperties["title"]
				if "description" in dictProperties:
					strDesc = dictProperties["description"]
				if "default" in dictProperties:
					strDefault = dictProperties["default"]
				if "choices" in dictProperties:
					dictChoices = dictProperties["choices"]
				if "keyIsValue" in dictProperties:
					bUseKeyAsValue = dictProperties["keyIsValue"]
		except:
			Globs.exc("Ändern der Konfiguration")
			varVal = None
		Globs.s_oSettingsLock.release()
		# <<< Critical Section
		if varVal == None:
			return False
		if strDesc:
			strDesc += " "
		strDesc += "Der Standardwert für die Einstellung ist %s." % (strDefault)
		self.m_oHtmlPage.createBox(
			strTitle, strDesc, bClose=False)
		self.m_oHtmlPage.openForm(dictTargets={
			"target" 	: self.m_strVal,
			"key" 		: self.m_strKey
		})
		if isinstance(varVal, bool):
			self.m_oHtmlPage.appendForm(self.m_strVal,
				strInput="%s" % (varVal),
				strTitle=strTitle,
				dictChoice = {
					"Ein"	: "True",
					"Aus"	: "False"
				})
		else:
			self.m_oHtmlPage.appendForm(self.m_strVal,
				strInput="%s" % (varVal),
				strTitle=strTitle,
				dictChoice=dictChoices,
				bUseKeyAsValue=bUseKeyAsValue)	
		self.m_oHtmlPage.closeForm()
		self.m_oHtmlPage.closeBox()
		return True
		
	def updateValue(self):
		strResult = ""
		if Globs.setSetting(self.m_strKey, self.m_strFxn, self.m_strVal):
			Globs.saveSettings()
			return True
		self.m_oHtmlPage.createBox(self.m_strFxn,
			"Die Einstellung \"%s\" konnte nicht auf den Wert \"%s\" geändert werden." % (
			self.m_strFxn, self.m_strVal),
			strType="warning")
		return False

class TaskDisplayLogMem(FutureTask):
	
	def __init__(self, oWorker, oHtmlPage, dictQuery=None, dictForm=None):
		super(TaskDisplayLogMem, self).__init__(oWorker)
		self.m_oHtmlPage = oHtmlPage
		self.m_dictQuery = dictQuery
		self.m_dictForm = dictForm
		self.m_strMode = ""
		return
		
	def __str__(self):
		strDesc = "Darstellen der Protokollierung"
		return  strDesc
		
	def do(self):
		self.m_strMode = ""
		
		self.m_oHtmlPage.setTitle("Protokollierung")
		
		if self.m_dictQuery and "mode" in self.m_dictQuery:
			self.m_strMode = self.m_dictQuery["mode"][0]
		elif self.m_dictForm and "mode" in self.m_dictForm:
			self.m_strMode = self.m_dictForm["mode"][0]
		
		bUpdate = (self.m_strMode and (self.m_strMode == "update"))
		lstLogMem = Globs.getLogMem(bUpdate)
		if self.m_strMode and self.m_strMode == "edit":
			self.createForm()
		elif self.m_strMode and self.m_strMode in ("EXC", "ERR", "WRN", "INF", "DBG"):
			Globs.setLogLvl(self.m_strMode)
			self.m_oHtmlPage.createBox("Protokollierung",
				"Die Detail-Tiefe der Protokollierung ist jetzt auf \"%s\" festgelegt." % (
					Globs.getLogLvl()))
		elif self.m_strMode and self.m_strMode.isdigit():
			self.showDetail(lstLogMem)
		else:
			self.showLogging(lstLogMem)
		return
		
	def createForm(self):
		self.m_oHtmlPage.createBox("Protokollierung",
			"Die Detail-Tiefe der Protokollierung kann geändert werden. "+
			"Niedrigere Detail-Stufen schließen höhere implizit mit ein.",
			bClose = False)
		self.m_oHtmlPage.openForm()
		self.m_oHtmlPage.appendForm(
			"mode", Globs.getLogLvl(), "Detail-Tiefe",
			dictChoice = {
				"Ausnahmen"	: "EXC",
				"Fehler"	: "ERR",
				"Warnungen"	: "WRN",
				"Hinweise"	: "INF",
				"Debugging" : "DBG"
			})
		self.m_oHtmlPage.closeForm()
		self.m_oHtmlPage.closeBox()
		return
		
	def showDetail(self, lstLogMem):
		nIndex = int(self.m_strMode)
		if (nIndex >= 0 and nIndex < len(lstLogMem)):
			oLogEntry = lstLogMem[nIndex]
			self.m_oHtmlPage.createBox(
				"%s - %s" % (oLogEntry.m_strType, oLogEntry.m_strDate),
				"%s" % (oLogEntry.m_strText), bClose=False)
			if (oLogEntry.m_lstTB):
				self.m_oHtmlPage.append("<ul>")
				for (filename, line, function, text) in oLogEntry.m_lstTB:
					self.m_oHtmlPage.append("<li>File \"%s\", line %s, in %s %s</li>" % (
						html.escape(filename),
						line,
						html.escape(function),
						html.escape(text)))
				self.m_oHtmlPage.append("</ul>")
			self.m_oHtmlPage.createButton("OK")
			self.m_oHtmlPage.closeBox()
		else:
			self.m_oHtmlPage.createBox(
				"Protokollierung",
				"Der angeforderte Eintrag existiert nicht.",
				strType="warning")
		return
		
	def showLogging(self, lstLogMem):
		# Tabelle öffnen
		self.m_oHtmlPage.openTable(
			"Protokollierung",
			["Nr", "Typ", "Zeit", "Meldung"], True, True)
		nIndex = 0
		for oLogEntry in lstLogMem:
			strType = ""
			if (oLogEntry.m_strType == "EXC"):
				strType = "ym-danger"
			elif (oLogEntry.m_strType == "ERR"):
				strType = "ym-warning"
			elif (oLogEntry.m_strType == "WRN"):
				strType = "ym-primary"
			elif (oLogEntry.m_strType == "INF"):
				strType = "ym-success" 
			self.m_oHtmlPage.appendTable([
				"%s" % (nIndex),
				"<div class=\"center\"><a class=\"%s %s\" href=\"%s?mode=%s\">%s</a></div>" % (
					"ym-button ym-xsmall", strType,
					self.m_oHtmlPage.m_strPath, nIndex,
					html.escape(oLogEntry.m_strType)),
				"%s" % (html.escape(oLogEntry.m_strDate)),
				"%s" % (html.escape(oLogEntry.m_strText))],
				bFirstIsHead=True, bEscape=False)
			nIndex += 1
		# Tabelle schließen
		self.m_oHtmlPage.closeTable()
		return
		
class TaskDisplaySounds(FutureTask):
	
	def __init__(self,
		oWorker,
		oHtmlPage,
		dictForm=None,
		dictQuery=None
		):
		super(TaskDisplaySounds, self).__init__(oWorker)
		self.m_oHtmlPage = oHtmlPage
		self.m_dictForm = dictForm
		self.m_dictQuery = dictQuery
		return
		
	def __str__(self):
		strDesc = "Darstellen der installierten Klänge"
		return  strDesc
		
	def do(self):
		self.displaySounds()
		return
		
	def displaySounds(self):
		self.m_oHtmlPage.setTitle("Klänge")
		self.m_oHtmlPage.extend([
			"<div class=\"nav-wrapper\">",
			"<nav class=\"ym-vlist\">",
			"<h6 class=\"ym-vtitle\">Installierte Klänge</h6>"
		])
		
		strSound = ""
		
		if self.m_dictQuery and "cache" in self.m_dictQuery:
			if self.m_dictQuery["cache"][0] == "clear":
				Globs.scanSoundFiles(bClear=True)
			if self.m_dictQuery["cache"][0] == "rescan":
				Globs.scanSoundFiles(bRescan=True)
		if self.m_dictQuery and "sound" in self.m_dictQuery:
			strSound = self.m_dictQuery["sound"][0]
		
		self.m_oHtmlPage.append("<ul>")
		if "Sounds" in Globs.s_dictSettings:
			dictSounds = Globs.s_dictSettings["Sounds"]
			# Eigene Klänge darstellen
			if "Default" in dictSounds:
				strAnchor = uuid.uuid1().hex
				self.m_oHtmlPage.append("<li id=\"Default\"><span>Eigene Klänge</span>")
				self.m_oHtmlPage.append("<ul>")
				for (strName, strFile) in sorted(dictSounds["Default"].items()):
					if strName == strSound:
						strActive = "&#x0266B;"
					else:
						strActive = "&#x025B6;"
					self.m_oHtmlPage.append(
						"<li><a href=\"%s?sound=%s&token=%s#%s\">%s %s</a></li>" % (
							"/sound/values.html", strName, strAnchor, "Default", strActive, strName))
				self.m_oHtmlPage.append("</ul>")
				self.m_oHtmlPage.append("</li>")
			# Alle übrigen Klänge darstellen
			for (strCategory, dictSounds) in sorted(Globs.s_dictSettings["Sounds"].items()):
				if strCategory == "Default":
					continue
				strAnchor = uuid.uuid1().hex
				self.m_oHtmlPage.append("<li id=\"%s\"><span>%s</span>" % (strCategory, strCategory))
				self.m_oHtmlPage.append("<ul>")
				for (strName, strFile) in sorted(dictSounds.items()):
					if strName == strSound:
						strActive = "&#x0266B;"
					else:
						strActive = "&#x025B6;"
					self.m_oHtmlPage.append(
						"<li><a href=\"%s?sound=%s&token=%s#%s\">%s %s</a></li>" % (
							"/sound/values.html", strName, strAnchor, strCategory, strActive, strName))
				self.m_oHtmlPage.append("</ul>")
				self.m_oHtmlPage.append("</li>")
		self.m_oHtmlPage.extend([
			"</ul>",
			"</nav>",
			"</div>"
		])
		return
		
class TaskStartPage(FutureTask):
	
	def __init__(self,
		oWorker,
		oHtmlPage,
		dictForm=None,
		dictQuery=None
		):
		super(TaskStartPage, self).__init__(oWorker)
		self.m_oHtmlPage = oHtmlPage
		self.m_dictForm = dictForm
		self.m_dictQuery = dictQuery
		return
		
	def __str__(self):
		strDesc = "Darstellen der Startseite"
		return  strDesc
		
	def do(self):
		secEdt = ""
		artEdt = ""
		btnEdt = ""
		
		self.m_oHtmlPage.setTitle("Startseite")
		if (not Globs.s_oStartPage):
			Globs.s_oStartPage = StartPage()
			
		bEdit = ("edit" in self.m_dictQuery and self.m_dictQuery["edit"][0] == "startpage")
		
		if self.m_dictForm:
			if "del" in self.m_dictForm:
				self.doDelete(self.m_dictForm["del"][0])
			elif "submit" in self.m_dictForm:
				self.doSubmit()
			elif ("btnAdd" in self.m_dictForm
				and "sec" in self.m_dictForm
				and "art" in self.m_dictForm):
				btnEdt = self.m_dictForm["btnAdd"][0]
				artEdt = self.m_dictForm["art"][0]
				secEdt = self.m_dictForm["sec"][0]
				self.doSubmit()
				self.doAdd(addBtn=btnEdt)
				bEdit = False
			elif ("btnEdt" in self.m_dictForm
				and "sec" in self.m_dictForm
				and "art" in self.m_dictForm):
				btnEdt = self.m_dictForm["btnEdt"][0]
				artEdt = self.m_dictForm["art"][0]
				secEdt = self.m_dictForm["sec"][0]
				self.doSubmit()
				bEdit = False
		if self.m_dictQuery:
			if "secEdt" in self.m_dictQuery:
				secEdt = self.m_dictQuery["secEdt"][0]
			if ("artEdt" in self.m_dictQuery
				and "sec" in self.m_dictQuery):
				secEdt = self.m_dictQuery["sec"][0]
				artEdt = self.m_dictQuery["artEdt"][0]
			if "secAdd" in self.m_dictQuery:
				secEdt = self.m_dictQuery["secAdd"][0]
				self.doAdd(addSec=secEdt)
			if ("artAdd" in self.m_dictQuery
				and "sec" in self.m_dictQuery):
				secEdt = self.m_dictQuery["sec"][0]
				artEdt = self.m_dictQuery["artAdd"][0]
				self.doAdd(addArt=artEdt)
			
		Globs.s_oStartPage.writeToPage(self.m_oHtmlPage, bEdit, secEdt, artEdt, btnEdt)
		return
		
	def doAdd(self, addSec="", addArt="", addBtn=""):
		
		strSec = ""
		strArt = ""
		strBtn = ""
		
		Globs.dbg(
			"doAdd(addSec=\"%s\", addArt=\"%s\", addBtn=\"%s\")" % (
			addSec, addArt, addBtn))
		
		if addBtn and self.m_dictForm:
			if "sec" in self.m_dictForm:
				strSec = self.m_dictForm["sec"][0]
				if "art" in self.m_dictForm:
					strArt = self.m_dictForm["art"][0]
		elif addSec:
			oSection = Section()
			oSection.setSection(addSec, True)
			Globs.s_oStartPage.update({addSec : oSection})
			return
		elif (addArt and self.m_dictQuery
			and "sec" in self.m_dictQuery):
			strSec = self.m_dictQuery["sec"][0]
		else:
			return
		
		for (strName, oSection) in Globs.s_oStartPage.items():
			if strName == strSec:
				if addArt:
					oArticle = Article()
					oArticle.setArticle(addArt)
					oSection.update({addArt : oArticle})
					return
				for (strName, oArticle) in oSection.items():
					if strName == strArt:
						if addBtn:
							oButton = Button()
							oButton.setButton(addBtn)
							oArticle.update({addBtn : oButton})
						return	
				return	
		return
		
	def doDelete(self, strType):
		
		strSec = ""
		strArt = ""
		strBtn = ""
		
		if "sec" in self.m_dictForm:
			strSec = self.m_dictForm["sec"][0]
			if "art" in self.m_dictForm:
				strArt = self.m_dictForm["art"][0]
				if "btn" in self.m_dictForm:
					strBtn = self.m_dictForm["btn"][0]
		else:
			return False
			
		Globs.dbg(
			"doDelete(strType=\"%s\"): strSec=\"%s\", strArt=\"%s\", strBtn=\"%s\"" % (
			strType, strSec, strArt, strBtn))
			
		for (strName, oSection) in Globs.s_oStartPage.items():
			if strName == strSec:
				if strType == "sec":
					Globs.s_oStartPage.pop(strSec)
					return True
				elif strArt:
					for (strName, oArticle) in oSection.items():
						if strName == strArt:
							if strType == "art":
								oSection.pop(strArt)
								return True
							elif strBtn:
								for (strName, oButton) in oArticle.items():
									if strName == strBtn:
										if strType == "btn":
											oArticle.pop(strBtn)
											return True
										return False
							return False
				return False
		return False
	
	def doSubmit(self):
		
		strSec = ""
		strArt = ""
		strBtn = ""
		
		if "sec" in self.m_dictForm:
			strSec = self.m_dictForm["sec"][0]
			strType = "sec"
			if "art" in self.m_dictForm:
				strArt = self.m_dictForm["art"][0]
				strType = "art"
				if "btn" in self.m_dictForm:
					strBtn = self.m_dictForm["btn"][0]
					strType = "btn"
		else:
			return
		
		for (strName, oSection) in Globs.s_oStartPage.items():
			if strName == strSec:
				if strType == "sec":
					self.doSubmitSection(oSection)
				elif strArt:
					for (strName, oArticle) in oSection.items():
						if strName == strArt:
							if strType == "art":
								self.doSubmitArticle(oArticle)
							elif strBtn:
								for (strName, oButton) in oArticle.items():
									if strName == strBtn:
										if strType == "btn":
											self.doSubmitButton(oButton)
										return
							return	
				return
		return
		
	def doSubmitSection(self, oSection):
		if ("secPrimary" in self.m_dictForm
			and self.m_dictForm["secPrimary"][0] == "primary"):
			oSection.m_bPrimary = True
		else:
			oSection.m_bPrimary = False
		return
		
	def doSubmitArticle(self, oArticle):
		if "artTitle" in self.m_dictForm:
			oArticle.m_strTitle = self.m_dictForm["artTitle"][0]
		if "artContent" in self.m_dictForm:
			oArticle.m_strMsg = self.m_dictForm["artContent"][0]
		if "artType" in self.m_dictForm:
			oArticle.m_strType = self.m_dictForm["artType"][0]
		return
		
	def doSubmitButton(self, oButton):
		if "btnTitle" in self.m_dictForm:
			oButton.m_strTitle = self.m_dictForm["btnTitle"][0]
		if "btnHRef" in self.m_dictForm:
			oButton.m_strHRef = self.m_dictForm["btnHRef"][0]
		if "btnIcon" in self.m_dictForm:
			oButton.m_strIcon = self.m_dictForm["btnIcon"][0]
		if "btnColor" in self.m_dictForm:
			oButton.m_strColor = self.m_dictForm["btnColor"][0]
		if "btnRedirect" in self.m_dictForm:
			oButton.m_strRedirect = self.m_dictForm["btnRedirect"][0]
		return

class Httpd:
	
	def __init__(self, oWorker):
		global g_oHttpdWorker
		
		Globs.signalCriticalActivity()
		g_oHttpdWorker = oWorker
		return
	
	## 
	#  @brief
	#  Startet den Web-Server und kehrt erst nach dessen Terminierung zurück.
	#  
	#  @param [in] self
	#  				die Httpd-Instanz
	#  
	#  @details
	#  Bevor der Web-Server gestartet wird, wechselt die Routine das Arbeitsverzeichnis in das
	#  Wurzelverzeichnis des Web-Servers. Das Wurzelverzeichnis des Web-Servers setzt sich
	#  zusammen aus `[@ref installdir]/www`.	
	#  
	#  
	def run(self):
		strHttpDir = os.path.join(Globs.s_strBasePath, "www")
		if (os.path.isdir(strHttpDir)):
			# Das Arbeitsverzeichnis muss das "www"-Verzeichnis sein
			os.chdir(strHttpDir)
			# Web-Server instanziieren
			Globs.s_oHttpd = BerryHttpServer((
				Globs.getSetting("System", "strHttpIp",
					"\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}",
					"0.0.0.0"),
				Globs.getSetting("System", "nHttpPort",
					"\\d{1,5}",
					8081)),
				BerryHttpHandler)
			# Web-Server starten
			print("Running HTTP Server on %s at %s ..." % (
				Globs.s_oHttpd.server_name, Globs.s_oHttpd.server_address))
			Globs.s_oHttpd.serve_forever()
		# Ressourcen des Web-Servers freigeben
		Globs.s_oHttpd.server_close()
		return
	
class BerryHttpHandler(SimpleHTTPRequestHandler):
	
	def installModule(self, strPath, dictForm):
		if ("ModuleFile" not in dictForm or
			not dictForm["ModuleFile"][0].filename or
			not dictForm["ModuleFile"][0].file):
			oHtmlPage = HtmlPage(strPath, strTitle = "Modulinstallation")
			oHtmlPage.createBox(
				"Unvollständige Eingabe",
				"Bitte geben Sie die zu installierende Python3 Moduldatei an.",
				strType="warning")
			return oHtmlPage
		oHtmlPage = HtmlPage("/system/modules.html", strTitle = "Modulkonfiguration")
		oModuleFile = dictForm["ModuleFile"][0]
		strFilename = oModuleFile.filename
		strFilename = strFilename.replace("\\", "/")
		strHead, strFilename = os.path.split(strFilename)
		strComponent, strExt = os.path.splitext(strFilename)
		if not re.match("\\.[Pp][Yy]", strExt):
			oHtmlPage = HtmlPage(strPath, strTitle = "Modulinstallation")
			oHtmlPage.createBox(
				"Unzulässige Eingabe",
				"Die Datei '%s' ist keine unterstützte Python3 Datei." % (strFilename) +
				"Bitte geben Sie eine Python3 Moduldatei (*.py) an.",
				strType="warning")
			return oHtmlPage
		if ("ModuleClass" in dictForm):
			strName = "%s" % (dictForm["ModuleClass"][0])
		if not strName:
			strName = strComponent
		try:
			foFile = open("%s/%s" % (
				Globs.s_strModulePath, strFilename), "w")
			oData = oModuleFile.file.read()
			foFile.write(oData.decode())
			foFile.close()
			del oData
		except:
			Globs.exc("Schreiben der Moduldatei %s/%s" % (
				Globs.s_strModulePath, strFilename))
			oHtmlPage.createBox(
				"Fehler",
				"Die hochgeladene Moduldatei '%s'" % (strFilename) +
				"konnte nicht in '%s' gespeichert werden." % (Globs.s_strModulePath),
				strType="error")
			return oHtmlPage
		# Tasks ausführen
		TaskInstallModule(g_oHttpdWorker, strComponent, strName).start()
		TaskModuleInit(g_oHttpdWorker, strComponent).start()
		TaskSaveSettings(g_oHttpdWorker).start()
		oTask = TaskDisplayModules(g_oHttpdWorker, oHtmlPage)
		if oTask.start():
			oTask.wait()
		return oHtmlPage
		
	def installSound(self, strPath, dictForm):
		if ("SoundFile" not in dictForm):
			oHtmlPage = HtmlPage(strPath, strTitle = "Klanginstallation")
			oHtmlPage.createBox(
				"Unvollständige Eingabe",
				"Es muss mindestens eine Klang- oder Zip-Datei angegeben werden.",
				strType="warning")
			return oHtmlPage
		oHtmlPage = HtmlPage("/sound/values.html", strTitle = "Installierte Klänge")
		for oSoundFile in dictForm["SoundFile"]:
			if (not oSoundFile.filename or
				not oSoundFile.file):
				oHtmlPage = HtmlPage(strPath, strTitle = "Klanginstallation")
				oHtmlPage.createBox(
					"Unvollständige Eingabe",
					"Es konnte keine gültige Klang- oder Zip-Datei empfangen werden.",
					strType="warning")
				return oHtmlPage
			try:
				if not self.processSoundFile(oSoundFile):
					oHtmlPage = HtmlPage(strPath, strTitle = "Klanginstallation")
					oHtmlPage.createBox(
						"Unzulässige Eingabe",
						"Bitte verwenden Sie nur zulässige Klangdateien (*.wav, *.mp3).",
						strType="warning")
					return oHtmlPage
			except Exception as ex:
				Globs.exc("Verarbeiten der Klangdatei %s" % (
					oSoundFile.filename))
				oHtmlPage.createBox(
					"Fehler",
					"Die empfangene Datei '%s' " % (oSoundFile.filename) +
					"konnte nicht verarbeitet werden (%s)." % (ex),
					strType="error")
				return oHtmlPage
		# Tasks ausführen
		Globs.scanSoundFiles(bRescan=True)
		oTask = TaskDisplaySounds(g_oHttpdWorker, oHtmlPage)
		if oTask.start():
			oTask.wait()
		return oHtmlPage
		
	def processSoundFile(self, oSoundFile):
		strSoundPath = Globs.getSetting("System", "strSoundLocation",
			varDefault="/usr/share/scratch/Media/Sounds")
		strFilename = oSoundFile.filename
		strFilename = strFilename.replace("\\", "/")
		strHead, strFilename = os.path.split(strFilename)
		strComponent, strExt = os.path.splitext(strFilename)
		bResult = False
		if (zipfile.is_zipfile(oSoundFile.file)):
			strDirname = os.path.join(strSoundPath, strComponent)
			if not (os.path.isdir(strDirname) or os.path.islink(strDirname)):
				os.mkdir(strDirname)
			with ZipFile(oSoundFile.file, "r") as oZipFile:
				for oZipInfo in (oZipFile.infolist()):
					foFile = oZipFile.open(oZipInfo)
					strHead, strFilename = os.path.split(oZipInfo.filename)
					if re.match("\\.[Ww][Aa][Vv]|\\.[Mm][Pp]3", strFilename):
						continue
					self.installSoundFile(foFile, os.path.join(strDirname, strFilename))
					bResult = True
		elif not re.match("\\.[Ww][Aa][Vv]|\\.[Mm][Pp]3", strExt):
			return False
		else:
			this.installSoundFile(oSoundFile.file, os.path.join(strSoundPath, strFilename))
			bResult = True
		return bResult
		
	def installSoundFile(self, foSource, strFilename):
		foFile = open(strFilename, "w+b")
		oData = foSource.read()
		foFile.write(oData)
		foFile.close()
		del oData
		return
		
	def changeModules(self, strPath, dictForm):
		oHtmlPage = HtmlPage(strPath, strTitle = "Modulkonfiguration")
		if ("submit" not in dictForm):
			oHtmlPage.createBox(
				"Fehler",
				"Im Formular fehlt die Angabe der auszuführenden Aktion (Parameter \"submit\").",
				strType="error")
			return oHtmlPage
		if ("target" not in dictForm):
			oHtmlPage.createBox(
				"Achtung",
				"Für den auszuführenden Vorgang müssen zunächst Objekte ausgewählt werden.",
				strType="warning")
			return oHtmlPage
		strAction = dictForm["submit"][0]
		if strAction == "save":
			if ("ModuleClass" not in dictForm):
				oHtmlPage.createBox(
					"Achtung",
					"Es muss ein gültiger Bezeichner für die Hauptklasse des Moduls angegeben werden.",
					strType="error")
				return oHtmlPage
			strTarget = dictForm["target"][0]
			strName = dictForm["ModuleClass"][0]
			# Modul installieren
			TaskInstallModule(g_oHttpdWorker, strTarget, strName).start()
			TaskModuleInit(g_oHttpdWorker, strTarget).start()
			TaskSaveSettings(g_oHttpdWorker).start()
		elif strAction == "enable" or strAction == "disable":
			lstTarget = dictForm["target"]
			bEnable = True
			if strAction == "disable":
				bEnable = False
			# Module aktivieren oder deaktivieren
			for strTarget in lstTarget:
				TaskEnableModule(g_oHttpdWorker, strTarget, bEnable).start()
				TaskModuleInit(g_oHttpdWorker, strTarget).start()
			TaskSaveSettings(g_oHttpdWorker).start()
		elif strAction == "delete":
			lstTarget = dictForm["target"]
			for strTarget in lstTarget:
				TaskRemoveModule(g_oHttpdWorker, strTarget).start()
				TaskModuleInit(g_oHttpdWorker, strTarget).start()
			TaskSaveSettings(g_oHttpdWorker).start()
		else:
			oHtmlPage.createBox(
				"Achtung",
				"Der angeforderte Vorgang wird (noch) nicht unterstützt.",
				strType="warning")
			return oHtmlPage
		oTask = TaskDisplayModules(g_oHttpdWorker, oHtmlPage)
		if oTask.start():
			oTask.wait()
		return oHtmlPage
	
	def serveGet(self,
		strPath,
		strRedirect=None,
		dictForm=None,
		dictQuery=None
		):
		try:
			oFutureTask = None
			oHtmlPage = None
			
			oHtmlPage = self.doCommand(strPath,
				dictForm=dictForm,
				dictQuery=dictQuery)
			if strRedirect:
				strPath = strRedirect
				oHtmlPage = None
				
			Globs.log("serveGet: '%s', redirect='%s' -> %s" % (strPath, strRedirect, oHtmlPage))
			
			if (not oHtmlPage):
				if strPath == "/system/settings.html":
					oHtmlPage = HtmlPage(strPath)
					oFutureTask = TaskDisplaySettings(g_oHttpdWorker,
						oHtmlPage,
						dictQuery=dictQuery,
						dictForm=dictForm)
				elif strPath == "/system/values.html":
					oHtmlPage = HtmlPage(strPath)
					oFutureTask = TaskDisplaySystem(g_oHttpdWorker,
						oHtmlPage,
						dictQuery=dictQuery,
						dictForm=dictForm)
				elif strPath == "/system/modules.html":
					oHtmlPage = HtmlPage(strPath)
					oFutureTask = TaskDisplayModules(g_oHttpdWorker,
						oHtmlPage,
						dictQuery=dictQuery)
				elif strPath == "/system/logging.html":
					oHtmlPage = HtmlPage(strPath)
					oFutureTask = TaskDisplayLogMem(g_oHttpdWorker,
						oHtmlPage,
						dictQuery=dictQuery,
						dictForm=dictForm)
				elif strPath == "/system/startpage.html":
					oHtmlPage = HtmlPage(strPath)
					oFutureTask = TaskStartPage(g_oHttpdWorker,
						oHtmlPage,
						dictQuery=dictQuery,
						dictForm=dictForm)
				elif strPath == "/sound/values.html":
					oHtmlPage = HtmlPage(strPath)
					oFutureTask = TaskDisplaySounds(g_oHttpdWorker,
						oHtmlPage,
						dictQuery=dictQuery,
						dictForm=dictForm)
						
			if oFutureTask:
				if oFutureTask.start():
					oFutureTask.wait()
				else:
					oHtmlPage = None
					
			if not oHtmlPage:
				SimpleHTTPRequestHandler.do_GET(self)
				return
		except:
			Globs.exc("HTTP GET Version %s: Client '%s' (%s), Path '%s'" % (
				self.request_version, self.client_address, self.address_string(),
				strPath))
			oHtmlPage = HtmlPage(strPath, strTitle = "Fehler")
			oHtmlPage.createBox(
				"Fehler",
				"Die Anforderung (GET) wurde wegen Fehlern abgebrochen.",
				strType="error")
		# HTML-Seite absenden
		self.send_response(200)
		self.end_headers()
		self.wfile.write(oHtmlPage.getContent())
		return
		
	def servePost(self, strPath, oForm, dictQuery = None):
		oHtmlPage = None
		try:
			# Formulardaten aufbereiten
			dictForm = {}
			for oKey in oForm.keys():
				strInfo = ""
				bSkip = False
				oField = oForm[oKey]
				if (type(oField) is list or type(oField) is tuple):
					for oItem in oField:
						if (oItem.filename):
							if strInfo:
								strInfo += ", '%s'" % (oItem.filename)
							else:
								strInfo = "mehrerer Dateien: %s='%s'" % (oKey, oItem.filename)
							if (oKey not in dictForm):
								dictForm.update({oKey : []})
							dictForm[oKey].append(oItem)
							bSkip = True
				elif (oField.filename):
					strInfo = "einer Datei: %s=%s" % (oKey, oField.filename)
					dictForm.update({oKey : [oField]})
					bSkip = True
				if strInfo:
					Globs.log("Hochladen %s" % (strInfo))
				if (not bSkip):
					dictForm.update({oKey : oForm.getlist(oKey)})
				
			if strPath == "/system/install.html":
				oHtmlPage = self.installModule(strPath, dictForm)
			elif strPath == "/sound/install.html":
				oHtmlPage = self.installSound(strPath, dictForm)
			elif strPath == "/system/modules.html":
				oHtmlPage = self.changeModules(strPath, dictForm)
			
			if not oHtmlPage:
				self.serveGet(strPath, dictForm=dictForm, dictQuery=dictQuery)
				return
		except:
			Globs.exc("HTTP POST Version %s: Client '%s' (%s), Path '%s'" % (
				self.request_version, self.client_address, self.address_string(),
				strPath))
			oHtmlPage = HtmlPage(strPath, strTitle = "Fehler")
			oHtmlPage.createBox(
				"Fehler",
				"Die Anforderung (POST) wurde wegen Fehlern abgebrochen.",
				strType="error")
		# HTML-Seite absenden
		self.send_response(200)
		self.end_headers()
		self.wfile.write(oHtmlPage.getContent())
		return
	
	def doCommand(self,
		strPath,
		dictForm=None,
		dictQuery=None
		):
		Globs.dbg("doCommand(strPath=%s, dictForm=%r, dictQuery=%r)" % (
			strPath, dictForm, dictQuery))
		# Built-in sound and speak command processing for GET and POST
		if (dictQuery and "sound" in dictQuery):
			for strArg in dictQuery["sound"]:
				TaskSound(g_oHttpdWorker, strArg).start()
		if (dictForm and "sound" in dictForm):
			for strArg in dictForm["sound"]:
				TaskSound(g_oHttpdWorker, strArg).start()
		if (dictQuery and "speak" in dictQuery):
			for strArg in dictQuery["speak"]:
				TaskSpeak(g_oHttpdWorker, strArg).start()
		if (dictForm and "speak" in dictForm):
			for strArg in dictForm["speak"]:
				TaskSpeak(g_oHttpdWorker, strArg).start()
		# External timer event from cron-job
		if (re.match("/ext/evt\\.src", strPath)
			and dictQuery
			and "timer" in dictQuery
			and dictQuery["timer"]
			and dictQuery["timer"][0] == "cron"):
			TaskModuleEvt(g_oHttpdWorker, strPath, dictQuery=dictQuery).start()
			return HtmlPage(strPath)
		# System or program termination
		if (re.match("/exit/(exit|halt|boot)\\.html", strPath)
			and dictQuery
			and "exit" in dictQuery
			and dictQuery["exit"]):
			TaskExit(g_oHttpdWorker, dictQuery["exit"][0]).start()
			return None
		Globs.log("doCommand: '%s'" % strPath)
		# Commands being passed to installed modules
		if (re.match("/modules/.+\\.(cmd|htm|html)", strPath)):
			Globs.log("Modulkommando: '%s'" % strPath)
			oHtmlPage = HtmlPage(strPath)
			oFutureTask = TaskModuleCmd(g_oHttpdWorker,
				strPath,
				oHtmlPage,
				dictForm=dictForm,
				dictQuery=dictQuery)
			if oFutureTask.start():
				oFutureTask.wait()
			else:
				oHtmlPage = None
			return oHtmlPage
		return None
		
	def do_HEAD(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		return

	def do_AUTHHEAD(self):
		self.send_response(401)
		self.send_header('WWW-Authenticate', 'Basic realm=\"RasPyWeb\"')
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		return
	
	def do_GET(self):
		# Webserver-Aktivität signalisieren
		Globs.signalCriticalActivity()
		# Die angeforderten Informationen auswerten
		oParsedPath = urlparse(self.path)
		strPath = oParsedPath.path
		dictQuery = {}
		for (p, v) in parse_qsl(oParsedPath.query):
			p = p.strip()
			if p not in dictQuery:
				dictQuery.update({p : []})
			dictQuery[p].append(v.strip())
		bRedirect = False
		strRedirect = None
		# HTTP-Server redirect commands
		if ("redirect2" in dictQuery):
			bRedirect = True
			strRedirect = Globs.getRedirect(dictQuery["redirect2"][0], strPath)
		oHtmlPage = None
		# Angeforderten Inhalt liefern
		self.serveGet(strPath,
			strRedirect=strRedirect,
			dictQuery = dictQuery)
		return
	
	def do_POST(self):
		# Webserver-Aktivität signalisieren
		Globs.signalCriticalActivity()
		# URL analysieren
		oParsedPath = urlparse(self.path)
		strPath = oParsedPath.path
		# Die angeforderten Informationen (Query) auswerten		
		dictQuery = {}
		for (p, v) in parse_qsl(oParsedPath.query):
			p = p.strip()
			if p not in dictQuery:
				dictQuery.update({p : []})
			dictQuery[p].append(v.strip())
		# Die angeforderten Informationen (Formular) auswerten
		oForm = cgi.FieldStorage(
			fp=self.rfile, 
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
				})
		# Das abgesendete Formular verarbeiten
		self.servePost(strPath, oForm, dictQuery=dictQuery)
		return

class BerryHttpServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""
	pass
