#mPythonType:0
from mpython import *
from bluebit import MAX30102
import time

g_isok = True

def on_button_a_pressed(_):
    global g_isok
    g_isok = False

button_a.event_pressed = on_button_a_pressed

while True:
    
    try:
        
        oled.fill(0)
    
        if g_isok:
            oled.DispChar(str('< 心率血氧 >'), 30, 10, 1,True)
            oled.DispChar(str('按下A键开始'), 30, 25, 1,True)
            
        else:
            max30102 = MAX30102()
            temp = max30102.read_fifo()[0]
        
            if temp >= 10000:
                g_isok  = True
                
            oled.DispChar(str('心率血氧测试'), 18, 5, 1,True)
            oled.DispChar(str('数值: ' + str(temp)), 15, 30, 1,True)
                
        oled.show()
        time.sleep(0.1)
        
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(3)
        machine.reset()
        
        
        
        

