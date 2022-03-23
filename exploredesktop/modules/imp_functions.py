import logging
from re import L
import time
from click import style
import explorepy

import numpy as np

from exploredesktop.modules.app_functions import AppFunctions
from exploredesktop.modules.app_settings import Settings
from explorepy.stream_processor import TOPICS
from PySide6.QtCore import Slot, QAbstractTableModel, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox
)
from PySide6.QtGui import QColor


logger = logging.getLogger("explorepy." + __name__)

def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

class ImpTableModel(QAbstractTableModel):
    def __init__(self):
        super(ImpTableModel, self).__init__()
        # self._data = ["5" for i in range(1,9)]
        # self._data = np.array([f"ch{i}\nNA" for i in range(1, 9)])
        self._data = np.array([[f"ch{i}\nNA" for i in range(1, 9)]])
        # self._data = np.array([[f"ch{i}\nNA" for i in range(1, 9)], [f"ch{i}\n5" for i in range(1, 9)]])
        print(self._data)
        self.mode = "dry"

    def get_stylesheet(self, value):
        rules_dict = Settings.COLOR_RULES_DRY if self.mode == "dry" else Settings.COLOR_RULES_WET

        if "Open" in value:
            imp_stylesheet = Settings.BLACK_IMPEDANCE_STYLESHEET
        elif not is_number(value): # or "NA" in value:
            imp_stylesheet = Settings.GRAY_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["red"]:
            imp_stylesheet = Settings.BLACK_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["orange"]:
            imp_stylesheet = Settings.RED_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["yellow"]:
            imp_stylesheet = Settings.ORANGE_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["green"]:
            imp_stylesheet = Settings.YELLOW_IMPEDANCE_STYLESHEET
        else:
            imp_stylesheet = Settings.GREEN_IMPEDANCE_STYLESHEET

        return imp_stylesheet

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row(), index.column()]

        if role == Qt.BackgroundRole:
            value = self._data[index.row(), index.column()]
            print(value)
            value = value.split("\n")[1]
            value = value.replace(" K\u03A9", "")
            value = value.replace("<", "")
            print(value)
            stylesheet = self.get_stylesheet(value)
            return QColor(stylesheet)
            # return QColor("#FFFFFF")

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter + Qt.AlignHCenter

        if role == Qt.ForegroundRole:
            return QColor("#FFFFFF")

    def rowCount(self, index):
        # The length of the outer list.
        return self._data.shape[0]

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        # if len(self._data) == 1:
        #     return 1
        # return self._data.shape[0]
        return self._data.shape[1]

    def setData(self, new_data, role=Qt.EditRole):
        if new_data is not None and role == Qt.EditRole:
            self._data = new_data
            self.layoutChanged.emit()
            # self.dataChanged.emit()
            return True
        return False

    def format_imp_value(self, value: float) -> str:
        """Format impedance value to correct display format

        Args:
            value (float): _description_

        Returns:
            str: formatted impedance value
        """
        if value < 5:
            str_value = "<5 K\u03A9"
        elif (self.mode == "wet" and value > Settings.COLOR_RULES_WET["open"]) or \
                (self.mode == "dry" and value > Settings.COLOR_RULES_DRY["open"]):
            str_value = "Open"
        else:
            str_value = str(int(round(value, 0))) + " K\u03A9"
        return str_value

    def imp_callback(self, packet):
        imp_values = packet.get_impedances()
        # for chan, value in zip(active_chan, imp_values):
        data_1d = []
        for chan, value in enumerate(imp_values):
            value = self.format_imp_value(value)
            data_1d.append(f"ch{chan+1}\n{value}")
        data = np.array([data_1d])
        if data.shape[1] > Settings.MAX_IMP_ROW:
            data = np.reshape(data.shape[1] // Settings.MAX_IMP_ROW, Settings.MAX_IMP_ROW)
        self.setData(data)

    def subscribe_callback(self, stream_processor):
        stream_processor.imp_initialize(notch_freq=50)
        stream_processor.subscribe(callback=self.imp_callback, topic=TOPICS.imp)




class IMPFunctions(AppFunctions):
    """_summary_

    Args:
        AppFunctions (_type_): _description_
    """
    def __init__(self, ui, explorer, signal_imp):
        super().__init__(ui, explorer)
        self.signal_imp = signal_imp
        self.is_imp_measuring = False

    def disable_imp(self):
        """
        Disable impedance measurement and reset GUI
        """
        if self.is_connected:
            self.explorer.stream_processor.disable_imp()
            self.reset_impedance()
            self.ui.btn_imp_meas.setText("Measure Impedances")
            self.is_imp_measuring = False
        else:
            return

    def emit_imp(self):
        """
        Update impedances
        """

        stream_processor = self.explorer.stream_processor
        logger.debug(f"emit_imp - {self.chan_dict=}")
        active_chan = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]
        logger.debug(f"active channels: {active_chan}")
        data = {ch: ["", self._impedance_stylesheet_wet("")] for ch in active_chan}

        def callback(packet):
            mode = "dry" if self.ui.imp_mode.currentText() == "Dry electrodes" else "wet"

            imp_values = packet.get_impedances()
            for chan, value in zip(active_chan, imp_values):
                # print(chan, value)
                value = value / 2
                # print(value)
                if value < 5:
                    str_value = "<5 K\u03A9"
                elif (mode == "wet" and value > Settings.COLOR_RULES_WET["open"]) or \
                     (mode == "dry" and value > Settings.COLOR_RULES_DRY["open"]):
                    str_value = "Open"
                else:
                    str_value = str(int(round(value, 0))) + " K\u03A9"

                if mode == "dry":
                    ch_stylesheet = self._impedance_stylesheet_dry(value=value)
                else:
                    ch_stylesheet = self._impedance_stylesheet_wet(value=value)

                data[chan] = [str_value, ch_stylesheet]

            self.signal_imp.emit(data)

        if self.is_connected is False:
            self.display_msg(msg_text="Please connect an Explore device first")
            return

        else:
            if self.is_imp_measuring is False:
                sr_ok = self._verify_sampling_rate()
                if sr_ok is False:
                    return
                self.ui.btn_imp_meas.setText("Stop")
                QApplication.processEvents()
                stream_processor.imp_initialize(notch_freq=50)
                stream_processor.subscribe(callback=callback, topic=TOPICS.imp)
                self.is_imp_measuring = True
                # AppFunctions.is_imp_measuring = self.is_imp_measuring

            else:
                # self.signal_imp.disconnect()
                self.disable_imp()

    @Slot(dict)
    def update_impedance(self, chan_dict_data):
        """Update impedance value and color

        Args:
            chan_dict_data (dict): dictionary with channel as key and [value, stylesheet] as value
        """
        for chan in chan_dict_data.keys():
            new_stylesheet = chan_dict_data[chan][1]
            frame_name = f"frame_{chan}_color"
            ch_frame = self.get_widget_by_objName(frame_name)
            ch_frame.setStyleSheet(new_stylesheet)

            new_value = chan_dict_data[chan][0]
            label_name = f"label_{chan}_value"
            ch_label = self.get_widget_by_objName(label_name)
            ch_label.setText(new_value)

    def check_is_imp(self):
        """
        Check if impedance measurement is active.
        If so ask the user whether to disable it.
        """
        disabled = False
        if self.is_imp_measuring:
            msg = "Impedance mode will be disabled. Do you want to continue?"
            response = self.display_msg(msg_text=msg, type="question")

            if response == QMessageBox.StandardButton.Yes:
                self.disable_imp()
                disabled = True

        return disabled

    def _impedance_stylesheet_wet(self, value):
        """
        Return the stylesheet corresponding to the impedance value
        """
        if isinstance(value, str):
            imp_stylesheet = Settings.GRAY_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_WET["red"]:  # 500
            imp_stylesheet = Settings.BLACK_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_WET["orange"]:  # 100
            imp_stylesheet = Settings.RED_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_WET["yellow"]:  # 50
            imp_stylesheet = Settings.ORANGE_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_WET["green"]:  # 20
            imp_stylesheet = Settings.YELLOW_IMPEDANCE_STYLESHEET
        else:
            imp_stylesheet = Settings.GREEN_IMPEDANCE_STYLESHEET

        return imp_stylesheet

    def _impedance_stylesheet_dry(self, value):
        """
        Return the stylesheet corresponding to the impedance value
        """
        if isinstance(value, str):
            imp_stylesheet = Settings.GRAY_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_DRY["red"]:  # 500
            imp_stylesheet = Settings.BLACK_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_DRY["orange"]:  # 200
            imp_stylesheet = Settings.RED_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_DRY["yellow"]:  # na
            imp_stylesheet = Settings.ORANGE_IMPEDANCE_STYLESHEET
        elif value > Settings.COLOR_RULES_DRY["green"]:  # 100
            imp_stylesheet = Settings.YELLOW_IMPEDANCE_STYLESHEET
        else:
            imp_stylesheet = Settings.GREEN_IMPEDANCE_STYLESHEET

        return imp_stylesheet

    def reset_impedance(self):
        """
        Reset impedance frame to default
        """
        if self.is_connected:
            active_chan = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]
            chan_dict_data = {ch: ["NA", self._impedance_stylesheet_wet("NA")] for ch in active_chan}

            for chan in chan_dict_data.keys():
                new_stylesheet = chan_dict_data[chan][1]
                frame_name = f"frame_{chan}_color"
                ch_frame = self.get_widget_by_objName(frame_name)
                ch_frame.setStyleSheet(new_stylesheet)

                new_value = chan_dict_data[chan][0]
                label_name = f"label_{chan}_value"
                ch_label = self.get_widget_by_objName(label_name)
                ch_label.setText(new_value)
                QApplication.processEvents()

            first_label = self.get_widget_by_objName(f"label_{active_chan[0]}_value")
            first_label.setText("NA")
            first_frame = self.get_widget_by_objName(f"frame_{active_chan[0]}_color")
            first_frame.setStyleSheet(self._impedance_stylesheet_wet("NA"))
            QApplication.processEvents()

        else:
            return

    def _verify_sampling_rate(self):
        """Check whether sampling rate is set to 250Hz. If not, ask the user if they want to change it

        Returns:
            bool: whether sampling rate is 250Hz
        """
        self.explorer._check_connection()
        s_rate = int(self.get_samplingRate())
        if s_rate != 250:
            question = (
                "Impedance mode only works in 250 Hz sampling rate!"
                f"\nThe current sampling rate is {s_rate}. "
                "Click on Yes to change the sampling rate.")

            response = self.display_msg(msg_text=question, type="question")

            if response == QMessageBox.StandardButton.Yes:
                self.explorer.set_sampling_rate(sampling_rate=250)
                self.ui.value_sampling_rate.setCurrentText(str(250))
                accept = True
            else:
                accept = False
        else:
            accept = True
        return accept

    def reset_imp_vars(self):
        """
        Reset class variables
        """
        self.is_imp_measuring = False

