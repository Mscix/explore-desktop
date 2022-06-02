import os
from abc import abstractmethod
from typing import Union

import numpy as np
from PySide6.QtCore import (
    QRegularExpression,
    QSettings
)
from PySide6.QtGui import (
    QCloseEvent,
    QIcon,
    QRegularExpressionValidator
)
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog
)


from exploredesktop.modules.app_settings import (  # isort: skip
    Messages,
    Settings
)
from exploredesktop.modules.utils import verify_filters  # isort: skip
from exploredesktop.modules.ui import (  # isort: skip
    Ui_PlotDialog,
    Ui_RecordingDialog
)

CWD = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(
    os.path.join(CWD, os.pardir), "images", "MentalabLogo.png")


class CustomDialog(QDialog):
    """Base class for custom pop-up dialogs

    Args:
       QDialog (Pyside6.QtWidgets.QDialog): pyside widget
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.close = False

    # pylint: disable=invalid-name
    def closeEvent(self, arg__1: QCloseEvent) -> None:
        """Rewrite close event

        Args:
            arg__1 (PySide6.QtGui.QCloseEvent): pyside close event
        """
        self.close = True
        return super().closeEvent(arg__1)

    def reject(self) -> None:
        """Rewrite reject event, i.e. clicking on cancel
        """
        self.close = True
        return super().reject()

    @abstractmethod
    def get_data(self):
        """Abstract function to be implemented in child classes

        Raises:
            NotImplementedError: method has to be override in child class
        """
        raise NotImplementedError("Must override get_data method")

    def exec(self) -> Union[bool, dict]:
        """Rewrite exec method

        Returns:
            Union[bool, dict]: False if dialog was closed or canceled. Otherwise dictionary with data from pop-up
        """
        super().exec()

        if self.close:
            return False

        data = self.get_data()
        return data


class RecordingDialog(CustomDialog):
    """Dialog Recording Settings pop up

    Args:
        QDialog (Pyside6.QtWidgets.QDialog): pyside widget
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_RecordingDialog()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(ICON_PATH))
        self.setWindowTitle("Recording Settings")

        self.recording_time = int(self.ui.spinBox_recording_time.value())
        self.recording_mode = "csv"
        self.recording_path = ""

        self.ui.btn_browse.clicked.connect(self.save_filename)
        self.ui.spinBox_recording_time.setMaximum(10000000)
        self.ui.spinBox_recording_time.setValue(3600)
        self.ui.rdbtn_csv.setChecked(True)

        # self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.cancelEvent)

    def file_extension(self) -> str:
        """Retrun file extension selected

        Returns:
            str: file extension (edf or csv)
        """
        if self.ui.rdbtn_edf.isChecked():
            self.file_type = "edf"
        else:
            self.file_type = "csv"

        return self.file_type

    def save_filename(self):
        """
        Open a dialog to select file name to be saved
        """
        settings = QSettings("Mentalab", "ExploreDesktop")
        path = settings.value("last_record_folder")
        if not path:
            path = os.path.expanduser("~")

        dialog = QFileDialog()
        file_path = dialog.getExistingDirectory(
            self,
            "Choose Directory",
            path,
            QFileDialog.ShowDirsOnly)

        self.recording_path = file_path
        self.ui.input_filepath.setText(self.recording_path)
        if path != self.recording_path:
            settings.setValue("last_record_folder", self.recording_path)

    def get_data(self) -> dict:
        """Get dialog data

        Returns:
            dict: _description_
        """
        data = {
            "file_name": self.ui.input_file_name.text(),
            "file_path": self.ui.input_filepath.text(),
            "duration": int(self.ui.spinBox_recording_time.value()),
            "file_type": self.file_extension()
        }
        return data


