from machine import Timer, UART
from mpython import *
import time, ubinascii, framebuf
import machine, music, audio
import ustruct, os
import _thread
import network
import socket
import urequests
from touchpad import TouchPad
from mpython import ledong_shield
import sensor
import lcd
import touchpad
from mpython import *

import ui

# MAC id
machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
print('Mac:{}'.format(machine_id.upper()))   # MAC地址

while True:
    # MAC地址
    print('Mac:{}'.format(machine_id.upper()))          
    time.sleep(1)