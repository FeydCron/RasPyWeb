import io
import time
import sys
import threading
import RPi.GPIO as IO
from threading import Thread
from subprocess import call

import SDK
from SDK import ModuleBase

VERBOSE = 0

class AMatisGPIO(ModuleBase):
	
	def moduleInit(self, dictModCfg={}, dictCfgUsr={}):
		global status
		
		status = 1
		
		print('init PI ' + str(IO.RPI_REVISION) + ' V'  + str(IO.VERSION))
		IO.setmode(IO.BOARD)
		IO.setup(I0,IO.IN,pull_up_down=IO.PUD_DOWN)
		IO.add_event_detect(I0, IO.BOTH, callback=in_cllbck, bouncetime=50)
		IO.setup(I1,IO.IN,pull_up_down=IO.PUD_DOWN)
		IO.add_event_detect(I1, IO.BOTH, callback=in_cllbck, bouncetime=50)  
		IO.setup(QBerry, IO.OUT)
		IO.setup(ch_list, IO.OUT)
		IO.output(ch_list,0)
		self.t1 = Thread(target=heartBeat)
		self.t1.setDaemon(1)
		self.t1.start()
		self.t2 = Thread(target=checkAlive)
		self.t2.setDaemon(1)
		self.t2.start()		
		
		IO.output(QBerry,1)
		return True
		
	def moduleExit(self):
		global status
		
		IO.cleanup()		
		status = 0
		self.t1.join()
		self.t2.join()
		return True
		
	def moduleExec(self, strPath, strCmd, strArg):
		if (strCmd == "ampel"):
			ampel(strArg)
		elif (strCmd == "alarm"):
			alarm(strArg)
		elif (strCmd == "status"):
			status(strArg)
		elif (strCmd == "alive"):
			#build rechner muss sich melden
			setAlive()
		elif (strCmd == "setClock"):
			setClock(strArg)
		return True

def prnt(text):
  if(VERBOSE and text):
    print(text)

class DuoLed:
  def __init__(self,r,g,io):#(Pin Rot, Pin Gruen, GPIO)
    self.r = r
    self.g = g
    self.IO = io
  def off(self):
    self.IO.output((self.r,self.g),0)
  def red(self):
    self.IO.output((self.r,self.g),0)
    self.IO.output(self.r,1)
  def grn(self):
    self.IO.output((self.r,self.g),0)
    self.IO.output(self.g,1)
  def ylw(self):
    self.IO.output((self.r,self.g),0)
    self.IO.output((self.r,self.g),1)
  def set(self, color):
    #r|R = red
    #y|Y = red
    #g|G = red
    #r|R = red
    if(color == '0' or color == 'o' or color == 'O'):
      self.IO.output((self.r,self.g),0)
    elif(color == 'r' or color == 'R'):
      self.IO.output((self.g),0)
      self.IO.output((self.r),1)
    elif(color == 'g' or color == 'G'):
      self.IO.output((self.r),0)
      self.IO.output((self.g),1)
    elif(color == 'y' or color == 'Y'):
      self.IO.output((self.r,self.g),1)
  #class DuoLed
  
status=1
I0 = 24
I1 = 26
QAR = 7
QAY = 5
QAG = 3
Q0r = 8
Q0g = 10
Q1r = 12
Q1g = 11
Q2r = 13
Q2g = 15
Q3r = 19
Q3g = 21
Q4r = 23
Q4g = 16
QBerry = 18
QRel = 22
L0 = DuoLed(Q0r,Q0g,IO)
L1 = DuoLed(Q1r,Q1g,IO)
L2 = DuoLed(Q2r,Q2g,IO)
L3 = DuoLed(Q3r,Q3g,IO)
L4 = DuoLed(Q4r,Q4g,IO)

eHlt = threading.Event()
eBtn = threading.Event()

ch_list = [QAR,QAY,QAG,Q0r,Q0g,Q1r,Q1g,Q2r,Q2g,Q3r,Q3g,Q4r,Q4g,QRel]
PORT = 80

isAlive = 0

def setLeds(leds):
  print('setLeds' + str(bin(leds)))
  if(status > 0):
    IO.output(Q0r,(leds>>1)&1)
    IO.output(QRel,(leds>>0)&1)
    IO.output(Q0g,(leds>>0)&1)
    IO.output(Q1r,(leds>>3)&1)
    IO.output(Q1g,(leds>>2)&1)
    IO.output(Q2r,(leds>>5)&1)
    IO.output(Q2g,(leds>>4)&1)
    IO.output(Q3r,(leds>>7)&1)
    IO.output(Q3g,(leds>>6)&1)

def ampel(ryg):
  if(status > 0):
    if(ryg == 'r' or ryg == 'R'):
      IO.output([QAR],1)
    elif(ryg == 'y' or ryg == 'Y'):
      IO.output([QAY],1)
    elif(ryg == 'g' or ryg == 'G'):
      IO.output([QAG],1)
    elif(ryg == 'o' or ryg == 'O' or ryg == '0'):
      IO.output([QAY,QAG],0)


def alarm(al):
  if(status > 0):
    if(al == 'on' or al == '1'):
      IO.output(QRel,1)
    elif(al == 'o' or al == 'O' or al == '0'):
      IO.output(QRel,0)

def setAlive():
  global isAlive
  if(isAlive<3):
    isAlive = isAlive+1

def alive():
  if(status > 0):
    if(isAlive > 1):
      IO.output([QAG],1)
    else:
      IO.output([QAG],0)
      IO.output([QAR],1)

def status(st):
  if(status > 0):
    ls = list(st)
    L0.set(ls[0])
    L1.set(ls[1])
    L2.set(ls[2])
    L3.set(ls[3])
    L4.set(ls[4])
    ampel(ls[5])
    alarm(ls[6])

def in_cllbck(ch):
  print('in_cllbck ' + str(ch) + str(IO.input(ch)))
  if(IO.input(I1)):
    eHlt.set()
  elif(IO.input(I0)):
    IO.output(ch_list,0)
	
def sysCall(cmd):
  try:
    call(cmd.split())
  except Exception as e:
    print(e)
	
def heartBeat():
  while(status != 0):
    on=0.5
    #getCPUuse()
    #off=(((60.0/(getCpuTemp()-20)))*1.5)-on
    off=(60.0/SDK.getCpuTemp())-on
    if(off>0.0):
      IO.output(QBerry,0)
      time.sleep(off)
    IO.output(QBerry,1)
    time.sleep(on)
	
def checkAlive():
  global isAlive
  i=0
  while(status != 0):
    time.sleep(1.0)
    if(i>7200):
      i=0
      isAlive = isAlive-1
    if(isAlive < 0):
      isAlive = 0
    i = i+1
    alive()
	