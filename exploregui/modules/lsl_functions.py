from modules.app_functions import AppFunctions


class LSLFunctions(AppFunctions):
    def __init__(self, ui, explorer):
        super().__init__(ui, explorer)
        self.is_pushing = False

    def push_lsl(self):
        if self.is_connected is False:
            self.exg_plot_datadisplay_msg(msg_text="Please connect an Explore device first")
            return

        # spinbox_val = self.ui.spinBox.value()
        # duration = None if spinbox_val == 0 else spinbox_val

        if self.is_pushing is False:
            self.is_pushing = True
            self.explorer.push2lsl(duration=None, block=False)
            self.ui.btn_push_lsl.setText("Stop")
        else:
            self.is_pushing = False
            self.explorer.stop_lsl()
            self.ui.btn_push_lsl.setText("Push")

    def enable_lsl_duration(self):
        enable = self.ui.checkBox.isChecked()
        # if self.ui.cb_lsl_duration.isChecked():
        self.ui.label_13.setEnabled(enable)
        # self.ui.label_lsl_duration.setEnabled(enable)
        self.ui.spinBox.setEnabled(enable)
        # self.ui.lsl_duration_.setEnabled(enable)

    def get_pushing_status(self):
        return self.is_pushing

    def set_pushing_status(self, value: bool):
        self.is_pushing = value
