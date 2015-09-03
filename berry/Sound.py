import os
import os.path

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
		strFile = "/usr/share/scratch/Media/Sounds"
		strPlay = "aplay"
	    
		for strDir, listSounds in self.s_sounds.items():
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
		return
	
	# Testroutine für Sound abspielen
	def testSound(self):
		for strKey, listSounds in self.s_sounds.items():
			for strSound in listSounds:
				sound(strSound)
		return
