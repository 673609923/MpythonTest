#mPythonType:0
from bluebit import SoilHumiditySensor
import time
from mpython import *
from bluebit import MAX30102

soilHumidity_0 = SoilHumiditySensor(0)

g_isok = True

def on_button_a_pressed(_):
    global g_isok
    g_isok = False

button_a.event_pressed = on_button_a_pressed

while True:
    
    try:
        
        oled.fill(0)
    
        if g_isok:
            oled.DispChar(str('< 土壤湿度 >'), 30, 10, 1,True)
            oled.DispChar(str('按下A键测试'), 30, 30, 1,True)
            
        else:
            val = soilHumidity_0.get_raw_val()
        
            if val >= 1000:
                g_isok  = True
                
            oled.DispChar(str('土壤湿度传感器测试'), 14, 5, 1,True)
            oled.DispChar(str('数值: ' + str(val)), 18, 30, 1,True)
                
        oled.show()
        time.sleep(0.1)
        
    except Exception as e:
        oled.DispChar(str('发生错误1秒后自动重启：{}'.format(e)), 0, 0, 1,True)
        oled.show()
        time.sleep(3)
        machine.reset()
        
        
        
        

