# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_recording_settings_light.ui'
##
## Created by: Qt User Interface Compiler version 6.2.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 200)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lbl_step2 = QLabel(Dialog)
        self.lbl_step2.setObjectName(u"lbl_step2")

        self.horizontalLayout_3.addWidget(self.lbl_step2)

        self.rdbtn_csv = QRadioButton(Dialog)
        self.rdbtn_csv.setObjectName(u"rdbtn_csv")

        self.horizontalLayout_3.addWidget(self.rdbtn_csv)

        self.rdbtn_edf = QRadioButton(Dialog)
        self.rdbtn_edf.setObjectName(u"rdbtn_edf")

        self.horizontalLayout_3.addWidget(self.rdbtn_edf)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.lbl_step1 = QLabel(Dialog)
        self.lbl_step1.setObjectName(u"lbl_step1")

        self.verticalLayout.addWidget(self.lbl_step1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(54, 0))

        self.horizontalLayout.addWidget(self.label_2)

        self.input_filepath = QLineEdit(Dialog)
        self.input_filepath.setObjectName(u"input_filepath")

        self.horizontalLayout.addWidget(self.input_filepath)

        self.btn_browse = QPushButton(Dialog)
        self.btn_browse.setObjectName(u"btn_browse")

        self.horizontalLayout.addWidget(self.btn_browse)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(54, 0))

        self.horizontalLayout_4.addWidget(self.label_3)

        self.input_file_name = QLineEdit(Dialog)
        self.input_file_name.setObjectName(u"input_file_name")

        self.horizontalLayout_4.addWidget(self.input_file_name)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.spinBox = QSpinBox(Dialog)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setMaximum(1000000)
        self.spinBox.setValue(3600)

        self.horizontalLayout_2.addWidget(self.spinBox)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.lbl_step2.setText(QCoreApplication.translate("Dialog", u"1. Select the file format :     ", None))
        self.rdbtn_csv.setText(QCoreApplication.translate("Dialog", u"csv", None))
        self.rdbtn_edf.setText(QCoreApplication.translate("Dialog", u"edf", None))
        self.lbl_step1.setText(QCoreApplication.translate("Dialog", u"2. Select the folder and name to store the file:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Folder:", None))
        self.btn_browse.setText(QCoreApplication.translate("Dialog", u"Browse", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"File name:", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"3. Select recording time (s):", None))
    # retranslateUi

