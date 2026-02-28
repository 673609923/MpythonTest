from machine import Timer, UART
from mpython import *
import time, ubinascii, framebuf
import machine, music,audio
import ustruct,os
import _thread

# WIFI_SSID = "TP-LINK_C5AB"
# WIFI_PASSWORD = ""


WIFI_SSID = "CYZN_Employee_7#10F"
WIFI_PASSWORD = "Sene@2024"

g_wifi_comm_state = 0
g_wifi_comm_dBm = 0

wlan = network.WLAN(network.STA_IF)
wlan.active(True)


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
        
 
P0 = MPythonPin(0, PinMode.ANALOG)
P1 = MPythonPin(1, PinMode.ANALOG)
P2 = MPythonPin(2, PinMode.ANALOG)
#P3 = MPythonPin(3, PinMode.ANALOG)

# # 引脚PWM测试
# P8 = MPythonPin(8, PinMode.PWM)
# P9 = MPythonPin(9, PinMode.PWM)
# P13 = MPythonPin(13, PinMode.PWM)
# P14 = MPythonPin(14, PinMode.PWM)
# P15 = MPythonPin(15, PinMode.PWM)
# P16 = MPythonPin(16, PinMode.PWM)

# P8.write_analog(512,20)
# P9.write_analog(512,20)
# P13.write_analog(512,20)
# P14.write_analog(512,20)
# P15.write_analog(512,20)
# P16.write_analog(512,20)



def record(file='test.wav'):
    rgb.write()
    audio.recorder_init()
    rgb[0] = (255, 0, 0)  # 用LED指示录音开始结束
    rgb.write()
    audio.record(file, 1)
    rgb[0] = (0, 0, 0)
    rgb.write()
    audio.recorder_deinit()



# MAC id
machine_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
_thread.start_new_thread(WifiCommTest, ())


# 创建定时器1
tim1 = Timer(1)
tim2 = Timer(2)
color_index = 0
show_index = 0

def Rgb_Neopixel():
    """板载RGB测试"""
    global color_index
    color = ((32, 0, 0), (0, 32, 0), (0, 0, 32))
    for i in range(0, 3):
        rgb[i] = color[color_index]
    rgb.write()
    color_index = color_index + 1
    color_index = color_index % 3


def Oled_Test():
    """屏幕测试"""
    global show_index
    oled.fill(show_index)
    oled.show()
    show_index = not show_index
    
def automatic_calibration(num=3):
    print('自动校准开始')
    
    # 先重置偏移量
    try:
        accelerometer.set_offset(0, 0, 0)
        gyroscope.set_offset(0, 0, 0)
    except Exception as e:
        print("重置偏移量失败:", e)
    
    a_x_sum = 0
    a_y_sum = 0
    a_z_sum = 0
    g_x_sum = 0
    g_y_sum = 0
    g_z_sum = 0

    # 验证num参数
    if num <= 0:
        print("错误: 采样次数必须大于0")
        return

    try:
        for i in range(num):
            time.sleep(0.1)
            
            # 加速度计读取 - 添加安全处理
            a_x = accelerometer.get_x()
            a_y = accelerometer.get_y()
            a_z = accelerometer.get_z()
            
            # 加速度计安全处理
            if a_x is None:
                print("警告: 第%d次读取加速度计X值为None" % (i+1))
                a_x = 0
            if a_y is None:
                print("警告: 第%d次读取加速度计Y值为None" % (i+1))
                a_y = 0
            if a_z is None:
                print("警告: 第%d次读取加速度计Z值为None" % (i+1))
                a_z = 0
            
            # 确保是有效的数值
            try:
                a_x_sum += float(a_x)
                a_y_sum += float(a_y)
                a_z_sum += float(a_z)
            except:
                print("警告: 第%d次加速度计数值无效" % (i+1))
                continue
            
            # 陀螺仪读取 
            g_x = gyroscope.get_x()  
            g_y = gyroscope.get_y()
            g_z = gyroscope.get_z()
            
            # 陀螺仪安全处理
            if g_x is None:
                print("警告: 第%d次读取陀螺仪X值为None" % (i+1))
                g_x = 0
            if g_y is None:
                print("警告: 第%d次读取陀螺仪Y值为None" % (i+1))
                g_y = 0
            if g_z is None:
                print("警告: 第%d次读取陀螺仪Z值为None" % (i+1))
                g_z = 0
            
            # 确保是有效的数值
            try:
                g_x_sum += float(g_x)
                g_y_sum += float(g_y)
                g_z_sum += float(g_z)
            except:
                print("警告: 第%d次陀螺仪数值无效" % (i+1))
                continue
        
            print('第{}次获取误差值'.format(i+1))
    
    except OSError as e:
        print("传感器数值获取失败!", e)
        return
    except:
        print("读取传感器时发生未知错误")
        return

    # 计算平均值
    try:
        # 计算实际读取的平均值
        valid_count = num  # 假设所有采样都有效
        avg_ax_raw = a_x_sum / valid_count
        avg_ay_raw = a_y_sum / valid_count
        avg_az_raw = a_z_sum / valid_count
        
        # 计算偏移量：静止时X、Y轴应为0，Z轴应为1
        offset_ax = -avg_ax_raw
        offset_ay = -avg_ay_raw
        offset_az = 1.0 - avg_az_raw
        
        # 检查偏移量是否在有效范围内（±1g）
        print("原始平均值: X=%.3f, Y=%.3f, Z=%.3f" % (avg_ax_raw, avg_ay_raw, avg_az_raw))
        print("计算偏移: X=%.3f, Y=%.3f, Z=%.3f" % (offset_ax, offset_ay, offset_az))
        
        # 限制偏移量在有效范围内
        if offset_ax < -1.0:
            offset_ax = -1.0
        elif offset_ax > 1.0:
            offset_ax = 1.0
            
        if offset_ay < -1.0:
            offset_ay = -1.0
        elif offset_ay > 1.0:
            offset_ay = 1.0
            
        if offset_az < -1.0:
            offset_az = -1.0
        elif offset_az > 1.0:
            offset_az = 1.0
        
        if abs(offset_az) > 0.9:
            print("警告: Z轴偏移量较大 (%.3f)，可能传感器未水平放置" % offset_az)
        
        accelerometer.set_offset(offset_ax, offset_ay, offset_az)
        print('加速度校准完成')
        print('加速度偏移: X=%.3f, Y=%.3f, Z=%.3f' % (offset_ax, offset_ay, offset_az))
        
    except OSError as e:
        print("加速度计校准值保存失败:", e)
    except ZeroDivisionError:
        print("错误: num不能为0")
    except ValueError as e:
        print("加速度计偏移量超出范围:", e)
        print("请确保传感器水平放置且静止")
    except:
        print("加速度计校准过程中发生未知错误")

    try:
        avg_gx_raw = g_x_sum / num
        avg_gy_raw = g_y_sum / num
        avg_gz_raw = g_z_sum / num
        
        # 陀螺仪静止时应该为0
        offset_gx = -avg_gx_raw
        offset_gy = -avg_gy_raw
        offset_gz = -avg_gz_raw
        
        gyroscope.set_offset(offset_gx, offset_gy, offset_gz)
        print('陀螺仪校准完成')
        print('陀螺仪偏移: X=%.3f, Y=%.3f, Z=%.3f' % (offset_gx, offset_gy, offset_gz))
        
    except OSError as e:
        print("陀螺仪校准值保存失败:", e)
    except ZeroDivisionError:
        print("错误: num不能为0")
    except:
        print("陀螺仪校准失败")

