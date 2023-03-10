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
from exploredesktop.modules.settings_module import SettingsFrameView, ConfigTableModel
from exploredesktop.modules.app_settings import ImpModes
from exploredesktop.modules.explore_interface import ExploreInterface
from collections import namedtuple
from explorepy.settings_manager import SettingsManager


def get_device_mock():
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

    se = SettingsManager('Explore_1234')
    se_dict = {
        # "hardware_mask"
        "software_mask": [1, 1, 1, 1],
        "adc_mask": [1, 1, 1, 1],
        # "channel_name"
        "channel_count": 4,
        "mac_address": '00: 13:43: A1:85: 5E',
        # "board_id"
        "sampling_rate": 250.0
    }
    mock_settings_manager = Mock(spec=se)
    mock_settings_manager.load_current_settings.return_value = se_dict
    mock_interface.settings = mock_settings_manager
    # load current settings soll immer das gleiche dict widergeben

    return mock_interface



class TestImpedance:

    # ExploreInterface
    # need device sampling rate
    # chan_dict_list
    # settings = SettingsManager(device_name)
    # Device info: {'device_name': 'Explore_855E', 'firmware_version': '2.1.5', 'adc_mask': [0, 0, 0, 0, 1, 1, 1, 1], 'sampling_rate': 250.0}

    # adc_mask: [1, 1, 1, 1] list of ints ?
    # channel_count: 4 int
    # firmware_version: 2.1.5 str
    # mac_address: 00: 13:43: A1:85: 5E str
    # sampling_rate: 250.0 float
    # software_mask: [1, 1, 1, 1] list

    def test_imp(self, qtbot):
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
            device_mock = get_device_mock()
            bt.explorer = device_mock
            app.settings_frame.explorer = device_mock

            input_field = bt.ui.dev_name_input
            qtbot.addWidget(input_field)
            qtbot.keyClicks(input_field, "1234")
            qtbot.keyClick(input_field, Qt.Key_Enter)


    """
    def test_impedance_with_mock(self, qtbot):
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
            device_mock = get_device_mock()
            bt.explorer = device_mock
            app.settings_frame.explorer = device_mock



            input_field = bt.ui.dev_name_input
            qtbot.addWidget(input_field)
            qtbot.keyClicks(input_field, "1234")
            qtbot.keyClick(input_field, Qt.Key_Enter)
            assert bt.explorer.is_connected
            settings = app.settings_frame
            settings.explorer.device_name = 'Explore_1234'
            settings.ui.table_settings.setModel(ConfigTableModel([{'input': 'ch1', 'enable': 1, 'name': 'ch1', 'type': 'EEG'}, {'input': 'ch2', 'enable': 1, 'name': 'ch2', 'type': 'EEG'}, {'input': 'ch3', 'enable': 1, 'name': 'ch3', 'type': 'EEG'}, {'input': 'ch4', 'enable': 1, 'name': 'ch4', 'type': 'EEG'}])) #fillthis?
            # setup_settings_frame one on init
            # and once on connect because we connect by mock it breaks...

            imp = app.imp_frame
            imp_button = app.ui.btn_impedance
            # press apply changes so the popup does not interfere
            apply_btn = settings.ui.btn_apply_settings
            qtbot.addWidget(apply_btn)
            # set the frame with default settings of the device
            settings.setup_settings_frame()
            qtbot.mouseClick(apply_btn, Qt.LeftButton)
            # change to impedance view
            qtbot.addWidget(imp_button)
            qtbot.mouseClick(imp_button, Qt.LeftButton)
            # press dropdown and select Wet Electrodes
            drop_down = imp.ui.imp_mode
            qtbot.addWidget(drop_down)
            qtbot.keyClicks(drop_down, ImpModes.WET.value)
            # Press measure btn
            meas_btn = imp.ui.btn_imp_meas
            qtbot.mouseClick(meas_btn, Qt.LeftButton)
            # sleep(5)
            # disable Impedance measurement
            qtbot.mouseClick(meas_btn, Qt.LeftButton)
            # Change to Dry Electrodes
            qtbot.keyClicks(drop_down, ImpModes.DRY.value)
            # start measuring Impedance
            qtbot.mouseClick(meas_btn, Qt.LeftButton)
            sleep(3)
            # check if color changes or something??
    """



