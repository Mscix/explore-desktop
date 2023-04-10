import pytest
import PySide6
from pytestqt.qtbot import QtBot
from PySide6.QtTest import QTest
import exploredesktop.main_window as mw
from PySide6.QtCore import Qt
from PySide6 import QtWidgets, QtCore
from time import sleep


def connect_device(qtbot):
    window = mw.MainWindow()
    bt = window.bt_frame
    input_field = bt.ui.dev_name_input
    qtbot.addWidget(input_field)
    qtbot.keyClicks(input_field, "855E")
    qtbot.keyClick(input_field, Qt.Key_Enter)
    sleep(5)
    qtbot.wait(5000)
    return window


# Call to this function right before clicking the UI element that will result in a QMessageBox pop up
def handle_dialog(qtbot, button_type=QtWidgets.QMessageBox.Ok, text_to_test=''):
    def helper():
        messagebox = QtWidgets.QApplication.activeWindow()
        if text_to_test != '':
            assert messagebox.text() == text_to_test  # Messages.IMP_INFO
        ok_button = messagebox.button(button_type)
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    QtCore.QTimer.singleShot(100, helper())

class TestMainWindow:
    def test_close_window(self, qtbot):
        window = mw.MainWindow()
        qtbot.addWidget(window)
        window.show()
        assert window.isVisible()
        QTest.qWaitForWindowExposed(window)
        window.close()
        assert not window.isVisible()







