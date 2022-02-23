# from PySide6.QtCore import Signal
import logging
import os

import explorepy._exceptions as xpy_ex
import numpy as np
from exploregui.modules.app_functions import AppFunctions
from exploregui.modules.app_settings import Settings
from explorepy.stream_processor import TOPICS
from explorepy.tools import bt_scan
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox
)


logger = logging.getLogger("explorepy." + __name__)

DISABLED_STYLESHEET = """
    background-color: rgb(89,90,111);
    color: rgb(155,155,155);
"""


class BTFunctions(AppFunctions):
    """
    Functions for Bluetooth connection
    """

    def __init__(self, ui, explorer):
        super().__init__(ui, explorer)
        # self.ui = ui
        # self.explorer = explorer
        self._battery_percent_list = []

    #########################
    # Scan/Connect Functions
    #########################

    def scan_devices(self) -> None:
        """"
        Scans for available explore devices.
        """

        self.ui.list_devices.clear()

        # Change footer and scan button
        self._scan_stylesheet()

        try:
            with self.wait_cursor():
                explore_devices = bt_scan()

        except (ValueError, SystemError):
            msg = "No Bluetooth connection available.\nPlease make sure the bluetooth is on."
            self._connection_error_gui(msg, scan=True)
            logger.warning("No Bluetooth connection available.")
            return

        if len(explore_devices) == 0:
            msg = "No explore devices found. Please make sure your device is turned on."
            self._connection_error_gui(msg, scan=True)
            logger.info("No explore devices found.")
            return

        # If platform is Windows display devices with Paired/Unpaired label and display warning
        if os.name == "nt":
            devs = [dev.name + "\t" + str(dev.is_paired) for dev in explore_devices]
            devs = [dev.replace("True", "Paired").replace("False", "Unpaired") for dev in devs]
            devs.sort(key=lambda x: x.endswith("Paired"))
            self.ui.lbl_wdws_warning.setText("Note: Listed paired devices might not be advertising")
            self.ui.lbl_wdws_warning.setStyleSheet("font: 11pt; color: red;")
            self.ui.lbl_wdws_warning.show()
            self.ui.lbl_wdws_warning.repaint()
        else:
            devs = [dev.name for dev in explore_devices]

        self.ui.list_devices.addItems(devs)

        # Reset footer and button
        self._scan_stylesheet(reset=True)

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
        device_name_le = self.get_device_from_le()
        device_name_list = self.get_device_from_list()
        device_name = ""
        if device_name_le != "":
            device_name = device_name_le
        elif device_name_list != "":
            device_name = device_name_list
        return device_name

    def connect2device(self):
        """
        Connect to the explore device.
        """
        device_name = self.get_dev_name()
        if device_name == "":
            msg = "Please select a device or provide a valid name (Explore_XXXX or XXXX) before connecting."
            self.display_msg(msg)
            return

        # Change footer and button
        self._connect_stylesheet(device_name=device_name)

        try:
            with self.wait_cursor():
                self.explorer.connect(device_name=device_name)
                self.is_connected = True
                AppFunctions.is_connected = self.is_connected

        except xpy_ex.DeviceNotFoundError as error:
            msg = str(error)
            self._connection_error_gui(msg)
            logger.warning("Device not found.")
            return
        except (TypeError, UnboundLocalError):
            msg = "Please select a device or provide a valid name (Explore_XXXX or XXXX) before connecting."
            self._connection_error_gui(msg)
            logger.warning("Invalid Explore name")
            return
        except (ValueError, SystemError):
            msg = "No Bluetooth connection available.\nPlease make sure the bluetooth is on."
            self._connection_error_gui(msg)
            logger.warning("No Bluetooth connection available.")
            return
        except Exception as error:
            msg = str(error)
            self._connection_error_gui(msg)
            logger.debug(
                f"Got an exception while connecting to the device: {error} of type: {type(error)}")
            return

        self._connect_stylesheet(reset=True)
        self.on_connection_change()

    def disconnect(self) -> None:
        """
        Disconnect from Explore device
        """
        try:
            self.explorer.disconnect()
            self.is_connected = False
            AppFunctions.is_connected = self.is_connected

        except Exception as error:
            msg = str(error)
            self.display_msg(msg)
            logger.debug(
                f"Got an exception while disconnecting from the device: {error} of type: {type(error)}")

        self.on_connection_change()

    #########################
    # Visual feedback functions
    #########################
    def _scan_stylesheet(self, reset: bool = False) -> None:
        """Change footer and scan button to stylesheet
        Args:
            resete (bool, optional): Whether to reset to default values. Defaults to False.
        """
        lbl_footer = "Not connected" if reset else "Scanning ..."
        btn_txt = "Scan" if reset else "Scanning"
        btn_stylesheet = "" if reset else DISABLED_STYLESHEET

        # Set footer
        self.ui.ft_label_device_3.setText(lbl_footer)
        self.ui.ft_label_device_3.repaint()

        # Set button
        self.ui.btn_scan.setText(btn_txt)
        self.ui.btn_scan.setStyleSheet(btn_stylesheet)
        QApplication.processEvents()

    def _connect_stylesheet(self, device_name: str = None, reset: bool = False) -> None:
        """Change footer and connect button to stylesheet
        Args:
            device_name (str, optional): Name of the device to connect. Defaults to None.
            reset (bool, optional): Whether to reset to default values. Defaults to False.
        """
        lbl_footer = "Not connected" if reset else f"Connecting to {device_name}..."
        btn_txt = "Connect" if reset else "Connecting"
        btn_stylesheet = "" if reset else DISABLED_STYLESHEET

        # Set footer
        self.ui.ft_label_device_3.setText(lbl_footer)
        self.ui.ft_label_device_3.adjustSize()
        self.ui.ft_label_device_3.repaint()

        # Set button
        self.ui.btn_connect.setText(btn_txt)
        self.ui.btn_connect.setStyleSheet(btn_stylesheet)

        # If platform is windows, add instructions
        if os.name == "nt":
            self.ui.lbl_bt_instructions.setText("Follow Windows' instructions to pair your device.")
            self.ui.lbl_bt_instructions.setHidden(reset)
        QApplication.processEvents()

    def _connection_error_gui(self, msg: str, scan: bool = False) -> None:
        """
        Reset footer and buttons when scan/connect functions throw an error.
        Display pop-up with the error

        Args:
            msg (str): error message to display
            scan (bool, optional): whether is scanning or connecting. Defaults to False.
        """

        if scan is False:
            self._connect_stylesheet(reset=True)
        else:
            self._scan_stylesheet(reset=True)

        # display error message
        self.display_msg(msg)

    def on_connection_change(self) -> None:
        """
        Update GUI when device is (dis)connected
        """
        # set number of channels:
        self.set_n_chan()
        # self.n_chan = 8
        # self.chan_list = Settings.CHAN_LIST[:self.n_chan]

        # change footer & button text:
        self.change_footer()
        self.change_btn_connect_txt()

        # Update device info and sttings frame
        if self.is_connected:
            self.info_callback_subscribe()
            self.update_frame_dev_settings()

        # init plots and impedances
        # self.init_plots()
        self.init_imp()

        self.ui.line_2.setHidden(True)

    def change_btn_connect_txt(self) -> None:
        """
        Change connect buttonn text to Connect/Disconnect depending on explore status
        """
        if self.is_connected:
            self.ui.btn_connect.setText("Disconnect")

        else:
            self.ui.btn_connect.setText("Connect")

    def change_footer(self) -> None:
        """
        Change the fields for device and firmware in the GUI footer
        """
        if self.is_connected:
            self.ui.ft_label_firmware.setHidden(False)
            self.ui.ft_label_firmware_value.setHidden(False)
            self.ui.ft_label_battery.setHidden(False)
            self.ui.ft_label_battery_value.setHidden(False)
            self.ui.ft_label_temp.setHidden(False)
            self.ui.ft_label_temp_value.setHidden(False)

            dev_name = self.explorer.stream_processor.device_info["device_name"]
            device_lbl = f"Connected to {dev_name}"
            firmware = self.explorer.stream_processor.device_info["firmware_version"]
            self._update_device_name(new_value=device_lbl)
            self._update_firmware(new_value=firmware)
        else:
            device_lbl = "Not connected"
            self._update_device_name(new_value=device_lbl)

            self.ui.ft_label_firmware.setHidden(True)
            self.ui.ft_label_firmware_value.setHidden(True)
            self.ui.ft_label_battery.setHidden(True)
            self.ui.ft_label_battery_value.setHidden(True)
            self.ui.ft_label_temp.setHidden(True)
            self.ui.ft_label_temp_value.setHidden(True)

    def update_frame_dev_settings(self, reset_data=True) -> None:
        """
        Update the frame with the device settings.

        Args:
            reset_data (bool): whether to reset exg plot data. Defaults to True
        """

        stream_processor = self.explorer.stream_processor

        # Set device name
        self.ui.label_explore_name.setText(
            stream_processor.device_info["device_name"])

        # Set active channels
        chan = stream_processor.device_info['adc_mask']
        chan = [i for i in reversed(chan)]

        self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], chan))
        AppFunctions.chan_dict = self.chan_dict

        for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
            w.setChecked(self.chan_dict[w.objectName().replace("cb_", "")])
            if w.objectName().replace("cb_", "") not in self.chan_list:
                w.hide()
            if w.isHidden() and w.objectName().replace("cb_", "") in self.chan_list:
                w.show()

        if reset_data:
            self.reset_exg_plot_data()

        # Set sampling rate (value_sampling_rate)
        sr = stream_processor.device_info['sampling_rate']
        self.ui.value_sampling_rate.setCurrentText(str(int(sr)))

    def info_callback(self, packet) -> None:
        """Update device information.

        Args:
            packet (explorepy.packet.Environment): Environment/DeviceInfo packet
        """
        new_info = packet.get_data()
        for key in new_info.keys():
            if key == "temperature":
                new_value = str(new_info[key][0]) if self.is_connected else "NA"
                self._update_temperature(new_value=new_value)

            elif key == "battery":
                self._battery_percent_list.append(new_info[key][0])
                if len(self._battery_percent_list) > Settings.BATTERY_N_MOVING_AVERAGE:
                    del self._battery_percent_list[0]
                value = int(np.mean(self._battery_percent_list))
                value = 1 if value < 1 else value
                new_value = value if self.is_connected else "NA"
                stylesheet = self._battery_stylesheet(value=new_value)
                self._update_battery(new_value=str(new_value), new_stylesheet=stylesheet)

            elif key == "fimrware":
                new_value = new_info[key] if self.is_connected else "NA"
                self._update_firmware(new_value=new_value)

            elif key == "device_name":
                connected_lbl = f"Connected to {new_info[key]}"
                not_connected_lbl = "Not connected"
                new_value = connected_lbl if self.is_connected else not_connected_lbl
                self._update_device_name(new_value=new_value)

            elif key == "light":
                pass

            else:
                logger.warning("There is no field named: " + key)

        QApplication.processEvents()

    def info_callback_subscribe(self) -> None:
        """
        Subscribe info callback to stream processor
        """
        self.explorer.stream_processor.subscribe(callback=self.info_callback, topic=TOPICS.device_info)
        self.explorer.stream_processor.subscribe(callback=self.info_callback, topic=TOPICS.env)

    #########################
    # Updater Functions
    #########################

    def _battery_stylesheet(self, value):
        if isinstance(value, str):
            stylesheet = Settings.BATTERY_STYLESHEETS["na"]
        elif value > 60:
            stylesheet = Settings.BATTERY_STYLESHEETS["high"]
        elif value > 30:
            stylesheet = Settings.BATTERY_STYLESHEETS["medium"]
        elif value > 0:
            stylesheet = Settings.BATTERY_STYLESHEETS["low"]
        else:
            stylesheet = Settings.BATTERY_STYLESHEETS["na"]
        return stylesheet

    def _update_temperature(self, new_value):
        self.ui.ft_label_temp_value.setText(new_value)

    def _update_light(self, new_value):
        self.ui.ft_label_lux_value.setText(new_value)

    def _update_battery(self, new_value, new_stylesheet):
        self.ui.ft_label_battery_value.setText(new_value)
        self.ui.ft_label_battery_value.setStyleSheet(new_stylesheet)

    def _update_device_name(self, new_value):
        self.ui.ft_label_device_3.setText(new_value)

    def _update_firmware(self, new_value):
        self.ui.ft_label_firmware_value.setText(new_value)

    #########################
    # Reset Functions
    #########################

    def reset_bt_vars(self) -> None:
        """
        Reset class variables
        """
        self._battery_percent_list = []
