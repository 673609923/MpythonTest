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
servo_0 = Servo(23, min_us=2500, max_us=500, actuation_range=180)

# MAC id
machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
print('Mac:{}'.format(machine_id.upper()))   # MAC地址

servo_0.write_angle(90)

while True:
    # MAC地址
    print('7001_C Mac:{}'.format(machine_id.upper()))          
    time.sleep(1)