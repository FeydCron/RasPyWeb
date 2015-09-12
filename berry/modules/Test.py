import os
import sys

import SDK
from SDK import ModuleBase

class Test(ModuleBase):
	def moduleInit(self, dictModCfg={}, dictCfgUsr={}):
		print("%r::moduleInit(%s)" % (self, SDK.getCpuTemp()))
		return True
		
	def moduleExit(self):
		print("%r::moduleExit()" % (self))
		return True
		
	def moduleExec(self, strPath, strCmd, strArg):
		print("%r::moduleExec(strPath=%s, strCmd=%s, strArg=%s)" % (
			self, strPath, strCmd, strArg))
		return True