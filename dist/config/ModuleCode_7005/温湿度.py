#mPythonType:0
from mpython import *
from machine import Timer
from machine import Timer
from onewire import OneWire
from ds18x20 import DS18X20
import dht
import time

dht11 = dht.DHT11(Pin(Pin.P0))

tim15 = Timer(15)

def timer15_tick(_):
    try: dht11.measure()
    except: pass
tim15.init(period=1000, mode=Timer.PERIODIC, callback=timer15_tick)




# 创建one wire总线,引脚为P0
ow = OneWire(Pin(Pin.P0)) 
 # 实例DS18X20类
ds = DS18X20(ow)
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
        oled.DispChar(str('< 温湿度测试 >'), 25, 10, 1,True)
        oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
    else:
        temperature = dht11.temperature()
        humidity = dht11.humidity()

        
        if temperature > 20 and temperature < 40 and humidity > 20 and humidity < 70:
            g_isok = True
        
        oled.DispChar(str('温湿度测试'), 30, 5, 1,True)
        oled.DispChar(str('温度: ' + str(temperature)), 20, 20, 1,True)
        oled.DispChar(str('湿度: ' + str(humidity)), 20, 40, 1,True)
        
    oled.show()
    
    time.sleep(0.1)
    
    
    
