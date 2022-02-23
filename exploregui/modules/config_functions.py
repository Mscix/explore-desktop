import logging
import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QMessageBox
)

from exploregui.modules import (
    AppFunctions,
    Settings
)
from exploregui.modules.bt_functions import DISABLED_STYLESHEET


logger = logging.getLogger("explorepy." + __name__)


class ConfigFunctions(AppFunctions):
    """[summary]

    Args:
        AppFunctions ([type]): [description]
    """
    def __init__(self, ui, explorer, vis_functions):
        super().__init__(ui, explorer)
        self.vis_functions = vis_functions

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
            unchecked_cb.setToolTip("At least one channel must be active")

        else:
            for ch_wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
                ch_wdgt.setEnabled(True)
                ch_wdgt.setToolTip("")

    @Slot()
    def format_memory(self):
        r"""
        Display a popup asking for confirmation.
        If yes, memory is formatted.
        """

        question = "Are you sure you want to format the memory?"
        response = self.display_msg(msg_text=question, type="question")

        if response == QMessageBox.StandardButton.Yes:
            with self.wait_cursor():
                self.explorer.format_memory()
            self.display_msg(msg_text="Memory formatted", type="info")
        else:
            return

    @Slot()
    def calibrate_orn(self):
        r"""
        Calibrate the orientation
        """
        lbl = self.ui.ft_label_device_3.text()
        question = ("Do you want to continue with the orientation sensors calibration?\n"
                    "This will overwrite the calibration data if it already exists\n\n"
                    "If yes, you would need to move and rotate the device for 100 seconds\n"
                    )
        response = self.display_msg(msg_text=question, type="question")

        if response == QMessageBox.StandardButton.Yes:
            # QMessageBox.information(self, "", "Calibrating...\nPlease move and rotate the device")
            self.ui.ft_label_device_3.setText("Calibrating ORN ... ")
            self.ui.ft_label_device_3.repaint()
            with self.wait_cursor():
                self.explorer.calibrate_orn(do_overwrite=True)
            self.ui.ft_label_device_3.setText(lbl)
            self.ui.ft_label_device_3.repaint()
            self.display_msg(msg_text="Calibration Complete", title="Done", type="info")
        else:
            return

    @Slot()
    def reset_settings(self):
        """
        Display a popup asking for confirmation.
        If yes, the settinngs are set to default.
        """
        reset = False
        question = (
            "Are you sure you want to reset your settings?\n"
            "The Explore device will disconnect after the soft reset."
        )
        response = self.display_msg(msg_text=question, type="question")

        if response == QMessageBox.StandardButton.Yes:
            with self.wait_cursor():
                self.explorer.reset_soft()
            reset = True
        return reset

    def display_sr_warning(self):
        """Display warning for 1000 Hz sampling rate
        """
        if int(self.ui.value_sampling_rate.currentText()) == 1000:
            self.ui.lbl_sr_warning.show()
        else:
            self.ui.lbl_sr_warning.hide()

    def change_sampling_rate(self):
        """Change the sampling rate

        Returns:
            bool: whether sampling rate has changed
        """

        sr = self.explorer.stream_processor.device_info['sampling_rate']
        str_value = self.ui.value_sampling_rate.currentText()
        value = int(str_value)
        changed = False

        if int(sr) != value:
            if self.plotting_filters is not None:
                self.check_filters_new_sr()

            logger.info("Old Sampling rate: %s", self.explorer.stream_processor.device_info['sampling_rate'])
            self.explorer.set_sampling_rate(sampling_rate=value)
            logger.info("New Sampling rate: %s", self.explorer.stream_processor.device_info['sampling_rate'])
            changed = True

        return changed

    def change_active_channels(self):
        """
        Read selected checkboxes and set the channel mask of the device

        Returns:
            bool: whether sampling rate has changed
        """

        active_chan = []
        changed = False

        for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
            status = str(1) if w.isChecked() else str(0)
            active_chan.append(status)

        active_chan = list(reversed(active_chan))
        active_chan_int = [int(i) for i in active_chan]
        n_active = sum(active_chan_int)
        print(f"{active_chan=}")
        print(f"{active_chan_int=}")
        if n_active == 0:
            self.display_msg("Please select at least one channel")
            return

        if active_chan_int != self.explorer.stream_processor.device_info['adc_mask']:
            if AppFunctions.plotting_filters is not None:
                self.vis_functions._baseline_corrector["baseline"] = None
                self.explorer.stream_processor.remove_filters()

            mask = "".join(active_chan)
            int_mask = int(mask, 2)
            print(f"{mask=}")
            print(f"{int_mask=}")
            try:
                self.explorer.set_channels(int_mask)
            except TypeError:
                self.explorer.set_channels(mask)

            n_chan = self.explorer.stream_processor.device_info['adc_mask']
            n_chan = list(reversed(n_chan))

            self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
            AppFunctions.chan_dict = self.chan_dict

            self.vis_functions.offsets = np.arange(1, n_chan.count(1) + 1)[:, np.newaxis].astype(float)
            self.vis_functions._baseline_corrector["baseline"] = None
            if self.plotting_filters is not None:
                self.apply_filters()
            self.init_imp()
            changed = True

        return changed

    @Slot()
    def change_settings(self):
        """
        Apply changes in device settings
        """

        stream_processor = self.explorer.stream_processor

        with self.wait_cursor():
            changed_chan = self.change_active_channels()
            changed_sr = self.change_sampling_rate()
            self.reset_exg_plot_data()

        if changed_sr or changed_chan:
            act_chan = ", ".join([ch for ch in self.chan_dict if self.chan_dict[ch] == 1])
            msg = (
                "Device settings have been changed:"
                f"\nSampling Rate: {int(stream_processor.device_info['sampling_rate'])}"
                f"\nActive Channels: {act_chan}"
            )
            self.display_msg(msg_text=msg, type="info")

        self.vis_functions.init_plots()

    def check_filters_new_sr(self):

        if self.plotting_filters is None:
            return

        reapply = False
        # r_value = self.plotting_filters["highpass"]
        # l_value = self.plotting_filters["lowpass"]

        r_value = "" if self.plotting_filters["highpass"] in [None, 'None'] else self.plotting_filters["highpass"]
        l_value = "" if self.plotting_filters["lowpass"] in [None, 'None'] else self.plotting_filters["lowpass"]

        str_value = self.ui.value_sampling_rate.currentText()
        sr = int(str_value)

        nyq_freq = sr / 2.

        max_hc_freq = round(nyq_freq - 1, 2)
        min_lc_freq = round(0.003 * nyq_freq, 2)

        warning = ""

        hc_freq_warning = (
            "High cutoff frequency cannot be larger than or equal to the nyquist frequency.\n"
            f"The high cutoff frequency has changed to {max_hc_freq:.2f} Hz!"
        )

        lc_freq_warning = (
            "Transient band for low cutoff frequency was too narrow.\n"
            f"The low cutoff frequency has changed {min_lc_freq:.2f} Hz!"
        )

        if (l_value != "") and (float(l_value) / nyq_freq <= 0.003):
            warning += lc_freq_warning
            self.plotting_filters["lowpass"] = min_lc_freq
            reapply = True

        if (r_value != "") and (float(r_value) >= nyq_freq):
            warning += hc_freq_warning
            self.plotting_filters["highpass"] = max_hc_freq
            reapply = True

        if reapply:
            logger.info("Updating filters for new sampling rate")
            self.explorer.stream_processor.remove_filters()
            self.apply_filters()
            AppFunctions.plotting_filters = self.plotting_filters

        if warning != "":
            self.display_msg(msg_text=warning, type="info")

    def enable_settings(self, enable=True):
        """Disable or enable device settings widgets

        Args:
            enable (bool, optional): True will enable, False will disable. Defaults to True.
        """
        if enable is False:
            for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
                w.setEnabled(False)

            self.ui.value_sampling_rate.setEnabled(False)
            self.ui.value_sampling_rate.setStyleSheet("color: gray;\nborder-color: gray;")

            self.ui.btn_apply_settings.setEnabled(False)
            self.ui.btn_apply_settings.setStyleSheet(DISABLED_STYLESHEET)
            self.ui.btn_apply_settings.setToolTip(
                "Changing the settings during recording and LSL streaming is not possible")

            self.ui.btn_reset_settings.setEnabled(False)
            self.ui.btn_reset_settings.setStyleSheet(DISABLED_STYLESHEET)
            self.ui.btn_reset_settings.setToolTip(
                "Resetting the settings during recording and LSL streaming is not possible")

            self.ui.btn_format_memory.setEnabled(False)
            self.ui.btn_format_memory.setStyleSheet(DISABLED_STYLESHEET)
            self.ui.btn_format_memory.setToolTip(
                "Formatting the memory during recording and LSL streaming is not possible")
        else:
            for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
                w.setEnabled(True)

            self.ui.value_sampling_rate.setEnabled(True)
            self.ui.value_sampling_rate.setStyleSheet("")

            self.ui.btn_apply_settings.setEnabled(True)
            self.ui.btn_apply_settings.setStyleSheet("")
            self.ui.btn_apply_settings.setToolTip("")

            self.ui.btn_reset_settings.setEnabled(True)
            self.ui.btn_reset_settings.setStyleSheet("")
            self.ui.btn_reset_settings.setToolTip("")

            self.ui.btn_format_memory.setEnabled(True)
            self.ui.btn_format_memory.setStyleSheet("")
            self.ui.btn_format_memory.setToolTip("")
