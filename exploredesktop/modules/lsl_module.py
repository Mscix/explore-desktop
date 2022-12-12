import logging
from datetime import datetime
from typing import Optional

from PySide6.QtCore import (
    QTimer,
    Slot
)


from exploredesktop.modules.base_model import BaseModel  # isort:skip

logger = logging.getLogger("explorepy." + __name__)


class IntegrationFrameView(BaseModel):
    def __init__(self, ui) -> None:
        super().__init__()
        self.ui = ui
        self.timer = QTimer()

    def setup_ui_connections(self) -> None:
        """Setup connections between widgets and slots"""
        self.ui.btn_push_lsl.clicked.connect(self.on_push_clicked)
        self.ui.cb_lsl_duration.stateChanged.connect(self.enable_lsl_duration)

    @Slot()
    def on_push_clicked(self) -> None:
        """Actions to perform when push button is clicked"""
        logger.debug("Pressed push2lsl button -> %s", not self.explorer.is_pushing_lsl)

        # spinbox_val = self.ui.lsl_duration_value.value()
        # duration = None if spinbox_val == 0 else spinbox_val

        if self.explorer.is_pushing_lsl is False:
            self.start_lsl_push()

        else:
            self.stop_lsl_push()

    def start_lsl_push(self, duration: Optional[int] = None) -> None:
        """Start pushing to lsl

        Args:
            duration (Optional[int]): Duration of the stream. Defaults to None.
        """
        duration = 3600 if duration is None else duration
        self.explorer.push2lsl(duration, block=False)
        self.ui.btn_push_lsl.setText("Stop")
        self.start_timer(duration)

    def stop_lsl_push(self) -> None:
        """Stop pushing to lsl"""
        self.explorer.stop_lsl()
        self.explorer.is_pushing_lsl = False
        self.ui.btn_push_lsl.setText("Push")

    @Slot()
    def enable_lsl_duration(self) -> None:
        """Disable/Enable LSL stream duration"""
        enable = self.ui.cb_lsl_duration.isChecked()
        # if self.ui.cb_lsl_duration.isChecked():
        self.ui.label_13.setEnabled(enable)
        # self.ui.label_lsl_duration.setEnabled(enable)
        self.ui.lsl_duration_value.setEnabled(enable)
        # self.ui.lsl_duration_.setEnabled(enable)

    def start_timer(self, duration: int) -> None:
        """Start timer

        Args:
            duration (int): stream duration
        """
        self.start_time = datetime.now()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: self.display_time(duration))
        self.timer.start()

    def display_time(self, duration: int) -> None:
        """
        Display recording time in label.
        Set button back to initial state once time has expired

        Args:
            duration (int): recording duration
        """
        time = datetime.now() - self.start_time
        total_sec = int(time.total_seconds())
        # strtime = str(time).split(".")[0]
        if duration is None or total_sec <= duration:
            # TODO decide if we want to display time
            # self.ui.label_recording_time.setText(strtime)
            pass
        else:
            self.stop_lsl_push()
