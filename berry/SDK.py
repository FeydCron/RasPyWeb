import os
import subprocess
import re
import threading
import socket
import html

from datetime import datetime

from Voice import Voice
from Sound import Sound
from Globs import Globs

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

class HtmlPage(list):

	def __init__(self, strPath, strTitle = "", nAutoRefresh=0):
		list.__init__([])
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
	
	def setTitle(self, strTitle):
		self.m_strTitle = strTitle
		return
		
	def setAutoRefresh(self, nAutoRefresh=0):
		if nAutoRefresh >= 5:
			self.m_strAutoRefresh = "<meta http-equiv=\"refresh\" content=\"%s\">" % (
				nAutoRefresh)
		else:
			self.m_strAutoRefresh = ""
		return
	
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
	def appendTableForm(self, strRef, lstData, bChk=False, dictAct={}, bEscape=True):
		strChecked = ""
		self.extend([
			"<tr>",
		])
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
		dictButtons={}	# {name : (value, title, class)}
		):
		self.append("<div class=\"ym-fbox-footer\">")
		self.extend([
			"<a class=\"ym-button ym-primary\" href=\"%s%s\">Abbrechen</a>" % (
				self.m_strPath, self.m_strQueries),
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
				"<input type=\"%s\" name=\"%s\" value=\"%s\" id=\"%s\" placeholder=\"%s\"/>" % (
					strTextType, strName, strInput, self.m_nId, html.escape(strInput)),
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
