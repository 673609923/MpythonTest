# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mpython_factory_test.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1112, 942)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.TabWidget = QTabWidget(self.centralwidget)
        self.TabWidget.setObjectName(u"TabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TabWidget.sizePolicy().hasHeightForWidth())
        self.TabWidget.setSizePolicy(sizePolicy)
        font = QFont()
        font.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font.setPointSize(12)
        self.TabWidget.setFont(font)
        self.TabWidget.setStyleSheet(u"#TabWidget, QTabWidget::pane{\n"
"	background-color: rgba(255, 255, 255, 100);\n"
"}\n"
"\n"
"#TabWidget QTabBar::tab\n"
"{\n"
"	background-color: rgba(150, 150, 150, 200);\n"
"	border:1px solid #34495e;\n"
"	\n"
"	color: rgb(0, 0, 0);\n"
"	font: 75 11pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"	border-radius:5px;\n"
"    min-width: 120px;\n"
"	min-height:28px;\n"
"	border-bottom-right-radius:0px;\n"
"	border-bottom-left-radius:0px;\n"
"	margin-left: 1px;\n"
"}\n"
"\n"
"\n"
"#TabWidget QTabBar::tab:selected\n"
"{\n"
"	background-color: rgba(231, 76, 60, 200);\n"
"	border:1px solid rgb(208, 66, 54);\n"
"}\n"
"\n"
"#TabWidget QTabBar::tab:hover\n"
"{\n"
"	background-color: rgba(231, 76, 60, 120);\n"
"	border:1px solid rgb(208, 66, 54);\n"
"	cursor:pointer;\n"
"}\n"
"\n"
"#TabWidget QTabBar::tab:!selected\n"
"{\n"
"    margin-top: 2px; \n"
"}")
        self.TabWidget.setTabPosition(QTabWidget.North)
        self.TabWidget.setTabShape(QTabWidget.Triangular)
        self.TabWidget.setElideMode(Qt.ElideLeft)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.TabWidget.addTab(self.tab, "")
        self.carve_tab = QWidget()
        self.carve_tab.setObjectName(u"carve_tab")
        self.carve_tab.setEnabled(True)
        self.carve_tab.setFont(font)
        self.carve_tab.setStyleSheet(u"")
        self.verticalLayout_18 = QVBoxLayout(self.carve_tab)
        self.verticalLayout_18.setSpacing(1)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(2, 1, 2, 2)
        self.carve_widget = QWidget(self.carve_tab)
        self.carve_widget.setObjectName(u"carve_widget")
        self.verticalLayout_17 = QVBoxLayout(self.carve_widget)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.widget = QWidget(self.carve_widget)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_5 = QHBoxLayout(self.widget)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.carve_serial_groupBox = QGroupBox(self.widget)
        self.carve_serial_groupBox.setObjectName(u"carve_serial_groupBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.carve_serial_groupBox.sizePolicy().hasHeightForWidth())
        self.carve_serial_groupBox.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font1.setPointSize(11)
        self.carve_serial_groupBox.setFont(font1)
        self.horizontalLayout_2 = QHBoxLayout(self.carve_serial_groupBox)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setSpacing(30)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.serial_carve_comboBox = QComboBox(self.carve_serial_groupBox)
        self.serial_carve_comboBox.setObjectName(u"serial_carve_comboBox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.serial_carve_comboBox.sizePolicy().hasHeightForWidth())
        self.serial_carve_comboBox.setSizePolicy(sizePolicy2)
        self.serial_carve_comboBox.setMinimumSize(QSize(150, 20))

        self.horizontalLayout_13.addWidget(self.serial_carve_comboBox)

        self.refresh_carve_Button = QPushButton(self.carve_serial_groupBox)
        self.refresh_carve_Button.setObjectName(u"refresh_carve_Button")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.refresh_carve_Button.sizePolicy().hasHeightForWidth())
        self.refresh_carve_Button.setSizePolicy(sizePolicy3)
        self.refresh_carve_Button.setMinimumSize(QSize(0, 30))
        self.refresh_carve_Button.setFont(font)

        self.horizontalLayout_13.addWidget(self.refresh_carve_Button)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_18)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_13)


        self.horizontalLayout_5.addWidget(self.carve_serial_groupBox)

        self.groupBox_2 = QGroupBox(self.widget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setFont(font1)
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_4.setSpacing(10)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(10, 10, 10, 10)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setHorizontalSpacing(15)
        self.iPLabel = QLabel(self.groupBox_2)
        self.iPLabel.setObjectName(u"iPLabel")
        self.iPLabel.setFont(font1)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.iPLabel)

        self.iPLineEdit = QLineEdit(self.groupBox_2)
        self.iPLineEdit.setObjectName(u"iPLineEdit")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.iPLineEdit.sizePolicy().hasHeightForWidth())
        self.iPLineEdit.setSizePolicy(sizePolicy4)
        self.iPLineEdit.setMinimumSize(QSize(0, 25))

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.iPLineEdit)

        self.portLabel = QLabel(self.groupBox_2)
        self.portLabel.setObjectName(u"portLabel")
        self.portLabel.setFont(font1)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.portLabel)

        self.portLineEdit = QLineEdit(self.groupBox_2)
        self.portLineEdit.setObjectName(u"portLineEdit")
        self.portLineEdit.setMinimumSize(QSize(0, 25))

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.portLineEdit)


        self.horizontalLayout_4.addLayout(self.formLayout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)


        self.horizontalLayout_5.addWidget(self.groupBox_2)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 1)

        self.verticalLayout_17.addWidget(self.widget)

        self.widget_2 = QWidget(self.carve_widget)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.carve_mac_label = QLabel(self.widget_2)
        self.carve_mac_label.setObjectName(u"carve_mac_label")
        sizePolicy2.setHeightForWidth(self.carve_mac_label.sizePolicy().hasHeightForWidth())
        self.carve_mac_label.setSizePolicy(sizePolicy2)
        self.carve_mac_label.setMinimumSize(QSize(0, 40))
        font2 = QFont()
        font2.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font2.setPointSize(20)
        self.carve_mac_label.setFont(font2)
        self.carve_mac_label.setStyleSheet(u"background-color: rgb(181, 181, 181);")
        self.carve_mac_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.carve_mac_label)

        self.horizontalSpacer_2 = QSpacerItem(195, 20, QSizePolicy.Ignored, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_2)

        self.carve_start_Button = QPushButton(self.widget_2)
        self.carve_start_Button.setObjectName(u"carve_start_Button")
        sizePolicy1.setHeightForWidth(self.carve_start_Button.sizePolicy().hasHeightForWidth())
        self.carve_start_Button.setSizePolicy(sizePolicy1)
        font3 = QFont()
        font3.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font3.setPointSize(26)
        self.carve_start_Button.setFont(font3)

        self.horizontalLayout_6.addWidget(self.carve_start_Button)


        self.verticalLayout_17.addWidget(self.widget_2)

        self.verticalSpacer = QSpacerItem(20, 478, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_17.addItem(self.verticalSpacer)

        self.verticalLayout_17.setStretch(0, 1)
        self.verticalLayout_17.setStretch(1, 1)
        self.verticalLayout_17.setStretch(2, 4)

        self.verticalLayout_18.addWidget(self.carve_widget)

        self.TabWidget.addTab(self.carve_tab, "")
        self.func_test_tab = QWidget()
        self.func_test_tab.setObjectName(u"func_test_tab")
        self.gridLayout = QGridLayout(self.func_test_tab)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.func_widget = QWidget(self.func_test_tab)
        self.func_widget.setObjectName(u"func_widget")
        self.gridLayout_3 = QGridLayout(self.func_widget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(5)
        self.gridLayout_3.setVerticalSpacing(1)
        self.gridLayout_3.setContentsMargins(5, 5, 5, 5)
        self.widget_3 = QWidget(self.func_widget)
        self.widget_3.setObjectName(u"widget_3")
        self.verticalLayout_19 = QVBoxLayout(self.widget_3)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.para_Button = QPushButton(self.widget_3)
        self.para_Button.setObjectName(u"para_Button")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.para_Button.sizePolicy().hasHeightForWidth())
        self.para_Button.setSizePolicy(sizePolicy5)
        font4 = QFont()
        font4.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font4.setPointSize(10)
        self.para_Button.setFont(font4)

        self.verticalLayout_19.addWidget(self.para_Button)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.change_prj_checkBox = QCheckBox(self.widget_3)
        self.change_prj_checkBox.setObjectName(u"change_prj_checkBox")
        sizePolicy1.setHeightForWidth(self.change_prj_checkBox.sizePolicy().hasHeightForWidth())
        self.change_prj_checkBox.setSizePolicy(sizePolicy1)
        self.change_prj_checkBox.setFont(font)

        self.gridLayout_4.addWidget(self.change_prj_checkBox, 1, 0, 1, 2)

        self.hw_Label = QLabel(self.widget_3)
        self.hw_Label.setObjectName(u"hw_Label")
        self.hw_Label.setFont(font1)
#if QT_CONFIG(accessibility)
        self.hw_Label.setAccessibleName(u"")
#endif // QT_CONFIG(accessibility)
        self.hw_Label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.hw_Label, 0, 0, 1, 1)

        self.hw_LineEdit = QLineEdit(self.widget_3)
        self.hw_LineEdit.setObjectName(u"hw_LineEdit")
        self.hw_LineEdit.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.hw_LineEdit.sizePolicy().hasHeightForWidth())
        self.hw_LineEdit.setSizePolicy(sizePolicy1)
        self.hw_LineEdit.setMinimumSize(QSize(0, 25))
        self.hw_LineEdit.setAlignment(Qt.AlignCenter)

        self.gridLayout_4.addWidget(self.hw_LineEdit, 0, 1, 1, 1)

        self.gridLayout_4.setRowStretch(0, 5)
        self.gridLayout_4.setColumnStretch(0, 5)

        self.verticalLayout_19.addLayout(self.gridLayout_4)

        self.verticalLayout_19.setStretch(0, 2)
        self.verticalLayout_19.setStretch(1, 1)

        self.gridLayout_3.addWidget(self.widget_3, 0, 2, 1, 1)

        self.result_func_label = QLabel(self.func_widget)
        self.result_func_label.setObjectName(u"result_func_label")
        font5 = QFont()
        font5.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font5.setPointSize(16)
        font5.setBold(False)
        font5.setItalic(False)
        font5.setWeight(50)
        self.result_func_label.setFont(font5)
        self.result_func_label.setStyleSheet(u"font: 16pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"\n"
"")
        self.result_func_label.setAlignment(Qt.AlignCenter)

        self.gridLayout_3.addWidget(self.result_func_label, 0, 1, 1, 1)

        self.func_log_groupBox = QGroupBox(self.func_widget)
        self.func_log_groupBox.setObjectName(u"func_log_groupBox")
        self.func_log_groupBox.setFont(font1)
        self.verticalLayout_20 = QVBoxLayout(self.func_log_groupBox)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.func_log_textEdit = QTextEdit(self.func_log_groupBox)
        self.func_log_textEdit.setObjectName(u"func_log_textEdit")

        self.verticalLayout_20.addWidget(self.func_log_textEdit)


        self.gridLayout_3.addWidget(self.func_log_groupBox, 2, 2, 1, 3)

        self.groupBox_5 = QGroupBox(self.func_widget)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy1.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy1)
        self.groupBox_5.setFont(font1)
        self.groupBox_5.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.verticalLayout_23 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.serial_func_comboBox = QComboBox(self.groupBox_5)
        self.serial_func_comboBox.setObjectName(u"serial_func_comboBox")
        sizePolicy2.setHeightForWidth(self.serial_func_comboBox.sizePolicy().hasHeightForWidth())
        self.serial_func_comboBox.setSizePolicy(sizePolicy2)
        self.serial_func_comboBox.setMinimumSize(QSize(150, 20))
        self.serial_func_comboBox.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_12.addWidget(self.serial_func_comboBox)

        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_17)

        self.com_func_Button = QPushButton(self.groupBox_5)
        self.com_func_Button.setObjectName(u"com_func_Button")
        sizePolicy2.setHeightForWidth(self.com_func_Button.sizePolicy().hasHeightForWidth())
        self.com_func_Button.setSizePolicy(sizePolicy2)
        self.com_func_Button.setMinimumSize(QSize(100, 40))
        self.com_func_Button.setFont(font)
        self.com_func_Button.setStyleSheet(u"")

        self.horizontalLayout_12.addWidget(self.com_func_Button)

        self.refresh_func_Button = QPushButton(self.groupBox_5)
        self.refresh_func_Button.setObjectName(u"refresh_func_Button")
        sizePolicy2.setHeightForWidth(self.refresh_func_Button.sizePolicy().hasHeightForWidth())
        self.refresh_func_Button.setSizePolicy(sizePolicy2)
        self.refresh_func_Button.setMinimumSize(QSize(100, 40))
        self.refresh_func_Button.setFont(font)

        self.horizontalLayout_12.addWidget(self.refresh_func_Button)


        self.verticalLayout_23.addLayout(self.horizontalLayout_12)


        self.gridLayout_3.addWidget(self.groupBox_5, 0, 0, 1, 1)

        self.func_test_groupBox = QGroupBox(self.func_widget)
        self.func_test_groupBox.setObjectName(u"func_test_groupBox")
        self.func_test_groupBox.setFont(font1)
        self.verticalLayout_9 = QVBoxLayout(self.func_test_groupBox)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.test_gridLayout = QGridLayout()
        self.test_gridLayout.setSpacing(5)
        self.test_gridLayout.setObjectName(u"test_gridLayout")
        self.test_gridLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.acc_x_widget = QWidget(self.func_test_groupBox)
        self.acc_x_widget.setObjectName(u"acc_x_widget")
        sizePolicy1.setHeightForWidth(self.acc_x_widget.sizePolicy().hasHeightForWidth())
        self.acc_x_widget.setSizePolicy(sizePolicy1)
        self.acc_x_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_16 = QVBoxLayout(self.acc_x_widget)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.acc_x_label = QLabel(self.acc_x_widget)
        self.acc_x_label.setObjectName(u"acc_x_label")
        sizePolicy1.setHeightForWidth(self.acc_x_label.sizePolicy().hasHeightForWidth())
        self.acc_x_label.setSizePolicy(sizePolicy1)
        font6 = QFont()
        font6.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font6.setPointSize(12)
        font6.setBold(False)
        font6.setItalic(False)
        font6.setWeight(50)
        self.acc_x_label.setFont(font6)
        self.acc_x_label.setStyleSheet(u"font: 12pt")
        self.acc_x_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_16.addWidget(self.acc_x_label)

        self.acc_x_value_label = QLabel(self.acc_x_widget)
        self.acc_x_value_label.setObjectName(u"acc_x_value_label")
        sizePolicy1.setHeightForWidth(self.acc_x_value_label.sizePolicy().hasHeightForWidth())
        self.acc_x_value_label.setSizePolicy(sizePolicy1)
        font7 = QFont()
        font7.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font7.setPointSize(9)
        font7.setBold(False)
        font7.setItalic(False)
        font7.setWeight(50)
        self.acc_x_value_label.setFont(font7)
        self.acc_x_value_label.setStyleSheet(u"font: 9pt ")
        self.acc_x_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_16.addWidget(self.acc_x_value_label)


        self.test_gridLayout.addWidget(self.acc_x_widget, 4, 3, 1, 1)

        self.p3_widget = QWidget(self.func_test_groupBox)
        self.p3_widget.setObjectName(u"p3_widget")
        sizePolicy1.setHeightForWidth(self.p3_widget.sizePolicy().hasHeightForWidth())
        self.p3_widget.setSizePolicy(sizePolicy1)
        self.p3_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_13 = QVBoxLayout(self.p3_widget)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.p3_label = QLabel(self.p3_widget)
        self.p3_label.setObjectName(u"p3_label")
        sizePolicy1.setHeightForWidth(self.p3_label.sizePolicy().hasHeightForWidth())
        self.p3_label.setSizePolicy(sizePolicy1)
        font8 = QFont()
        font8.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font8.setPointSize(18)
        font8.setBold(False)
        font8.setItalic(False)
        font8.setWeight(50)
        self.p3_label.setFont(font8)
        self.p3_label.setStyleSheet(u"")
        self.p3_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_13.addWidget(self.p3_label)

        self.p3_value_label = QLabel(self.p3_widget)
        self.p3_value_label.setObjectName(u"p3_value_label")
        sizePolicy1.setHeightForWidth(self.p3_value_label.sizePolicy().hasHeightForWidth())
        self.p3_value_label.setSizePolicy(sizePolicy1)
        self.p3_value_label.setFont(font7)
        self.p3_value_label.setStyleSheet(u"font: 9pt ")
        self.p3_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_13.addWidget(self.p3_value_label)


        self.test_gridLayout.addWidget(self.p3_widget, 2, 4, 1, 1)

        self.ty_widget = QWidget(self.func_test_groupBox)
        self.ty_widget.setObjectName(u"ty_widget")
        sizePolicy6 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.ty_widget.sizePolicy().hasHeightForWidth())
        self.ty_widget.setSizePolicy(sizePolicy6)
        self.ty_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);\n"
