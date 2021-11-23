from PySide6.QtCore import Slot
from PySide6.QtWidgets import QCheckBox, QMessageBox
from modules.app_functions import AppFunctions
from modules.app_settings import Settings
import numpy as np


class ConfigFunctions(AppFunctions):
    def __init__(self, ui, explorer):
        super().__init__(ui, explorer)

    @Slot()
    def format_memory(self):
        r"""
        Display a popup asking for confirmation.
        If yes, memory is formatted.
        """

        question = "Are you sure you want to format the memory?"
        response = self.display_msg(msg_text=question, type="question")

        if response == QMessageBox.StandardButton.Yes:
            print("yes")
            self.explorer.format_memory()
            self.display_msg(msg_text="Memory formatted", type="info")
        else:
            print("no")
            return

    @Slot()
    def calibrate_orn(self):
        r"""
        Calibrate the orientation
        """
        question = ("Do you want to continue with the orientation sensors calibration?\n"
                    "This will overwrite the calibration data if it already exists\n\n"
                    "If yes, you would need to move and rotate the device for 100 seconds\n"
                    )
        # response = QMessageBox.question(self, "Confirmation", question)
        response = self.display_msg(msg_text=question, type="question")

        if response == QMessageBox.StandardButton.Yes:
            # QMessageBox.information(self, "", "Calibrating...\nPlease move and rotate the device")
            self.explorer.calibrate_orn(do_overwrite=True)
            msg = "Calibration Complete"
            title = "Done"
            # QMessageBox.information(self, title, msg)
            self.display_msg(msg_text=msg, title=title, type="info")
        else:
            return

    @Slot()
    def reset_settings(self):
        r"""
        Display a popup asking for confirmation.
        If yes, the settinngs are set to default.
        """

        question = "Are you sure you want to reset your settings?"
        response = self.display_msg(msg_text=question, type="question")

        if response == QMessageBox.StandardButton.Yes:
            self.explorer.reset_soft()

            self.explorer.set_sampling_rate(sampling_rate=250)
            mask = "11111111"
            int_mask = int(mask, 2)
            try:
                self.explorer.set_channels(int_mask)
            except TypeError:
                self.explorer.set_channels(mask)

            print(self.explorer.stream_processor.device_info['sampling_rate'])
            self.update_frame_dev_settings()
            self.display_msg(msg_text="Settings reset", type="info")

        else:
            return

    def change_sampling_rate(self):
        """
        Change the sampling rate
        """

        # AppFunctions._check_filters_new_sr(self)

        sr = self.explorer.stream_processor.device_info['sampling_rate']
        str_value = self.ui.value_sampling_rate.currentText()
        value = int(str_value)
        if int(sr) != value:
            print(
                "Old Sampling rate: ",
                self.explorer.stream_processor.device_info['sampling_rate'])
            self.explorer.set_sampling_rate(sampling_rate=value)
            print(
                "New Sampling rate: ",
                self.explorer.stream_processor.device_info['sampling_rate'])
        else:
            print("Same sampling rate")

    def change_active_channels(self):
        """
        Read selected checkboxes and set the channel mask of the device
        """

        active_chan = []

        for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
            status = str(1) if w.isChecked() else str(0)
            active_chan.append(status)

        active_chan_int = [int(i) for i in active_chan]
        active_chan = [i for i in reversed(active_chan)]

        if active_chan_int != self.explorer.stream_processor.device_info['adc_mask']:
            mask = "".join(active_chan)
            int_mask = int(mask, 2)
            try:
                self.explorer.set_channels(int_mask)
            except TypeError:
                self.explorer.set_channels(mask)

            n_chan = self.explorer.stream_processor.device_info['adc_mask']
            n_chan = [i for i in reversed(n_chan)]

            self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
            AppFunctions.chan_dict = self.chan_dict

            # print('changed')
            # print(f"{self.explorer.stream_processor.device_info['adc_mask']=}")
            # print(f"{self.chan_dict=}")

            self.init_imp()

        else:
            print("Same channel mask")

    @Slot()
    def change_settings(self):
        """
        Apply changes in device settings
        """

        stream_processor = self.explorer.stream_processor

        with self.wait_cursor():
            self.change_active_channels()
            self.change_sampling_rate()

            points = self.plot_points()
            # self.exg_plot = {ch: np.array([np.NaN]*points) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
            # self.t_exg_plot = np.array([np.NaN]*points)
            self.exg_plot_data[1] = {
                ch: np.array([np.NaN]*points) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
            self.exg_plot_data[0] = np.array([np.NaN]*points)
            AppFunctions.exg_plot_data = self.exg_plot_data

            pass

        act_chan = ", ".join([ch for ch in self.chan_dict if self.chan_dict[ch] == 1])
        msg = (
            "Device settings have been changed:"
            f"\nSampling Rate: {int(stream_processor.device_info['sampling_rate'])}"
            f"\nActive Channels: {act_chan}"
        )
        self.display_msg(msg_text=msg, type="info")

        # AppFunctions.init_plots(self)

    # def on_n_chan_change(self):
    #     self.set_n_chan()
    #     self.update_frame_dev_settings()

    def _check_filters_new_sr(self):

        if self.plotting_filters is None:
            return

        # r_value = self.plotting_filters["highpass"]
        # l_value = self.plotting_filters["lowpass"]

        r_value = "" if self.plotting_filters["highpass"] in [None, 'None'] else self.plotting_filters["highpass"]
        l_value = "" if self.plotting_filters["lowpass"] in [None, 'None'] else self.plotting_filters["lowpass"]

        str_value = self.ui.value_sampling_rate.currentText()
        sr = int(str_value)

        nyq_freq = sr / 2.

        max_hc_freq = round(nyq_freq-1, 2)
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

        if (r_value != "") and (float(r_value) >= nyq_freq):
            warning += hc_freq_warning
            self.plotting_filters["highpass"] = max_hc_freq

        AppFunctions._apply_filters(self)
        if warning != "":
            self.display_msg(msg_text=warning, type="info")
