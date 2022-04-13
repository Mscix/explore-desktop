# -*- coding: utf-8 -*-
"""
Module containing impedance related functionalities
"""
import logging
from enum import Enum

import numpy as np
from explorepy.stream_processor import TOPICS
from PySide6.QtCore import (
    QTimer,
    Slot
)


from exploredesktop.modules.app_settings import (  # isort: skip
    ConnectionStatus,
    EnvVariables,
    Settings,
    Stylesheets
)
from exploredesktop.modules.base_model import BaseModel  # isort: skip


logger = logging.getLogger("explorepy." + __name__)


class FooterData(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    def __init__(self) -> None:
        self._battery_percent_list = []

    def reset_vars(self, connection) -> None:
        """reset class variables
        """
        if connection == ConnectionStatus.DISCONNECTED:
            self._battery_percent_list = []

    def env_callback(self, packet) -> None:
        """Update device information.

        Args:
            packet (explorepy.packet.Environment): Environment/DeviceInfo packet
        """
        if not self.explorer.is_connected:
            return
        new_info = packet.get_data()
        for key in new_info.keys():
            if key == EnvVariables.TEMPERATURE.value:
                temperature = str(new_info[key][0]) + " ºC" if self.explorer.is_connected else "NA"

            elif key == EnvVariables.BATTERY.value:
                self._battery_percent_list.append(new_info[key][0])
                if len(self._battery_percent_list) > Settings.BATTERY_N_MOVING_AVERAGE:
                    del self._battery_percent_list[0]
                value = int(np.mean(self._battery_percent_list))
                value = 1 if value < 1 else value
                battery_val = value if self.explorer.is_connected else "NA"
                battery_stylesheet = self._battery_stylesheet(value=battery_val)

            elif key == EnvVariables.LIGHT.value:
                pass

            else:
                logger.warning("There is no field named: %s", key)

        data = {
            EnvVariables.BATTERY: [str(battery_val), battery_stylesheet],
            EnvVariables.TEMPERATURE: temperature,
        }
        self.signals.envInfoChanged.emit(data)

    def subscribe_env_callback(self, connection) -> None:
        """subscribe env callback to stream processor
        """
        if connection == ConnectionStatus.CONNECTED:
            self.explorer.subscribe(callback=self.env_callback, topic=TOPICS.env)

    def check_connection_status(self) -> None:
        """Check connection status
        """
        if not self.explorer.is_connected:
            return
        sp_connected = self.explorer.stream_processor.is_connected
        reconnecting = self.explorer.stream_processor.parser._is_reconnecting
        if sp_connected and reconnecting:
            self.signals.connectionStatus.emit(ConnectionStatus.RECONNECTING)
        elif sp_connected and reconnecting is False:
            self.signals.connectionStatus.emit(ConnectionStatus.CONNECTED)
        elif sp_connected is False and reconnecting is False:
            self.signals.connectionStatus.emit(ConnectionStatus.DISCONNECTED)
        else:
            logger.warning("Connection status unknown. stream_processor.is_connected=%s", sp_connected)

    def timer_connection(self) -> None:
        """Timer for checking connection status
        """
        self.timer_con = QTimer()
        self.timer_con.setInterval(2000)
        self.timer_con.timeout.connect(self.check_connection_status)
        self.timer_con.start()

    @staticmethod
    def _battery_stylesheet(value) -> None:
        if isinstance(value, str):
            stylesheet = Stylesheets.BATTERY_STYLESHEETS["na"]
        elif value <= 10:
            stylesheet = Stylesheets.BATTERY_STYLESHEETS["low"]
        else:
            stylesheet = Stylesheets.BATTERY_STYLESHEETS["na"]
        return stylesheet


class FooterFrameView():
    """Footer frame functions
    """
    def __init__(self, ui, model) -> None:
        self.ui = ui
        self.model = model
        self.signals = model.get_signals()
        self.explorer = model.get_explorer()

    def get_model(self):
        """Retrun impedance model

        Returns:
            ImpModel: impedance data model
        """
        return self.model

    @Slot(Enum)
    def print_connection_status(self, status: Enum) -> None:
        """Print the connection status in the Footer

        Args:
            status (str): Connection status. Can be "Reconnecting", "Connected", "Disconnected"
        """
        reconnecting_label = ConnectionStatus.RECONNECTING.value
        not_connected_label = ConnectionStatus.DISCONNECTED.value
        dev_name = self.model.explorer.device_name if self.model.explorer.is_connected else ""
        connected_label = ConnectionStatus.CONNECTED.value.replace("dev_name", dev_name)
        label_text = self.ui.ft_label_device_3.text()

        if status == ConnectionStatus.RECONNECTING and label_text != reconnecting_label:
            self.signals.devInfoChanged.emit({EnvVariables.DEVICE_NAME: reconnecting_label})

        elif status == ConnectionStatus.CONNECTED and label_text != connected_label:
            self.signals.devInfoChanged.emit({EnvVariables.DEVICE_NAME: connected_label})

        elif status == ConnectionStatus.DISCONNECTED and label_text != not_connected_label:
            self.explorer.is_connected = False
            self.signals.devInfoChanged.emit({EnvVariables.DEVICE_NAME: not_connected_label})
            self.signals.btnConnectChanged.emit("Connect")
            # TODO: implement functions bellow when all the modules are together
            # self.stop_processes()
            # self.reset_vars()
            # self.bt_funct.on_connection_change()
            # self.change_page(btn_name="btn_bt")
            # self.highlight_left_button("btn_bt")

    @Slot(dict)
    def update_env_info(self, data: dict) -> None:
        """Update footer with environmental data

        Args:
            data (dict): dictionary of data, must contain keys "battery" and "temperature"
        """
        if EnvVariables.BATTERY not in data:
            logger.debug("battery key not found in env data dictionary")
            return
        if EnvVariables.TEMPERATURE not in data:
            logger.debug("battery key not found in env data dictionary")
            return

        battery, stylesheet_battery = data[EnvVariables.BATTERY]
        temperature = data[EnvVariables.TEMPERATURE]

        battery = battery + "%" if battery != "NA" else battery
        self._update_battery(new_value=battery, new_stylesheet=stylesheet_battery)
        self._update_temperature(new_value=temperature)

    @Slot(dict)
    def update_dev_info(self, data: dict) -> None:
        """Update footer with device information

        Args:
            data (dict): dictionary of data, must contain keys "device_name" or "firmware"
        """
        hide = False if self.explorer.is_connected else True
        self.ui.ft_label_firmware.setHidden(hide)
        self.ui.ft_label_firmware_value.setHidden(hide)
        self.ui.ft_label_battery.setHidden(hide)
        self.ui.ft_label_battery_value.setHidden(hide)
        self.ui.ft_label_temp.setHidden(hide)
        self.ui.ft_label_temp_value.setHidden(hide)

        if len(data) == 0:
            return

        if EnvVariables.DEVICE_NAME in data:
            self._update_device_name(data[EnvVariables.DEVICE_NAME])
        if EnvVariables.FIRMWARE in data:
            self._update_firmware(data[EnvVariables.FIRMWARE])

    def _update_battery(self, new_value, new_stylesheet) -> None:
        self.ui.ft_label_battery_value.setText(new_value)
        self.ui.ft_label_battery_value.setStyleSheet(new_stylesheet)

    def _update_temperature(self, new_value) -> None:
        self.ui.ft_label_temp_value.setText(new_value)

    def _update_device_name(self, new_value) -> None:
        self.ui.ft_label_device_3.setText(new_value)
        self.ui.ft_label_device_3.adjustSize()
        self.ui.ft_label_device_3.repaint()

    def _update_firmware(self, new_value) -> None:
        self.ui.ft_label_firmware_value.setText(new_value)
