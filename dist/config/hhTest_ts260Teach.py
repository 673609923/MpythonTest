from mpython import *
from machine import Timer, UART
import math
from bluebit import *
import time
import smartcamera_new as smartcamera
from bluebit import SHT20
from servo import Servo
from mpython import ledong_shield
import _thread
import music

# MAC id
machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
WIFI_SSID = "CYZN_Employee_7#10F"
WIFI_PASSWORD = "Sene@2024"
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
g_Servo_Index = 0
g_Servo_Direction = 1  
g_light_value = 0
g_wifi_comm_state = 0
g_wifi_comm_dBm = 0

sht20 = SHT20()
p2 = MPythonPin(2, PinMode.ANALOG)
g_servo_11 = Servo(11, min_us=500, max_us=2500, actuation_range=180)

ledong_shield.set_motor(1, 100)
p0 = MPythonPin(0, PinMode.OUT)  
p15 = MPythonPin(15, PinMode.OUT) 
p0.write_digital(1)
p15.write_digital(1)


print("摄像头初始化")
smart_camera = smartcamera.SmartCamera(tx=Pin.P14, rx=Pin.P13)

def test():
    global smart_camera
    print("进入工厂模式")
    smart_camera.factory_init()

    print("进入lcd屏幕测试")
    smart_camera.factory_lcd()
    time.sleep(5)
    
    print("进入摄像头测试")
    smart_camera.factory_sensor()
    time.sleep(5)


_thread.start_new_thread(test,())


def on_button_a_pressed(_):
    print('a')
    music.play("C4:4")
    music.stop()

def on_button_b_pressed(_):
    print('b')
    music.play("C4:4")
    music.stop()
    

button_a.event_pressed = on_button_a_pressed
button_b.event_pressed = on_button_b_pressed


def check_list_length(lst, expected_length):
    print(lst)
    return len(lst) == expected_length



def Servo_Neopixel():
    global g_Servo_Index
    global g_Servo_Direction  # 1 表示递增，-1 表示递减
    global g_light_value
    global g_servo_11
    
    if g_light_value > 50:
        # 更新逻辑
        g_Servo_Index += g_Servo_Direction
        
        # 到达边界时改变方向
        if g_Servo_Index >= 180:
            g_Servo_Index = 180
            g_Servo_Direction = -1  # 改为递减
            time.sleep(1)
        elif g_Servo_Index <= 0:
            g_Servo_Index = 0
            g_Servo_Direction = 1   # 改为递增
            time.sleep(1)
    
        g_servo_11.write_angle(g_Servo_Index)

      
      
def connect_wifi():
    global wlan
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(5):
            if wlan.isconnected():
                break
            time.sleep(1)
        if wlan.isconnected():
            print("WiFi Connected!")
            print("IP:", wlan.ifconfig()[0])
            return True
        else:
            print("Connection Failed")
            return False
    return True



def WifiCommTest():
    global g_wifi_comm_state
    while True:
        if connect_wifi():
            g_wifi_comm_state = 1
            return
        
rgb.fill(int(50), int(50), int(50))

tim2 = Timer(2)
tim2.init(period=8, mode=Timer.PERIODIC, callback=lambda t: Servo_Neopixel())
_thread.start_new_thread(WifiCommTest, ())

def get_signal_strength():
    if wlan.isconnected():
        return wlan.status("rssi")
    return 0
    
            
while True:
    print("----------------------------")
    if g_wifi_comm_state:
        g_wifi_comm_dBm = get_signal_strength()
    ledong_shield.set_motor(2, 60)
    i2cIsOk = int(check_list_length(i2c.scan(),6))
    g_light_value = int(light.read())
    print('temperature:%d' % sht20.temperature())                                       # 湿度
    print('humidity:%d' % sht20.humidity())                                             # 湿度
    print('light:%d' % g_light_value)                                                   # 光线
    print('slider:%d' % numberMap(p2.read_analog(),0,4095,0,100))                       # 滑块   
    print('Sound:%d' % sound.read())                                                    # 声音
    print('i2c:%d' % i2cIsOk)                                                           # i2c
    print('Wifi:%d,Name:%s,Pass:%s' % (g_wifi_comm_dBm, WIFI_SSID, WIFI_PASSWORD))      # wifi
    print('Mac:{}'.format(machine_id.upper()))                                          # MAC地址
    
    if smart_camera.a_status == 1:
        music.play("C4:4")
        music.stop()
    
    if smart_camera.b_status == 2:
        music.play("C4:4")
        music.stop()
    
    time.sleep_ms(100)