if __name__ == "__main__":
    from PySide6 import QtWidgets
    import sys

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()

            self.impTable = QtWidgets.QTableView()

            self.button = QtWidgets.QPushButton("test", self)
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(self.impTable)
            layout.addWidget(self.button)
            widget = QtWidgets.QWidget()
            widget.setLayout(layout)
            self.button.clicked.connect(self.updatedata)
            # data = [5 for i in range(1,9)]
            # print(data)
            self.model = ImpTableModel()
            self.impTable.setModel(self.model)
            self.impTable.horizontalHeader().setVisible(False)
            self.impTable.verticalHeader().setVisible(False)
            # self.impTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
            # self.impTable.verticalHeader().setDefaultSectionSize(30)
            self.impTable.setRowHeight(0, 100)
            self.impTable.setRowHeight(1, 100)

            self.setCentralWidget(widget)
            self.connect()
            # self.setCentralWidget(self.impTable)

        def connect(self):
            explorer = explorepy.Explore()
            explorer.connect(device_name="Explore_CA18")
            self.stream_processor = explorer.stream_processor

        def updatedata(self):
            # data = np.array([[f"ch{i}\n20" for i in range(1, 9)], [f"ch{i}\n80" for i in range(1, 9)]])
            # self.model.setData(data)
            self.model.subscribe_callback(self.stream_processor)


    app=QtWidgets.QApplication(sys.argv)
    window=MainWindow()
    window.show()
    app.exec()