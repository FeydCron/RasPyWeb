from sdk import LongTask

class TaskCheckForUpdates(LongTask):
	
	def __init__(self, oWorker):
		super(TaskCheckForUpdates, self).__init__(oWorker)
		return
		
	def __str__(self):
		strDesc = "Programmaktualisierung suchen"
		return  strDesc
	
	def do(self):
		
		return
	
	def requestGet(self, strURL):
		
		return
