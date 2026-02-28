from bluebit import EncoderMotor
import time
from mpython import Pin,oled
from machine import UART
import _thread
from time import sleep_ms
from bluebit import FanPWM
from mpython import MPythonPin,PinMode
from bluebit import Ultrasonic
from mpython import *

encoder_motor = EncoderMotor()


g_is_reversal = True

def on_button_a_pressed(_):
    global g_is_reversal
    g_is_reversal = False
    


button_a.event_pressed = on_button_a_pressed

while True:
    
    try:
        oled.fill(0)
        
        if g_is_reversal:
            oled.DispChar(str('< 驱动板|电机|水泵 >'), 5, 10, 1,True)
            oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
        else:
            oled.DispChar(str('驱动器|编码电机|水泵'), 5, 5, 1,True)
            oled.DispChar(str('测试中,正常运行则OK'), 5, 25, 1,True)
            
            time.sleep(1)
            encoder_motor.setvater_pump(100)
            encoder_motor.motor_run(1,100)
            encoder_motor.motor_run(2,100)
            time.sleep(5)
        oled.show()
        
    except Exception as e:
        oled.DispChar(str('<发生错误5秒后重启>'), 5, 42, 1,True)
        oled.show()
        time.sleep(5)
        machine.reset()
        
        
        
        
        