class FiltersDialog(CustomDialog):
    """Dialog Filters Pop-up

    Args:
        QDialog (Pyside6.QtWidgets.QDialog): pyside widget
    """
    def __init__(self, sr, current_filters, parent=None):
        super().__init__(parent)
        self.ui = Ui_PlotDialog()
        self.s_rate = float(sr)
        self.current_filters = current_filters

        self.ui.setupUi(self)
        self.setWindowTitle("Visualization Settings")

        self.ui.lbl_warning.hide()
        self.ui.cb_offset.setToolTip(Messages.OFFSET_EXPLANATION)

        self.set_current_values()
        self.display_current_values()
        self.add_validators()

        # Verify input without output message when typing
        self.ui.value_lowcutoff.textChanged.connect(self.verify_input)
        self.ui.value_highcutoff.textChanged.connect(self.verify_input)

        # Verify input without output message when typing
        self.ui.value_lowcutoff.textChanged.connect(self.verify_input)
        self.ui.value_highcutoff.textChanged.connect(self.verify_input)

    def set_current_values(self) -> None:
        """Set values from current filters to attributes
        """
        if self.current_filters is None:  # default values
            self.offset = True
            self.notch = "50"
            self.low_cutoff = "1" if self.s_rate < 1000 else "2"
            self.high_cutoff = "30"
        else:
            self.offset = self.current_filters["offset"]
            self.notch = str(self.current_filters["notch"])
            self.low_cutoff = str(self.current_filters["low_cutoff"])
            self.high_cutoff = str(self.current_filters["high_cutoff"])

        if self.high_cutoff == "None":
            self.high_cutoff = ""
        if self.low_cutoff == "None":
            self.low_cutoff = ""

    def display_current_values(self) -> None:
        """Add filter values to UI
        """
        # Add options to notch combobox
        self.ui.value_notch.addItems(["", "50", "60"])

        # Display current values
        self.ui.value_notch.setCurrentText(self.notch)
        self.ui.value_highcutoff.setText(self.high_cutoff)
        self.ui.value_lowcutoff.setText(self.low_cutoff)
        self.ui.cb_offset.setChecked(self.offset)

    def add_validators(self) -> None:
        """Add validator to text boxes to only accept doubles
        """
        # Set validators (only accept doubles)
        regex = QRegularExpression(r"([0-9]+\.?[0-9]|\.[0-9])")
        self.ui.value_highcutoff.setValidator(QRegularExpressionValidator(regex))
        self.ui.value_lowcutoff.setValidator(QRegularExpressionValidator(regex))

    def verify_input(self):
        """Verify frequencies are not above/below the threshold
        """
        nyq_freq = self.s_rate / 2.
        max_hc_freq = nyq_freq - 1
        min_lc_freq = Settings.MIN_LC_WEIGHT * nyq_freq

        hc_freq_warning = (
            "High cutoff frequency cannot be larger than or equal to the nyquist frequency."
            f"The maximum high cutoff frequency is {np.ceil(max_hc_freq*10)/10} Hz!"
        )

        lc_freq_warning = (
            "Transient band for low cutoff frequency is too narrow."
            f"The minimum low cutoff frequency is {np.ceil(min_lc_freq*10)/10} Hz!"
        )

        bp_freq_warning = ("High cutoff frequency must be larger than low cutoff frequency.")

        hc_freq = "" if self.ui.value_highcutoff.text() in [None, 'None', ''] else self.ui.value_highcutoff.text()
        lc_freq = "" if self.ui.value_lowcutoff.text() in [None, 'None', ''] else self.ui.value_lowcutoff.text()

        hc_stylesheet = ""
        lc_stylesheet = ""
        lbl_txt = ""

        if hc_freq in ["."] or lc_freq in ["."]:
            return

        filter_ok = verify_filters((lc_freq, hc_freq), self.s_rate)

        if filter_ok['lc_freq'] is False:
            lbl_txt = lc_freq_warning
            hc_stylesheet = ""
            lc_stylesheet = "border: 1px solid rgb(217, 0, 0)"

        elif filter_ok['hc_freq'] is False:
            lbl_txt = hc_freq_warning
            hc_stylesheet = "border: 1px solid rgb(217, 0, 0)"
            lc_stylesheet = ""

        elif filter_ok['bp_valid'] is False:
            lbl_txt = bp_freq_warning
            hc_stylesheet = "border: 1px solid rgb(217, 0, 0)"
            lc_stylesheet = "border: 1px solid rgb(217, 0, 0)"

        self._apply_le_stylesheets(lc_stylesheet, hc_stylesheet, lbl_txt)
        enable = False not in filter_ok.values()
        self._enable_ok_button(enable)

    def _apply_le_stylesheets(self, lc_stylesheet: str, hc_stylesheet: str, lbl_txt: str):
        self.ui.value_highcutoff.setStyleSheet(hc_stylesheet)
        self.ui.value_lowcutoff.setStyleSheet(lc_stylesheet)
        self.ui.lbl_warning.setText(lbl_txt)
        if lbl_txt != "":
            self.ui.lbl_warning.setHidden(False)
        else:
            self.ui.lbl_warning.setHidden(True)

    def _enable_ok_button(self, enable: bool):
        self.ui.value_lowcutoff.textChanged.connect(
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable))
        self.ui.value_highcutoff.textChanged.connect(
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable))

    def get_data(self) -> dict:
        """Get filter data from dialog

        Returns:
            dict: dictionary containing filter values
        """
        data = {
            "offset":
                self.ui.cb_offset.isChecked(),
            "notch":
                None if self.ui.value_notch.currentText() == "" else int(self.ui.value_notch.currentText()),
            "low_cutoff":
                None if self.ui.value_lowcutoff.text() in [None, 'None', ""] else float(self.ui.value_lowcutoff.text()),
            "high_cutoff":
                None if self.ui.value_highcutoff.text() in [
                    None, 'None', ""] else float(self.ui.value_highcutoff.text())
        }
        return data
