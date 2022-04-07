from multiprocessing.connection import wait
import os
import re
import sys
import traceback
from PySide6.QtCore import QRunnable, Signal, QObject, Slot
import explorepy
import explorepy._exceptions as xpy_ex
import logging

from exploredesktop.modules.app_settings import Messages, Stylesheets
from exploredesktop.modules.base_model import BaseModel
from exploredesktop.modules.tools import display_msg, wait_cursor

logger = logging.getLogger("explorepy." + __name__)


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread"""
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)


class Worker(QRunnable):
    """Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    Args:
        callback: The function callback to run on this worker thread. Supplied args and
                        kwargs will be passed through to the runner.
        args: Arguments to pass to the callback function
        kwargs: Keywords to pass to the callback function
    """

    def __init__(self, funct, *args, **kwargs) -> None:
        super().__init__()

        self.funct = funct
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    # @Slot()
    def run(self):
        """Initialise the runner function with passed args, kwargs"""
        # TODO: do we want the wait cursor if we are in a thread
        with wait_cursor():
            try:
                result = self.funct(*self.args, **self.kwargs)
            # pylint: disable=bare-except
            except:
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            else:
                self.signals.result.emit(result)  # Return the result of the processing
            finally:
                self.signals.finished.emit()  # Done


class BTFrameView():
    """_summary_
    """
    def __init__(self, ui, model, threadpool) -> None:
        self.ui = ui
        self.model = model
        self.threadpool = threadpool

        self.signals = model.get_signals()
        self.explorer = model.get_explorer()

    #########################
    # Get device name functions
    #########################
    def get_device_from_le(self) -> str:
        """
        Get device name from line edit widget.
        If the input string does not contain the word Explore it will added

        Returns:
            str: full name of the device (Explore_XXXX). Empty if format is not correct
        """

        input_name = self.ui.dev_name_input.text()

        if not input_name.startswith("Explore_") and len(input_name) == 4:
            device_name = "Explore_" + input_name
        elif input_name.startswith("Explore_"):
            device_name = input_name
        else:
            device_name = ""

        if len(device_name) != 12:
            device_name = ""

        return device_name

    #########################
    # Slots
    #########################
    @Slot()
    def connect_clicked(self):
        """_summary_
        """
        device_name = self.get_device_from_le()
        if device_name == "":
            display_msg(Messages.INVALID_EXPLORE_NAME)
            return
        # Change footer and button
        self._connect_stylesheet(device_name=device_name)

        worker = Worker(self.explorer.connect, device_name=device_name)
        worker.signals.result.connect(lambda result: print("connected ", result, "\n\n"))
        worker.signals.error.connect(self.connection_error_gui)
        worker.signals.finished.connect(lambda: print("thread done!!"))
        self.threadpool.start(worker)

        self._connect_stylesheet(reset=True)

    @Slot()
    def connection_error_gui(self, err_tuple) -> None:
        """
        Reset footer and buttons when scan/connect functions throw an error.
        Display pop-up with the error

        Args:
            msg (str): error message to display
            scan (bool, optional): whether is scanning or connecting. Defaults to False.
        """
        self._connect_stylesheet(reset=True)
        
        err_type = err_tuple[0]
        err_msg = err_tuple[1]
        
        if err_type == xpy_ex.DeviceNotFoundError:
            msg = err_msg
            logger.warning("Device not found.")

        elif err_type == TypeError or err_type == UnboundLocalError:
            msg = Messages.INVALID_EXPLORE_NAME
            logger.warning("Invalid Explore name")

        elif err_type == ValueError or err_type == SystemError:
            msg = Messages.NO_BT_CONNECTION
            logger.warning("No Bluetooth connection available.")

        else:
            msg = err_msg
            logger.debug("Got an exception while connecting to the device: %s of type: %s", err_msg, err_type)

        display_msg(msg)

    def _connect_stylesheet(self, device_name: str = None, reset: bool = False) -> None:
        """Change footer and connect button to stylesheet
        Args:
            device_name (str, optional): Name of the device to connect. Defaults to None.
            reset (bool, optional): Whether to reset to default values. Defaults to False.
        """
        lbl_footer = "Not connected" if reset else f"Connecting to {device_name}..."
        btn_txt = "Connect" if reset else "Connecting"
        btn_stylesheet = "" if reset else Stylesheets.DISABLED_BTN_STYLESHEET

        # Set footer
        self.ui.ft_label_device_3.setText(lbl_footer)
        self.ui.ft_label_device_3.adjustSize()
        self.ui.ft_label_device_3.repaint()

        # Set button
        self.ui.btn_connect.setText(btn_txt)
        self.ui.btn_connect.setStyleSheet(btn_stylesheet)

        # If platform is windows, add instructions
        if os.name == "nt":
            self.ui.lbl_bt_instructions.setText(Messages.WINDOWS_PAIR_INSTRUCTIONS)
            self.ui.lbl_bt_instructions.setHidden(reset)


if __name__ == "__main__":
    from PySide6 import QtWidgets
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtCore import QThreadPool, Slot
    import sys
    from exploredesktop.modules import Ui_MainWindow


    class MainWindow(QMainWindow):
        """_summary_

        Args:
            QtWidgets (_type_): _description_
        """
        def __init__(self):
            super(MainWindow, self).__init__()
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)

            self.threadpool = QThreadPool()
            self.bt_frame = BTFrameView(self.ui, BaseModel(), self.threadpool)

            self.ui.btn_connect.clicked.connect(self.bt_frame.connect_clicked)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()