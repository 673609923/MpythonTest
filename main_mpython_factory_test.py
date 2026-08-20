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
from typing import Any, Callable, Dict, Optional, Tuple,List
import configparser
import secrets
from typing import Tuple, Dict
import platform
import datetime
from typing import Union
import random


# 全局互斥锁，所有数据库操作共用这一把锁
DB_LOCK = threading.Lock()

class ProjectType(Enum):
    v260Zkb   = (0, 7)
    x7001     = (1, 0)
    c7001     = (2, 1)
    v260Teach = (3, 6)
    v7005     = (4, 2)
    m7005     = (5, 3)
    v7007     = (6, 4)
    v7009     = (7, 5)
    v7010     = (8, -2)
    v7011     = (9, -3)
    d7011     = (10, -4)
    sn_mac    = (11, -1)

    @property
    def val1(self):
        return self.value[0]

    @property
    def val2(self):
        return self.value[1]

# 自定义静态方法，输入数字val1，返回枚举对象
    @staticmethod
    def from_val1(num):
        for member in ProjectType:
            if member.val1 == num:
                return member
        raise 0



CONFIG_DICT = dict()
IS_READED_MAC = False
g_test_mode = 0
g_project = 0
g_projectMutation = False
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
        """使用Windows API强制切换
        英文输入法"""
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
            if (snlen == 20 and g_project == ProjectType.c7001.val2 or g_project == ProjectType.x7001.val2) or\
                (snlen >= 18 and snlen <= 22 and g_project == ProjectType.v7009.val2):
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


def initialize_db_connection():
    """初始化并返回数据库连接（带失败状态缓存）"""
    global g_db_connection, g_connection_failed, g_MyWin

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

        if g_db_connection:
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接成功!", "green"))
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接成功!", "green"))
        else:
            QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接失败", "red"))
            QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接失败!", "red"))
        return g_db_connection

    except pymysql.MySQLError as e:
        QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接失败", "red"))
        QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接失败", "red"))
        return None
    except Exception as e:
        QTimer.singleShot(0, lambda: g_MyWin.LogShow("MES连接失败", "red"))
        QTimer.singleShot(0, lambda: g_MyWin.LogShowSnMac("MES连接失败", "red"))
        return None


class MyMainWindow(QMainWindow, Ui_MainWindow):
    refresh_port = pyqtSignal()

    class DbWorker(QThread):
        sig_log_show = pyqtSignal(str, str)

        def run(self):
            while True:
                try:
                    initialize_db_connection()
                except Exception as e:
                    print("重连失败")
                QThread.msleep(1000)


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
        if g_project != ProjectType.sn_mac.val2:
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
        if g_project == ProjectType.sn_mac.val2:
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







    def closeEvent(self, event):
        """窗口关闭，退出子线程，防止内存泄露"""
        if hasattr(self, "db_worker") and self.db_worker.isRunning():
            self.db_worker.terminate()
            self.db_worker.wait()
        super().closeEvent(event)


    def binding_mac_sn_code_info(self,mac,sn,code ,info):
        global g_db_connection,g_MesTableName

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            return False,"MES未连接,上传数据失败"

        try:

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

                return True,f"MAC:{mac}\nSN:{sn}\nCODE:{code} 绑定上传成功"

        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            return False,"上传MES数据失败"
        except Exception as e:
            if connection:
                connection.rollback()
            return False,"上传MES数据失败"



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
            if (g_test_mode == 1 and g_project == ProjectType.x7001.val2 or g_project == ProjectType.c7001.val2) or\
                g_test_mode == 2 and g_project == ProjectType.v7009.val2:
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

        global g_test_mode,g_project,g_projectMutation,g_MesTableName

        t_isConnectMes = True
        if g_project == ProjectType.v7011.val2:
            if g_test_mode == 0:
                __NAME__ = "< 7011-讯飞 X-CARD 1拖动4 主控测试 >    "
                g_MesTableName = "7011_x_card_final"
                self.TabWidget.removeTab(4)
                self.TabWidget.removeTab(3)
                self.TabWidget.removeTab(2)
                self.TabWidget.removeTab(0)
            else:
                __NAME__ = "< 7011-讯飞 X-CARD 主控成品测试 >    "
                g_MesTableName = "7011_x_card_final"
                self.TabWidget.removeTab(4)
                self.TabWidget.removeTab(3)
                self.TabWidget.removeTab(2)
                self.TabWidget.removeTab(0)


        elif g_project == ProjectType.d7011.val2:
            __NAME__ = "< 7011-讯飞 X-CARD 底座测试 >    "
            g_MesTableName = ""
            self.TabWidget.removeTab(4)
            self.TabWidget.removeTab(3)
            self.TabWidget.removeTab(1)
            self.TabWidget.removeTab(0)
            self.resize(600, 720)
            t_isConnectMes = False
        else:
            self.TabWidget.removeTab(2)
            self.TabWidget.removeTab(1)
            self.TabWidget.setCurrentIndex(0)
            self.resize(940, 735)

            if g_project == ProjectType.x7001.val2:
                __NAME__ = "< 7001-讯飞实验箱-小学版 >    "
                g_MesTableName = "7001_xiaoxue_final"

            elif g_project == ProjectType.c7001.val2:
                __NAME__ = "< 7001-讯飞实验箱-初中版 >    "
                g_MesTableName = "7001_chuzhong_final"

            elif g_project == ProjectType.v260Teach.val2:
                __NAME__ = "< TS260-信息科技示教版 >    "
                g_MesTableName = "v260Teach_blank"

            elif g_project == ProjectType.v260Zkb.val2:
                __NAME__ = "< TS260-掌控板 >    "
                g_MesTableName = "v260Zkb_blank"

            elif g_project == ProjectType.v7005.val2:
                __NAME__ = "< 7005-掌控板-学境 >    "
                if g_test_mode == 0:
                    g_MesTableName = "7005_blank"
                elif g_test_mode == 1:
                    g_MesTableName = "7005_final"

            elif g_project == ProjectType.v7010.val2:
                __NAME__ = "< 7010-掌控板-学境2.0 >    "
                if g_test_mode == 0:
                    g_MesTableName = "7005_blank"
                elif g_test_mode == 1:
                    g_MesTableName = "7005_final"
                g_project = ProjectType.v7005.val2
                g_projectMutation = True

            elif g_project == ProjectType.m7005.val2:
                __NAME__ = "< 7005-模块-学境 >    "

            elif g_project == ProjectType.v7007.val2:
                __NAME__ = "< 7007-掌控板-单板 >    "
                g_MesTableName = "7007_final"

            elif g_project == ProjectType.v7009.val2:
                __NAME__ = "< 7009-乐动掌控2.0 >    "
                if g_test_mode == 0:
                    g_MesTableName = "7009_blank"
                elif g_test_mode == 1 or g_test_mode == 2:
                    g_MesTableName = "7009_final"

            elif g_project == ProjectType.sn_mac.val2:
                # 移除前两个页面
                self.TabWidget.removeTab(2)  # 先移除第二个（索引1）
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

        if g_project != ProjectType.sn_mac.val2:
            if g_project == ProjectType.v7009.val2:
                if g_test_mode == 0:
                    __MODEL__ = "(半成品测试)"
                elif g_test_mode == 1:
                    __MODEL__ = "(盛思_成品测试)"
                elif g_test_mode == 2:
                    __MODEL__ = "(讯飞_成品测试)"
            else:
                if g_test_mode == 0:
                    __MODEL__ = "(半成品测试)"
                elif g_test_mode == 1:
                    __MODEL__ = "(成品测试)"
        else:
            __MODEL__ = ""

        self.stackedWidget.setCurrentIndex(g_project)

        if g_project != ProjectType.sn_mac.val2:
            self.TabWidget.removeTab(2)

        if t_isConnectMes:
            if g_project == ProjectType.v7011.val2 or g_project == ProjectType.d7011.val2:
                self.db_worker = self.DbWorker()
                self.db_worker.start()
            else:
                self.timer = QTimer(self)
                self.timer.timeout.connect(initialize_db_connection)
                self.timer.start(1000)



        # 注册 F6 快捷键
        keyboard.add_hotkey('shift', self.CopyMacInfo)


        self.old_pageNum_1 = 0
        self.old_testNum_1 = ""
        self.old_text_1 = ""

        self.old_pageNum_2 = 0
        self.old_testNum_2 = ""
        self.old_text_2 = ""

        self.old_pageNum_3 = 0
        self.old_testNum_3 = ""
        self.old_text_3 = ""

        self.old_pageNum_4 = 0
        self.old_testNum_4 = ""
        self.old_text_4 = ""

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

        if g_project == ProjectType.m7005.val2:
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

        if g_project == ProjectType.v7011.val2:

            if g_test_mode == 0:
                self.ui_stackedWidget_work_1.setCurrentIndex(2)
                self.ui_stackedWidget_work_2.setCurrentIndex(2)
                self.ui_stackedWidget_work_3.setCurrentIndex(2)
                self.ui_stackedWidget_work_4.setCurrentIndex(2)

                # 刷新串口 槽函数
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.pairing_com)
                self.timer.start(100)

                self.test_func_thread = OneToFourTest_Thread(1)  # 功能测试线程
                self.test_func_thread.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread.start()

                self.test_func_thread2 = OneToFourTest_Thread(2)  # 功能测试线程
                self.test_func_thread2.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread2.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread2.start()

                self.test_func_thread3 = OneToFourTest_Thread(3)  # 功能测试线程
                self.test_func_thread3.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread3.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread3.start()

                self.test_func_thread4 = OneToFourTest_Thread(4)  # 功能测试线程
                self.test_func_thread4.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread4.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread4.start()
            else:

                self.ui_stackedWidget_work_1.setCurrentIndex(2)
                self.ui_stackedWidget_work_2.setCurrentIndex(2)
                self.ui_stackedWidget_work_3.setCurrentIndex(2)
                self.ui_stackedWidget_work_4.setCurrentIndex(2)

                # 刷新串口 槽函数
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.pairing_com)
                self.timer.start(100)

                self.test_func_thread = FinalTest_Thread(1)  # 功能测试线程
                self.test_func_thread.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread.start()

                self.test_func_thread2 = FinalTest_Thread(2)  # 功能测试线程
                self.test_func_thread2.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread2.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread2.start()

                self.test_func_thread3 = FinalTest_Thread(3)  # 功能测试线程
                self.test_func_thread3.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread3.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread3.start()

                self.test_func_thread4 = FinalTest_Thread(4)  # 功能测试线程
                self.test_func_thread4.signal_get_work_com.connect(self.get_Lord_work_from_ui)
                self.test_func_thread4.signal_set_ui_page.connect(self.set_Lord_ui_page)
                self.test_func_thread4.start()

        elif g_project == ProjectType.d7011.val2:

            self.ui_stackedWidget_bot.setCurrentIndex(2)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.pairing_bot_com)
            self.timer.start(100)
            self.test_func_thread = BaseTest_Thread(g_test_mode)  # 功能测试线程
            self.test_func_thread.signal_get_work_com.connect(self.get_Base_work_from_ui)
            self.test_func_thread.signal_set_ui_page.connect(self.set_Base_ui_page)
            self.test_func_thread.start()
        else:
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

        self.setWindowTitle(__NAME__ + __MODEL__ + "     < 版本：4.0 >")


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
            #QMessageBox.critical(self, '错误', '加载配置文件错误!\n{}'.format(e))
            return

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
                #QTimer.singleShot(0, lambda: g_MyWin.LogShow(manufacturer, "red"))
                if manufacturer in ["Silicon Labs", "wch.cn","Microsoft","(Undefined Vendor)"]:
                    manufacturer_type = 0 if manufacturer == "Silicon Labs" else 1
                    port_name = port.portName()
                    self.com_list.update({port_name: manufacturer_type})
            com_list = list(self.com_list.keys())
            com_list.sort(reverse=True)
            for port in com_list:
                self.serial_func_comboBox.addItem(port)
            print(self.com_list)


    def pairing_com(self):
        # 仅在串口检测功能开启时运行
        if not self.is_func_serial_opened:
            return

        # 收集当前可用的端口（并保留 manufacturer 类型）
        self.com_list = {}
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            manufacturer = port.manufacturer()
            if manufacturer in ["Silicon Labs", "wch.cn", "Microsoft", "(Undefined Vendor)"]:
                manufacturer_type = 0 if manufacturer == "Silicon Labs" else 1
                self.com_list[port.portName()] = manufacturer_type

        # 按端口名尾部的数字升序排序（如 COM3 < COM10）；无数字的排在后面
        def _port_sort_key(name):
            m = re.search(r'(\d+)$', name)
            if m:
                return (0, int(m.group(1)), name)  # 有数字的按数字排序，数字相同再按名字
            return (1, name)  # 无数字的放到最后，按名字排序

        available_ports = sorted(self.com_list.keys(), key=_port_sort_key)

        # 四个 lineEdit 的引用（按你 UI 的顺序）
        line_edits = [
            self.ui_lineEdit_work_1,
            self.ui_lineEdit_work_2,
            self.ui_lineEdit_work_3,
            self.ui_lineEdit_work_4,
        ]

        # 1) 清除那些已绑定但当前不可用的 port（设备拔掉时只清除对应的 lineEdit）
        assigned_ports = set()
        for le in line_edits:
            text = le.text().strip()
            if text:
                if text not in available_ports:
                    le.clear()
                else:
                    assigned_ports.add(text)

        # 2) 将尚未分配的可用端口依次填入第一个空的 lineEdit（不重复分配）
        for port in available_ports:
            if port in assigned_ports:
                continue
            # 找到第一个空的 lineEdit 来填充
            for le in line_edits:
                if not le.text().strip():
                    le.setText(port)
                    assigned_ports.add(port)
                    break
            # 如果没有空 slot（4 个都被占用），则跳过该 port

        # 调试输出（保留）
        #print(self.com_list)

    def pairing_bot_com(self):
        # 仅在串口检测功能开启时运行
        if not self.is_func_serial_opened:
            return

        # 收集当前可用的端口（并保留 manufacturer 类型）
        self.com_list = {}
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            manufacturer = port.manufacturer()
            if manufacturer in ["Silicon Labs", "wch.cn", "Microsoft", "(Undefined Vendor)"]:
                manufacturer_type = 0 if manufacturer == "Silicon Labs" else 1
                self.com_list[port.portName()] = manufacturer_type

        # 按端口名尾部的数字升序排序（如 COM3 < COM10）；无数字的排在后面
        def _port_sort_key(name):
            m = re.search(r'(\d+)$', name)
            if m:
                return (0, int(m.group(1)), name)  # 有数字的按数字排序，数字相同再按名字
            return (1, name)  # 无数字的放到最后，按名字排序

        available_ports = sorted(self.com_list.keys(), key=_port_sort_key)

        # 四个 lineEdit 的引用（按你 UI 的顺序）
        line_edits = [
            self.ui_bot_lineEdit_work
        ]

        # 1) 清除那些已绑定但当前不可用的 port（设备拔掉时只清除对应的 lineEdit）
        assigned_ports = set()
        for le in line_edits:
            text = le.text().strip()
            if text:
                if text not in available_ports:
                    le.clear()
                else:
                    assigned_ports.add(text)

        # 2) 将尚未分配的可用端口依次填入第一个空的 lineEdit（不重复分配）
        for port in available_ports:
            if port in assigned_ports:
                continue
            # 找到第一个空的 lineEdit 来填充
            for le in line_edits:
                if not le.text().strip():
                    le.setText(port)
                    assigned_ports.add(port)
                    break
            # 如果没有空 slot（4 个都被占用），则跳过该 port

        # 调试输出（保留）
        #print(self.com_list)


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

        if snlen < 18 or snlen > 22:
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
                if manufacturer in ["FTDI","Microsoft","wch.cn"]:
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



    # 一拖四 开始测试按键
    @pyqtSlot()
    def on_ui_btn_startTest_clicked(self):
        global g_db_connection,g_project,g_test_mode
        if not g_db_connection and g_test_mode == 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("错误")
            msg.setText("MES连接失败,请检查网络是否正常！")
            btn_confirm = msg.addButton("返回", QMessageBox.RejectRole)
            btn_continue = msg.addButton("离线测试", QMessageBox.AcceptRole)
            msg.exec_()  # 在 PyQt6 中可以用 msg.exec()

            if msg.clickedButton() == btn_confirm:
                self.is_func_serial_opened = True


        if not self.is_func_serial_opened:
            self.ui_btn_startTest.setText("停止测试")
            self.is_func_serial_opened = True
            self.ui_lineEdit_work_1.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";border: 1px solid rgb(85, 170, 127); padding: 1px;')
            self.ui_lineEdit_work_2.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";border: 1px solid rgb(85, 170, 127); padding: 1px;')
            self.ui_lineEdit_work_3.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";border: 1px solid rgb(85, 170, 127); padding: 1px;')
            self.ui_lineEdit_work_4.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";border: 1px solid rgb(85, 170, 127); padding: 1px;')
        else:
            self.ui_btn_startTest.setText("开始测试")
            self.is_func_serial_opened = False
            self.ui_lineEdit_work_1.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";')
            self.ui_lineEdit_work_2.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";')
            self.ui_lineEdit_work_3.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";')
            self.ui_lineEdit_work_4.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";')
            self.ui_lineEdit_work_1.clear()
            self.ui_lineEdit_work_2.clear()
            self.ui_lineEdit_work_3.clear()
            self.ui_lineEdit_work_4.clear()

        self.ui_stackedWidget_work_1.setCurrentIndex(2)
        self.ui_stackedWidget_work_2.setCurrentIndex(2)
        self.ui_stackedWidget_work_3.setCurrentIndex(2)
        self.ui_stackedWidget_work_4.setCurrentIndex(2)


    # 底座 开始测试按键
    @pyqtSlot()
    def on_ui_btn_bot_startTest_clicked(self):
        global g_project,g_test_mode
        if not self.is_func_serial_opened:
            self.ui_btn_bot_startTest.setText("停止测试")
            self.is_func_serial_opened = True
            self.ui_bot_lineEdit_work.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";border: 1px solid rgb(85, 170, 127); padding: 1px;')
        else:
            self.ui_btn_bot_startTest.setText("开始测试")
            self.is_func_serial_opened = False
            self.ui_bot_lineEdit_work.setStyleSheet('color: rgb(85, 170, 127);font: 87 10pt "Arial Black";')
            self.ui_bot_lineEdit_work.clear()

        self.ui_stackedWidget_bot.setCurrentIndex(2)

        # 底座 开始测试按键

    @pyqtSlot()
    def on_ui_btn_bot_retest_clicked(self):
        global g_project, g_test_mode
        if self.is_func_serial_opened:
            self.test_func_thread.signal_isRetest.emit(True)





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

            if g_project == ProjectType.m7005.val2:
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

            if not g_project == ProjectType.m7005.val2:
                self.change_test_prj_Button.setEnabled(True)
                self.manual_change_Button.setEnabled(True)

            self.retest_Button.setEnabled(True)
            self.start_test_thread_func(self)


            if self.test_func_thread.serial.isOpen():
                if g_project == ProjectType.c7001.val2 or g_project == ProjectType.x7001.val2 or g_project == ProjectType.v7009.val2 and g_test_mode == 2:
                    self.bindingSnWin = StartBindingSn(parent=self)
                    self.bindingSnWin.show()
                    self.bindingSnWin.activateWindow()  # 激活窗口到最前
        else:
            if hasattr(self, 'bindingSnWin') and g_project == ProjectType.c7001.val2 or g_project == ProjectType.x7001.val2 or g_project == ProjectType.v7009.val2 and g_test_mode == 2:
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

            if g_project == ProjectType.m7005.val2:
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

    def get_Lord_work_from_ui(self, num):
        isStart = self.is_func_serial_opened
        if num == 1:
            text = self.ui_lineEdit_work_1.text()
            self.test_func_thread.signal_com_refresh.emit(text, isStart)
        elif num == 2:
            text = self.ui_lineEdit_work_2.text()
            self.test_func_thread2.signal_com_refresh.emit(text, isStart)
        elif num == 3:
            text = self.ui_lineEdit_work_3.text()
            self.test_func_thread3.signal_com_refresh.emit(text, isStart)
        elif num == 4:
            text = self.ui_lineEdit_work_4.text()
            self.test_func_thread4.signal_com_refresh.emit(text, isStart)


    def get_Base_work_from_ui(self, num):
        text = self.ui_bot_lineEdit_work.text()
        isStart = self.is_func_serial_opened
        self.test_func_thread.signal_com_refresh.emit(text, isStart)


    @pyqtSlot()
    def on_ui_btnPass_work_1_clicked(self):
        self.test_func_thread.signal_isPassOrNg.emit(True)

    @pyqtSlot()
    def on_ui_btnNg_work_1_clicked(self):
        self.test_func_thread.signal_isPassOrNg.emit(False)


    @pyqtSlot()
    def on_ui_btnPass_work_2_clicked(self):
        self.test_func_thread2.signal_isPassOrNg.emit(True)

    @pyqtSlot()
    def on_ui_btnNg_work_2_clicked(self):
        self.test_func_thread2.signal_isPassOrNg.emit(False)


    @pyqtSlot()
    def on_ui_btnPass_work_3_clicked(self):
        self.test_func_thread3.signal_isPassOrNg.emit(True)

    @pyqtSlot()
    def on_ui_btnNg_work_3_clicked(self):
        self.test_func_thread3.signal_isPassOrNg.emit(False)


    @pyqtSlot()
    def on_ui_btnPass_work_4_clicked(self):
        self.test_func_thread4.signal_isPassOrNg.emit(True)

    @pyqtSlot()
    def on_ui_btnNg_work_4_clicked(self):
        self.test_func_thread4.signal_isPassOrNg.emit(False)

    @pyqtSlot()
    def on_ui_btn_bot_Pass_work_clicked(self):
        self.test_func_thread.signal_isPassOrNg.emit(True)

    @pyqtSlot()
    def on_ui_btn_bot_Ng_work_clicked(self):
        self.test_func_thread.signal_isPassOrNg.emit(False)



    def set_Lord_ui_page(self, work,isAutoTest, pageNum, testNum, text):
        if work == 1:
            if self.old_pageNum_1 == pageNum and self.old_testNum_1 == testNum and self.old_text_1 == text:
                return
            else:
                self.old_pageNum_1 = pageNum
                self.old_testNum_1 = testNum
                self.old_text_1 = text
                self.ui_stackedWidget_work_1.setCurrentIndex(pageNum)
                if pageNum == 0:
                    self.ui_showPassInfo_work_1.setText(testNum)
                if pageNum == 1:
                    self.ui_showNgInfo_work_1.setText(testNum)
                if pageNum == 3:
                    self.ui_showTestNum_work_1.setText(testNum)
                    self.ui_showTestInfo_work_1.setText(text)
                    self.ui_widgetPN_1.setVisible(isAutoTest)

        if work == 2:
            if self.old_pageNum_2 == pageNum and self.old_testNum_2 == testNum and self.old_text_2 == text:
                return
            else:
                self.old_pageNum_2 = pageNum
                self.old_testNum_2 = testNum
                self.old_text_2 = text
                self.ui_stackedWidget_work_2.setCurrentIndex(pageNum)
                if pageNum == 0:
                    self.ui_showPassInfo_work_2.setText(testNum)
                if pageNum == 1:
                    self.ui_showNgInfo_work_2.setText(testNum)
                if pageNum == 3:
                    self.ui_showTestNum_work_2.setText(testNum)
                    self.ui_showTestInfo_work_2.setText(text)
                    self.ui_widgetPN_2.setVisible(isAutoTest)

        if work == 3:
            if self.old_pageNum_3 == pageNum and self.old_testNum_3 == testNum and self.old_text_3 == text:
                return
            else:
                self.old_pageNum_3 = pageNum
                self.old_testNum_3 = testNum
                self.old_text_3 = text
                self.ui_stackedWidget_work_3.setCurrentIndex(pageNum)
                if pageNum == 0:
                    self.ui_showPassInfo_work_3.setText(testNum)
                if pageNum == 1:
                    self.ui_showNgInfo_work_3.setText(testNum)
                if pageNum == 3:
                    self.ui_showTestNum_work_3.setText(testNum)
                    self.ui_showTestInfo_work_3.setText(text)
                    self.ui_widgetPN_3.setVisible(isAutoTest)

        if work == 4:
            if self.old_pageNum_4 == pageNum and self.old_testNum_4 == testNum and self.old_text_4 == text:
                return
            else:
                self.old_pageNum_4 = pageNum
                self.old_testNum_4 = testNum
                self.old_text_4 = text
                self.ui_stackedWidget_work_4.setCurrentIndex(pageNum)
                if pageNum == 0:
                    self.ui_showPassInfo_work_4.setText(testNum)
                if pageNum == 1:
                    self.ui_showNgInfo_work_4.setText(testNum)
                if pageNum == 3:
                    self.ui_showTestNum_work_4.setText(testNum)
                    self.ui_showTestInfo_work_4.setText(text)
                    self.ui_widgetPN_4.setVisible(isAutoTest)

    def set_Base_ui_page(self, isAutoTest, pageNum, testNum, text):

        if self.old_pageNum_1 == pageNum and self.old_testNum_1 == testNum and self.old_text_1 == text:
            return
        else:
            self.old_pageNum_1 = pageNum
            self.old_testNum_1 = testNum
            self.old_text_1 = text

            self.ui_stackedWidget_bot.setCurrentIndex(pageNum)
            if pageNum == 0:
                self.ui_showPassInfo_work_bot.setText(testNum)
            if pageNum == 1:
                self.ui_showNgInfo_work_bot.setText(testNum)
            if pageNum == 3:
                self.ui_bot_showTestNum_work.setText(testNum)
                self.ui_bot_showTestInfo_work.setText(text)
                self.ui_widgetPN_bot.setVisible(isAutoTest)




    def fun_is_func_serial_opened(self):
        self.test_func_thread.recv_is_func_serial_opened.emit(self.is_func_serial_opened)



    # 开始测试线程
    def start_test_thread_func(self, _):
        global g_project

        self.test_func_thread = FuncTest_Thread(self.serial_func_comboBox.currentText())  # 功能测试线程
        self.test_func_thread.open_serial_link()  # 打开串口
        self.test_func_thread.data_received.connect(self.repl_recv_func)  # 信息
        self.test_func_thread.data_update.connect(self.updata_gui_func)  # 更新UI界面信息
        self.test_func_thread.timer.start()
        self.test_func_thread.start()


        if g_project == ProjectType.x7001.val2:
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

        elif g_project == ProjectType.c7001.val2:
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

        elif g_project == ProjectType.v260Teach.val2:
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

        elif g_project == ProjectType.v7007.val2:
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

        elif g_project == ProjectType.v260Zkb.val2:
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


        elif g_project == ProjectType.v7005.val2:
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

        elif g_project == ProjectType.v7009.val2:
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
        global g_project,g_projectMutation

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
            if g_project == ProjectType.x7001.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7001_小学版.py')
            elif g_project == ProjectType.c7001.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7001_初中版.py')
            elif g_project == ProjectType.v7005.val2 and not g_projectMutation:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7005.py')
            elif g_project == ProjectType.v7005.val2 and g_projectMutation:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7010.py')
            elif g_project == ProjectType.v7007.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7007.py')
            elif g_project == ProjectType.v7009.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_7009.py')
            elif g_project == ProjectType.v260Teach.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhTest_ts260Teach.py')
            elif g_project == ProjectType.v260Zkb.val2:
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

        if g_project == ProjectType.x7001.val2:
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

        elif g_project == ProjectType.c7001.val2:
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

        elif g_project == ProjectType.v260Teach.val2:
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


        elif g_project == ProjectType.v7005.val2:

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


        elif g_project == ProjectType.v7007.val2:
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

        elif g_project == ProjectType.v260Zkb.val2:
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


        elif g_project == ProjectType.v7009.val2:

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

    # OK的
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
            if g_project == ProjectType.x7001.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7001_小学版.py')

            if g_project == ProjectType.c7001.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7001_初中版.py')

            if g_project == ProjectType.v7005.val2 and not g_projectMutation:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7005.py')

            if g_project == ProjectType.v7005.val2 and g_projectMutation:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7010.py')

            if g_project == ProjectType.v7007.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemoNULL.py')

            if g_project == ProjectType.v260Teach.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_ts260Teach.py')


            if g_project == ProjectType.v7009.val2:
                external_file_path = os.path.join(os.getcwd(), 'config\hhDemo_7009.py')

            if g_project == ProjectType.v260Zkb.val2:
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
        if g_project == ProjectType.x7001.val2:
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
        elif g_project == ProjectType.c7001.val2:
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
        elif g_project == ProjectType.v260Teach.val2:
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
        elif g_project == ProjectType.v7005.val2:

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
        elif g_project == ProjectType.v7007.val2:

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
        elif g_project == ProjectType.v260Zkb.val2:

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
        elif g_project == ProjectType.v7009.val2:

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
            if g_project == ProjectType.x7001.val2:
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

            elif g_project == ProjectType.c7001.val2:
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

            elif g_project == ProjectType.v260Teach.val2:
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



            elif g_project == ProjectType.v7005.val2:

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

            elif g_project == ProjectType.v7007.val2:

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

            elif g_project == ProjectType.v260Zkb.val2:

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


            elif g_project == ProjectType.v7009.val2:

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



