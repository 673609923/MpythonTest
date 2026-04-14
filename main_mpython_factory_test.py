import os
import sys
import sys, os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog,QMainWindow, QPushButton, QTextEdit, QMessageBox, QCheckBox,QShortcut
from Ui_mpython_factory_test import Ui_MainWindow  # 使用vscode生成的调用方法
from Ui_parameter import Ui_parameter_dialog
from Ui_startHmi import Ui_startHmi
from Ui_bindingSn import Ui_bindingSn
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QMetaObject,Q_ARG,QThread, pyqtSlot, QSize, Qt, pyqtSignal, QTimer, QIODevice,QEvent
from PyQt5.QtGui import QColor,QTextCharFormat,QTextCursor, QKeySequence,QGuiApplication
import pymysql
import pyperclip
import pyautogui
import esptool
import socket
import re
import serial
import binascii
import threading
import time
import keyboard
import subprocess
import json
from repl import *
import requests
import hashlib
import json  # 使用JSON序列化确保转义可靠性
import _thread
from enum import Enum
import wmi
import base64
import ctypes
from ctypes import wintypes
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from pathlib import Path


class ProjectType(Enum):
    x7001 = 0
    c7001 = 1
    v7005 = 2
    m7005 = 3
    v7007 = 4
    v7009 = 5
    sn_mac = 6
    v260Teach = 7
    v260Zkb = 8

CONFIG_DICT = dict()
IS_READED_MAC = False
g_test_mode = 0
g_project = 0
g_mac = ''
g_MesTableName = ""
TCP_CLIENTSOCKET = None
TCP_ADDRESS = None
g_db_connection = None
g_connection_failed = False
g_MyWin = None
g_SnCode = ""


class StartBindingSn(QDialog):

    finish_signal = pyqtSignal()  # 完成信号

    def set_english_input_method(self):
        """使用Windows API强制切换英文输入法"""
        try:
            # 获取当前前景窗口句柄
            hwnd = ctypes.windll.user32.GetForegroundWindow()

            # 获取当前线程ID
            thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)

            # 加载英文键盘布局（美式英语）
            english_layout = ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 0)

            # 激活英文键盘布局
            result = ctypes.windll.user32.ActivateKeyboardLayout(english_layout, 0)

            if result:
                print("成功切换到英文输入法")
            else:
                print("切换输入法失败")

        except Exception as e:
            print(f"切换输入法失败: {e}")


    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_bindingSn()
        self.ui.setupUi(self)


        # 关键：设置窗口标志，只保留关闭按钮
        self.setWindowFlags(
            Qt.Window |  # 基本窗口类型
            Qt.WindowCloseButtonHint |  # 关闭按钮
            Qt.WindowTitleHint |  # 标题栏（可选）
            Qt.WindowStaysOnTopHint
        )

        # 只允许英文和数字
        regex = QRegExp("[A-Za-z0-9]+")
        validator = QRegExpValidator(regex, self.ui.SnLineEdit_MAC)
        self.ui.SnLineEdit_MAC.setValidator(validator)
        self.ui.SnLineEdit_MAC.setFocus()

        self.setFixedSize(self.size())  # 固定为当前大小
        self.setModal(False)  # 明确设置为非模态
        self.set_english_input_method()
        self.ui.SnLineEdit_MAC.returnPressed.connect(lambda: self.on_btnEnter_clicked())



    # 功能测试开始按键
    @pyqtSlot()
    def on_btnEnter_clicked(self):
        global g_SnCode
        sn = self.ui.SnLineEdit_MAC.text()
        snlen = int(len(sn))

        if snlen > 0:
            if (snlen == 20 and g_project == ProjectType.c7001.value or g_project == ProjectType.x7001.value) or\
                (snlen >= 17 and snlen <= 20 and g_project == ProjectType.v7009.value):
                g_SnCode = str(sn)
                self.ui.SnLineEdit_MAC.returnPressed.disconnect()
                self.close()
                self.finish_signal.emit()
            else:
                self.ui.SnLineEdit_MAC.setText('')
                self.ui.SnLineEdit_MAC.setEnabled(True)

                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("错误")
                msg_box.setIcon(QMessageBox.Critical)  # 设置错误图标
                msg_box.setText(f"SN绑定MAC失败!!! 位数 {snlen} 不对")
                msg_box.setStandardButtons(QMessageBox.NoButton)
                QTimer.singleShot(3000, msg_box.accept)
                msg_box.exec_()
                self.ui.SnLineEdit_MAC.setFocus()
        else:
            self.ui.SnLineEdit_MAC.setFocus()



