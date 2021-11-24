import sys
from datetime import datetime
import numpy as np

from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QMainWindow, QMessageBox, QPushButton, QFileDialog, QSizeGrip
from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, Signal, QTimer, Slot
from PySide6.QtGui import QColor, QIcon, QFontDatabase, QIntValidator
import explorepy as xpy

# from exploregui.modules import *

from exploregui.modules.dialogs import RecordingDialog  # , PlotDialog
from exploregui.modules.stylesheets.stylesheet_centralwidget import CENTRAL_STYLESHEET, MAINBODY_STYLESHEET
# from exploregui.modules import Ui_MainWindow, Settings, AppFunctions, Plots
from exploregui.modules import Settings, Ui_MainWindow
from exploregui.modules import AppFunctions, BTFunctions, ConfigFunctions, VisualizationFunctions
from exploregui.modules import IMPFunctions, LSLFunctions, RecordFunctions


# pyside6-uic ui_main_window.ui > ui_main_window.py
# pyside6-uic dialog_plot_settings.ui > dialog_plot_settings.py
# pyside6-uic dialog_recording_settings.ui > dialog_recording_settings.py

VERSION_APP = 'v0.19'
WINDOW_SIZE = False


class MainWindow(QMainWindow):
    signal_exg = Signal(object)
    signal_orn = Signal(object)
    signal_imp = Signal(object)
    signal_mkr = Signal(object)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("exploregui/images/MentalabLogo.png"))

        self.explorer = xpy.Explore()
        self.funct = AppFunctions(self.ui, self.explorer)
        self.LSL_funct = LSLFunctions(self.ui, self.explorer)
        self.BT_funct = BTFunctions(self.ui, self.explorer)
        self.config_funct = ConfigFunctions(self.ui, self.explorer)
        self.imp_funct = IMPFunctions(self.ui, self.explorer, self.signal_imp)
        self.vis_funct = VisualizationFunctions(
            self.ui, self.explorer,
            {"exg": self.signal_exg, "mkr": self.signal_mkr, "orn": self.signal_orn}
            )
        self.record_funct = RecordFunctions(self.ui, self.explorer)

        # Defined in connect_clicked
        # self.is_connected = self.explorer.is_connected
        # self.chan_dict = {}
        # self.n_chan = 8
        # self.chan_list = Settings.CHAN_LIST[:self.n_chan]

        # self.t_exg_plot = np.array([np.NaN]*2500)
        # self.exg_plot = {}

        #########

        self.is_streaming = False
        # self.battery_percent_list = []
        self.is_recording = False
        # self.is_imp_measuring = False
        self.file_names = None
        self.is_started = False

        # self.is_pushing = False
        
        # self.ui.duration_push_lsl.hide()
        # self.ui.frame_6.hide()
        self.ui.frame_impedance_widgets_16.hide()
        self.ui.imp_meas_info.setHidden(True)
        self.ui.label_3.setHidden(self.file_names is None)
        self.ui.label_7.setHidden(self.file_names is None)

        # self.plotting_filters = None
        # self.plotting_filters = {'offset': True, 'notch': 50, 'lowpass': 0.5, 'highpass': 30.0}

        # self.downsampling = False
        # self.exg_pointer = 0
        
        # self.mrk_plot = {"t": [], "code": [], "line": []}
        # self.mrk_replot = {"t": [], "code": [], "line": []}

        # self.orn_plot = {k: np.array([np.NaN]*200) for k in Settings.ORN_LIST}
        # self.t_orn_plot = np.array([np.NaN]*200)
        # self.orn_pointer = 0

        # self._vis_time_offset = None
        # self._baseline_corrector = {"MA_length": 1.5 * Settings.EXG_VIS_SRATE,
        #                             "baseline": 0}

        # self.y_unit = Settings.DEFAULT_SCALE
        # self.y_string = "1 mV"

        # self.line = None

        # self.lines_orn = [None, None, None]
        # self.last_t = 0
        # self.last_t_orn = 0

        # self.rr_estimator = None
        # self.r_peak = {"t": [], "r_peak": [], "points": []}

        # self._lambda_exg = lambda data: self.vis_funct.plot_exg(data)
        # self._lambda_orn = lambda data: AppFunctions.plot_orn(data)
        # self._lambda_marker = lambda data: AppFunctions.plot_marker(data)

        # Hide os bar
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Add app version to footer
        self.ui.ft_label_version.setText(VERSION_APP)

        # Hide frame of device settings when launching app
        self.ui.frame_device.hide()
        self.ui.line_2.hide()

        # Set UI definitions (close, restore, etc)
        self.ui_definitions()

        # Initialize values
        self.init_dropdowns()

        # Apply stylesheets
        self.ui.centralwidget.setStyleSheet(CENTRAL_STYLESHEET)
        self.ui.main_body.setStyleSheet(MAINBODY_STYLESHEET)
        self.ui.line.setStyleSheet(
            """background-color: #FFFFFF;
            border:none;""")
        QFontDatabase.addApplicationFont("./modules/stylesheets/DMSans-Regular.ttf")


        # List devices when starting the app
        # test = False
        # if test:
        #     # pass
        #     self.explorer.connect(device_name="Explore_CA18")
        #     # self.explorer.connect(device_name="Explore_CA4C")
        #     # self.explorer.connect(device_name="Explore_CA07")
        #     self.is_connected = True
        #     # self.n_chan = 4
        #     self.n_chan = len(self.explorer.stream_processor.device_info['adc_mask'])
        #     self.chan_list = Settings.CHAN_LIST[:self.n_chan]

        #     AppFunctions.info_device(self)
        #     AppFunctions.update_frame_dev_settings(self)
        #     stream_processor = self.explorer.stream_processor
        #     n_chan = stream_processor.device_info['adc_mask']
        #     n_chan = [i for i in reversed(n_chan)]
        #     self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
        #     # self.exg_plot = {ch:[] for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
        #     self.exg_plot = {ch: np.array([np.NaN]*2500) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
        #     # AppFunctions.init_plot_exg(self)
        #     # AppFunctions.init_plot_orn(self)
        #     # AppFunctions.init_plot_fft(self)
        #     AppFunctions.init_plots(self)
        #     AppFunctions.init_imp(self)


        '''else:
            AppFunctions.scan_devices(self)'''

        # Slidable left panel
        self.ui.btn_left_menu_toggle.clicked.connect(lambda: self.slideLeftMenu())

        # Stacked pages - default open home
        # self.ui.stackedWidget.setCurrentWidget(self.ui.page_settings_testing)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)
        # self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)
        # AppFunctions.emit_signals(self)

        # Stacked pages - navigation
        for w in self.ui.left_side_menu.findChildren(QPushButton):
            w.clicked.connect(self.leftMenuButtonClicked)

        # SETTINNGS PAGE BUTTONS
        self.ui.btn_connect.clicked.connect(lambda: self.connect_clicked())
        self.ui.dev_name_input.returnPressed.connect(lambda: self.connect_clicked())
        self.ui.btn_scan.clicked.connect(lambda: self.BT_funct.scan_devices())

        # self.ui.btn_import_data.clicked.connect(lambda: self.import_recorded_data())
        self.ui.btn_format_memory.clicked.connect(lambda: self.config_funct.format_memory())
        self.ui.btn_reset_settings.clicked.connect(lambda: self.config_funct.reset_settings())
        self.ui.btn_apply_settings.clicked.connect(lambda: self.settings_changed())
        self.ui.btn_calibrate.clicked.connect(lambda: self.config_funct.calibrate_orn())
        self.ui.n_chan.currentTextChanged.connect(lambda: self.n_chan_changed())

        # IMPEDANCE PAGE
        self.ui.imp_meas_info.setToolTip("Sum of impedances on REF and individual channels divided by 2")
        self.signal_imp.connect(self.imp_funct.update_impedance)
        self.ui.btn_imp_meas.clicked.connect(lambda: self.imp_meas_clicked())
        self.ui.label_6.setHidden(True)

        # PLOTTING PAGE
        self.ui.btn_record.clicked.connect(lambda: self.record_funct.on_record())
        self.ui.btn_plot_filters.clicked.connect(lambda: self.vis_funct.popup_filters())

        self.ui.btn_marker.setEnabled(False)
        self.ui.value_event_code.textChanged[str].connect(lambda: self.ui.btn_marker.setEnabled(
                (self.ui.value_event_code.text() != "")
                or
                ((self.ui.value_event_code.text().isnumeric()) and (8 <= int(self.ui.value_event_code.text())))
            )
        )
        # self.ui.value_event_code.setEnabled(self.ui.btn_record.text()=="Stop")
        self.ui.btn_marker.clicked.connect(lambda: self.vis_funct.set_marker())
        # self.ui.value_event_code.returnPressed.connect(lambda: AppFunctions.set_marker(self))

        self.ui.value_yAxis.currentTextChanged.connect(lambda: self.vis_funct.change_scale())
        self.ui.value_timeScale.currentTextChanged.connect(lambda: self.vis_funct.change_timescale())

        self.signal_exg.connect(self.vis_funct.plot_exg)
        self.signal_orn.connect(self.vis_funct.plot_orn)
        self.signal_mkr.connect(self.vis_funct.plot_mkr)

        self.ui.btn_stream.hide()
        # self.ui.btn_stream.clicked.connect(lambda: AppFunctions.emit_exg(self, stop=True))
        # self.ui.btn_stream.clicked.connect(lambda: self.update_fft())
        # self.ui.btn_stream.clicked.connect(lambda: self.update_heart_rate())

        # self.signal_exg.connect(lambda data: AppFunctions.plot_exg_moving(self, data))
        # self.signal_orn.connect(lambda data: AppFunctions.plot_orn_moving(self, data))
        # self.signal_mkr.connect(lambda data: AppFunctions.plot_marker_moving(self, data))

        self.ui.label_7.linkActivated.connect(
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsRecorded)
        )

        # Recorded data plotting page
        self.ui.label_3.linkActivated.connect(
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)
        )
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)

        self.ui.btn_stream_rec.clicked.connect(lambda: self.start_recorded_plots())

        # INTEGRATION PAGE
        self.ui.btn_push_lsl.clicked.connect(lambda: self.LSL_funct.push_lsl())

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
    @Slot()
    def connect_clicked(self):
        self.BT_funct.connect2device()
        self.vis_funct.init_plots()
        self.is_connected = self.BT_funct.get_is_connected()

        if self.is_connected:
            self.chan_dict = self.BT_funct.get_chan_dict()
            self.chan_list = self.BT_funct.get_chan_list()
            self.n_chan = len(self.chan_list)
            self.t_exg_plot, self.exg_plot = self.BT_funct.get_exg_plot_data()
        else:
            self.chan_dict = {}
            self.n_chan = 8
            self.chan_list = Settings.CHAN_LIST[:self.n_chan]
            self.t_exg_plot = np.array([np.NaN]*2500)
            self.exg_plot = {}

    @Slot()
    def n_chan_changed(self):
        self.BT_funct.set_n_chan()
        self.BT_funct.update_frame_dev_settings()

    @Slot()
    def settings_changed(self):
        self.config_funct.change_settings()
        self.t_exg_plot, self.exg_plot = self.config_funct.get_exg_plot_data()
        self.chan_dict = self.config_funct.get_chan_dict()
        print(f"{len(self.config_funct.get_exg_plot_data()[0])=}")
        print(f"{len(self.BT_funct.get_exg_plot_data()[0])=}")
        print(f"{len(self.funct.get_exg_plot_data()[0])=}")

        print(f"{self.config_funct.get_chan_dict()=}")
        print(f"{self.BT_funct.get_chan_dict()=}")
        print(f"{self.funct.get_chan_dict()=}")

    @Slot()
    def imp_meas_clicked(self):
        # self.chan_dict = self.BT_funct.get_chan_dict()
        # self.is_connected = self.BT_funct.get_is_connected()
        self.imp_funct.emit_imp()

    def update_fft(self):
        self.timer_fft = QTimer(self)
        self.timer_fft.setInterval(2000)
        self.timer_fft.timeout.connect(lambda: self.vis_funct.plot_fft())
        self.timer_fft.start()

    def update_heart_rate(self):
        self.timer_hr = QTimer(self)
        self.timer_hr.setInterval(2000)
        self.timer_hr.timeout.connect(lambda: self.vis_funct.plot_heart_rate())
        self.timer_hr.start()

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

        files = ", ".join(self.file_names)
        self.ui.le_data_path.setText(files)
        print(self.file_names)

    """def plot_filters(self):
        '''
        Open plot filter dialog and apply filters
        '''
        wait = True if self.plotting_filters is None else False
        sr = self.explorer.stream_processor.device_info['sampling_rate']
        dialog = PlotDialog(sr=sr, current_filters=self.plotting_filters)
        self.plotting_filters = dialog.exec()
        AppFunctions._apply_filters(self)
        # self.loading = LoadingScreen()
        if wait:
            time.sleep(1.5)"""

    """def start_timer_recorder(self):
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
    """
    def start_recorded_plots(self):
        '''
        Start plotting recorded data
        '''

        '''if self.file_names is None:
            QMessageBox.critical(self, "Error", "Import data first")'''

        # if self.ui.cb_swiping.isChecked():
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

            if any("orn" in s.lower() for s in self.file_names):
                self.plot_orn_recorded = Plots("orn", self.file_names, orn_wdgt, time_scale)

        # if self.is_streaming is False and self.ui.cb_swiping.isChecked():
        if self.is_streaming is False and self.ui.cb_swipping_rec.isChecked():
            self.ui.btn_stream_rec.setText("Stop Data Stream")
            self.ui.btn_stream_rec.setStyleSheet(Settings.STOP_BUTTON_STYLESHEET)
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
            self.ui.btn_stream_rec.setText("Start Data Stream")
            self.ui.btn_stream_rec.setStyleSheet(Settings.START_BUTTON_STYLESHEET)
            self.is_streaming = False
            try:
                self.timer_exg.stop()
                self.timer_orn.stop()
            except AttributeError as e:
                print(str(e))

    #########################
    # UI Functions
    #########################
    def changePage(self, btn_name):
        """
        Change the active page when the object is clicked
        Args:
            btn_name
        """
        self.is_imp_measuring = self.imp_funct.get_imp_status()
        # btn = self.sender()
        # btn_name = btn.objectName()

        if btn_name == "btn_home":
            self.imp_funct.check_is_imp()
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)

        elif btn_name == "btn_settings":
            self.imp_funct.check_is_imp()
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)

        elif btn_name == "btn_plots":
            # self.ui.label_3.setHidden(self.file_names is None)
            # self.ui.label_7.setHidden(self.file_names is None)

            self.imp_funct.check_is_imp()

            if self.funct.is_connected is False and self.file_names is None:
                msg = "Please connect an Explore device or import data before attempting to visualize the data"
                QMessageBox.information(self, "!", msg)
                return

            elif self.file_names is None:
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)
                if self.funct.plotting_filters is None:
                    filt = self.vis_funct.popup_filters()

                if not self.is_streaming and filt:
                    self.vis_funct.emit_signals()
                    self.update_fft()
                    self.update_heart_rate()
                    self.is_streaming = True

                if filt is False:
                    self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)

                # for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
                #     w.setEnabled(False)
                #     w.setToolTip("Changing channels during visualization is not allowed")
                #     w.setStyleSheet("color: gray")

            else:
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsRecorded)

        elif btn_name == "btn_impedance":
            if self.funct.is_connected is False:
                msg = "Please connect an Explore device to visualize the impedances."
                self.funct.display_msg(msg_text=msg, type="info")
                return

            self.ui.stackedWidget.setCurrentWidget(self.ui.page_impedance)
            self.imp_funct.reset_impedance()

        elif btn_name == "btn_integration":
            if self.funct.is_connected is False:
                msg = "Please connect an Explore device to push the data."
                self.funct.display_msg(msg_text=msg, type="info")
                return

            self.imp_funct.check_is_imp()
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_integration)

    def slideLeftMenu(self, enable=True):
        # Get current left menu width
        width = self.ui.left_side_menu.width()
        if width == Settings.LEFT_MENU_MIN:
            new_width = Settings.LEFT_MENU_MAX
        else:
            new_width = Settings.LEFT_MENU_MIN

        # Animate transition
        self.animation = QPropertyAnimation(
            self.ui.left_side_menu, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(new_width)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.start()

    def leftMenuButtonClicked(self):
        """
        Change style of the button clicked and move to the selected page
        """

        btn = self.sender()
        btn_name = btn.objectName()

        # Navigate to active page
        self.changePage(btn_name)

        if btn_name != "btn_left_menu_toggle":
            # Reset style for other buttons
            for w in self.ui.left_side_menu.findChildren(QPushButton):
                if w.objectName() != btn_name:
                    defaultStyle = w.styleSheet().replace(Settings.BTN_LEFT_MENU_SELECTED_STYLESHEET, "")
                    # Apply default style
                    w.setStyleSheet(defaultStyle)

            # Apply new style
            newStyle = btn.styleSheet() + (Settings.BTN_LEFT_MENU_SELECTED_STYLESHEET)
            btn.setStyleSheet(newStyle)

    def mousePressEvent(self, event):
        '''
        Get mouse current position to move the window
        Args: mouse press event
        '''
        self.clickPosition = event.globalPosition().toPoint()

    @Slot()
    def restore_or_maximize(self):
        # Global window state
        global WINDOW_SIZE
        win_status = WINDOW_SIZE

        if not win_status:
            WINDOW_SIZE = True
            self.showMaximized()
            # Update button icon
            self.ui.btn_restore.setIcon(QIcon(
                u":icons/icons/cil-window-restore.png"))

        else:
            WINDOW_SIZE = False
            self.showNormal()  # normal is 800x400
            # Update button icon
            self.ui.btn_restore.setIcon(QIcon(
                u":icons/icons/icon_maximize.png"))

    @Slot()
    def on_close(self):
        self.stop_processes()
        self.close()

    def ui_definitions(self):
        # Double click onn bar to maximize/restore the window
        def doubleClickMaximize(e):
            if e.type() == QEvent.MouseButtonDblClick:
                QTimer.singleShot(
                    250, lambda: self.restore_or_maximize())
        self.ui.main_header.mouseDoubleClickEvent = doubleClickMaximize

        # Move Winndow poisitionn
        def moveWindow(e):
            '''
            Move window on mouse drag event on the title bar
            '''
            # if maximized restore to normal
            if WINDOW_SIZE:
                self.restore_or_maximize()

            if e.buttons() == Qt.LeftButton:
                # Move window:
                self.move(self.pos() + e.globalPosition().toPoint() - self.clickPosition)
                self.clickPosition = e.globalPosition().toPoint()
                e.accept()

        if Settings.CUSTOM_TITLE_BAR:
            # Add click/move/drag event to the top header to move the window
            self.ui.main_header.mouseMoveEvent = moveWindow
        else:
            self.ui.top_right_btns.hide()

        # Drop Shadow
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(17)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.ui.centralwidget.setGraphicsEffect(self.shadow)

        # Resize winndow
        self.sizegrip = QSizeGrip(self.ui.frame_size_grip)
        self.sizegrip.setStyleSheet("width: 20px; height: 20px; margin 0px; padding: 0px;")

        # Button click events:
        # Minimize
        self.ui.btn_minimize.clicked.connect(lambda: self.showMinimized())
        # Restore/Maximize
        self.ui.btn_restore.clicked.connect(lambda: self.restore_or_maximize())
        # Restore/Maximize
        self.ui.btn_close.clicked.connect(lambda: self.on_close())

    #########################
    # other Functions
    #########################
    def init_dropdowns(self):
        '''
        Initilize the GUI dropdowns with the values specified above
        '''

        # value number of channels:
        self.ui.n_chan.addItems(Settings.N_CHAN_LIST)
        self.ui.n_chan.setCurrentText("8")

        # value_signal_type
        self.ui.value_signal.addItems(Settings.MODE_LIST)
        self.ui.value_signal_rec.addItems(Settings.MODE_LIST)

        # value_yaxis
        self.ui.value_yAxis.addItems(Settings.SCALE_MENU.keys())
        self.ui.value_yAxis.setCurrentText("1 mV")

        self.ui.value_yAxis_rec.addItems(Settings.SCALE_MENU.keys())
        self.ui.value_yAxis_rec.setCurrentText("1 mV")

        # value_time_scale
        self.ui.value_timeScale.addItems(Settings.TIME_RANGE_MENU.keys())
        self.ui.value_timeScale_rec.addItems(Settings.TIME_RANGE_MENU.keys())

        # value_sampling_rate
        self.ui.value_sampling_rate.addItems([str(int(sr)) for sr in Settings.SAMPLING_RATES])

        self.ui.value_event_code.setValidator(QIntValidator(8, 65535))

        self.ui.cb_swipping_rec.setChecked(True)

        self.ui.imp_mode.addItems(["Wet electrodes", "Dry electrodes"])

    def stop_processes(self):
        if self.record_funct.is_recording:
            self.record_funct.stop_record()
            self.record_funct.is_recording = False
        if self.is_started:
            pass
        if self.LSL_funct.get_pushing_status():
            self.explorer.stop_lsl()
            self.LSL_funct.is_pushing = False
            self.ui.btn_push_lsl.setText("Push")
        if self.imp_funct.get_imp_status():
            self.imp_funct.disable_imp()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
