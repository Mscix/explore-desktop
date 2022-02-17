import logging
from contextlib import contextmanager

import numpy as np
from exploregui.modules.app_settings import Settings
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox
)


logger = logging.getLogger("explorepy." + __name__)


class AppFunctions():
    chan_dict = {}
    is_connected = False
    exg_plot_data = [np.array([np.NaN] * 2500), {}, {}]
    n_chan = 8
    chan_list = Settings.CHAN_LIST[:n_chan]
    plotting_filters = None

    def __init__(self, ui, explorer) -> None:
        self.ui = ui
        self.explorer = explorer

    #########################
    # Init Functions
    #########################
    def init_imp(self):
        active_chan = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]

        for chan in Settings.CHAN_LIST:
            frame_name = f"frame_{chan}_2"
            ch_frame = self.get_widget_by_objName(frame_name)

            if ch_frame is None:
                logger.warning(f"Could not find frame widget {frame_name}")
            else:
                if chan not in active_chan:
                    ch_frame.hide()
                elif chan in active_chan and ch_frame.isHidden():
                    ch_frame.show()

    #########################
    # Aux Functions
    #########################
    def lineedit_stylesheet(self):

        if self.ui.dev_name_input.text() == "":
            color = "#B4B4B4"
        else:
            color = "#000000"

        stylesheet = f"""
        QLineEdit{{
            color: {color};
            border: 1px solid rgb(84, 89, 124);
        }}"""

        self.ui.dev_name_input.setStyleSheet(stylesheet)

    def get_widget_by_objName(self, name):
        widgets = QApplication.instance().allWidgets()
        for x in widgets:
            if str(x.objectName()) == name:
                return x
        logger.warning(f"Could not find {name}")
        return None

    def display_msg(self, msg_text, title=None, type="error"):
        msg = QMessageBox()
        msg.setText(msg_text)
        # msg.setStyleSheet(Settings.POPUP_STYLESHEET)

        if type == "error":
            wdw_title = "Error" if title is None else title
            msg.setIcon(QMessageBox.Critical)
        elif type == "info":
            wdw_title = "Information" if title is None else title
            msg.setIcon(QMessageBox.Information)
        elif type == "question":
            wdw_title = "Confirmation" if title is None else title
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setIcon(QMessageBox.Question)

        msg.setWindowTitle(wdw_title)

        response = msg.exec()
        return response

    @contextmanager
    def wait_cursor(self):
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            yield
        finally:
            QApplication.restoreOverrideCursor()

    def plot_points(self, orn=False, downsampling=Settings.DOWNSAMPLING):
        time_scale = self.get_timeScale()
        sr = self.get_samplingRate()

        if not orn:
            if downsampling:
                points = (time_scale * sr) / (sr / Settings.EXG_VIS_SRATE)
            else:
                points = (time_scale * sr)
        else:
            points = time_scale * Settings.ORN_SRATE

        return int(points)

    def get_timeScale(self):
        t_str = self.ui.value_timeScale.currentText()
        t = Settings.TIME_RANGE_MENU[t_str]
        return t

    def get_samplingRate(self):
        stream_processor = self.explorer.stream_processor
        sr = stream_processor.device_info['sampling_rate']
        return sr

    def apply_filters(self):
        stream_processor = self.explorer.stream_processor
        notch_freq = self.plotting_filters["notch"]
        high_freq = self.plotting_filters["highpass"]
        low_freq = self.plotting_filters["lowpass"]

        if notch_freq is not None:
            stream_processor.add_filter(cutoff_freq=notch_freq, filter_type='notch')

        if high_freq is not None and low_freq is not None:
            stream_processor.add_filter(
                cutoff_freq=(low_freq, high_freq), filter_type='bandpass')
        elif high_freq is not None:
            stream_processor.add_filter(cutoff_freq=high_freq, filter_type='highpass')
        elif low_freq is not None:
            stream_processor.add_filter(cutoff_freq=low_freq, filter_type='lowpass')

        logger.info(f"Applied filters{self.plotting_filters}")

    #########################
    # Set/Get Functions
    #########################

    def set_n_chan(self):
        self.n_chan = int(self.ui.n_chan.currentText())
        self.chan_list = Settings.CHAN_LIST[:self.n_chan]

    def get_chan_dict(self):
        chan_dict = self.chan_dict
        return chan_dict

    def set_chan_dict(self, value: dict):
        self.chan_dict = value

    def get_exg_plot_data(self):
        exg_plot_data = self.exg_plot_data
        return exg_plot_data

    def set_exg_plot_data(self, value: list):
        self.exg_plot_data = value

    def get_is_connected(self):
        is_conn = self.is_connected
        return is_conn

    def set_is_connected(self, value: bool):
        self.is_connected = value

    def get_chan_list(self):
        chan_list = self.chan_list
        return chan_list

    def get_imp_status(self):
        return self.is_imp_measuring

    def set_imp_status(self, value: bool):
        self.is_imp_measuring = value

    #########################
    # Set/Get Functions
    #########################
    def reset_exg_plot_data(self):
        """
        Resets variable exg_plot_data
        """
        points = self.plot_points()
        points_no_ds = self.plot_points(downsampling=False)
        self.exg_plot_data[0] = np.array([np.NaN] * points)
        self.exg_plot_data[1] = {
            ch: np.array([np.NaN] * points) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
        self.exg_plot_data[2] = {
            ch: np.array([np.NaN] * points_no_ds) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}

    def reset_vars(self):
        self.chan_dict = {}
        self.is_connected = False
        self.exg_plot_data = [np.array([np.NaN] * 2500), {}, {}]
        self.n_chan = 8
        self.chan_list = Settings.CHAN_LIST[:self.n_chan]
        self.plotting_filters = None