class OneToFourTest_Thread(QThread):
    signal_get_work_com = pyqtSignal(int)
    signal_set_ui_page = pyqtSignal(int,bool,int, str, str)
    signal_com_refresh = pyqtSignal(str, bool)
    signal_isPassOrNg =  pyqtSignal(bool)


    class TestType(Enum):
        null = 0
        rgb = 1
        lcd = 2
        tf = 3
        mp3 = 4
        btn = 5
        i2c = 6
        adc = 7
        msg = 8
        wifi = 9
        gpio = 10
        mes = 11
        writeSn = 12
        finish = 13


    def __init__(self,work):
        super(OneToFourTest_Thread, self).__init__()
        self._recv_accum = ""           # 累积接收文本，处理分片
        self.port = ""
        self.isStart = False
        self.isOpenPort = False
        self.serial = None
        self._check_timer = None
        self._write_timer = None
        self.work = work
        self.initVars()

        self.cmd_rgb = "tool call test_rgb r=50 g=50 b=50"
        self.cmd_lcd_rgb = "tool call test_lcd r=255 g=255 b=255\ntool call test_lcd r=255 g=0 b=0\ntool call test_lcd r=0 g=255 b=0\ntool call test_lcd r=0 g=0 b=255"
        self.cmd_lcd_rgb_white = "tool call test_lcd r=255 g=255 b=255"
        self.cmd_btn = "tool call test_buttons timeout_ms=1000"
        self.cmd_tf = "tool call test_tf"
        self.cmd_play = "tool call test_audio action=play"
        self.cmd_adc = "tool call test_sound_adc duration_ms=1000"
        self.cmd_msg = "tool call test_sensors"
        self.cmd_i2c = "i2c_scan\n"

        self.ssid, self.password = self.getWifiConfig()
        if self.ssid and self.password:
            self.cmd_wifi = 'tool call test_wifi --json {{"ssid":"{}","password":"{}"}}'.format(self.ssid, self.password)
        else:
            self.cmd_wifi = ""

        self.cmd_mp3 = "tool call play_audio url=file:///sdcard/voice/music_1.mp3"
        self.cmd_gpio = "tool call test_ext_pin pin=P0 mode=in\ntool call test_ext_pin pin=P1 mode=in\ntool call test_ext_pin pin=P2 mode=in\ntool call test_ext_pin pin=P3 mode=in\n"
        self.cmd_base_rgb = "tool call control_ext_rgb module=base index=-1 r=50 g=50 b=50"

        angle1, angle2 = self.getServoAngle(self.work)
        self.cmd_servo_turn = "tool call control_ext_servo servo_num=1 angle={}\ntool call control_ext_servo servo_num=2 angle={}".format(angle1, angle2)
        self.cmd_servo_stop = "tool call control_ext_servo servo_num=1 angle=0.0\ntool call control_ext_servo servo_num=2 angle=0.0"
        self.cmd_base_power = "tool call control_base_power enable=true"
        self.cmd_read_mac = "tool call read_mac"


        self.signal_com_refresh.connect(self.set_work_code)
        self.signal_isPassOrNg.connect(self.Is_Pass_Or_Ng)

    def getServoAngle(self,station_num: int):
        # 拼接文件路径：当前目录/config/ServoAngle.ini
        ini_path = os.path.join(os.getcwd(), "config", "ServoAngle.ini")
        cfg = configparser.ConfigParser()

        # 判断文件是否存在
        if not os.path.exists(ini_path):
            QMessageBox.critical(None, "配置错误", f"配置文件不存在：\n{ini_path}")
            return None, None

        # 读取ini
        try:
            cfg.read(ini_path, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(None, "读取失败", f"读取ServoAngle.ini出错：{str(e)}")
            return None, None

        sec_name = str(station_num)
        # 判断工位section是否存在
        if sec_name not in cfg.sections():
            QMessageBox.warning(None, "工位不存在", f"无工位{station_num}配置")
            return None, None

        try:
            top_val = float(cfg.get(sec_name, "top"))
            down_val = float(cfg.get(sec_name, "down"))
            return top_val, down_val
        except Exception as e:
            QMessageBox.critical(None, "参数解析错误", f"工位{station_num}参数读取失败：{str(e)}")
            return None, None

    def getWifiConfig(self):
        """
        读取INI中 [wifi] 节点的ssid、password
        :return: (ssid, password) 读取失败返回 (None, None)
        """
        ini_path = os.path.join(os.getcwd(), "config", "ServoAngle.ini")
        cfg = configparser.ConfigParser()

        # 文件存在校验
        if not os.path.exists(ini_path):
            QMessageBox.critical(None, "配置错误", f"wifi配置文件不存在：\n{ini_path}")
            return None, None

        # 加载ini
        try:
            cfg.read(ini_path, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(None, "读取失败", f"读取配置文件异常：{str(e)}")
            return None, None

        # 校验[wifi]区块
        wifi_section = "wifi"
        if wifi_section not in cfg.sections():
            QMessageBox.warning(None, "配置缺失", "INI文件内无 [wifi] 配置区块")
            return None, None

        try:
            ssid = cfg.get(wifi_section, "ssid").strip()
            password = cfg.get(wifi_section, "password").strip()
            return ssid, password
        except Exception as e:
            QMessageBox.critical(None, "参数缺失", f"wifi ssid/password读取失败：{str(e)}")
            return None, None

    def initVars(self):
        self._recv_accum = ""
        self.msn = 0
        self.mac = ""
        self.sn = ""
        self.oldSn = ""
        self.code = ""
        self.isUpdata = False
        self.oldCurrentTestIndex = 0
        self.currentTestIndex = 1
        self._last_now = None
        self.turn_state = False
        self.currentMsgNum = 0


        self.testNum = random.choice([2, 3, 4])
        self.rssi = 0
        self.servoCount = 0
        self.servoCount = 0
        self.m_p0_on_num = 0
        self.m_p0_off_num = 0
        self.m_p1_on_num = 0
        self.m_p1_off_num = 0

        self.m_p2_on_num = 0
        self.m_p2_off_num = 0
        self.m_p3_on_num = 0
        self.m_p3_off_num = 0

        self.light = 0.00
        self.accel = 0.00
        self.gyro  = 0.00
        self.mag   = 0.00

        self.test_rgb_result = False
        self.test_lcd_result = False
        self.test_btn_result = False
        self.test_play_result = False
        self.test_tf_result = False
        self.test_adc_result = False
        self.test_msg_result = False
        self.test_wifi_result = False
        self.test_gpio_result = False

        self._sent_rgb_cmd = False
        self._finish_rgb = False
        self._waiting_rgb_cmd = False

        self._sent_lcd_cmd = False
        self._finish_lcd = False
        self._waiting_lcd_cmd = False

        self._sent_btn_cmd = False
        self._finish_btn = False
        self._waiting_btn_cmd = False

        self.confirm_pressed = False
        self.return_pressed = False
        self.select_pressed = False

        self._sent_tf_cmd = False
        self._finish_tf = False
        self._waiting_tf_cmd = False

        self._sent_play_cmd = False
        self._finish_play = False
        self._waiting_play_cmd = False

        self._sent_adc_cmd = False
        self._finish_adc = False
        self._waiting_adc_cmd = False

        self._finish_i2c = False
        self._sent_i2c_cmd = False
        self._waiting_i2c_cmd = False


        self._sent_msg_cmd = False
        self._finish_msg = False
        self._waiting_msg_cmd = False

        self._sent_wifi_cmd = False
        self._finish_wifi = False
        self._waiting_wifi_cmd = False
        self._wifi_retry_num = 0

        self._msg_retry_num = 0
        self._msg_Through_num = 0

        self._sent_gpio_cmd = False
        self._finish_gpio = False
        self._waiting_gpio_cmd = False

        self._finish_mp3 = False
        self._sent_mp3_cmd = False
        self._waiting_mp3_cmd = False

        self._finish_base_power = False
        self._sent_base_power_cmd = False
        self._waiting_base_power_cmd = False

        self._finish_base_servo = False
        self._sent_base_servo_cmd = False
        self._waiting_base_servo_cmd = False


        self._finish_read_mac = False
        self._sent_read_mac_cmd = False
        self._waiting_read_mac_cmd = False

        self.is_finish_write_sn_code = False
        self.write_sn_code = False

        self._waiting_write_sn_cmd = False
        self._waiting_write_code_cmd = False

    def find_mac(self, mac: str):
        global g_db_connection, g_MesTableName

        # 预先清空旧 SN，避免残留
        self.oldSn = None

        if not isinstance(mac, str) or not mac.strip():
            return False

        normalized_mac = mac.strip().upper()

        # 获取现有连接（不尝试重连）
        connection = g_db_connection if (
                g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            return False

        try:
            sql = "SELECT sn FROM `{}` WHERE UPPER(mac) = %s LIMIT 1".format(g_MesTableName)
            with connection.cursor() as cursor:
                cursor.execute(sql, (normalized_mac,))
                row = cursor.fetchone()
                if not row:
                    return False

                # 兼容不同 cursor 返回类型
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    sn = row[0]
                elif isinstance(row, dict):
                    sn = row.get('sn') if 'sn' in row else (next(iter(row.values())) if row else None)
                else:
                    sn = row

                if sn is None:
                    return False

                # 确保是字符串
                if isinstance(sn, bytes):
                    try:
                        sn = sn.decode('utf-8')
                    except Exception:
                        sn = str(sn)

                self.oldSn = str(sn)
                return True

        except pymysql.MySQLError:
            return False
        except Exception:
            return False

    def uploading(self,info):
        global g_db_connection,g_MesTableName

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            return False

        print("\nmac = :", self.mac)
        print("\nsn = :", self.sn)
        print("\nrandom_code = :", self.code)

        try:
            if not self.isUpdata:
                with connection.cursor() as cursor:
                    # 开始事务
                    connection.begin()

                    # 插入新记录
                    insert_sql = "INSERT INTO `" + g_MesTableName + "` (mac, sn, code,info, time) VALUES (%s, %s, %s, %s,NOW())"
                    cursor.execute(insert_sql, (self.mac, self.sn ,self.code, info))

                    # 提交事务
                    connection.commit()
                    return True
            else:
                with connection.cursor() as cursor:
                    # 开始事务
                    connection.begin()

                    # 根据MAC地址更新内容,但是不更新新记录
                    update_sql = "UPDATE `{}` SET info = %s, time = NOW() WHERE UPPER(mac) = %s".format(g_MesTableName)
                    cursor.execute(update_sql, (info, self.mac))


                    # 提交事务
                    connection.commit()
                    return True

        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            return False
        except Exception as e:
            if connection:
                connection.rollback()
            return False

    def create_random_code(self,sn: str, mac: str) -> Tuple[bytes, Dict[str, str]]:
        normalized_sn = sn.strip()
        normalized_mac = mac.strip().upper()
        MAC_PATTERN = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$")
        if not normalized_sn:
            raise ValueError("SN不能为空")
        if not MAC_PATTERN.fullmatch(normalized_mac):
            raise ValueError("MAC必须使用 AA:BB:CC:DD:EE:FF 格式")
        device_secret_raw = secrets.token_bytes(32)
        return str(device_secret_raw.hex())


    def find_first_missing_sn_serial(self):
        global g_db_connection, g_MesTableName

        conn = g_db_connection if (g_db_connection is not None and getattr(g_db_connection, 'open', True)) else None
        if conn is None:
            return False, "MES未连接, 无法查询"

        try:
            cursor = conn.cursor()
            # 如果你的代码是DictCursor，上面改成 cursor = conn.cursor(pymysql.cursors.DictCursor)

            sql = """
            SELECT
                sn,
                SUBSTRING(sn, LENGTH(sn)-6, 6) AS serial_str,
                CAST(SUBSTRING(sn, LENGTH(sn)-6, 6) AS UNSIGNED) AS serial_num,
                RIGHT(sn,1) AS color,
                LEFT(sn, LENGTH(sn)-7) AS real_prefix
            FROM 7011_x_card_final
            WHERE LENGTH(sn)>=7  
              AND CAST(SUBSTRING(sn, LENGTH(sn)-6, 6) AS UNSIGNED) BETWEEN 1 AND 999999
            ORDER BY serial_num ASC;
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()

            serial_list = []
            for row in rows:
                # dict模式：row是字典；普通cursor：row是tuple
                if isinstance(row, dict):
                    val = row.get("serial_num")
                else:
                    if len(row) < 3:
                        continue
                    val = row[2]

                if val is not None and isinstance(val, int):
                    serial_list.append(val)

            if not serial_list:
                return True, 1

            missing = None
            expect = 1
            for num in serial_list:
                if num > expect:
                    missing = expect
                    break
                expect = num + 1

            # 全部连续无缺口，返回最后一个+1（即expect）
            if missing is None:
                missing = expect

            return True, missing

        except Exception as e:
            import traceback
            err_text = f"查询异常:{str(e)}\n{traceback.format_exc()}"
            return False, err_text

    def create_sn(self,serial: int,
                  product_type: str = "13",
                  product_name: str = "48",
                  version: str = "A",
                  reserved: str = "00",
                  check: str = "A",
                  color: str = "W",
                  prod_date: Optional[datetime.date] = None
                  ) -> str:

        # 验证 serial
        if not isinstance(serial, int) or serial < 0 or serial > 999999:
            raise ValueError("流水号必须是 0 到 999999 之间的整数（含边界）")

        # 简单长度验证
        if len(product_type) != 2 or len(product_name) != 2 or len(version) != 1 or len(reserved) != 2:
            raise ValueError("产品类型/产品名称/版本/预留长度无效")
        if len(check) != 1 or len(color) != 1:
            raise ValueError("校验位和产品颜色必须为单个字符")

        # 生产日期（默认今天）
        if prod_date is None:
            prod_date = datetime.date.today()

        iso_year, iso_week, _ = prod_date.isocalendar()
        year_part = f"{(iso_year % 100):02d}"
        week_part = f"{iso_week:02d}"
        serial_part = f"{serial:06d}"

        sn = f"{product_type}{product_name}{version}{reserved}{year_part}{week_part}{check}{serial_part}{color}"
        return sn


    def set_work_code(self, com, isStart):
        if com and com != self.port and self.isOpenPort:
            try:
                if QThread.currentThread() == self.thread():
                    self._close_serial()
                else:
                    QMetaObject.invokeMethod(self, "_close_serial", Qt.BlockingQueuedConnection)
            except Exception:
                # 兜底：尝试直接关闭
                try:
                    self._close_serial()
                except Exception:
                    pass

        # 更新端口与启动标志
        self.port = com
        self.isStart = isStart


    def Is_Pass_Or_Ng(self, var,test = ""):
        if self.currentTestIndex == self.TestType.rgb.value and self._finish_rgb:
            if var:
                self.currentTestIndex += 1
                self.test_rgb_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.test_rgb_result = False
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.lcd.value and self._finish_lcd:
            if var:
                self.currentTestIndex += 1
                self.test_lcd_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.test_lcd_result = False
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.i2c.value and self._finish_i2c:
            if var:
                self.currentTestIndex += 1
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "I2C异常", "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.btn.value and self._finish_btn:
            if var:
                self.currentTestIndex += 1
                self.test_btn_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.test_btn_result = False
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.tf.value and self._finish_tf:
            if var:
                self.currentTestIndex += 1
                self.test_tf_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "无法读取TF卡", "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.mp3.value and self._finish_mp3:
            if var:
                self.currentTestIndex += 1
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "音频播放异常", "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.i2c.value and self._sent_play_cmd:
            if var:
                self.currentTestIndex += 1
                self.test_play_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "喇叭功能异常", "")
                self.currentTestIndex = 0


        elif self.currentTestIndex == self.TestType.adc.value and self._finish_adc:
            if var:
                self.currentTestIndex += 1
                self.test_adc_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "麦克风异常", "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.msg.value and self._finish_msg or test:
            if var:
                self.currentTestIndex += 1
                self.test_msg_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.wifi.value and self._finish_wifi:
            if var:
                self.currentTestIndex += 1
                self.test_wifi_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "WIFI连接失败", "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.gpio.value and self._finish_gpio:
            if var:
                self.currentTestIndex += 1
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "GPIO异常", "")
                self.currentTestIndex = 0


    def open_serial_link(self):
        if not self.port:
            print("open_serial_link: 未指定端口")
            return False

        available = [p.portName() for p in QSerialPortInfo.availablePorts()]
        if self.port not in available:
            print(f"open_serial_link: 请求的端口 {self.port} 不在可用端口列表: {available}")
            return False

        try:
            if self.serial is not None:
                self._close_serial()

            self.serial = QSerialPort()
            self.serial.setPortName(self.port)
            self.serial.setBaudRate(115200)
            self.serial.setDataBits(QSerialPort.Data8)
            self.serial.setParity(QSerialPort.NoParity)
            self.serial.setStopBits(QSerialPort.OneStop)
            self.serial.setFlowControl(QSerialPort.NoFlowControl)

            if self.serial.open(QIODevice.ReadWrite):
                print(f"\n成功打开串口: {self.port}")
                self.signal_set_ui_page.emit(self.work,False, 2, "", "")
                try:
                    self.serial.clear()
                except Exception:
                    pass
                time.sleep(0.05)

                try:
                    self.serial.readyRead.connect(self.on_serial_read)
                except Exception as e:
                    print("readyRead connect 异常:", e)

                # reset states
                self.initVars()

                self.isOpenPort = True
                QTimer.singleShot(2000, self._start_periodic_write)  # 延迟 2s 启动写定时器
                return True
            else:
                print(f"\n打开串口失败: {self.port}")
                self.isOpenPort = False
                return False
        except Exception as e:
            print("open_serial_link 异常:", e)
            self.isOpenPort = False
            return False

    def _close_serial(self):
        # 1) 停写定时器，避免并发写
        try:
            self._stop_periodic_write()
        except Exception:
            pass

        # 2) 标记端口已关闭，避免其它逻辑再尝试写
        self.isOpenPort = False

        if not self.serial:
            return

        try:
            # 3) 断开信号
            try:
                self.serial.readyRead.disconnect(self.on_serial_read)
            except Exception:
                pass

            # 4) 嘗試短等待 pending bytes 写入排空（可选，短超时）
            try:
                self.serial.waitForBytesWritten(200)  # 200 ms
            except Exception:
                pass

            # 5) 清理缓冲
            try:
                self.serial.clear()
            except Exception:
                pass

            # 6) 关闭端口
            try:
                self.serial.close()
            except Exception:
                pass

            # 7) 释放引用（不要依赖 deleteLater 必须由事件循环处理）
            try:
                self.serial = None
            except Exception:
                self.serial = None

        finally:
            # 8) 重置状态标志（按需）
            self._sent_rgb_cmd = False
            self._finish_rgb = False
            self._waiting_rgb_cmd = False
            self._last_now = 0.0
            # ... 重置其它标志 ...
            self._recv_accum = ""
            self.isOpenPort = False

    def _start_periodic_write(self):
        if not self.isOpenPort or self.serial is None:
            return
        if self._write_timer is None:
            self._write_timer = QTimer()
            self._write_timer.timeout.connect(self._on_write_timer)
            self._write_timer.start(100)

    def _stop_periodic_write(self):
        if self._write_timer is not None:
            try:
                if self._write_timer.isActive():
                    self._write_timer.stop()
            except Exception:
                pass
            try:
                self._write_timer.timeout.disconnect(self._on_write_timer)
            except Exception:
                pass
            self._write_timer = None
            print("写入定时器已停止")

    # 指令发送
    def _on_write_timer(self):
        global DB_LOCK
        if not self.isOpenPort or self.serial is None:
            self._stop_periodic_write()
            return

        now = time.time()

        if self.currentTestIndex == self.TestType.rgb.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_rgb
            if not self._finish_rgb:
                self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[RGB灯]\n发送控制指令中...")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_rgb_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_rgb_cmd = True
                        self._waiting_rgb_cmd = True
                        self._last_now = now
                        print(f"[发送] RGB cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] RGB cmd={t_cmd}")
            else:
                self.signal_set_ui_page.emit(self.work,True, 3, t_testPro, "\n << < 人工查看 >> >\n\n[RGB灯]\n[电源指示灯]\n\n\n是否点亮?")

        if self.currentTestIndex == self.TestType.lcd.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            if not self._finish_lcd:
                t_cmd = self.cmd_lcd_rgb
                self.signal_set_ui_page.emit(self.work,True, 3, t_testPro, "\n << < 人工查看 >> >\n\n[LCD显示屏]\n\n\n\n是否无坏点,无划痕?")
                cmd_bytes = (self.cmd_lcd_rgb + "\r\n").encode('utf-8')
                if (not self._waiting_lcd_cmd) or (now - self._last_now > 15.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_lcd_cmd = True
                        self._finish_lcd = True
                        self._waiting_lcd_cmd = True
                        self._last_now = now
                        print(f"[发送] LCD显示屏 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] LCD显示屏 cmd={t_cmd}")

        if self.currentTestIndex == self.TestType.tf.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_tf
            if not self._finish_tf:
                self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[TF卡自检]\n")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_tf_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(500)
                        except Exception:
                            pass
                        self._sent_tf_cmd = True
                        self._waiting_tf_cmd = True
                        self._last_now = now
                        print(f"[发送] TF卡自检 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] TF卡自检 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(self.test_tf_result)

        if self.currentTestIndex == self.TestType.mp3.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_mp3
            self.signal_set_ui_page.emit(self.work,True, 3, t_testPro, "\n << < 人工聆听 >> >\n\n[音频播放测试]\n\n\n\n是否正常播放?")
            cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
            if (not self._waiting_mp3_cmd) or (now - self._last_now >= 5.0):
                try:
                    bytes_written = self.serial.write(cmd_bytes)
                    try:
                        self.serial.waitForBytesWritten(500)
                    except Exception:
                        pass
                    self._sent_mp3_cmd = True
                    self._waiting_mp3_cmd = True
                    self._finish_mp3 = True
                    self._last_now = now
                    print(f"[发送] mp3音频播放 cmd={t_cmd} bytes={bytes_written}")
                except Exception:
                    print(f"[发送失败] mp3音频播放 cmd={t_cmd}")

        if self.currentTestIndex == self.TestType.btn.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_btn
            if not self._finish_btn:
                self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[功能按键测试]\n正在检测按键是否按下...")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_btn_cmd) or (now - self._last_now > 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_btn_cmd = True
                        self._waiting_btn_cmd = True
                        self._last_now = now
                        print(f"[发送] 功能按键检测 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 功能按键检测 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(True)

        if self.currentTestIndex == self.TestType.i2c.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_i2c
            if not self._finish_i2c:
                self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[I2C自检]\n")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_i2c_cmd) or (now - self._last_now > 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(500)
                        except Exception:
                            pass
                        self._sent_i2c_cmd = True
                        self._waiting_i2c_cmd = True
                        self._last_now = now
                        print(f"[发送] I2C自检 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] I2C卡自检 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(True)

        if self.currentTestIndex == self.TestType.adc.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_adc
            if not self._finish_adc:
                self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[ADC自检]\n")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_adc_cmd) or (now - self._last_now > 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(500)
                        except Exception:
                            pass
                        self._sent_adc_cmd = True
                        self._waiting_adc_cmd = True
                        self._last_now = now
                        print(f"[发送] ADC自检 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] ADC卡自检 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(True)

        if self.currentTestIndex == self.TestType.msg.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_msg
            if not self._finish_msg:
                self.signal_set_ui_page.emit(self.work, False, 3, t_testPro,f"\n\n\n[传感器自检]\n[光线]:{self.light}\n[加速度]:{self.accel}\n[陀螺仪]:{self.gyro}\n测试次数:{self.currentMsgNum}")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_msg_cmd) or (now - self._last_now > 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(500)
                        except Exception:
                            pass
                        self._sent_msg_cmd = True
                        self._waiting_msg_cmd = True
                        self._last_now = now
                        print(f"[发送] 传感器自检 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 传感器自检 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(True)

        if self.currentTestIndex == self.TestType.wifi.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_wifi
            self.ssid, self.password
            if self.rssi != 0:
                self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, f"\n\n\n\n\n[WIFI自检]\n[SSID]:{self.ssid}\n[CODE]:{self.password}" + "RSSI: " + str(self.rssi))
            else:
                self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, f"\n\n\n\n\n[WIFI自检]\n[SSID]:{self.ssid}\n[CODE]:{self.password}")

            if not self._finish_wifi:
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_wifi_cmd) or (now - self._last_now >= 5.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(500)
                        except Exception:
                            pass
                        self._sent_wifi_cmd = True
                        self._waiting_wifi_cmd = True
                        self._last_now = now
                        print(f"[发送] WIFI自检 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] WIFI自检 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(True)

        if self.currentTestIndex == self.TestType.gpio.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)

            if self.m_p0_on_num > self.testNum:
                self._finish_base_servo = True

            if not self._finish_base_servo:
                t_cmd = self.cmd_gpio
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                try:
                    bytes_written = self.serial.write(cmd_bytes)
                    self.serial.waitForBytesWritten(1000)
                    print(f"[发送] GPIO读取 cmd={t_cmd} bytes={bytes_written}")
                except Exception:
                    print(f"[发送失败] GPIO读取 cmd={t_cmd}")
                    pass
                t_time = 2
                if self.turn_state:
                    t_cmd = self.cmd_servo_turn
                    self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[金手指自检-TREN]")
                    cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                    if (now - self._last_now > t_time):
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(1000)
                            self.m_p0_on_num += 1
                            print(f"[发送] 舵机转动 cmd={t_cmd} bytes={bytes_written}")
                        except Exception:
                            print(f"[发送失败] 舵机转动 cmd={t_cmd}")

                        self._last_now = now
                        self.turn_state = not self.turn_state
                else:
                    t_cmd = self.cmd_servo_stop
                    self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[金手指自检-ZERO]")
                    cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                    if (now - self._last_now > t_time):
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(1000)
                            self.m_p0_on_num += 1
                            print(f"[发送] 舵机归位自检 cmd={t_cmd} bytes={bytes_written}")
                        except Exception:
                            print(f"[发送失败] 舵机归位自检 cmd={t_cmd}")
                            pass

                        self._last_now = now
                        self.turn_state = not self.turn_state
            else:
                self.currentTestIndex += 1

        if self.currentTestIndex == self.TestType.mes.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)

            if self.msn == 0:
                if not self.mac:
                    t_cmd = self.cmd_read_mac
                    if not self._finish_read_mac:
                        self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[读取MAC地址]\n")
                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (not self._waiting_read_mac_cmd) or (now - self._last_now > 2.0):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(500)
                                except Exception:
                                    pass
                                self._sent_read_mac_cmd = True
                                self._waiting_read_mac_cmd = True
                                self._last_now = now
                                print(f"[发送] 读取MAC地址 cmd={t_cmd} bytes={bytes_written}")
                            except Exception:
                                print(f"[发送失败] 读取MAC地址 cmd={t_cmd}")
                else:
                    self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, f"\n\n\n\n[读取MAC地址]\n{self.mac}")
                    if now - self._last_now > 1.0:
                        self.isUpdata = self.find_mac(self.mac)
                        if self.isUpdata:
                            self.currentTestIndex += 1
                        else:
                            self.msn = 1
                            self._last_now = now

            if self.msn == 1:
                if not self.sn:
                    ok, serial = self.find_first_missing_sn_serial()

                    if ok:
                        self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[生成SN码]\n")
                        self.sn = self.create_sn(serial)
                        self._last_now = now
                else:
                    self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, f"\n\n\n\n[生成SN码]\n{self.sn}")
                    self.msn = 2



            if self.msn == 2:
                if not self.code:
                    self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[生成设备密钥]\n")
                    self.code = self.create_random_code(self.sn, self.mac)
                    self._last_now = now
                else:
                    self.signal_set_ui_page.emit(self.work, False, 3, t_testPro,f"\n\n\n\n[生成设备密钥]\n{self.code[:22]}\n{self.code[22:44]}\n{self.code[44:]}")
                    self.msn = 3


            if self.msn == 3:
                try:
                    self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[上传MES系统]\n")
                    if self.uploading(""):
                        print("上传MES成功:")
                        self.currentTestIndex += 1
                    else:
                        print("上传MES失败")
                        self.signal_set_ui_page.emit(self.work, False, 1, "上传MES系统失败", "")
                        self.currentTestIndex = -1
                except ValueError as e:
                    print("上传MES失败错误:", e)


        if self.currentTestIndex == self.TestType.writeSn.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            if not self.isUpdata:
                if not self.is_finish_write_sn_code:
                    if not self.write_sn_code:
                        t_cmd = ("tool call write_sn sn=" +  str(self.sn) +"\n")
                        self.signal_set_ui_page.emit(self.work,False, 3, t_testPro, "\n\n\n\n\n[写SN码]\n" + str(self.sn))
                        cmd_bytes = t_cmd.encode('utf-8')
                        if (not self._waiting_write_sn_cmd) or (now - self._last_now >= 3.0):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(200)
                                except Exception:
                                    pass
                                self._waiting_write_sn_cmd = True
                                self._last_now = now
                                print(f"[发送] 写SN码 cmd={t_cmd} bytes={bytes_written}")
                            except Exception:
                                print(f"[发送失败] 写SN码 cmd={t_cmd}")
                    else:
                        t_cmd = ("tool call write_device_secret device_secret=" +  str(self.code) +"\n")
                        self.signal_set_ui_page.emit(self.work, False, 3, t_testPro,f"\n\n\n\n[写设备密钥]\n{self.code[:22]}\n{self.code[22:44]}\n{self.code[44:]}")
                        cmd_bytes = (t_cmd).encode('utf-8')
                        if (not self._waiting_write_code_cmd) or (now - self._last_now >= 3.0):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(200)
                                except Exception:
                                    pass
                                self._waiting_write_code_cmd = True
                                self._last_now = now
                                print(f"[发送] 写设备密钥 cmd={t_cmd} bytes={bytes_written}")
                            except Exception:
                                print(f"[发送失败] 写设备密钥 cmd={t_cmd}")
                else:
                    self.currentTestIndex += 1
            else:
                self.currentTestIndex += 1


        if self.currentTestIndex == self.TestType.finish.value:
            self.signal_set_ui_page.emit(self.work,False, 0, f"测试通过\n\n[设备SN]\n{self.oldSn if self.isUpdata else self.sn}", "")


    # 指令接收
    def on_serial_read(self):
        if not self.serial:
            return
        try:
            qba = self.serial.readAll()
            chunk = qba.data() if hasattr(qba, "data") else bytes(qba)
        except Exception:
            chunk = b''
            print("serial.readAll() 读取异常")
        if not chunk:
            return
        try:
            recv_str = chunk.decode('utf-8', errors='replace')
        except Exception:
            recv_str = ''
            print("recv data decode err")

        self._recv_accum += recv_str
        if len(self._recv_accum) > 5000:
            self._recv_accum = self._recv_accum[-5000:]


        # --------------------------------- 主控 ---------------------------------
        # RGB 检查
        if self.currentTestIndex == self.TestType.rgb.value:
            if not self._finish_rgb:
                expected_echo = self.cmd_rgb
                expected_json = {"status": "ok"}

                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self._finish_rgb = True
                    self._waiting_rgb_cmd = False
                    print(">>>>>>>>收到 RGB 确认 JSON:", json.dumps(obj, ensure_ascii=False))

        if self.currentTestIndex == self.TestType.lcd.value:
            if not self._finish_lcd:
                expected_echo = self.cmd_lcd_rgb
                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo)
                if obj is not None:
                    self._finish_lcd = True
                    self._waiting_lcd_cmd = False
                    print(">>>>>>>>收到 LCD 确认 JSON:", json.dumps(obj, ensure_ascii=False))

        if self.currentTestIndex == self.TestType.btn.value:
            if not self._finish_btn:
                expected_status = "ok"
                keys = ["confirm_pressed", "return_pressed", "select_pressed"]
                res = self.contains_confirmation2(self._recv_accum,expected_echo=None,expected_status=expected_status,keys=keys)
                if res is not None:
                    parsed, end_index = res
                    if not self.confirm_pressed:
                        self.confirm_pressed = parsed.get("confirm_pressed")
                    if not self.return_pressed:
                        self.return_pressed = parsed.get("return_pressed")
                    if not self.select_pressed:
                        self.select_pressed = parsed.get("select_pressed")

                    if self.confirm_pressed and self.return_pressed and self.select_pressed:
                        self._finish_btn = True
                        self._waiting_btn_cmd = False
                    # 截断缓冲
                    self._recv_accum = self._recv_accum[end_index:]
                    print(">>>>>>>>收到 功能按键确认 JSON:", json.dumps(res, ensure_ascii=False))



        if self.currentTestIndex == self.TestType.tf.value:
            if not self._finish_tf:
                expected_echo = self.cmd_tf
                expected_json = {"status": "ok"}

                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self._finish_tf = True
                    self._waiting_tf_cmd = False
                    self.test_tf_result = True
                    print(">>>>>>>>收到 TF卡确认 JSON:", json.dumps(obj, ensure_ascii=False))

                expected_json = {"status": "error"}
                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self._finish_tf = True
                    self._waiting_tf_cmd = False
                    self.test_tf_result = False
                    print(">>>>>>>>收到 TF卡确认 JSON:", json.dumps(obj, ensure_ascii=False))

        if self.currentTestIndex == self.TestType.i2c.value:
            if not self._finish_i2c:
                expected_status = "ok"
                keys = ["devices"]
                res = self.contains_confirmation2(self._recv_accum, expected_echo=None,expected_status=expected_status, keys=keys)
                if res is not None:
                    parsed, end_index = res
                    device_list = parsed.get("devices", [])
                    # 判断是列表，并且恰好5个i2c地址
                    if isinstance(device_list, list) and len(device_list) == 5:
                        self._finish_i2c = True
                        self._waiting_i2c_cmd = False
                        self.test_i2c_result = True

                    if isinstance(device_list, list) and len(device_list) > 1 and len(device_list) < 5:
                        self._finish_i2c = True
                        self._waiting_i2c_cmd = False
                        self.test_i2c_result = True
                        self.Is_Pass_Or_Ng(False)

                    # 截断缓冲，无论地址数量是否达标，这条报文都消费掉
                    self._recv_accum = self._recv_accum[end_index:]
                    print(">>>>>>>>收到 I2C扫描确认, devices:", device_list)


        if self.currentTestIndex == self.TestType.adc.value:
            if not self._finish_adc:
                expected_status = "success"
                keys = ["sound_raw_avg", "sound_raw_max", "sound_mv_avg", "samples"]
                res = self.contains_confirmation2(self._recv_accum,expected_echo=None,expected_status=expected_status,keys=keys)
                if res is not None:
                    parsed, end_index = res
                    raw_avg = parsed.get("sound_raw_avg")
                    raw_max = parsed.get("sound_raw_max")
                    mv_avg = parsed.get("sound_mv_avg")
                    samples = parsed.get("samples")
                    if raw_avg and raw_max and mv_avg and samples:
                        self._finish_adc = True
                        self._waiting_adc_cmd = False
                        self.test_adc_result = True
                    # 截断缓冲
                    self._recv_accum = self._recv_accum[end_index:]
                    print(">>>>>>>>收到 ADC确认:", raw_avg, raw_max, mv_avg, samples)

        if self.currentTestIndex == self.TestType.msg.value:
            if not self._finish_msg:
                expected_echo = self.cmd_msg
                keys = ["light_lux", "accel", "gyro"]
                res = self.contains_confirmation2(self._recv_accum, expected_echo=expected_echo,expected_status="ok", keys=keys)
                if res is not None:
                    parsed, end_index = res
                    self.light = parsed.get("light_lux")
                    self.accel = parsed.get("accel")  # 期望 list/tuple
                    self.gyro  = parsed.get("gyro")
                    self._recv_accum = self._recv_accum[end_index:]


                    bad = False
                    errorInfo = ""
                    if self.light == 0.00:
                        errorInfo = f"光线传感器异常\n{self.light}\n测试次数:{self.currentMsgNum}"
                        bad = True
                    if not bad:
                        if isinstance(self.accel, (list, tuple)) and all(x == 0.00 for x in self.accel):
                            errorInfo = f"加速度传感器异常\n{self.accel}\n测试次数:{self.currentMsgNum}"
                            bad = True
                    if not bad:
                        if isinstance(self.gyro, (list, tuple)) and all(x == 0.00 for x in self.gyro):
                            errorInfo = f"陀螺仪异常\n{self.gyro}\n测试次数:{self.currentMsgNum}"
                            bad = True


                    self._waiting_msg_cmd = False
                    #bad = False
                    self.currentMsgNum += 1
                    if bad:
                        self._msg_retry_num += 1
                        print("存在 0 值")
                    else:
                        self._msg_Through_num += 1

                    if self._msg_retry_num > 3:
                        self.Is_Pass_Or_Ng(False, errorInfo)

                    if self._msg_Through_num > 3:
                        self._finish_msg = True
                        self.test_msg_result = True

                    print(">>>>>>>>收到 六轴确认:", self.light, self.accel, self.gyro)


        if self.currentTestIndex == self.TestType.wifi.value:
            if not self._finish_read_mac:
                expected_status = "ok"
                keys = ["ip", "rssi"]
                res = self.contains_confirmation2(self._recv_accum, expected_echo=None, expected_status=expected_status,keys=keys)
                if res is not None:
                    parsed, end_index = res
                    ip = parsed.get("ip")
                    self.rssi = parsed.get("rssi")
                    if self.rssi >= -70:
                    #if self.rssi >= -100:
                        self._finish_wifi = True
                        self._waiting_wifi_cmd = False
                        self.test_wifi_result = True
                    print(">>>>>>>>收到 WIFI确认:", ip, self.rssi)


        if self.currentTestIndex == self.TestType.mes.value:
            if not self.mac:
                expected_echo = self.cmd_read_mac
                expected_status = "ok"
                # 不给 keys -> 返回完整解析的 JSON 对象
                res = self.contains_confirmation2(self._recv_accum,
                                                  expected_echo=expected_echo,
                                                  expected_status=expected_status,
                                                  keys=None)  # or just omit keys parameter
                if res is not None:
                    parsed, end_index = res
                    mac = parsed.get("mac")
                    if mac:
                        self.mac = mac
                    # 截断缓冲
                    self._recv_accum = self._recv_accum[end_index:]
                    print(">>>>>>>>收到 MAC确认:", mac)

        if self.currentTestIndex == self.TestType.writeSn.value:
            if not self.is_finish_write_sn_code:
                expected_status = "ok"

                if not self.write_sn_code:
                    # 阶段1：只处理带sn字段的ok报文
                    res = self.contains_confirmation2(self._recv_accum, expected_echo=None,
                                                      expected_status=expected_status, keys=None)
                    if res is not None:
                        parsed, end_index = res
                        # 关键：必须要有sn字段才认为是本阶段有效包
                        sn = parsed.get("sn")
                        if sn is not None:
                            if sn == self.sn:
                                self.write_sn_code = True
                                print(">>>>>>>>收到 SN码确认:", sn)
                        else:
                            # 当前阶段不需要这个包，但是仍然消费掉，清掉缓冲区旧垃圾包
                            self._recv_accum = self._recv_accum[end_index:]

                else:
                    # 阶段2：只处理带device_secret字段的ok报文
                    res = self.contains_confirmation2(self._recv_accum, expected_echo=None,
                                                      expected_status=expected_status, keys=None)
                    if res is not None:
                        parsed, end_index = res
                        code = parsed.get("device_secret")
                        if code is not None:
                            if code == self.code:
                                self.is_finish_write_sn_code = True
                                print(">>>>>>>>收到 设备密钥码确认:", code)
                        else:
                            # 这是旧sn应答包，消费丢弃，清缓冲区，防止卡死
                            self._recv_accum = self._recv_accum[end_index:]



    # 提取 echo+json 配对（按回显后紧随的 JSON）
    def extract_echo_json_pairs(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        pairs: List[Tuple[str, Dict[str, Any]]] = []
        for m in re.finditer(r'(^|\r?\n)\s*(tool\s+call[^\r\n]+)\s*(\r?\n|$)', text, re.I):
            echo = m.group(2).strip()
            search_start = m.end()
            jm = re.search(r'\{.*?\}', text[search_start:], re.S)
            if not jm:
                continue
            jtext = jm.group(0)
            try:
                obj = json.loads(jtext)
            except Exception:
                continue
            pairs.append((echo, obj))
        return pairs

    def json_matches(self, obj: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        def _match_val(val, exp) -> bool:
            if callable(exp):
                try:
                    return bool(exp(val))
                except Exception:
                    return False
            if isinstance(exp, dict):
                if not isinstance(val, dict):
                    return False
                return all(_match_val(val.get(k), v) for k, v in exp.items())
            if isinstance(exp, (list, tuple)):
                if not isinstance(val, (list, tuple)) or len(val) != len(exp):
                    return False
                return all(_match_val(a, b) for a, b in zip(val, exp))
            try:
                return val == exp
            except Exception:
                return False
        return all(_match_val(obj.get(k), v) for k, v in expected.items())


    def extract_json_objects(self, text: str) -> List[Dict[str, Any]]:
        """返回文本中能解析的所有 JSON 对象（按出现顺序）。"""
        objs: List[Dict[str, Any]] = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append(obj)
            except Exception:
                continue
        return objs

    def json_matches(self, obj: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """
        宽松匹配：expected 的值可以是常量、可调用或 'true'/'false' 字符串。
        - 如果 expected 为 'true'/'false'（字符串），会接受 obj 中为 True/False 或 "true"/"false" 或 1/0。
        - 数字/字符串会用 str() 比较（便于 "119" vs 119 的情况）。
        - 嵌套 dict/list 会递归比较。
        """

        def _match_val(val, exp) -> bool:
            # callable
            if callable(exp):
                try:
                    return bool(exp(val))
                except Exception:
                    return False

            # expected is 'true'/'false' string -> accept bool/str/int
            if isinstance(exp, str) and exp.lower() in ("true", "false"):
                exp_bool = (exp.lower() == "true")
                if isinstance(val, bool):
                    return val == exp_bool
                if isinstance(val, str):
                    return val.lower() == exp.lower()
                if isinstance(val, (int, float)):
                    # treat 0 as False, others as True
                    return bool(val) == exp_bool
                return False

            # nested dict
            if isinstance(exp, dict):
                if not isinstance(val, dict):
                    return False
                return all(_match_val(val.get(k), v) for k, v in exp.items())

            # list/tuple expected
            if isinstance(exp, (list, tuple)):
                if not isinstance(val, (list, tuple)) or len(val) != len(exp):
                    return False
                return all(_match_val(a, b) for a, b in zip(val, exp))

            # loose numeric/string compare: try direct equality first, then str() compare
            try:
                if val == exp:
                    return True
            except Exception:
                pass
            try:
                return str(val) == str(exp)
            except Exception:
                return False

        return all(_match_val(obj.get(k), v) for k, v in expected.items())

    def extract_json_objects_positions(self, text: str) -> List[Tuple[Dict[str, Any], int, int]]:
        objs = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            start = m.start()
            end = m.end()
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append((obj, start, end))
            except Exception:
                continue
        return objs

    def contains_confirmation(self, text: str,
                              expected_echo: Optional[str] = None,
                              expected_json: Optional[Dict[str, Any]] = None) -> Optional[Tuple[Dict[str, Any], int]]:

        # Helper json match (reuse your json_matches if present)
        def _json_ok(obj, exp) -> bool:
            if exp is None:
                return obj.get("status") == "ok"
            return self.json_matches(obj, exp)

        # Case A: expected_echo specified -> find occurrences of that literal substring
        if expected_echo is not None:
            # find all literal occurrences (not regex) to be robust
            start_pos = 0
            esc = re.escape(expected_echo)
            for m in re.finditer(esc, text):
                # search for first JSON after this echo occurrence
                search_start = m.end()
                jm = re.search(r'\{.*?\}', text[search_start:], re.S)
                if not jm:
                    continue
                json_text = jm.group(0)
                json_abs_end = search_start + jm.end()
                try:
                    obj = json.loads(json_text)
                except Exception:
                    continue
                if _json_ok(obj, expected_json):
                    return obj, json_abs_end
            return None

        # Case B: expected_echo is None -> JSON-only scan
        json_objs = self.extract_json_objects_positions(text)
        if not json_objs:
            return None
        for obj, start, end in json_objs:
            if _json_ok(obj, expected_json):
                return obj, end
        return None


    def extract_json_objects_positions(self, text: str) -> List[Tuple[Dict[str, Any], int, int]]:
        """返回文本中所有可解析 JSON 的三元组 (obj, start_index, end_index)。"""
        objs: List[Tuple[Dict[str, Any], int, int]] = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            start = m.start()
            end = m.end()
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append((obj, start, end))
            except Exception:
                continue
        return objs

    def extract_echo_json_pairs_positions(self, text: str) -> List[Tuple[str, Dict[str, Any], int, int]]:
        """
        返回所有 (echo, json_obj, echo_start_index, json_end_index)
        echo_start_index 以便需要时做更精确的截断或调试
        """
        pairs: List[Tuple[str, Dict[str, Any], int, int]] = []
        for m in re.finditer(r'(^|\r?\n)\s*(tool\s+call[^\r\n]+)\s*(\r?\n|$)', text, re.I):
            echo = m.group(2).strip()
            echo_start = m.start(2)
            search_start = m.end()
            jm = re.search(r'\{.*?\}', text[search_start:], re.S)
            if not jm:
                continue
            json_abs_start = search_start + jm.start()
            json_abs_end = search_start + jm.end()
            jtext = jm.group(0)
            try:
                obj = json.loads(jtext)
            except Exception:
                continue
            pairs.append((echo, obj, echo_start, json_abs_end))
        return pairs

    def contains_confirmation2(self,
                               text: str,
                               expected_echo: Optional[str] = None,
                               expected_status: Optional[str] = None,
                               keys: Optional[List[str]] = None
                               ) -> Optional[Tuple[Dict[str, Any], int]]:

        def to_number(v) -> Optional[float]:
            if v is None:
                return None
            if isinstance(v, bool):
                return 1.0 if v else 0.0
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                s = v.strip()
                # try direct float
                try:
                    return float(s)
                except Exception:
                    pass
                # try extract first numeric substring
                m = re.search(r'-?\d+(?:\.\d+)?', s)
                if m:
                    try:
                        return float(m.group(0))
                    except Exception:
                        return None
                return None
            return None

        def to_number_or_array(v):
            # if list/tuple => convert each element
            if isinstance(v, (list, tuple)):
                nums = []
                for e in v:
                    ne = to_number(e)
                    if ne is None:
                        return None
                    nums.append(ne)
                return nums
            # scalar
            return to_number(v)

        # helper to check status
        def status_ok(obj):
            if expected_status is None:
                return True
            s = obj.get("status")
            if s is None:
                return False
            return str(s).lower() == str(expected_status).lower()

        # Mode A: echo specified -> find occurrences and pair with next JSON
        if expected_echo is not None:
            esc = re.escape(expected_echo)
            for m in re.finditer(esc, text):
                search_start = m.end()
                jm = re.search(r'\{.*?\}', text[search_start:], re.S)
                if not jm:
                    continue
                json_text = jm.group(0)
                json_end = search_start + jm.end()
                try:
                    obj = json.loads(json_text)
                except Exception:
                    continue
                if not status_ok(obj):
                    continue
                # if no keys requested, return full obj
                if not keys:
                    return obj, json_end
                result: Dict[str, Any] = {}
                ok = True
                for k in keys:
                    if k not in obj:
                        ok = False
                        break
                    val = to_number_or_array(obj.get(k))
                    if val is None:
                        ok = False
                        break
                    result[k] = val
                if ok:
                    return result, json_end
            return None

        # Mode B: JSON-only scan
        json_objs = self.extract_json_objects_positions(text)
        if not json_objs:
            return None
        for obj, start, end in json_objs:
            if not status_ok(obj):
                continue
            if not keys:
                return obj, end
            result: Dict[str, Any] = {}
            ok = True
            for k in keys:
                if k not in obj:
                    ok = False
                    break
                val = to_number_or_array(obj.get(k))
                if val is None:
                    ok = False
                    break
                result[k] = val
            if ok:
                return result, end
        return None

    def parse_sequential_ext_pin_levels(self,
                                        text: str,
                                        pins: Optional[List[str]] = None,
                                        command_keyword: str = "test_ext_pin",
                                        expected_status: Optional[str] = "ok"
                                        ) -> Optional[Tuple[List[int], int]]:
        if pins is None:
            pins = ["P0", "P1", "P2", "P3"]
        cur = 0
        levels: List[int] = []
        # 宽松匹配每一条 echo（允许有前缀如 "x_card> "）
        for pin in pins:
            # 找到包含 command_keyword 且包含 pin=Px 的 echo 行（从 cur 开始）
            pat = re.compile(r'(^|\r?\n)([^\r\n]*\btool\s+call\s+' + re.escape(command_keyword) +
                             r'[^\r\n]*\bpin=' + re.escape(pin) + r'\b[^\r\n]*)', re.I)
            m = pat.search(text, cur)
            if not m:
                return None
            echo_end = m.end(2)
            # 在 echo 之后寻找第一个完整 JSON
            jm = re.search(r'\{.*?\}', text[echo_end:], re.S)
            if not jm:
                return None
            json_text = jm.group(0)
            json_end = echo_end + jm.end()
            # 解析 JSON
            try:
                obj = json.loads(json_text)
            except Exception:
                return None
            # 检查 status（如配置）
            if expected_status is not None:
                s = obj.get("status")
                if s is None or str(s).lower() != str(expected_status).lower():
                    return None
            # 确认 JSON 中的 pin 与期望 pin 匹配（更稳健）
            obj_pin = obj.get("pin")
            if obj_pin is None or str(obj_pin).upper() != pin.upper():
                return None
            # 提取 level 并转为 int
            lev = obj.get("level")
            try:
                level_int = int(lev)
            except Exception:
                try:
                    level_int = int(float(str(lev).strip()))
                except Exception:
                    return None
            levels.append(level_int)
            # 下一次从当前 json 结束位置继续查找（保证顺序）
            cur = json_end
        # 全部找到
        return levels, cur

    def run(self):
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._periodic_check)
        self._check_timer.start(100)
        self.exec_()
        if self.isOpenPort:
            self._close_serial()


    def _periodic_check(self):
        try:
            self.signal_get_work_com.emit(self.work)
        except Exception:
            pass
        if not self.isStart:
            if self.isOpenPort:
                print("isStart False，关闭端口")
                self._close_serial()
            return
        if self.isStart and not self.isOpenPort:
            if not self.port:
                return
            available = [p.portName() for p in QSerialPortInfo.availablePorts()]
            if self.port in available:
                self.open_serial_link()
            else:
                pass
        else:
            if self.isOpenPort and self.serial and self.serial.portName() != self.port:
                self.signal_set_ui_page.emit(self.work,False, 2, "", "")
                print("端口名称变化，重启串口")
                self._close_serial()

    def stop(self):
        # 停止检查定时器
        try:
            if self._check_timer and self._check_timer.isActive():
                self._check_timer.stop()
        except Exception:
            pass

        # 停止写定时器（立即）
        try:
            self._stop_periodic_write()
        except Exception:
            pass

        # 确保在串口所属线程中同步关闭串口（若已打开）
        try:
            if self.isOpenPort:
                if QThread.currentThread() == self.thread():
                    # 已经在本线程，直接关闭
                    self._close_serial()
                else:
                    # 在其它线程（通常是主线程）调用，使用阻塞队列调用确保 _close_serial 在本线程执行完
                    QMetaObject.invokeMethod(self, "_close_serial", Qt.BlockingQueuedConnection)
        except Exception:
            # 兜底
            try:
                self._close_serial()
            except Exception:
                pass

        # 退出事件循环并等待线程结束（短等待）
        try:
            self.quit()
            # 等待线程退出一段时间以让 deleteLater/清理完成
            self.wait(500)  # 500 ms，可根据需要调整/移除
        except Exception:
            pass

#############################################################################################################

class BaseTest_Thread(QThread):
    signal_get_work_com = pyqtSignal(int)
    signal_set_ui_page = pyqtSignal(bool,int, str, str)
    signal_com_refresh = pyqtSignal(str, bool)
    signal_isPassOrNg =  pyqtSignal(bool)
    signal_isRetest = pyqtSignal(bool)

    def initVars(self):
        self._recv_accum = ""
        self.oldCurrentTestIndex = 0
        self.currentTestIndex = 0
        self._last_now = None

        self.motor_p0_is_unlock = -1
        self.motor_p0_state_0 = False
        self.motor_p0_state_1 = False

        self.motor_p1_is_unlock = -1
        self.motor_p1_state_0 = False
        self.motor_p1_state_1 = False

        self.servo_p2_is_unlock = -1
        self.servo_p2_state_0 = False
        self.servo_p2_state_1 = False

        self.servo_p3_is_unlock = -1
        self.servo_p3_state_0 = False
        self.servo_p3_state_1 = False


        self.m_p0_on_num = 0
        self.m_p0_off_num = 0
        self.m_p1_on_num = 0
        self.m_p1_off_num = 0

        self.m_p2_on_num = 0
        self.m_p2_off_num = 0
        self.m_p3_on_num = 0
        self.m_p3_off_num = 0

        self.i2c_retry_count = 0
        self.servo_retry_count = 0

        self.servoTestNum = random.choice([4, 5, 6])
        #self.servoTestNum = 6
        self.servo_current_num = 0


        self.motorTestNum = 5
        self.motor_current_num = 0

        self.base_powerNum = 5
        self.base_power_current_num = 0


        self.turn_state = False
        self.test_rgb_result = False
        self.test_lcd_result = False
        self.test_btn_result = False
        self.test_play_result = False
        self.test_tf_result = False
        self.test_adc_result = False
        self.test_msg_result = False
        self.test_wifi_result = False
        self._waiting_base_rgb_cmd = False

        self._sent_base_testing_cmd = False
        self._finish_base_testing = False
        self._waiting_base_testing_cmd = False

        self.base_motor_1_state = False
        self.base_motor_2_state = False
        self._finish_base_motor = False

        self._sent_btn_cmd = False
        self._finish_btn = False
        self._waiting_btn_cmd = False

        self._sent_tf_cmd = False
        self._finish_tf = False
        self._waiting_tf_cmd = False

        self._sent_play_cmd = False
        self._finish_play = False
        self._waiting_play_cmd = False

        self._sent_adc_cmd = False
        self._finish_adc = False
        self._waiting_adc_cmd = False

        self._sent_msg_cmd = False
        self._finish_msg = False
        self._waiting_msg_cmd = False

        self._sent_wifi_cmd = False
        self._finish_wifi = False
        self._waiting_wifi_cmd = False
        self._wifi_retry_num = 0

        self._sent_gpio_cmd = False
        self._finish_gpio = False
        self._waiting_gpio_cmd = False

        self._finish_base_power = False
        self._sent_base_power_cmd = False
        self._waiting_base_power_cmd = False

        self._finish_base_servo = False
        self._sent_base_servo_cmd = False
        self._waiting_base_servo_cmd = False

        self._sent_i2c_cmd = False
        self._waiting_i2c_cmd = False
        self._finish_i2c = False


    def __init__(self,test_mode):
        super(BaseTest_Thread, self).__init__()
        self.port = ""
        self.isStart = False
        self.isOpenPort = False
        self.serial = None
        self._check_timer = None
        self._write_timer = None
        self.test_mode = test_mode
        self.initVars()

        self.cmd_rgb = "tool call test_rgb r=50 g=50 b=50"
        self.cmd_motor_in = "tool call test_ext_pin pin=P0 mode=in\ntool call test_ext_pin pin=P1 mode=in\n"
        self.cmd_servo_in = "tool call test_ext_pin pin=P2 mode=in\ntool call test_ext_pin pin=P3 mode=in\n"
        self.cmd_base_rgb = "tool call control_ext_rgb module=base index=-1 r=50 g=50 b=50"
        self.cmd_base_testing = "tool call test_power"


        self.cmd_motor_foreward = "tool call control_ext_motor motor_num=1 speed=-80\ntool call control_ext_motor motor_num=2 speed=80\ntool call control_ext_motor motor_num=1 speed=-80\ntool call control_ext_motor motor_num=2 speed=80\n"
        self.cmd_motor_reversal = "tool call control_ext_motor motor_num=1 speed=80\ntool call control_ext_motor motor_num=2 speed=-80\ntool call control_ext_motor motor_num=1 speed=80\ntool call control_ext_motor motor_num=2 speed=-80\n"
        self.cmd_motor_stop = "tool call control_ext_motor motor_num=1 speed=0\ntool call control_ext_motor motor_num=2 speed=0"

        self.cmd_servo_turn = "tool call control_ext_servo servo_num=1 angle=105.0\ntool call control_ext_servo servo_num=2 angle=110.0"
        self.cmd_servo_stop = "tool call control_ext_servo servo_num=1 angle=0.0\ntool call control_ext_servo servo_num=2 angle=0.0"
        self.cmd_base_power = "tool call control_base_power enable=true"
        self.cmd_i2c = "i2c_scan"

        self.signal_com_refresh.connect(self.set_work_code)
        self.signal_isPassOrNg.connect(self.Is_Pass_Or_Ng)

        self.signal_isRetest.connect(self.Is_Retest)


    def set_work_code(self, com, isStart):
        if com and com != self.port and self.isOpenPort:
            try:
                if QThread.currentThread() == self.thread():
                    self._close_serial()
                else:
                    QMetaObject.invokeMethod(self, "_close_serial", Qt.BlockingQueuedConnection)
            except Exception:
                # 兜底：尝试直接关闭
                try:
                    self._close_serial()
                except Exception:
                    pass

        # 更新端口与启动标志
        self.port = com
        self.isStart = isStart


    def Is_Pass_Or_Ng(self, var):
        if self.test_mode == 0 or self.test_mode == 1:
            if self.currentTestIndex == 1:
                if var:
                    self.currentTestIndex += 1
                else:
                    self.signal_set_ui_page.emit(False, 1, "RGB灯异常", "")
                    self.currentTestIndex = -1

            if self.currentTestIndex == 2 and self._finish_base_motor:
                if var:
                    self.currentTestIndex += 1
                else:
                    self.signal_set_ui_page.emit(False, 1, "电机转动异常", "")
                    self.currentTestIndex = -1


    def Is_Retest(self, var):
        self.signal_set_ui_page.emit(False, 2, "", "")
        self.initVars()

    def open_serial_link(self):
        if not self.port:
            print("open_serial_link: 未指定端口")
            return False

        available = [p.portName() for p in QSerialPortInfo.availablePorts()]
        if self.port not in available:
            print(f"open_serial_link: 请求的端口 {self.port} 不在可用端口列表: {available}")
            return False

        try:
            if self.serial is not None:
                self._close_serial()

            self.serial = QSerialPort()
            self.serial.setPortName(self.port)
            self.serial.setBaudRate(115200)
            self.serial.setDataBits(QSerialPort.Data8)
            self.serial.setParity(QSerialPort.NoParity)
            self.serial.setStopBits(QSerialPort.OneStop)
            self.serial.setFlowControl(QSerialPort.NoFlowControl)

            if self.serial.open(QIODevice.ReadWrite):
                print(f"\n成功打开串口: {self.port}")
                self.signal_set_ui_page.emit(False, 2, "", "")
                try:
                    self.serial.clear()
                except Exception:
                    pass
                time.sleep(0.05)

                try:
                    self.serial.readyRead.connect(self.on_serial_read)
                except Exception as e:
                    print("readyRead connect 异常:", e)

                # reset states
                self.initVars()
                self._recv_accum = ""
                self.isOpenPort = True
                QTimer.singleShot(2000, self._start_periodic_write)  # 延迟 2s 启动写定时器
                return True
            else:
                print(f"\n打开串口失败: {self.port}")
                self.isOpenPort = False
                return False
        except Exception as e:
            print("open_serial_link 异常:", e)
            self.isOpenPort = False
            return False

    def _close_serial(self):
        # 1) 停写定时器，避免并发写
        try:
            self._stop_periodic_write()
        except Exception:
            pass

        # 2) 标记端口已关闭，避免其它逻辑再尝试写
        self.isOpenPort = False

        if not self.serial:
            return

        try:
            # 3) 断开信号
            try:
                self.serial.readyRead.disconnect(self.on_serial_read)
            except Exception:
                pass

            # 4) 嘗試短等待 pending bytes 写入排空（可选，短超时）
            try:
                self.serial.waitForBytesWritten(200)  # 200 ms
            except Exception:
                pass

            # 5) 清理缓冲
            try:
                self.serial.clear()
            except Exception:
                pass

            # 6) 关闭端口
            try:
                self.serial.close()
            except Exception:
                pass

            # 7) 释放引用（不要依赖 deleteLater 必须由事件循环处理）
            try:
                self.serial = None
            except Exception:
                self.serial = None

        finally:
            # 8) 重置状态标志（按需）
            self._sent_rgb_cmd = False
            self._waiting_rgb_cmd = False
            self._last_now = 0.0
            # ... 重置其它标志 ...
            self._recv_accum = ""
            self.isOpenPort = False

    def _start_periodic_write(self):
        if not self.isOpenPort or self.serial is None:
            return
        if self._write_timer is None:
            self._write_timer = QTimer()
            self._write_timer.timeout.connect(self._on_write_timer)
            self._write_timer.start(100)

    def _stop_periodic_write(self):
        if self._write_timer is not None:
            try:
                if self._write_timer.isActive():
                    self._write_timer.stop()
            except Exception:
                pass
            try:
                self._write_timer.timeout.disconnect(self._on_write_timer)
            except Exception:
                pass
            self._write_timer = None
            print("写入定时器已停止")

    # 指令发送
    def _on_write_timer(self):
        if not self.isOpenPort or self.serial is None:
            self._stop_periodic_write()
            return

        now = time.time()

        if self.test_mode == 0:
            if self.currentTestIndex == 0:
                t_testPro = "测试项目" + str(self.currentTestIndex)
                t_cmd = self.cmd_base_testing
                if not self._finish_base_testing:
                    self.signal_set_ui_page.emit(False, 2, "","")
                    cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                    if (not self._waiting_base_testing_cmd) or (now - self._last_now > 1.0):
                        try:
                            bytes_written = self.serial.write(cmd_bytes)
                            try:
                                self.serial.waitForBytesWritten(200)
                            except Exception:
                                pass
                            self._sent_base_testing_cmd = True
                            self._waiting_base_testing_cmd = True
                            self._last_now = now
                            print(f"[发送] 底座检测 cmd={t_cmd} bytes={bytes_written}")
                        except Exception:
                            print(f"[发送失败] 底座检测 cmd={t_cmd}")
                else:
                    self.currentTestIndex += 1

            if self.currentTestIndex == 1:
                t_testPro = "测试项目" + str(self.currentTestIndex)
                t_cmd = self.cmd_base_rgb
                self.signal_set_ui_page.emit(True, 3, t_testPro, "\n << < 人工查看 >> >\n\n[RGB灯]\n\n\n是否点亮?")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_base_rgb_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._waiting_base_rgb_cmd = True
                        self._last_now = now
                        print(f"[发送] 底座RGB cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 底座RGB cmd={t_cmd}")

            if self.currentTestIndex == 2:
                if self.motor_current_num >= self.motorTestNum:
                    self._finish_base_motor = True

                t_testPro = "测试项目" + str(self.currentTestIndex)
                if not self._finish_base_motor:
                    if self.turn_state:
                        t_cmd = self.cmd_motor_foreward
                        self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n\n[人工查看电机正转]\n[测试次数]:{self.motor_current_num}/{self.motorTestNum}\n[电机1]:是否正常转动?\n[电机2]:是否正常转动?")
                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (now - self._last_now >= 2):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(100)
                                    self.motor_current_num += 1
                                except Exception:
                                    pass

                                self._last_now = now
                                self.turn_state = not self.turn_state
                                print(f"[发送] 电机正传 cmd={t_cmd} bytes={bytes_written}")

                            except Exception:
                                print(f"[发送失败] 电机正传 cmd={t_cmd}")
                    else:
                        t_cmd = self.cmd_motor_reversal
                        self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n\n[人工查看电机反转]\n[测试次数]:{self.motor_current_num}/{self.motorTestNum}\n[电机1]:是否正常转动?\n[电机2]:是否正常转动?")
                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (now - self._last_now >= 2):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(100)
                                    self.motor_current_num += 1
                                except Exception:
                                    pass

                                self._last_now = now
                                self.turn_state = not self.turn_state
                                print(f"[发送] 电机反传 cmd={t_cmd} bytes={bytes_written}")

                            except Exception:
                                print(f"[发送失败] 电机反传 cmd={t_cmd}")
                else:
                    t_cmd = self.cmd_motor_stop
                    cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        self.serial.waitForBytesWritten(1)
                        print(f"[发送] 电机停止 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 电机停止 cmd={t_cmd}")
                        pass
                    self.signal_set_ui_page.emit(True, 3, t_testPro,"\n << < 人工评判 >> >\n\n[电机1]:是否正常转动?\n[电机2]:是否正常转动?")

            if self.currentTestIndex == 3:
                if not self._finish_base_power:
                    t_testPro = "测试项目" + str(self.currentTestIndex)
                    t_cmd = self.cmd_base_power
                    self.signal_set_ui_page.emit(False, 3, t_testPro, "\n\n\n\n\n[金手指供电开启]\n")
                    cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                    if (not self._waiting_base_power_cmd) or (now - self._last_now > 2.0):
                        try:
                            bytes_written = self.serial.write(cmd_bytes)
                            try:
                                self.serial.waitForBytesWritten(1000)
                                self.base_power_current_num += 1
                            except Exception:
                                pass
                            self._sent_base_power_cmd = True
                            self._waiting_base_power_cmd = True
                            self._last_now = now
                            print(f"[发送] 金手指供电开启 cmd={t_cmd} bytes={bytes_written}")
                        except Exception:
                            print(f"[发送失败] 金手指供电开启 cmd={t_cmd}")
                else:
                    self.turn_state = False
                    self.currentTestIndex += 1

                if self.base_power_current_num >= self.base_powerNum:
                    self.signal_set_ui_page.emit(False, 1, "金手指供电开启异常", "")
                    self.currentTestIndex = -1

            if self.currentTestIndex == 4:
                if self.servo_current_num > self.servoTestNum:
                    self._finish_base_servo = True

                if not self._finish_base_servo:
                    t_testPro = "测试项目" + str(self.currentTestIndex)
                    if not self.turn_state:
                        t_cmd = self.cmd_servo_turn
                        #self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n[舵机归位自检]\n[测试次数]:{self.servo_current_num}/{self.servoTestNum}\n[舵机1]: 转动[{self.servo_p2_state_0}], 归零[{self.servo_p2_state_1}]\n[舵机2]: 转动[{self.servo_p3_state_0}], 归零[{self.servo_p3_state_1}]")
                        self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n[舵机归位自检]\n[测试次数]:{self.servo_current_num}")

                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (now - self._last_now > 1.0):
                            bytes_written = self.serial.write(cmd_bytes)
                            try:
                                self.serial.waitForBytesWritten(1000)
                                self.servo_current_num += 1
                                print(f"[发送] 舵机转动 cmd={t_cmd} bytes={bytes_written}")
                            except Exception:
                                print(f"[发送失败] 舵机转动 cmd={t_cmd}")

                            self._last_now = now
                            self.turn_state = not self.turn_state

                    else:
                        t_cmd = self.cmd_servo_stop
                        #self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n[舵机转动自检]\n[测试次数]:{self.servo_current_num}/{self.servoTestNum}\n[舵机1]: 转动[{self.servo_p2_state_0}], 归零[{self.servo_p2_state_1}]\n[舵机2]: 转动[{self.servo_p3_state_0}], 归零[{self.servo_p3_state_1}]")
                        self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n[舵机转动自检]\n[测试次数]:{self.servo_current_num}")
                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (now - self._last_now > 1.0):
                            bytes_written = self.serial.write(cmd_bytes)
                            try:
                                self.serial.waitForBytesWritten(1000)
                                self.servo_current_num += 1
                                print(f"[发送] 舵机归位自检 cmd={t_cmd} bytes={bytes_written}")
                            except Exception:
                                print(f"[发送失败] 舵机归位自检 cmd={t_cmd}")
                                pass

                            self._last_now = now
                            self.turn_state = not self.turn_state
                else:
                    self.currentTestIndex += 1


            # if self.currentTestIndex == 5:
            #     if not self._finish_i2c:
            #         t_testPro = "测试项目" + str(self.currentTestIndex)
            #         t_cmd = self.cmd_i2c
            #         self.signal_set_ui_page.emit(False, 3, t_testPro, "\n\n\n\n\n[I2C自检]\n")
            #         cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
            #         if (not self._waiting_i2c_cmd) or (now - self._last_now > 3.0):
            #             try:
            #                 bytes_written = self.serial.write(cmd_bytes)
            #                 try:
            #                     self.serial.waitForBytesWritten(500)
            #                 except Exception:
            #                     pass
            #                 self._sent_i2c_cmd = True
            #                 self._waiting_i2c_cmd = True
            #                 self._last_now = now
            #                 self.i2c_retry_count += 1
            #                 print(f"[发送] I2C自检 cmd={t_cmd} bytes={bytes_written}")
            #             except Exception:
            #                 print(f"[发送失败] I2C自检 cmd={t_cmd}")
            #     else:
            #         self.currentTestIndex += 1
            #     # if self.i2c_retry_count >= 5:
            #     #     self.currentTestIndex = -1
            #     #     self.signal_set_ui_page.emit(False, 1, "I2C异常\n", "")

            if self.currentTestIndex == 5:
                self.signal_set_ui_page.emit(False, 0, "测试通过", "")
                t_cmd = self.cmd_base_testing
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (now - self._last_now > 0.5):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._last_now = now
                        print(f"[发送] 底座断开检测 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 底座断开检测 cmd={t_cmd}")
        else:
            if self.currentTestIndex == 0:
                t_testPro = "测试项目" + str(self.currentTestIndex)
                t_cmd = self.cmd_base_testing
                if not self._finish_base_testing:
                    self.signal_set_ui_page.emit(False, 2, "","")
                    cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                    if (not self._waiting_base_testing_cmd) or (now - self._last_now > 1.0):
                        try:
                            bytes_written = self.serial.write(cmd_bytes)
                            try:
                                self.serial.waitForBytesWritten(200)
                            except Exception:
                                pass
                            self._sent_base_testing_cmd = True
                            self._waiting_base_testing_cmd = True
                            self._last_now = now
                            print(f"[发送] 底座检测 cmd={t_cmd} bytes={bytes_written}")
                        except Exception:
                            print(f"[发送失败] 底座检测 cmd={t_cmd}")
                else:
                    self.currentTestIndex += 1

            if self.currentTestIndex == 1:
                t_testPro = "测试项目" + str(self.currentTestIndex)
                t_cmd = self.cmd_base_rgb
                self.signal_set_ui_page.emit(True, 3, t_testPro, "\n << < 人工查看 >> >\n\n[RGB灯]\n\n\n是否点亮?")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_base_rgb_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._waiting_base_rgb_cmd = True
                        self._last_now = now
                        print(f"[发送] 底座RGB cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 底座RGB cmd={t_cmd}")

            if self.currentTestIndex == 2:
                if self.motor_current_num > self.motorTestNum:
                    self._finish_base_motor = True

                if not self._finish_base_motor:
                    t_testPro = "测试项目" + str(self.currentTestIndex)
                    if self.turn_state:
                        t_cmd = self.cmd_motor_foreward
                        self.signal_set_ui_page.emit(False, 3, t_testPro, f"\n\n\n\n\n[电机I2C自检]\n[测试次数]:{self.motor_current_num}/{self.motorTestNum}")
                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (now - self._last_now >= 1):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(100)
                                    self.motor_current_num += 1
                                except Exception:
                                    pass

                                self._last_now = now
                                self.turn_state = not self.turn_state
                                print(f"[发送] 电机正传 cmd={t_cmd} bytes={bytes_written}")

                            except Exception:
                                print(f"[发送失败] 电机正传 cmd={t_cmd}")
                    else:
                        t_cmd = self.cmd_motor_reversal
                        self.signal_set_ui_page.emit(False, 3, t_testPro,f"\n\n\n\n\n[电机I2C自检]\n[测试次数]:{self.motor_current_num}/{self.motorTestNum}")
                        cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                        if (now - self._last_now >= 1):
                            try:
                                bytes_written = self.serial.write(cmd_bytes)
                                try:
                                    self.serial.waitForBytesWritten(100)
                                    self.motor_current_num += 1
                                except Exception:
                                    pass

                                self._last_now = now
                                self.turn_state = not self.turn_state
                                print(f"[发送] 电机反传 cmd={t_cmd} bytes={bytes_written}")

                            except Exception:
                                print(f"[发送失败] 电机反传 cmd={t_cmd}")
                else:
                    self.currentTestIndex += 1
                    self._recv_accum = ""

            if self.currentTestIndex == 3:
                self.signal_set_ui_page.emit(False, 0, "测试通过", "")
                t_cmd = self.cmd_base_testing
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (now - self._last_now > 0.5):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._last_now = now
                        print(f"[发送] 底座断开检测 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 底座断开检测 cmd={t_cmd}")



    # 指令接收
    def on_serial_read(self):
        if not self.serial:
            return
        try:
            qba = self.serial.readAll()
            chunk = qba.data() if hasattr(qba, "data") else bytes(qba)
        except Exception:
            chunk = b''
            print("serial.readAll() 读取异常")
        if not chunk:
            return
        try:
            recv_str = chunk.decode('utf-8', errors='replace')
        except Exception:
            recv_str = ''
            print("recv data decode err")

        self._recv_accum += recv_str
        if len(self._recv_accum) > 8192:
            self._recv_accum = self._recv_accum[-8192:]


        # --------------------------------- 底座 ---------------------------------
        if self.test_mode == 0:
            # 底座检查
            if self.currentTestIndex == 0:
                if not self._finish_base_testing:
                    expected_echo = self.cmd_base_testing
                    expected_json = {"status": "ok","base_present":"true"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                    if obj is not None:
                        self._finish_base_testing = True
                        self._waiting_base_testing_cmd = False
                        print(">>>>>>>>收到 底座检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

            if self.currentTestIndex == 2:
                if not self._finish_base_motor:
                    expected_echo = None
                    expected_json = {"status": "ok", "motor_num": "1"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,
                                                     expected_json=expected_json)
                    if obj is not None:
                        self.base_motor_1_state = True
                        print(">>>>>>>>收到 底座电机1检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

                    expected_json = {"status": "ok", "motor_num": "2"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,expected_json=expected_json)
                    if obj is not None:
                        self.base_motor_2_state = True
                        print(">>>>>>>>收到 底座电机2检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

                    expected_json = {"status": "error", "reason": "driver_failed"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,expected_json=expected_json)

                    if obj is not None:
                        self.currentTestIndex = -1
                        self.signal_set_ui_page.emit(False, 1, "底座电机控制异常\n[请重烧固件再次尝试]", "")
                        print(">>>>>>>>收到 电机输出异常 确认 JSON:", json.dumps(obj, ensure_ascii=False))


            if self.currentTestIndex == 3:
                if not self._finish_base_power:
                    expected_echo = self.cmd_base_power
                    expected_json = {"status":"ok","base_power":"true"}
                    obj = self.contains_confirmation(self._recv_accum, expected_json=expected_json)
                    if obj is not None:
                        self._finish_base_power = True
                        print(">>>>>>>>收到 金手指供电确认 JSON:", json.dumps(obj, ensure_ascii=False))

            # if self.currentTestIndex == 4:
            #     if not self._finish_base_servo:
            #         if not self.servo_p2_state_1 or not self.servo_p2_state_0 or not self.servo_p3_state_1 or not self.servo_p3_state_0:
            #             while True:
            #                 parsed = self.pop_first_json_ok()
            #                 if parsed is None:
            #                     break
            #
            #                 pin = parsed.get("pin")
            #                 level = parsed.get("level")
            #
            #                 if pin is not None:
            #                     # GPIO引脚报文
            #                     print(f"引脚反馈 pin={pin}, level={level}")
            #                     if pin == "P2":
            #
            #                         if self.servo_p2_is_unlock == -1:
            #                             self.servo_p2_is_unlock = level
            #
            #                         if self.servo_p2_is_unlock != level or self.servo_p2_is_unlock == -2:
            #                             self.servo_p2_is_unlock = -2
            #                             if level == 1:
            #                                 self.servo_p2_state_1 = True
            #                             if level == 0:
            #                                 self.servo_p2_state_0 = True
            #
            #                     elif pin == "P3":
            #                         if self.servo_p3_is_unlock == -1:
            #                             self.servo_p3_is_unlock = level
            #
            #                         if self.servo_p3_is_unlock != level or self.servo_p3_is_unlock == -2:
            #                             self.servo_p3_is_unlock = -2
            #                             if level == 1:
            #                                 self.servo_p3_state_1 = True
            #                             if level == 0:
            #                                 self.servo_p3_state_0 = True
            #
            #     if self.servo_p2_state_0 and self.servo_p2_state_1 and self.servo_p3_state_0 and self.servo_p3_state_1:
            #         self._finish_base_servo = True
            #     else:
            #         if self.servo_current_num >= self.servoTestNum:
            #             self.currentTestIndex = -1
            #             str = "底座舵机引脚输出异常"
            #             if not self.servo_p2_state_0 or not self.servo_p2_state_1:
            #                 str += "\n[舵机1异常]"
            #             if not self.servo_p3_state_0 or not self.servo_p3_state_1:
            #                 str += "\n[舵机2异常]"
            #             self.signal_set_ui_page.emit(False, 1, str, "")

            if self.currentTestIndex == 5:
                expected_echo = self.cmd_base_testing
                expected_json = {"status": "ok","base_present":"false"}

                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self.initVars()
                    print(">>>>>>>>收到 底座断开检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

        else:
            # 底座检查
            if self.currentTestIndex == 0:
                if not self._finish_base_testing:
                    expected_echo = self.cmd_base_testing
                    expected_json = {"status": "ok", "base_present": "true"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,
                                                     expected_json=expected_json)
                    if obj is not None:
                        self._finish_base_testing = True
                        self._waiting_base_testing_cmd = False
                        print(">>>>>>>>收到 底座检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

            if self.currentTestIndex == 2:
                if not self._finish_base_motor:
                    expected_echo = None
                    expected_json = {"status": "ok", "motor_num": "1"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,
                                                     expected_json=expected_json)
                    if obj is not None:
                        self.base_motor_1_state = True
                        print(">>>>>>>>收到 底座电机1检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

                    expected_json = {"status": "ok", "motor_num": "2"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,
                                                     expected_json=expected_json)
                    if obj is not None:
                        self.base_motor_2_state = True
                        print(">>>>>>>>收到 底座电机2检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))

                    expected_json = {"status": "error", "reason": "driver_failed"}

                    obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,
                                                     expected_json=expected_json)

                    if obj is not None:
                        self.currentTestIndex = -1
                        self.signal_set_ui_page.emit(False, 1, "底座电机I2C异常\n", "")
                        print(">>>>>>>>收到 电机输出异常 确认 JSON:", json.dumps(obj, ensure_ascii=False))

                else:
                    self.base_motor_start_test = True

                if self.motor_current_num > self.motorTestNum:
                    self._finish_base_motor = True


            if self.currentTestIndex == 3:
                expected_echo = self.cmd_base_testing
                expected_json = {"status": "ok", "base_present": "false"}

                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo,
                                                 expected_json=expected_json)
                if obj is not None:
                    self.initVars()
                    print(">>>>>>>>收到 底座断开检测 确认 JSON:", json.dumps(obj, ensure_ascii=False))


    # 提取 echo+json 配对（按回显后紧随的 JSON）
    def extract_echo_json_pairs(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        pairs: List[Tuple[str, Dict[str, Any]]] = []
        for m in re.finditer(r'(^|\r?\n)\s*(tool\s+call[^\r\n]+)\s*(\r?\n|$)', text, re.I):
            echo = m.group(2).strip()
            search_start = m.end()
            jm = re.search(r'\{.*?\}', text[search_start:], re.S)
            if not jm:
                continue
            jtext = jm.group(0)
            try:
                obj = json.loads(jtext)
            except Exception:
                continue
            pairs.append((echo, obj))
        return pairs

    def json_matches(self, obj: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        def _match_val(val, exp) -> bool:
            if callable(exp):
                try:
                    return bool(exp(val))
                except Exception:
                    return False
            if isinstance(exp, dict):
                if not isinstance(val, dict):
                    return False
                return all(_match_val(val.get(k), v) for k, v in exp.items())
            if isinstance(exp, (list, tuple)):
                if not isinstance(val, (list, tuple)) or len(val) != len(exp):
                    return False
                return all(_match_val(a, b) for a, b in zip(val, exp))
            try:
                return val == exp
            except Exception:
                return False
        return all(_match_val(obj.get(k), v) for k, v in expected.items())


    def extract_json_objects(self, text: str) -> List[Dict[str, Any]]:
        """返回文本中能解析的所有 JSON 对象（按出现顺序）。"""
        objs: List[Dict[str, Any]] = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append(obj)
            except Exception:
                continue
        return objs

    def json_matches(self, obj: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """
        宽松匹配：expected 的值可以是常量、可调用或 'true'/'false' 字符串。
        - 如果 expected 为 'true'/'false'（字符串），会接受 obj 中为 True/False 或 "true"/"false" 或 1/0。
        - 数字/字符串会用 str() 比较（便于 "119" vs 119 的情况）。
        - 嵌套 dict/list 会递归比较。
        """

        def _match_val(val, exp) -> bool:
            # callable
            if callable(exp):
                try:
                    return bool(exp(val))
                except Exception:
                    return False

            # expected is 'true'/'false' string -> accept bool/str/int
            if isinstance(exp, str) and exp.lower() in ("true", "false"):
                exp_bool = (exp.lower() == "true")
                if isinstance(val, bool):
                    return val == exp_bool
                if isinstance(val, str):
                    return val.lower() == exp.lower()
                if isinstance(val, (int, float)):
                    # treat 0 as False, others as True
                    return bool(val) == exp_bool
                return False

            # nested dict
            if isinstance(exp, dict):
                if not isinstance(val, dict):
                    return False
                return all(_match_val(val.get(k), v) for k, v in exp.items())

            # list/tuple expected
            if isinstance(exp, (list, tuple)):
                if not isinstance(val, (list, tuple)) or len(val) != len(exp):
                    return False
                return all(_match_val(a, b) for a, b in zip(val, exp))

            # loose numeric/string compare: try direct equality first, then str() compare
            try:
                if val == exp:
                    return True
            except Exception:
                pass
            try:
                return str(val) == str(exp)
            except Exception:
                return False

        return all(_match_val(obj.get(k), v) for k, v in expected.items())

    def extract_json_objects_positions(self, text: str) -> List[Tuple[Dict[str, Any], int, int]]:
        objs = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            start = m.start()
            end = m.end()
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append((obj, start, end))
            except Exception:
                continue
        return objs

    def contains_confirmation(self, text: str,
                              expected_echo: Optional[str] = None,
                              expected_json: Optional[Dict[str, Any]] = None) -> Optional[Tuple[Dict[str, Any], int]]:

        # Helper json match (reuse your json_matches if present)
        def _json_ok(obj, exp) -> bool:
            if exp is None:
                return obj.get("status") == "ok"
            return self.json_matches(obj, exp)

        # Case A: expected_echo specified -> find occurrences of that literal substring
        if expected_echo is not None:
            # find all literal occurrences (not regex) to be robust
            start_pos = 0
            esc = re.escape(expected_echo)
            for m in re.finditer(esc, text):
                # search for first JSON after this echo occurrence
                search_start = m.end()
                jm = re.search(r'\{.*?\}', text[search_start:], re.S)
                if not jm:
                    continue
                json_text = jm.group(0)
                json_abs_end = search_start + jm.end()
                try:
                    obj = json.loads(json_text)
                except Exception:
                    continue
                if _json_ok(obj, expected_json):
                    return obj, json_abs_end
            return None

        # Case B: expected_echo is None -> JSON-only scan
        json_objs = self.extract_json_objects_positions(text)
        if not json_objs:
            return None
        for obj, start, end in json_objs:
            if _json_ok(obj, expected_json):
                return obj, end
        return None


    def extract_json_objects_positions(self, text: str) -> List[Tuple[Dict[str, Any], int, int]]:
        """返回文本中所有可解析 JSON 的三元组 (obj, start_index, end_index)。"""
        objs: List[Tuple[Dict[str, Any], int, int]] = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            start = m.start()
            end = m.end()
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append((obj, start, end))
            except Exception:
                continue
        return objs

    def extract_echo_json_pairs_positions(self, text: str) -> List[Tuple[str, Dict[str, Any], int, int]]:
        """
        返回所有 (echo, json_obj, echo_start_index, json_end_index)
        echo_start_index 以便需要时做更精确的截断或调试
        """
        pairs: List[Tuple[str, Dict[str, Any], int, int]] = []
        for m in re.finditer(r'(^|\r?\n)\s*(tool\s+call[^\r\n]+)\s*(\r?\n|$)', text, re.I):
            echo = m.group(2).strip()
            echo_start = m.start(2)
            search_start = m.end()
            jm = re.search(r'\{.*?\}', text[search_start:], re.S)
            if not jm:
                continue
            json_abs_start = search_start + jm.start()
            json_abs_end = search_start + jm.end()
            jtext = jm.group(0)
            try:
                obj = json.loads(jtext)
            except Exception:
                continue
            pairs.append((echo, obj, echo_start, json_abs_end))
        return pairs

    def contains_confirmation2(self,
                               text: str,
                               expected_echo: Optional[str] = None,
                               expected_status: Optional[str] = None,
                               keys: Optional[List[str]] = None
                               ) -> Optional[Tuple[Dict[str, Any], int]]:

        def to_number(v) -> Optional[float]:
            if v is None:
                return None
            if isinstance(v, bool):
                return 1.0 if v else 0.0
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                s = v.strip()
                # try direct float
                try:
                    return float(s)
                except Exception:
                    pass
                # try extract first numeric substring
                m = re.search(r'-?\d+(?:\.\d+)?', s)
                if m:
                    try:
                        return float(m.group(0))
                    except Exception:
                        return None
                return None
            return None

        def to_number_or_array(v):
            # if list/tuple => convert each element
            if isinstance(v, (list, tuple)):
                nums = []
                for e in v:
                    ne = to_number(e)
                    if ne is None:
                        return None
                    nums.append(ne)
                return nums
            # scalar
            return to_number(v)

        # helper to check status
        def status_ok(obj):
            if expected_status is None:
                return True
            s = obj.get("status")
            if s is None:
                return False
            return str(s).lower() == str(expected_status).lower()

        # Mode A: echo specified -> find occurrences and pair with next JSON
        if expected_echo is not None:
            esc = re.escape(expected_echo)
            for m in re.finditer(esc, text):
                search_start = m.end()
                jm = re.search(r'\{.*?\}', text[search_start:], re.S)
                if not jm:
                    continue
                json_text = jm.group(0)
                json_end = search_start + jm.end()
                try:
                    obj = json.loads(json_text)
                except Exception:
                    continue
                if not status_ok(obj):
                    continue
                # if no keys requested, return full obj
                if not keys:
                    return obj, json_end
                result: Dict[str, Any] = {}
                ok = True
                for k in keys:
                    if k not in obj:
                        ok = False
                        break
                    val = to_number_or_array(obj.get(k))
                    if val is None:
                        ok = False
                        break
                    result[k] = val
                if ok:
                    return result, json_end
            return None

        # Mode B: JSON-only scan
        json_objs = self.extract_json_objects_positions(text)
        if not json_objs:
            return None
        for obj, start, end in json_objs:
            if not status_ok(obj):
                continue
            if not keys:
                return obj, end
            result: Dict[str, Any] = {}
            ok = True
            for k in keys:
                if k not in obj:
                    ok = False
                    break
                val = to_number_or_array(obj.get(k))
                if val is None:
                    ok = False
                    break
                result[k] = val
            if ok:
                return result, end
        return None


    def pop_first_json_ok(self):
        """
        从self._recv_accum取出第一条完整 {"status":"ok",...} json
        成功：返回 parsed_dict，并且自动把该段json从_recv_accum删掉
        失败：返回 None，缓冲区不变
        """
        buf = self._recv_accum
        # 找第一个 {
        start = buf.find("{")
        if start == -1:
            return None

        # 找成对的 }，支持json内部嵌套
        brace_cnt = 0
        end_pos = -1
        for idx, c in enumerate(buf[start:]):
            if c == "{":
                brace_cnt += 1
            elif c == "}":
                brace_cnt -= 1
                if brace_cnt == 0:
                    end_pos = start + idx
                    break
        if end_pos == -1:
            # 半包，没有闭合，不修改缓冲区
            return None

        json_slice = buf[start: end_pos + 1]
        try:
            data = json.loads(json_slice)
        except json.JSONDecodeError:
            # json解析失败，把这个{丢掉，截断到end_pos+1，防止死循环
            self._recv_accum = buf[end_pos + 1:]
            return None

        # 判断status必须是 ok
        if data.get("status") != "ok":
            # 不是status=ok的json，丢弃这段，继续往后
            self._recv_accum = buf[end_pos + 1:]
            return None

        # ✅匹配成功，原地裁剪缓冲区，删掉已经处理的这一段
        self._recv_accum = buf[end_pos + 1:]
        return data
    def parse_sequential_ext_pin_levels(self,
                                        text: str,
                                        pins: Optional[List[str]] = None,
                                        command_keyword: str = "test_ext_pin",
                                        expected_status: Optional[str] = "ok"
                                        ) -> Optional[Tuple[List[int], int]]:
        if pins is None:
            pins = ["P0", "P1", "P2", "P3"]
        cur = 0
        levels: List[int] = []
        # 宽松匹配每一条 echo（允许有前缀如 "x_card> "）
        for pin in pins:
            # 找到包含 command_keyword 且包含 pin=Px 的 echo 行（从 cur 开始）
            pat = re.compile(r'(^|\r?\n)([^\r\n]*\btool\s+call\s+' + re.escape(command_keyword) +
                             r'[^\r\n]*\bpin=' + re.escape(pin) + r'\b[^\r\n]*)', re.I)
            m = pat.search(text, cur)
            if not m:
                return None
            echo_end = m.end(2)
            # 在 echo 之后寻找第一个完整 JSON
            jm = re.search(r'\{.*?\}', text[echo_end:], re.S)
            if not jm:
                return None
            json_text = jm.group(0)
            json_end = echo_end + jm.end()
            # 解析 JSON
            try:
                obj = json.loads(json_text)
            except Exception:
                return None
            # 检查 status（如配置）
            if expected_status is not None:
                s = obj.get("status")
                if s is None or str(s).lower() != str(expected_status).lower():
                    return None
            # 确认 JSON 中的 pin 与期望 pin 匹配（更稳健）
            obj_pin = obj.get("pin")
            if obj_pin is None or str(obj_pin).upper() != pin.upper():
                return None
            # 提取 level 并转为 int
            lev = obj.get("level")
            try:
                level_int = int(lev)
            except Exception:
                try:
                    level_int = int(float(str(lev).strip()))
                except Exception:
                    return None
            levels.append(level_int)
            # 下一次从当前 json 结束位置继续查找（保证顺序）
            cur = json_end
        # 全部找到
        return levels, cur

    def run(self):
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._periodic_check)
        self._check_timer.start(100)
        self.exec_()
        if self.isOpenPort:
            self._close_serial()


    def _periodic_check(self):
        try:
            self.signal_get_work_com.emit(1)
        except Exception:
            pass
        if not self.isStart:
            if self.isOpenPort:
                print("isStart False，关闭端口")
                self._close_serial()
            return
        if self.isStart and not self.isOpenPort:
            if not self.port:
                return
            available = [p.portName() for p in QSerialPortInfo.availablePorts()]
            if self.port in available:
                self.open_serial_link()
            else:
                pass
        else:
            if self.isOpenPort and self.serial and self.serial.portName() != self.port:
                self.signal_set_ui_page.emit(False, 2, "", "")
                print("端口名称变化，重启串口")
                self._close_serial()

    def stop(self):
        # 停止检查定时器
        try:
            if self._check_timer and self._check_timer.isActive():
                self._check_timer.stop()
        except Exception:
            pass

        # 停止写定时器（立即）
        try:
            self._stop_periodic_write()
        except Exception:
            pass

        # 确保在串口所属线程中同步关闭串口（若已打开）
        try:
            if self.isOpenPort:
                if QThread.currentThread() == self.thread():
                    # 已经在本线程，直接关闭
                    self._close_serial()
                else:
                    # 在其它线程（通常是主线程）调用，使用阻塞队列调用确保 _close_serial 在本线程执行完
                    QMetaObject.invokeMethod(self, "_close_serial", Qt.BlockingQueuedConnection)
        except Exception:
            # 兜底
            try:
                self._close_serial()
            except Exception:
                pass

        # 退出事件循环并等待线程结束（短等待）
        try:
            self.quit()
            # 等待线程退出一段时间以让 deleteLater/清理完成
            self.wait(500)  # 500 ms，可根据需要调整/移除
        except Exception:
            pass


class FinalTest_Thread(QThread):
    signal_get_work_com = pyqtSignal(int)
    signal_set_ui_page = pyqtSignal(int,bool,int, str, str)
    signal_com_refresh = pyqtSignal(str, bool)
    signal_isPassOrNg =  pyqtSignal(bool)

    class TestType(Enum):
        null = 0
        base_testing = 1
        audio = 2
        rgb = 3
        lcd = 4
        btn = 5
        tf = 6
        finish = 7


    def __init__(self,work):
        super(FinalTest_Thread, self).__init__()
        self._recv_accum = ""           # 累积接收文本，处理分片
        self.port = ""
        self.isStart = False
        self.isOpenPort = False
        self.serial = None
        self._check_timer = None
        self._write_timer = None
        self.work = work
        self.initVars()

        self.cmd_rgb = "tool call test_rgb r=50 g=50 b=50"
        self.cmd_lcd_rgb = "tool call test_lcd_loop enable=true"
        self.cmd_btn = "tool call test_buttons timeout_ms=1000"
        self.cmd_tf = "tool call test_tf"
        self.cmd_play = "tool call test_audio action=play"
        self.cmd_adc = "tool call test_sound_adc duration_ms=1000"
        self.cmd_msg = "tool call test_sensors"
        self.cmd_base_testing = "tool call test_power"
        self.cmd_audio = "tool call test_audio action=echo"
        self.cmd_read_mac = "tool call read_mac"


        self.signal_com_refresh.connect(self.set_work_code)
        self.signal_isPassOrNg.connect(self.Is_Pass_Or_Ng)

    def getServoAngle(self,station_num: int):
        # 拼接文件路径：当前目录/config/ServoAngle.ini
        ini_path = os.path.join(os.getcwd(), "config", "ServoAngle.ini")
        cfg = configparser.ConfigParser()

        # 判断文件是否存在
        if not os.path.exists(ini_path):
            QMessageBox.critical(None, "配置错误", f"配置文件不存在：\n{ini_path}")
            return None, None

        # 读取ini
        try:
            cfg.read(ini_path, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(None, "读取失败", f"读取ServoAngle.ini出错：{str(e)}")
            return None, None

        sec_name = str(station_num)
        # 判断工位section是否存在
        if sec_name not in cfg.sections():
            QMessageBox.warning(None, "工位不存在", f"无工位{station_num}配置")
            return None, None

        try:
            top_val = float(cfg.get(sec_name, "top"))
            down_val = float(cfg.get(sec_name, "down"))
            return top_val, down_val
        except Exception as e:
            QMessageBox.critical(None, "参数解析错误", f"工位{station_num}参数读取失败：{str(e)}")
            return None, None

    def getWifiConfig(self):
        """
        读取INI中 [wifi] 节点的ssid、password
        :return: (ssid, password) 读取失败返回 (None, None)
        """
        ini_path = os.path.join(os.getcwd(), "config", "ServoAngle.ini")
        cfg = configparser.ConfigParser()

        # 文件存在校验
        if not os.path.exists(ini_path):
            QMessageBox.critical(None, "配置错误", f"wifi配置文件不存在：\n{ini_path}")
            return None, None

        # 加载ini
        try:
            cfg.read(ini_path, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(None, "读取失败", f"读取配置文件异常：{str(e)}")
            return None, None

        # 校验[wifi]区块
        wifi_section = "wifi"
        if wifi_section not in cfg.sections():
            QMessageBox.warning(None, "配置缺失", "INI文件内无 [wifi] 配置区块")
            return None, None

        try:
            ssid = cfg.get(wifi_section, "ssid").strip()
            password = cfg.get(wifi_section, "password").strip()
            return ssid, password
        except Exception as e:
            QMessageBox.critical(None, "参数缺失", f"wifi ssid/password读取失败：{str(e)}")
            return None, None

    def initVars(self):
        self._recv_accum = ""
        self.mac = ""
        self.sn = ""
        self.oldSn = ""
        self.code = ""
        self.isUpdata = False
        self.oldCurrentTestIndex = 0
        self.currentTestIndex = self.TestType.base_testing.value
        self._last_now = None
        self.turn_state = False
        self.currentMsgNum = 0

        self.testNum = random.choice([2, 3, 4])
        self.rssi = 0
        self.servoCount = 0
        self.servoCount = 0
        self.m_p0_on_num = 0
        self.m_p0_off_num = 0
        self.m_p1_on_num = 0
        self.m_p1_off_num = 0

        self.battery_percent = 0
        self._sent_battery_test_cmd = False
        self._finish_battery_test = False
        self._waiting_battery_test_cmd = False

        self.m_p2_on_num = 0
        self.m_p2_off_num = 0
        self.m_p3_on_num = 0
        self.m_p3_off_num = 0

        self.light = 0.00
        self.accel = 0.00
        self.gyro  = 0.00
        self.mag   = 0.00

        self.test_rgb_result = False
        self.test_lcd_result = False
        self.test_btn_result = False
        self.test_play_result = False
        self.test_tf_result = False
        self.test_adc_result = False
        self.test_msg_result = False
        self.test_wifi_result = False
        self.test_gpio_result = False

        self._finish_audio = False
        self._sent_audio_cmd = False
        self._waiting_audio_cmd = False

        self._sent_rgb_cmd = False
        self._finish_rgb = False
        self._waiting_rgb_cmd = False

        self._sent_lcd_cmd = False
        self._finish_lcd = False
        self._waiting_lcd_cmd = False

        self._sent_btn_cmd = False
        self._finish_btn = False
        self._waiting_btn_cmd = False

        self.confirm_pressed = False
        self.return_pressed = False
        self.select_pressed = False

        self._sent_tf_cmd = False
        self._finish_tf = False
        self._waiting_tf_cmd = False

        self._sent_play_cmd = False
        self._finish_play = False
        self._waiting_play_cmd = False

        self._sent_adc_cmd = False
        self._finish_adc = False
        self._waiting_adc_cmd = False

        self._sent_msg_cmd = False
        self._finish_msg = False
        self._waiting_msg_cmd = False

        self._sent_wifi_cmd = False
        self._finish_wifi = False
        self._waiting_wifi_cmd = False
        self._wifi_retry_num = 0

        self._msg_retry_num = 0
        self._msg_Through_num = 0

        self._sent_gpio_cmd = False
        self._finish_gpio = False
        self._waiting_gpio_cmd = False

        self._finish_mp3 = False
        self._sent_mp3_cmd = False
        self._waiting_mp3_cmd = False

        self._finish_base_power = False
        self._sent_base_power_cmd = False
        self._waiting_base_power_cmd = False

        self._finish_base_servo = False
        self._sent_base_servo_cmd = False
        self._waiting_base_servo_cmd = False


        self._finish_read_mac = False
        self._sent_read_mac_cmd = False
        self._waiting_read_mac_cmd = False

        self.is_finish_write_sn_code = False
        self.write_sn_code = False

        self._waiting_write_sn_cmd = False
        self._waiting_write_code_cmd = False

    def find_mac(self, mac: str):
        global g_db_connection, g_MesTableName

        # 预先清空旧 SN，避免残留
        self.oldSn = None

        if not isinstance(mac, str) or not mac.strip():
            return False

        normalized_mac = mac.strip().upper()

        # 获取现有连接（不尝试重连）
        connection = g_db_connection if (
                g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            return False

        try:
            sql = "SELECT sn FROM `{}` WHERE UPPER(mac) = %s LIMIT 1".format(g_MesTableName)
            with connection.cursor() as cursor:
                cursor.execute(sql, (normalized_mac,))
                row = cursor.fetchone()
                if not row:
                    return False

                # 兼容不同 cursor 返回类型
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    sn = row[0]
                elif isinstance(row, dict):
                    sn = row.get('sn') if 'sn' in row else (next(iter(row.values())) if row else None)
                else:
                    sn = row

                if sn is None:
                    return False

                # 确保是字符串
                if isinstance(sn, bytes):
                    try:
                        sn = sn.decode('utf-8')
                    except Exception:
                        sn = str(sn)

                self.oldSn = str(sn)
                return True

        except pymysql.MySQLError:
            return False
        except Exception:
            return False

    def uploading(self,info):
        global g_db_connection,g_MesTableName

        # 获取现有连接（不尝试重新连接）
        connection = g_db_connection if (g_db_connection is not None and hasattr(g_db_connection, 'open') and g_db_connection.open) else None
        if connection is None:
            return False

        self.isUpdata = self.find_mac(self.mac)

        try:
            if not self.isUpdata:
                print("\nmac = :", self.mac)
                print("\nsn = :", self.sn)
                print("\nrandom_code = :", self.code)

                if not self.code:
                    print("\n密钥生成失败")
                    return False

                with connection.cursor() as cursor:
                    # 开始事务
                    connection.begin()

                    # 插入新记录
                    insert_sql = "INSERT INTO `" + g_MesTableName + "` (mac, sn, code,info, time) VALUES (%s, %s, %s, %s,NOW())"
                    cursor.execute(insert_sql, (self.mac, self.sn ,self.code, info))

                    # 提交事务
                    connection.commit()
                    return True
            else:
                with connection.cursor() as cursor:
                    # 开始事务
                    connection.begin()

                    # 根据MAC地址更新内容,但是不更新新记录
                    update_sql = "UPDATE `{}` SET info = %s, time = NOW() WHERE UPPER(mac) = %s".format(g_MesTableName)
                    cursor.execute(update_sql, (info, self.mac))


                    # 提交事务
                    connection.commit()
                    return True

        except pymysql.MySQLError as e:
            if connection:
                connection.rollback()
            return False
        except Exception as e:
            if connection:
                connection.rollback()
            return False

    def create_random_code(self,sn: str, mac: str) -> Tuple[bytes, Dict[str, str]]:
        normalized_sn = sn.strip()
        normalized_mac = mac.strip().upper()
        MAC_PATTERN = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$")
        if not normalized_sn:
            raise ValueError("SN不能为空")
        if not MAC_PATTERN.fullmatch(normalized_mac):
            raise ValueError("MAC必须使用 AA:BB:CC:DD:EE:FF 格式")
        device_secret_raw = secrets.token_bytes(32)
        return str(device_secret_raw.hex())

    def find_first_missing_sn_serial(self, prefix: str, color: str, expected_count: Optional[int] = None):
        global g_db_connection, g_MesTableName

        if not prefix or not isinstance(prefix, str):
            return False, "prefix 参数无效"
        if not color or not isinstance(color, str) or len(color) != 1:
            return False, "color 参数无效"

        conn = g_db_connection if (g_db_connection is not None and getattr(g_db_connection, 'open', True)) else None
        if conn is None:
            return False, "MES未连接, 无法查询"

        try:
            # SQL: 从 SN 中截取流水号的开始位置（MySQL SUBSTRING 从1开始）
            pos = len(prefix) + 1
            like_pattern = prefix + "______" + color  # '_' 匹配单字符，6个下划线匹配 6 位流水号

            # 提取流水号为整数，忽略不能转换的行
            sql = f"SELECT CAST(SUBSTRING(`sn`, %s, 6) AS UNSIGNED) AS serial FROM `{g_MesTableName}` WHERE `sn` LIKE %s"
            with conn.cursor() as cur:
                cur.execute(sql, (pos, like_pattern))
                rows = cur.fetchall()

            serial_list = []
            for row in rows:
                # 兼容不同 cursor：可能是 (serial,) 也可能是 {'serial': val}
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    val = row[0]
                elif isinstance(row, dict):
                    # 字典形式的 cursor（DictCursor）
                    val = row.get('serial') or list(row.values())[0] if row else None
                else:
                    val = row
                try:
                    if val is None:
                        continue
                    ival = int(val)
                    if 1 <= ival <= 999999:
                        serial_list.append(ival)
                except Exception:
                    continue

            if not serial_list:
                # 没有符合记录，返回第一个流水号
                return True, f"{1:06d}"

            serial_set = set(serial_list)
            # N: 要检查的区间上限（按你的规则：如果没有传 expected_count 用记录数 len(serial_list)）
            N = expected_count if (expected_count is not None and expected_count > 0) else len(serial_list)

            # 在 1..N 内查缺号
            for i in range(1, N + 1):
                if i not in serial_set:
                    return True, f"{i:06d}"

            # 如果 1..N 都存在，则返回 N+1
            next_one = N + 1
            if next_one > 999999:
                return False, "流水号已达到上限 999999"
            return True, f"{next_one:06d}"

        except pymysql.MySQLError as e:
            return False, f"数据库错误: {e}"
        except Exception as e:
            return False, f"执行错误: {e}"

    def create_sn(self,serial: int,
                  product_type: str = "13",
                  product_name: str = "48",
                  version: str = "A",
                  reserved: str = "00",
                  check: str = "A",
                  color: str = "W",
                  prod_date: Optional[datetime.date] = None
                  ) -> str:

        # 验证 serial
        if not isinstance(serial, int) or serial < 0 or serial > 999999:
            raise ValueError("流水号必须是 0 到 999999 之间的整数（含边界）")

        # 简单长度验证
        if len(product_type) != 2 or len(product_name) != 2 or len(version) != 1 or len(reserved) != 2:
            raise ValueError("产品类型/产品名称/版本/预留长度无效")
        if len(check) != 1 or len(color) != 1:
            raise ValueError("校验位和产品颜色必须为单个字符")

        # 生产日期（默认今天）
        if prod_date is None:
            prod_date = datetime.date.today()

        iso_year, iso_week, _ = prod_date.isocalendar()
        year_part = f"{(iso_year % 100):02d}"
        week_part = f"{iso_week:02d}"
        serial_part = f"{serial:06d}"

        sn = f"{product_type}{product_name}{version}{reserved}{year_part}{week_part}{check}{serial_part}{color}"
        return sn

    def get_next_sn_and_generate(self):
        # 产品默认参数（与 create_sn 默认一致）
        product_type = "13"
        product_name = "48"
        version = "A"
        reserved = "00"
        check = "A"
        color = "W"

        # 生产日期 = 今天
        prod_date = datetime.date.today()
        iso_year, iso_week, _ = prod_date.isocalendar()
        year_part = f"{(iso_year % 100):02d}"
        week_part = f"{iso_week:02d}"

        # prefix 应与 find_first_missing_sn_serial 的期待一致：
        # product_type + product_name + version + reserved + year(2) + week(2) + check
        prefix = f"{product_type}{product_name}{version}{reserved}{year_part}{week_part}{check}"

        # 从 DB 查找第一个缺号或下一个流水（返回 6 位字符串，如 "000003"）
        ok, serial_or_err = self.find_first_missing_sn_serial(prefix=prefix, color=color, expected_count=None)
        if not ok:
            return False, serial_or_err

        # serial_or_err 应为类似 "000003" 的字符串，转为 int 传给 create_sn
        try:
            serial_int = int(serial_or_err)
            return True,serial_int
        except Exception as e:
            return False, f"解析流水号失败: {e}"


    def set_work_code(self, com, isStart):
        if com and com != self.port and self.isOpenPort:
            try:
                if QThread.currentThread() == self.thread():
                    self._close_serial()
                else:
                    QMetaObject.invokeMethod(self, "_close_serial", Qt.BlockingQueuedConnection)
            except Exception:
                # 兜底：尝试直接关闭
                try:
                    self._close_serial()
                except Exception:
                    pass

        # 更新端口与启动标志
        self.port = com
        self.isStart = isStart


    def Is_Pass_Or_Ng(self, var,test = ""):
        if self.currentTestIndex == self.TestType.rgb.value and self._finish_rgb:
            if var:
                self.currentTestIndex += 1
                self.test_rgb_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.test_rgb_result = False
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.lcd.value and self._finish_lcd:
            if var:
                self.currentTestIndex += 1
                self.test_lcd_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.test_lcd_result = False
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.btn.value and self._finish_btn:
            if var:
                self.currentTestIndex += 1
                self.test_btn_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, test, "")
                self.test_btn_result = False
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.tf.value and self._finish_tf:
            if var:
                self.currentTestIndex += 1
                self.test_tf_result = True
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "无法读取TF卡", "")
                self.currentTestIndex = 0

        elif self.currentTestIndex == self.TestType.audio.value and self._sent_audio_cmd:
            if var:
                self.currentTestIndex += 1
            else:
                self.signal_set_ui_page.emit(self.work,False, 1, "录音播放异常", "")
                self.currentTestIndex = 0



    def open_serial_link(self):
        if not self.port:
            print("open_serial_link: 未指定端口")
            return False

        available = [p.portName() for p in QSerialPortInfo.availablePorts()]
        if self.port not in available:
            print(f"open_serial_link: 请求的端口 {self.port} 不在可用端口列表: {available}")
            return False

        try:
            if self.serial is not None:
                self._close_serial()

            self.serial = QSerialPort()
            self.serial.setPortName(self.port)
            self.serial.setBaudRate(115200)
            self.serial.setDataBits(QSerialPort.Data8)
            self.serial.setParity(QSerialPort.NoParity)
            self.serial.setStopBits(QSerialPort.OneStop)
            self.serial.setFlowControl(QSerialPort.NoFlowControl)

            if self.serial.open(QIODevice.ReadWrite):
                print(f"\n成功打开串口: {self.port}")
                self.signal_set_ui_page.emit(self.work,False, 2, "", "")
                try:
                    self.serial.clear()
                except Exception:
                    pass
                time.sleep(0.05)

                try:
                    self.serial.readyRead.connect(self.on_serial_read)
                except Exception as e:
                    print("readyRead connect 异常:", e)

                # reset states
                self.initVars()

                self.isOpenPort = True
                QTimer.singleShot(2000, self._start_periodic_write)  # 延迟 2s 启动写定时器
                return True
            else:
                print(f"\n打开串口失败: {self.port}")
                self.isOpenPort = False
                return False
        except Exception as e:
            print("open_serial_link 异常:", e)
            self.isOpenPort = False
            return False

    def _close_serial(self):
        # 1) 停写定时器，避免并发写
        try:
            self._stop_periodic_write()
        except Exception:
            pass

        # 2) 标记端口已关闭，避免其它逻辑再尝试写
        self.isOpenPort = False

        if not self.serial:
            return

        try:
            # 3) 断开信号
            try:
                self.serial.readyRead.disconnect(self.on_serial_read)
            except Exception:
                pass

            # 4) 嘗試短等待 pending bytes 写入排空（可选，短超时）
            try:
                self.serial.waitForBytesWritten(200)  # 200 ms
            except Exception:
                pass

            # 5) 清理缓冲
            try:
                self.serial.clear()
            except Exception:
                pass

            # 6) 关闭端口
            try:
                self.serial.close()
            except Exception:
                pass

            # 7) 释放引用（不要依赖 deleteLater 必须由事件循环处理）
            try:
                self.serial = None
            except Exception:
                self.serial = None

        finally:
            # 8) 重置状态标志（按需）
            self._sent_rgb_cmd = False
            self._finish_rgb = False
            self._waiting_rgb_cmd = False
            self._last_now = 0.0
            # ... 重置其它标志 ...
            self._recv_accum = ""
            self.isOpenPort = False

    def _start_periodic_write(self):
        if not self.isOpenPort or self.serial is None:
            return
        if self._write_timer is None:
            self._write_timer = QTimer()
            self._write_timer.timeout.connect(self._on_write_timer)
            self._write_timer.start(100)

    def _stop_periodic_write(self):
        if self._write_timer is not None:
            try:
                if self._write_timer.isActive():
                    self._write_timer.stop()
            except Exception:
                pass
            try:
                self._write_timer.timeout.disconnect(self._on_write_timer)
            except Exception:
                pass
            self._write_timer = None
            print("写入定时器已停止")

    # 指令发送
    def _on_write_timer(self):
        if not self.isOpenPort or self.serial is None:
            self._stop_periodic_write()
            return

        now = time.time()
        if self.currentTestIndex == self.TestType.base_testing.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_base_testing
            if not self._finish_battery_test:
                if self.battery_percent == 0:
                    self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[电池电量检测]\n发送检测指令中...")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_battery_test_cmd) or (now - self._last_now > 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_battery_test_cmd = True
                        self._waiting_battery_test_cmd = True
                        self._last_now = now
                        print(f"[发送] 电池电量检测 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 电池电量检测 cmd={t_cmd}")
            else:
                time.sleep(3)
                self.currentTestIndex += 1

        if self.currentTestIndex == self.TestType.audio.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_audio
            if not self._finish_audio:
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_audio_cmd) or (now - self._last_now > 7.0):
                    if self._waiting_audio_cmd and now - self._last_now < 7.0 + 10:
                        self.signal_set_ui_page.emit(self.work, True, 3, t_testPro,f"\n\n\n\n[录音完成/正在播放]\n{int(18 - (now - self._last_now))}秒后重新录制播放")
                    else:
                        try:
                            bytes_written = self.serial.write(cmd_bytes)
                            try:
                                self.serial.waitForBytesWritten(500)
                            except Exception:
                                pass
                            self._sent_audio_cmd = True
                            self._waiting_audio_cmd = True
                            self._last_now = now
                            print(f"[发送] 录音播放 cmd={t_cmd} bytes={bytes_written}")
                        except Exception:
                            print(f"[发送失败] 录音播放 cmd={t_cmd}")

                else:
                    self.signal_set_ui_page.emit(self.work, True, 3, t_testPro,"\n\n\n\n[录音播放测试]\n[正在录音/5秒后播放]\n\n请对麦克风说出:你好,你好")



        if self.currentTestIndex == self.TestType.rgb.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_rgb
            if not self._finish_rgb:
                self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[RGB灯]\n发送控制指令中...")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_rgb_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_rgb_cmd = True
                        self._waiting_rgb_cmd = True
                        self._last_now = now
                        print(f"[发送] RGB cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] RGB cmd={t_cmd}")
            else:
                self.signal_set_ui_page.emit(self.work, True, 3, t_testPro, "\n << < 人工查看 >> >\n\n[RGB灯]\n[充电指示灯]\n\n\n是否点亮?")

        if self.currentTestIndex == self.TestType.lcd.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_lcd_rgb
            if not self._finish_lcd:
                self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[LCD显示屏]\n发送控制指令中...")
                cmd_bytes = (self.cmd_lcd_rgb + "\r\n").encode('utf-8')
                if (not self._waiting_lcd_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_lcd_cmd = True
                        self._waiting_lcd_cmd = True
                        self._last_now = now
                        self._finish_lcd = True
                        print(f"[发送] LCD显示屏 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] LCD显示屏 cmd={t_cmd}")
            else:
                self.signal_set_ui_page.emit(self.work, True, 3, t_testPro, "\n << < 人工查看 >> >\n\n[LCD显示屏]\n\n\n\n是否无坏点,无划痕?")

        if self.currentTestIndex == self.TestType.btn.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_btn
            if not self._finish_btn:
                self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[功能按键测试]\n正在检测按键是否按下...")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_btn_cmd) or (now - self._last_now > 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(200)
                        except Exception:
                            pass
                        self._sent_btn_cmd = True
                        self._waiting_btn_cmd = True
                        self._last_now = now
                        print(f"[发送] 功能按键检测 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] 功能按键检测 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(True)

        if self.currentTestIndex == self.TestType.tf.value:
            t_testPro = "测试项目" + str(self.currentTestIndex)
            t_cmd = self.cmd_tf
            if not self._finish_tf:
                self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, "\n\n\n\n\n[TF卡自检]\n")
                cmd_bytes = (t_cmd + "\r\n").encode('utf-8')
                if (not self._waiting_tf_cmd) or (now - self._last_now >= 2.0):
                    try:
                        bytes_written = self.serial.write(cmd_bytes)
                        try:
                            self.serial.waitForBytesWritten(500)
                        except Exception:
                            pass
                        self._sent_tf_cmd = True
                        self._waiting_tf_cmd = True
                        self._last_now = now
                        print(f"[发送] TF卡自检 cmd={t_cmd} bytes={bytes_written}")
                    except Exception:
                        print(f"[发送失败] TF卡自检 cmd={t_cmd}")
            else:
                self.Is_Pass_Or_Ng(self.test_tf_result)

        if self.currentTestIndex == self.TestType.finish.value:
            self.signal_set_ui_page.emit(self.work, False, 0, f"测试通过", "")


    # 指令接收
    def on_serial_read(self):
        if not self.serial:
            return
        try:
            qba = self.serial.readAll()
            chunk = qba.data() if hasattr(qba, "data") else bytes(qba)
        except Exception:
            chunk = b''
            print("serial.readAll() 读取异常")
        if not chunk:
            return
        try:
            recv_str = chunk.decode('utf-8', errors='replace')
        except Exception:
            recv_str = ''
            print("recv data decode err")

        self._recv_accum += recv_str
        if len(self._recv_accum) > 3000:
            self._recv_accum = self._recv_accum[-3000:]


        # --------------------------------- 主控 ---------------------------------
        # 电量检查
        if self.currentTestIndex == self.TestType.base_testing.value:
            if not self._finish_battery_test:
                expected_status = "ok"
                res = self.contains_confirmation2(self._recv_accum, expected_echo=None, expected_status=expected_status, keys=None)
                if res is not None:
                    parsed, end_index = res
                    t_battery_percent = parsed.get("battery_percent")
                    if t_battery_percent:
                        self.battery_percent = t_battery_percent
                        # 合格判定：60% ~ 90% 放行测试
                        if 60 <= self.battery_percent <= 90:
                            t_testPro = "测试项目" + str(self.currentTestIndex)
                            self.signal_set_ui_page.emit(self.work, False, 3, t_testPro, f"\n\n\n\n\n[电池电量通过]\n当前电量：{self.battery_percent}%")
                            self._finish_battery_test = True
                        else:
                            tip_text = f"[电池电量不合格]\n当前电量：{self.battery_percent}%\n电量要求在70% ~ 90%区间"
                            self.signal_set_ui_page.emit(self.work, False, 1, tip_text, "")

                        self._recv_accum = self._recv_accum[end_index:]
                        print(">>>>>>>>收到 电池电量 确认:", f"当前电量:{self.battery_percent}%")


        # RGB 检查
        if self.currentTestIndex == self.TestType.rgb.value:
            if not self._finish_rgb:
                expected_echo = self.cmd_rgb
                expected_json = {"status": "ok"}

                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self._finish_rgb = True
                    self._waiting_rgb_cmd = False
                    print(">>>>>>>>收到 RGB 确认 JSON:", json.dumps(obj, ensure_ascii=False))

        if self.currentTestIndex == self.TestType.lcd.value:
            if not self._finish_lcd:
                expected_echo = self.cmd_lcd_rgb
                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo)
                if obj is not None:
                    self._finish_lcd = True
                    self._waiting_lcd_cmd = False
                    print(">>>>>>>>收到 LCD 确认 JSON:", json.dumps(obj, ensure_ascii=False))


        if self.currentTestIndex == self.TestType.btn.value:
            if not self._finish_btn:
                expected_status = "ok"
                keys = ["confirm_pressed", "return_pressed", "select_pressed"]
                res = self.contains_confirmation2(self._recv_accum,expected_echo=None,expected_status=expected_status,keys=keys)
                if res is not None:
                    parsed, end_index = res
                    if not self.confirm_pressed:
                        self.confirm_pressed = parsed.get("confirm_pressed")
                    if not self.return_pressed:
                        self.return_pressed = parsed.get("return_pressed")
                    if not self.select_pressed:
                        self.select_pressed = parsed.get("select_pressed")

                    if self.confirm_pressed and self.return_pressed and self.select_pressed:
                        self._finish_btn = True
                        self._waiting_btn_cmd = False
                    # 截断缓冲
                    self._recv_accum = self._recv_accum[end_index:]
                    print(">>>>>>>>收到 功能按键确认 JSON:", json.dumps(res, ensure_ascii=False))


        if self.currentTestIndex == self.TestType.tf.value:
            if not self._finish_tf:
                expected_echo = self.cmd_tf
                expected_json = {"status": "ok"}

                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self._finish_tf = True
                    self._waiting_tf_cmd = False
                    self.test_tf_result = True
                    print(">>>>>>>>收到 TF卡确认 JSON:", json.dumps(obj, ensure_ascii=False))

                expected_json = {"status": "error"}
                obj = self.contains_confirmation(self._recv_accum, expected_echo=expected_echo, expected_json=expected_json)
                if obj is not None:
                    self._finish_tf = True
                    self._waiting_tf_cmd = False
                    self.test_tf_result = False
                    print(">>>>>>>>收到 TF卡确认 JSON:", json.dumps(obj, ensure_ascii=False))



    # 提取 echo+json 配对（按回显后紧随的 JSON）
    def extract_echo_json_pairs(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        pairs: List[Tuple[str, Dict[str, Any]]] = []
        for m in re.finditer(r'(^|\r?\n)\s*(tool\s+call[^\r\n]+)\s*(\r?\n|$)', text, re.I):
            echo = m.group(2).strip()
            search_start = m.end()
            jm = re.search(r'\{.*?\}', text[search_start:], re.S)
            if not jm:
                continue
            jtext = jm.group(0)
            try:
                obj = json.loads(jtext)
            except Exception:
                continue
            pairs.append((echo, obj))
        return pairs

    def json_matches(self, obj: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        def _match_val(val, exp) -> bool:
            if callable(exp):
                try:
                    return bool(exp(val))
                except Exception:
                    return False
            if isinstance(exp, dict):
                if not isinstance(val, dict):
                    return False
                return all(_match_val(val.get(k), v) for k, v in exp.items())
            if isinstance(exp, (list, tuple)):
                if not isinstance(val, (list, tuple)) or len(val) != len(exp):
                    return False
                return all(_match_val(a, b) for a, b in zip(val, exp))
            try:
                return val == exp
            except Exception:
                return False
        return all(_match_val(obj.get(k), v) for k, v in expected.items())


    def extract_json_objects(self, text: str) -> List[Dict[str, Any]]:
        """返回文本中能解析的所有 JSON 对象（按出现顺序）。"""
        objs: List[Dict[str, Any]] = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append(obj)
            except Exception:
                continue
        return objs

    def json_matches(self, obj: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """
        宽松匹配：expected 的值可以是常量、可调用或 'true'/'false' 字符串。
        - 如果 expected 为 'true'/'false'（字符串），会接受 obj 中为 True/False 或 "true"/"false" 或 1/0。
        - 数字/字符串会用 str() 比较（便于 "119" vs 119 的情况）。
        - 嵌套 dict/list 会递归比较。
        """

        def _match_val(val, exp) -> bool:
            # callable
            if callable(exp):
                try:
                    return bool(exp(val))
                except Exception:
                    return False

            # expected is 'true'/'false' string -> accept bool/str/int
            if isinstance(exp, str) and exp.lower() in ("true", "false"):
                exp_bool = (exp.lower() == "true")
                if isinstance(val, bool):
                    return val == exp_bool
                if isinstance(val, str):
                    return val.lower() == exp.lower()
                if isinstance(val, (int, float)):
                    # treat 0 as False, others as True
                    return bool(val) == exp_bool
                return False

            # nested dict
            if isinstance(exp, dict):
                if not isinstance(val, dict):
                    return False
                return all(_match_val(val.get(k), v) for k, v in exp.items())

            # list/tuple expected
            if isinstance(exp, (list, tuple)):
                if not isinstance(val, (list, tuple)) or len(val) != len(exp):
                    return False
                return all(_match_val(a, b) for a, b in zip(val, exp))

            # loose numeric/string compare: try direct equality first, then str() compare
            try:
                if val == exp:
                    return True
            except Exception:
                pass
            try:
                return str(val) == str(exp)
            except Exception:
                return False

        return all(_match_val(obj.get(k), v) for k, v in expected.items())

    def extract_json_objects_positions(self, text: str) -> List[Tuple[Dict[str, Any], int, int]]:
        objs = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            start = m.start()
            end = m.end()
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append((obj, start, end))
            except Exception:
                continue
        return objs

    def contains_confirmation(self, text: str,
                              expected_echo: Optional[str] = None,
                              expected_json: Optional[Dict[str, Any]] = None) -> Optional[Tuple[Dict[str, Any], int]]:

        # Helper json match (reuse your json_matches if present)
        def _json_ok(obj, exp) -> bool:
            if exp is None:
                return obj.get("status") == "ok"
            return self.json_matches(obj, exp)

        # Case A: expected_echo specified -> find occurrences of that literal substring
        if expected_echo is not None:
            # find all literal occurrences (not regex) to be robust
            start_pos = 0
            esc = re.escape(expected_echo)
            for m in re.finditer(esc, text):
                # search for first JSON after this echo occurrence
                search_start = m.end()
                jm = re.search(r'\{.*?\}', text[search_start:], re.S)
                if not jm:
                    continue
                json_text = jm.group(0)
                json_abs_end = search_start + jm.end()
                try:
                    obj = json.loads(json_text)
                except Exception:
                    continue
                if _json_ok(obj, expected_json):
                    return obj, json_abs_end
            return None

        # Case B: expected_echo is None -> JSON-only scan
        json_objs = self.extract_json_objects_positions(text)
        if not json_objs:
            return None
        for obj, start, end in json_objs:
            if _json_ok(obj, expected_json):
                return obj, end
        return None


    def extract_json_objects_positions(self, text: str) -> List[Tuple[Dict[str, Any], int, int]]:
        """返回文本中所有可解析 JSON 的三元组 (obj, start_index, end_index)。"""
        objs: List[Tuple[Dict[str, Any], int, int]] = []
        for m in re.finditer(r'\{.*?\}', text, re.S):
            start = m.start()
            end = m.end()
            j = m.group(0)
            try:
                obj = json.loads(j)
                if isinstance(obj, dict):
                    objs.append((obj, start, end))
            except Exception:
                continue
        return objs

    def extract_echo_json_pairs_positions(self, text: str) -> List[Tuple[str, Dict[str, Any], int, int]]:
        """
        返回所有 (echo, json_obj, echo_start_index, json_end_index)
        echo_start_index 以便需要时做更精确的截断或调试
        """
        pairs: List[Tuple[str, Dict[str, Any], int, int]] = []
        for m in re.finditer(r'(^|\r?\n)\s*(tool\s+call[^\r\n]+)\s*(\r?\n|$)', text, re.I):
            echo = m.group(2).strip()
            echo_start = m.start(2)
            search_start = m.end()
            jm = re.search(r'\{.*?\}', text[search_start:], re.S)
            if not jm:
                continue
            json_abs_start = search_start + jm.start()
            json_abs_end = search_start + jm.end()
            jtext = jm.group(0)
            try:
                obj = json.loads(jtext)
            except Exception:
                continue
            pairs.append((echo, obj, echo_start, json_abs_end))
        return pairs

    def contains_confirmation2(self,
                               text: str,
                               expected_echo: Optional[str] = None,
                               expected_status: Optional[str] = None,
                               keys: Optional[List[str]] = None
                               ) -> Optional[Tuple[Dict[str, Any], int]]:

        def to_number(v) -> Optional[float]:
            if v is None:
                return None
            if isinstance(v, bool):
                return 1.0 if v else 0.0
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                s = v.strip()
                # try direct float
                try:
                    return float(s)
                except Exception:
                    pass
                # try extract first numeric substring
                m = re.search(r'-?\d+(?:\.\d+)?', s)
                if m:
                    try:
                        return float(m.group(0))
                    except Exception:
                        return None
                return None
            return None

        def to_number_or_array(v):
            # if list/tuple => convert each element
            if isinstance(v, (list, tuple)):
                nums = []
                for e in v:
                    ne = to_number(e)
                    if ne is None:
                        return None
                    nums.append(ne)
                return nums
            # scalar
            return to_number(v)

        # helper to check status
        def status_ok(obj):
            if expected_status is None:
                return True
            s = obj.get("status")
            if s is None:
                return False
            return str(s).lower() == str(expected_status).lower()

        # Mode A: echo specified -> find occurrences and pair with next JSON
        if expected_echo is not None:
            esc = re.escape(expected_echo)
            for m in re.finditer(esc, text):
                search_start = m.end()
                jm = re.search(r'\{.*?\}', text[search_start:], re.S)
                if not jm:
                    continue
                json_text = jm.group(0)
                json_end = search_start + jm.end()
                try:
                    obj = json.loads(json_text)
                except Exception:
                    continue
                if not status_ok(obj):
                    continue
                # if no keys requested, return full obj
                if not keys:
                    return obj, json_end
                result: Dict[str, Any] = {}
                ok = True
                for k in keys:
                    if k not in obj:
                        ok = False
                        break
                    val = to_number_or_array(obj.get(k))
                    if val is None:
                        ok = False
                        break
                    result[k] = val
                if ok:
                    return result, json_end
            return None

        # Mode B: JSON-only scan
        json_objs = self.extract_json_objects_positions(text)
        if not json_objs:
            return None
        for obj, start, end in json_objs:
            if not status_ok(obj):
                continue
            if not keys:
                return obj, end
            result: Dict[str, Any] = {}
            ok = True
            for k in keys:
                if k not in obj:
                    ok = False
                    break
                val = to_number_or_array(obj.get(k))
                if val is None:
                    ok = False
                    break
                result[k] = val
            if ok:
                return result, end
        return None

    def parse_sequential_ext_pin_levels(self,
                                        text: str,
                                        pins: Optional[List[str]] = None,
                                        command_keyword: str = "test_ext_pin",
                                        expected_status: Optional[str] = "ok"
                                        ) -> Optional[Tuple[List[int], int]]:
        if pins is None:
            pins = ["P0", "P1", "P2", "P3"]
        cur = 0
        levels: List[int] = []
        # 宽松匹配每一条 echo（允许有前缀如 "x_card> "）
        for pin in pins:
            # 找到包含 command_keyword 且包含 pin=Px 的 echo 行（从 cur 开始）
            pat = re.compile(r'(^|\r?\n)([^\r\n]*\btool\s+call\s+' + re.escape(command_keyword) +
                             r'[^\r\n]*\bpin=' + re.escape(pin) + r'\b[^\r\n]*)', re.I)
            m = pat.search(text, cur)
            if not m:
                return None
            echo_end = m.end(2)
            # 在 echo 之后寻找第一个完整 JSON
            jm = re.search(r'\{.*?\}', text[echo_end:], re.S)
            if not jm:
                return None
            json_text = jm.group(0)
            json_end = echo_end + jm.end()
            # 解析 JSON
            try:
                obj = json.loads(json_text)
            except Exception:
                return None
            # 检查 status（如配置）
            if expected_status is not None:
                s = obj.get("status")
                if s is None or str(s).lower() != str(expected_status).lower():
                    return None
            # 确认 JSON 中的 pin 与期望 pin 匹配（更稳健）
            obj_pin = obj.get("pin")
            if obj_pin is None or str(obj_pin).upper() != pin.upper():
                return None
            # 提取 level 并转为 int
            lev = obj.get("level")
            try:
                level_int = int(lev)
            except Exception:
                try:
                    level_int = int(float(str(lev).strip()))
                except Exception:
                    return None
            levels.append(level_int)
            # 下一次从当前 json 结束位置继续查找（保证顺序）
            cur = json_end
        # 全部找到
        return levels, cur

    def run(self):
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._periodic_check)
        self._check_timer.start(100)
        self.exec_()
        if self.isOpenPort:
            self._close_serial()


    def _periodic_check(self):
        try:
            self.signal_get_work_com.emit(self.work)
        except Exception:
            pass
        if not self.isStart:
            if self.isOpenPort:
                print("isStart False，关闭端口")
                self._close_serial()
            return
        if self.isStart and not self.isOpenPort:
            if not self.port:
                return
            available = [p.portName() for p in QSerialPortInfo.availablePorts()]
            if self.port in available:
                self.open_serial_link()
            else:
                pass
        else:
            if self.isOpenPort and self.serial and self.serial.portName() != self.port:
                self.signal_set_ui_page.emit(self.work,False, 2, "", "")
                print("端口名称变化，重启串口")
                self._close_serial()

    def stop(self):
        # 停止检查定时器
        try:
            if self._check_timer and self._check_timer.isActive():
                self._check_timer.stop()
        except Exception:
            pass

        # 停止写定时器（立即）
        try:
            self._stop_periodic_write()
        except Exception:
            pass

        # 确保在串口所属线程中同步关闭串口（若已打开）
        try:
            if self.isOpenPort:
                if QThread.currentThread() == self.thread():
                    # 已经在本线程，直接关闭
                    self._close_serial()
                else:
                    # 在其它线程（通常是主线程）调用，使用阻塞队列调用确保 _close_serial 在本线程执行完
                    QMetaObject.invokeMethod(self, "_close_serial", Qt.BlockingQueuedConnection)
        except Exception:
            # 兜底
            try:
                self._close_serial()
            except Exception:
                pass

        # 退出事件循环并等待线程结束（短等待）
        try:
            self.quit()
            # 等待线程退出一段时间以让 deleteLater/清理完成
            self.wait(500)  # 500 ms，可根据需要调整/移除
        except Exception:
            pass


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
    t_key = generate_key(machine_code)
    return key == t_key


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



def get_file_creation_time(file_path: Union[str, os.PathLike]):
    """
    返回文件的最后修改时间（st_mtime），格式 'YYYY-MM-DD HH:MM:SS'。
    如果获取失败或文件不存在，返回 " "。
    """
    try:
        if not os.path.exists(file_path):
            return " "

        st = os.stat(file_path)
        mod_ts = st.st_mtime  # 使用修改时间

        dt_obj = datetime.datetime.fromtimestamp(mod_ts)
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S")

    except PermissionError:
        return " "
    except Exception:
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

        self.ui.combo_project.addItem("7001_盛思_掌控板1.0")
        self.ui.combo_project.addItem("7001_讯飞实验箱_小学版")
        self.ui.combo_project.addItem("7001_讯飞实验箱_初中版")
        self.ui.combo_project.addItem("7001_盛思_信息科技示教板")
        self.ui.combo_project.addItem("7005_盛思_掌控板_学境1.0")
        self.ui.combo_project.addItem("7005_盛思_模块_学境")
        self.ui.combo_project.addItem("7007_盛思_掌控板_单板")
        self.ui.combo_project.addItem("7009_盛思_乐动掌控2.0")
        self.ui.combo_project.addItem("7010_盛思_掌控板_学境2.0")
        self.ui.combo_project.addItem("7011_讯飞_X-CARD_主控")
        self.ui.combo_project.addItem("7011_讯飞_X-CARD_底座")
        #self.ui.combo_project.addItem("SN码绑定MAC地址")


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
                # index == ProjectType.sn_mac.val1 的情况
                (self.ui.combo_stage.clear(),
                 self.ui.combo_stage.addItems(["7008_1956主控","7009_乐动掌控2.0"]),
                 self.ui.combo_stage.setCurrentIndex(0),
                 self.ui.combo_stage.setEnabled(True)) if index == ProjectType.sn_mac.val1 else
                # index == ProjectType.v7009.val1
                (self.ui.combo_stage.clear(),
                 self.ui.combo_stage.addItems(["半成品测试", "盛思_成品测试", "讯飞_成品测试"]),
                 self.ui.combo_stage.setCurrentIndex(0),
                 self.ui.combo_stage.setEnabled(True)) if index == ProjectType.v7009.val1 else
                # index == ProjectType.v7011.val1
                (self.ui.combo_stage.clear(),
                 self.ui.combo_stage.addItems(["1拖4_半成品测试", "成品测试"]),
                 self.ui.combo_stage.setCurrentIndex(0),
                 self.ui.combo_stage.setEnabled(True)) if index == ProjectType.v7011.val1 else
                # 处理其他情况
                (self.ui.combo_stage.clear(),
                 self.ui.combo_stage.addItems(["半成品测试", "成品测试"]),
                 self.ui.combo_stage.setCurrentIndex(1) if index in [ProjectType.x7001.val1,
                                                                     ProjectType.c7001.val1,
                                                                     ProjectType.v7007.val1,
                                                                     ProjectType.m7005.val1,
                                                                     ProjectType.v7005.val1,
                                                                     ProjectType.v7010.val1,
                                                                     ProjectType.v260Teach.val1,
                                                                     ProjectType.v260Zkb.val1,] else None,
                 self.ui.combo_stage.setEnabled(index not in [ProjectType.x7001.val1,ProjectType.c7001.val1,ProjectType.v7007.val1, ProjectType.m7005.val1,ProjectType.v260Teach.val1,ProjectType.v7005.val1,ProjectType.v260Zkb.val1,ProjectType.v7010.val1]))
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
        g_project = ProjectType.from_val1(self.ui.combo_project.currentIndex()).val2
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





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartHmiWindow()
    window.show()
    sys.exit(app.exec_())


