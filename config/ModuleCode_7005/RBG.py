#mPythonType:0
from mpython import *
import time
import neopixel

my_rgb = neopixel.NeoPixel(Pin(Pin.P0), n=1, bpp=3, timing=1)

while True:
    oled.fill(0)
    oled.DispChar(str('< RGB灯测试 >'), 27, 10, 1,True)
    oled.show()
    my_rgb.fill( (10, 10, 10) )
    my_rgb.write()
    time.sleep(1)
