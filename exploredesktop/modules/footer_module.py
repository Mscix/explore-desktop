# -*- coding: utf-8 -*-
"""
Module containing impedance related functionalities
"""
import logging
from enum import Enum
from typing import Union

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
    """Model for footer data
    """

    def __init__(self) -> None:
        super().__init__()
        self._battery_percent_list = []
        self.connection_status = ConnectionStatus.DISCONNECTED

    def reset_vars(self) -> None:
        """Reset class variables
        """
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

        try:
            self.signals.envInfoChanged.emit(data)
        # RuntimeError might happen when the app closes
        except RuntimeError as error:
            logger.debug("RuntimeError: %s", str(error))

    def subscribe_env_callback(self) -> None:
        """subscribe env callback to stream processor
        """
        self.explorer.subscribe(callback=self.env_callback, topic=TOPICS.env)

    def check_connection_status(self) -> None:
        """Check connection status
        """

        if not self.explorer.is_connected:
            return
        sp_connected = self.explorer.stream_processor.is_connected
        # pylint: disable=protected-access
        reconnecting = self.explorer.stream_processor.parser._is_reconnecting

        if (sp_connected and reconnecting) and self.connection_status != ConnectionStatus.RECONNECTING:
            self.connection_status = ConnectionStatus.RECONNECTING
            self.signals.connectionStatus.emit(ConnectionStatus.RECONNECTING)

        elif (sp_connected and reconnecting is False) and self.connection_status != ConnectionStatus.CONNECTED:
            self.connection_status = ConnectionStatus.CONNECTED
            self.signals.connectionStatus.emit(ConnectionStatus.CONNECTED)

        elif (sp_connected is False and reconnecting is False) and \
                self.connection_status != ConnectionStatus.DISCONNECTED:
            self.connection_status = ConnectionStatus.DISCONNECTED
            self.signals.connectionStatus.emit(ConnectionStatus.DISCONNECTED)

    def timer_connection(self) -> None:
        """Timer for checking connection status
        """
        self.timer_con = QTimer()
        self.timer_con.setInterval(2000)
        self.timer_con.timeout.connect(self.check_connection_status)
        self.timer_con.start()

    @staticmethod
    def _battery_stylesheet(value: Union[str, int]) -> str:
        """Obtain battery stylesheet

        Args:
            value (Union[str, int]): battery value

        Returns:
            str: stylesheet
        """
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

    def __init__(self, ui) -> None:
        self.ui = ui
        self.model = FooterData()
        self.signals = self.model.get_signals()
        self.explorer = self.model.get_explorer()

        self.model.timer_connection()

    def get_model(self) -> None:
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

    @Slot(dict)
    def update_env_info(self, data: dict) -> None:
        """Update footer with environmental data

        Args:
            data (dict): dictionary of data, must contain keys "battery" and "temperature"
        """
        data_ok = self._verify_env_data(data)
        if not data_ok:
            return

        self.update_battery_info(data)
        self.update_temperature_info(data)

    def _verify_env_data(self, data: dict) -> bool:
        """Verify that environmental data dictionary contains all required fields

        Args:
            data (dict): dictionary with explore environmental data

        Returns:
            bool: whether data dictionary is correct
        """
        data_ok = True
        if EnvVariables.BATTERY not in data:
            logger.debug("battery key not found in env data dictionary")
            data_ok = False
        if EnvVariables.TEMPERATURE not in data:
            logger.debug("temperature key not found in env data dictionary")
            data_ok = False
        return data_ok

    def update_temperature_info(self, data: dict) -> None:
        """Get temperature and update UI field

        Args:
            data (dict): dictionary with explore environmental data
        """
        temperature = data[EnvVariables.TEMPERATURE]
        self._update_temperature(new_value=temperature)

    def update_battery_info(self, data: dict) -> None:
        """Get battery and update UI field

        Args:
            data (dict): dictionary with explore environmental data
        """
        battery, stylesheet_battery = data[EnvVariables.BATTERY]
        battery = battery + "%" if battery != "NA" else battery
        self._update_battery(new_value=battery, new_stylesheet=stylesheet_battery)

    @Slot(dict)
    def update_dev_info(self, data: dict) -> None:
        """Update footer with device information

        Args:
            data (dict): dictionary of data, must contain keys "device_name" or "firmware"
        """
        self.hide_footer_fields()

        if len(data) == 0:
            return

        if EnvVariables.DEVICE_NAME in data:
            self._update_device_name(data[EnvVariables.DEVICE_NAME])
        if EnvVariables.FIRMWARE in data:
            self._update_firmware(data[EnvVariables.FIRMWARE])

    def hide_footer_fields(self) -> None:
        """Hide footer fields if device is not connected
        """
        hide = False if self.explorer.is_connected else True
        self.ui.ft_label_firmware.setHidden(hide)
        self.ui.ft_label_firmware_value.setHidden(hide)
        self.ui.ft_label_battery.setHidden(hide)
        self.ui.ft_label_battery_value.setHidden(hide)
        self.ui.ft_label_temp.setHidden(hide)
        self.ui.ft_label_temp_value.setHidden(hide)

    def _update_battery(self, new_value: str, new_stylesheet: str) -> None:
        """Update battery UI field

        Args:
            new_value (str): new battery value
            new_stylesheet (str): stylesheet to apply
        """
        self.ui.ft_label_battery_value.setText(new_value)
        self.ui.ft_label_battery_value.setStyleSheet(new_stylesheet)

    def _update_temperature(self, new_value: str) -> None:
        """Update temperature UI field

        Args:
            new_value (str): new temperature value
        """
        self.ui.ft_label_temp_value.setText(new_value)

    def _update_device_name(self, new_value: str) -> None:
        """Update device name UI field

        Args:
            new_value (str): new device name value
        """
        self.ui.ft_label_device_3.setText(new_value)
        self.ui.ft_label_device_3.adjustSize()
        self.ui.ft_label_device_3.repaint()

    def _update_firmware(self, new_value: str) -> None:
        """Update firmware UI field

        Args:
            new_value (str): new firmware value
        """
        self.ui.ft_label_firmware_value.setText(new_value)