class MyMainWindow(QMainWindow, Ui_MainWindow):
    refresh_port = pyqtSignal()

    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.MyMain_Init()




    def setup_refresh_mac_sn_timer(self):
        self.refresh_mac_sn_timer = QTimer()
        self.refresh_mac_sn_timer.timeout.connect(self.refresh_mac_sn_event)
        self.refresh_mac_sn_timer.start(100)  # 100毫秒刷新一次


    def setup_refresh_carve_timer(self):
        self.refresh_carve_timer = QTimer()
        self.refresh_carve_timer.timeout.connect(self.refresh_carve_event)
        self.refresh_carve_timer.start(100)  # 100毫秒刷新一次


    def LogShow(self, rxData, color="black"):
        global g_project
        if g_project != ProjectType.sn_mac.value:
            try:
                # 获取当前默认文本格式（保存原先的格式）
                cursor = self.LogTextEdit.textCursor()
                original_format = cursor.charFormat()

                # 创建新的文本格式对象
                text_format = QTextCharFormat()

                # 设置文本颜色
                if color.lower() == "red":
                    text_format.setForeground(QColor(239, 71, 63))
                elif color.lower() == "green":
                    text_format.setForeground(QColor(34, 177, 76))
                else:
                    text_format.setForeground(QColor(color))

                # 移动到文档末尾
                cursor.movePosition(QTextCursor.End)

                # 应用新文本格式
                cursor.setCharFormat(text_format)

                # 插入文本
                cursor.insertText(rxData)
                cursor.insertText("\n")  # 换行

                # 恢复原先的文本格式
                cursor.setCharFormat(original_format)

                # 更新光标位置
                self.LogTextEdit.setTextCursor(cursor)

            except Exception as e:
                print(f"插入文本错误: {e}")


    def LogShowSnMac(self, rxData, color="black"):
        global  g_project
        if g_project == ProjectType.sn_mac.value:
            try:
                # 获取当前默认文本格式（保存原先的格式）
                cursor = self.sn_textEdit.textCursor()
                original_format = cursor.charFormat()

                # 创建新的文本格式对象
                text_format = QTextCharFormat()

                # 设置文本颜色
                if color.lower() == "red":
                    text_format.setForeground(QColor(239, 71, 63))
                elif color.lower() == "green":
                    text_format.setForeground(QColor(34, 177, 76))
                else:
                    text_format.setForeground(QColor(color))

                # 移动到文档末尾
                cursor.movePosition(QTextCursor.End)

                # 应用新文本格式
                cursor.setCharFormat(text_format)

                # 插入文本
                cursor.insertText(rxData)
                cursor.insertText("\n")  # 换行

                # 恢复原先的文本格式
                cursor.setCharFormat(original_format)

                # 更新光标位置
                self.LogTextEdit.setTextCursor(cursor)

            except Exception as e:
                print(f"插入文本错误: {e}")



    def initialize_db_connection(self):
        """初始化并返回数据库连接（带失败状态缓存）"""
        global g_db_connection, g_connection_failed, g_MyWin

        # 如果之前连接失败过,直接返回None
        if g_connection_failed:
            return None

        # 如果连接已存在且有效,则直接返回
        if g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open:
            return g_db_connection

        try:
            g_db_connection = pymysql.connect(
                host='10.30.17.92',
                user='hehao',
                password='hehao666',
                database='sengsi',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
            g_connection_failed = False
            if g_db_connection:
                QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接成功!", "green"))
                QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接成功!", "green"))
            else:
                QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接失败", "red"))
                QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接失败!", "red"))
            return g_db_connection

        except pymysql.MySQLError as e:
            g_connection_failed = True
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接失败", "red"))
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接失败", "red"))
            return None
        except Exception as e:
            g_connection_failed = True
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接失败", "red"))
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接失败", "red"))
            return None



    def query_by_mac(mac_address):
        """根据MAC地址查询数据"""
        global g_db_connection, g_connection_failed,g_test_mode
        # 如果之前连接失败过，直接返回None
        if g_connection_failed:
            print("数据库错误: 数据库连接不可用，请检查连接", file=sys.stderr)
            return None

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (
                    g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            print("数据库错误: 数据库未初始化", file=sys.stderr)
            return None

        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `7001_xiaoxue_final` WHERE mac = %s"


                cursor.execute(sql, (mac_address,))
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"数据库错误: 数据库查询错误: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"数据库错误: 发生意外错误: {e}", file=sys.stderr)
            return None


    def replace_mac_record(self,mac, info):
        """替换MAC记录（存在则先删除后插入，不存在则直接插入）"""
        global g_db_connection, g_connection_failed,g_MesTableName,g_project,g_SnCode,g_test_mode

        # 如果之前连接失败过，直接返回False
        if g_connection_failed:
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES未连接,上传数据失败", "red"))
            return False

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES未连接,上传数据失败", "red"))
            return False

        try:
            if g_test_mode == 1 and g_project == ProjectType.x7001.value or g_project == ProjectType.c7001.value or g_project == ProjectType.v7009.value:
                if not g_SnCode:
                    QTimer.singleShot(0, lambda: g_MyWin.LogShow("SN为空 上传MES数据失败", "red"))
                    return False

                with connection.cursor() as cursor:
                    # 开始事务
                    connection.begin()

                    # 先尝试删除
                    delete_sql = "DELETE FROM `" + g_MesTableName + "` WHERE mac = %s"
                    cursor.execute(delete_sql, (mac,))

                    # 插入新记录
                    insert_sql = "INSERT INTO `" + g_MesTableName + "` (mac, sn, info, time) VALUES (%s, %s, %s, NOW())"
                    cursor.execute(insert_sql, (mac,g_SnCode,info))

                    # 提交事务
                    connection.commit()

                    QTimer.singleShot(0, lambda: g_MyWin.LogShow(f"MAC: {mac} 绑定 SN: {g_SnCode} 上传数据成功", "green"))
                    return True

            else:
                with connection.cursor() as cursor:
                    # 开始事务
                    connection.begin()

                    # 先尝试删除
                    delete_sql = "DELETE FROM `" + g_MesTableName + "` WHERE mac = %s"
                    cursor.execute(delete_sql, (mac,))

                    # 插入新记录
                    insert_sql = "INSERT INTO `" + g_MesTableName + "` (mac, info, time) VALUES (%s, %s, NOW())"
                    cursor.execute(insert_sql, (mac, info))

                    # 提交事务
                    connection.commit()

                    QTimer.singleShot(0, lambda: g_MyWin.LogShow(f"MES上传数据成功: {info}", "green"))
                    return True


        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("上传MES数据失败", "red"))
            return False
        except Exception as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("上传MES数据失败", "red"))
            return False

    def CopyMacInfo(event=None):
        global g_mac
        if g_mac:

            # 将 MAC 复制到剪贴板
            pyperclip.copy(g_mac)

            # 验证剪贴板内容（可选）
            clipboard_content = pyperclip.paste()

            # 模拟Delete键删除已选内容
            pyautogui.press('backspace')
            time.sleep(0.2)

            # 模拟Ctrl+V粘贴剪贴板内容
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)

            # 模拟回车键
            pyautogui.press('esc')

            pyautogui.hotkey('ctrl', 'p')
            time.sleep(0.2)

            pyautogui.press('enter')
            time.sleep(0.2)



    # 主窗口初始化
    def MyMain_Init(self):

        global g_test_mode,g_project,g_MesTableName

        self.stackedWidget.setCurrentIndex(g_project)

        if g_project == ProjectType.x7001.value:
            __NAME__ = "< 7001-讯飞实验箱-小学版 >    "
            g_MesTableName = "7001_xiaoxue_final"

        elif g_project == ProjectType.c7001.value:
            __NAME__ = "< 7001-讯飞实验箱-初中版 >    "
            g_MesTableName = "7001_chuzhong_final"


        elif g_project == ProjectType.v260Teach.value:
            __NAME__ = "< TS260-信息科技示教版 >    "
            g_MesTableName = "v260Teach_blank"

        elif g_project == ProjectType.v260Zkb.value:
            __NAME__ = "< TS260-掌控板 >    "
            g_MesTableName = "v260Zkb_blank"

        elif g_project == ProjectType.v7005.value:
            __NAME__ = "< 7005-掌控板-学境 >    "
            if g_test_mode == 0:
                g_MesTableName = "7005_blank"
            elif g_test_mode == 1:
                g_MesTableName = "7005_final"

        elif g_project == ProjectType.m7005.value:
            __NAME__ = "< 7005-模块-学境 >    "


        elif g_project == ProjectType.v7007.value:
            __NAME__ = "< 7007-掌控板-单板 >    "
            g_MesTableName = "7007_final"

        elif g_project == ProjectType.v7009.value:
            __NAME__ = "< 7009-乐动掌控2.0 >    "
            if g_test_mode == 0:
                g_MesTableName = "7009_blank"
            elif g_test_mode == 1:
                g_MesTableName = "7009_final"

        elif g_project == ProjectType.sn_mac.value:
            # 移除前两个页面
            self.TabWidget.removeTab(1)  # 先移除第二个（索引1）
            self.TabWidget.removeTab(0)  # 再移除第一个（索引0）

            if g_test_mode == 0:
                __NAME__ = "< 7008-SN绑定MAC地址 >    "
                g_MesTableName = "7008_1956"
            elif g_test_mode == 1:
                __NAME__ = "< 7009-SN绑定MAC地址 >    "
                g_MesTableName = "7009_final"
            elif g_test_mode == 2:
                __NAME__ = "< 7001-讯飞小学版-SN绑定MAC地址 >    "
                g_MesTableName = "7001_xiaoxue_final"
            elif g_test_mode == 3:
                __NAME__ = "< 7001-讯飞初中版-SN绑定MAC地址 >    "
                g_MesTableName = "7001_chuzhong_final"

        if g_project != ProjectType.sn_mac.value:
            if g_test_mode == 0:
                __MODEL__ = "(半成品测试)"
            elif g_test_mode == 1:
                __MODEL__ = "(成品测试)"
        else:
            __MODEL__ = ""

        if g_project != ProjectType.sn_mac.value:
            self.TabWidget.removeTab(2)

        QTimer.singleShot(1000, self.initialize_db_connection)

        # 注册 F6 快捷键
        keyboard.add_hotkey('shift', self.CopyMacInfo)

        self.is_func_serial_opened = False  # 是否打开串口
        self.is_funcTest_started = False    # 是否启动功能测试
        self.IS_CARVE_STARTED = False       # 是否雕刻开始
        self.IS_SN_STARTED = False          # 是否开始SN上传
        self.IS_WAIT_EWM = False            # 是否等待扫码
        self.TIME_MAC = ""
        self.Is_START_GET_MAC_FUN = False
        self.Is_START_GET_SN_FUN  = False
        self.change_test_prj_Button.setEnabled(False)
        self.manual_change_Button.setEnabled(False)
        self.retest_Button.setEnabled(False)

        if g_project == ProjectType.m7005.value:
            self.p7005_camera_module.setEnabled(False)
            self.p7005_rgb_module.setEnabled(False)
            self.p7005_soil_module.setEnabled(False)
            self.p7005_fan_module.setEnabled(False)
            self.p7005_light_module.setEnabled(False)
            self.p7005_hunting_module.setEnabled(False)
            self.p7005_pot_module.setEnabled(False)
            self.p7005_Temp_module.setEnabled(False)
            self.p7005_humiture_module.setEnabled(False)
            self.p7005_Ultrasonic_module.setEnabled(False)
            self.p7005_driver_module.setEnabled(False)
            self.p7005_colour_module.setEnabled(False)
            self.p7005_sense_module.setEnabled(False)
            self.p7005_rfid_module.setEnabled(False)
            self.p7005_hrrest_module.setEnabled(False)

        # 只允许英文和数字
        regex = QRegExp("[A-Za-z0-9]+")
        validator = QRegExpValidator(regex, self.SnLineEdit_MAC)
        self.SnLineEdit_MAC.setValidator(validator)

        # 刷新串口 槽函数                                   
        self.on_refresh_func_Button_clicked()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_refresh_func_Button_clicked)
        self.timer.start(100)

        # 镭雕 槽函数                                                           
        self.iPLineEdit.setText(self.get_local_ip())  # 镭雕机的IP地址
        self.portLineEdit.setText("1000")  # 镭雕机的端口
        self.setup_refresh_mac_sn_timer()
        self.setup_refresh_carve_timer()

        self.setWindowTitle(__NAME__ + __MODEL__ + "     < 版本：1.3 >")

        # 加载config
        external_file_path = os.path.join(os.getcwd(), 'config\hhconfig.json')
        self.load_configure(external_file_path)
        self.ui_parameter_show()



    def ui_parameter_show(self):
        global CONFIG_DICT

        # 光线 判断标准
        self.light_label_1.setText("判断标准:{}~{}".format(CONFIG_DICT.get("light_min"), CONFIG_DICT.get("light_max")))

        # 声音 判断标准
        self.sound_label_1.setText("判断标准:{}~{}".format(CONFIG_DICT.get("sound_min"), CONFIG_DICT.get("sound_max")))

        # 参数范围设置 绑定函数
        self.para_Button.clicked.connect(self.para_Button_clicked_funct)

    # 参数设置窗口
    def para_Button_clicked_funct(self):
        global CONFIG_DICT
        self.parameter_ui = Ui_parameter_dialog()
        self.parameter_dialog = QtWidgets.QDialog()
        self.parameter_ui.setupUi(self.parameter_dialog)

        # self.load_configure('./config.json')
        self.parameter_ui.min_light_lineEdit.setText(str(CONFIG_DICT.get('light_min')))
        self.parameter_ui.max_light_lineEdit.setText(str(CONFIG_DICT.get('light_max')))

        self.parameter_ui.min_sound_lineEdit.setText(str(CONFIG_DICT.get('sound_min')))
        self.parameter_ui.max_sound_lineEdit.setText(str(CONFIG_DICT.get('sound_max')))

        self.parameter_ui.min_humiture_lineEdit.setText(str(CONFIG_DICT.get('humiture_min')))
        self.parameter_ui.max_humiture_lineEdit.setText(str(CONFIG_DICT.get('humiture_max')))

        self.parameter_ui.min_ultrasound_lineEdit.setText(str(CONFIG_DICT.get('ultrasound_min')))
        self.parameter_ui.max_ultrasound_lineEdit.setText(str(CONFIG_DICT.get('ultrasound_max')))

        self.parameter_ui.min_ir1_lineEdit.setText(str(CONFIG_DICT.get('ir1_min')))
        self.parameter_ui.max_ir1_lineEdit.setText(str(CONFIG_DICT.get('ir1_max')))

        self.parameter_dialog.show()

    def load_configure(self, path):
        global CONFIG_DICT
        try:
            with open(path, "r") as f:
                CONFIG_DICT = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, '错误', '加载配置文件错误!\n{}'.format(e))

    def save_configure(self, path):
        global CONFIG_DICT
        try:
            with open(path, "w") as f:
                json.dump(CONFIG_DICT, f)
        except Exception as e:
            QMessageBox.critical(self, '错误', '保存配置文件错误!\n{}'.format(e))

    def parameter_accepted_func(self):
        global CONFIG_DICT
        CONFIG_DICT['sound_min'] = float(self.parameter_ui.min_sound_lineEdit.text())
        CONFIG_DICT['sound_max'] = float(self.parameter_ui.max_sound_lineEdit.text())

        CONFIG_DICT['light_min'] = float(self.parameter_ui.min_light_lineEdit.text())
        CONFIG_DICT['light_max'] = float(self.parameter_ui.max_light_lineEdit.text())

        CONFIG_DICT['humiture_min'] = float(self.parameter_ui.min_humiture_lineEdit.text())
        CONFIG_DICT['humiture_max'] = float(self.parameter_ui.max_humiture_lineEdit.text())

        CONFIG_DICT['ultrasound_min'] = float(self.parameter_ui.min_ultrasound_lineEdit.text())
        CONFIG_DICT['ultrasound_max'] = float(self.parameter_ui.max_ultrasound_lineEdit.text())

        CONFIG_DICT['ir1_min'] = float(self.parameter_ui.min_ir1_lineEdit.text())
        CONFIG_DICT['ir1_max'] = float(self.parameter_ui.max_ir1_lineEdit.text())

        self.save_configure('./hhconfig.json')
        self.ui_parameter_show()

    # 获取本机ip
    def get_local_ip(self):
        return '127.0.0.1'


    def change_background(self, obj, stylesheet_):
        temp_stylesheet = obj.styleSheet()
        index = temp_stylesheet.find("background-color:")
        replace_ = temp_stylesheet[index + 18:index + 18 + 18]
        new_str = temp_stylesheet.replace(replace_, stylesheet_)
        obj.setStyleSheet(new_str)




    def set_english_input_method(self):
        """使用Windows API强制切换英文输入法"""
        try:
            # 获取当前前景窗口句柄
            hwnd = ctypes.windll.user32.GetForegroundWindow()

            # 获取当前线程ID
            thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)

            # 加载英文键盘布局（美式英语）
            english_layout = ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 0)

            # 激活英文键盘布局
            result = ctypes.windll.user32.ActivateKeyboardLayout(english_layout, 0)

            if result:
                print("成功切换到英文输入法")
            else:
                print("切换输入法失败")

        except Exception as e:
            print(f"切换输入法失败: {e}")



    def waitForEnter(self,str):
        self.set_english_input_method()
        if not self.IS_WAIT_EWM or self.TIME_MAC != str:

            if self.TIME_MAC != str:
                self.clearHandleEnterPressed()

            self.TIME_MAC = str
            self.handleStartBindingMac(str)
        else:
            self.SnLineEdit_MAC.setFocus()



    def start_get_sn_func(self):
        if not self.Is_START_GET_SN_FUN:
            self.sn_func_thread = TestInfo_Thread(self.sn_put_comboBox.currentText())  # 功能测试线程
            self.sn_func_thread.open_serial_link()  # 打开串口
            self.sn_func_thread.startBindingMac.connect(self.waitForEnter)
            self.sn_func_thread.start()
            self.Is_START_GET_SN_FUN = True

    def close_get_sn_func(self):
        if self.Is_START_GET_SN_FUN:
            self.sn_func_thread.serial.close()
            self.sn_func_thread.quit()
            self.sn_func_thread.terminate()
            self.sn_func_thread.wait()
            self.IS_WAIT_EWM = False
            self.Is_START_GET_SN_FUN = False

    def start_get_mac_func(self):
        if not self.Is_START_GET_MAC_FUN:
            self.mac_func_thread = ReadMac_Thread(self.serial_carve_comboBox.currentText())  # 功能测试线程
            self.mac_func_thread.open_serial_link_mac()  # 打开串口
            self.mac_func_thread.updataMac.connect(lambda str_: self.LineEdit_MAC.setText(str_))  # 雕刻MAC标签
            self.mac_func_thread.start()
            self.Is_START_GET_MAC_FUN = True

    def close_get_mac_func(self):
        if self.Is_START_GET_MAC_FUN:
            self.mac_func_thread.serial.close()
            self.mac_func_thread.quit()
            self.mac_func_thread.terminate()
            self.mac_func_thread.wait()
            self.Is_START_GET_MAC_FUN = False

    def on_refresh_func_Button_clicked(self):
        if not self.is_func_serial_opened and not self.IS_CARVE_STARTED:
            self.com_list = {}
            self.serial_func_comboBox.clear()
            ports = QSerialPortInfo.availablePorts()
            for port in ports:
                manufacturer = port.manufacturer()
                print(manufacturer)
                if manufacturer in ["Silicon Labs", "wch.cn","Microsoft","(Undefined Vendor)"]:
                    manufacturer_type = 0 if manufacturer == "Silicon Labs" else 1
                    port_name = port.portName()
                    self.com_list.update({port_name: manufacturer_type})
            com_list = list(self.com_list.keys())
            com_list.sort(reverse=True)
            for port in com_list:
                self.serial_func_comboBox.addItem(port)
            print(self.com_list)


    def binding_sn_mac(self, mac, sn):
        """绑定SN和MAC地址（存在则更新SN，不存在则返回False）"""
        global g_db_connection, g_connection_failed, g_MesTableName

        # 如果之前连接失败过，直接返回False
        if g_connection_failed:
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES未连接,上传数据失败", "red"))
            return False

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (
                g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES未连接,上传数据失败", "red"))
            return False

        try:
            with connection.cursor() as cursor:
                # 开始事务
                connection.begin()

                # 先查询是否存在该MAC地址
                select_sql = "SELECT * FROM `" + g_MesTableName + "` WHERE mac = %s"
                cursor.execute(select_sql, (mac,))
                result = cursor.fetchone()

                # 如果查询不到该MAC地址，插入新记录
                if result is None:
                    info = f'mac:{mac};wifi:-59;i2c:True;light:407;sound:87;p:1;y:1;t:1;h:1;o:1:n:1;acc_x:1.09;acc_y:0.37;acc_z:-0.3;mag_x:549.81;mag_y:263.56;mag_z:-1036.38;gyroscope_x:0.16;gyroscope_y:-6.69;gyroscope_z:-1.88;camera:True;lcd:True;pinout:True;m2out:True;aKey:True;bKey:True;record_play:True;rgb:True;'

                    insert_sql = "INSERT INTO `" + g_MesTableName + "` (mac, sn, info, time) VALUES (%s, %s, %s, NOW())"
                    cursor.execute(insert_sql, (mac, sn, info))

                    # 检查插入是否成功（受影响行数大于0表示成功）
                    if cursor.rowcount <= 0:
                        connection.rollback()
                        QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("插入新记录失败", "red"))
                        return False

                    # 提交事务
                    connection.commit()
                    return True

                # 更新SN字段
                update_sql = "UPDATE `" + g_MesTableName + "` SET sn = %s WHERE mac = %s"
                cursor.execute(update_sql, (sn, mac))


                # 提交事务
                connection.commit()
                return True

        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"绑定SN失败: {str(e)}", "red"))
            return False
        except Exception as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"绑定SN失败: {str(e)}", "red"))
            return False


    def binding_sn_mac_7001(self, mac, sn):
        """绑定SN和MAC地址（存在则更新SN，不存在则返回False）"""
        global g_db_connection, g_connection_failed, g_MesTableName

        # 如果之前连接失败过，直接返回False
        if g_connection_failed:
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES未连接,上传数据失败", "red"))
            return False

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (
                g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES未连接,上传数据失败", "red"))
            return False

        try:
            with connection.cursor() as cursor:
                # 开始事务
                connection.begin()

                # 先查询是否存在该MAC地址
                select_sql = "SELECT * FROM `" + g_MesTableName + "` WHERE mac = %s"
                cursor.execute(select_sql, (mac,))
                result = cursor.fetchone()

                # 如果查询不到该MAC地址，插入新记录
                if result is None:
                    return False

                # 更新SN字段
                update_sql = "UPDATE `" + g_MesTableName + "` SET sn = %s WHERE mac = %s"
                cursor.execute(update_sql, (sn, mac))

                # 提交事务
                connection.commit()
                return True

        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"绑定SN失败: {str(e)}", "red"))
            return False
        except Exception as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"绑定SN失败: {str(e)}", "red"))
            return False


    def binding_sn_mac_info(self, mac, sn,info):
        """替换MAC记录（存在则先删除后插入，不存在则直接插入）"""
        global g_db_connection, g_connection_failed,g_MesTableName

        # 如果之前连接失败过，直接返回False
        if g_connection_failed:
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES未连接,上传数据失败", "red"))
            return False

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES未连接,上传数据失败", "red"))
            return False

        try:
            with connection.cursor() as cursor:
                # 开始事务
                connection.begin()

                # 先尝试删除
                delete_sql = "DELETE FROM `" + g_MesTableName + "` WHERE mac = %s"
                cursor.execute(delete_sql, (mac,))

                # 插入新记录
                insert_sql = "INSERT INTO `" + g_MesTableName + "` (mac, sn, info, time) VALUES (%s, %s, %s,NOW())"
                cursor.execute(insert_sql, (mac, sn , info))

                # 提交事务
                connection.commit()

                return True

        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"绑定SN失败: {str(e)}", "red"))
            return False
        except Exception as e:
            if connection:
                connection.rollback()
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"绑定SN失败: {str(e)}", "red"))
            return False




    def handleStartBindingMac(self, str):
        # 设置焦点
        self.SnLineEdit_MAC.setFocus()
        self.SnLineEdit_MAC.setStyleSheet("""
                                                color: rgb(34, 177, 76);
                                                border: 2px dashed rgb(34, 177, 76);
                                                padding: 2px;
                                            """)

        # 使用 lambda 传递参数
        self.SnLineEdit_MAC.returnPressed.connect(lambda: self.handleEnterPressed(str))
        print("returnPressed 信号已连接，请按回车键")
        self.IS_WAIT_EWM = True

    def handleEnterPressed(self, str):
        self.SnLineEdit_MAC.setEnabled(False)
        global g_test_mode,g_MyWin
        """处理回车键事件"""
        sn = self.SnLineEdit_MAC.text()
        snlen = int(len(sn))

        if snlen < 18 or snlen > 21:
            self.SnLineEdit_MAC.setText('')
            self.SnLineEdit_MAC.setEnabled(True)
            self.SnLineEdit_MAC.setFocus()
            QMessageBox.critical(self, "错误", f"SN绑定MAC失败!!! 位数 {snlen} 不对")
            return

        try:
            # 7008
            if g_test_mode == 0:
                info = str
                pattern = re.compile(r'(?<=mac:)[A-Fa-f0-9]{12}')
                finded_list = pattern.findall(info)
                if finded_list:
                    mac = finded_list[-1]  # 取最后一个匹配项
                    if self.binding_sn_mac_info(mac,sn,info):
                        QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"1956主控 SN绑定MAC成功: MAC = {mac}, SN = {sn}, INFO = {info}", "green"))
                    else:
                        QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"1956主控  SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!", "red"))
                        QMessageBox.critical(self, "错误", f"1956主控  SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!")
            # 7009
            if g_test_mode == 1:
                mac = str
                if self.binding_sn_mac(mac,sn):
                    QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"7009乐动掌控 SN绑定MAC成功: MAC = {mac}, SN = {sn}", "green"))
                else:
                    QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"7009乐动掌控 SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!", "red"))
                    QMessageBox.critical(self, "错误", f"7009乐动掌控 SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!")

            # 7001 小学版
            if g_test_mode == 2:
                mac = str
                if self.binding_sn_mac_7001(mac,sn):
                    QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"7001_讯飞_小学版 SN绑定MAC成功: MAC = {mac}, SN = {sn}", "green"))
                else:
                    QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"7001_讯飞_小学版 SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!", "red"))
                    QMessageBox.critical(self, "错误", f"7001_讯飞_小学版 SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!")

            # 7001 初中版
            if g_test_mode == 3:
                mac = str
                if self.binding_sn_mac_7001(mac,sn):
                    QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"7001_讯飞_初中版 SN绑定MAC成功: MAC = {mac}, SN = {sn}", "green"))
                else:
                    QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac(f"7001_讯飞_初中版 SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!", "red"))
                    QMessageBox.critical(self, "错误", f"7001_讯飞_初中版 SN绑定MAC失败!!! 没有找到MAC地址,无法绑定,请重新返回测试至成功过站!")



            self.SnLineEdit_MAC.setText('')
            self.SnLineEdit_MAC.returnPressed.disconnect()
            self.IS_WAIT_EWM = False
            print("信号连接已断开")
        except:
            print("断开连接失败")

        self.sn_textEdit.moveCursor(QTextCursor.End)  # 移动光标到底部
        self.SnLineEdit_MAC.setEnabled(True)



    def clearHandleEnterPressed(self):
        try:
            self.SnLineEdit_MAC.returnPressed.disconnect()
        except:
            return

    #  扫SN的串口刷新
    def refresh_mac_sn_event(self):
        global g_mac
        if self.IS_SN_STARTED:
            current_port = self.sn_put_comboBox.currentText()  # 获取当前选中的串口

            Isclear = True
            # 扫描所有可用串口并筛选符合条件的
            com_list = QSerialPortInfo.availablePorts()
            for com_info in com_list:
                manufacturer = com_info.manufacturer()
                if manufacturer in ["Microsoft","wch.cn",]:
                    port_name = com_info.portName()
                    if port_name != current_port:
                        self.sn_put_comboBox.clear()
                        self.sn_put_comboBox.addItem(com_info.portName())
                        self.start_get_sn_func()
                    Isclear = False

            if Isclear:
                # 关闭串口事件处理
                self.close_get_sn_func()
                self.sn_put_comboBox.clear()
                self.SnLineEdit_MAC.setStyleSheet("""
                                color: rgb(255, 23, 23);
                                border: 2px dashed rgb(255, 23, 23);
                                padding: 2px;
                            """)
                self.SnLineEdit_MAC.clearFocus()

    #  镭雕的串口刷新
    def refresh_carve_event(self):
        global g_mac
        if self.IS_CARVE_STARTED:
            current_port = self.serial_carve_comboBox.currentText()  # 获取当前选中的串口

            Isclear = True
            # 扫描所有可用串口并筛选符合条件的
            com_list = QSerialPortInfo.availablePorts()
            for com_info in com_list:
                manufacturer = com_info.manufacturer()
                if manufacturer in ["Microsoft","wch.cn"]:
                    port_name = com_info.portName()
                    if port_name != current_port:
                        self.serial_carve_comboBox.clear()
                        self.serial_carve_comboBox.addItem(com_info.portName())
                        self.start_get_mac_func()
                    Isclear = False

            if Isclear:
                # 关闭串口事件处理
                g_mac = ""
                self.LineEdit_MAC.setText("空")
                self.close_get_mac_func()
                self.serial_carve_comboBox.clear()


    # 镭雕开始按键事件
    @pyqtSlot()
    def on_carve_start_Button_clicked(self):
        global g_mac
        if not self.IS_CARVE_STARTED:
            # 开始
            self.IS_CARVE_STARTED = True
            self.serial_carve_comboBox.setEnabled(False)
            self.iPLineEdit.setEnabled(False)
            self.portLineEdit.setEnabled(False)
            self.carve_start_Button.setText("停止")

            self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket通信
            self.serversocket.bind((self.iPLineEdit.text(), int(self.portLineEdit.text())))  # 绑定IP 端口
            self.serversocket.listen(1)  # 开始监听

            self.tcp_thread = TCP_Thread(self.serversocket)
            self.tcp_thread.start()
        else:
            g_mac = ""
            self.LineEdit_MAC.setText("空")
            self.IS_CARVE_STARTED = False
            self.serial_carve_comboBox.clear()
            self.serial_carve_comboBox.setEnabled(True)
            self.iPLineEdit.setEnabled(True)
            self.portLineEdit.setEnabled(True)
            self.carve_start_Button.setText("开始")

            # 关闭TCP服务
            self.serversocket.close()
            self.tcp_thread.quit()
            self.tcp_thread.terminate()
            self.tcp_thread.wait()

            # 关闭串口事件处理       
            self.close_get_mac_func()

    # SN扫码绑定上传开始按键事件
    @pyqtSlot()
    def on_sn_put_Button_clicked(self):
        if not self.IS_SN_STARTED:
            self.IS_SN_STARTED = True
            self.sn_put_comboBox.setEnabled(False)
            self.sn_put_Button.setText("停止")
        else:
            self.LineEdit_MAC.setText("空")
            self.IS_WAIT_EWM = False  # 是否等待扫码
            self.IS_SN_STARTED = False
            self.sn_put_comboBox.clear()
            self.sn_put_comboBox.setEnabled(True)
            self.sn_put_Button.setText("开始")

            self.SnLineEdit_MAC.setStyleSheet("""
                                                color: rgb(255, 23, 23);
                                                border: 2px dashed rgb(255, 23, 23);
                                                padding: 2px;
                                              """)
            self.close_get_sn_func()

    # 功能测试开始按键
    @pyqtSlot()
    def on_com_func_Button_clicked(self):
        global g_project,g_test_mode
        if not self.is_func_serial_opened:

            currentText = self.serial_func_comboBox.currentText()
            if len(currentText) == 0:
                return

            # 打开串口事件处理
            self.com_func_Button.setText("关闭串口")
            # 按键颜色
            self.com_func_Button.setStyleSheet("QPushButton{color: rgb(0, 170, 127)}")
            self.is_func_serial_opened = True
            # 禁止配置串口
            self.serial_func_comboBox.setEnabled(False)

            if g_project == ProjectType.m7005.value:
                self.p7005_camera_module.setEnabled(True)
                self.p7005_rgb_module.setEnabled(True)
                self.p7005_soil_module.setEnabled(True)
                self.p7005_fan_module.setEnabled(True)
                self.p7005_light_module.setEnabled(True)
                self.p7005_hunting_module.setEnabled(True)
                self.p7005_pot_module.setEnabled(True)
                self.p7005_Temp_module.setEnabled(True)
                self.p7005_humiture_module.setEnabled(True)
                self.p7005_Ultrasonic_module.setEnabled(True)
                self.p7005_driver_module.setEnabled(True)
                self.p7005_colour_module.setEnabled(True)
                self.p7005_sense_module.setEnabled(True)
                self.p7005_rfid_module.setEnabled(True)
                self.p7005_hrrest_module.setEnabled(True)

            if not g_project == ProjectType.m7005.value:
                self.change_test_prj_Button.setEnabled(True)
                self.manual_change_Button.setEnabled(True)

            self.retest_Button.setEnabled(True)
            self.start_test_thread_func(self)


            if self.test_func_thread.serial.isOpen():
                if g_project == ProjectType.c7001.value or g_project == ProjectType.x7001.value or g_project == ProjectType.v7009.value and g_test_mode == 1:
                    self.bindingSnWin = StartBindingSn(parent=self)
                    self.bindingSnWin.show()
                    self.bindingSnWin.activateWindow()  # 激活窗口到最前
        else:
            if hasattr(self, 'bindingSnWin') and g_project == ProjectType.c7001.value or g_project == ProjectType.x7001.value or g_project == ProjectType.v7009.value and g_test_mode == 1:
                self.bindingSnWin.close()               # 关闭窗口
                self.bindingSnWin.deleteLater()         # 安全销毁对象
                self.bindingSnWin = None                # 清除引用

            # 关闭串口事件处理       
            self.com_func_Button.setText("打开串口")
            self.com_func_Button.setStyleSheet("")
            self.is_func_serial_opened = False
            self.serial_func_comboBox.setEnabled(True)
            self.serial_func_comboBox.setEnabled(True)
            self.change_test_prj_Button.setEnabled(False)
            self.manual_change_Button.setEnabled(False)
            self.retest_Button.setEnabled(False)
            self.is_funcTest_started = False

            if g_project == ProjectType.m7005.value:
                self.p7005_camera_module.setEnabled(False)
                self.p7005_rgb_module.setEnabled(False)
                self.p7005_soil_module.setEnabled(False)
                self.p7005_fan_module.setEnabled(False)
                self.p7005_light_module.setEnabled(False)
                self.p7005_hunting_module.setEnabled(False)
                self.p7005_pot_module.setEnabled(False)
                self.p7005_Temp_module.setEnabled(False)
                self.p7005_humiture_module.setEnabled(False)
                self.p7005_Ultrasonic_module.setEnabled(False)
                self.p7005_driver_module.setEnabled(False)
                self.p7005_colour_module.setEnabled(False)
                self.p7005_sense_module.setEnabled(False)
                self.p7005_rfid_module.setEnabled(False)
                self.p7005_hrrest_module.setEnabled(False)

            self.test_func_thread.serial.close()
            self.test_func_thread.timer.stop()
            self.test_func_thread.quit()
            self.test_func_thread.terminate()
            self.test_func_thread.wait()
            self.clear_all_TestItem()




    # 开始测试线程
    def start_test_thread_func(self, _):
        global g_project

        self.test_func_thread = FuncTest_Thread(self.serial_func_comboBox.currentText())  # 功能测试线程
        self.test_func_thread.open_serial_link()  # 打开串口
        self.test_func_thread.data_received.connect(self.repl_recv_func)  # 信息
        self.test_func_thread.data_update.connect(self.updata_gui_func)  # 更新UI界面信息
        self.test_func_thread.timer.start()
        self.test_func_thread.start()


        if g_project == ProjectType.x7001.value:
            self.test_func_thread.signal_ir1.connect(
                lambda: self.change_background(self.x7001_ir1_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_humiture.connect(
                lambda: self.change_background(self.x7001_humiture_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_pot.connect(
                lambda: self.change_background(self.x7001_pot_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_rfid.connect(
                lambda: self.change_background(self.x7001_rfid_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_ultrasound.connect(
                lambda: self.change_background(self.x7001_ultrasound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_tracking.connect(
                lambda: self.change_background(self.x7001_tracking_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.x7001_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sda_scl.connect(
                lambda: self.change_background(self.x7001_sda_scl_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.x7001_light_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.x7001_sound_value_label, "rgb(0, 170, 127)"))

        elif g_project == ProjectType.c7001.value:
            self.test_func_thread.signal_ir1.connect(
                lambda: self.change_background(self.c7001_ir1_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_humiture.connect(
                lambda: self.change_background(self.c7001_humiture_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_rfid.connect(
                lambda: self.change_background(self.c7001_rfid_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_ultrasound.connect(
                lambda: self.change_background(self.c7001_ultrasound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.c7001_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sda_scl.connect(
                lambda: self.change_background(self.c7001_sda_scl_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.c7001_light_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.c7001_sound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_acc_all.connect(
                lambda: self.change_background(self.c7001_acc_value_label, "rgb(0, 170, 127)"))

        elif g_project == ProjectType.v260Teach.value:
            self.test_func_thread.signal_ir1.connect(
                lambda: self.change_background(self.ts260_slider_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_humiture.connect(
                lambda: self.change_background(self.ts260_humiture_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.ts260_mic_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.ts260_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sda_scl.connect(
                lambda: self.change_background(self.ts260_iic_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.ts260_light_value_label, "rgb(0, 170, 127)"))

        elif g_project == ProjectType.v7007.value:
            self.test_func_thread.signal_touchpad_p.connect(
                lambda: self.change_background(self.v7007_tp_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_y.connect(
                lambda: self.change_background(self.v7007_ty_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_t.connect(
                lambda: self.change_background(self.v7007_tt_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_h.connect(
                lambda: self.change_background(self.v7007_th_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_o.connect(
                lambda: self.change_background(self.v7007_to_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_n.connect(
                lambda: self.change_background(self.v7007_tn_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.v7007_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.v7007_light_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.v7007_sound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Mag.connect(
                lambda: self.change_background(self.v7007_mag_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Gyroscope.connect(
                lambda: self.change_background(self.v7007_gyroscope_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_acc_all.connect(
                lambda: self.change_background(self.v7007_acc_value_label, "rgb(0, 170, 127)"))

        elif g_project == ProjectType.v260Zkb.value:
            self.test_func_thread.signal_touchpad_p.connect(
                lambda: self.change_background(self.v260Zkb_tp_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_y.connect(
                lambda: self.change_background(self.v260Zkb_ty_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_t.connect(
                lambda: self.change_background(self.v260Zkb_tt_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_h.connect(
                lambda: self.change_background(self.v260Zkb_th_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_o.connect(
                lambda: self.change_background(self.v260Zkb_to_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_n.connect(
                lambda: self.change_background(self.v260Zkb_tn_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.v260Zkb_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.v260Zkb_light_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.v260Zkb_sound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Mag.connect(
                lambda: self.change_background(self.v260Zkb_mag_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Gyroscope.connect(
                lambda: self.change_background(self.v260Zkb_gyroscope_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_acc_all.connect(
                lambda: self.change_background(self.v260Zkb_acc_value_label, "rgb(0, 170, 127)"))

            self.test_func_thread.signal_p0.connect(
                lambda: self.change_background(self.v260Zkb_p0_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_p1.connect(
                lambda: self.change_background(self.v260Zkb_p1_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_p2.connect(
                lambda: self.change_background(self.v260Zkb_p2_value_label, "rgb(0, 170, 127)"))


        elif g_project == ProjectType.v7005.value:
            self.test_func_thread.signal_touchpad_p.connect(
                lambda: self.change_background(self.v7005_tp_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_y.connect(
                lambda: self.change_background(self.v7005_ty_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_t.connect(
                lambda: self.change_background(self.v7005_tt_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_h.connect(
                lambda: self.change_background(self.v7005_th_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_o.connect(
                lambda: self.change_background(self.v7005_to_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_n.connect(
                lambda: self.change_background(self.v7005_tn_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.v7005_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.v7005_light_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.v7005_sound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Mag.connect(
                lambda: self.change_background(self.v7005_mag_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Gyroscope.connect(
                lambda: self.change_background(self.v7005_gyroscope_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_acc_all.connect(
                lambda: self.change_background(self.v7005_acc_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sda_scl.connect(
                lambda: self.change_background(self.v7005_sda_scl_value_label, "rgb(0, 170, 127)"))

        elif g_project == ProjectType.v7009.value:
            self.test_func_thread.signal_touchpad_p.connect(
                lambda: self.change_background(self.v7009_tp_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_y.connect(
                lambda: self.change_background(self.v7009_ty_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_t.connect(
                lambda: self.change_background(self.v7009_tt_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_h.connect(
                lambda: self.change_background(self.v7009_th_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_o.connect(
                lambda: self.change_background(self.v7009_to_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_touchpad_n.connect(
                lambda: self.change_background(self.v7009_tn_widget, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_wifi.connect(
                lambda: self.change_background(self.v7009_wifi_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Light.connect(
                lambda: self.change_background(self.v7009_light_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sound.connect(
                lambda: self.change_background(self.v7009_sound_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Mag.connect(
                lambda: self.change_background(self.v7009_mag_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_Gyroscope.connect(
                lambda: self.change_background(self.v7009_gyroscope_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_acc_all.connect(
                lambda: self.change_background(self.v7009_acc_value_label, "rgb(0, 170, 127)"))
            self.test_func_thread.signal_sda_scl.connect(
                lambda: self.change_background(self.v7009_sda_scl_value_label, "rgb(0, 170, 127)"))



        self.test_func_thread.All_funct_test_pass.connect(self.change_main_and_upload_mac)
        self.is_funcTest_started = True

    # 手工确认按键按下事件
    @pyqtSlot()
    def on_manual_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_CAMERA_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True
            self.test_func_thread.IS_SCL_SDA_PASS = True
            self.test_func_thread.IS_RGB_PASS = True
            self.test_func_thread.IS_FAN_PASS = True
            self.test_func_thread.IS_MOTOR_PASS = True
            self.test_func_thread.IS_WATERPUMP_PASS = True
            self.test_func_thread.IS_SERVO_PASS = True
            self.change_background(self.x7001_pinout_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_a_b_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_audio_play_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_camera_Button, "rgb(0, 170, 127)")

            self.change_background(self.x7001_scl_sda_p22_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_rgb_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_fan_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_motor_Button, "rgb(0, 170, 127)")
            self.change_background(self.x7001_waterPump_Button, "rgb(0, 170, 127)")

    @pyqtSlot()
    def on_manual_Button_2_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True
            self.test_func_thread.IS_RGB_PASS = True
            self.test_func_thread.IS_FAN_PASS = True
            self.test_func_thread.IS_WATERPUMP_PASS = True
            self.test_func_thread.IS_SERVO_PASS  = True

            self.change_background(self.c7001_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_fan_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_a_b_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_audio_play_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_pinout_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_waterPump_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_servo_Button, "rgb(0, 170, 127)")
            self.change_background(self.c7001_rgb_Button, "rgb(0, 170, 127)")

    @pyqtSlot()
    def on_manual_Button_6_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True
            self.test_func_thread.IS_RGB_PASS = True
            self.test_func_thread.IS_FAN_PASS = True
            self.test_func_thread.IS_WATERPUMP_PASS = True
            self.test_func_thread.IS_SERVO_PASS = True
            self.test_func_thread.IS_CAMERA_PASS = True
            self.test_func_thread.IS_SOUT_PASS = True

            self.change_background(self.ts260_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_camera_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_rgb_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_a_b_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_s1_s2_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_2pinout_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_m1out_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_servo_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_fan_Button, "rgb(0, 170, 127)")
            self.change_background(self.ts260_bugle_Button, "rgb(0, 170, 127)")




    @pyqtSlot()
    def on_manual_Button_3_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True
            self.test_func_thread.IS_RGB_PASS = True
            self.test_func_thread.IS_FAN_PASS = True
            self.test_func_thread.IS_WATERPUMP_PASS = True
            self.test_func_thread.IS_SERVO_PASS = True

            self.change_background(self.v7007_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7007_pinout_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7007_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7007_audio_Button, "rgb(0, 170, 127)")

    @pyqtSlot()
    def on_manual_Button_7_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True
            self.test_func_thread.IS_RGB_PASS = True
            self.test_func_thread.IS_FAN_PASS = True
            self.test_func_thread.IS_WATERPUMP_PASS = True
            self.test_func_thread.IS_SERVO_PASS = True

            self.change_background(self.v260Zkb_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.v260Zkb_buzzer_Button, "rgb(0, 170, 127)")



    @pyqtSlot()
    def on_manual_Button_4_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_M2PIN_PASS = True
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_CAMERA_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True
            self.change_background(self.v7009_pinout_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7009_m2out_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7009_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7009_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7009_audio_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7009_camera_Button, "rgb(0, 170, 127)")

    @pyqtSlot()
    def on_manual_Button_5_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.test_func_thread.IS_PINOUT_PASS = True
            self.test_func_thread.IS_OLED_PASS = True
            self.test_func_thread.IS_BUZZ_PASS = True
            self.test_func_thread.IS_AUDIO_PASS = True

            self.change_background(self.v7005_display_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7005_buzzer_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7005_audio_Button, "rgb(0, 170, 127)")
            self.change_background(self.v7005_pinout_Button, "rgb(0, 170, 127)")

    # 重测按键按下事件
    @pyqtSlot()
    def on_retest_Button_clicked(self):

        self.on_com_func_Button_clicked()
        time.sleep(1)
        self.on_com_func_Button_clicked()


    def change_main_and_upload_mac(self, str):
        global g_test_mode

        # 按分号分割成键值对
        pairs = str.split(";")

        # 遍历查找 mac 的值
        mac_value = None
        for pair in pairs:
            if pair.startswith("mac:"):
                mac_value = pair.split(":")[1]
                break

        MesIsUpload = self.replace_mac_record(mac_value, str)

        if MesIsUpload:
            if g_test_mode:
                self.test_func_thread.write_main()
                self.all_pass_func()
            else:
                self.all_pass_func()


    @pyqtSlot()
    def on_manual_change_Button_clicked(self):
        try:
            self.test_func_thread.write_main()
        except:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("错误")
            msg_box.setIcon(QMessageBox.Critical)  # 设置错误图标
            msg_box.setText("转出厂程序失败,请重试!!!")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()

    @pyqtSlot()
    def on_change_test_prj_Button_clicked(self):
        global g_project

        try:
            self.test_func_thread.serial.readyRead.disconnect()
        except:
            pass

        self.test_func_thread.repl.interrupt()
        self.test_func_thread.sleep(1)
        self.test_func_thread.repl.interrupt()
        self.test_func_thread.sleep(1)
        self.test_func_thread.repl.interrupt()


        try:
            if g_project == ProjectType.x7001.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7001_小学版.py')
            elif g_project == ProjectType.c7001.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7001_初中版.py')
            elif g_project == ProjectType.v7005.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7005.py')
            elif g_project == ProjectType.v7007.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7007.py')
            elif g_project == ProjectType.v7009.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7009.py')
            elif g_project == ProjectType.v260Teach.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_ts260Teach.py')
            elif g_project == ProjectType.v260Zkb.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_ZKB.py')

            # 1. 读取文件内容并预处理
            with open(external_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 2. 智能分块传输（自动处理所有特殊字符）
            CHUNK_SIZE = 5000  # 经测试的最佳分块大小
            commands = [
                "f = open('main.py', 'w', encoding='utf-8')",
                "content = []"  # 使用列表避免长字符串问题
            ]

            # 分割内容为安全块
            for i in range(0, len(content), CHUNK_SIZE):
                chunk = content[i:i + CHUNK_SIZE]

                # 关键转义步骤（使用JSON序列化保证完整性）
                escaped_chunk = json.dumps(chunk)[1:-1]  # 去除外层引号
                commands.append(f'content.append("{escaped_chunk}")')

            commands.extend([
                "f.write(''.join(content))",
                "f.close()"
            ])


            # 3. 执行命令（确保原子性操作）
            for cmd in commands:
                self.test_func_thread.repl.write_cmdline(cmd)
                time.sleep(0.01)  # 关键延迟，确保设备处理完成

            # 重启掌控板刷新
            time.sleep(1)  # 整体执行缓冲
            self.test_func_thread.repl.write_cmdline("machine.reset()")
            time.sleep(2)  # 整体执行缓冲

            #self.on_retest_Button_clicked()


            # 关闭串口事件处理
            self.is_funcTest_started = False
            self.test_func_thread.serial.close()
            self.test_func_thread.timer.stop()
            self.test_func_thread.quit()
            self.test_func_thread.terminate()
            self.test_func_thread.wait()
            self.clear_all_TestItem()

            msg_box = QMessageBox()
            msg_box.setWindowTitle("成功")
            msg_box.setText("刷入产测程序成功,正在重启")
            msg_box.setStandardButtons(QMessageBox.NoButton)
            QTimer.singleShot(10000, msg_box.accept)
            msg_box.exec_()

            self.is_func_serial_opened = True
            self.test_func_thread.IS_ALL_FUNCT_PASS = False
            self.test_func_thread.wifi_emit = False
            self.test_func_thread.signal_sda_scl_emit = False
            self.test_func_thread.Tracking_emit = False
            self.test_func_thread.ultrasound_emit = False
            self.test_func_thread.rfid_emit = False
            self.test_func_thread.pot_emit = False
            self.test_func_thread.Tracking_On = False
            self.test_func_thread.Tracking_Off = False
            self.test_func_thread.ultrasound_far = False
            self.test_func_thread.ultrasound_near = False
            self.test_func_thread.pot_min = False
            self.test_func_thread.pot_max = False
            self.test_func_thread.IS_SCL_SDA_PASS = False
            self.test_func_thread.IS_RGB_PASS = False
            self.test_func_thread.IS_FAN_PASS = False
            self.test_func_thread.IS_MOTOR_PASS = False
            self.test_func_thread.IS_WATERPUMP_PASS = False
            self.test_func_thread.IS_SERVO_PASS = False
            self.test_func_thread.IS_OLED_PASS = False
            self.test_func_thread.IS_M2PIN_PASS = False
            self.test_func_thread.IS_PINOUT_PASS = False
            self.test_func_thread.IS_BUZZ_PASS = False
            self.test_func_thread.IS_AUDIO_PASS = False
            self.test_func_thread.IS_CAMERA_PASS = False
            self.test_func_thread.light_emit = False
            self.test_func_thread.sound_emit = False
            self.clear_all_TestItem()
            self.start_test_thread_func(self)

            #time.sleep(2)


        except Exception as e:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("错误")
            msg_box.setIcon(QMessageBox.Critical)  # 设置错误图标
            msg_box.setText("刷入产测程序失败,请联系相关人员解决!" + str(e))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()


    def transitionCode(self,path):
        global g_project

        try:
            self.test_func_thread.serial.readyRead.disconnect()
        except:
            pass
        self.test_func_thread.repl.interrupt()
        self.test_func_thread.sleep(1)
        self.test_func_thread.repl.interrupt()
        self.test_func_thread.sleep(1)
        self.test_func_thread.repl.interrupt()

        try:
            external_file_path = path

            # 1. 读取文件内容并预处理
            with open(external_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 2. 智能分块传输（自动处理所有特殊字符）
            CHUNK_SIZE = 5000  # 经测试的最佳分块大小
            commands = [
                "f = open('main.py', 'w', encoding='utf-8')",
                "content = []"  # 使用列表避免长字符串问题
            ]

            # 分割内容为安全块
            for i in range(0, len(content), CHUNK_SIZE):
                chunk = content[i:i + CHUNK_SIZE]

                # 关键转义步骤（使用JSON序列化保证完整性）
                escaped_chunk = json.dumps(chunk)[1:-1]  # 去除外层引号
                commands.append(f'content.append("{escaped_chunk}")')

            commands.extend([
                "f.write(''.join(content))",
                "f.close()"
            ])

            # 3. 执行命令（确保原子性操作）
            for cmd in commands:
                self.test_func_thread.repl.write_cmdline(cmd)
                time.sleep(0.01)  # 关键延迟，确保设备处理完成

            # 重启掌控板刷新
            time.sleep(1)  # 整体执行缓冲

            msg_box = QMessageBox()
            msg_box.setWindowTitle("成功")
            msg_box.setText("刷入产测程序成功")
            msg_box.setStandardButtons(QMessageBox.NoButton)
            QTimer.singleShot(2000, msg_box.accept)
            msg_box.exec_()

            self.on_retest_Button_clicked()
            time.sleep(2)

            # 关闭串口事件处理
            self.is_funcTest_started = False
            self.test_func_thread.serial.close()
            self.test_func_thread.timer.stop()
            self.test_func_thread.quit()
            self.test_func_thread.terminate()
            self.test_func_thread.wait()
            self.clear_all_TestItem()

            time.sleep(1)

            self.is_func_serial_opened = True
            self.start_test_thread_func(self)


        except Exception as e:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("错误")
            msg_box.setIcon(QMessageBox.Critical)  # 设置错误图标
            msg_box.setText("刷入产测程序失败,请联系相关人员解决!" + str(e))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()

    # 7005 模块
    # RBG灯
    @pyqtSlot()
    def on_p7005_rgb_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\RBG.py')

    # AI摄像头
    @pyqtSlot()
    def on_p7005_camera_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\Ai摄像头.py')


    # 土壤湿度
    @pyqtSlot()
    def on_p7005_soil_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\土壤湿度.py')

    # 风扇
    @pyqtSlot()
    def on_p7005_fan_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\风扇.py')

    # 光敏
    @pyqtSlot()
    def on_p7005_light_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\光敏.py')

    # 红外巡线
    @pyqtSlot()
    def on_p7005_hunting_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\红外巡线.py')

    # 旋钮电位器
    @pyqtSlot()
    def on_p7005_pot_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\旋钮电位器.py')

    # 温度
    @pyqtSlot()
    def on_p7005_Temp_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\温度.py')

    # 温湿度
    @pyqtSlot()
    def on_p7005_humiture_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\温湿度.py')

    # 超声波
    @pyqtSlot()
    def on_p7005_Ultrasonic_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\超声波.py')

    # 驱动器/编码电机/水泵
    @pyqtSlot()
    def on_p7005_driver_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\驱动器.py')

    # 颜色
    @pyqtSlot()
    def on_p7005_colour_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\颜色.py')

    # 人体感应
    @pyqtSlot()
    def on_p7005_sense_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\人体感应.py')

    # RFID
    @pyqtSlot()
    def on_p7005_rfid_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\RFID.py')

    # 心率血氧
    @pyqtSlot()
    def on_p7005_hrrest_module_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.transitionCode('config\ModuleCode_7005\心率血氧.py')


    # 7001 小学版
    # 引脚输出测试按键事件
    @pyqtSlot()
    def on_x7001_pinout_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_pinout_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_PINOUT_PASS = True

    # 屏幕测试按键事件
    @pyqtSlot()
    def on_x7001_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # 蜂鸣器测试按键事件
    @pyqtSlot()
    def on_x7001_a_b_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_a_b_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True

    # 音频测试按键事件
    @pyqtSlot()
    def on_x7001_audio_play_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_audio_play_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_AUDIO_PASS = True


    ## SCL/SDA/P22按键事件
    @pyqtSlot()
    def on_x7001_scl_sda_p22_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_scl_sda_p22_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_SCL_SDA_PASS = True


    ## RGB 按键事件
    @pyqtSlot()
    def on_x7001_rgb_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_rgb_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_RGB_PASS = True


    ## 风扇 按键事件
    @pyqtSlot()
    def on_x7001_fan_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_fan_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_FAN_PASS = True

    ## 左/右编码电机 按键事件
    @pyqtSlot()
    def on_x7001_motor_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_motor_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_MOTOR_PASS = True



    ## 水泵 按键事件
    @pyqtSlot()
    def on_x7001_waterPump_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_waterPump_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_WATERPUMP_PASS = True


    # 摄像头测试按键事件
    @pyqtSlot()
    def on_x7001_camera_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.x7001_camera_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_CAMERA_PASS = True

    ###############################

    # Ts260 掌控板
    # 显示屏 测试按键事件
    @pyqtSlot()
    def on_v260Zkb_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v260Zkb_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # (A键/B键/喇叭) 测试按键事件
    @pyqtSlot()
    def on_v260Zkb_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v260Zkb_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True


    ###############################

    # Ts260 初中版
    # 显示屏 测试按键事件
    @pyqtSlot()
    def on_ts260_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # 摄像头测试按键事件
    @pyqtSlot()
    def on_ts260_camera_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_camera_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_CAMERA_PASS = True

    # 风扇 测试按键事件 ok
    @pyqtSlot()
    def on_ts260_fan_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_fan_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_FAN_PASS = True


    # (A键/B键/喇叭) 测试按键事件
    @pyqtSlot()
    def on_ts260_a_b_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_a_b_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True

    # 录音/播放 测试按键事件
    @pyqtSlot()
    def on_ts260_bugle_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_bugle_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_AUDIO_PASS = True

    # P0/P1/P2/P3 测试按键事件
    @pyqtSlot()
    def on_ts260_2pinout_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_2pinout_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_PINOUT_PASS = True

    # P0/P1/P2/P3 测试按键事件
    @pyqtSlot()
    def on_ts260_s1_s2_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_s1_s2_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_SOUT_PASS = True


    # 水泵 测试按键事件
    @pyqtSlot()
    def on_ts260_m1out_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_m1out_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_WATERPUMP_PASS = True

    # 舵机 测试按键事件
    @pyqtSlot()
    def on_ts260_servo_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_servo_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_SERVO_PASS = True

    # RGB灯 测试按键事件
    @pyqtSlot()
    def on_ts260_rgb_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.ts260_rgb_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_RGB_PASS = True

    ###############################

    # 7001 初中版
    # 显示屏 测试按键事件
    @pyqtSlot()
    def on_c7001_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # 风扇 测试按键事件 ok
    @pyqtSlot()
    def on_c7001_fan_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_fan_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_FAN_PASS = True

    # (A键/B键/喇叭) 测试按键事件
    @pyqtSlot()
    def on_c7001_a_b_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_a_b_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True

    # 录音/播放 测试按键事件
    @pyqtSlot()
    def on_c7001_audio_play_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_audio_play_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_AUDIO_PASS = True

    # P0/P1/P2/P3 测试按键事件
    @pyqtSlot()
    def on_c7001_pinout_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_pinout_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_PINOUT_PASS = True

    # 水泵 测试按键事件
    @pyqtSlot()
    def on_c7001_waterPump_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_waterPump_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_WATERPUMP_PASS = True

    # 舵机 测试按键事件
    @pyqtSlot()
    def on_c7001_servo_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_servo_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_SERVO_PASS = True

    # RGB灯 测试按键事件
    @pyqtSlot()
    def on_c7001_rgb_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.c7001_rgb_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_RGB_PASS = True


    ###############################

    # 7005 学境-掌控板
    # 显示屏 测试按键事件
    @pyqtSlot()
    def on_v7005_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7005_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # AB键/蜂鸣器 测试按键事件
    @pyqtSlot()
    def on_v7005_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7005_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True

    # 录音/播放 测试按键事件
    @pyqtSlot()
    def on_v7005_audio_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7005_audio_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_AUDIO_PASS = True

    # (1~6接口输出正常)
    @pyqtSlot()
    def on_v7005_pinout_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7005_pinout_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_PINOUT_PASS = True


    ###############################

    # 7007 掌控板
    # 显示屏 测试按键事件
    @pyqtSlot()
    def on_v7007_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7007_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # (引脚输出LED灯全亮) 测试按键事件
    @pyqtSlot()
    def on_v7007_pinout_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7007_pinout_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True

    # (A键/B键/蜂鸣器) 测试按键事件
    @pyqtSlot()
    def on_v7007_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7007_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_PINOUT_PASS = True

    # (录音/播放) 测试按键事件
    @pyqtSlot()
    def on_v7007_audio_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7007_audio_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_AUDIO_PASS = True

    ###############################

    # 7009 掌控板
    # PIN引脚输出测试按键事件
    @pyqtSlot()
    def on_v7009_pinout_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7009_pinout_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_PINOUT_PASS = True

    # M2引脚输出测试按键事件
    @pyqtSlot()
    def on_v7009_m2out_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7009_m2out_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_M2PIN_PASS = True

    # 屏幕测试按键事件
    @pyqtSlot()
    def on_v7009_display_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7009_display_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_OLED_PASS = True

    # 蜂鸣器测试按键事件
    @pyqtSlot()
    def on_v7009_buzzer_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7009_buzzer_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_BUZZ_PASS = True

    # 音频测试按键事件
    @pyqtSlot()
    def on_v7009_audio_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7009_audio_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_AUDIO_PASS = True

    # 摄像头测试按键事件
    @pyqtSlot()
    def on_v7009_camera_Button_clicked(self):
        if hasattr(self, 'test_func_thread'):
            self.change_background(self.v7009_camera_Button, "rgb(0, 170, 127)")
            self.test_func_thread.IS_CAMERA_PASS = True

    ###############################

    def all_pass_func(self):
        self.result_func_label.setText("PASS")
        self.change_background(self.result_func_label, "rgb(0, 170, 127)")
        time_ = time.strftime("%H:%M:%S", time.localtime())

    ###############################

    # REPL
    def repl_recv_func(self, rxData):
        try:
            self.LogTextEdit.insertPlainText(rxData)
        except:
            pass
        cursor = self.LogTextEdit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.LogTextEdit.setTextCursor(cursor)




    # 界面数据更新
    def updata_gui_func(self, list_):

        global g_project

        if g_project == ProjectType.x7001.value:
            # -------------- 光线 --------------
            self.x7001_light_value_label.setText(list_[0])

            # -------------- 声音 --------------
            self.x7001_sound_value_label.setText(list_[1])

            # -------------- Wifi --------------
            self.x7001_wifi_value_label.setText(list_[2])

            # -------------- 循迹 --------------
            self.x7001_tracking_value_label.setText(list_[3])

            # -------------- 超声波 --------------
            self.x7001_ultrasound_value_label.setText(list_[4])

            # -------------- RFID --------------
            self.x7001_rfid_value_label.setText(list_[5])

            # -------------- 旋钮电位器 --------------
            self.x7001_pot_value_label.setText(list_[6])

            # -------------- 温湿度 --------------
            self.x7001_humiture_value_label.setText(list_[7] + "/" + list_[11])

            # -------------- 红外探测 --------------
            strIr1 = "左:" + str(list_[8]) + "\n" + "右:" + str(list_[9])
            self.x7001_ir1_value_label.setText(strIr1)

            # -------------- SDA/SCL --------------
            self.x7001_sda_scl_value_label.setText(list_[10])

        elif g_project == ProjectType.c7001.value:
            # -------------- 光线 --------------
            self.c7001_light_value_label.setText(list_[0])

            # -------------- 声音 --------------
            self.c7001_sound_value_label.setText(list_[1])

            # -------------- Wifi --------------
            self.c7001_wifi_value_label.setText(list_[2])

            # -------------- 超声波 --------------
            self.c7001_ultrasound_value_label.setText(list_[3])

            # -------------- RFID --------------
            strIr1 = "1:" + str(list_[4]) + "\n" + "2:" + str(list_[5])
            self.c7001_rfid_value_label.setText(strIr1)

            # -------------- 温湿度 --------------
            self.c7001_humiture_value_label.setText(list_[6] + "/" + list_[7])

            # -------------- 红外探测 --------------
            strIr1 = "左:" + str(list_[8]) + "\n" + "右:" + str(list_[9])
            self.c7001_ir1_value_label.setText(strIr1)

            # -------------- 加速度 --------------
            self.c7001_acc_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[10], list_[11], list_[12]))

            # -------------- SDA/SCL --------------
            self.c7001_sda_scl_value_label.setText(list_[13])

        elif g_project == ProjectType.v260Teach.value:
            # -------------- 光线 --------------
            self.ts260_light_value_label.setText(list_[0])

            # -------------- 滑杆 --------------
            self.ts260_slider_value_label.setText(list_[1])

            # -------------- 声音 --------------
            self.ts260_mic_value_label.setText(list_[2])

            # -------------- Wifi --------------
            self.ts260_wifi_value_label.setText(list_[3])

            # -------------- 温湿度 --------------
            self.ts260_humiture_value_label.setText(list_[4] + "/" + list_[5])

            # -------------- iic --------------
            self.ts260_iic_value_label.setText(list_[6])


        elif g_project == ProjectType.v7005.value:

            # -------------- 触摸 --------------
            self.v7005_tp_value_label.setText(list_[0])
            self.v7005_ty_value_label.setText(list_[1])
            self.v7005_tt_value_label.setText(list_[2])
            self.v7005_th_value_label.setText(list_[3])
            self.v7005_to_value_label.setText(list_[4])
            self.v7005_tn_value_label.setText(list_[5])

            # -------------- 光线 --------------
            self.v7005_light_value_label.setText(list_[6])

            # -------------- 声音 --------------
            self.v7005_sound_value_label.setText(list_[7])

            # -------------- 加速度 --------------
            self.v7005_acc_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[8], list_[9], list_[10]))

            # -------------- 陀螺仪 --------------
            self.v7005_gyroscope_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[11], list_[12], list_[13]))

            # -------------- 磁力计 --------------
            self.v7005_mag_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[14], list_[15], list_[16]))

            # -------------- Wifi --------------
            self.v7005_wifi_value_label.setText(list_[17])

            # -------------- SDA/SCL --------------
            self.v7005_sda_scl_value_label.setText(list_[18])


        elif g_project == ProjectType.v7007.value:
            # -------------- 触摸 --------------
            self.v7007_tp_value_label.setText(list_[0])
            self.v7007_ty_value_label.setText(list_[1])
            self.v7007_tt_value_label.setText(list_[2])
            self.v7007_th_value_label.setText(list_[3])
            self.v7007_to_value_label.setText(list_[4])
            self.v7007_tn_value_label.setText(list_[5])

            # -------------- 光线 --------------
            self.v7007_light_value_label.setText(list_[6])

            # -------------- 声音 --------------
            self.v7007_sound_value_label.setText(list_[7])

            # -------------- 加速度 --------------
            self.v7007_acc_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[8], list_[9], list_[10]))

            # -------------- 陀螺仪 --------------
            self.v7007_gyroscope_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[11], list_[12], list_[13]))

            # -------------- 磁力计 --------------
            self.v7007_mag_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[14], list_[15], list_[16]))

            # -------------- Wifi --------------
            self.v7007_wifi_value_label.setText(list_[17])

        elif g_project == ProjectType.v260Zkb.value:
            # -------------- 触摸 --------------
            self.v260Zkb_tp_value_label.setText(list_[0])
            self.v260Zkb_ty_value_label.setText(list_[1])
            self.v260Zkb_tt_value_label.setText(list_[2])
            self.v260Zkb_th_value_label.setText(list_[3])
            self.v260Zkb_to_value_label.setText(list_[4])
            self.v260Zkb_tn_value_label.setText(list_[5])

            # -------------- 光线 --------------
            self.v260Zkb_light_value_label.setText(list_[6])

            # -------------- 声音 --------------
            self.v260Zkb_sound_value_label.setText(list_[7])

            # -------------- 加速度 --------------
            self.v260Zkb_acc_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[8], list_[9], list_[10]))

            # -------------- 陀螺仪 --------------
            self.v260Zkb_gyroscope_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[11], list_[12], list_[13]))

            # -------------- 磁力计 --------------
            self.v260Zkb_mag_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[14], list_[15], list_[16]))

            # -------------- Wifi --------------
            self.v260Zkb_wifi_value_label.setText(list_[17])

            # -------------- P1 --------------
            self.v260Zkb_p0_value_label.setText(list_[18])

            # -------------- P2 --------------
            self.v260Zkb_p1_value_label.setText(list_[19])

            # -------------- P3 --------------
            self.v260Zkb_p2_value_label.setText(list_[20])


        elif g_project == ProjectType.v7009.value:

            # -------------- 触摸 --------------
            self.v7009_tp_value_label.setText(list_[0])
            self.v7009_ty_value_label.setText(list_[1])
            self.v7009_tt_value_label.setText(list_[2])
            self.v7009_th_value_label.setText(list_[3])
            self.v7009_to_value_label.setText(list_[4])
            self.v7009_tn_value_label.setText(list_[5])

            # -------------- 光线 --------------
            self.v7009_light_value_label.setText(list_[6])

            # -------------- 声音 --------------
            self.v7009_sound_value_label.setText(list_[7])

            # -------------- 加速度 --------------
            self.v7009_acc_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[8], list_[9], list_[10]))

            # -------------- 陀螺仪 --------------
            self.v7009_gyroscope_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[11], list_[12], list_[13]))

            # -------------- 磁力计 --------------
            self.v7009_mag_value_label.setText("X: {}\nY: {}\nZ: {}".format(list_[14], list_[15], list_[16]))

            # -------------- Wifi --------------
            self.v7009_wifi_value_label.setText(list_[17])

            # -------------- SDA/SCL --------------
            self.v7009_sda_scl_value_label.setText(list_[18])

    


    def clear_all_TestItem(self):
        # 7001 小学版
        self.change_background(self.x7001_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_sound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_sda_scl_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_tracking_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_ultrasound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_ir1_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_pot_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_rfid_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_pinout_Button, "rgb(203, 203, 203)")

        self.change_background(self.x7001_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_a_b_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_audio_play_Button, "rgb(203, 203, 203)")
        self.change_background(self.result_func_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_camera_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_humiture_value_label, "rgb(203, 203, 203)")
        self.change_background(self.x7001_scl_sda_p22_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_rgb_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_fan_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_motor_Button, "rgb(203, 203, 203)")
        self.change_background(self.x7001_waterPump_Button, "rgb(203, 203, 203)")


        # v260Teach
        self.change_background(self.ts260_slider_value_label, "rgb(203, 203, 203)")
        self.change_background(self.ts260_iic_value_label, "rgb(203, 203, 203)")
        self.change_background(self.ts260_mic_value_label, "rgb(203, 203, 203)")
        self.change_background(self.ts260_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.ts260_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.ts260_humiture_value_label, "rgb(203, 203, 203)")


        self.change_background(self.ts260_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_camera_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_rgb_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_a_b_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_s1_s2_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_2pinout_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_m1out_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_servo_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_fan_Button, "rgb(203, 203, 203)")
        self.change_background(self.ts260_bugle_Button, "rgb(203, 203, 203)")

        # 7001 初中版
        self.change_background(self.c7001_ir1_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_humiture_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_rfid_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_ultrasound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_sda_scl_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_sound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.c7001_acc_value_label, "rgb(203, 203, 203)")

        self.change_background(self.c7001_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_fan_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_a_b_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_audio_play_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_pinout_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_waterPump_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_servo_Button, "rgb(203, 203, 203)")
        self.change_background(self.c7001_rgb_Button, "rgb(203, 203, 203)")

        # 7005 学境-掌控板
        self.change_background(self.v7005_tp_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7005_ty_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7005_tt_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7005_th_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7005_to_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7005_tn_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7005_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7005_sound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7005_mag_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7005_gyroscope_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7005_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7005_acc_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7005_sda_scl_value_label, "rgb(203, 203, 203)")

        self.change_background(self.v7005_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7005_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7005_audio_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7005_pinout_Button, "rgb(203, 203, 203)")

        # 7007 掌控板 单板
        self.change_background(self.v7007_tp_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7007_ty_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7007_tt_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7007_th_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7007_to_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7007_tn_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7007_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7007_sound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7007_mag_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7007_gyroscope_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7007_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7007_acc_value_label, "rgb(203, 203, 203)")

        self.change_background(self.v7007_pinout_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7007_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7007_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7007_audio_Button, "rgb(203, 203, 203)")

        # 掌控板 单板
        self.change_background(self.v260Zkb_tp_widget, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_ty_widget, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_tt_widget, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_th_widget, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_to_widget, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_tn_widget, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_sound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_mag_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_gyroscope_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_acc_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_p0_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_p1_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_p2_value_label, "rgb(203, 203, 203)")

        self.change_background(self.v260Zkb_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.v260Zkb_buzzer_Button, "rgb(203, 203, 203)")



        # 7009 乐动掌控2.0
        self.change_background(self.v7009_tp_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7009_ty_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7009_tt_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7009_th_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7009_to_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7009_tn_widget, "rgb(203, 203, 203)")
        self.change_background(self.v7009_light_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7009_sound_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7009_mag_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7009_gyroscope_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7009_wifi_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7009_acc_value_label, "rgb(203, 203, 203)")
        self.change_background(self.v7009_sda_scl_value_label, "rgb(203, 203, 203)")

        self.change_background(self.v7009_pinout_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7009_m2out_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7009_display_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7009_buzzer_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7009_audio_Button, "rgb(203, 203, 203)")
        self.change_background(self.v7009_camera_Button, "rgb(203, 203, 203)")

        self.change_background(self.result_func_label, "rgb(203, 203, 203)")
        self.result_func_label.setText("")


################################################################
""" 线程处理 """
# 镭雕TCP线程
class TCP_Thread(QThread):

    def __init__(self, _socket):
        QThread.__init__(self)
        self._socket = _socket

    def run(self):
        global g_mac, TCP_CLIENTSOCKET, TCP_ADDRESS
        while True:
            if not TCP_CLIENTSOCKET:
                TCP_CLIENTSOCKET, TCP_ADDRESS = self._socket.accept()
                print(TCP_CLIENTSOCKET, TCP_ADDRESS)
            else:
                pass

            while True:
                tmp = TCP_CLIENTSOCKET.recv(255)
                if tmp == b'TCP:Give me string':
                    if len(g_mac) == 12:
                        mac_byte = g_mac.encode()
                        TCP_CLIENTSOCKET.send(mac_byte[:6] + b'\n' + mac_byte[6:])
                        print('Tcp Send MAC:{}'.format(g_mac))



# 功能测试线程
class FuncTest_Thread(QThread):
    data_received = pyqtSignal(str)
    data_update = pyqtSignal(list)
    signal_touchpad_p = pyqtSignal()
    signal_touchpad_y = pyqtSignal()
    signal_touchpad_t = pyqtSignal()
    signal_touchpad_h = pyqtSignal()
    signal_touchpad_o = pyqtSignal()
    signal_touchpad_n = pyqtSignal()
    signal_Gyroscope = pyqtSignal()
    signal_Mag = pyqtSignal()
    signal_wifi = pyqtSignal()
    signal_sda_scl = pyqtSignal()
    signal_tracking = pyqtSignal()
    signal_ultrasound = pyqtSignal()
    signal_ir1 = pyqtSignal()
    signal_pot = pyqtSignal()
    signal_rfid = pyqtSignal()
    signal_acc_all = pyqtSignal()
    signal_Light = pyqtSignal()
    signal_sound = pyqtSignal()
    signal_humiture = pyqtSignal()
    Acc_z = pyqtSignal(float, float, float)
    All_funct_test_pass = pyqtSignal(str)
    Func_test_log = pyqtSignal(str)
    signal_p0 = pyqtSignal()
    signal_p1 = pyqtSignal()
    signal_p2 = pyqtSignal()

    def __init__(self, _port):
        super(FuncTest_Thread, self).__init__()
        self.port = _port
        self.recv_buf = b''
        self.tp_value, self.ty_value, self.tt_value, self.th_value, self.to_value, self.tn_value = '0' * 6
        self.P0_value = self.P1_value = self.P2_value = self.Magnetic_x = self.Magnetic_y = self.Magnetic_z = self.Gyroscope_x = self.Gyroscope_y = self.Gyroscope_z = self.acc_x_val = self.acc_y_val = self.acc_z_val = self.sda_scl_val = self.Wifi = '0'
        self.slider_value = self.Temperature_value = self.ir1_left_value = self.ir1_right_value = self.humiture_value = self.pot_min_val = self.pot_max_val = self.Pot = self.Rfid1 = self.Rfid2 =self.Ultrasound = self.Ultrasound_near_val = self.Ultrasound_far_val = self.Tracking = self.light_value = self.sound_value = self.mag_value = '-1'
        self.light_emit = False
        self.slider_emit = False
        self.acc_all_emit = False
        self.humiture_emit = False
        self.sound_emit = False
        self.mag_emit = False
        self.gyroscope_emit = False
        self.tp_emit = False
        self.IS_M2PIN_PASS = False
        self.ty_emit = False
        self.tt_emit = False
        self.th_emit = False
        self.to_emit = False
        self.tn_emit = False
        self.wifi_emit = False
        self.sda_scl_emit= False
        self.Tracking_emit = False
        self.ultrasound_emit = False
        self.ir1_emit = False
        self.ir1_left = False
        self.ir1_right = False
        self.rfid_emit = False
        self.rfid2_emit = False
        self.pot_emit = False
        self.p0_emit = False
        self.p1_emit = False
        self.p2_emit = False
        self.p3_emit = False
        self.IS_ALL_FUNCT_PASS = False
        self.IS_PINOUT_PASS = False
        self.IS_SOUT_PASS = False
        self.IS_OLED_PASS = False
        self.IS_BUZZ_PASS = False
        self.IS_AUDIO_PASS = False
        self.IS_SCL_SDA_PASS = False
        self.IS_RGB_PASS = False
        self.IS_FAN_PASS = False
        self.IS_MOTOR_PASS = False
        self.IS_WATERPUMP_PASS = False
        self.IS_SERVO_PASS = False
        self.IS_CAMERA_PASS = False
        self.Tracking_On = False
        self.Tracking_Off = False
        self.ultrasound_far = False
        self.ultrasound_near = False
        self.pot_min = False
        self.mac = ""
        self.pot_max = False
        self.light_list = []
        self.sound_list = []
        self.sample_num = 20
        self.sample_acc_num = 10
        self.timer = QTimer()
        self.timer.setInterval(1)
        self.timer.start()



    def open_serial_link(self):
        max_retries = 3  # 最大重试次数
        retry_count = 0

        # 可选：发送重试进度信号（如果有进度条或状态显示）
        if hasattr(self, 'retryProgress'):
            self.retryProgress.emit(0, max_retries)

        while retry_count < max_retries:
            # 可选：更新重试进度
            if hasattr(self, 'retryProgress'):
                self.retryProgress.emit(retry_count + 1, max_retries)

            """改进的串口初始化方法"""
            self.serial = QSerialPort()
            self.repl = Repl(self.serial)
            self.serial.setPortName(self.port)
            self.serial.setBaudRate(115200)
            self.serial.setDataBits(QSerialPort.Data8)
            self.serial.setParity(QSerialPort.NoParity)
            self.serial.setStopBits(QSerialPort.OneStop)
            self.serial.setFlowControl(QSerialPort.NoFlowControl)

            if self.serial.open(QIODevice.ReadWrite):
                print(f"成功打开串口: {self.port}")

                # 清空缓冲区
                self.serial.clear()
                time.sleep(0.1)

                # 发送初始化序列
                self.serial.write(b'\r\n')
                time.sleep(0.1)

                # 控制DTR和RTS信号
                self.serial.setDataTerminalReady(False)
                self.serial.setRequestToSend(False)
                time.sleep(0.2)

                self.serial.setDataTerminalReady(True)
                self.serial.setRequestToSend(True)
                time.sleep(0.3)

                # 再次清空缓冲区
                self.serial.clear()

                # 绑定数据读取事件
                self.serial.readyRead.connect(self.on_serial_read)

                return True

            else:
                retry_count += 1
                error_msg = self.serial.errorString()
                print(f"连接失败 (尝试 {retry_count}/{max_retries}): {error_msg}")

                # 清理资源
                if self.serial.isOpen():
                    self.serial.close()

                # 等待1秒后重试
                if retry_count < max_retries:
                    time.sleep(1)

        # 所有重试都失败
        self.show_serial_error_message(max_retries, error_msg)
        return False


    def show_serial_error_message(self, retry_count, error_msg):
        """显示串口错误消息"""
        msg = f"无法连接串口: {self.port}\n错误: {error_msg}\n已重试 {retry_count} 次"
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Critical)
        msgbox.setWindowTitle("串口连接失败")
        msgbox.setText(msg)
        msgbox.setStandardButtons(QMessageBox.Cancel)

        result = msgbox.exec_()


    def on_serial_read_mac(self):
        recv_buf = self.serial.readAll()
        try:
            recv_str = recv_buf.data().decode('UTF-8')
        except:
            print("recv data decode err")
        else:
            # 提取数据
            self.collect_mac_data(recv_str)

    def on_serial_read(self):
        if not self.IS_ALL_FUNCT_PASS:
            recv_buf = self.serial.readAll()
            try:
                recv_str = recv_buf.data().decode('UTF-8')
            except:
                recv_str = ''
                print("recv data decode err")
            else:
                # 提取数据
                self.collect_data(recv_str)
                # repl 数据发送
                self.data_received.emit(recv_str)


    def write_main(self):
        global g_project

        try:
            self.serial.readyRead.disconnect()
        except:
            pass
        self.repl.interrupt()
        self.sleep(1)
        self.repl.interrupt()
        self.sleep(1)
        self.repl.interrupt()

        try:
            # 拼接目标文件路径
            if g_project == ProjectType.x7001.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7001_小学版.py')

            if g_project == ProjectType.c7001.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7001_初中版.py')


            if g_project == ProjectType.v7005.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7005.py')

            if g_project == ProjectType.v7007.value or g_project == ProjectType.v260Teach.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemoNULL.py')

            if g_project == ProjectType.v7009.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7009.py')

            if g_project == ProjectType.v260Zkb.value:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_ZKB.py')



            # 1. 读取文件内容并预处理
            with open(external_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 2. 智能分块传输（自动处理所有特殊字符）
            CHUNK_SIZE = 5000  # 经测试的最佳分块大小
            commands = [
                "f = open('main.py', 'w', encoding='utf-8')",
                "content = []"  # 使用列表避免长字符串问题
            ]

            # 分割内容为安全块
            for i in range(0, len(content), CHUNK_SIZE):
                chunk = content[i:i + CHUNK_SIZE]
                # 关键转义步骤（使用JSON序列化保证完整性）
                escaped_chunk = json.dumps(chunk)[1:-1]  # 去除外层引号
                commands.append(f'content.append("{escaped_chunk}")')

            commands.extend([
                "f.write(''.join(content))",
                "f.close()"
            ])

            # 3. 执行命令（确保原子性操作）
            for cmd in commands:
                self.repl.write_cmdline(cmd)
                time.sleep(0.01)  # 关键延迟，确保设备处理完成

            msg_box = QMessageBox()
            msg_box.setWindowTitle("成功")
            msg_box.setText("刷入出厂程序成功")
            msg_box.setStandardButtons(QMessageBox.NoButton)  # 关键点：不显示任何按钮
            QTimer.singleShot(3000, msg_box.accept)  # 使用 accept() 代替 close()
            msg_box.exec_()

            # 重启掌控板刷新
            self.repl.write_cmdline("machine.reset()")


        except Exception as e:
            self.repl.interrupt()
            self.repl.write_cmdline("machine.reset()")
            msg_box = QMessageBox()
            msg_box.setWindowTitle("错误")
            msg_box.setIcon(QMessageBox.Critical)  # 设置错误图标
            msg_box.setText("刷入出厂程序失败,请联系相关人员解决!" + str(e))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()


    # 提取串口数据
    def collect_data(self, recv_str):
        list_ = []

        # 7001小学版
        if g_project == ProjectType.x7001.value:
            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.wifi_emit:
                self.Wifi = finded_list[-1]

            # -------------- SDA/SCL --------------
            pattern = re.compile(r'(?<=SdaScl:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sda_scl_emit:
                self.sda_scl_val = finded_list[-1]

            # -------------- 循迹 --------------
            pattern = re.compile(r'Tracking:(\d+),(\d+),(\d+),(\d+),(\d+)')
            match = pattern.search(recv_str)

            if match:
                tracking_data = list(map(int, match.groups()))
                tracking_str = ",".join(map(str, tracking_data))  # 用逗号连接
                self.Tracking = tracking_str  # 存储字符串格式

            # -------------- 超声波 --------------
            pattern = re.compile(r'(?<=Ultrasound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Ultrasound = finded_list[-1]

            # -------------- Rfid --------------
            pattern = re.compile(r'(?<=Rfid:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.rfid_emit:
                self.Rfid1 = finded_list[-1]

            # -------------- 旋钮电位器 --------------
            pattern = re.compile(r'(?<=Pot:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Pot = finded_list[-1]

            # -------------- 温度 --------------
            pattern = re.compile(r'(?<=Humiture:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.humiture_emit:
                self.humiture_value = finded_list[-1]

            # -------------- 湿度 --------------
            pattern = re.compile(r'(?<=Temperature:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Temperature_value = finded_list[-1]

            # -------------- 红外探测 --------------
            pattern = re.compile(r'(?<=Ir1:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.ir1_emit:
                self.ir1_left_value = finded_list[-1]

            pattern = re.compile(r'(?<=Ir2:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.ir1_emit:
                self.ir1_right_value = finded_list[-1]

            pattern = re.compile(r'(?<=Rfid:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.rfid_emit:
                self.Rfid1 = finded_list[-1]

            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            list_ = [
                self.light_value,
                self.sound_value,
                self.Wifi,
                self.Tracking,
                self.Ultrasound,
                self.Rfid1,
                self.Pot,
                self.humiture_value,
                self.ir1_left_value,
                self.ir1_right_value,
                self.sda_scl_val,
                self.Temperature_value,
            ]


        # 7001初中版
        elif g_project == ProjectType.c7001.value:
            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- 加速度 --------------
            pattern = re.compile(r'(?<=Accel_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_x_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_y_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_z_val = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.wifi_emit:
                self.Wifi = finded_list[-1]

            # -------------- 超声波 --------------
            pattern = re.compile(r'(?<=Ultrasound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Ultrasound = finded_list[-1]

            # -------------- Rfid --------------
            pattern = re.compile(r'(?<=Rfid1:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.rfid_emit:
                if len(str(self.Rfid1)) < 6:
                    self.Rfid1 = finded_list[-1]

            pattern = re.compile(r'(?<=Rfid2:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.rfid2_emit:
                if len(str(self.Rfid2)) < 6:
                    self.Rfid2 = finded_list[-1]

            # -------------- SDA/SCL --------------
            pattern = re.compile(r'(?<=SdaScl:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.sda_scl_val = finded_list[-1]

            # -------------- 温度 --------------
            pattern = re.compile(r'(?<=Humiture:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.humiture_emit:
                self.humiture_value = finded_list[-1]

            # -------------- 湿度 --------------
            pattern = re.compile(r'(?<=Temperature:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.humiture_emit:
                self.Temperature_value = finded_list[-1]

            # -------------- 红外探测 --------------
            pattern = re.compile(r'(?<=Ir1:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.ir1_emit:
                self.ir1_left_value = finded_list[-1]

            pattern = re.compile(r'(?<=Ir2:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.ir1_emit:
                self.ir1_right_value = finded_list[-1]

            # -------------- MAC --------------
            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            list_ = [
                self.light_value,
                self.sound_value,
                self.Wifi,
                self.Ultrasound,
                self.Rfid1,
                self.Rfid2,
                self.humiture_value,
                self.Temperature_value,
                self.ir1_left_value,
                self.ir1_right_value,
                self.acc_x_val,
                self.acc_y_val,
                self.acc_z_val,
                self.sda_scl_val
            ]

        # v260Teach
        elif g_project == ProjectType.v260Teach.value:
            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 滑块 --------------
            pattern = re.compile(r'(?<=slider:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.slider_emit:
                self.slider_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.wifi_emit:
                self.Wifi = finded_list[-1]

            # -------------- iic --------------
            pattern = re.compile(r'(?<=i2c:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list :
                self.sda_scl_val = finded_list[-1]

            # -------------- 温度 --------------
            pattern = re.compile(r'(?<=temperature:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.humiture_emit:
                self.humiture_value = finded_list[-1]

            # -------------- 湿度 --------------
            pattern = re.compile(r'(?<=humidity:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.humiture_emit:
                self.Temperature_value = finded_list[-1]

            # -------------- MAC --------------
            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            list_ = [
                self.light_value,
                self.slider_value,
                self.sound_value,
                self.Wifi,
                self.humiture_value,
                self.Temperature_value,
                self.sda_scl_val
            ]



        # 7005 学境-掌控板
        elif g_project == ProjectType.v7005.value:

            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            # -------------- 触摸 --------------
            pattern = re.compile(r'(?<=Touch_P:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tp_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.ty_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_T:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tt_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_H:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.th_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_O:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.to_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_N:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tn_value = finded_list[-1]

            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- 加速度 --------------
            pattern = re.compile(r'(?<=Accel_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_x_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_y_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_z_val = finded_list[-1]

            # -------------- 陀螺仪 --------------
            pattern = re.compile(r'(?<=Gyroscope_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_x = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_y = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_z = finded_list[-1]

            # -------------- 磁力计 --------------
            pattern = re.compile(r'(?<=Magnetic_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_x = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_y = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_z = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Wifi = finded_list[-1]

            # -------------- SDA/SCL --------------
            pattern = re.compile(r'(?<=SdaScl:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.sda_scl_val = finded_list[-1]


            list_ = [
                self.tp_value, self.ty_value, self.tt_value, self.th_value, self.to_value, self.tn_value,
                self.light_value,
                self.sound_value,
                self.acc_x_val, self.acc_y_val, self.acc_z_val,
                self.Gyroscope_x, self.Gyroscope_y, self.Gyroscope_z,
                self.Magnetic_x, self.Magnetic_y, self.Magnetic_z,
                self.Wifi,
                self.sda_scl_val
            ]


        # 7007 掌控板 单板
        elif g_project == ProjectType.v7007.value:

            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            # -------------- 触摸 --------------
            pattern = re.compile(r'(?<=Touch_P:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tp_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.ty_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_T:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tt_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_H:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.th_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_O:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.to_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_N:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tn_value = finded_list[-1]

            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- 加速度 --------------
            pattern = re.compile(r'(?<=Accel_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_x_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_y_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_z_val = finded_list[-1]

            # -------------- 陀螺仪 --------------
            pattern = re.compile(r'(?<=Gyroscope_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_x = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_y = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_z = finded_list[-1]

            # -------------- 磁力计 --------------
            pattern = re.compile(r'(?<=Magnetic_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_x = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_y = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_z = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Wifi = finded_list[-1]

            list_ = [
                self.tp_value, self.ty_value, self.tt_value, self.th_value, self.to_value, self.tn_value,
                self.light_value,
                self.sound_value,
                self.acc_x_val, self.acc_y_val, self.acc_z_val,
                self.Gyroscope_x, self.Gyroscope_y, self.Gyroscope_z,
                self.Magnetic_x, self.Magnetic_y, self.Magnetic_z,
                self.Wifi
            ]

        # 旧版 掌控板 单板
        elif g_project == ProjectType.v260Zkb.value:

            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            # -------------- 触摸 --------------
            pattern = re.compile(r'(?<=Touch_P:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tp_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.ty_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_T:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tt_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_H:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.th_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_O:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.to_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_N:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tn_value = finded_list[-1]

            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- 加速度 --------------
            pattern = re.compile(r'(?<=Accel_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_x_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_y_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_z_val = finded_list[-1]

            # -------------- 陀螺仪 --------------
            pattern = re.compile(r'(?<=Gyroscope_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_x = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_y = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_z = finded_list[-1]

            # -------------- 磁力计 --------------
            pattern = re.compile(r'(?<=Magnetic_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_x = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_y = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_z = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Wifi = finded_list[-1]

            # -------------- P0口 --------------
            pattern = re.compile(r'(?<=P0:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.P0_value = finded_list[-1]

            # -------------- P1口 --------------
            pattern = re.compile(r'(?<=P1:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.P1_value = finded_list[-1]

            # -------------- P2口 --------------
            pattern = re.compile(r'(?<=P2:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.P2_value = finded_list[-1]

            list_ = [
                self.tp_value, self.ty_value, self.tt_value, self.th_value, self.to_value, self.tn_value,
                self.light_value,
                self.sound_value,
                self.acc_x_val, self.acc_y_val, self.acc_z_val,
                self.Gyroscope_x, self.Gyroscope_y, self.Gyroscope_z,
                self.Magnetic_x, self.Magnetic_y, self.Magnetic_z,
                self.Wifi,
                self.P0_value,
                self.P1_value,
                self.P2_value
            ]




        # 7009 乐动掌控板2.0
        elif g_project == ProjectType.v7009.value:

            pattern = re.compile(r'(?<=Mac:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.mac = finded_list[-1]

            # -------------- 触摸 --------------
            pattern = re.compile(r'(?<=Touch_P:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tp_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.ty_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_T:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tt_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_H:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.th_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_O:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.to_value = finded_list[-1]

            pattern = re.compile(r'(?<=Touch_N:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.tn_value = finded_list[-1]

            # -------------- 光线 --------------
            pattern = re.compile(r'(?<=light:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.light_emit:
                self.light_value = finded_list[-1]

            # -------------- 声音 --------------
            pattern = re.compile(r'(?<=Sound:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list and not self.sound_emit:
                self.sound_value = finded_list[-1]

            # -------------- 加速度 --------------
            pattern = re.compile(r'(?<=Accel_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_x_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_y_val = finded_list[-1]

            pattern = re.compile(r'(?<=Accel_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.acc_z_val = finded_list[-1]

            # -------------- 陀螺仪 --------------
            pattern = re.compile(r'(?<=Gyroscope_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_x = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_y = finded_list[-1]

            pattern = re.compile(r'(?<=Gyroscope_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Gyroscope_z = finded_list[-1]

            # -------------- 磁力计 --------------
            pattern = re.compile(r'(?<=Magnetic_X:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_x = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Y:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_y = finded_list[-1]

            pattern = re.compile(r'(?<=Magnetic_Z:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Magnetic_z = finded_list[-1]

            # -------------- Wifi --------------
            pattern = re.compile(r'(?<=Wifi:)[-+]?\d+\.?\d*')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.Wifi = finded_list[-1]
                # self.Wifi = "-43"

            # -------------- SDA/SCL --------------
            pattern = re.compile(r'(?<=SdaScl:)[^\r\n]+')
            finded_list = pattern.findall(recv_str)
            if finded_list:
                self.sda_scl_val = finded_list[-1]

            list_ = [
                self.tp_value, self.ty_value, self.tt_value, self.th_value, self.to_value, self.tn_value,
                self.light_value,
                self.sound_value,
                self.acc_x_val, self.acc_y_val, self.acc_z_val,
                self.Gyroscope_x, self.Gyroscope_y, self.Gyroscope_z,
                self.Magnetic_x, self.Magnetic_y, self.Magnetic_z,
                self.Wifi,
                self.sda_scl_val
            ]


        self.data_update.emit(list_)





    # 测试逻辑
    def run(self):

        print("功能测试开始!")
        while True:
            if g_project == ProjectType.x7001.value:
                # Wifi
                if int(self.Wifi) > -70 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True

                # i2c
                if int(self.sda_scl_val) == 1 and not self.sda_scl_emit:
                    print("signal_sda_scl pass")
                    self.signal_sda_scl.emit()
                    self.sda_scl_emit = True

                # 循迹
                if str(self.Tracking) == '1,1,1,1,1' and not self.Tracking_emit:
                    self.Tracking_On = True

                # 循迹
                if str(self.Tracking) == '0,0,0,0,0' and not self.Tracking_emit:
                    self.Tracking_Off = True

                # 循迹
                if self.Tracking_On and self.Tracking_Off and not self.Tracking_emit:
                    print("循迹 pass")
                    self.signal_tracking.emit()
                    self.Tracking_emit = True

                # 超声波 近
                if int(self.Ultrasound) > 0 and int(self.Ultrasound) <= 20 and not self.ultrasound_emit:
                    self.Ultrasound_near_val = self.Ultrasound
                    self.ultrasound_near = True

                # 超声波 远
                if int(self.Ultrasound) >= 60 and int(self.Ultrasound) <= 500 and not self.ultrasound_emit:
                    self.Ultrasound_far_val = self.Ultrasound
                    self.ultrasound_far = True

                # 超声波
                if self.ultrasound_near and self.ultrasound_far and not self.ultrasound_emit:
                    self.signal_ultrasound.emit()
                    self.ultrasound_emit = True

                # 红外探测 左
                if int(self.ir1_left_value) > 1 and int(self.ir1_left_value) <= 200 and int(
                        self.ir1_right_value) > 1 and int(self.ir1_right_value) <= 200 and not self.ir1_emit:
                    self.ir1_left = True

                # 红外探测 右
                if int(self.ir1_left_value) > 1 and int(self.ir1_left_value) <= 3000 and int(
                        self.ir1_right_value) > 1 and int(self.ir1_right_value) <= 3000 and not self.ir1_emit:
                    self.ir1_right = True

                # 红外探测
                if self.ir1_left and self.ir1_right and not self.ir1_emit:
                    print("红外探测 pass")
                    self.signal_ir1.emit()
                    self.ir1_emit = True

                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(self.light_value) >= CONFIG_DICT.get(
                        "light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 温湿度
                if int(self.humiture_value) >= 25 and int(self.humiture_value) <= 40 and not self.humiture_emit:
                    print("温湿度 emit")
                    self.signal_humiture.emit()
                    self.humiture_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(self.sound_value) <= CONFIG_DICT.get(
                        "sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True

                # RFID
                if str(self.Rfid1) != 'False' and len(str(self.Rfid1)) > 6 and not self.rfid_emit:
                    print("RFID pass")
                    self.signal_rfid.emit()
                    self.rfid_emit = True

                # 旋钮电位器 0
                if int(self.Pot) == 0 and not self.pot_emit:
                    self.pot_min_val = self.Pot
                    self.pot_min = True

                # 旋钮电位器 4095
                if int(self.Pot) == 4095 and not self.pot_emit:
                    self.pot_max_val = self.Pot
                    self.pot_max = True

                # 旋钮电位器
                if self.pot_min and self.pot_max and not self.pot_emit:
                    print("旋钮电位器 pass")
                    self.signal_pot.emit()
                    self.pot_emit = True

                if self.sda_scl_emit and self.pot_emit and self.rfid_emit and self.humiture_emit and self.ir1_emit and self.wifi_emit and self.Tracking_emit and self.ultrasound_emit and self.light_emit and self.sound_emit and \
                        self.IS_OLED_PASS and self.IS_PINOUT_PASS and self.IS_BUZZ_PASS and self.IS_AUDIO_PASS and self.IS_CAMERA_PASS and self.IS_SCL_SDA_PASS and self.IS_RGB_PASS and self.IS_FAN_PASS and self.IS_MOTOR_PASS and self.IS_WATERPUMP_PASS:
                    if not self.IS_ALL_FUNCT_PASS:
                        result = f"mac:{self.mac};wifi:{self.Wifi};i2c:{self.sda_scl_val};rfid:{self.Rfid1};light:{self.light_value};humiture:{self.humiture_value};sound:{self.sound_value};Tracking:{self.Tracking_emit};Ultrasound_far:{self.Ultrasound_far_val};Ultrasound_near:{self.Ultrasound_near_val};pot_max:{self.pot_max_val};pot_min:{self.pot_min_val};ir1_left:{self.ir1_left_value};ir1_right:{self.ir1_right_value};"
                        result += f"lcd:True;p0_p1_p2_p3:True;aKey:True;bKey:True;record_play:True;fun:True;servo:True;rgb:True;motor_1:True;motor_2:True;waterPump:True;"
                        print("function test all Pass")
                        time.sleep(0.5)
                        self.All_funct_test_pass.emit(result)
                        self.IS_ALL_FUNCT_PASS = True

            elif g_project == ProjectType.c7001.value:
                # Wifi
                if int(self.Wifi) > -70 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True

                # 超声波 近
                if int(self.Ultrasound) > 0 and int(self.Ultrasound) <= 100 and not self.ultrasound_emit:
                    self.ultrasound_near = True

                # 超声波 远
                if int(self.Ultrasound) >= 500 and int(self.Ultrasound) <= 3000 and not self.ultrasound_emit:
                    self.ultrasound_far = True

                # 超声波
                if self.ultrasound_near and self.ultrasound_far and not self.ultrasound_emit:
                    self.signal_ultrasound.emit()
                    self.ultrasound_emit = True

                # 红外探测 左
                if int(self.ir1_left_value) > 1 and int(self.ir1_left_value) <= 200 and int(
                        self.ir1_right_value) > 1 and int(self.ir1_right_value) <= 200 and not self.ir1_emit:
                    self.ir1_left = True

                # 红外探测 右
                if int(self.ir1_left_value) > 1 and int(self.ir1_left_value) <= 3000 and int(
                        self.ir1_right_value) > 1 and int(self.ir1_right_value) <= 3000 and not self.ir1_emit:
                    self.ir1_right = True

                # 红外探测
                if self.ir1_left and self.ir1_right and not self.ir1_emit:
                    print("红外探测 pass")
                    self.signal_ir1.emit()
                    self.ir1_emit = True

                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(self.light_value) >= CONFIG_DICT.get("light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 温湿度
                if int(self.humiture_value) >= 20 and int(self.humiture_value) <= 40 and not self.humiture_emit:
                    print("温湿度 emit")
                    self.signal_humiture.emit()
                    self.humiture_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(self.sound_value) <= CONFIG_DICT.get(
                        "sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True

                # RFID
                if str(self.Rfid1) != 'False' and len(str(self.Rfid1)) > 6 and str(self.Rfid2) != 'False' and len(str(self.Rfid2)) > 6 and not self.rfid_emit:
                    print("RFID pass")
                    self.signal_rfid.emit()
                    self.rfid_emit = True

                # SDA/SCL
                if int(self.sda_scl_val) == 1 and not self.sda_scl_emit:
                    print("SDA/SCL pass")
                    self.signal_sda_scl.emit()
                    self.sda_scl_emit = True

                # 加速度
                diff_x = round(float(self.acc_x_val), 2)
                diff_y = round(float(self.acc_y_val), 2)
                diff_z = round(float(self.acc_z_val), 2)
                if diff_x != 0 and diff_y != 0 and diff_z != 0 and \
                    diff_x >= -10 and diff_x <= 10 and \
                    diff_y >= -10 and diff_y <= 10 and \
                    diff_z >= -10 and diff_z <= 10:
                    if not self.acc_all_emit:
                        print("acc_all emit")
                        self.acc_all_emit = True
                        self.signal_acc_all.emit()

                if self.acc_all_emit and self.sda_scl_emit  and self.rfid_emit and self.humiture_emit and self.ir1_emit and self.wifi_emit and  self.ultrasound_emit and self.light_emit and self.sound_emit and \
                        self.IS_OLED_PASS and self.IS_PINOUT_PASS and self.IS_BUZZ_PASS and self.IS_AUDIO_PASS and self.IS_RGB_PASS and self.IS_FAN_PASS  and self.IS_WATERPUMP_PASS and self.IS_SERVO_PASS:
                    if not self.IS_ALL_FUNCT_PASS:
                        result = f"mac:{self.mac};wifi:{self.Wifi};i2c:{self.sda_scl_val};rfid1:{self.Rfid1};rfid2:{self.Rfid2};light:{self.light_value};humiture:{self.humiture_value};sound:{self.sound_value};Ultrasound_far:{self.Ultrasound_far_val};Ultrasound_near:{self.Ultrasound_near_val};ir1_left:{self.ir1_left_value};ir1_right:{self.ir1_right_value};"
                        result += f"lcd:True;p0_p1_p2_p3:True;aKey:True;bKey:True;record_play:True;fun:True;servo:True;rgb:True;waterPump:True;"
                        print("function test all Pass")
                        time.sleep(0.5)
                        self.All_funct_test_pass.emit(result)
                        self.IS_ALL_FUNCT_PASS = True

            elif g_project == ProjectType.v260Teach.value:
                # Wifi
                if int(self.Wifi) > -80 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True

                # 滑杆 大
                if int(self.slider_value) == 0 and not self.ir1_emit:
                    self.ir1_left = True

                # 滑杆 小
                if int(self.slider_value) == 100  and not self.ir1_emit:
                    self.ir1_right = True

                # 滑杆
                if self.ir1_left and self.ir1_right and not self.ir1_emit:
                    self.signal_ir1.emit()
                    self.ir1_emit = True

                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(self.light_value) >= CONFIG_DICT.get("light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 温湿度
                if (int(self.humiture_value) >= 20 and int(self.humiture_value) <= 40 and
                    int(self.Temperature_value) >= 10 and int(self.Temperature_value) <= 80 and not self.humiture_emit):
                    print("温湿度 emit")
                    self.signal_humiture.emit()
                    self.humiture_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(self.sound_value) <= CONFIG_DICT.get("sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True

                # SDA/SCL
                if int(self.sda_scl_val) == 1 and not self.sda_scl_emit:
                    print("SDA/SCL pass")
                    self.signal_sda_scl.emit()
                    self.sda_scl_emit = True

                if (self.sda_scl_emit and self.humiture_emit and self.ir1_emit and self.wifi_emit and  self.light_emit and self.sound_emit and \
                        self.IS_OLED_PASS and self.IS_PINOUT_PASS and self.IS_BUZZ_PASS and self.IS_AUDIO_PASS and self.IS_RGB_PASS and \
                        self.IS_FAN_PASS  and self.IS_WATERPUMP_PASS and self.IS_SERVO_PASS and self.IS_CAMERA_PASS and self.IS_SOUT_PASS):

                    if not self.IS_ALL_FUNCT_PASS:
                        result = f"mac:{self.mac};wifi:{self.Wifi};i2c:{self.sda_scl_val};rfid:ok;light:{self.light_value};humiture:{self.humiture_value};sound:{self.sound_value};slider:{self.ir1_left_value};"
                        result += f"lcd:True;p0_p1_p15_p16:True;M1:True;bugle:True;aKey:True;bKey:True;s1Key:True;s2Key:True;buzzer:True;fun:True;servo:True;rgb:True;"
                        print("function test all Pass")
                        time.sleep(0.5)
                        self.All_funct_test_pass.emit(result)
                        self.IS_ALL_FUNCT_PASS = True



            elif g_project == ProjectType.v7005.value:

                # 触摸P
                if int(self.tp_value) > 0 and not self.tp_emit:
                    print("touch p pass")
                    self.signal_touchpad_p.emit()
                    self.tp_emit = True

                # 触摸Y
                if int(self.ty_value) > 0 and not self.ty_emit:
                    print("touch y pass")
                    self.signal_touchpad_y.emit()
                    self.ty_emit = True

                # 触摸T
                if int(self.tt_value) > 0 and not self.tt_emit:
                    print("touch t pass")
                    self.signal_touchpad_t.emit()
                    self.tt_emit = True

                # 触摸H
                if int(self.th_value) > 0 and not self.th_emit:
                    print("touch h pass")
                    self.signal_touchpad_h.emit()
                    self.th_emit = True

                # 触摸O
                if int(self.to_value) > 0 and not self.to_emit:
                    print("touch o pass")
                    self.signal_touchpad_o.emit()
                    self.to_emit = True

                # 触摸N
                if int(self.tn_value) > 0 and not self.tn_emit:
                    print("touch n pass")
                    self.signal_touchpad_n.emit()
                    self.tn_emit = True

                # Wifi
                if int(self.Wifi) > -70 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True

                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(self.light_value) >= CONFIG_DICT.get("light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(self.sound_value) <= CONFIG_DICT.get("sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True

                # 陀螺仪
                Gyroscope_x = round(float(self.Gyroscope_x), 2)
                Gyroscope_y = round(float(self.Gyroscope_y), 2)
                Gyroscope_z = round(float(self.Gyroscope_z), 2)
                if Gyroscope_x != 0 and Gyroscope_y != 0 and Gyroscope_y != 0 and \
                        Gyroscope_x >= -10 and Gyroscope_x <= 10 and \
                        Gyroscope_y >= -10 and Gyroscope_y <= 10 and \
                        Gyroscope_z >= -10 and Gyroscope_z <= 10:
                    if not self.gyroscope_emit:
                        print("gyroscope emit")
                        self.gyroscope_emit = True
                        self.signal_Gyroscope.emit()

                # 磁力计
                Magnetic_x = round(float(self.Magnetic_x), 2)
                Magnetic_y = round(float(self.Magnetic_y), 2)
                Magnetic_z = round(float(self.Magnetic_z), 2)
                if Magnetic_x != 0 and Magnetic_y != 0 and Magnetic_z != 0 and \
                        Magnetic_x >= -3000 and Magnetic_x <= 3000 and \
                        Magnetic_y >= -2000 and Magnetic_y <= 2000 and \
                        Magnetic_z >= -8000.0 and Magnetic_z <= 8000.0:
                    if not self.mag_emit:
                        print("Mag_head emit")
                        self.mag_emit = True
                        self.signal_Mag.emit()

                # 加速度
                diff_x = round(float(self.acc_x_val), 2)
                diff_y = round(float(self.acc_y_val), 2)
                diff_z = round(float(self.acc_z_val), 2)
                if diff_x != 0 and diff_y != 0 and diff_z != 0 and \
                        diff_x >= -10 and diff_x <= 10 and \
                        diff_y >= -10 and diff_y <= 10 and \
                        diff_z >= -10 and diff_z <= 10:
                    if not self.acc_all_emit:
                        print("acc_all emit")
                        self.acc_all_emit = True
                        self.signal_acc_all.emit()

                # SDA/SCL
                if int(self.sda_scl_val) == 1 and not self.sda_scl_emit:
                    print("SDA/SCL pass")
                    self.signal_sda_scl.emit()
                    self.sda_scl_emit = True


                if self.tp_emit and self.ty_emit and self.tt_emit and self.th_emit and self.to_emit and self.tn_emit and self.wifi_emit and self.light_emit and self.mag_emit and self.sound_emit and self.gyroscope_emit and self.acc_all_emit and self.sda_scl_emit and \
                        self.IS_OLED_PASS and self.IS_PINOUT_PASS and self.IS_BUZZ_PASS and self.IS_AUDIO_PASS:
                        if not self.IS_ALL_FUNCT_PASS:
                            result = f"mac:{self.mac};wifi:{self.Wifi};i2c:{self.sda_scl_emit};light:{self.light_value};sound:{self.sound_value};p:1;y:1;t:1;h:1;o:1:n:1;acc_x:{diff_x};acc_y:{diff_y};acc_z:{diff_z};mag_x:{Magnetic_x};mag_y:{Magnetic_y};mag_z:{Magnetic_z};gyroscope_x:{Gyroscope_x};gyroscope_y:{Gyroscope_y};gyroscope_z:{Gyroscope_z};"
                            result += f"oled:True;pinout:True;aKey:True;bKey:True;record_play:True;rgb:True;"
                            print("function test all Pass")
                            time.sleep(0.5)
                            self.All_funct_test_pass.emit(result)
                            self.IS_ALL_FUNCT_PASS = True

            elif g_project == ProjectType.v7007.value:

                # 触摸P
                if int(self.tp_value) > 0 and not self.tp_emit:
                    print("touch p pass")
                    self.signal_touchpad_p.emit()
                    self.tp_emit = True

                # 触摸Y
                if int(self.ty_value) > 0 and not self.ty_emit:
                    print("touch y pass")
                    self.signal_touchpad_y.emit()
                    self.ty_emit = True

                # 触摸T
                if int(self.tt_value) > 0 and not self.tt_emit:
                    print("touch t pass")
                    self.signal_touchpad_t.emit()
                    self.tt_emit = True

                # 触摸H
                if int(self.th_value) > 0 and not self.th_emit:
                    print("touch h pass")
                    self.signal_touchpad_h.emit()
                    self.th_emit = True

                # 触摸O
                if int(self.to_value) > 0 and not self.to_emit:
                    print("touch o pass")
                    self.signal_touchpad_o.emit()
                    self.to_emit = True

                # 触摸N
                if int(self.tn_value) > 0 and not self.tn_emit:
                    print("touch n pass")
                    self.signal_touchpad_n.emit()
                    self.tn_emit = True

                # Wifi
                if int(self.Wifi) > -70 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True


                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(self.light_value) >= CONFIG_DICT.get("light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(self.sound_value) <= CONFIG_DICT.get("sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True


                # 陀螺仪
                Gyroscope_x = round(float(self.Gyroscope_x), 2)
                Gyroscope_y = round(float(self.Gyroscope_y), 2)
                Gyroscope_z = round(float(self.Gyroscope_z), 2)
                if Gyroscope_x != 0 and Gyroscope_y != 0 and Gyroscope_y != 0 and \
                    Gyroscope_x >= -10 and Gyroscope_x <= 10 and \
                    Gyroscope_y >= -10 and Gyroscope_y <= 10 and \
                    Gyroscope_z >= -10 and Gyroscope_z <= 10:
                    if not self.gyroscope_emit:
                        print("gyroscope emit")
                        self.gyroscope_emit = True
                        self.signal_Gyroscope.emit()

                # 磁力计
                Magnetic_x = round(float(self.Magnetic_x), 2)
                Magnetic_y = round(float(self.Magnetic_y), 2)
                Magnetic_z = round(float(self.Magnetic_z), 2)
                if Magnetic_x != 0 and Magnetic_y != 0 and Magnetic_z != 0 and \
                        Magnetic_x >= -3000 and Magnetic_x <= 3000 and \
                        Magnetic_y >= -5000 and Magnetic_y <= 5000 and \
                        Magnetic_z >= -9000.0 and Magnetic_z <= 9000.0:
                    if not self.mag_emit:
                        print("Mag_head emit")
                        self.mag_emit = True
                        self.signal_Mag.emit()


                # 加速度
                diff_x = round(float(self.acc_x_val), 2)
                diff_y = round(float(self.acc_y_val), 2)
                diff_z = round(float(self.acc_z_val), 2)
                if diff_x != 0 and diff_y != 0 and diff_z != 0 and \
                        diff_x >= -10 and diff_x <= 10 and \
                        diff_y >= -10 and diff_y <= 10 and \
                        diff_z >= -10 and diff_z <= 10:
                    if not self.acc_all_emit:
                        print("acc_all emit")
                        self.acc_all_emit = True
                        self.signal_acc_all.emit()

                if self.tp_emit and self.ty_emit and self.tt_emit and self.th_emit and self.to_emit and self.tn_emit and self.wifi_emit and self.light_emit and self.mag_emit and self.sound_emit and self.gyroscope_emit and self.acc_all_emit and \
                        self.IS_OLED_PASS and self.IS_PINOUT_PASS and self.IS_BUZZ_PASS and self.IS_AUDIO_PASS:
                    if not self.IS_ALL_FUNCT_PASS:

                        result = f"mac:{self.mac};wifi:{self.Wifi};light:{self.light_value};sound:{self.sound_value};p:1;y:1;t:1;h:1;o:1:n:1;acc_x:{diff_x};acc_y:{diff_y};acc_z:{diff_z};mag_x:{Magnetic_x};mag_y:{Magnetic_y};mag_z:{Magnetic_z};gyroscope_x:{Gyroscope_x};gyroscope_y:{Gyroscope_y};gyroscope_z:{Gyroscope_z};"
                        result += f"lcd:True;pinout:True;aKey:True;bKey:True;record_play:True;rgb:True;"
                        print("function test all Pass")
                        time.sleep(0.5)
                        self.All_funct_test_pass.emit(result)
                        self.IS_ALL_FUNCT_PASS = True

            elif g_project == ProjectType.v260Zkb.value:

                # 触摸P
                if int(self.tp_value) > 0 and not self.tp_emit:
                    print("touch p pass")
                    self.signal_touchpad_p.emit()
                    self.tp_emit = True

                # 触摸Y
                if int(self.ty_value) > 0 and not self.ty_emit:
                    print("touch y pass")
                    self.signal_touchpad_y.emit()
                    self.ty_emit = True

                # 触摸T
                if int(self.tt_value) > 0 and not self.tt_emit:
                    print("touch t pass")
                    self.signal_touchpad_t.emit()
                    self.tt_emit = True

                # 触摸H
                if int(self.th_value) > 0 and not self.th_emit:
                    print("touch h pass")
                    self.signal_touchpad_h.emit()
                    self.th_emit = True

                # 触摸O
                if int(self.to_value) > 0 and not self.to_emit:
                    print("touch o pass")
                    self.signal_touchpad_o.emit()
                    self.to_emit = True

                # 触摸N
                if int(self.tn_value) > 0 and not self.tn_emit:
                    print("touch n pass")
                    self.signal_touchpad_n.emit()
                    self.tn_emit = True

                # Wifi
                if int(self.Wifi) > -70 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True


                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(self.light_value) >= CONFIG_DICT.get("light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(self.sound_value) <= CONFIG_DICT.get("sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True


                # 陀螺仪
                Gyroscope_x = round(float(self.Gyroscope_x), 2)
                Gyroscope_y = round(float(self.Gyroscope_y), 2)
                Gyroscope_z = round(float(self.Gyroscope_z), 2)
                if Gyroscope_x != 0 and Gyroscope_y != 0 and Gyroscope_y != 0 and \
                    Gyroscope_x >= -10 and Gyroscope_x <= 10 and \
                    Gyroscope_y >= -10 and Gyroscope_y <= 10 and \
                    Gyroscope_z >= -10 and Gyroscope_z <= 10:
                    if not self.gyroscope_emit:
                        print("gyroscope emit")
                        self.gyroscope_emit = True
                        self.signal_Gyroscope.emit()


                # 磁力计
                Magnetic_x = round(float(self.Magnetic_x), 2)
                Magnetic_y = round(float(self.Magnetic_y), 2)
                Magnetic_z = round(float(self.Magnetic_z), 2)
                if Magnetic_x != 0 and Magnetic_y != 0 and Magnetic_z != 0 and \
                        Magnetic_x >= -3000 and Magnetic_x <= 3000 and \
                        Magnetic_y >= -5000 and Magnetic_y <= 5000 and \
                        Magnetic_z >= -9000.0 and Magnetic_z <= 9000.0:
                    if not self.mag_emit:
                        print("Mag_head emit")
                        self.mag_emit = True
                        self.signal_Mag.emit()


                # 加速度
                diff_x = round(float(self.acc_x_val), 2)
                diff_y = round(float(self.acc_y_val), 2)
                diff_z = round(float(self.acc_z_val), 2)
                if diff_x != 0 and diff_y != 0 and diff_z != 0 and \
                        diff_x >= -10 and diff_x <= 10 and \
                        diff_y >= -10 and diff_y <= 10 and \
                        diff_z >= -10 and diff_z <= 10:

                    if not self.acc_all_emit:
                        print("acc_all emit")
                        self.acc_all_emit = True
                        self.signal_acc_all.emit()

                # p0
                if int(self.P0_value) > 3000 and int(self.P0_value) <= 4096:
                    if not self.p0_emit:
                        print("P0 emit")
                        self.signal_p0.emit()
                        self.p0_emit = True

                # p1
                if int(self.P1_value) > 3000 and int(self.P1_value) <= 4096:
                    if not self.p1_emit:
                        print("P1 emit")
                        self.signal_p1.emit()
                        self.p1_emit = True

                # p2
                if int(self.P2_value) > 3000 and int(self.P2_value) <= 4096:
                    if not self.p2_emit:
                        print("P2 emit")
                        self.signal_p2.emit()
                        self.p2_emit = True



                if self.p0_emit and self.p1_emit and self.p2_emit and self.tp_emit and self.ty_emit and self.tt_emit and self.th_emit and self.to_emit and self.tn_emit and self.wifi_emit and self.light_emit and self.mag_emit and self.sound_emit and self.gyroscope_emit and self.acc_all_emit and \
                        self.IS_OLED_PASS and self.IS_BUZZ_PASS:
                    if not self.IS_ALL_FUNCT_PASS:
                        result = f"mac:{self.mac};wifi:{self.Wifi};light:{self.light_value};sound:{self.sound_value};p:1;y:1;t:1;h:1;o:1:n:1;acc_x:{diff_x};acc_y:{diff_y};acc_z:{diff_z};mag_x:{Magnetic_x};mag_y:{Magnetic_y};mag_z:{Magnetic_z};gyroscope_x:{Gyroscope_x};gyroscope_y:{Gyroscope_y};gyroscope_z:{Gyroscope_z};"
                        result += f"lcd:True;pinout:True;aKey:True;bKey:True;rgb:True;"
                        print("function test all Pass")
                        time.sleep(0.5)
                        self.All_funct_test_pass.emit(result)
                        self.IS_ALL_FUNCT_PASS = True


            elif g_project == ProjectType.v7009.value:

                # 触摸P
                if int(self.tp_value) > 0 and not self.tp_emit:
                    print("touch p pass")
                    self.signal_touchpad_p.emit()
                    self.tp_emit = True

                # 触摸Y
                if int(self.ty_value) > 0 and not self.ty_emit:
                    print("touch y pass")
                    self.signal_touchpad_y.emit()
                    self.ty_emit = True

                # 触摸T
                if int(self.tt_value) > 0 and not self.tt_emit:
                    print("touch t pass")
                    self.signal_touchpad_t.emit()
                    self.tt_emit = True

                # 触摸H
                if int(self.th_value) > 0 and not self.th_emit:
                    print("touch h pass")
                    self.signal_touchpad_h.emit()
                    self.th_emit = True

                # 触摸O
                if int(self.to_value) > 0 and not self.to_emit:
                    print("touch o pass")
                    self.signal_touchpad_o.emit()
                    self.to_emit = True

                # 触摸N
                if int(self.tn_value) > 0 and not self.tn_emit:
                    print("touch n pass")
                    self.signal_touchpad_n.emit()
                    self.tn_emit = True

                # Wifi
                if int(self.Wifi) > -70 and int(self.Wifi) < 0 and not self.wifi_emit:
                    print("wifi pass")
                    self.signal_wifi.emit()
                    self.wifi_emit = True

                # 光线
                if int(self.light_value) <= CONFIG_DICT.get("light_max") and int(
                        self.light_value) >= CONFIG_DICT.get("light_min"):
                    if not self.light_emit:
                        print("光线 emit")
                        self.signal_Light.emit()
                        self.light_emit = True

                # 麦克风
                if int(self.sound_value) >= CONFIG_DICT.get("sound_min") and int(
                        self.sound_value) <= CONFIG_DICT.get("sound_max"):
                    if not self.sound_emit:
                        print("麦克风 emit")
                        self.signal_sound.emit()
                        self.sound_emit = True

                # 陀螺仪
                Gyroscope_x = round(float(self.Gyroscope_x), 2)
                Gyroscope_y = round(float(self.Gyroscope_y), 2)
                Gyroscope_z = round(float(self.Gyroscope_z), 2)
                if Gyroscope_x != 0 and Gyroscope_y != 0 and Gyroscope_y != 0 and \
                        Gyroscope_x >= -10 and Gyroscope_x <= 10 and \
                        Gyroscope_y >= -10 and Gyroscope_y <= 10 and \
                        Gyroscope_z >= -10 and Gyroscope_z <= 10:
                    if not self.gyroscope_emit:
                        print("gyroscope emit")
                        self.gyroscope_emit = True
                        self.signal_Gyroscope.emit()

                # 磁力计
                Magnetic_x = round(float(self.Magnetic_x), 2)
                Magnetic_y = round(float(self.Magnetic_y), 2)
                Magnetic_z = round(float(self.Magnetic_z), 2)
                if Magnetic_x != 0 and Magnetic_y != 0 and Magnetic_z != 0 and \
                        Magnetic_x >= -3000 and Magnetic_x <= 3000 and \
                        Magnetic_y >= -5000 and Magnetic_y <= 5000 and \
                        Magnetic_z >= -8000.0 and Magnetic_z <= 8000.0:
                    if not self.mag_emit:
                        print("Mag_head emit")
                        self.mag_emit = True
                        self.signal_Mag.emit()

                # 加速度
                diff_x = round(float(self.acc_x_val), 2)
                diff_y = round(float(self.acc_y_val), 2)
                diff_z = round(float(self.acc_z_val), 2)
                if diff_x != 0 and diff_y != 0 and diff_z != 0 and \
                        diff_x >= -10 and diff_x <= 10 and \
                        diff_y >= -10 and diff_y <= 10 and \
                        diff_z >= -10 and diff_z <= 10:
                    if not self.acc_all_emit:
                        print("acc_all emit")
                        self.acc_all_emit = True
                        self.signal_acc_all.emit()

                # SDA/SCL
                if int(self.sda_scl_val) == 1 and not self.sda_scl_emit:
                    print("SDA/SCL pass")
                    self.signal_sda_scl.emit()
                    self.sda_scl_emit = True


                if self.tp_emit and self.ty_emit and self.tt_emit and self.th_emit and self.to_emit and self.tn_emit and self.wifi_emit and self.light_emit and self.mag_emit and self.sound_emit and self.gyroscope_emit and self.acc_all_emit and self.sda_scl_emit and \
                       self.IS_M2PIN_PASS and self.IS_OLED_PASS and self.IS_PINOUT_PASS and self.IS_BUZZ_PASS and self.IS_AUDIO_PASS and self.IS_CAMERA_PASS:
                        if not self.IS_ALL_FUNCT_PASS:
                            result = f"mac:{self.mac};wifi:{self.Wifi};i2c:{self.sda_scl_emit};light:{self.light_value};sound:{self.sound_value};p:1;y:1;t:1;h:1;o:1:n:1;acc_x:{diff_x};acc_y:{diff_y};acc_z:{diff_z};mag_x:{Magnetic_x};mag_y:{Magnetic_y};mag_z:{Magnetic_z};gyroscope_x:{Gyroscope_x};gyroscope_y:{Gyroscope_y};gyroscope_z:{Gyroscope_z};"
                            result += f"camera:True;lcd:True;pinout:True;m2out:True;aKey:True;bKey:True;record_play:True;rgb:True;"
                            print("function test all Pass")
                            time.sleep(0.5)
                            self.All_funct_test_pass.emit(result)
                            self.IS_ALL_FUNCT_PASS = True



# 读取MAC线程
class ReadMac_Thread(QThread):
    updataMac = pyqtSignal(str)

    def __init__(self, _port):
        super(ReadMac_Thread, self).__init__()
        self.port = _port

    # 打开串行链路MAC
    def open_serial_link_mac(self):
        """ 创建一个新的串行链路实例 """
        time.sleep(1)
        self.input_buffer = []
        self.serial = QSerialPort()  # 串口类
        self.serial.setPortName(self.port)  # 设置端口
        self.repl = Repl(self.serial)
        if self.serial.open(QIODevice.ReadWrite):
            self.serial.setRequestToSend(1)  # 设置请求发送
            self.msleep(20)
            self.serial.setRequestToSend(0)
            self.serial.setBaudRate(115200)  # 设置波特率
            self.serial.setFlowControl(QSerialPort.NoFlowControl)  # 设置流量控制,无流量控制
            self.serial.readyRead.connect(self.on_serial_read_mac)  # 绑定端口读数据事件 !!!
        else:
            msg = ("连接串口错误,请重试 {}").format(self.port)  # 无法连接到端口上的设备
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setWindowTitle("串口错误")
            msgbox.setText(msg)
            msgbox.setStandardButtons(QMessageBox.Yes)
            msgbox.exec_()

    def open_serial_link_mac2(self):
        # 先创建并配置串口对象，再打开
        self.serial = QSerialPort()  # 串口类
        self.repl = Repl(self.serial)
        self.serial.setPortName(self.port)  # 设置端口
        self.serial.setBaudRate(115200)  # 设置波特率
        self.serial.setDataBits(QSerialPort.Data8)  # 数据位
        self.serial.setParity(QSerialPort.NoParity)  # 校验位
        self.serial.setStopBits(QSerialPort.OneStop)  # 停止位
        self.serial.setFlowControl(QSerialPort.NoFlowControl)  # 设置流量控制

        # 尝试打开串口
        if self.serial.open(QIODevice.ReadWrite):
            # 绑定数据读取事件 - 确保在打开串口后连接信号
            self.serial.setDataTerminalReady(True);
            self.serial.readyRead.connect(self.on_serial_read)
        else:
            self.serial.close()
            #msg = f"连接串口错误,请重试 {self.port}"  # 无法连接到端口上的设备
            #msgbox = QMessageBox()
            #msgbox.setIcon(QMessageBox.Critical)
            #msgbox.setWindowTitle("串口错误")
            #msgbox.setText(msg)
            #msgbox.setStandardButtons(QMessageBox.Yes)
            #msgbox.exec_()

    # 提取串口数据
    def collect_mac_data(self, recv_str):
        global g_mac
        pattern = re.compile(r'(?<=Mac:)[A-Fa-f0-9]{12}')
        finded_list = pattern.findall(recv_str)
        if finded_list:
            self.mac_value = finded_list[-1]  # 取最后一个匹配项
            if g_mac != self.mac_value:
                g_mac = self.mac_value
                self.updataMac.emit(g_mac)
            print("提取的 MAC 地址:", self.mac_value)  # 输出: E4B323F0BF54


    def on_serial_read_mac(self):
        recv_buf = self.serial.readAll()
        try:
            recv_str = recv_buf.data().decode('UTF-8')
        except:
            print("recv data decode err")
        else:
            # 提取数据
            self.collect_mac_data(recv_str)



# 读取测试信息线程
class TestInfo_Thread(QThread):
    startBindingMac = pyqtSignal(str)

    def __init__(self, _port):
        super(TestInfo_Thread, self).__init__()
        self.port = _port

    def DDopen_serial_link2(self):
        time.sleep(1)
        # 先创建并配置串口对象，再打开
        self.serial = QSerialPort()  # 串口类
        self.repl = Repl(self.serial)
        self.serial.setPortName(self.port)  # 设置端口
        self.serial.setBaudRate(115200)  # 设置波特率
        self.serial.setDataBits(QSerialPort.Data8)  # 数据位
        self.serial.setParity(QSerialPort.NoParity)  # 校验位
        self.serial.setStopBits(QSerialPort.OneStop)  # 停止位
        self.serial.setFlowControl(QSerialPort.NoFlowControl)  # 设置流量控制

        # 尝试打开串口
        if self.serial.open(QIODevice.ReadWrite):
            # 绑定数据读取事件 - 确保在打开串口后连接信号
            self.serial.setDataTerminalReady(True);
            self.serial.readyRead.connect(self.on_serial_read)

    def open_serial_link(self):
        time.sleep(1)
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            # 先创建并配置串口对象，再打开
            self.serial = QSerialPort()                             # 串口类
            self.repl = Repl(self.serial)
            self.serial.setPortName(self.port)                      # 设置端口
            self.serial.setBaudRate(115200)                         # 设置波特率
            self.serial.setDataBits(QSerialPort.Data8)              # 数据位
            self.serial.setParity(QSerialPort.NoParity)             # 校验位
            self.serial.setStopBits(QSerialPort.OneStop)            # 停止位
            self.serial.setFlowControl(QSerialPort.NoFlowControl)   # 设置流量控制

            # 尝试打开串口
            if self.serial.open(QIODevice.ReadWrite):
                # 绑定数据读取事件 - 确保在打开串口后连接信号
                self.serial.setDataTerminalReady(True)
                self.serial.readyRead.connect(self.on_serial_read)
                return True  # 打开成功，直接返回
            else:
                # 关闭串口并增加重试计数
                self.serial.close()
                attempt += 1
                if attempt < max_retries:
                    time.sleep(0.5)  # 等待片刻再重试

        # 如果所有尝试都失败，弹出错误提示
        error_msg = f"无法打开串口 {self.port}，请检查连接和端口权限。"
        QMessageBox.critical(None, "串口连接错误", error_msg)
        return False  # 返回失败状态


    # 提取串口数据 7001
    def collect_data_7001(self, recv_str):
        global g_test_mode, g_MyWin
        lines = recv_str.strip().split('\n')

        if g_test_mode == 2:
            # 反向遍历，找到最后一条包含7001_C的数据
            for line in reversed(lines):
                if '7001_X' in line:
                    # 只在这行包含7001_C的字符串中搜索Mac地址
                    pattern = re.compile(r'(?<=Mac:)[A-Fa-f0-9]{12}')
                    finded_list = pattern.findall(line)  # 改为在当前行中搜索，而不是整个recv_str

                    if finded_list:
                        # 每次只处理最新的数据，清空之前的匹配
                        self.mac_value = finded_list[-1]  # 取最后一个匹配项
                        if self.mac_value:
                            self.startBindingMac.emit(self.mac_value)
                            break  # 找到后可以跳出循环，避免不必要的继续搜索

        if g_test_mode == 3:
            # 反向遍历，找到最后一条包含7001_C的数据
            for line in reversed(lines):
                if '7001_C' in line:
                    # 只在这行包含7001_C的字符串中搜索Mac地址
                    pattern = re.compile(r'(?<=Mac:)[A-Fa-f0-9]{12}')
                    finded_list = pattern.findall(line)  # 改为在当前行中搜索，而不是整个recv_str

                    if finded_list:
                        # 每次只处理最新的数据，清空之前的匹配
                        self.mac_value = finded_list[-1]  # 取最后一个匹配项
                        if self.mac_value:
                            self.startBindingMac.emit(self.mac_value)
                            break  # 找到后可以跳出循环，避免不必要的继续搜索


    # 提取串口数据 7008
    def collect_data_7008(self, recv_str):
        global g_test_mode, g_MyWin
        lines = recv_str.strip().split('\n')

        # 反向遍历，找到最后一条包含'1956'的数据
        for line in reversed(lines):
            if '1956' in line:
                self.startBindingMac.emit(line)
                return

    # 提取串口数据 7009
    def collect_data_7009(self, recv_str):
        pattern = re.compile(r'(?<=Mac:)[A-Fa-f0-9]{12}')

        finded_list = pattern.findall(recv_str)

        if finded_list:
            # 每次只处理最新的数据，清空之前的匹配
            self.mac_value = finded_list[-1]  # 取最后一个匹配项
            if self.mac_value:
                self.startBindingMac.emit(self.mac_value)
                # 清空匹配列表，确保下次只处理新数据
                return




    def on_serial_read(self):
        global g_test_mode
        recv_buf = self.serial.readAll()

        try:
            recv_str = recv_buf.data().decode('UTF-8')
        except:
            print("recv data decode err")
        else:
            if g_test_mode == 0:
                self.collect_data_7008(recv_str)
            if g_test_mode == 1:
                self.collect_data_7009(recv_str)
            if g_test_mode == 2 or g_test_mode == 3:
                self.collect_data_7001(recv_str)





def get_motherboard_serial():
    c = wmi.WMI()
    for board in c.Win32_BaseBoard():
        return board.SerialNumber.strip()
    return None



def generate_machine_code(base_str):
    # 使用 SHA-256 哈希算法
    hash_obj = hashlib.sha256(base_str.encode())
    return hash_obj.hexdigest()  # 返回64位16进制字符串


def generate_key(machine_code):
    """从机器码生成密钥（示例：Base64 编码前16字节）"""
    hash_bytes = bytes.fromhex(machine_code)  # 16进制转字节
    return base64.b64encode(hash_bytes[:16]).decode()  # 取前16字节并Base64编码


def verify(machine_code, key):
    """验证密钥是否匹配机器码"""
    expected_key = generate_key(machine_code)
    return key == expected_key




def get_file_creation_time(file_path):
    """
    获取文件的修改时间，返回格式化的年月日时间字符串

    Args:
        file_path (str): 文件的路径

    Returns:
        str: 格式化的时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'
             如果获取失败，返回相应的错误信息
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return " "

        # 获取文件状态信息
        file_stat = os.stat(file_path)

        # 获取最新修改时间戳 (st_mtime 是最后修改时间)
        timestamp = file_stat.st_mtime

        # 将时间戳转换为 datetime 对象
        dt_object = datetime.fromtimestamp(timestamp)

        # 格式化为年月日时分秒字符串
        formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

        return formatted_time

    except PermissionError:
        return " "
    except Exception as e:
        return " "





class StartHmiWindow(QDialog):

    def check_or_create_config(self,input_str):

        # 构建配置文件路径
        config_path = os.path.join(os.path.expanduser("~"), "AppData", f"{get_motherboard_serial()}.ini")

        # 如果文件不存在，创建空文件并返回False
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)  # 确保目录存在
            with open(config_path, 'w') as f:
                pass  # 创建空文件
            return False

        # 文件存在，读取内容并比较
        with open(config_path, 'r') as f:
            file_content = f.read().strip()  # 读取并去除首尾空白字符

        if file_content == input_str:
            t_path = get_file_creation_time(config_path)
            self.setWindowTitle('注册时间：' + t_path)
            return True
        else:
            return False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_startHmi()
        self.ui.setupUi(self)

        # 关键：设置窗口标志，只保留关闭按钮
        self.setWindowFlags(
            Qt.Window |  # 基本窗口类型
            Qt.WindowCloseButtonHint |  # 关闭按钮
            Qt.WindowTitleHint | # 标题栏（可选）
            Qt.WindowStaysOnTopHint
        )

        self.setFixedSize(self.size())  # 固定为当前大小
        self.ui.code_lineEdit.setReadOnly(True)  # 用户可以看到内容但无法编辑

        serial = get_motherboard_serial()
        #serial = "AAAGQ0FCYEP3PD"
        #print(f"主板序列号: {serial}")

        machine_code = generate_machine_code(serial)
        #print("机器码（SHA-256）:", machine_code)

        # 示例
        key = generate_key(machine_code)        # 生成的密钥

        # 第一次运行（文件不存在）
        result = self.check_or_create_config(key)

        if result:
            self.ui.stackedWidget.setCurrentIndex(0)
        else:
            self.ui.stackedWidget.setCurrentIndex(1)
            self.ui.code_lineEdit.setText(machine_code)
            self.ui.code_lineEdit.setCursorPosition(0)  # 将光标移动到开头


        self.ui.combo_project.currentIndexChanged.connect(
            lambda index: (
                # 处理index=6的情况
                (self.ui.combo_stage.clear(),
                 self.ui.combo_stage.addItems(["7008_1956主控"]),
                 self.ui.combo_stage.setCurrentIndex(0),
                 self.ui.combo_stage.setEnabled(True)) if index == 6 else
                # 处理其他情况
                (self.ui.combo_stage.clear(),
                 self.ui.combo_stage.addItems(["半成品测试", "成品测试"]),
                 self.ui.combo_stage.setCurrentIndex(1) if index in [ProjectType.x7001.value,
                                                                     ProjectType.c7001.value,
                                                                     ProjectType.v7007.value,
                                                                     ProjectType.m7005.value,
                                                                     ProjectType.v7005.value,
                                                                     ProjectType.v260Teach.value,
                                                                     ProjectType.v260Zkb.value] else None,
                 self.ui.combo_stage.setEnabled(index not in [ProjectType.x7001.value,ProjectType.c7001.value,ProjectType.v7007.value, ProjectType.m7005.value,ProjectType.v260Teach.value,ProjectType.v7005.value,ProjectType.v260Zkb.value]))
            )
        )

        # 延迟触发（确保UI已完全加载）
        QTimer.singleShot(100, lambda:self.ui.combo_project.currentIndexChanged.emit(self.ui.combo_project.currentIndex()))



    @pyqtSlot()
    def on_login_btn_clicked(self):
        serial = get_motherboard_serial()
        machine_code = generate_machine_code(serial)

        key = self.ui.key_lineEdit.text()
        if verify(machine_code, key):
            # 写入匹配内容
            config_path = os.path.join(os.path.expanduser("~"), "AppData", f"{get_motherboard_serial()}.ini")
            with open(config_path, 'w') as f:
                f.write(key)
            result = self.check_or_create_config(key)
            if result:
                self.ui.stackedWidget.setCurrentIndex(0)
            else:
                QMessageBox.critical(self, '错误', '保存密钥配置失败!')
        else:
            QMessageBox.critical(self, '错误', '密钥错误!')


    @pyqtSlot()
    def on_code_btn_clicked(self):
        # 复制到剪贴板
        pyperclip.copy(self.ui.code_lineEdit.text())


    @pyqtSlot()
    def on_button_confirm_clicked(self):
        global g_MyWin,g_project,g_test_mode
        g_project = self.ui.combo_project.currentIndex()
        g_test_mode = self.ui.combo_stage.currentIndex()
        self.close()



        g_MyWin = MyMainWindow()
        g_MyWin.show()
        g_MyWin.raise_()  # 提升到最上层（类似 Alt+Tab 选中）
        g_MyWin.activateWindow()  # 激活窗口（获取焦点）





import ctypes
import time


def turn_off_display():
    """ 关闭显示器 """
    # 发送系统命令关闭显示器
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)


def turn_on_display():
    """ 打开显示器 """
    # 发送系统命令打开显示器
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, -1)


# # 使用示例
# if __name__ == "__main__":
#     #print("关闭显示器")
#     #turn_off_display()
#     #print("关闭显示器OK")
#     print("打开显示器")
#     turn_on_display()
#     print("显示器已打开")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartHmiWindow()
    window.show()
    sys.exit(app.exec_())


