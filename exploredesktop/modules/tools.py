"""
Tools/utils for GUI

Functions:
    get_widget_by_object_name
    display_message
"""
import logging

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from contextlib import contextmanager


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
