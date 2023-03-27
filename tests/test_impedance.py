import pytest
import PySide6
from time import sleep
from pytestqt.qtbot import QtBot
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
import unittest
from unittest.mock import Mock, MagicMock, patch
from exploredesktop.modules.app_settings import ImpModes
from exploredesktop.modules.explore_interface import ExploreInterface
from collections import namedtuple
from explorepy.settings_manager import SettingsManager
from test_main import connect_device
from exploredesktop.modules.app_settings import Messages
from unittest.mock import patch

# TODO tests todo
# TODO check if filters have been applied
# TODO test upper hotbar for evrything output file and stuff
# TODO last week for Andrea
# Wednesday vorbeikommen MEntalab anschrieben

def get_device_mock():
    e_interface = ExploreInterface()
    mock_interface = Mock(spec=e_interface)
    mock_interface.is_connected.return_value = False

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
    mock_interface.device_name = 'Explore_1234'
    mock_interface.chan_dict_list = [{'input': 'ch1', 'enable': 1, 'name': 'ch1', 'type': 'EEG'}, {'input': 'ch2', 'enable': 1, 'name': 'ch2', 'type': 'EEG'}, {'input': 'ch3', 'enable': 1, 'name': 'ch3', 'type': 'EEG'}, {'input': 'ch4', 'enable': 1, 'name': 'ch4', 'type': 'EEG'}]
    mock_interface.device_chan = 4  # TODO problems
    # Mocking all methods of ExplorePy Interface

    # Mock sampling_rate(), which is a property
    # mock_interface.sampling_rate.return_value = 250.0
    mock_interface.sampling_rate = 250.0

    # Mock n_active_chan()
    # return sum(self.chan_mask) so probably 4
    mock_interface.n_active_chan = 4

    # Mock is_recording()
    mock_interface.is_recording.return_value = True

    # Mock is_pushing_lsl(), No idea what that is ask in Meeting
    mock_interface.is_pushing_lsl.return_value = True

    # Mock scan_devices(), done

    # Mock connect(), done?

    # Mock disconnect()

    # Mock set_chan_mask()
    # self.chan_mask and self.settings.set_adc_mask are set
    def set_chan_mask_se(a):
        mock_interface.chan_mask = [1, 1, 1, 1]
        mock_interface.settings.adc_mask = [1, 1, 1, 1]

    mock_interface.set_chan_mask = set_chan_mask_se

    # Mock set_chan_dict_list()
    def set_chan_dict_list_se(a):
        pass  # doing a pass as the chan_dict list should not change and is set before
    mock_interface.set_chan_dict_list = set_chan_dict_list_se

    # Mock get_chan_dict_list()
    # should still work? TODO: does not work


    # Mock _set_n_chan(packet: explorepy.packet.EEG)

    # Mock get_device_chan() -> int
    mock_interface.get_device_chan.return_value = 4

    # Mock active_chan_list(self, custom_name=False)
    # could work by itself

    # Mock full_chan_list(self, custom_name) -> list
    # Could also work by itself

    # Mock measure_imp(self, imp_callback: Callable) -> bool
    # Lets go with returning True
    def measure_imp_se(*args, **kwargs):
        return True
    mock_interface.measure_imp.return_value = measure_imp_se

    # Mock disable_imp(self, imp_callback: Callable) -> bool
    def disable_imp_se(*args, **kwargs):
        return True
    mock_interface.disable_imp.return_value = disable_imp_se()

    # Mock set_sampling_rate(self, sampling_rate: int) -> Optional[bool]
    def set_sampling_rate_se(*args, **kwargs):
        # Don't want to change anything might break so check if ok
        return False
    mock_interface.set_sampling_rate = set_sampling_rate_se

    # Problem when measure_imp clicked the explorepy is used where it is not explore_interface mock

    # Mock subscribe(self, callback: Callable, topic: TOPICS) -> None:
    # TOPIC:
    # Callable:
    # self.stream_processor.subscribe(callback, topic)
    # def subscribe_se():
    return mock_interface


def navigate_to_impedance_view(qtbot, window):
    imp_button = window.ui.btn_impedance
    # change to impedance view
    qtbot.addWidget(imp_button)
    qtbot.mouseClick(imp_button, Qt.LeftButton)


class TestImpedance:

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
            imp.explorer = device_mock
            imp.model.explorer = device_mock
            imp_button = app.ui.btn_impedance

            exg = app.exg_plot
            exg.explorer = device_mock
            exg.model.explorer = device_mock

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

    # Can only always test one test as each test needs its own device...

    """
    def test_no_mock(self, qtbot):
        app = connect_device(qtbot)
        imp = app.imp_frame
        navigate_to_impedance_view(qtbot, app)
        # press dropdown and select Wet Electrodes
        drop_down = imp.ui.imp_mode
        qtbot.addWidget(drop_down)
        qtbot.keyClicks(drop_down, ImpModes.WET.value)
        # Press measure btn
        meas_btn = imp.ui.btn_imp_meas
        qtbot.mouseClick(meas_btn, Qt.LeftButton)
        qtbot.wait(1000)
        # Check the color
        # disable Impedance measurement
        qtbot.mouseClick(meas_btn, Qt.LeftButton)
        # Change to Dry Electrodes
        qtbot.keyClicks(drop_down, ImpModes.DRY.value)
        # start measuring Impedance
        qtbot.mouseClick(meas_btn, Qt.LeftButton)
    """


    def test_pop_up(self, qtbot):
        # Helper method where Qtbot connects the device and returns QMainWindow instance
        window = connect_device(qtbot)
        # Only for visualisation
        window.show()
        # Helper method where Qtbot navigates to the Impedance View Frame
        navigate_to_impedance_view(qtbot, window)
        imp = window.imp_frame
        # Get the reference to the question mark button in the Impedance Frame
        info = imp.ui.imp_meas_info
        # Give the reference to qtbot so it know it
        qtbot.addWidget(info)
        # Get instance of the currently running application
        # The application was started by qtbot fixture
        app = QApplication.instance()
        # print(app.topLevelWidgets())
        def handle_dialog():
            msg_box = None
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMessageBox):
                    print(widget.text())
                    if widget.text() == Messages.IMP_INFO:
                        assert True
                        msg_box = widget
            qtbot.mouseClick(msg_box.button(QMessageBox.Ok), Qt.LeftButton)
        QTimer.singleShot(500, handle_dialog())
        qtbot.mouseClick(info, Qt.LeftButton, delay=0)
        qtbot.wait(2000)



