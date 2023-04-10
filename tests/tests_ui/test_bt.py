import pytest
import PySide6
from time import sleep
from pytestqt.qtbot import QtBot
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
import exploredesktop.main_window as mw
import unittest
from unittest.mock import Mock, MagicMock, patch
from exploredesktop.modules.bt_module import BTFrameView
from collections import namedtuple

from exploredesktop.modules.explore_interface import ExploreInterface



##### Mocks ######

# this will be the default ExplorerInterface Mock object
def get_device_mock_for_BT():
    e_interface = ExploreInterface()
    mock_interface = Mock(spec=e_interface)
    mock_interface.is_connected.return_value = False

    # side effect for when accessing is_connected
    # sorry have to do this (check if there is another way with lambda or else)
    def connect_se():
        mock_interface.is_connected = True
    mock_interface.connect = connect_se

    def disconnect_se():
        mock_interface.is_connected = False
    mock_interface.disconnect = disconnect_se

    NearbyDeviceInfo = namedtuple("NearbyDeviceInfo", ["name", "address", "is_paired"])
    mock_interface.scan_devices.return_value = [NearbyDeviceInfo("Explore_1234", "abcde", True)]  # True = Paired
    return mock_interface


class TestBT:
    def test_connect_w_add_scanned_device_mock(self, qtbot):
        app = mw.MainWindow()
        app.show()
        og_bt = app.bt_frame
        with patch.object(BTFrameView, 'connect') as mock_connect:
            # Set behaviour for mocked connect and test
            mock_connect.return_value = True
            result = app.bt_frame.connect()
            mock_connect.assert_called_once_with()
            assert result
            # instantiate BT with mocked connect method
            app.bt_frame = BTFrameView(og_bt.ui)
            bt = app.bt_frame
            bt.explorer = get_device_mock_for_BT()
            # Skip scanning for devices as not possible to mock
            # Add device to scanned list
            device_list = bt.explorer.scan_devices()
            bt.add_scanned_devices(device_list)
            # Select first device shown in list
            dl_ui = bt.ui.list_devices
            item_rect = dl_ui.visualItemRect(dl_ui.item(0))
            qtbot.mouseClick(dl_ui.viewport(), Qt.LeftButton, pos=item_rect.center())
            # Click 'Connect' button with Qtbot
            c_button = bt.ui.btn_connect
            qtbot.addWidget(c_button)
            qtbot.mouseClick(c_button, Qt.LeftButton)
            assert bt.explorer.is_connected

    def test_connect_w_input_device_short_name(self, qtbot):
        app = mw.MainWindow()
        og_bt = app.bt_frame
        with patch.object(BTFrameView, 'connect') as mock_connect:
            # Set behaviour for mocked connect and test
            mock_connect.return_value = True
            result = app.bt_frame.connect()
            mock_connect.assert_called_once_with()
            assert result
            # instantiate BT with mocked connect method
            app.bt_frame = BTFrameView(og_bt.ui)
            bt = app.bt_frame
            bt.explorer = get_device_mock_for_BT()
            input_field = bt.ui.dev_name_input
            qtbot.addWidget(input_field)
            qtbot.keyClicks(input_field, "1234")
            qtbot.keyClick(input_field, Qt.Key_Enter)
            assert bt.explorer.is_connected

    def test_connect_w_input_device_full_name(self, qtbot):
        app = mw.MainWindow()
        og_bt = app.bt_frame
        with patch.object(BTFrameView, 'connect') as mock_connect:
            # Set behaviour for mocked connect and test
            mock_connect.return_value = True
            result = app.bt_frame.connect()
            mock_connect.assert_called_once_with()
            assert result
            # instantiate BT with mocked connect method
            app.bt_frame = BTFrameView(og_bt.ui)
            bt = app.bt_frame
            bt.explorer = get_device_mock_for_BT()
            input_field = bt.ui.dev_name_input
            qtbot.addWidget(input_field)
            qtbot.keyClicks(input_field, "Explore_1234")
            qtbot.keyClick(input_field, Qt.Key_Enter)
            assert bt.explorer.is_connected

    """
    def test_connect_turns_connecting(self, qtbot):
        app = mw.MainWindow()
        og_bt = app.bt_frame
        with patch.object(BTFrameView, 'connect') as mock_connect:
            # Set behaviour for mocked connect and test
            mock_connect.return_value = True
            result = app.bt_frame.connect()
            mock_connect.assert_called_once_with()
            assert result
            # instantiate BT with mocked connect method
            app.bt_frame = BTFrameView(og_bt.ui)
            bt = app.bt_frame
            bt.explorer = get_device_mock_for_BT()
            scan_btn = bt.ui.btn_scan
            # TODO
            with qtbot.waitSignal(scan_btn, timeout=3000) as blocker:
                qtbot.addWidget(scan_btn)
                qtbot.mouseClick(scan_btn, Qt.LeftButton)
        """


    def test_disconnect(self, qtbot):
        # footer removes all information about device
        # All pages unreachable but the home page??? how to test this lol
        app = mw.MainWindow()
        og_bt = app.bt_frame
        with patch.object(BTFrameView, 'connect') as mock_connect:
            # Set behaviour for mocked connect and test
            mock_connect.return_value = True
            result = app.bt_frame.connect()
            mock_connect.assert_called_once_with()
            assert result
            # instantiate BT with mocked connect method
            app.bt_frame = BTFrameView(og_bt.ui)
            bt = app.bt_frame
            bt.explorer = get_device_mock_for_BT()
            input_field = bt.ui.dev_name_input
            qtbot.addWidget(input_field)
            qtbot.keyClicks(input_field, "Explore_1234")
            qtbot.keyClick(input_field, Qt.Key_Enter)
            sleep(4)
            assert bt.explorer.is_connected







