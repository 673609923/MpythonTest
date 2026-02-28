#mPythonType:0
from mpython import *
from machine import Timer
from onewire import OneWire
from ds18x20 import DS18X20

# 创建one wire总线,引脚为P0
ow = OneWire(Pin(Pin.P0)) 
 # 实例DS18X20类
ds = DS18X20(ow)
g_isok = True


def on_button_a_pressed(_):
    print('A')
    global g_isok 
    g_isok = False
    


def on_button_b_pressed(_):
    print('B')


button_a.event_pressed = on_button_a_pressed
button_b.event_pressed = on_button_b_pressed

    
while True:
    
    
    oled.fill(0)
    
    if g_isok:
        
        oled.DispChar(str('< 温度测试 >'), 30, 10, 1,True)
        oled.DispChar(str('按下A键开始'), 30, 30, 1,True)
    else:
        # 扫描总线上的DS18B20，获取设备列表
        roms = ds.scan()  
        # 转换温度值,每次获取温度前必须调用convert_temp，否则温度数据不会更新
        ds.convert_temp()
        # 返回总线的上ds18b20设备的温度值
        val = float(ds.read_temp(roms[0]))
        
        if val > 20 and val < 40:
            g_isok = True
            time.sleep(1)
        
        oled.DispChar(str('温度测试'), 30, 5, 1,True)
        oled.DispChar(str('当前数值: ' + str(val)), 20, 30, 1,True)
        
    oled.show()
    
    time.sleep(0.1)
    
    
    
