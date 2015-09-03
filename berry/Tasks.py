from Voice import Voice
from Sound import Sound
from Clock import Clock
from Globs import Globs

class QueueTask:
	
	def __init__(self, oWorker):
		
		self.m_oWorker = oWorker
		return
	
	def start(self):
		
		self.m_oWorker.m_oQueue.put(self)
		return
	
	def do(self):
		return

class TaskQueueStop(QueueTask):
	
	def do(self):
		self.m_oWorker.m_bIsQueueShutdown = True
		return

class TaskSpeak(QueueTask):
	
	s_oVoice = Voice("de-DE")
	
	def __init__(self, oWorker, strSpeak):
		super(TaskSpeak, self).__init__(oWorker)
		self.m_strSpeak = strSpeak
		return
	
	def do(self):
		self.s_oVoice.speak(self.m_strSpeak)
		return

class TaskSound(QueueTask):
	
	s_oSound = Sound()
	
	def __init__(self, oWorker, strSound):
		super(TaskSound, self).__init__(oWorker)
		self.m_strSound = strSound
		return
	
	def do(self):
		self.s_oSound.sound(self.m_strSound)
		return
		
class TaskClock(QueueTask):
	
	s_oClock = Clock()
	
	def __init__(self, oWorker, strMode):
		super(TaskClock, self).__init__(oWorker)
		self.m_strMode = strMode
		return
	
	def do(self):
		if self.m_strMode == "gong":
			self.s_oClock.updateTime()
			self.s_oClock.gong()
		elif self.m_strMode == "speak":
			self.s_oClock.updateTime()
			self.s_oClock.speakTime()
		else:
			self.s_oClock.run()
		return
		
class TaskExit(QueueTask):
	
	def __init__(self, oWorker, strMode):
		super(TaskExit, self).__init__(oWorker)
		self.m_strMode = strMode
		return
	
	def do(self):
		Globs.s_strExitMode = self.m_strMode
		return
