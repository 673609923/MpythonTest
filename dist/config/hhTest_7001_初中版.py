from machine import Timer, UART
from mpython import *
from bluebit import EncoderMotor
import time, ubinascii, framebuf
import machine, music, audio
import ustruct, os
import _thread
import network
import socket
import urequests
from mpython import *
from mfrc import *
import lcd 
from hcsr04 import HCSR04
from servo import Servo

servo_0 = Servo(23, min_us=2500, max_us=500, actuation_range=180)
hcsr04 = HCSR04(trigger_pin=Pin.P25, echo_pin=Pin.P24)
rfid1 = Rfid(i2c = i2c, i2c_addr = 43)
rfid2 = Rfid(i2c = i2c, i2c_addr = 47)


def check_list_length(lst, expected_length):
    return len(lst) == expected_length


WIFI_SSID = "TP-LINK_C5AB"
WIFI_PASSWORD = ""



wlan = network.WLAN(network.STA_IF)
wlan.active(True)


g_GetDataLock = _thread.allocate_lock()
g_wifi_comm_state = 0
g_wifi_comm_dBm = 0
g_isRecordPlay = False
btn_a = 0
btn_b = 0



p0 = MPythonPin(0, PinMode.OUT)  # OK
p1 = MPythonPin(1, PinMode.OUT)  # OK
p2 = MPythonPin(2, PinMode.OUT)  # OK
p3 = MPythonPin(3, PinMode.OUT)  # OK

g_Servo_Index = 0
g_Servo_Direction = 1  # 初始方向：递增

g_Color_Index = 0
FREQ = 2000
FREQ_RNAG = 0.2
PEAK = 6000


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



def record():
    print("record_1")
    audio.play('GuangboTicao.mp3')
    print("record_2")
    time.sleep(5)



# MAC id
machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()


def on_button_a_pressed(_):
    music.pitch(400, 100)
    global btn_a
    btn_a = 1


# button B
def on_button_b_pressed(_):
    music.pitch(400, 100)
    global btn_b
    btn_b = 1



button_a.event_pressed = on_button_a_pressed
button_b.event_pressed = on_button_b_pressed

# 创建定时器1
tim1 = Timer(1)
tim2 = Timer(2)
g_Color_Index = 0
g_GPIO_State = 0


def Rgb_Neopixel():
    
    # 板载RGB测试
    global g_Color_Index
    global g_GPIO_State
    
    color = ((200, 0, 0), (0, 200, 0), (0, 0, 200))
    lcdColor = (lcd.RED, lcd.GREEN, lcd.BLUE)
    rgb.fill(color[g_Color_Index]) 
    rgb.write()
    
    g_Color_Index = g_Color_Index + 1
    g_Color_Index = g_Color_Index % 3

    
    
    lcd.draw_color(lcdColor[g_Color_Index])
    
    if g_GPIO_State == 0:
        g_GPIO_State = 1
    else:
        g_GPIO_State = 0

    
    p0.write_digital(g_GPIO_State)
    p1.write_digital(g_GPIO_State)
    p2.write_digital(g_GPIO_State)
    p3.write_digital(g_GPIO_State)


def Servo_Neopixel():
    global g_Servo_Index
    global g_Servo_Direction  # 1 表示递增，-1 表示递减
    global g_isRecordPlay
    
    if not g_isRecordPlay:
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
            music.pitch(200, 100)
            time.sleep(2)
    
        servo_0.write_angle(g_Servo_Index)



tim1.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: Rgb_Neopixel())
tim2.init(period=10, mode=Timer.PERIODIC, callback=lambda t: Servo_Neopixel())


_thread.start_new_thread(WifiCommTest, ())


def get_signal_strength():
    if wlan.isconnected():
        return wlan.status("rssi")
    return 0
    

    
while True:
    
    g_GetDataLock.acquire()
    
    if btn_a and btn_b:
        time.sleep(0.5)
        ledong_shield.set_motor(1, 0)
        g_isRecordPlay = True
        accelerometer.set_nvs_offset(0,0,0)
        for freq in range(0, 3, 1):
            music.pitch(400, 90)
            time.sleep(0.1)
        time.sleep(0.5)
        record()
        btn_a = 0
        btn_b = 0
        g_isRecordPlay = False

    print("----------------------------")

    if g_wifi_comm_state:
        g_wifi_comm_dBm = get_signal_strength()
        
    light_value = light.read()
    sound_value = sound.read()
    ultrasound_value = hcsr04.distance_mm()
    ir1_value = ir1.read()
    ir2_value = ir2.read()
    rfid1_value = str(rfid1.get_serial_num())
    rfid2_value = str(rfid2.get_serial_num())
    temperature_value = int(sht20.temperature())
    humiture_value = int(sht20.humidity())
    acc_x, acc_y, acc_z = accelerometer.get_x(), accelerometer.get_y(), accelerometer.get_z()
    SdaScl_value = int(check_list_length(i2c.scan(),9))
    
    

    # 光线
    print('light:%d' % light_value)                     
    
    # 声音
    print('Sound:%d' % sound_value)                     
    
    # 超声波
    print('Ultrasound:%d' % ultrasound_value)           
    
    # 红外探测
    print('Ir1:%d,Ir2:%d' % (ir1_value,ir2_value))      
    
    # RFID 1
    print('Rfid1:%s' % rfid1_value)          
    
    # RFID 2
    print('Rfid2:%s' % rfid2_value) 
    
    # 温度
    print('Humiture:%d' % temperature_value)  
    
    # 湿度
    print('Temperature:%d' % humiture_value) 
    
    # 加速度
    print('Accel_X:%.2f,Accel_Y:%.2f,Accel_Z:%.2f' % (acc_x, acc_y, acc_z)) 
    
    # WIFI
    print('Wifi:%d,Name:%s,Pass:%s' % (g_wifi_comm_dBm, WIFI_SSID, WIFI_PASSWORD))  
    
    # SDA/SCL
    print('SdaScl:%d' % SdaScl_value)  

    # MAC地址
    print('Mac:{}'.format(machine_id.upper()))          

    # 风扇
    ledong_shield.set_motor(1, 60)
    
    #水泵
    ledong_shield.set_motor(2, 200)

    
    g_GetDataLock.release()
    
    time.sleep(0.5)


