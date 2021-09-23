# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys


from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog
from PySide6.QtCore import QTimer, Qt, Signal, QTimer
from PySide6.QtGui import QIcon
import explorepy as xpy
from pyqtgraph.Qt import App
from pyqtgraph.functions import disconnect
from modules import *
import pyqtgraph as pg
from datetime import datetime
from modules.dialogs import RecordingDialog, PlotDialog


# pyside6-uic ui_main_window.ui > ui_main_window.py
# pyside6-uic dialog_plot_settings.ui > dialog_plot_settings.py
# pyside6-uic dialog_recording_settings.ui > dialog_recording_settings.py

VERSION_APP = 'v0.14'


class MainWindow(QMainWindow):
    signal_exg = Signal(object)
    signal_fft = Signal(object)
    signal_orn = Signal(object)
    signal_imp = Signal(object)
    signal_marker= Signal(object)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("images/MentalabLogo.png"))

        self.explorer = xpy.Explore()
        self.is_connected = self.explorer.is_connected
        self.is_streaming = False
        self.battery_percent_list = []
        self.chan_dict = {}
        self.mode = "home"
        self.is_recording = False
        self.is_imp_measuring = False
        self.file_names = None
        self.is_started = False

        self.plotting_filters = None

        self.t_exg_plot = []
        self.exg_plot = {}
        self.orn_plot = {k:[] for k in Settings.ORN_LIST}
        self.t_orn_plot = []
        self.mrk_plot = {"t":[], "code":[], "line":[]}

        self._vis_time_offset = None
        self._baseline_corrector = {"MA_length": 1.5 * Settings.EXG_VIS_SRATE,
                                    "baseline": 0}
        self.y_unit = Settings.DEFAULT_SCALE
        self.y_string = "1 mV"

        # Hide os bar
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Add app version to footer
        self.ui.ft_label_version.setText(VERSION_APP)

        # Hide frame of device settings when launcinng app
        self.ui.frame_device.hide()
        self.ui.line_2.hide()

        # Set UI definitions (close, restore, etc)
        UIFunctions.ui_definitions(self)

        # Initialize values
        AppFunctions.init_dropdowns(self)

        # List devices when starting the app
        test = True
        if test:
            # pass
            self.explorer.connect(device_name="Explore_CA18")
            # self.explorer.connect(device_name="Explore_CA0E")
            AppFunctions.info_device(self)
            AppFunctions.update_frame_dev_settings(self)
            self.is_connected = True

            stream_processor = self.explorer.stream_processor
            n_chan = stream_processor.device_info['adc_mask']
            self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
            self.exg_plot = {ch:[] for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
        else:
            AppFunctions.scan_devices(self)

        # Slidable left panel
        self.ui.btn_left_menu_toggle.clicked.connect(lambda: UIFunctions.slideLeftMenu(self))

        # Stacked pages - default open home
        # self.ui.stackedWidget.setCurrentWidget(self.ui.page_settings_testing)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)

        # Stacked pages - navigation
        for w in self.ui.left_side_menu.findChildren(QPushButton):
            w.clicked.connect(self.leftMenuButtonClicked)

        # SETTINNGS PAGE BUTTONS
        self.ui.btn_connect.clicked.connect(lambda: AppFunctions.connect2device(self))
        # self.ui.input_device_name.returnPressed.connect(lambda: AppFunctions.connect2device(self))
        self.ui.btn_scan.clicked.connect(lambda: AppFunctions.scan_devices(self))
        self.ui.btn_import_data.clicked.connect(lambda: self.import_recorded_data())
        self.ui.btn_format_memory.clicked.connect(lambda: AppFunctions.format_memory(self))
        self.ui.btn_reset_settings.clicked.connect(lambda: AppFunctions.reset_settings(self))
        self.ui.btn_apply_settings.clicked.connect(lambda: AppFunctions.change_settings(self))
        self.ui.btn_calibrate.clicked.connect(lambda: AppFunctions.calibrate_orn(self))

        # IMPEDANCE PAGE
        self.ui.btn_imp_meas.clicked.connect(lambda: AppFunctions.emit_imp(self))
        self.signal_imp.connect(lambda data: AppFunctions._update_impedance(self, data))
        self.ui.label_6.linkActivated.connect(lambda: AppFunctions.disable_imp(self))

        # PLOTTING PAGE
        self.ui.btn_record.clicked.connect(self.start_record)    
        self.ui.btn_plot_filters.clicked.connect(lambda: self.plot_filters())

        self.ui.btn_marker.setEnabled(False)
        self.ui.value_event_code.textChanged[str].connect(lambda: self.ui.btn_marker.setEnabled(
                (self.ui.value_event_code.text() != "") 
                or 
                ((self.ui.value_event_code.text().isnumeric()) and (8 <= int(self.ui.value_event_code.text()) <= 65535))
            )
        )
        # self.ui.value_event_code.setEnabled(self.ui.btn_record.text()=="Stop")
        self.ui.btn_marker.clicked.connect(lambda: AppFunctions.set_marker(self))

        self.ui.value_yAxis.currentTextChanged.connect(lambda: AppFunctions._change_scale(self))

        self.signal_exg.connect(lambda data: AppFunctions.plot_exg(self, data))
        self.signal_fft.connect(lambda data: AppFunctions.plot_fft(self, data))
        self.signal_orn.connect(lambda data: AppFunctions.plot_orn(self, data))
        self.signal_marker.connect(lambda data: AppFunctions.plot_orn(self, data))
        
        if self.file_names is None:
            self.ui.btn_stream.clicked.connect(lambda: AppFunctions.emit_signals(self))
        else:
            self.ui.btn_stream.clicked.connect(lambda: self.start_recorded_plots())

        # INTEGRATION PAGE
        self.ui.btn_push_lsl.clicked.connect(lambda: AppFunctions.push_lsl(self))

        # /////////////////////////////// START TESTING ///////////////////////
        '''self.signal_exg.connect(lambda data: AppFunctions.plot_exg(self, data))
        # self.ui.pushButton_2.clicked.connect(lambda: AppFunctions.emit_exg(self))
        

        self.signal_fft.connect(lambda data: AppFunctions.plot_fft(self, data))
        # self.ui.pushButton_2.clicked.connect(lambda: AppFunctions.emit_fft(self))

        self.signal_orn.connect(lambda data: AppFunctions.plot_orn(self, data))
        self.ui.pushButton_2.clicked.connect(lambda: AppFunctions.emit_orn(self))

        from datetime import datetime
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
        self.ui.pushButton_3.clicked.connect(lambda: self.df.to_csv(f"output_{dt_string}.csv"))
        # self.ui.pushButton_3.clicked.connect(lambda: self.ui.graphicsView.clear())'''

        # /////////////////////////////// END TESTING ///////////////////////

    def import_recorded_data(self):
        '''
        Open file dialog to select file to import
        '''
        file_types = "CSV files(*.csv);;EDF files (*.edf);;BIN files (*.BIN)"
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        self.file_names, _ = dialog.getOpenFileNames(
            self,
            "Select Files to import",
            "",
            filter=file_types
            )

        # self.myTextBox.setText(fileName)
        print(self.file_names)

    def plot_filters(self):
        '''
        Open plot filter dialog and apply filters
        '''

        dialog = PlotDialog()
        self.plotting_filters = dialog.exec()


    def start_timer_recorder(self):
        '''
        Start timer to display recording time
        '''
        print("clicked")
        self.start_time = datetime.now()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: self.displayTime())
        self.timer.start()

    def displayTime(self):
        '''
        Display recording time in label
        '''
        time = datetime.now() - self.start_time
        strtime = str(time).split(".")[0]
        self.ui.label_recording_time.setText(strtime)

    def start_record(self):
        '''
        Start/Stop signal recording
        '''
        if self.is_recording is False:
            dialog = RecordingDialog()
            data = dialog.exec()
            print(data)

            file_name = data["file_path"]
            file_type = data["file_type"]
            duration = data["duration"] if data["duration"] != 0 else None

            self.ui.btn_record.setIcon(QIcon(
                u":icons/icons/icon_maximize.png"))
            self.ui.btn_record.setText("Stop")
            QApplication.processEvents()

            self.explorer.record_data(
                file_name=file_name, 
                file_type=file_type, 
                duration=duration)
            self.is_recording = True
            self.start_timer_recorder()

        else:
            self.explorer.stop_recording()
            self.ui.btn_record.setIcon(QIcon(
                    u":icons/icons/cil-circle.png"))
            self.ui.btn_record.setText("Record")
            QApplication.processEvents()
            self.is_recording = False
            self.timer.stop()

    def start_recorded_plots(self):
        '''
        Start plotting recorded data
        '''

        '''if self.file_names is None:
            QMessageBox.critical(self, "Error", "Import data first")'''

        if self.ui.cb_swipping_rec.isChecked():
            time_scale = self.ui.value_timeScale_rec.currentText()
        else:
            time_scale = None


        if self.is_started is False:
            self.is_started = True
            exg_wdgt = self.ui.plot_exg_rec
            orn_wdgt = self.ui.plot_orn_rec
            fft_wdgt = self.ui.plot_fft_rec
            if any("exg" in s.lower() for s in self.file_names):
                self.plot_exg_recorded = Plots("exg", self.file_names, exg_wdgt, time_scale)
                plot_fft = Plots("fft", self.file_names, fft_wdgt, time_scale)


            if any("exg" in s.lower() for s in self.file_names):
                self.plot_orn_recorded = Plots("orn", self.file_names, orn_wdgt, time_scale)

        if self.is_streaming is False and self.ui.cb_swipping.isChecked():
            self.ui.btn_stream.setText("Stop Data Stream")
            self.ui.btn_stream.setStyleSheet(Settings.STOP_BUTTON_STYLESHEET)
            self.is_streaming = True
            QApplication.processEvents()

            
            self.timer_exg = QTimer()
            self.timer_exg.setInterval(1)
            self.timer_exg.timeout.connect(lambda: self.plot_exg_recorded.update_plot_exg())
            self.timer_exg.start()

            
            self.timer_orn = QTimer()
            self.timer_orn.setInterval(50)
            self.timer_orn.timeout.connect(lambda: self.plot_orn_recorded.update_plot_orn())
            self.timer_orn.start()


        else:
            self.ui.btn_stream.setText("Start Data Stream")
            self.ui.btn_stream.setStyleSheet(Settings.START_BUTTON_STYLESHEET)
            self.is_streaming = False
            self.timer_exg.stop()
            self.timer_orn.stop()

    def changePage(self, btn_name):
        """
        Change the active page when the object is clicked

        Args:
            btn_name
        """
        # btn = self.sender()
        # btn_name = btn.objectName()

        if btn_name == "btn_home":
            self.mode = "home"
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
            # if self.is_imp_measuring:
            #     self.explorer.stream_processor.disable_imp()

        elif btn_name == "btn_settings":
            self.mode = "settings"
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)
            # if self.is_imp_measuring:
            #     self.explorer.stream_processor.disable_imp()

        elif btn_name == "btn_plots":
            self.mode = "exg"
            # self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)

            if self.file_names is None:
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)
            else:
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsRecorded)

            # self.ui.stackedWidget.setCurrentWidget(self.ui.page_plots)
            # self.ui.stackedWidget.setCurrentWidget(self.ui.page_settings_testing)
            # if self.is_imp_measuring:
            #     self.explorer.stream_processor.disable_imp()

            if self.ui.plot_exg.getItem(0,0) is None:
                AppFunctions.init_plot_orn(self)
                AppFunctions.init_plot_exg(self)
            
            if self.plotting_filters is None:
                self.plot_filters()


        elif btn_name == "btn_impedance":
            self.mode = "imp"
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_impedance)
            AppFunctions._reset_impedance(self)

        elif btn_name == "btn_integration":
            self.mode = "integration"
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_integration)
            # if self.is_imp_measuring:
            #     self.explorer.stream_processor.disable_imp()


    def leftMenuButtonClicked(self):
        """
        Change style of the button clicked and move to the selected page
        """

        btn = self.sender()
        btn_name = btn.objectName()

        if btn_name != "btn_left_menu_toggle":
            #Reset style for other buttons
            for w in self.ui.left_side_menu.findChildren(QPushButton):
                if w.objectName() != btn_name:
                    defaultStyle = w.styleSheet().replace(Settings.BTN_LEFT_MENU_SELECTED_STYLESHEET, "")
                    # Apply default style
                    w.setStyleSheet(defaultStyle)

            # Apply new style
            newStyle = btn.styleSheet() + (Settings.BTN_LEFT_MENU_SELECTED_STYLESHEET)
            btn.setStyleSheet(newStyle)

            # Navigate to active page
            self.changePage(btn_name)

    def mousePressEvent(self, event):
        '''
        Get mouse current position to move the window

        Args: mouse press event
        '''
        self.clickPosition = event.globalPos() 

    '''def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)'''





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