"\n"
"")
        self.verticalLayout_3 = QVBoxLayout(self.ty_widget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.ty_label = QLabel(self.ty_widget)
        self.ty_label.setObjectName(u"ty_label")
        sizePolicy1.setHeightForWidth(self.ty_label.sizePolicy().hasHeightForWidth())
        self.ty_label.setSizePolicy(sizePolicy1)
        self.ty_label.setFont(font8)
        self.ty_label.setStyleSheet(u"")
        self.ty_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.ty_label)

        self.ty_value_label = QLabel(self.ty_widget)
        self.ty_value_label.setObjectName(u"ty_value_label")
        sizePolicy1.setHeightForWidth(self.ty_value_label.sizePolicy().hasHeightForWidth())
        self.ty_value_label.setSizePolicy(sizePolicy1)
        self.ty_value_label.setFont(font7)
        self.ty_value_label.setStyleSheet(u"font: 9pt ")
        self.ty_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.ty_value_label)


        self.test_gridLayout.addWidget(self.ty_widget, 1, 2, 1, 1)

        self.touch_widget = QWidget(self.func_test_groupBox)
        self.touch_widget.setObjectName(u"touch_widget")
        sizePolicy6.setHeightForWidth(self.touch_widget.sizePolicy().hasHeightForWidth())
        self.touch_widget.setSizePolicy(sizePolicy6)
        self.verticalLayout_26 = QVBoxLayout(self.touch_widget)
        self.verticalLayout_26.setSpacing(1)
        self.verticalLayout_26.setObjectName(u"verticalLayout_26")
        self.verticalLayout_26.setContentsMargins(0, 0, 0, 0)
        self.touch_label = QLabel(self.touch_widget)
        self.touch_label.setObjectName(u"touch_label")
        sizePolicy1.setHeightForWidth(self.touch_label.sizePolicy().hasHeightForWidth())
        self.touch_label.setSizePolicy(sizePolicy1)
        font9 = QFont()
        font9.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font9.setPointSize(18)
        self.touch_label.setFont(font9)
        self.touch_label.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);")
        self.touch_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_26.addWidget(self.touch_label)

        self.touch_label_1 = QLabel(self.touch_widget)
        self.touch_label_1.setObjectName(u"touch_label_1")
        sizePolicy1.setHeightForWidth(self.touch_label_1.sizePolicy().hasHeightForWidth())
        self.touch_label_1.setSizePolicy(sizePolicy1)
        font10 = QFont()
        font10.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font10.setPointSize(9)
        self.touch_label_1.setFont(font10)
        self.touch_label_1.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"")
        self.touch_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_26.addWidget(self.touch_label_1)

        self.verticalLayout_26.setStretch(0, 3)
        self.verticalLayout_26.setStretch(1, 1)

        self.test_gridLayout.addWidget(self.touch_widget, 1, 0, 1, 1)

        self.to_widget = QWidget(self.func_test_groupBox)
        self.to_widget.setObjectName(u"to_widget")
        sizePolicy1.setHeightForWidth(self.to_widget.sizePolicy().hasHeightForWidth())
        self.to_widget.setSizePolicy(sizePolicy1)
        self.to_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_6 = QVBoxLayout(self.to_widget)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.to_label = QLabel(self.to_widget)
        self.to_label.setObjectName(u"to_label")
        sizePolicy1.setHeightForWidth(self.to_label.sizePolicy().hasHeightForWidth())
        self.to_label.setSizePolicy(sizePolicy1)
        self.to_label.setFont(font8)
        self.to_label.setStyleSheet(u"")
        self.to_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_6.addWidget(self.to_label)

        self.to_value_label = QLabel(self.to_widget)
        self.to_value_label.setObjectName(u"to_value_label")
        sizePolicy1.setHeightForWidth(self.to_value_label.sizePolicy().hasHeightForWidth())
        self.to_value_label.setSizePolicy(sizePolicy1)
        self.to_value_label.setFont(font7)
        self.to_value_label.setStyleSheet(u"font: 9pt ")
        self.to_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_6.addWidget(self.to_value_label)


        self.test_gridLayout.addWidget(self.to_widget, 1, 5, 1, 1)

        self.mag_value_label = QLabel(self.func_test_groupBox)
        self.mag_value_label.setObjectName(u"mag_value_label")
        font11 = QFont()
        font11.setFamily(u"\u5fae\u8f6f\u96c5\u9ed1")
        font11.setPointSize(10)
        font11.setBold(False)
        font11.setItalic(False)
        font11.setWeight(50)
        self.mag_value_label.setFont(font11)
        self.mag_value_label.setStyleSheet(u"background-color: rgb(203, 203, 203);\n"
"\n"
"")
        self.mag_value_label.setAlignment(Qt.AlignCenter)

        self.test_gridLayout.addWidget(self.mag_value_label, 5, 5, 1, 1)

        self.tn_widget = QWidget(self.func_test_groupBox)
        self.tn_widget.setObjectName(u"tn_widget")
        sizePolicy1.setHeightForWidth(self.tn_widget.sizePolicy().hasHeightForWidth())
        self.tn_widget.setSizePolicy(sizePolicy1)
        self.tn_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_8 = QVBoxLayout(self.tn_widget)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.tn_label = QLabel(self.tn_widget)
        self.tn_label.setObjectName(u"tn_label")
        sizePolicy1.setHeightForWidth(self.tn_label.sizePolicy().hasHeightForWidth())
        self.tn_label.setSizePolicy(sizePolicy1)
        self.tn_label.setFont(font8)
        self.tn_label.setStyleSheet(u"")
        self.tn_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_8.addWidget(self.tn_label)

        self.tn_value_label = QLabel(self.tn_widget)
        self.tn_value_label.setObjectName(u"tn_value_label")
        sizePolicy1.setHeightForWidth(self.tn_value_label.sizePolicy().hasHeightForWidth())
        self.tn_value_label.setSizePolicy(sizePolicy1)
        self.tn_value_label.setFont(font7)
        self.tn_value_label.setStyleSheet(u"font: 9pt ")
        self.tn_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_8.addWidget(self.tn_value_label)


        self.test_gridLayout.addWidget(self.tn_widget, 1, 6, 1, 1)

        self.th_widget = QWidget(self.func_test_groupBox)
        self.th_widget.setObjectName(u"th_widget")
        sizePolicy6.setHeightForWidth(self.th_widget.sizePolicy().hasHeightForWidth())
        self.th_widget.setSizePolicy(sizePolicy6)
        self.th_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_5 = QVBoxLayout(self.th_widget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.th_label = QLabel(self.th_widget)
        self.th_label.setObjectName(u"th_label")
        sizePolicy1.setHeightForWidth(self.th_label.sizePolicy().hasHeightForWidth())
        self.th_label.setSizePolicy(sizePolicy1)
        self.th_label.setFont(font8)
        self.th_label.setStyleSheet(u"")
        self.th_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_5.addWidget(self.th_label)

        self.th_value_label = QLabel(self.th_widget)
        self.th_value_label.setObjectName(u"th_value_label")
        sizePolicy1.setHeightForWidth(self.th_value_label.sizePolicy().hasHeightForWidth())
        self.th_value_label.setSizePolicy(sizePolicy1)
        self.th_value_label.setFont(font7)
        self.th_value_label.setStyleSheet(u"font: 9pt ")
        self.th_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_5.addWidget(self.th_value_label)


        self.test_gridLayout.addWidget(self.th_widget, 1, 4, 1, 1)

        self.display_Button = QPushButton(self.func_test_groupBox)
        self.display_Button.setObjectName(u"display_Button")
        sizePolicy7 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.display_Button.sizePolicy().hasHeightForWidth())
        self.display_Button.setSizePolicy(sizePolicy7)
        self.display_Button.setStyleSheet(u"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"")

        self.test_gridLayout.addWidget(self.display_Button, 6, 1, 1, 1)

        self.audio_Button = QPushButton(self.func_test_groupBox)
        self.audio_Button.setObjectName(u"audio_Button")
        sizePolicy7.setHeightForWidth(self.audio_Button.sizePolicy().hasHeightForWidth())
        self.audio_Button.setSizePolicy(sizePolicy7)
        self.audio_Button.setStyleSheet(u"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"")

        self.test_gridLayout.addWidget(self.audio_Button, 6, 6, 1, 1)

        self.acc_value_label = QLabel(self.func_test_groupBox)
        self.acc_value_label.setObjectName(u"acc_value_label")
        self.acc_value_label.setFont(font11)
        self.acc_value_label.setStyleSheet(u"background-color: rgb(203, 203, 203);\n"
"\n"
"")
        self.acc_value_label.setAlignment(Qt.AlignCenter)

        self.test_gridLayout.addWidget(self.acc_value_label, 4, 4, 1, 1)

        self.acc_y_widget = QWidget(self.func_test_groupBox)
        self.acc_y_widget.setObjectName(u"acc_y_widget")
        sizePolicy1.setHeightForWidth(self.acc_y_widget.sizePolicy().hasHeightForWidth())
        self.acc_y_widget.setSizePolicy(sizePolicy1)
        self.acc_y_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_15 = QVBoxLayout(self.acc_y_widget)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.acc_y_label = QLabel(self.acc_y_widget)
        self.acc_y_label.setObjectName(u"acc_y_label")
        sizePolicy1.setHeightForWidth(self.acc_y_label.sizePolicy().hasHeightForWidth())
        self.acc_y_label.setSizePolicy(sizePolicy1)
        self.acc_y_label.setFont(font6)
        self.acc_y_label.setStyleSheet(u"font: 12pt")
        self.acc_y_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_15.addWidget(self.acc_y_label)

        self.acc_y_value_label = QLabel(self.acc_y_widget)
        self.acc_y_value_label.setObjectName(u"acc_y_value_label")
        sizePolicy1.setHeightForWidth(self.acc_y_value_label.sizePolicy().hasHeightForWidth())
        self.acc_y_value_label.setSizePolicy(sizePolicy1)
        self.acc_y_value_label.setFont(font7)
        self.acc_y_value_label.setStyleSheet(u"font: 9pt ")
        self.acc_y_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_15.addWidget(self.acc_y_value_label)


        self.test_gridLayout.addWidget(self.acc_y_widget, 4, 2, 1, 1)

        self.current_Button = QPushButton(self.func_test_groupBox)
        self.current_Button.setObjectName(u"current_Button")
        sizePolicy7.setHeightForWidth(self.current_Button.sizePolicy().hasHeightForWidth())
        self.current_Button.setSizePolicy(sizePolicy7)
        self.current_Button.setStyleSheet(u"\n"
"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"")

        self.test_gridLayout.addWidget(self.current_Button, 6, 4, 1, 1)

        self.acc_z_widget = QWidget(self.func_test_groupBox)
        self.acc_z_widget.setObjectName(u"acc_z_widget")
        sizePolicy1.setHeightForWidth(self.acc_z_widget.sizePolicy().hasHeightForWidth())
        self.acc_z_widget.setSizePolicy(sizePolicy1)
        self.acc_z_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_14 = QVBoxLayout(self.acc_z_widget)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.acc_z_label = QLabel(self.acc_z_widget)
        self.acc_z_label.setObjectName(u"acc_z_label")
        sizePolicy1.setHeightForWidth(self.acc_z_label.sizePolicy().hasHeightForWidth())
        self.acc_z_label.setSizePolicy(sizePolicy1)
        self.acc_z_label.setFont(font6)
        self.acc_z_label.setStyleSheet(u"font: 12pt")
        self.acc_z_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_14.addWidget(self.acc_z_label)

        self.acc_z_value_label = QLabel(self.acc_z_widget)
        self.acc_z_value_label.setObjectName(u"acc_z_value_label")
        sizePolicy1.setHeightForWidth(self.acc_z_value_label.sizePolicy().hasHeightForWidth())
        self.acc_z_value_label.setSizePolicy(sizePolicy1)
        self.acc_z_value_label.setFont(font7)
        self.acc_z_value_label.setStyleSheet(u"font: 9pt ")
        self.acc_z_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_14.addWidget(self.acc_z_value_label)


        self.test_gridLayout.addWidget(self.acc_z_widget, 4, 1, 1, 1)

        self.p1_widget = QWidget(self.func_test_groupBox)
        self.p1_widget.setObjectName(u"p1_widget")
        sizePolicy1.setHeightForWidth(self.p1_widget.sizePolicy().hasHeightForWidth())
        self.p1_widget.setSizePolicy(sizePolicy1)
        self.p1_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_11 = QVBoxLayout(self.p1_widget)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.p1_label = QLabel(self.p1_widget)
        self.p1_label.setObjectName(u"p1_label")
        sizePolicy1.setHeightForWidth(self.p1_label.sizePolicy().hasHeightForWidth())
        self.p1_label.setSizePolicy(sizePolicy1)
        self.p1_label.setFont(font8)
        self.p1_label.setStyleSheet(u"")
        self.p1_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_11.addWidget(self.p1_label)

        self.p1_value_label = QLabel(self.p1_widget)
        self.p1_value_label.setObjectName(u"p1_value_label")
        sizePolicy1.setHeightForWidth(self.p1_value_label.sizePolicy().hasHeightForWidth())
        self.p1_value_label.setSizePolicy(sizePolicy1)
        self.p1_value_label.setFont(font7)
        self.p1_value_label.setStyleSheet(u"font: 9pt ")
        self.p1_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_11.addWidget(self.p1_value_label)


        self.test_gridLayout.addWidget(self.p1_widget, 2, 2, 1, 1)

        self.buzzer_Button = QPushButton(self.func_test_groupBox)
        self.buzzer_Button.setObjectName(u"buzzer_Button")
        sizePolicy7.setHeightForWidth(self.buzzer_Button.sizePolicy().hasHeightForWidth())
        self.buzzer_Button.setSizePolicy(sizePolicy7)
        self.buzzer_Button.setStyleSheet(u"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"")

        self.test_gridLayout.addWidget(self.buzzer_Button, 6, 3, 1, 1)

        self.pinout_Button = QPushButton(self.func_test_groupBox)
        self.pinout_Button.setObjectName(u"pinout_Button")
        sizePolicy7.setHeightForWidth(self.pinout_Button.sizePolicy().hasHeightForWidth())
        self.pinout_Button.setSizePolicy(sizePolicy7)
        self.pinout_Button.setStyleSheet(u"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"\n"
"\n"
"")

        self.test_gridLayout.addWidget(self.pinout_Button, 6, 2, 1, 1)

        self.pin_widget = QWidget(self.func_test_groupBox)
        self.pin_widget.setObjectName(u"pin_widget")
        sizePolicy6.setHeightForWidth(self.pin_widget.sizePolicy().hasHeightForWidth())
        self.pin_widget.setSizePolicy(sizePolicy6)
        self.verticalLayout_27 = QVBoxLayout(self.pin_widget)
        self.verticalLayout_27.setSpacing(1)
        self.verticalLayout_27.setObjectName(u"verticalLayout_27")
        self.verticalLayout_27.setContentsMargins(0, 0, 0, 0)
        self.pin_label = QLabel(self.pin_widget)
        self.pin_label.setObjectName(u"pin_label")
        sizePolicy1.setHeightForWidth(self.pin_label.sizePolicy().hasHeightForWidth())
        self.pin_label.setSizePolicy(sizePolicy1)
        self.pin_label.setFont(font9)
        self.pin_label.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);")
        self.pin_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_27.addWidget(self.pin_label)

        self.pin_label_1 = QLabel(self.pin_widget)
        self.pin_label_1.setObjectName(u"pin_label_1")
        sizePolicy1.setHeightForWidth(self.pin_label_1.sizePolicy().hasHeightForWidth())
        self.pin_label_1.setSizePolicy(sizePolicy1)
        self.pin_label_1.setFont(font10)
        self.pin_label_1.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"")
        self.pin_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_27.addWidget(self.pin_label_1)

        self.verticalLayout_27.setStretch(0, 3)
        self.verticalLayout_27.setStretch(1, 1)

        self.test_gridLayout.addWidget(self.pin_widget, 2, 0, 1, 1)

        self.p2_widget = QWidget(self.func_test_groupBox)
        self.p2_widget.setObjectName(u"p2_widget")
        sizePolicy1.setHeightForWidth(self.p2_widget.sizePolicy().hasHeightForWidth())
        self.p2_widget.setSizePolicy(sizePolicy1)
        self.p2_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_12 = QVBoxLayout(self.p2_widget)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.p2_label = QLabel(self.p2_widget)
        self.p2_label.setObjectName(u"p2_label")
        sizePolicy1.setHeightForWidth(self.p2_label.sizePolicy().hasHeightForWidth())
        self.p2_label.setSizePolicy(sizePolicy1)
        self.p2_label.setFont(font8)
        self.p2_label.setStyleSheet(u"")
        self.p2_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.p2_label)

        self.p2_value_label = QLabel(self.p2_widget)
        self.p2_value_label.setObjectName(u"p2_value_label")
        sizePolicy1.setHeightForWidth(self.p2_value_label.sizePolicy().hasHeightForWidth())
        self.p2_value_label.setSizePolicy(sizePolicy1)
        self.p2_value_label.setFont(font7)
        self.p2_value_label.setStyleSheet(u"font: 9pt ")
        self.p2_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.p2_value_label)


        self.test_gridLayout.addWidget(self.p2_widget, 2, 3, 1, 1)

        self.p0_widget = QWidget(self.func_test_groupBox)
        self.p0_widget.setObjectName(u"p0_widget")
        sizePolicy1.setHeightForWidth(self.p0_widget.sizePolicy().hasHeightForWidth())
        self.p0_widget.setSizePolicy(sizePolicy1)
        self.p0_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.verticalLayout_10 = QVBoxLayout(self.p0_widget)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.p0_label = QLabel(self.p0_widget)
        self.p0_label.setObjectName(u"p0_label")
        sizePolicy1.setHeightForWidth(self.p0_label.sizePolicy().hasHeightForWidth())
        self.p0_label.setSizePolicy(sizePolicy1)
        self.p0_label.setFont(font8)
        self.p0_label.setStyleSheet(u"")
        self.p0_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_10.addWidget(self.p0_label)

        self.p0_value_label = QLabel(self.p0_widget)
        self.p0_value_label.setObjectName(u"p0_value_label")
        sizePolicy1.setHeightForWidth(self.p0_value_label.sizePolicy().hasHeightForWidth())
        self.p0_value_label.setSizePolicy(sizePolicy1)
        self.p0_value_label.setFont(font7)
        self.p0_value_label.setStyleSheet(u"font: 9pt ")
        self.p0_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_10.addWidget(self.p0_value_label)


        self.test_gridLayout.addWidget(self.p0_widget, 2, 1, 1, 1)

        self.sound_value_label = QLabel(self.func_test_groupBox)
        self.sound_value_label.setObjectName(u"sound_value_label")
        self.sound_value_label.setFont(font11)
        self.sound_value_label.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.sound_value_label.setAlignment(Qt.AlignCenter)

        self.test_gridLayout.addWidget(self.sound_value_label, 5, 3, 1, 1)

        self.tt_widget = QWidget(self.func_test_groupBox)
        self.tt_widget.setObjectName(u"tt_widget")
        sizePolicy6.setHeightForWidth(self.tt_widget.sizePolicy().hasHeightForWidth())
        self.tt_widget.setSizePolicy(sizePolicy6)
        self.tt_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);\n"