def get_signal_strength():
    if wlan.isconnected():
        return wlan.status("rssi")
    return 0
    
    

tim1.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: Rgb_Neopixel())
tim2.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: Oled_Test())

btn_a = 0
btn_b = 0
touch_p = 0
touch_y = 0
touch_t = 0
touch_h = 0
touch_o = 0
touch_n = 0

def on_button_a_pressed(_):
    print("------ A键")
    music.pitch(400, 100)
    global btn_a
    btn_a = 1

# button B
def on_button_b_pressed(_):
    print("------ B键")
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

    
MAGNETIC_HAVE = 48 in i2c.scan()

while True:

    if btn_a and btn_b:
        time.sleep(0.5)
        for freq in range(0, 3, 1):
            music.pitch(400, 90)
            time.sleep(0.1)

        automatic_calibration()
        btn_a = 0
        btn_b = 0
        
        
    p0_value, p1_value, p2_value = P0.read_analog(), P1.read_analog(), P2.read_analog()
    light_value = light.read()
    sound_value = sound.read()
    acc_x, acc_y, acc_z = accelerometer.get_x(), accelerometer.get_y(), accelerometer.get_z()
    gyroscope_x, gyroscope_y, gyroscope_z = gyroscope.get_x(), gyroscope.get_y(), gyroscope.get_z()
    
    if MAGNETIC_HAVE:
        magnetic_x, magnetic_y, magnetic_z = magnetic.get_x(), magnetic.get_y(), magnetic.get_z()
    else:
        magnetic_x, magnetic_y, magnetic_z = 0, 0, 0
        
    if g_wifi_comm_state:
        g_wifi_comm_dBm = get_signal_strength()
        
    print("----------------------------")
    print('Touch_P:%d,Touch_Y:%d,Touch_T:%d,Touch_H:%d,Touch_O:%d,Touch_N:%d' % (touch_p, touch_y, touch_t, touch_h,touch_o, touch_n))  # 触摸
    print('P0:%d, P1:%d ,P2:%d' % (p0_value, p1_value, p2_value))
    print('light:%d' % light_value)  # 光线
    print('Sound:%d' % sound_value)  # 声音
    print('Accel_X:%.2f,Accel_Y:%.2f,Accel_Z:%.2f' % (acc_x, acc_y, acc_z))  # 加速度
    
    # 使用 format() 并提供默认值
    print('Gyroscope_X:{:.2f},Gyroscope_Y:{:.2f},Gyroscope_Z:{:.2f}'.format(
        gyroscope_x if gyroscope_x is not None else 0.0,
        gyroscope_y if gyroscope_y is not None else 0.0,
        gyroscope_z if gyroscope_z is not None else 0.0
    ))

    print('Wifi:%d,Name:%s,Pass:%s' % (g_wifi_comm_dBm, WIFI_SSID, WIFI_PASSWORD))  # WIFI
    print('Magnetic_X:%.2f,Magnetic_Y:%.2f,Magnetic_Z:%.2f' % (magnetic_x, magnetic_y, magnetic_z))  # 磁力计
    print('Mac:{}'.format(machine_id.upper()))  # MAC地址
    
        