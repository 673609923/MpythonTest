from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from serial import Serial
import time

class Repl():

    def __init__(self, serial):
        self.serial = serial

    def interrupt(self):
        for i in range(3):
            self.serial.write(b"\r\x03")
            print("中断: {}".format(i))
            if self.serial.waitForReadyRead(50):
                _buf = self.serial.readAll()
                if _buf.endsWith(b'>>> '):
                    break
            time.sleep(0.02)
        if self.serial.waitForReadyRead(100):
            _buf = self.serial.readAll()

    def write_cmdline(self, cmd):
        _buf =b''
        cmd += '\r\n'
        cmd_bytes = cmd.encode()
        self.serial.write(cmd_bytes)
        if self.serial.waitForReadyRead(1000):
            _buf = self.serial.readAll()
            while self.serial.waitForReadyRead(20):
                _buf += self.serial.readAll()
        # print(_buf)
        # list_=_buf.split(b"\r\n")
        # if len(list_)==2:
        #     return b''
        # elif len(list_)==3:
        #     return list_[-2]
        # else:
        #     return b''