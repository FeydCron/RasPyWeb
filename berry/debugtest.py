#import ptvsd
#ptvsd.enable_attach("debug")

import threading
import globs
import sdk

def main():
	global nCount

#	ptvsd.wait_for_attach()
#	ptvsd.break_into_debugger()
	
	nCount = 0
	threading.Timer(2.0, onTimer).start()   

	return

def onTimer():
	global nCount

#	ptvsd.break_into_debugger()

	nCount += 1
	print("onTimer is running for " + str(nCount) + " times - waiting 2 seconds ...")
	threading.Timer(2.0, onTimer).start()
	return

if __name__ == '__main__':
#	main()
	pass
	sdk.fetchImapEmail(
		"imap.gmail.com",
		"ed303239@gmail.com",
		"RasPyWeb geht online")
