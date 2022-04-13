import logging
import os

import explorepy._exceptions as xpy_ex
from PySide6.QtCore import Slot


from exploredesktop.modules.app_settings import (  # isort: skip
    ConnectionStatus,
    EnvVariables,
    Messages,
    Stylesheets
)
from exploredesktop.modules.tools import display_msg  # isort: skip
from exploredesktop.modules.worker import Worker  # isort: skip

logger = logging.getLogger("explorepy." + __name__)


class BTFrameView():
    """_summary_
    """
    def __init__(self, ui, model, threadpool) -> None:
        self.ui = ui
        self.model = model
        self.threadpool = threadpool

        self.signals = model.get_signals()
        self.explorer = model.get_explorer()

    def setup_ui_connections(self) -> None:
        """_summary_
        """
        self.ui.btn_connect.clicked.connect(self.connect_clicked)
        self.ui.dev_name_input.returnPressed.connect(self.connect_clicked)
        self.ui.btn_scan.clicked.connect(self.scan_clicked)

    #########################
    # Get device name functions
    #########################
    def get_device_from_le(self) -> str:
        """
        Get device name from line edit widget.
        If the input string does not contain the word Explore it will added

        Returns:
            str: full name of the device (Explore_XXXX). Empty if format is not correct
        """

        input_name = self.ui.dev_name_input.text()

        if not input_name.startswith("Explore_") and len(input_name) == 4:
            device_name = "Explore_" + input_name
        elif input_name.startswith("Explore_"):
            device_name = input_name
        else:
            device_name = ""

        if len(device_name) != 12:
            device_name = ""

        return device_name

    def get_device_from_list(self) -> str:
        """
        Get device name from the selected item in the list widget.

        Returns:
            str: full name of the device (Explore_XXXX). Empty if no device is selected
        """
        try:
            device_name = self.ui.list_devices.selectedItems()[0].text()
            device_name = device_name[:12]
        except IndexError:
            device_name = ""

        return device_name

    def get_dev_name(self) -> str:
        """Get selected device name by looking at line edit and device list.

        Returns:
            str: Explore device name. Empty string if error happens
        """
        device_name = ""

        device_name_le = self.get_device_from_le()
        device_name_list = self.get_device_from_list()

        if device_name_le != "":
            device_name = device_name_le
        elif device_name_list != "":
            device_name = device_name_list
        return device_name

    #########################
    # Connect/disconnect methods
    #########################
    def connect(self):
        """Connect to a explore device"""
        # Get device name
        device_name = self.get_dev_name()
        if device_name == "":
            display_msg(Messages.INVALID_EXPLORE_NAME)
            return

        # Change footer and button
        self._connect_stylesheet(device_name=device_name)
        self.ui.btn_connect.setEnabled(False)

        worker = Worker(self.explorer.connect, device_name=device_name)
        worker.signals.error.connect(self.connection_error)

        worker.signals.finished.connect(lambda: self._connect_stylesheet(reset=True))
        worker.signals.finished.connect(self.on_connection_change)
        worker.signals.finished.connect(lambda: self.ui.btn_connect.setEnabled(True))

        self.threadpool.start(worker)

    def disconnect(self):
        """Disconnect from explore device"""
        try:
            self.explorer.disconnect()

        except Exception as error:
            display_msg(str(error))
            logger.debug("Got an exception while disconnecting from the device: %s of type: %s", error, type(error))

        self.on_connection_change()
    #########################
    # Slots
    #########################

    @Slot()
    def connect_clicked(self):
        """_summary_
        """
        if not self.explorer.is_connected:
            self.connect()

        else:
            self.disconnect()

    @Slot()
    def scan_clicked(self):
        """Scan for devices in a separate thread"""
        self.ui.list_devices.clear()

        # Change footer and scan button
        self._scan_stylesheet()
        self.ui.btn_scan.setEnabled(False)

        worker = Worker(self.explorer.scan_devices)
        worker.signals.result.connect(self.add_scanned_devices)
        worker.signals.error.connect(self.scan_error)

        worker.signals.finished.connect(lambda: self._scan_stylesheet(reset=True))
        worker.signals.finished.connect(lambda: self.ui.btn_scan.setEnabled(True))

        self.threadpool.start(worker)

    @Slot(list)
    def add_scanned_devices(self, explore_devices: list) -> None:
        """Add scanned devices into QlistWidget

        Args:
            explore_devices (list): list of NamedTuple containing device name and pairing status
        """
        if len(explore_devices) == 0:
            self.scan_error(Messages.NO_EXPLORE_DEVICES)
            logger.info("No explore devices found.")
            return

        # If platform is Windows display devices with Paired/Unpaired label and display warning
        if os.name == "nt":
            devs = [dev.name + "\t" + str(dev.is_paired) for dev in explore_devices]
            devs = [dev.replace("True", "Paired").replace("False", "Unpaired") for dev in devs]
            devs.sort(key=lambda x: x.endswith("Paired"))
            devs.sort()
            self.ui.lbl_wdws_warning.setText(Messages.WARNING_PAIRED_DEV_WINDOWS)
            self.ui.lbl_wdws_warning.setStyleSheet("font: 11pt; color: red;")
            self.ui.lbl_wdws_warning.show()
            self.ui.lbl_wdws_warning.repaint()
        else:
            devs = [dev.name for dev in explore_devices]

        self.ui.list_devices.addItems(devs)

    @Slot()
    def connection_error(self, err_tuple: tuple) -> None:
        """
        Catch error thrown by connect thread and reset footer and buttons.
        Display pop-up with the error.

        Args:
            err_tuple (tuple): tuple with error message and type
        """
        self._connect_stylesheet(reset=True)

        err_type = err_tuple[0]
        err_msg = err_tuple[1]

        if err_type == xpy_ex.DeviceNotFoundError:
            msg = err_msg
            logger.warning("Device not found.")

        elif err_type == TypeError or err_type == UnboundLocalError:
            msg = Messages.INVALID_EXPLORE_NAME
            logger.warning("Invalid Explore name")

        elif err_type == ValueError or err_type == SystemError:
            msg = Messages.NO_BT_CONNECTION
            logger.warning("No Bluetooth connection available.")

        else:
            msg = err_msg
            logger.debug("Got an exception while connecting to the device: %s of type: %s", err_msg, err_type)

        display_msg(str(msg))

    @Slot()
    def scan_error(self, err_tuple) -> None:
        """
        Catch error thrown by scan thread and reset footer and buttons.
        Display pop-up with the error.

        Args:
            err_tuple (tuple): tuple with error message and type
        """
        self._scan_stylesheet(reset=True)

        err_type = err_tuple[0]
        err_msg = err_tuple[1]

        if err_type == ValueError or err_type == SystemError:
            msg = Messages.NO_BT_CONNECTION
            logger.warning("No Bluetooth connection available.")
        else:
            msg = err_msg
            logger.debug("Got an exception while scanning for devices: %s of type: %s", err_msg, err_type)

        display_msg(msg)

    #########################
    # Visual feedback
    #########################
    def _connect_stylesheet(self, device_name: str = None, reset: bool = False) -> None:
        """Change footer and connect button to stylesheet
        Args:
            device_name (str, optional): Name of the device to connect. Defaults to None.
            reset (bool, optional): Whether to reset to default values. Defaults to False.
        """
        lbl_footer = "Not connected" if reset else f"Connecting to {device_name}..."
        btn_txt = "Connect" if reset else "Connecting"
        # btn_stylesheet = "" if reset else Stylesheets.DISABLED_BTN_STYLESHEET

        # Set footer
        self.signals.devInfoChanged.emit({EnvVariables.DEVICE_NAME: lbl_footer})

        # Set button
        self.signals.btnConnectChanged.emit(btn_txt)
        # TODO: decide which stylesheet to apply
        # self.ui.btn_connect.setStyleSheet(btn_stylesheet)

        # TODO: decide if we need to display the warning
        # If platform is windows, add instructions
        # if os.name == "nt":
        #     self.ui.lbl_bt_instructions.setText(Messages.WINDOWS_PAIR_INSTRUCTIONS)
        #     self.ui.lbl_bt_instructions.setHidden(reset)

    def _scan_stylesheet(self, reset: bool = False) -> None:
        """Change footer and scan button to stylesheet
        Args:
            resete (bool, optional): Whether to reset to default values. Defaults to False.
        """
        lbl_footer = "Not connected" if reset else "Scanning ..."
        btn_txt = "Scan" if reset else "Scanning"
        # btn_stylesheet = "" if reset else Stylesheets.DISABLED_BTN_STYLESHEET

        # Set footer
        self.signals.devInfoChanged.emit({EnvVariables.DEVICE_NAME: lbl_footer})

        # Set button
        self.ui.btn_scan.setText(btn_txt)
        # TODO: decide which stylesheet to apply
        # self.ui.btn_scan.setStyleSheet(btn_stylesheet)

    def on_connection_change(self):
        """_summary"""
        if self.explorer.is_connected:
            self.signals.btnConnectChanged.emit("Disconnect")
            self.signals.displayDefaultImp.emit()
            self.signals.connectionStatus.emit(ConnectionStatus.CONNECTED)

            dev_name = self.explorer.stream_processor.device_info["device_name"]
            device_lbl = f"Connected to {dev_name}"
            firmware = self.explorer.stream_processor.device_info["firmware_version"]
            data = {EnvVariables.DEVICE_NAME: device_lbl, EnvVariables.FIRMWARE: firmware}
            self.signals.devInfoChanged.emit(data)
        else:
            self.signals.btnConnectChanged.emit("Connect")
            self.signals.connectionStatus.emit(ConnectionStatus.DISCONNECTED)
            data = {EnvVariables.DEVICE_NAME: "Not Connected"}
            self.signals.devInfoChanged.emit(data)
