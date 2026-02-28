from mpython import Pin,oled
from machine import UART
import _thread
from time import sleep_ms
from bluebit import FanPWM
from mpython import MPythonPin,PinMode
from bluebit import Ultrasonic
from mpython import *


p0 = MPythonPin(0, PinMode.IN)

def boolean_P0():
    return p0.read_digital() == 1
    
    
    

g_istrue = True
g_isfalse = True


def on_button_a_pressed(_):
    global g_istrue,g_isfalse 
    g_istrue = False
    g_isfalse = False
    


button_a.event_pressed = on_button_a_pressed


        
while True:
    
    try:
        oled.fill(0)
    
        if g_isfalse and g_istrue:
            oled.DispChar(str('< 人体感应 >'), 30, 10, 1,True)
            oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
            
        else:
            val = boolean_P0()
        
            if val:
                g_isfalse = True
            else:
                g_istrue = True
                
            oled.DispChar(str('人体感应测试'), 27, 5, 1,True)
            if val:
                oled.DispChar(str('当前检测到有人!'), 20, 30, 1,True)
            else:
                oled.DispChar(str('当前检测到无人.'), 20, 30, 1,True)
            
        oled.show()
        
        time.sleep(0.1)
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(1)
        machine.reset()
        
    
    
    