import cgi
import os
import re
import traceback
import uuid
import html
import zipfile
import ssl
import http.client

from urllib.parse import urlparse
from urllib.parse import parse_qsl
from datetime import datetime
from collections import OrderedDict
from zipfile import ZipFile

import SDK
from SDK import FastTask
from SDK import LongTask

from Worker import FutureTask

from Globs import Globs

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