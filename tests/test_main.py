import pytest
import PySide6
from pytestqt.qtbot import QtBot
from PySide6.QtTest import QTest
import exploredesktop.main_window as mw



class TestMainWindow:
    def test_close_window(self, qtbot):
        window = mw.MainWindow()
        qtbot.addWidget(window)
        window.show()
        assert window.isVisible()
        QTest.qWaitForWindowExposed(window)
        window.close()
        assert not window.isVisible()





