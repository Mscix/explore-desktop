import logging
import os
from datetime import datetime

from exploregui.modules.app_functions import AppFunctions
from exploregui.modules.dialogs import RecordingDialog
from PySide6.QtCore import (
    QTimer,
    Slot
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


logger = logging.getLogger("explorepy." + __name__)


class RecordFunctions(AppFunctions):
    """
    Functions for recording functionality
    """

    def __init__(self, ui, explorer):
        super().__init__(ui, explorer)
        self.is_recording = False

    @Slot()
    def on_record(self):
        """
        Start or stop recording when button is pressed
        """
        logger.debug("Pressed record button -> %s", not self.is_recording)
        if self.is_recording is False:
            self.start_record()
        else:
            self.stop_record()

    def start_record(self):
        '''
        Start signal recording
        '''

        dialog = RecordingDialog()
        default_file_name = self.explorer.stream_processor.device_info["device_name"]
        default_file_name += datetime.now().strftime("_%d%b%Y_%H%M")
        dialog.ui.input_file_name.setPlaceholderText(default_file_name)

        default_dir = str(os.path.expanduser("~"))
        dialog.ui.input_filepath.setPlaceholderText(default_dir)
        data = dialog.exec()

        if data is False:
            return

        file_name = data["file_name"] if data["file_name"] != "" else default_file_name
        if os.path.isfile(file_name + "_ExG.csv"):
            file_name += datetime.now().strftime("_%d%b%Y_%H%M")

        file_path = data["file_path"] if data["file_path"] != "" else default_dir

        file_type = data["file_type"]
        record_duration = data["duration"] if data["duration"] != 0 else None

        self.explorer.record_data(
            file_name=os.path.join(file_path, file_name),
            file_type=file_type,
            duration=record_duration)

        self.is_recording = True
        self.start_timer_recorder(duration=record_duration)

        self.ui.btn_record.setIcon(QIcon(u":icons/icons/cil-media-stop.png"))
        self.ui.btn_record.setText("Stop")
        QApplication.processEvents()

    def stop_record(self):
        """
        Stop recording
        """
        self.explorer.stop_recording()
        self.is_recording = False
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
        self.timer.timeout.connect(lambda: self.displayTime(duration))
        self.timer.start()

    def displayTime(self, duration):
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

    def reset_record_vars(self):
        self.is_recording = False
