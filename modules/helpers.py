from contextlib import contextmanager
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QMessageBox
from modules.app_settings import Settings


def get_widget_by_objName(name):
    # widgets = page.allWidgets()
    widgets = QApplication.instance().allWidgets()
    for x in widgets:
        # print(x)
        if str(x.objectName()) == name:
            return x
    print(f"Could not find {name}")
    return None


def display_msg(msg_text, title=None, type="error"):
    # msg = QMessageBox.critical(self, title="Error", text=msg)
    msg = QMessageBox()
    msg.setText(msg_text)
    msg.setStyleSheet(Settings.POPUP_STYLESHEET)

    if type == "error":
        wdw_title = "Error" if title is None else title
        msg.setIcon(QMessageBox.Critical)
    elif type == "info":
        wdw_title = "!" if title is None else title
        msg.setIcon(QMessageBox.Information)
    elif type == "question":
        wdw_title = "Confirmation" if title is None else title
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setIcon(QMessageBox.Question)

    msg.setWindowTitle(wdw_title)
    response = msg.exec()
    return response


@contextmanager
def wait_cursor():
    try:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        yield
    finally:
        QApplication.restoreOverrideCursor()


def plot_points(ui, explorer, orn=False, downsampling=False):
    time_scale = get_timeScale(ui)
    sr = get_samplingRate(explorer)

    if not orn:
        if downsampling:
            points = (time_scale * sr) / (sr / Settings.EXG_VIS_SRATE)
        else:
            points = (time_scale * sr)
    else:
        points = time_scale * Settings.ORN_SRATE

    return int(points)


def get_timeScale(ui):
    t_str = ui.value_timeScale.currentText()
    t = Settings.TIME_RANGE_MENU[t_str]
    return t


def get_samplingRate(explorer):
    stream_processor = explorer.stream_processor
    sr = stream_processor.device_info['sampling_rate']
    return sr
