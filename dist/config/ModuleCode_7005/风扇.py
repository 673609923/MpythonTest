from mpython import *
from bluebit import FanPWM
import time

fanpwm0 = FanPWM(0)

while True:
    fanpwm0.pwm(50)
    oled.fill(0)
    oled.DispChar(str('< 风扇测试 >'), 30, 5, 1,True)
    oled.show()
    

