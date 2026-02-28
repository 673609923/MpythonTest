import time
import math
from bluebit import LineFollow
from mpython import Pin,oled
from machine import UART
from time import sleep_ms
from bluebit import FanPWM
from mpython import MPythonPin,PinMode
from bluebit import Ultrasonic
from mpython import *

p0 = MPythonPin(0, PinMode.ANALOG)


g_wmd_min_ok = True
g_wmd_max_ok = True

def on_button_a_pressed(_):
    global g_wmd_min_ok,g_wmd_max_ok
    g_wmd_min_ok = False
    g_wmd_max_ok = False
    


button_a.event_pressed = on_button_a_pressed


while True:
    
    try:
        oled.fill(0)
    
        if g_wmd_min_ok and g_wmd_max_ok:
            oled.DispChar(str('< 旋钮电位器度 >'), 20, 10, 1,True)
            oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
            
        else:
  
            val = p0.read_analog()
    
            if val == 0:
                g_wmd_min_ok = True
            elif val >= 4095:
                g_wmd_max_ok = True
            
                
            oled.DispChar(str('旋钮电位器'), 30, 5, 1,True)
            oled.DispChar(str('数值: ' + str(val)), 30, 30, 1,True)
                
        oled.show()
        
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(1)
        machine.reset()
        


