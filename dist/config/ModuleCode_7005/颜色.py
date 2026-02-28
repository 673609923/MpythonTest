#mPythonType:0
from mpython import *
from bluebit import *
import time

g_black_is_ok = True
g_white_is_ok = True

def on_button_a_pressed(_):
    global g_black_is_ok,g_white_is_ok
    g_black_is_ok = False
    g_white_is_ok = False


button_a.event_pressed = on_button_a_pressed

color = Color()
while True:
    
    try:
        oled.fill(0)
    
        if g_black_is_ok and g_white_is_ok:
            oled.DispChar(str('< 颜色 >'), 40, 10, 1,True)
            oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
        else:
  
            val = color.getRGB()
            print(val[0])
            print(val[1])
            print(val[2])
            
            if val[0] < 50 and val[1] < 50 and val[2] < 50:
                g_black_is_ok = True
                
            if val[0] > 200 and val[1] > 200 and val[2] > 200:
                g_white_is_ok = True 

            
            oled.DispChar(str('颜色'), 30, 5, 1,True)
            oled.DispChar(str('白: ' + str(g_white_is_ok)), 30, 20, 1,True)
            oled.DispChar(str('黑: ' + str(g_black_is_ok)), 30, 40, 1,True)
                
            if g_black_is_ok and g_white_is_ok:
                oled.show()
                time.sleep(1)
        oled.show()
        
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(1)
        machine.reset()
        
    oled.fill(0)


