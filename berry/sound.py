import os.path
import re

import globs

class Sound:
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
	
	s_sounds = {
		'Animal': [
			'Bird',		'Cat',		'Crickets',
			'Cricket',	'Dog1',		'Dog2',
			'Duck',		'Goose',	'HorseGallop',
			'Horse',	'Kitten', 	'Meow',
			'Owl',		'Rooster',	'SeaLion',
			'WolfHowl'],
		'Effects': [
			'BalloonScratch',		'BellToll',		'Bubbles',
			'CarPassing',			'DoorClose',	'DoorCreak',
			'MotorcyclePassing',	'Plunge',		'Pop',
			'Rattle',				'Ripples',		'SewingMachine',
			'Typing',				'WaterDrop',	'WaterRunning'],
		'Electronic': [
			'AlienCreak1',		'AlienCreak2',	'ComputerBeeps1',
			'ComputerBeeps2',	'DirtyWhir',	'Fairydust',
			'Laser1',			'Laser2',		'Peculiar',
			'Screech',			'SpaceRipple',	'Spiral',
			'Whoop',			'Zoop'],
		'Human': [
			'BabyCry',			'Cough-female',		'Cough-male',
			'FingerSnap',		'Footsteps-1',		'Footsteps-2',
			'Laugh-female',		'Laugh-male1',		'Laugh-male2',
			'Laugh-male3',		'PartyNoise',		'Scream-female',
			'Scream-male1',		'Scream-male2',		'Slurp',
			'Sneeze-female',	'Sneeze-male'],
		'Instruments': [
			'AfroString',	'Chord',		'Dijjeridoo',
			'GuitarStrum',	'SpookyString',	'StringAccent',
			'StringPluck',	'Suspense',		'Tambura',
			'Trumpet1',		'Trumpet2'],
		'Music Loops': [
			'Cave',				'DripDrop',		'DrumMachine',
			'Drum',				'DrumSet1',		'DrumSet2',
			'Eggs',				'Garden',		'GuitarChords1',
			'GuitarChords2',	'HipHop',		'HumanBeatbox1',
			'HumanBeatbox2',	'Jungle',		'Medieval1',
			'Medieval2',		'Techno2',		'Techno',
			'Triumph',			'Xylo1',		'Xylo2',
			'Xylo3',			'Xylo4'],
		'Percussion': [
			'CymbalCrash',	'DrumBuzz',		'Gong',
			'HandClap',		'RideCymbal',	'Shaker'],
		'Vocals': [
			'BeatBox1',		'BeatBox2',			'Come-and-play',
			'Doy-doy-doy',	'Got-inspiration',	'Hey-yay-hey',
			'Join-us',		'Oooo-badada',		'Singer1',
			'Singer2',		'Sing-me-a-song',	'Ya']}
	
	###########################################################################
	# Konstruktor
	#
	def __init__(self):
		pass
		return
	
	# Sound abspielen
	def sound(self, strSound):
		strFile = None
		strPlay = "aplay"
		
		# >>> Critical Section
		globs.s_oSettingsLock.acquire()
		try:
			if "Sounds" in globs.s_dictSettings:
				# Direkte Übereinstimmung finden
				for (strCategory, dictSounds) in globs.s_dictSettings["Sounds"].items():
					if strSound in dictSounds:
						strFile = globs.s_dictSettings["Sounds"][strCategory][strSound]
						break
				if not strFile:
					# Partiellen Treffer finden
					for (strCategory, dictSounds) in sorted(globs.s_dictSettings["Sounds"].items()):
						for (strName, strPath) in dictSounds.items():
							if re.match(".*" + strSound + ".*", strName):
								globs.log("Sound '%s' für angeforderten Sound '%s' verwendet." % (
									strName, strSound))
								strFile = strPath
								break
		except:
			globs.exc("Sound '%s' finden" % (strSound))
		globs.s_oSettingsLock.release()
		# <<< Critical Section
		
		if not strFile:
			globs.wrn("Der angeforderte Sound konnte nicht gefunden werden: '%s'" % (strSound))
			print("\\a")
			return
	
		if os.path.isfile(strFile):
			if re.match(".*\\.[Ww][Aa][Vv]", strFile):
				strPlay = "aplay"
			elif re.match(".*\\.[Mm][Pp]3", strFile):
				strPlay = "omxplayer -o both"
			else:
				globs.wrn("Das Format der Sound-Datei wird nicht unterstützt: '%s'" % (strFile))
				print("\\a")
				return
		else:
			globs.wrn("Die Datei des angeforderten Sounds ist ungültig: '%s'" % (strFile))
			print("\\a")
			return
			
		print("Now playing: '%s' <%s>" %(strSound, strFile))
		os.system('%s "%s"' %(strPlay, strFile))
		return
