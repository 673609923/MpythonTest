#mPythonType:0
from bluebit import LineFollow
import time
from mpython import Pin,oled
from machine import UART
import _thread
from time import sleep_ms
from bluebit import FanPWM
from mpython import MPythonPin,PinMode
from bluebit import Ultrasonic
from mpython import *

LF = LineFollow(0, 1)
LF.set_threshold([2000, 2000])


g_left_on = False
g_left_off = False
g_right_on = False
g_right_off = False

def on_button_a_pressed(_):
    global g_left_on,g_left_off,g_right_on,g_right_off
    g_left_on = False
    g_left_off = False
    g_right_on = False
    g_right_off = False
    


button_a.event_pressed = on_button_a_pressed

while True:
    
    try:
        oled.fill(0)
    
        if g_left_on and g_left_off and g_right_on and g_right_off:
            oled.DispChar(str('测试通过,按下A键继续'), 5, 25, 1,True)
            
        else:
  
            left = LF.detect(2)
            right = LF.detect(1)
    
            if left:
                g_left_on = True
            else:
                g_left_off = True
            
            if right:
                g_right_on = True
            else:
                g_right_off = True
                
            oled.DispChar(str('红外循迹测试'), 30, 5, 1,True)
            oled.DispChar(str('左: ' + str(left) + '   |   右: '+ str(right)), 30, 30, 1,True)
                
        oled.show()
        time.sleep(0.1)
        
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(1)
        machine.reset()