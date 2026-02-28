from mpython import *
from machine import UART,unique_id
import _thread
from time import sleep_ms,time

#全局变量
my_clock = Clock(oled, 64, 32, 30)
oledLock = _thread.allocate_lock()
gLock = _thread.allocate_lock()
uart1 = UART(1, baudrate=115200, tx=Pin.P0, rx=Pin.P1)

print(str(unique_id()))

def RetCommand(command):
    pass

#读取MAC
def Read_PCB_MAC():
    from ubinascii import hexlify
    
    s = hexlify(unique_id()).decode().upper()
    result = []
    for i in range(0, len(s), 2):
        part = s[i:i+2]
        result.append(part)
    retStr = ' '.join(result)
    RetCommand("FF 5A 00 0C 00 08 01 01 05 00 " + retStr)
    
    del hexlify
    
#返回16进制指令
def RetCommand(command):
    hex_list = command.split()
    byte_list = []
    for hex_val in hex_list:
        byte_list.append(int(hex_val, 16))
    hex_bytes = bytes(byte_list)
    uart1.write(hex_bytes)


#十六进制转化十进制
def HexToDec(hex_num = "0"):
    return int(hex_num, 16)


#接收数据
def UARTDataThread():
    try:
        oled.fill(0)
        #oled.DispChar(str('启动成功！'), 0, 0, 1,True)
        
        while True:
            oled.fill(0)
            my_clock.settime()
            my_clock.drawClock()
            oled.show()
            if uart1.any():
                #获得互斥锁
                gLock.acquire()
                sleep_ms(50)
                received_bytes = uart1.readline()
                #释放互斥锁
                gLock.release()
                if received_bytes:
                    hex_data = ""
                    for b in received_bytes:
                        hex_byte = '%02X' % b
                        hex_data += hex_byte
                else:
                    print("未接收到任何数据")
                    break
                
                RecData = " ".join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])
                
                DataDeal(RecData)
    except Exception as e:
        oledLock.acquire()
        oled.fill(0)
        oled.DispChar(str('发生错误 请重启掌控版：{}'.format(e)), 0, 0, 1,True)
        oled.show()

#数据处理
def DataDeal(data):
    m_commandList = data.split()
    print("指令长度："+str(len(m_commandList)))
    if len(m_commandList) < 9:
        print("指令有误！")
        return
    if m_commandList[0] != "FF" and m_commandList[1] != "5A":
        print("指令有误！")
        return

    #SID到数据段的长度
    m_dataLen = HexToDec(str(m_commandList[2]) + str(m_commandList[3]))
    #指令模块ID(SID)    默认为08
    m_dataSID = str(m_commandList[4]) + str(m_commandList[5])
    #模块编号(subSID)   基本信息：01    功能管理：02    外设管理：03
    m_subSID = m_commandList[6]
    #子模块编号(ssubSID)
    m_ssubSID = m_commandList[7]
    #测试项编号
    m_testNum = m_commandList[8]
    if len(m_commandList) > 9:
        # 计算数据位有多少
        m_subDataLen = m_dataLen - 5
        # 获取列表的最后 num_elements_to_merge 个元素
        last_elements = m_commandList[-m_subDataLen:]
        # 将这些元素转换为字符串并连接
        m_dataSite = ' '.join(map(str, last_elements))
        print("数据位为："+m_dataSite)
    print(m_commandList)
    
    #基本信息：01    功能管理：02    外设管理：03
    if m_subSID == "01":
        if m_ssubSID == "01":                       #信息管理
            if m_testNum == "05":
                Read_PCB_MAC()
    elif m_subSID == "03":
        if m_ssubSID == "01":                           #通用外设控制
            if m_testNum == "22":                       #串口测试
                Read_PCB_MAC()

#线程一直捕获串口数据
UARTDataThread()