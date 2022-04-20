"""Settings module"""
import logging

import numpy as np
from exploredesktop.modules import Settings
from exploredesktop.modules.app_settings import (
    ConnectionStatus,
    Messages,
    Settings,
    Stylesheets
)
from exploredesktop.modules.base_model import BaseModel
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QMessageBox
)

from exploredesktop.modules.tools import display_msg, wait_cursor


logger = logging.getLogger("explorepy." + __name__)


class SettingsFrameView(BaseModel):
    """_summary_
    """
    def __init__(self, ui) -> None:
        super().__init__()
        self.ui = ui

        self.setup_dropdown()

    def setup_dropdown(self):
        """Initialize dropdown
        """
        self.ui.value_sampling_rate.addItems([str(int(sr)) for sr in Settings.SAMPLING_RATES])

    def setup_ui_connections(self):
        """Connect ui widgets to corresponding slot
        """
        for ch_wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
            ch_wdgt.stateChanged.connect(self.one_chan_selected)

        self.ui.value_sampling_rate.currentTextChanged.connect(self.display_sr_warning)

        self.ui.btn_reset_settings.clicked.connect(self.reset_settings)
        # TODO uncomment when implemented
        # self.ui.btn_format_memory.clicked.connect(self.config_funct.format_memory)
        # self.ui.btn_apply_settings.clicked.connect(self.config_funct.change_settings)
        # self.ui.btn_calibrate.setHidden(True)

    def setup_settings_frame(self, connection=ConnectionStatus.CONNECTED):
        """Setup the settings frame
        """
        if connection != ConnectionStatus.CONNECTED or not self.explorer.is_connected:
            return

        # Set device name
        self.ui.label_explore_name.setText(self.explorer.device_name)

        # Set active channels
        chan_dict = self.explorer.get_chan_dict()
        chan_list = Settings.CHAN_LIST[:self.explorer.get_device_chan()]

        for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
            w.setChecked(chan_dict[w.objectName().replace("cb_", "")])
            if w.objectName().replace("cb_", "") not in chan_list:
                w.hide()
            if w.isHidden() and w.objectName().replace("cb_", "") in chan_list:
                w.show()

        # Set sampling rate
        sr = int(self.explorer.sampling_rate)
        self.ui.value_sampling_rate.setCurrentText(str(sr))

    ###
    # Button slots
    ###
    @Slot()
    def reset_settings(self):
        """
        Display a popup asking for confirmation.
        If yes, the settinngs are set to default.
        """
        reset = False

        response = display_msg(msg_text=Messages.RESET_SETTINGS_QUESTION, popup_type="question")

        if response == QMessageBox.StandardButton.Yes:
            with wait_cursor():
                reset = self.explorer.reset_soft()
                disconnect = self.explorer.disconnect()
                # TODO revisit signals, connection changed vs connection status
                # self.signals.connectionChanged.emit(ConnectionStatus.DISCONNECTED)
                self.signals.connectionStatus.emit(ConnectionStatus.DISCONNECTED)
                self.signals.pageChange.emit("btn_bt")
                # TODO: move to bt page, and stop processes
                # TODO: change change_page funct to work with signals
        return reset

    ###
    # Vis feedback slots
    ###
    @Slot()
    def one_chan_selected(self):
        """
        Make sure at least one checkbox is selected.
        If only one checkbox is left it will be disabled so status cannot change. A tooltip will be added.
        """
        cbs = {ch_wdgt: ch_wdgt.isChecked() for ch_wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox)}
        if sum(cbs.values()) == 1:
            unchecked_cb = list(cbs.keys())[list(cbs.values()).index(True)]
            unchecked_cb.setEnabled(False)
            unchecked_cb.setToolTip(Messages.SELECT_1_CHAN)

        else:
            for ch_wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
                ch_wdgt.setEnabled(True)
                ch_wdgt.setToolTip("")

    @Slot()
    def display_sr_warning(self):
        """Display warning for 1000 Hz sampling rate
        """
        if int(self.ui.value_sampling_rate.currentText()) == 1000:
            self.ui.lbl_sr_warning.show()
        else:
            self.ui.lbl_sr_warning.hide()
