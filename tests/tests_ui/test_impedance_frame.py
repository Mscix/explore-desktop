from PySide6.QtWidgets import QApplication, QMessageBox
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt, QTimer
from unittest.mock import Mock
from exploredesktop.modules.app_settings import ImpModes
from exploredesktop.modules.explore_interface import ExploreInterface
from collections import namedtuple
from explorepy.settings_manager import SettingsManager
from test_window import connect_device
from exploredesktop.modules.app_settings import Messages



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
    mock_interface.chan_dict_list = [{'input': 'ch1', 'enable': 1, 'name': 'ch1', 'type': 'EEG'},
                                     {'input': 'ch2', 'enable': 1, 'name': 'ch2', 'type': 'EEG'},
                                     {'input': 'ch3', 'enable': 1, 'name': 'ch3', 'type': 'EEG'},
                                     {'input': 'ch4', 'enable': 1, 'name': 'ch4', 'type': 'EEG'}]
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


def test_impedance_modes(qtbot):
    window = connect_device(qtbot)
    # window.show()
    imp = window.imp_frame
    navigate_to_impedance_view(qtbot, window)
    # press dropdown and select Wet Electrodes
    drop_down = imp.ui.imp_mode
    qtbot.addWidget(drop_down)
    qtbot.keyClicks(drop_down, ImpModes.WET.value)
    # Press measure btn
    meas_btn = imp.ui.btn_imp_meas
    qtbot.mouseClick(meas_btn, Qt.LeftButton)
    qtbot.wait(1000)
    # Check the color
    # get Impframe view call get_stylesheet check color?
    imp_model = imp.get_graph().model
    assert imp_model.mode == ImpModes.WET
    # disable Impedance measurement
    qtbot.mouseClick(meas_btn, Qt.LeftButton)
    # Change to Dry Electrodes
    qtbot.keyClicks(drop_down, ImpModes.DRY.value)
    assert imp_model.mode == ImpModes.DRY
    # stop measuring Impedance
    qtbot.mouseClick(meas_btn, Qt.LeftButton)


def test_info_pop_up(qtbot):
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

    def handle_dialog():
        # Get an instance of the currently open window and answer it
        messagebox = QApplication.activeWindow()
        assert messagebox.text() == Messages.IMP_INFO
        ok_button = messagebox.button(QMessageBox.Ok)
        qtbot.mouseClick(ok_button, Qt.LeftButton)

    QTimer.singleShot(100, handle_dialog)
    qtbot.mouseClick(info, Qt.LeftButton, delay=1)


