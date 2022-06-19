"""Settings module"""
import logging

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QMessageBox
)


from exploredesktop.modules import (  # isort: skip
    Messages,
    Settings,
    BaseModel
)
from exploredesktop.modules.app_settings import ConnectionStatus, DataAttributes  # isort: skip
from exploredesktop.modules.utils import display_msg, wait_cursor  # isort: skip


logger = logging.getLogger("explorepy." + __name__)


class SettingsFrameView(BaseModel):
    """_summary_
    """
    def __init__(self, ui, filters) -> None:
        super().__init__()
        self.ui = ui
        self.filters = filters
        self.setup_dropdown()

    def setup_dropdown(self) -> None:
        """Initialize dropdown
        """
        self.ui.value_sampling_rate.addItems([str(int(sr)) for sr in Settings.SAMPLING_RATES])

    def setup_ui_connections(self) -> None:
        """Connect ui widgets to corresponding slot
        """
        for ch_wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
            ch_wdgt.stateChanged.connect(self.one_chan_selected)

        self.ui.value_sampling_rate.currentTextChanged.connect(self.display_sr_warning)

        self.ui.btn_reset_settings.clicked.connect(self.reset_settings)
        self.ui.btn_format_memory.clicked.connect(self.format_memory)
        self.ui.btn_apply_settings.clicked.connect(self.change_settings)
        # TODO uncomment when implemented
        # self.ui.btn_calibrate.setHidden(True)

    def setup_settings_frame(self) -> None:
        """Setup the settings frame
        """
        # Set device name
        self.ui.label_explore_name.setText(self.explorer.device_name)

        # Set active channels
        self._setup_active_channels()

        # Set sampling rate
        s_rate = int(self.explorer.sampling_rate)
        self.ui.value_sampling_rate.setCurrentText(str(s_rate))

    def _setup_active_channels(self) -> None:
        """Setup checkboxes to reflect channel status (active vs unactive)"""
        chan_dict = self.explorer.get_chan_dict()
        chan_list = Settings.CHAN_LIST[:self.explorer.get_device_chan()]

        for wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
            wdgt.setChecked(chan_dict[wdgt.objectName().replace("cb_", "")])
            if wdgt.objectName().replace("cb_", "") not in chan_list:
                wdgt.hide()
            if wdgt.isHidden() and wdgt.objectName().replace("cb_", "") in chan_list:
                wdgt.show()

    ###
    # Button slots
    ###
    @Slot()
    def reset_settings(self) -> None:
        """
        Display a popup asking for confirmation.
        If yes, the settinngs are set to default.
        """
        reset = False

        response = display_msg(msg_text=Messages.RESET_SETTINGS_QUESTION, popup_type="question")

        if response == QMessageBox.StandardButton.No:
            return reset

        with wait_cursor():
            reset = self.explorer.reset_soft()
            disconnect = self.explorer.disconnect()
            self.signals.connectionStatus.emit(ConnectionStatus.DISCONNECTED)
            self.signals.pageChange.emit("btn_bt")

        if reset:
            self.explorer.disconnect()
            self.signals.connectionStatus.emit(ConnectionStatus.DISCONNECTED)

        else:
            msg = (
                "There was an error while resetting the settings."
                "\nPlease make sure the bluetooth connection is stable and try again."
            )
            display_msg(msg)

    @Slot()
    def format_memory(self) -> None:
        """
        Display a popup asking for confirmation.
        If yes, memory is formatted.
        """

        response = display_msg(msg_text=Messages.FORMAT_MEM_QUESTION, popup_type="question")

        if response != QMessageBox.StandardButton.Yes:
            return

        with wait_cursor():
            result = self.explorer.format_memory()

        if result:
            display_msg(msg_text="Memory formatted", popup_type="info")
        else:
            msg = (
                "There was an error while formatting the memory."
                "\nPlease make sure the bluetooth connection is stable and try again."
            )
            display_msg(msg)

    @Slot()
    def change_settings(self) -> None:
        """
        Apply changes in device settings
        """
        with wait_cursor():
            self._remove_filters()

            changed_chan = self.change_active_channels()
            changed_sr = self.change_sampling_rate()

            # Reset exg data and reapply filters
            self.signals.updateDataAttributes.emit([DataAttributes.DATA])
            if self.filters.current_filters is not None:
                self.filters.apply_filters()

        if changed_sr or changed_chan:
            self._display_new_settings()

        self.signals.restartPlot.emit()

    def _display_new_settings(self) -> None:
        """Display popup with new sampling rate and active channels
        """
        chan_dict = self.explorer.get_chan_dict()
        act_chan = ", ".join([item[0] for item in chan_dict.items() if item[1]])
        msg = (
            "Device settings have been changed:"
            f"\nSampling Rate: {self.explorer.sampling_rate}"
            f"\nActive Channels: {act_chan}"
        )
        display_msg(msg_text=msg, popup_type="info")

    def _remove_filters(self) -> None:
        """Remove filters"""
        if self.filters.current_filters is not None:
            self.signals.updateDataAttributes.emit([DataAttributes.BASELINE])
            self.explorer.stream_processor.remove_filters()

    ###
    # Change settings functions
    ###
    def change_active_channels(self) -> bool:
        """
        Read selected checkboxes and set the channel mask of the device

        Returns:
            bool: whether sampling rate has changed
        """

        changed = False

        active_chan = self.get_active_chan_ui()
        active_chan_int = [int(i) for i in active_chan]

        # verify at least one channel is selected
        n_active = sum(active_chan_int)
        if n_active == 0:
            display_msg(Messages.SELECT_1_CHAN)
            return

        if active_chan_int != self.explorer.stream_processor.device_info['adc_mask']:
            mask = "".join(active_chan)
            changed = self.explorer.set_channels(mask)

            # n_chan = self.explorer.stream_processor.device_info['adc_mask']
            # n_chan = list(reversed(n_chan))

            self.explorer.set_chan_dict()
            self.update_modules()

        return changed

    def update_modules(self) -> None:
        """Update modules dependent on number of active channels"""
        self.signals.updateDataAttributes.emit([DataAttributes.OFFSETS, DataAttributes.BASELINE])
        self.signals.displayDefaultImp.emit()

    def get_active_chan_ui(self) -> list:
        """Get active channels from UI checkboxes

        Returns:
            list[int]: binary list indicating whether channel is active
        """

        active_chan = []
        for wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
            status = str(1) if wdgt.isChecked() else str(0)
            active_chan.append(status)

        active_chan = list(reversed(active_chan))
        return active_chan

    def change_sampling_rate(self) -> bool:
        """Change the sampling rate

        Returns:
            bool: whether sampling rate has changed
        """

        current_sr = int(self.explorer.sampling_rate)
        new_sr = int(self.ui.value_sampling_rate.currentText())
        changed = False

        if int(current_sr) != new_sr:
            if self.filters.current_filters is not None:
                self.filters.check_filters_sr(new_sr)

            logger.info("Old Sampling rate: %s", self.explorer.sampling_rate)
            changed = self.explorer.set_sampling_rate(sampling_rate=new_sr)
            logger.info("New Sampling rate: %s", self.explorer.sampling_rate)

        return changed

    ###
    # Vis feedback slots
    ###
    @Slot()
    def one_chan_selected(self) -> None:
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
    def display_sr_warning(self) -> None:
        """Display warning for 1000 Hz sampling rate
        """
        if int(self.ui.value_sampling_rate.currentText()) == 1000:
            self.ui.lbl_sr_warning.show()
        else:
            self.ui.lbl_sr_warning.hide()

    def enable_settings(self, enable=True) -> None:
        """Disable or enable device settings widgets

        Args:
            enable (bool, optional): True will enable, False will disable. Defaults to True.
        """

        enabled = True
        s_rate_stylesheet = ""
        # TODO decide which stylesheet to use
        # stylesheet = ""
        tooltip_apply_settings = ""
        tooltip_reset_settings = ""
        tooltip_format_mem = ""

        if enable is False:
            enabled = False
            s_rate_stylesheet = "color: gray;\nborder-color: gray;"
            # stylesheet = Stylesheets.DISABLED_BTN_STYLESHEET
            tooltip_apply_settings = Messages.DISABLED_SETTINGS
            tooltip_reset_settings = Messages.DISABLED_RESET
            tooltip_format_mem = Messages.DISABLED_FORMAT_MEM

        for wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
            wdgt.setEnabled(enabled)

        self.ui.value_sampling_rate.setEnabled(enabled)
        self.ui.value_sampling_rate.setStyleSheet(s_rate_stylesheet)

        self.ui.btn_apply_settings.setEnabled(enabled)
        # self.ui.btn_apply_settings.setStyleSheet(stylesheet)
        self.ui.btn_apply_settings.setToolTip(tooltip_apply_settings)

        self.ui.btn_reset_settings.setEnabled(enabled)
        # self.ui.btn_reset_settings.setStyleSheet(stylesheet)
        self.ui.btn_reset_settings.setToolTip(tooltip_reset_settings)

        self.ui.btn_format_memory.setEnabled(enabled)
        # self.ui.btn_format_memory.setStyleSheet(stylesheet)
        self.ui.btn_format_memory.setToolTip(tooltip_format_mem)

        self.ui.label_warning_disabled.setHidden(enabled)
