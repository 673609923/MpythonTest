from machine import Timer, UART
from mpython import *
from bluebit import EncoderMotor
import time, ubinascii, framebuf
import machine, music, audio
import ustruct, os
import _thread
import network
import socket
import urequests
from mpython import *
from mfrc import *
import lcd 
from hcsr04 import HCSR04
from servo import Servo

# MAC id
machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
print('Mac:{}'.format(machine_id.upper()))   # MAC地址

while True:
    # MAC地址
    print('7001_X Mac:{}'.format(machine_id.upper()))          
    time.sleep(1)