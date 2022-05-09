from abc import abstractmethod
import os
from typing import Union
from exploredesktop.modules.app_settings import Messages

from exploredesktop.modules.ui import (
    Ui_PlotDialog,
    Ui_RecordingDialog
)
from PySide6.QtCore import QRegularExpression, QSettings
from PySide6.QtGui import (
    QIcon,
    QRegularExpressionValidator,
    QCloseEvent
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog
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
            "file_type": self.file_extension(),
            "duration": int(self.ui.spinBox_recording_time.value())
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
        self.ui.value_lowpass.textChanged.connect(self.verify_input)
        self.ui.value_highpass.textChanged.connect(self.verify_input)

        # Verify input without output message when typing
        self.ui.value_lowpass.textChanged.connect(lambda: self.verify_input(borderOnly=False))
        self.ui.value_highpass.textChanged.connect(lambda: self.verify_input(borderOnly=False))

    def set_current_values(self) -> None:
        """Set values from current filters to attributes
        """
        if self.current_filters is None:  # default values
            self.offset = True
            self.notch = "50"
            self.lowpass = "1"
            self.highpass = "30"
        else:
            self.offset = self.current_filters["offset"]
            self.notch = str(self.current_filters["notch"])
            self.lowpass = str(self.current_filters["lowpass"])
            self.highpass = str(self.current_filters["highpass"])

        if self.highpass == "None":
            self.highpass = ""
        if self.lowpass == "None":
            self.lowpass = ""

    def display_current_values(self) -> None:
        """Add filter values to UI
        """
        # Add options to notch combobox
        self.ui.value_notch.addItems(["", "50", "60"])

        # Display current values
        self.ui.value_notch.setCurrentText(self.notch)
        self.ui.value_highpass.setText(self.highpass)
        self.ui.value_lowpass.setText(self.lowpass)
        self.ui.cb_offset.setChecked(self.offset)

    def add_validators(self) -> None:
        """Add validator to text boxes to only accept doubles
        """
        # Set validators (only accept doubles)
        regex = QRegularExpression(r"([0-9]+\.?[0-9]|\.[0-9])")
        self.ui.value_highpass.setValidator(QRegularExpressionValidator(regex))
        self.ui.value_lowpass.setValidator(QRegularExpressionValidator(regex))

    def verify_input(self, borderOnly=False):
        """Verify frequencies are not above/below the threshold

        Args:
            borderOnly (bool, optional): display message if False. Defaults to False.

        Returns:
            bool: whether input for filter values is correct
        """
        nyq_freq = self.s_rate / 2.

        max_hc_freq = nyq_freq - 1
        min_lc_freq = 0.0035 * nyq_freq

        hc_freq_warning = (
            "High cutoff frequency cannot be larger than or equal to the nyquist frequency."
            f"The maximum high cutoff frequency is {max_hc_freq:.1f} Hz!"
        )

        lc_freq_warning = (
            "Transient band for low cutoff frequency is too narrow."
            f"The minimum low cutoff frequency is {min_lc_freq:.1f} Hz!"
        )

        bp_freq_warning = ("High cutoff frequency must be larger than low cutoff frequency.")

        r_value = "" if self.ui.value_highpass.text() in [None, 'None'] else self.ui.value_highpass.text()
        l_value = "" if self.ui.value_lowpass.text() in [None, 'None'] else self.ui.value_lowpass.text()

        r_stylesheet = ""
        l_stylesheet = ""
        lbl_txt = ""

        accepted = True

        if r_value == "." or l_value == ".":
            accepted = False
            return

        if r_value != "" and l_value == "":  # lowpass
            if float(r_value) >= nyq_freq:
                lbl_txt = hc_freq_warning
                r_stylesheet = "border: 1px solid rgb(217, 0, 0)"
                l_stylesheet = ""
                accepted = False

        elif r_value == "" and l_value != "":
            lc_freq = float(l_value) / nyq_freq
            if lc_freq <= 0.0035:
                lbl_txt = lc_freq_warning
                r_stylesheet = ""
                l_stylesheet = "border: 1px solid rgb(217, 0, 0)"
                accepted = False

        elif r_value != "" and l_value != "":
            lc_freq = float(l_value) / nyq_freq
            if float(l_value) >= float(r_value):
                lbl_txt = bp_freq_warning
                r_stylesheet = "border: 1px solid rgb(217, 0, 0)"
                l_stylesheet = "border: 1px solid rgb(217, 0, 0)"
                accepted = False

            elif float(r_value) >= nyq_freq:
                lbl_txt = hc_freq_warning
                r_stylesheet = "border: 1px solid rgb(217, 0, 0)"
                l_stylesheet = ""
                accepted = False

            elif lc_freq <= 0.0035:
                lbl_txt = lc_freq_warning
                r_stylesheet = ""
                l_stylesheet = "border: 1px solid rgb(217, 0, 0)"
                accepted = False

        else:
            r_stylesheet = ""
            l_stylesheet = ""
            lbl_txt = ""

        self.ui.value_highpass.setStyleSheet(r_stylesheet)
        self.ui.value_lowpass.setStyleSheet(l_stylesheet)
        if not borderOnly:
            self.ui.lbl_warning.setText(lbl_txt)
            if lbl_txt != "":
                self.ui.lbl_warning.setHidden(False)
            else:
                self.ui.lbl_warning.setHidden(True)

        self.ui.value_lowpass.textChanged.connect(
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(accepted))
        self.ui.value_highpass.textChanged.connect(
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(accepted))
        return accepted

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
            "lowpass":
                None if self.ui.value_lowpass.text() in [None, 'None', ""] else float(self.ui.value_lowpass.text()),
            "highpass":
                None if self.ui.value_highpass.text() in [None, 'None', ""] else float(self.ui.value_highpass.text())
        }
        return data


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    plotting_filters = {'offset': True, 'notch': 50, 'lowpass': 0.5, 'highpass': 30.0}

    dialog = FiltersDialog(sr=250, current_filters=plotting_filters)
    # filt = dialog.exec()
    # print(filt)
    # dialog = RecordingDialog()
    filt = dialog.exec()
    print(filt)
