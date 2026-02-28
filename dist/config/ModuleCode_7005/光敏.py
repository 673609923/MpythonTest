#mPythonType:0
from mpython import *
import time
import math

p0 = MPythonPin(0, PinMode.ANALOG)

while True:
    oled.fill(0)
    oled.DispChar(str('< 光敏测试 >'), 30, 10, 1,True)
    oled.show()
    print(p0.read_analog())
    time.sleep(0.2)
