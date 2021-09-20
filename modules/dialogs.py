from modules.dialog_plot_settings import Ui_Dialog as Ui_PlotDialog
from modules.dialog_recording_settings import Ui_Dialog as Ui_RecordingDialog
from main import *
from PySide6.QtWidgets import QDialog


class PlotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PlotDialog()
        self.ui.setupUi(self)
        # self.int_validator = QIntValidator()
        self.ui.label_5.hide()

        # self.ui.value_notch.addItems(["", 50, 60])
        self.ui.comboBox.addItems(["", "50", "60"])
        self.ui.comboBox.setCurrentText("")
        # self.ui.value_notch.setValidator(QIntValidator())
        # self.ui.lineEdit.setValidator(QIntValidator())

        self.ui.value_highpass.setValidator(QDoubleValidator())
        self.ui.value_lowpass.setValidator(QDoubleValidator())

    def exec(self):
        super().exec()
        return {
            "offset": self.ui.cb_offset.isChecked(),
            "notch": None if self.ui.comboBox.currentText() == "" == "" else int(self.ui.comboBox.currentText()),
            "lowpass": None if self.ui.value_lowpass.text() == "" else float(self.ui.value_lowpass.text()),
            "highpass": None if self.ui.value_highpass.text() == "" else float(self.ui.value_highpass.text())
            }


class RecordingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_RecordingDialog()
        self.ui.setupUi(self)
        self.recording_time = self.ui.spinBox.value()
        self.recording_mode = "csv"
        self.recording_path = ""

        self.ui.btn_browse.clicked.connect(self.save_filename)
        self.ui.spinBox.setMaximum(10000000)
        self.ui.rdbtn_csv.setChecked(True)

    def save_filename(self):
        """
        Open a dialog to select file name to be saved
        """
        if self.ui.rdbtn_csv.isChecked():
            self.recording_mode = "csv"
        elif self.ui.rdbtn_edf.isChecked():
            self.recording_mode = "edf"
        else:
            self.recording_mode = "csv"

        file_types = "CSV files(*.csv);;EFD files (*.efd)"
        dialog = QFileDialog()
        # dialog.setDefaultSuffix(".csv")
        options = dialog.Options()
        file_name, _ = dialog.getSaveFileName(
            self,
            "Save File As",
            "",
            filter=file_types, options=options
            )

        self.recording_path = file_name  # + "." + self.recording_mode
        self.ui.input_filepath.setText(self.recording_path)
        QApplication.processEvents()

    def exec(self):
        super().exec()
        return {
            "file_path": self.recording_path,
            "file_type": self.recording_mode,
            "duration": self.recording_time
            }
