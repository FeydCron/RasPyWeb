import ptvsd
ptvsd.enable_attach("debug")

import threading

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
	main()
