from mpython import *
import smartcamera_new as smartcamera
import _thread
from machine import UART,reset
from time import sleep_ms
from music import play
from time import time
from machine import Timer, UART
import time, ubinascii, framebuf
import machine, music, audio
import ustruct, os
import _thread
import network
import socket
import urequests
from time import sleep,time
from mpython import *

global smart_camera

aIsOk = False
bIsOk = False

def on_button_a_pressed(_):
    print("掌控板 A 按键")
    global aIsOk，bIsOk
    if bIsOk and bIsOk:
        reset()
          
button_a.event_pressed = on_button_a_pressed  

oled.fill(0)
oled.DispChar(str('正在连接摄像头请稍后...'), 0, 0, 1)
oled.show()

smart_camera = smartcamera.SmartCamera(tx=Pin.P0, rx=Pin.P1)
smart_camera.factory_init()


oled.fill(0)
oled.DispChar(str('打开LED灯测试'), 0, 0, 1)
oled.show()
smart_camera.factory_light(1)
sleep_ms(2000)


oled.fill(0)
oled.DispChar(str('屏幕RGB测试'), 0, 0, 1)
oled.show()
smart_camera.factory_lcd()                
sleep_ms(8000)
    
oled.fill(0)
oled.DispChar(str('摄像头,AB按键测试'), 0, 0, 1)
oled.show()
smart_camera.factory_sensor()
    

while True:
    
    if not aIsOk:
        if smart_camera.a_status == 1:   
            oled.fill(0)
            oled.DispChar(str('按键A按下 OK'), 0, 0, 1)
            oled.show()
            aIsOk = True
            
    if not bIsOk:    
        if smart_camera.b_status == 1:
            oled.fill(0)
            oled.DispChar(str('按键B按下 OK'), 0, 0, 1)
            oled.show()
            bIsOk = True
        
    if aIsOk and bIsOk:
        oled.fill(0)
        oled.DispChar(str('测试完成,按下A按继续'), 5, 20, 1)
        oled.show()
        
    time.sleep(0.1)

