

import logging

from exploredesktop.modules.base_model import BaseModel


logger = logging.getLogger("explorepy." + __name__)


class IntegrationFrameView(BaseModel):
    def __init__(self, ui) -> None:
        super().__init__()
        self.ui = ui

    def setup_ui_connections(self):
        self.ui.btn_push_lsl.clicked.connect(self.on_push_clicked)
        self.ui.cb_lsl_duration.stateChanged.connect(self.enable_lsl_duration)

    def on_push_clicked(self):
        """."""
        logger.debug("Pressed push2lsl button -> %s", not self.explorer.is_pushing_lsl)

        # spinbox_val = self.ui.lsl_duration_value.value()
        # duration = None if spinbox_val == 0 else spinbox_val

        if self.explorer.is_pushing_lsl is False:
            self.start_lsl_push()

        else:
            self.stop_lsl_push()

    def start_lsl_push(self, duration=None):
        """Start pushing to lsl"""
        self.explorer.push2lsl(duration, block=False)
        self.ui.btn_push_lsl.setText("Stop")

    def stop_lsl_push(self):
        """Stop pushing to lsl"""
        self.explorer.stop_lsl()
        self.ui.btn_push_lsl.setText("Push")

    def enable_lsl_duration(self):
        enable = self.ui.cb_lsl_duration.isChecked()
        # if self.ui.cb_lsl_duration.isChecked():
        self.ui.label_13.setEnabled(enable)
        # self.ui.label_lsl_duration.setEnabled(enable)
        self.ui.lsl_duration_value.setEnabled(enable)
        # self.ui.lsl_duration_.setEnabled(enable)
