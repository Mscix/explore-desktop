from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from test_window import connect_device


def test_reset_settings(qtbot):
    window = connect_device(qtbot)
    # By default, should redirect to Settings Frame view, but just to be sure:
    settings_btn = window.ui.btn_settings
    qtbot.addWidget(settings_btn)
    qtbot.mouseClick(settings_btn, Qt.LeftButton)

    reset_btn = window.settings_frame.ui.btn_reset_settings
    qtbot.addWidget(reset_btn)

    # Handle dialog about the Explore device disconnection
    def handle_dialog():
        # Get an instance of the currently open window
        messagebox = QApplication.activeWindow()
        yes_button = messagebox.button(QMessageBox.Yes)
        qtbot.mouseClick(yes_button, Qt.LeftButton)

    QTimer.singleShot(100, handle_dialog)
    qtbot.mouseClick(reset_btn, Qt.LeftButton, delay=1)

    # Check that back on the Blue Tooth page, and device disconnected
    qtbot.wait(1000)
    assert not window.explorer.is_connected
    print(window.ui.stackedWidget.currentWidget().children())
    assert window.ui.stackedWidget.currentWidget().objectName() == "page_bt"


def test_apply_settings(qtbot):
    window = connect_device(qtbot)
    # window.show()
    table = window.settings_frame.ui.table_settings
    model = table.model()
    # index for the second channel tick box
    cell_2 = model.index(1, 1)
    rect = table.visualRect(cell_2).center()
    qtbot.mouseClick(table.viewport(), Qt.LeftButton, pos=rect)

    # Change sampling rate
    sampling_rate = window.settings_frame.ui.value_sampling_rate
    qtbot.addWidget(sampling_rate)
    qtbot.mouseClick(sampling_rate, Qt.LeftButton)

    qtbot.keyClick(sampling_rate, Qt.Key_Down, delay=3)
    qtbot.keyClick(sampling_rate, Qt.Key_Enter, delay=3)

    # apply settings
    btn_apply = window.settings_frame.ui.btn_apply_settings
    qtbot.addWidget(btn_apply)
    qtbot.wait(1000)

    def handle_dialog():
        # Get an instance of the currently open window
        messagebox = QApplication.activeWindow()
        ok_button = messagebox.button(QMessageBox.Ok)
        qtbot.mouseClick(ok_button, Qt.LeftButton)

    QTimer.singleShot(100, handle_dialog)
    qtbot.mouseClick(btn_apply, Qt.LeftButton, delay=1)


def test_format_memory_no(qtbot):
    window = connect_device(qtbot)
    format_mem = window.settings_frame.ui.btn_format_memory
    qtbot.addWidget(format_mem)

    def handle_dialog():
        # Get an instance of the currently open window
        messagebox = QApplication.activeWindow()
        no_button = messagebox.button(QMessageBox.No)
        qtbot.mouseClick(no_button, Qt.LeftButton)

    QTimer.singleShot(100, handle_dialog)
    qtbot.mouseClick(format_mem, Qt.LeftButton, delay=1)