from mpython import *
import audio
from machine import Timer, UART
import time, ubinascii, framebuf
import machine, music, audio
import ustruct, os
import _thread
import network
import urequests
from time import sleep,time
from mpython import *


machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
print('Mac:{}'.format(machine_id.upper()))  # MAC地址

WIFI_SSID = "TP-LINK_C5AB"
WIFI_PASSWORD = ""

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

g_GetDataLock = _thread.allocate_lock()
g_wifi_comm_state = 0
g_wifi_comm_dBm = 0
btn_a = 0
btn_b = 0
touch_p = 0
touch_y = 0
touch_t = 0
touch_h = 0
touch_o = 0
touch_n = 0
tim1 = Timer(1)
g_Color_Index = 0
g_GPIO_State = 0

p0 = MPythonPin(0, PinMode.OUT)  # OK
p1 = MPythonPin(1, PinMode.OUT)  # OK

p2 = MPythonPin(2, PinMode.OUT)  # OK
p3 = MPythonPin(3, PinMode.OUT)  # OK

p6 = MPythonPin(6, PinMode.OUT)  # OK
p7 = MPythonPin(7, PinMode.OUT)  # OK

p8 = MPythonPin(8, PinMode.OUT)  # OK
p9 = MPythonPin(9, PinMode.OUT)  # OK

p13 = MPythonPin(13, PinMode.OUT)  # OK
p14 = MPythonPin(14, PinMode.OUT)  # OK

p15 = MPythonPin(15, PinMode.OUT)  # OK
p16 = MPythonPin(16, PinMode.OUT)  # OK



def connect_wifi():
    try:
        global wlan
        if not wlan.isconnected():
            print("Connecting to WiFi...")
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            for _ in range(10):
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
    except Exception as e:
        time.sleep(5)
        return False
    
    


def WifiCommTest():
    global g_wifi_comm_state
    while True:
        if connect_wifi():
            g_wifi_comm_state = 1
            return


def record():
    print("1.录音开始")
    audio.record('2.wav', 5)
    time.sleep(6)
    print("2.录音结束")
    time.sleep(0.2)
    print("3.开始播放")
    audio.play('2.wav')
    print("4.播放结束")
    

def on_button_a_pressed(_):
    music.pitch(400, 100)
    global btn_a
    btn_a = 1


def on_button_b_pressed(_):
    music.pitch(400, 100)
    global btn_b
    btn_b = 1


def on_touchpad_p_pressed(_):
    global touch_p
    touch_p = 1


def on_touchpad_o_pressed(_):
    global touch_o
    touch_o = 1


def on_touchpad_y_pressed(_):
    global touch_y
    touch_y = 1


def on_touchpad_n_pressed(_):
    global touch_n
    touch_n = 1


def on_touchpad_t_pressed(_):
    global touch_t
    touch_t = 1


def on_touchpad_h_pressed(_):
    global touch_h
    touch_h = 1

 
touchpad_p.event_pressed = on_touchpad_p_pressed
touchpad_o.event_pressed = on_touchpad_o_pressed
touchpad_y.event_pressed = on_touchpad_y_pressed
touchpad_n.event_pressed = on_touchpad_n_pressed
touchpad_t.event_pressed = on_touchpad_t_pressed
touchpad_h.event_pressed = on_touchpad_h_pressed
button_a.event_pressed = on_button_a_pressed
button_b.event_pressed = on_button_b_pressed




def Rgb_Neopixel():
    global g_Color_Index
    global g_GPIO_State
    color = ((32, 0, 0), (0, 32, 0), (0, 0, 32))
    for i in range(0, 3):
        rgb[i] = color[g_Color_Index]
    rgb.write()
    g_Color_Index = g_Color_Index + 1
    g_Color_Index = g_Color_Index % 3



    if g_GPIO_State == 0:
        oled.fill(0)
        oled.show()
        g_GPIO_State = 1
    else:
        oled.fill(1)
        oled.show()
        g_GPIO_State = 0
        
    p0.write_digital(g_GPIO_State)
    p1.write_digital(g_GPIO_State)
    
    p2.write_digital(g_GPIO_State)
    p3.write_digital(g_GPIO_State)
    
    p6.write_digital(g_GPIO_State)
    p7.write_digital(g_GPIO_State)
    
    p8.write_digital(g_GPIO_State)
    p9.write_digital(g_GPIO_State)
    
    p13.write_digital(g_GPIO_State)
    p14.write_digital(g_GPIO_State)
    
    p15.write_digital(g_GPIO_State)
    p16.write_digital(g_GPIO_State)



def get_signal_strength():
    if wlan.isconnected():
        return wlan.status("rssi")
    return 0
    
    
tim1.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: Rgb_Neopixel())
_thread.start_new_thread(WifiCommTest, ())


def check_list_length(lst, expected_length):
    return len(lst) == expected_length
    
    
    
while True:
    if btn_a and btn_b:
        time.sleep(0.5)
        for freq in range(0, 3, 1):
            music.pitch(400, 90)
            time.sleep(0.1)
        record()
        btn_a = 0
        btn_b = 0


    if g_wifi_comm_state:
        g_wifi_comm_dBm = get_signal_strength()
        
    light_value = light.read()
    sound_value = sound.read()
    acc_x, acc_y, acc_z = accelerometer.get_x(), accelerometer.get_y(), accelerometer.get_z()
    gyroscope_x, gyroscope_y, gyroscope_z = gyroscope.get_x(), gyroscope.get_y(), gyroscope.get_z()
    magnetic_x, magnetic_y, magnetic_z = magnetic.get_x(), magnetic.get_y(), magnetic.get_z()
    SdaScl_value = int(check_list_length(i2c.scan(),7))

    print("----------------------------")
    print('Touch_P:%d,Touch_Y:%d,Touch_T:%d,Touch_H:%d,Touch_O:%d,Touch_N:%d' % (touch_p, touch_y, touch_t, touch_h,touch_o, touch_n))  # 触摸
    print('light:%d' % light_value)  # 光线
    print('Sound:%d' % sound_value)  # 声音
    print('Accel_X:%.2f,Accel_Y:%.2f,Accel_Z:%.2f' % (acc_x, acc_y, acc_z))  # 加速度
    print('Gyroscope_X:%.2f,Gyroscope_Y:%.2f,Gyroscope_Z:%.2f' % (gyroscope_x, gyroscope_y, gyroscope_z))  # 陀螺仪
    print('Magnetic_X:%.2f,Magnetic_Y:%.2f,Magnetic_Z:%.2f' % (magnetic_x, magnetic_y, magnetic_z))  # 磁力计
    print('Wifi:%d,Name:%s,Pass:%s' % (g_wifi_comm_dBm, WIFI_SSID, WIFI_PASSWORD))  # WIFI
    print('SdaScl:%d' % SdaScl_value)            # SDA/SCL
    print('Mac:{}'.format(machine_id.upper()))  # MAC地址


    time.sleep(0.5)


