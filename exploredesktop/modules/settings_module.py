"""Settings module"""
"""+ one_chan_selected()
+ format_memory_clicked()
+ calibrate_orn_clicked()
+ reset_settings_clicked(): bool
+ display_sr_warning()
+ sampling_rate_changed(): bool
+ active_channels_changed(): bool
+ apply_settings_clicked()
+ enable_settings()"""

from exploredesktop.modules.app_settings import ConnectionStatus, Messages, Settings
from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Slot


class SettingsFrameView():
    """_summary_
    """
    def __init__(self, ui, model, threadpool) -> None:
        self.ui = ui
        self.model = model
        self.threadpool = threadpool

        self.signals = model.get_signals()
        self.explorer = model.get_explorer()

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