"\n"
"")
        self.verticalLayout_7 = QVBoxLayout(self.tt_widget)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.tt_label = QLabel(self.tt_widget)
        self.tt_label.setObjectName(u"tt_label")
        sizePolicy1.setHeightForWidth(self.tt_label.sizePolicy().hasHeightForWidth())
        self.tt_label.setSizePolicy(sizePolicy1)
        self.tt_label.setFont(font8)
        self.tt_label.setStyleSheet(u"")
        self.tt_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_7.addWidget(self.tt_label)

        self.tt_value_label = QLabel(self.tt_widget)
        self.tt_value_label.setObjectName(u"tt_value_label")
        sizePolicy1.setHeightForWidth(self.tt_value_label.sizePolicy().hasHeightForWidth())
        self.tt_value_label.setSizePolicy(sizePolicy1)
        self.tt_value_label.setFont(font7)
        self.tt_value_label.setStyleSheet(u"font: 9pt ")
        self.tt_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_7.addWidget(self.tt_value_label)


        self.test_gridLayout.addWidget(self.tt_widget, 1, 3, 1, 1)

        self.manual_Button = QPushButton(self.func_test_groupBox)
        self.manual_Button.setObjectName(u"manual_Button")
        sizePolicy7.setHeightForWidth(self.manual_Button.sizePolicy().hasHeightForWidth())
        self.manual_Button.setSizePolicy(sizePolicy7)
        self.manual_Button.setFont(font9)
        self.manual_Button.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"")

        self.test_gridLayout.addWidget(self.manual_Button, 6, 0, 1, 1)

        self.cp210x_Button = QPushButton(self.func_test_groupBox)
        self.cp210x_Button.setObjectName(u"cp210x_Button")
        sizePolicy7.setHeightForWidth(self.cp210x_Button.sizePolicy().hasHeightForWidth())
        self.cp210x_Button.setSizePolicy(sizePolicy7)
        self.cp210x_Button.setStyleSheet(u"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"")

        self.test_gridLayout.addWidget(self.cp210x_Button, 6, 5, 1, 1)

        self.light_value_label = QLabel(self.func_test_groupBox)
        self.light_value_label.setObjectName(u"light_value_label")
        self.light_value_label.setFont(font11)
        self.light_value_label.setStyleSheet(u"background-color: rgb(203, 203, 203);")
        self.light_value_label.setAlignment(Qt.AlignCenter)

        self.test_gridLayout.addWidget(self.light_value_label, 5, 1, 1, 1)

        self.tp_widget = QWidget(self.func_test_groupBox)
        self.tp_widget.setObjectName(u"tp_widget")
        sizePolicy6.setHeightForWidth(self.tp_widget.sizePolicy().hasHeightForWidth())
        self.tp_widget.setSizePolicy(sizePolicy6)
        self.tp_widget.setStyleSheet(u"background-color: rgb(203, 203, 203);\n"
"\n"
"")
        self.verticalLayout_4 = QVBoxLayout(self.tp_widget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tp_label = QLabel(self.tp_widget)
        self.tp_label.setObjectName(u"tp_label")
        sizePolicy1.setHeightForWidth(self.tp_label.sizePolicy().hasHeightForWidth())
        self.tp_label.setSizePolicy(sizePolicy1)
        self.tp_label.setFont(font8)
        self.tp_label.setStyleSheet(u"")
        self.tp_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.tp_label)

        self.tp_value_label = QLabel(self.tp_widget)
        self.tp_value_label.setObjectName(u"tp_value_label")
        sizePolicy1.setHeightForWidth(self.tp_value_label.sizePolicy().hasHeightForWidth())
        self.tp_value_label.setSizePolicy(sizePolicy1)
        self.tp_value_label.setFont(font7)
        self.tp_value_label.setStyleSheet(u"font: 9pt ")
        self.tp_value_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.tp_value_label)


        self.test_gridLayout.addWidget(self.tp_widget, 1, 1, 1, 1)

        self.acceler_widget = QWidget(self.func_test_groupBox)
        self.acceler_widget.setObjectName(u"acceler_widget")
        sizePolicy6.setHeightForWidth(self.acceler_widget.sizePolicy().hasHeightForWidth())
        self.acceler_widget.setSizePolicy(sizePolicy6)
        self.verticalLayout_29 = QVBoxLayout(self.acceler_widget)
        self.verticalLayout_29.setSpacing(1)
        self.verticalLayout_29.setObjectName(u"verticalLayout_29")
        self.verticalLayout_29.setContentsMargins(0, 0, 0, 0)
        self.acceler_label = QLabel(self.acceler_widget)
        self.acceler_label.setObjectName(u"acceler_label")
        sizePolicy1.setHeightForWidth(self.acceler_label.sizePolicy().hasHeightForWidth())
        self.acceler_label.setSizePolicy(sizePolicy1)
        self.acceler_label.setFont(font9)
        self.acceler_label.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);")
        self.acceler_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_29.addWidget(self.acceler_label)

        self.acceler_label_1 = QLabel(self.acceler_widget)
        self.acceler_label_1.setObjectName(u"acceler_label_1")
        sizePolicy1.setHeightForWidth(self.acceler_label_1.sizePolicy().hasHeightForWidth())
        self.acceler_label_1.setSizePolicy(sizePolicy1)
        self.acceler_label_1.setFont(font10)
        self.acceler_label_1.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"")
        self.acceler_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_29.addWidget(self.acceler_label_1)

        self.verticalLayout_29.setStretch(0, 3)
        self.verticalLayout_29.setStretch(1, 1)

        self.test_gridLayout.addWidget(self.acceler_widget, 4, 0, 1, 1)

        self.light_widget = QWidget(self.func_test_groupBox)
        self.light_widget.setObjectName(u"light_widget")
        sizePolicy6.setHeightForWidth(self.light_widget.sizePolicy().hasHeightForWidth())
        self.light_widget.setSizePolicy(sizePolicy6)
        self.verticalLayout_30 = QVBoxLayout(self.light_widget)
        self.verticalLayout_30.setSpacing(1)
        self.verticalLayout_30.setObjectName(u"verticalLayout_30")
        self.verticalLayout_30.setContentsMargins(0, 0, 0, 0)
        self.light_label = QLabel(self.light_widget)
        self.light_label.setObjectName(u"light_label")
        sizePolicy1.setHeightForWidth(self.light_label.sizePolicy().hasHeightForWidth())
        self.light_label.setSizePolicy(sizePolicy1)
        self.light_label.setFont(font9)
        self.light_label.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);")
        self.light_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_30.addWidget(self.light_label)

        self.light_label_1 = QLabel(self.light_widget)
        self.light_label_1.setObjectName(u"light_label_1")
        sizePolicy1.setHeightForWidth(self.light_label_1.sizePolicy().hasHeightForWidth())
        self.light_label_1.setSizePolicy(sizePolicy1)
        self.light_label_1.setFont(font10)
        self.light_label_1.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"")
        self.light_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_30.addWidget(self.light_label_1)

        self.verticalLayout_30.setStretch(0, 3)
        self.verticalLayout_30.setStretch(1, 1)

        self.test_gridLayout.addWidget(self.light_widget, 5, 0, 1, 1)

        self.sound_widget = QWidget(self.func_test_groupBox)
        self.sound_widget.setObjectName(u"sound_widget")
        sizePolicy6.setHeightForWidth(self.sound_widget.sizePolicy().hasHeightForWidth())
        self.sound_widget.setSizePolicy(sizePolicy6)
        self.verticalLayout_31 = QVBoxLayout(self.sound_widget)
        self.verticalLayout_31.setSpacing(1)
        self.verticalLayout_31.setObjectName(u"verticalLayout_31")
        self.verticalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.sound_label = QLabel(self.sound_widget)
        self.sound_label.setObjectName(u"sound_label")
        sizePolicy1.setHeightForWidth(self.sound_label.sizePolicy().hasHeightForWidth())
        self.sound_label.setSizePolicy(sizePolicy1)
        self.sound_label.setFont(font9)
        self.sound_label.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);")
        self.sound_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_31.addWidget(self.sound_label)

        self.sound_label_1 = QLabel(self.sound_widget)
        self.sound_label_1.setObjectName(u"sound_label_1")
        sizePolicy1.setHeightForWidth(self.sound_label_1.sizePolicy().hasHeightForWidth())
        self.sound_label_1.setSizePolicy(sizePolicy1)
        self.sound_label_1.setFont(font10)
        self.sound_label_1.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"")
        self.sound_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_31.addWidget(self.sound_label_1)

        self.verticalLayout_31.setStretch(0, 3)
        self.verticalLayout_31.setStretch(1, 1)

        self.test_gridLayout.addWidget(self.sound_widget, 5, 2, 1, 1)

        self.mag_widget = QWidget(self.func_test_groupBox)
        self.mag_widget.setObjectName(u"mag_widget")
        sizePolicy6.setHeightForWidth(self.mag_widget.sizePolicy().hasHeightForWidth())
        self.mag_widget.setSizePolicy(sizePolicy6)
        self.verticalLayout_32 = QVBoxLayout(self.mag_widget)
        self.verticalLayout_32.setSpacing(1)
        self.verticalLayout_32.setObjectName(u"verticalLayout_32")
        self.verticalLayout_32.setContentsMargins(0, 0, 0, 0)
        self.mag_label = QLabel(self.mag_widget)
        self.mag_label.setObjectName(u"mag_label")
        sizePolicy1.setHeightForWidth(self.mag_label.sizePolicy().hasHeightForWidth())
        self.mag_label.setSizePolicy(sizePolicy1)
        self.mag_label.setFont(font9)
        self.mag_label.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);")
        self.mag_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_32.addWidget(self.mag_label)

        self.mag_label_1 = QLabel(self.mag_widget)
        self.mag_label_1.setObjectName(u"mag_label_1")
        sizePolicy1.setHeightForWidth(self.mag_label_1.sizePolicy().hasHeightForWidth())
        self.mag_label_1.setSizePolicy(sizePolicy1)
        self.mag_label_1.setFont(font10)
        self.mag_label_1.setStyleSheet(u"background-color: rgb(255, 170, 127);\n"
"color: rgb(255, 255, 255);\n"
"")
        self.mag_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_32.addWidget(self.mag_label_1)

        self.verticalLayout_32.setStretch(0, 3)
        self.verticalLayout_32.setStretch(1, 1)

        self.test_gridLayout.addWidget(self.mag_widget, 5, 4, 1, 1)

        self.calc_button = QPushButton(self.func_test_groupBox)
        self.calc_button.setObjectName(u"calc_button")
        sizePolicy7.setHeightForWidth(self.calc_button.sizePolicy().hasHeightForWidth())
        self.calc_button.setSizePolicy(sizePolicy7)
        self.calc_button.setStyleSheet(u"font: 13pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(203, 203, 203);\n"
"")

        self.test_gridLayout.addWidget(self.calc_button, 4, 5, 1, 1)

        self.test_gridLayout.setRowStretch(1, 1)
        self.test_gridLayout.setRowStretch(2, 1)
        self.test_gridLayout.setRowStretch(4, 1)
        self.test_gridLayout.setRowStretch(5, 1)
        self.test_gridLayout.setRowStretch(6, 1)
        self.test_gridLayout.setColumnStretch(0, 1)
        self.test_gridLayout.setColumnStretch(1, 1)
        self.test_gridLayout.setColumnStretch(2, 1)
        self.test_gridLayout.setColumnStretch(3, 1)
        self.test_gridLayout.setColumnStretch(4, 1)
        self.test_gridLayout.setColumnStretch(5, 1)
        self.test_gridLayout.setColumnStretch(6, 1)

        self.verticalLayout_9.addLayout(self.test_gridLayout)


        self.gridLayout_3.addWidget(self.func_test_groupBox, 1, 0, 1, 5)

        self.retest_Button = QPushButton(self.func_widget)
        self.retest_Button.setObjectName(u"retest_Button")
        sizePolicy7.setHeightForWidth(self.retest_Button.sizePolicy().hasHeightForWidth())
        self.retest_Button.setSizePolicy(sizePolicy7)
        self.retest_Button.setStyleSheet(u"font: 16pt \"\u5fae\u8f6f\u96c5\u9ed1\";\n"
"color: rgb(0, 0, 127);\n"
"background-color: rgb(170, 255, 255);\n"
"\n"
"\n"
"\n"
"")

        self.gridLayout_3.addWidget(self.retest_Button, 0, 4, 1, 1)

        self.groupBox = QGroupBox(self.func_widget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setFont(font1)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setSpacing(10)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.repl_textEdit = QTextEdit(self.groupBox)
        self.repl_textEdit.setObjectName(u"repl_textEdit")
        sizePolicy1.setHeightForWidth(self.repl_textEdit.sizePolicy().hasHeightForWidth())
        self.repl_textEdit.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.repl_textEdit)


        self.gridLayout_3.addWidget(self.groupBox, 2, 0, 1, 2)

        self.widget_4 = QWidget(self.func_widget)
        self.widget_4.setObjectName(u"widget_4")
        self.verticalLayout_21 = QVBoxLayout(self.widget_4)
        self.verticalLayout_21.setSpacing(2)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setContentsMargins(2, 2, 2, 2)
        self.manual_change_Button = QPushButton(self.widget_4)
        self.manual_change_Button.setObjectName(u"manual_change_Button")
        sizePolicy5.setHeightForWidth(self.manual_change_Button.sizePolicy().hasHeightForWidth())
        self.manual_change_Button.setSizePolicy(sizePolicy5)
        self.manual_change_Button.setFont(font4)

        self.verticalLayout_21.addWidget(self.manual_change_Button)

        self.change_test_prj_Button = QPushButton(self.widget_4)
        self.change_test_prj_Button.setObjectName(u"change_test_prj_Button")
        sizePolicy5.setHeightForWidth(self.change_test_prj_Button.sizePolicy().hasHeightForWidth())
        self.change_test_prj_Button.setSizePolicy(sizePolicy5)
        self.change_test_prj_Button.setFont(font4)

        self.verticalLayout_21.addWidget(self.change_test_prj_Button)

        self.verticalLayout_21.setStretch(0, 1)
        self.verticalLayout_21.setStretch(1, 1)

        self.gridLayout_3.addWidget(self.widget_4, 0, 3, 1, 1)

        self.gridLayout_3.setRowStretch(0, 1)
        self.gridLayout_3.setRowStretch(1, 4)
        self.gridLayout_3.setRowStretch(2, 2)
        self.gridLayout_3.setColumnStretch(0, 3)
        self.gridLayout_3.setColumnStretch(1, 2)
        self.gridLayout_3.setColumnStretch(2, 1)
        self.gridLayout_3.setColumnStretch(3, 1)
        self.gridLayout_3.setColumnStretch(4, 2)
        self.gridLayout_3.setRowMinimumHeight(0, 1)
        self.gridLayout_3.setRowMinimumHeight(1, 1)
        self.gridLayout_3.setRowMinimumHeight(2, 1)

        self.gridLayout.addWidget(self.func_widget, 0, 0, 1, 1)

        self.TabWidget.addTab(self.func_test_tab, "")

        self.verticalLayout.addWidget(self.TabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1112, 23))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.TabWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.TabWidget.setTabText(self.TabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"\u70e7\u5f55", None))
        self.carve_serial_groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u4e32\u53e3\u8bbe\u7f6e", None))
        self.refresh_carve_Button.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\u956d\u96d5\u673a\u8bbe\u7f6e", None))
        self.iPLabel.setText(QCoreApplication.translate("MainWindow", u"IP:", None))
        self.portLabel.setText(QCoreApplication.translate("MainWindow", u"port", None))
        self.carve_mac_label.setText(QCoreApplication.translate("MainWindow", u"MAC", None))
        self.carve_start_Button.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb", None))
        self.TabWidget.setTabText(self.TabWidget.indexOf(self.carve_tab), QCoreApplication.translate("MainWindow", u"\u956d\u96d5", None))
        self.para_Button.setText(QCoreApplication.translate("MainWindow", u"\u53c2\u6570\u8303\u56f4\u8bbe\u7f6e", None))
        self.change_prj_checkBox.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u8f6c\u51fa\u5382\u7a0b\u5e8f", None))
        self.hw_Label.setText(QCoreApplication.translate("MainWindow", u"\u786c\u4ef6\u7248\u672c:", None))
        self.hw_LineEdit.setText(QCoreApplication.translate("MainWindow", u"01", None))
        self.result_func_label.setText("")
        self.func_log_groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u8bb0\u5f55", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"\u8bbe\u7f6e", None))
        self.com_func_Button.setText(QCoreApplication.translate("MainWindow", u"\u8fde\u63a5\u4e32\u53e3", None))
        self.refresh_func_Button.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0", None))
        self.func_test_groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u6d4b\u8bd5\u9879\u76ee", None))
        self.acc_x_label.setText("")
        self.acc_x_value_label.setText("")
        self.p3_label.setText(QCoreApplication.translate("MainWindow", u"P3", None))
        self.p3_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.ty_label.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.ty_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.touch_label.setText(QCoreApplication.translate("MainWindow", u"\u89e6\u6478:", None))
        self.touch_label_1.setText(QCoreApplication.translate("MainWindow", u"\u5224\u65ad\u6807\u51c6:", None))
        self.to_label.setText(QCoreApplication.translate("MainWindow", u"O", None))
        self.to_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.mag_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.tn_label.setText(QCoreApplication.translate("MainWindow", u"N", None))
        self.tn_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.th_label.setText(QCoreApplication.translate("MainWindow", u"H", None))
        self.th_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.display_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt;\">\u65e0\u50cf\u7d20\u574f\u70b9 \u5feb\u6377\u952e\u6570\u5b571</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.display_Button.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u5c4f/RGB\u706f", None))
