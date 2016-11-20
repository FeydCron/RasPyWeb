import hashlib
import os.path
import time


# Schedule (Experimental)
# Auslöser:
#	'Year'		- Jahr, vierstellig
#	'Month'		- Monat im Jahr, 1 = Januar bis 12 = Dezember
#	'Day'		- Tag des Monats
#	'Weekday'	- Wochentag, 0 = Sonntag, 1 = Montag bis 6 = Samstag
#	'Hour'		- Stunde (24h)
#	'Minute'	- Minimale Auflösung von 5 Minuten
# Aktionen:
#	'Time'		- (True|False) Ansage der aktuellen Uhrzeit
#	'Play'		- <sound> Abspielen des angegebenen Sounds
#	'Talk'		- <Text> Sprechen des angegebenen Textes
schedule = {
	'Test': {
		'Weekday':	range(22, 23),
		'Hour': 	range(0, 23),
		'Minute':	range(0, 59),
		'Time': 	True,
		'Play':		"Horse",
		'Talk':		"Dies ist nur ein Test"}}

# Globale Variablen
sMonName = ""	# Monatsname (%B)
sDayName = ""	# Name des Wochentags (%A)
nMonYear = 0	# Monat (%m) 
nDayWeek = 0	# Wochentag als Zahl (%w) 
nYear4xY = 0	# Jahr, 4-stellig (%Y)
nYear2xY = 0	# Jahr, 2-stellig (%y)
nWeekOfY = 0	# Kalenderwoche [00,53] (%W)
nHour24h = 0	# Stunde in 24 Stunden (%H)
nHour12h = 0	# Stunde in 12 Stunden (%I)
nMinutes = 0	# Minutes (%M)

nTimeSpoken = 0

# Parametrierungen
nSilenceFrom = 19		# Anfang der Ruhezeit Stunde/24
nSilenceTo   = 6		# Ende der Ruhezeit Stunde/24
nTellTimeInt = 30		# Intervall der akustischen Zeitanzeige/-ansage
bTestMode	 = False	# Testmodus ein- (True) bzw. ausschalten (False)

def watchScheduledEvents():
	global schedule
	global nYear4xY
	global nMonYear
	
	isTrigger = False
	scheduled = False
	
	for name, param in schedule:
		isTrigger = True
		if param['Year'] and isTrigger:
			isTrigger = nYear4xY in param['Year']
			scheduled = True
		if param['Month'] and isTrigger:
			isTrigger = nMonYear in param['Month']
			scheduled = True
		if param['Day'] and isTrigger:
			#isTrigger = nDay
			pass
		

# Aktuelle Zeit holen und in globalen Variablen speichern
def updateTime():
	global sMonName
	global sDayName
	global nMonYear
	global nDayWeek
	global nYear4xY
	global nYear2xY
	global nWeekOfY
	global nHour24h
	global nHour12h
	global nMinutes

	sMonName = time.strftime("%B")
	sDayName = time.strftime("%A")
	nMonYear = int(time.strftime("%m"))
	nDayWeek = int(time.strftime("%w"))
	nYear4xY = int(time.strftime("%Y"))
	nYear2xY = int(time.strftime("%y"))
	nWeekOfY = int(time.strftime("%W"))
	nHour24h = int(time.strftime("%H"))
	nHour12h = int(time.strftime("%I"))
	nMinutes = int(time.strftime("%M"))

# Sprachausgabe
def speak(strSpeak):
	hash = hashlib.md5(strSpeak.encode())
	strFile = "/tmp/" + hash.hexdigest() + ".wav"
	if os.path.isfile(strFile):
		os.system('aplay %s' %strFile)
	else:
		os.system('pico2wave --lang=de-DE --wave=%s "%s"; aplay %s' %(strFile, strSpeak, strFile))

