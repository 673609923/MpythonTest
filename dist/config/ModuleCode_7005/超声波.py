from mpython import Pin,oled
from machine import UART
import _thread
from time import sleep_ms
from bluebit import FanPWM
from mpython import MPythonPin,PinMode
from bluebit import Ultrasonic
from mpython import *

ultrasonic = Ultrasonic()

ultrasonic_MaxVal = True
ultrasonic_MinVal = True


def on_button_a_pressed(_):
    print('A')
    global ultrasonic_MaxVal,ultrasonic_MinVal 
    ultrasonic_MaxVal = False
    ultrasonic_MinVal = False
    


def on_button_b_pressed(_):
    print('B')


button_a.event_pressed = on_button_a_pressed
button_b.event_pressed = on_button_b_pressed



        
while True:
    
    try:
        oled.fill(0)
    
        if ultrasonic_MinVal and ultrasonic_MaxVal:
            oled.DispChar(str('< 超声波 >'), 35, 10, 1,True)
            oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
            
        else:
            val = int(ultrasonic.distance())
        
            if val > 0 and val < 20:
                ultrasonic_MinVal = True
            
            if val >= 190:
                ultrasonic_MaxVal = True
                
            oled.DispChar(str('超声波测试'), 30, 5, 1,True)
            oled.DispChar(str('当前数值: ' + str(val)), 20, 30, 1,True)
            
        oled.show()
        
        time.sleep(0.1)
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(1)
        machine.reset()
        
    
    
    