#if QT_CONFIG(tooltip)
        self.audio_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt;\">\u5f55\u97f3\u6d4b\u8bd5PASS \u5feb\u6377\u952e\u6570\u5b576</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.audio_Button.setText(QCoreApplication.translate("MainWindow", u"\u5f55\u97f3\u6d4b\u8bd5", None))
        self.acc_value_label.setText("")
        self.acc_y_label.setText("")
        self.acc_y_value_label.setText("")
#if QT_CONFIG(tooltip)
        self.current_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt;\">\u6b63\u5e38\u5de5\u4f5c\u7535\u6d41\u57280.2~0.3A</span></p><p><span style=\" font-size:10pt;\">\u5feb\u6377\u952e\u6570\u5b574</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.current_Button.setWhatsThis(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.current_Button.setText(QCoreApplication.translate("MainWindow", u"\u5de5\u4f5c\u7535\u6d41", None))
        self.acc_z_label.setText(QCoreApplication.translate("MainWindow", u"\u5e73\u653e", None))
        self.acc_z_value_label.setText("")
        self.p1_label.setText(QCoreApplication.translate("MainWindow", u"P1", None))
        self.p1_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.buzzer_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt;\">- \u6309\u952e\u624b\u611f\u597d,\u7262\u56fa</span></p><p><span style=\" font-size:10pt;\">- \u8702\u9e23\u5668\u58f0\u97f3\u54cd\u4eae</span></p><p><span style=\" font-size:10pt;\">\u5feb\u6377\u952e\u6570\u5b573</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.buzzer_Button.setText(QCoreApplication.translate("MainWindow", u"\u8702\u9e23\u5668/A,B\u6309\u952e", None))
