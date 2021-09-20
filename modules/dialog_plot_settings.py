# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_plot_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.1.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(396, 216)
        self.layoutWidget = QWidget(Dialog)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(3, 10, 391, 201))
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.cb_offset = QCheckBox(self.layoutWidget)
        self.cb_offset.setObjectName(u"cb_offset")

        self.verticalLayout.addWidget(self.cb_offset)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.comboBox = QComboBox(self.layoutWidget)
        self.comboBox.setObjectName(u"comboBox")

        self.horizontalLayout_2.addWidget(self.comboBox)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_3 = QLabel(self.layoutWidget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout.addWidget(self.label_3)

        self.value_lowpass = QLineEdit(self.layoutWidget)
        self.value_lowpass.setObjectName(u"value_lowpass")

        self.horizontalLayout.addWidget(self.value_lowpass)

        self.value_highpass = QLineEdit(self.layoutWidget)
        self.value_highpass.setObjectName(u"value_highpass")

        self.horizontalLayout.addWidget(self.value_highpass)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_4 = QLabel(self.layoutWidget)
        self.label_4.setObjectName(u"label_4")
        font = QFont()
        font.setPointSize(10)
        font.setItalic(True)
        self.label_4.setFont(font)

        self.verticalLayout.addWidget(self.label_4)

        self.buttonBox = QDialogButtonBox(self.layoutWidget)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(20, 20, 376, 23))
        self.label_5.setFont(font)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p align=\"center\"><span style=\" font-weight:600;\">Visualization Settings</span></p></body></html>", None))
        self.cb_offset.setText(QCoreApplication.translate("Dialog", u"Baseline Correction", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Notch Filter", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Band pass filter", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"If only one value is introduced, the filter will be a high/low pass", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"If only one value is introduced, the filter will be a high/low pass", None))
    # retranslateUi

