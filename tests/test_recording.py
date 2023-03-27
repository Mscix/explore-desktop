import pytest
import PySide6
from time import sleep
from pytestqt.qtbot import QtBot
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtCore import Qt, QCoreApplication, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QMessageBox
import unittest
from unittest.mock import Mock, MagicMock, patch
from test_main import connect_device
from exploredesktop.modules.recording_module import RecordFunctions
from exploredesktop.modules.dialogs import RecordingDialog
from exploredesktop.modules.app_settings import Messages
import os


def navigate_to_recording_view(qtbot, app):
    record_btn = app.ui.btn_plots
    qtbot.addWidget(record_btn)
    qtbot.mouseClick(record_btn, Qt.LeftButton)




class TestRecording:

    def test_recording(self, qtbot):
        app = connect_device(qtbot)
        app.show()
        navigate_to_recording_view(qtbot, app)
        record_functions = app.recording
        record_btn = record_functions.ui.btn_record
        # TODO bypass the dialog just call the function the dialog would call with the same input
        # QTbot can not just press enter have to figure out how to Bypass dialog with mock

        # FiltersDialog is the first window tha pops up when entering recording ...
        # How to bypass???
        # used in the filters module...
        # When is the pop up started???? here: pop_filters is called inside the mainwindow in change page so when the
        # the page is changed to recording then it automatically pops up...

        # if self.filters.current_filters is None:
        #  filt = self.filters.popup_filters()
        #  somehow have to set filt to True though otherwise will go automatically back to settings
        # so mock pop?
        filters = app.filters
        filter_pop = filters.ui.btn_plot_filters

        qtbot.addWidget(filter_pop)
        qtbot.mouseClick(filter_pop, Qt.LeftButton)

        recording_dialog = RecordingDialog()
        record_functions_mock = Mock(spec=record_functions)
        default_file_name = record_functions_mock._set_filename_placeholder(recording_dialog)
        default_dir = record_functions_mock._set_dir_placeholder(recording_dialog)

        path = 'C:Users\"Mentalab\"Desktop\"test_data'
        filename = 'test_file'
        data = {
            "file_name": filename,
            "file_path": os.path.join(path, filename),
            "duration": 10,
            "file_type": "csv"
        }
        data_empty = {
            "file_name": '',
            "file_path": '',
            "duration": 10,
            "file_type": "csv"
        }

        # oder lasse ich es einfahc leer?
        # C:\Users\Mentalab\Desktop\test_data
        record_functions_mock.get_dialog_data.return_value = default_file_name, default_dir, data
        app.recording = record_functions_mock
        qtbot.wait(2000)
        qtbot.addWidget(record_btn)
        qtbot.mouseClick(record_btn, Qt.LeftButton)
        qtbot.wait(2000)

        # qtbot should at least wait as long as the recording goes and then test the file output




    #self.orn_plot = ORNPlot(self.ui)
    #self.orn_plot.setup_ui_connections()
    #self.exg_plot = ExGPlot(self.ui, self.filters)
    #self.exg_plot.setup_ui_connections()
    #self.fft_plot = FFTPlot(self.ui)
    #self.mkr_plot = MarkerPlot(self.ui)
    #self.mkr_plot.setup_ui_connections()