#if QT_CONFIG(tooltip)
        self.pinout_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>\u5feb\u6377\u952e\u6570\u5b572</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pinout_Button.setText(QCoreApplication.translate("MainWindow", u"\u5f15\u811a\u8f93\u51fa", None))
        self.pin_label.setText(QCoreApplication.translate("MainWindow", u"\u5f15\u811a:", None))
        self.pin_label_1.setText(QCoreApplication.translate("MainWindow", u"\u5224\u65ad\u6807\u51c6:", None))
        self.p2_label.setText(QCoreApplication.translate("MainWindow", u"P2", None))
        self.p2_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.p0_label.setText(QCoreApplication.translate("MainWindow", u"P0", None))
        self.p0_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.sound_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.tt_label.setText(QCoreApplication.translate("MainWindow", u"T", None))
        self.tt_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.manual_Button.setText(QCoreApplication.translate("MainWindow", u"\u624b\u5de5\u786e\u8ba4:", None))
#if QT_CONFIG(tooltip)
        self.cp210x_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt;\">\u786e\u8ba4\u4e32\u53e3\u6307\u793a\u706f\u95ea\u70c1 </span></p><p><span style=\" font-size:10pt;\">\u5feb\u6377\u952e\u6570\u5b575</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.cp210x_Button.setText(QCoreApplication.translate("MainWindow", u"\u4e32\u53e3\u6307\u793a\u706f", None))
        self.light_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.tp_label.setText(QCoreApplication.translate("MainWindow", u"P", None))
        self.tp_value_label.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.acceler_label.setText(QCoreApplication.translate("MainWindow", u"\u52a0\u901f\u5ea6:", None))
        self.acceler_label_1.setText(QCoreApplication.translate("MainWindow", u"\u5224\u65ad\u6807\u51c6:", None))
        self.light_label.setText(QCoreApplication.translate("MainWindow", u"\u5149\u7ebf:", None))
        self.light_label_1.setText(QCoreApplication.translate("MainWindow", u"\u5224\u65ad\u6807\u51c6:", None))
        self.sound_label.setText(QCoreApplication.translate("MainWindow", u"\u58f0\u97f3:", None))
        self.sound_label_1.setText(QCoreApplication.translate("MainWindow", u"\u5224\u65ad\u6807\u51c6:", None))
        self.mag_label.setText(QCoreApplication.translate("MainWindow", u"\u78c1\u573a\u65b9\u5411:", None))
        self.mag_label_1.setText(QCoreApplication.translate("MainWindow", u"\u5224\u65ad\u6807\u51c6:", None))
#if QT_CONFIG(tooltip)
        self.calc_button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>\u540c\u65f6\u6309P0\u548cP2\u6309\u952e\u8fdb\u5165</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.calc_button.setText(QCoreApplication.translate("MainWindow", u"\u52a0\u901f\u5ea6\u6821\u51c6", None))
#if QT_CONFIG(tooltip)
        self.retest_Button.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>\u5feb\u6377\u952e\u6570\u5b570</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.retest_Button.setText(QCoreApplication.translate("MainWindow", u"\u91cd\u65b0\u6d4b\u8bd5", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"REPL", None))
        self.repl_textEdit.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'SimSun'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.manual_change_Button.setText(QCoreApplication.translate("MainWindow", u"\u8f6c\u51fa\u5382\u7a0b\u5e8f", None))
        self.change_test_prj_Button.setText(QCoreApplication.translate("MainWindow", u"\u8f6c\u6d4b\u8bd5\u7a0b\u5e8f", None))
        self.TabWidget.setTabText(self.TabWidget.indexOf(self.func_test_tab), QCoreApplication.translate("MainWindow", u"\u529f\u80fd\u6d4b\u8bd5", None))
    # retranslateUi

