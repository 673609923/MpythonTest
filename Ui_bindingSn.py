# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\desktop\项目\掌控板测试软件\MpythonTest_7001\MpythonTest_7001\bindingSn.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_bindingSn(object):
    def setupUi(self, bindingSn):
        bindingSn.setObjectName("bindingSn")
        bindingSn.resize(444, 127)
        self.gridLayout = QtWidgets.QGridLayout(bindingSn)
        self.gridLayout.setObjectName("gridLayout")
        self.carve_serial_groupBox_5 = QtWidgets.QGroupBox(bindingSn)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.carve_serial_groupBox_5.sizePolicy().hasHeightForWidth())
        self.carve_serial_groupBox_5.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(11)
        self.carve_serial_groupBox_5.setFont(font)
        self.carve_serial_groupBox_5.setObjectName("carve_serial_groupBox_5")
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout(self.carve_serial_groupBox_5)
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.SnLineEdit_MAC = QtWidgets.QLineEdit(self.carve_serial_groupBox_5)
        self.SnLineEdit_MAC.setEnabled(True)
        self.SnLineEdit_MAC.setMinimumSize(QtCore.QSize(0, 50))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.SnLineEdit_MAC.setFont(font)
        self.SnLineEdit_MAC.setStyleSheet("color: rgb(34, 177, 76);\n"
"border: 2px dashed rgb(34, 177, 76);\n"
"padding: 2px;")
        self.SnLineEdit_MAC.setText("")
        self.SnLineEdit_MAC.setAlignment(QtCore.Qt.AlignCenter)
        self.SnLineEdit_MAC.setObjectName("SnLineEdit_MAC")
        self.horizontalLayout_16.addWidget(self.SnLineEdit_MAC)
        self.btnEnter = QtWidgets.QPushButton(self.carve_serial_groupBox_5)
        self.btnEnter.setMinimumSize(QtCore.QSize(0, 50))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btnEnter.setFont(font)
        self.btnEnter.setObjectName("btnEnter")
        self.horizontalLayout_16.addWidget(self.btnEnter)
        self.gridLayout.addWidget(self.carve_serial_groupBox_5, 0, 0, 1, 1)

        self.retranslateUi(bindingSn)
        QtCore.QMetaObject.connectSlotsByName(bindingSn)

    def retranslateUi(self, bindingSn):
        _translate = QtCore.QCoreApplication.translate
        bindingSn.setWindowTitle(_translate("bindingSn", " "))
        self.carve_serial_groupBox_5.setTitle(_translate("bindingSn", "请输入 20 位数的SN码"))
        self.SnLineEdit_MAC.setPlaceholderText(_translate("bindingSn", "请输入SN码"))
        self.btnEnter.setText(_translate("bindingSn", "确定(Enter)"))

