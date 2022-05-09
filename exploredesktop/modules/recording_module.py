import logging
import os
from datetime import datetime

from exploredesktop.modules.base_model import BaseModel
from exploredesktop.modules.dialogs import RecordingDialog
from PySide6.QtCore import (
    QTimer,
    Slot,
    QSettings
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog


logger = logging.getLogger("explorepy." + __name__)


class RecordFunctions(BaseModel):
    """
    Functions for recording functionality
    """

    def __init__(self, ui):
        super().__init__()
        self.ui = ui

    def setup_ui_connections(self):
        self.ui.btn_record.clicked.connect(self.on_record_clicked)

    @Slot()
    def on_record_clicked(self):
        """
        Start or stop recording when button is pressed
        """
        logger.debug("Pressed record button -> %s", not self.explorer.is_recording)
        if self.explorer.is_recording is False:
            self.start_record()
        else:
            self.stop_record()

    def start_record(self):
        """
        Start signal recording
        """

        dialog = RecordingDialog()
        default_file_name = self._set_filename_placeholder(dialog)
        default_dir = self._set_dir_placeholder(dialog)
        data = dialog.exec()

        if data is False:
            return

        file_name = data["file_name"] if data["file_name"] != "" else default_file_name
        if os.path.isfile(file_name + "_ExG.csv"):
            file_name += datetime.now().strftime("_%d%b%Y_%H%M")

        file_path = data["file_path"] if data["file_path"] != "" else default_dir
        record_duration = data["duration"] if data["duration"] != 0 else None
        file_type = data["file_type"]

        self.explorer.record_data(
            file_name=os.path.join(file_path, file_name),
            file_type=file_type,
            duration=record_duration)

        # self.is_recording = True
        self.start_timer_recorder(duration=record_duration)

        self.ui.btn_record.setIcon(QIcon(u":icons/icons/cil-media-stop.png"))
        self.ui.btn_record.setText("Stop")
        QApplication.processEvents()

    def _set_dir_placeholder(self, dialog: QDialog) -> str:
        """Define default saving directory and set it up as a placeholder.

        Args:
            dialog (QDialog): Recording dialog with the line edit that needs the placeholder

        Returns:
            str: default directory path
        """
        settings = QSettings("Mentalab", "ExploreDesktop")
        default_dir = settings.value("last_record_folder")
        if not default_dir:
            default_dir = str(os.path.expanduser("~"))
        dialog.ui.input_filepath.setPlaceholderText(default_dir)
        return default_dir

    def _set_filename_placeholder(self, dialog: QDialog) -> str:
        """Define default saving file name and set it up as a placeholder.

        Args:
            dialog (QDialog): Recording dialog with the line edit that needs the placeholder

        Returns:
            str: default file name
        """
        default_file_name = self.explorer.device_name
        default_file_name += datetime.now().strftime("_%d%b%Y_%H%M")
        dialog.ui.input_file_name.setPlaceholderText(default_file_name)
        return default_file_name

    def stop_record(self):
        """
        Stop recording
        """
        self.explorer.stop_recording()
        self.timer.stop()
        self.ui.btn_record.setIcon(QIcon(u":icons/icons/cil-media-record.png"))
        self.ui.btn_record.setText("Record")
        self.ui.label_recording_time.setText("00:00:00")
        QApplication.processEvents()

    def start_timer_recorder(self, duration):
        """
        Start timer to display recording time
        """
        self.start_time = datetime.now()

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: self.display_rec_time(duration))
        self.timer.start()

    def display_rec_time(self, duration):
        """
        Display recording time in label
        """
        time = datetime.now() - self.start_time
        total_sec = int(time.total_seconds())
        strtime = str(time).split(".")[0]
        if duration is None or total_sec <= duration:
            self.ui.label_recording_time.setText(strtime)
        else:
            self.stop_record()
