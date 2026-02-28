from mpython import *
from bluebit import *
from machine import Timer


scan_rfid = Scan_Rfid()
g_isok = True

def on_button_a_pressed(_):
    print('A')
    global g_isok 
    g_isok = False
    

button_a.event_pressed = on_button_a_pressed

    
while True:
    
    oled.fill(0)
    
    if g_isok:
        time.sleep(1)
        oled.DispChar(str('< RFID测试 >'), 30, 10, 1,True)
        oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
    else:
        
        oled.DispChar(str('电子标签测试'), 27, 5, 1,True)
        
        rf = scan_rfid.scanning()
        if rf:
            g_isok = True
        
    oled.show()
    
    time.sleep(0.1)
    
    


