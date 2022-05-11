"""
Tools/utils for GUI

Functions:
    get_widget_by_object_name
    display_message
    wait_cursor
"""
import logging
from contextlib import contextmanager

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox
)

from exploredesktop.modules.app_settings import FilterTypes, Settings


logger = logging.getLogger("explorepy." + __name__)


def get_widget_by_obj_name(name: str):
    """Get widget object by its name

    Args:
        name (str): widget name

    Returns:
        Union(None, PySide6.QtWidget): widget object corresponding to the input name.
                                        If no matching widget is found, returns None
    """
    widgets = QApplication.instance().allWidgets()
    for wdgt in widgets:
        if str(wdgt.objectName()) == name:
            return wdgt
    logger.warning("Could not find %s", name)
    return None


def display_msg(msg_text: str, title: str = None, popup_type: str = "error"):
    """Display pop up with given message.

    Args:
        msg_text (str): message to display
        title (str, optional): title of the pop-up. Defaults to None.
        type (str, optional): pop-up type. Options are "error", "info", "question" Defaults to "error".

    Returns:
        PySide6.QtWidgets.QMessageBox.StandardButton: button clicked
    """
    msg = QMessageBox()
    msg.setText(msg_text)
    # msg.setStyleSheet(Stylesheets.POPUP_STYLESHEET)

    if popup_type == "error":
        wdw_title = "Error" if title is None else title
        msg.setIcon(QMessageBox.Critical)
    elif popup_type == "info":
        wdw_title = "Information" if title is None else title
        msg.setIcon(QMessageBox.Information)
    elif popup_type == "question":
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


def identify_filter(filter_values: tuple):
    if filter_values[0] is not None and filter_values[1] is None:
        filter_type = FilterTypes.HIGHPASS
    elif filter_values[0] is None and filter_values[1] is not None:
        filter_type = FilterTypes.LOWPASS
    elif filter_values[0] is not None and filter_values[1] is not None:
        filter_type = FilterTypes.BANDPASS
    else:
        logger.warning(f"Filter with values {filter_values} not identified")
        filter_type = None
    return filter_type


def verify_filters(filter_values: tuple, sampling_rate):
    lc_valid = True
    hc_valid = True
    bp_valid = True
    lc_freq = float(filter_values[0]) if filter_values[0] != "" else None
    hc_freq = float(filter_values[1]) if filter_values[1] != "" else None

    nyq_freq = sampling_rate / 2.
    min_lc_freq = Settings.MIN_LC_WEIGHT * nyq_freq

    filter_type = identify_filter((lc_freq, hc_freq))
    print(filter_type)
    if (filter_type == FilterTypes.HIGHPASS) and (lc_freq <= min_lc_freq):
        lc_valid = False

    elif (filter_type == FilterTypes.LOWPASS) and (hc_freq >= nyq_freq):
        hc_valid = False

    elif (filter_type == FilterTypes.BANDPASS):
        print(f"{lc_freq=}")
        print(f"{hc_freq=}")
        if lc_freq >= hc_freq:
            bp_valid = False
        elif hc_freq >= nyq_freq:
            hc_valid = False
        elif lc_freq <= min_lc_freq:
            lc_valid = False

    return {'lc_freq': lc_valid, 'hc_freq': hc_valid, 'bp_valid': bp_valid}