# Animal/           
# ------------------
# Bird, Owl
# Cat, Kitten, Meow
# Crickets, Cricket
# Dog1, Dog2
# Duck
# Goose
# HorseGallop, Horse
# Rooster
# SeaLion
# WolfHowl

sounds = {
	'Animal': {
		'Bird',		'Cat',		'Crickets',
		'Cricket',	'Dog1',		'Dog2',
		'Duck',		'Goose',	'HorseGallop',
		'Horse',	'Kitten', 	'Meow',
		'Owl',		'Rooster',	'SeaLion',
		'WolfHowl'},
	'Effects': {
		'BalloonScratch',		'BellToll',		'Bubbles',
		'CarPassing',			'DoorClose',	'DoorCreak',
		'MotorcyclePassing',	'Plunge',		'Pop',
		'Rattle',				'Ripples',		'SewingMachine',
		'Typing',				'WaterDrop',	'WaterRunning'},
	'Electronic': {
		'AlienCreak1',		'AlienCreak2',	'ComputerBeeps1',
		'ComputerBeeps2',	'DirtyWhir',	'Fairydust',
		'Laser1',			'Laser2',		'Peculiar',
		'Screech',			'SpaceRipple',	'Spiral',
		'Whoop',			'Zoop'},
	'Human': {
		'BabyCry',			'Cough-female',		'Cough-male',
		'FingerSnap',		'Footsteps-1',		'Footsteps-2',
		'Laugh-female',		'Laugh-male1',		'Laugh-male2',
		'Laugh-male3',		'PartyNoise',		'Scream-female',
		'Scream-male1',		'Scream-male2',		'Slurp',
		'Sneeze-female',	'Sneeze-male'},
	'Instruments': {
		'AfroString',	'Chord',		'Dijjeridoo',
		'GuitarStrum',	'SpookyString',	'StringAccent',
		'StringPluck',	'Suspense',		'Tambura',
		'Trumpet1',		'Trumpet2'},
	'Music Loops': {
		'Cave',				'DripDrop',		'DrumMachine',
		'Drum',				'DrumSet1',		'DrumSet2',
		'Eggs',				'Garden',		'GuitarChords1',
		'GuitarChords2',	'HipHop',		'HumanBeatbox1',
		'HumanBeatbox2',	'Jungle',		'Medieval1',
		'Medieval2',		'Techno2',		'Techno',
		'Triumph',			'Xylo1',		'Xylo2',
		'Xylo3',			'Xylo4'},
	'Percussion': {
		'CymbalCrash',	'DrumBuzz',		'Gong',
		'HandClap',		'RideCymbal',	'Shaker'},
	'Vocals': {
		'BeatBox1',		'BeatBox2',			'Come-and-play',
		'Doy-doy-doy',	'Got-inspiration',	'Hey-yay-hey',
		'Join-us',		'Oooo-badada',		'Singer1',
		'Singer2',		'Sing-me-a-song',	'Ya'}}

# sound abspielen
def sound(strSound):
	global sounds
	
	strFile = "/usr/share/scratch/Media/Sounds"
	strPlay = "aplay"
	
	for strDir, listSounds in sounds.items():
		if strSound in listSounds:
			strFile += "/" + strDir + "/" + strSound
			break

	if os.path.isfile(strFile + ".wav"):
		strFile += ".wav"
		strPlay = "aplay"
	elif os.path.isfile(strFile + ".mp3"):
		strFile += ".mp3"
		strPlay = "omxplayer"
	else:
		strFile = "/usr/share/scratch/Media/Sounds/Electronic/ComputerBeeps2.wav"

	if os.path.isfile(strFile):
		print('Now playing: "%s" <%s>' %(strSound, strFile))
		os.system('%s "%s"' %(strPlay, strFile))
	else:
		print("*** Error: File <%s> not found!" %strFile);

# Testroutine für sound abspielen
def testSound():
	global sounds

	for strKey, listSounds in sounds.items():
		for strSound in listSounds:
			sound(strSound)

