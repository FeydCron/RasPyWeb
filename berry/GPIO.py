import io
import time
import sys
import threading
import RPi.GPIO as IO
from subprocess import call, Popen, PIPE
import SimpleHTTPServer
import SocketServer
from threading import Thread
from subprocess import call

import SDK
from SDK import ModuleBase

VERBOSE = 0

class AMatisGPIO(ModuleBase):



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


	