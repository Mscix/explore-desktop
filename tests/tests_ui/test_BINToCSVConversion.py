import pytest
import PySide6
from time import sleep
from pytestqt.qtbot import QtBot
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
import exploredesktop.main_window as mw
import unittest
from test_Window import connect_device
import os
from exploredesktop.modules.dialogs import ConvertBinDialog
from PySide6.QtWidgets import QApplication


class TestFile:
    """
    def test_convert_file(self, qtbot):
        window = connect_device(qtbot)
        window.show()

        # TODO: with mouse clicks has proven to be non trivial...
        # menubar = window.ui.menuBar
        # file_menu = window.ui.menuFile

        # action_convert =
        # qtbot.addWidget(menubar)
        # file_rect = menubar.actionGeometry(file_menu.menuAction())
        # actionConvert = window.ui.actionConvert

        # qtbot.wait(3000)
        # qtbot.mouseMove(menubar, action_rect.center())
        # qtbot.mouseClick(menubar, Qt.LeftButton, pos=file_rect.center())
        # qtbot.mouseClick(file_menu, Qt.LeftButton, pos=)
        # qtbot.wait(3000)

        # File path to the input Bin file:
        standard_path = "C:/Users/Mentalab/Desktop/explore-desktop/tests/tests_ui/test_files/"
        file_name = "DATA000_8_channel.BIN"
        input_path = os.path.abspath(standard_path + file_name)
        # File path to where the result will be written:
        result_path = "C:/Users/Mentalab/Desktop/explore-desktop/tests/tests_ui/test_files"
        output_path = os.path.abspath(result_path)

        qtbot.wait(1000)

        def handle_dialog():
            # Get an instance of the currently open window
            dialog = QApplication.activeWindow()
            input_field = dialog.ui.input_filepath
            output_field = dialog.ui.input_dest_folder
            qtbot.addWidget(input_field)
            qtbot.keyClicks(input_field, input_path)
            qtbot.addWidget(output_field)
            qtbot.keyClicks(output_field, output_path)
            dialog.accept()

        def pop_up():
            dialog = QApplication.activeWindow()
            dialog.accept()

        QTimer.singleShot(100, handle_dialog)
        # Answers the conversion confirmation pop up
        QTimer.singleShot(500, pop_up)

        # Easy way:
        # -> ConvertBinDialog().exec()
        window.ui.actionConvert.trigger()

        # Checks for CSV files:
        exg_file = os.path.abspath(standard_path + "DATA000_8_channel_ExG.csv")
        marker_file = os.path.abspath(standard_path + "DATA000_8_channel_Marker.csv")
        meta_file = os.path.abspath(standard_path + "DATA000_8_channel_Meta.csv")
        orn_file = os.path.abspath(standard_path + "DATA000_8_channel_ORN.csv")

        assert os.path.exists(exg_file)
        assert os.path.exists(marker_file)
        assert os.path.exists(meta_file)
        assert os.path.exists(orn_file)

        try:
            os.remove(exg_file)
            os.remove(marker_file)
            os.remove(meta_file)
            os.remove(orn_file)
        except FileExistsError:
            raise FileExistsError('Error in file conversion')





        # TODO: mark the unreliable tests expected to fail

    """
    def test_invalid_path(self, qtbot):
        window = connect_device(qtbot)
        window.show()

        input_path = 'This is a wrong path'
        output_path = 'This is a wrong path also'

        try:
            def handle_dialog():
                # Get an instance of the currently open window
                dialog = QApplication.activeWindow()
                input_field = dialog.ui.input_filepath
                output_field = dialog.ui.input_dest_folder
                qtbot.addWidget(input_field)
                qtbot.keyClicks(input_field, input_path)
                qtbot.addWidget(output_field)
                qtbot.keyClicks(output_field, output_path)
                dialog.accept()

            def handle_pop_up():
                dialog = QApplication.activeWindow()
                dialog.accept()

            QTimer.singleShot(100, handle_dialog)
            # Answers the conversion alert pop up
            QTimer.singleShot(500, handle_pop_up)

            # Easy way:
            # -> ConvertBinDialog().exec()
            window.ui.actionConvert.trigger()

        except Exception as e:
            if not isinstance(e, AssertionError):
                pass