# Glockenschlag
def gong(nCount):
	for i in range(nCount):
		os.system("aplay /usr/share/scratch/Media/Sounds/Effects/BellToll.wav");

# Akustische Zeitanzeige
def signalTime():
	global nHour24h
	global nMinutes

	if nMinutes == 0:	# Volle Stunde:
		gong(nHour12h)	# Anzahl Stunden schlagen	
	if nMinutes == 30:	# Halbe Stunde:
		gong(1)			# Einmal schlagen

# Akustische Zeitansage
def speakTime():
	global nHour12h
	global nMinutes
	global nTimeSpoken

	if nTimeSpoken > 0:
		return

	nTimeSpoken += 1

	strPart = "um"
	strNext = "viertel"
	nHour = nHour12h

	if nMinutes >= 45:
		strPart = "dreiviertel"
		strNext = "um"
		nHour += 1
	elif nMinutes >= 30:
		strPart = "halb"
		strNext = "dreiviertel"
		nHour += 1
	elif nMinutes >= 15:
		strPart = "viertel -"
		strNext = "halb"
		nHour += 1

	if nHour == 13:
		nHour = 1

	nMinutesPast = nMinutes % 15
	if nMinutesPast > 1 and nMinutesPast <= 5:
		strPart = "kurz nach " + strPart
	elif nMinutesPast > 5 and nMinutesPast <= 10:
		strPart = "nach " + strPart
	elif nMinutesPast > 10:
		strPart = "kurz vor " + strNext

	strSpeech = "Es ist jetzt " + strPart + " " + str(nHour)
	speak(strSpeech)

def tellEventsOnWorkingDays():
	global nHour24h
	global nMinutes
	
	time = False
	play = False
	talk = False

	if nHour24h == 6:
		if nMinutes >= 35 and nMinutes < 45:
			time = True
			play = "Horse"
			talk = "Es wird Zeit, mit dem Essen fertig zu werden."
			talk += " Bitte denkt daran, euer Geschirr abzuräumen."
		elif nMinutes >= 45:
			time = True
			play = "Horse"
			talk = "Bitte geht euch anziehen."
			talk += " Ich wünsche euch viel Spaß im Kindergarten."
			talk += " Tschüß, bis heute nachmittag."
			
	if nHour24h == 22:
		if nMinutes >= 45:
			time = True
			play = "WolfHowl"
			talk = "Es ist jetzt wirklich Zeit für's Bett."
			talk += " Bitte geht jetzt schlafen."
		elif nMinutes >= 30:
			time = True
			play = "WolfHowl"
			talk = "Es wird immer später."
			talk += " Ihr solltet schon längst im Bett sein."
		elif nMinutes >= 15:
			time = True
			play = "Owl"
			talk = "Es wird langsam spät."
			talk += " Ihr solltet schlafen gehen."
		else:
			time = True
			play = "Owl"
			talk = "Ihr solltet langsam schlafen gehen."

	if play:
		sound(play)
	if time:
		speakTime()
	if talk:
		speak(talk)
	
# Hauptprogramm
def main():
	updateTime()
	if (nMinutes % nTellTimeInt) == 0 and nHour24h < nSilenceFrom and nHour24h > nSilenceTo:
		signalTime()
		speakTime()
	elif bTestMode:
		speak("Entschuldigung. Testmodus.")
		signalTime()
		speakTime()

	if nDayWeek >= 0 and nDayWeek < 5:
		tellEventsOnWorkingDays()
		
# Ausführung des Hauptprogramms
if __name__ == '__main__':
	try:
		main()
	except Exception as ex:
		talk = "Marco? Hilfe!"
		talk += " In meinem Programm ist ein unerwarteter Fehler aufgetreten."
		talk += " Es wäre schön, wenn Du Dich zeitnah darum kümmern könntest."
		speak(talk)
		talk = "Hier sind die Details: " + "{0}".format(ex)
		speak(talk)

