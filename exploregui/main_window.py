import datetime
import os
import sys

import exploregui
import explorepy as xpy
from exploregui.modules import (
    AppFunctions,
    BTFunctions,
    ConfigFunctions,
    IMPFunctions,
    LSLFunctions,
    RecordFunctions,
    Settings,
    Ui_MainWindow,
    VisualizationFunctions
)
from explorepy.log_config import (
    read_config,
    write_config
)
from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
    Slot
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QIntValidator
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGraphicsDropShadowEffect,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizeGrip
)


VERSION_APP = exploregui.__version__
WINDOW_SIZE = False


class MainWindow(QMainWindow):
    """
    Main window class. Connect signals and slots
    Args:
        QMainWindow (PySide.QtWidget.QMainWindow): MainWindow widget
    """
    signal_exg = Signal(object)
    signal_orn = Signal(object)
    signal_imp = Signal(object)
    signal_mkr = Signal(object)

    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "MentalabLogo.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('ExploreGUI')

        self.explorer = xpy.Explore()
        self.funct = AppFunctions(self.ui, self.explorer)
        self.lsl_funct = LSLFunctions(self.ui, self.explorer)
        self.bt_funct = BTFunctions(self.ui, self.explorer)
        self.imp_funct = IMPFunctions(self.ui, self.explorer, self.signal_imp)
        self.vis_funct = VisualizationFunctions(
            self.ui, self.explorer,
            {"exg": self.signal_exg, "mkr": self.signal_mkr, "orn": self.signal_orn}
        )
        self.config_funct = ConfigFunctions(self.ui, self.explorer, self.vis_funct)
        self.record_funct = RecordFunctions(self.ui, self.explorer)

        self.is_streaming = False
        self.file_names = None
        self.is_started = False

        bold_font = QFont()
        bold_font.setBold(True)
        self.ui.ft_label_device_3.setFont(bold_font)
        self.ui.ft_label_device_3.setStyleSheet("font-weight: bold")
        self.ui.label_3.setHidden(self.file_names is None)
        self.ui.label_7.setHidden(self.file_names is None)

        # Hide os bar
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Add app version to footer
        self.ui.ft_label_version.setText(VERSION_APP)

        # Hide footer
        self.ui.ft_label_firmware.setHidden(True)
        self.ui.ft_label_firmware_value.setHidden(True)
        self.ui.ft_label_battery.setHidden(True)
        self.ui.ft_label_battery_value.setHidden(True)
        self.ui.ft_label_temp.setHidden(True)
        self.ui.ft_label_temp_value.setHidden(True)

        # Set UI definitions (close, restore, etc)
        self.ui_definitions()

        # Initialize values
        self.init_dropdowns()

        # Apply stylesheets
        self.funct.lineedit_stylesheet()

        # Slidable left panel
        self.ui.btn_left_menu_toggle.clicked.connect(self.slide_left_menu)

        # Stacked pages - default open connect or home if permissions are not set
        existing_permission = self.check_permissions()
        if existing_permission:
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)
            self.highlight_left_button("btn_bt")
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
            self.highlight_left_button("btn_home")
            # Set data sharing permissions
            self.set_permissions()

        # Start with foucus on line edit for device name
        self.ui.dev_name_input.setFocus()

        # Stacked pages - navigation
        for btn_wdgt in self.ui.left_side_menu.findChildren(QPushButton):
            btn_wdgt.clicked.connect(self.left_menu_button_clicked)

        # Check connection every 2 seconds
        self.check_connection()

        # HOME PAGE
        self.ui.cb_permission.stateChanged.connect(self.set_permissions)
        # CONNECT PAGE BUTTONS
        self.ui.lbl_wdws_warning.hide()
        # hide import data:
        self.ui.btn_import_data.hide()
        self.ui.le_data_path.hide()
        self.ui.label_16.setHidden(True)
        self.ui.line_2.hide()
        self.ui.lbl_bt_instructions.hide()

        self.ui.dev_name_input.textChanged.connect(self.funct.lineedit_stylesheet)
        self.ui.btn_connect.clicked.connect(self.connect_clicked)
        self.ui.dev_name_input.returnPressed.connect(self.connect_clicked)
        self.ui.btn_scan.clicked.connect(self.bt_funct.scan_devices)

        # SETTING PAGE BUTTONS
        self.ui.lbl_sr_warning.hide()
        self.ui.value_sampling_rate.currentTextChanged.connect(self.config_funct.display_sr_warning)
        # self.ui.btn_import_data.clicked.connect(self.import_recorded_data)
        self.ui.btn_format_memory.clicked.connect(self.config_funct.format_memory)
        self.ui.btn_reset_settings.clicked.connect(self.soft_reset)
        self.ui.btn_apply_settings.clicked.connect(self.config_funct.change_settings)
        self.ui.btn_calibrate.setHidden(True)
        # self.ui.btn_calibrate.clicked.connect(self.config_funct.calibrate_orn())
        self.ui.n_chan.currentTextChanged.connect(self.n_chan_changed)
        for ch_wdgt in self.ui.frame_cb_channels.findChildren(QCheckBox):
            ch_wdgt.stateChanged.connect(self.config_funct.one_chan_selected)

        # IMPEDANCE PAGE
        self.ui.imp_meas_info.setHidden(False)

        self.ui.imp_meas_info.clicked.connect(self.imp_info_clicked)
        # self.ui.imp_meas_info.setToolTip("Sum of impedances on REF and individual channels divided by 2")
        self.signal_imp.connect(self.imp_funct.update_impedance)
        self.ui.btn_imp_meas.clicked.connect(self.imp_meas_clicked)
        self.ui.label_6.setHidden(True)

        # PLOTTING PAGE
        self.ui.value_signal.currentTextChanged.connect(self.vis_funct._mode_change)
        self.ui.btn_record.clicked.connect(self.record_funct.on_record)
        self.ui.btn_plot_filters.clicked.connect(self.vis_funct.popup_filters)

        self.ui.btn_marker.setEnabled(False)
        self.ui.value_event_code.textChanged[str].connect(lambda: self.ui.btn_marker.setEnabled(
            (self.ui.value_event_code.text() != "")))
        self.ui.value_event_code.textChanged[str].connect(lambda: self.ui.btn_marker.setEnabled(
            (self.ui.value_event_code.text().isnumeric()) and (8 <= int(self.ui.value_event_code.text()))))

        # self.ui.value_event_code.setEnabled(self.ui.btn_record.text()=="Stop")
        self.ui.btn_marker.clicked.connect(self.vis_funct.set_marker)
        self.ui.value_event_code.returnPressed.connect(self.vis_funct.set_marker)

        self.ui.value_yAxis.currentTextChanged.connect(self.vis_funct.change_scale)
        self.ui.value_timeScale.currentTextChanged.connect(self.vis_funct.change_timescale)

        self.signal_exg.connect(self.vis_funct.plot_exg)
        self.signal_orn.connect(self.vis_funct.plot_orn)
        self.signal_mkr.connect(self.vis_funct.plot_mkr)

        self.ui.btn_stream.hide()

        # INTEGRATION PAGE
        self.ui.lsl_duration_value.hide()
        self.ui.cb_lsl_duration.hide()
        self.ui.label_lsl_duration.setHidden(True)
        self.ui.cb_lsl_duration.stateChanged.connect(self.lsl_funct.enable_lsl_duration)
        self.ui.btn_push_lsl.clicked.connect(self.lsl_funct.push_lsl)

        self.last_t = datetime.datetime.now()
        self.first_t = datetime.datetime.now()

    @Slot()
    def connect_clicked(self) -> None:
        """
        Connect or disconnect from device
        """
        if self.funct.get_is_connected() is False:
            self.bt_funct.connect2device()
            self.funct.is_connected = self.bt_funct.is_connected
            if self.funct.is_connected:
                # Initialize plots
                self.vis_funct.init_plots()
                # Move to settings page
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_settings)
                # Change left menu button highlight
                self.highlight_left_button("btn_settings")
        else:
            self.bt_funct.disconnect()
            self.funct.is_connected = self.bt_funct.is_connected
            self.stop_processes()
            self.reset_vars()

    @Slot()
    def n_chan_changed(self):
        """
        Update settings page when number of channels is changed
        """
        self.bt_funct.set_n_chan()
        self.bt_funct.update_frame_dev_settings()

    @Slot()
    def soft_reset(self):
        """Reset device settings and disconnect it
        """
        reset = self.config_funct.reset_settings()
        if reset:
            self.bt_funct.disconnect()
            self.stop_processes()
            self.reset_vars()
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_bt)
            self.highlight_left_button("btn_bt")

    @Slot()
    def imp_meas_clicked(self):
        """
        Start impedance measurement.
        If another process is running, it will ask the user for confirmation
        """
        msg = (
            "Impedance measurement will introduce noise to the signal"
            " and affect the visualization, recording, and LSL stream."
            "\nAre you sure you want to continue?")
        if not self.imp_funct.is_imp_measuring and (self.record_funct.is_recording or self.lsl_funct.is_pushing):
            response = self.funct.display_msg(msg_text=msg, type="question")
            if response == QMessageBox.StandardButton.No:
                return
        self.imp_funct.emit_imp()

    def update_fft(self):
        """Start QTimer to update impedance every two seconds
        """
        self.timer_fft = QTimer(self)
        self.timer_fft.setInterval(2000)
        self.timer_fft.timeout.connect(self.vis_funct.plot_fft)
        self.timer_fft.start()

    def update_heart_rate(self):
        """Start QTimer to update heart rate every two seconds
        """
        self.timer_hr = QTimer(self)
        self.timer_hr.setInterval(2000)
        self.timer_hr.timeout.connect(self.vis_funct.plot_heart_rate)
        self.timer_hr.start()

    @Slot()
    def imp_info_clicked(self):
        """Display message when impedance question mark is clicked
        """
        imp_msg = (
            "NOTE: The impedance value displayed for each channel also depends on"
            " the impedance of the reference electrode.\n\n"
            "If all channel’s impedances are high, try cleaning the skin under the reference electrode more thoroughly"
            " (e.g. with alcohol, abrasive gel, EEG gel)"
        )
        self.funct.display_msg(imp_msg, type="info")

    #########################
    # UI Functions
    #########################
    def change_page(self, btn_name):
        """
        Change the active page when the object is clicked
        Args:
            btn_name (str): button named
        """
        btn_page_map = {
            "btn_home": self.ui.page_home, "btn_bt": self.ui.page_bt,
            "btn_settings": self.ui.page_settings, "btn_plots": self.ui.page_plotsNoWidget,
            "btn_impedance": self.ui.page_impedance, "btn_integration": self.ui.page_integration}

        # If not navigating to impedance, verify if imp mode is active
        if self.imp_funct.is_imp_measuring and btn_name != "btn_impedance":
            imp_disabled = self.imp_funct.check_is_imp()
            if not imp_disabled:
                return False
        # If the page requires connection to a Explore device, verify
        if btn_name in Settings.LEFT_BTN_REQUIRE_CONNECTION and self.funct.is_connected is False:
            msg = "Please connect an Explore device."
            self.funct.display_msg(msg_text=msg, type="info")
            return False

        # Actions for specific pages
        if btn_name == "btn_settings":
            self.bt_funct.update_frame_dev_settings(reset_data=False)
            self.config_funct.one_chan_selected()
            enable = not self.record_funct.is_recording and not self.lsl_funct.is_pushing
            self.config_funct.enable_settings(enable)
            self.ui.value_sampling_rate.setEnabled(True)

        elif btn_name == "btn_plots":
            filt = True
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)
            if self.funct.plotting_filters is None:
                filt = self.vis_funct.popup_filters()

            if filt is False:
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_settings)
                return False

            if not self.is_streaming and filt:
                self.vis_funct.emit_signals()
                self.update_fft()
                self.update_heart_rate()
                self.is_streaming = True

        elif btn_name == "btn_impedance":
            self.imp_funct.reset_impedance()

        # Move to page
        self.ui.stackedWidget.setCurrentWidget(btn_page_map[btn_name])
        return True

    def slide_left_menu(self):
        """
        Animation to display the whole left menu
        """
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

    def highlight_left_button(self, btn_name):
        """
        Change style of the button clicked

        Args:
            btn_name (str): name of the button to highlight
        """
        if btn_name != "btn_left_menu_toggle":
            # Reset style for other buttons
            for btn_wdgt in self.ui.left_side_menu.findChildren(QPushButton):
                if btn_wdgt.objectName() != btn_name:
                    default_style = btn_wdgt.styleSheet().replace(Settings.BTN_LEFT_MENU_SELECTED_STYLESHEET, "")
                    btn_wdgt.setStyleSheet(default_style)

            # Apply new style
            btn = self.funct.get_widget_by_objName(btn_name)
            new_style = btn.styleSheet() + (Settings.BTN_LEFT_MENU_SELECTED_STYLESHEET)
            btn.setStyleSheet(new_style)

    def left_menu_button_clicked(self):
        """
        Change style of the button clicked and move to the selected page
        """
        btn = self.sender()
        btn_name = btn.objectName()

        # Navigate to active page
        change = self.change_page(btn_name)
        if change is False:
            return
        # Apply stylesheet
        self.highlight_left_button(btn_name)

    def mousePressEvent(self, event):
        """
        Get mouse current position to move the window
        Args: mouse press event
        """
        self.clickPosition = event.globalPosition().toPoint()

    @Slot()
    def restore_or_maximize(self):
        """
        Restore or maximize window
        """
        # Global window state
        global WINDOW_SIZE
        win_status = WINDOW_SIZE

        if not win_status:
            WINDOW_SIZE = True
            self.showMaximized()
            # Update button icon
            self.ui.btn_restore.setIcon(QIcon(":icons/icons/cil-window-restore.png"))

        else:
            WINDOW_SIZE = False
            self.showNormal()  # normal is 800x400
            # Update button icon
            self.ui.btn_restore.setIcon(QIcon(":icons/icons/cil-window-maximize.png"))

    @Slot()
    def on_close(self):
        """
        Stop all ongoing processes when closing the app
        """
        try:
            self.vis_funct.emit_orn(stop=True)
            self.vis_funct.emit_exg(stop=True)
            self.signal_orn.disconnect(self.vis_funct.plot_orn)
            self.signal_exg.disconnect(self.vis_funct.plot_exg)
        except AttributeError:
            pass
        self.stop_processes()
        self.close()

    def ui_definitions(self):
        """UI functions
        """
        # Double click on bar to maximize/restore the window
        def double_click_maximize(e):
            """Maximixe or restore window when top bar is double-clicked

            Args:
                e (event): mouse double click event
            """
            if e.type() == QEvent.MouseButtonDblClick:
                QTimer.singleShot(250, self.restore_or_maximize)
        self.ui.main_header.mouseDoubleClickEvent = double_click_maximize

        # Move Winndow poisitionn
        def move_window(e):
            """
            Move window on mouse drag event on the title bar
            """
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
            self.ui.main_header.mouseMoveEvent = move_window
        else:
            self.ui.top_right_btns.hide()

        # Drop Shadow
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 0))
        self.ui.centralwidget.setGraphicsEffect(self.shadow)

        # Resize winndow
        self.sizegrip = QSizeGrip(self.ui.frame_size_grip)
        self.sizegrip.setStyleSheet("width: 20px; height: 20px; margin 0px; padding: 0px;")

        # Button click events:
        # Minimize
        self.ui.btn_minimize.clicked.connect(self.showMinimized)
        # Restore/Maximize
        self.ui.btn_restore.clicked.connect(self.restore_or_maximize)
        # Restore/Maximize
        self.ui.btn_close.clicked.connect(self.on_close)

    #########################
    # other Functions
    #########################
    def init_dropdowns(self):
        """
        Initilize the GUI dropdowns with the values specified above
        """

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
        """Stop ongoing processes
        """
        if self.record_funct.is_recording:
            self.record_funct.stop_record()
            self.record_funct.is_recording = False
        if self.is_started:
            pass
        if self.lsl_funct.get_pushing_status():
            self.explorer.stop_lsl()
            self.lsl_funct.is_pushing = False
            self.ui.btn_push_lsl.setText("Push")
        if self.imp_funct.get_imp_status():
            self.imp_funct.disable_imp()

    def reset_vars(self):
        """Reset al variables in modules"""
        self.is_streaming = False
        self.funct.reset_vars()
        self.bt_funct.reset_bt_vars()
        self.vis_funct.reset_vis_vars()
        self.record_funct.reset_record_vars()
        self.imp_funct.reset_imp_vars()
        self.lsl_funct.reset_lsl_vars()

    #########################
    # Connection Functions
    #########################
    def print_connection(self):
        """Update connection label
        """
        reconnecting_label = "Reconnecting ..."
        not_connected_label = "Not connected"
        connected_label = f"Connected to {self.explorer.device_name}"

        if self.explorer.is_connected:
            sp_connected = self.explorer.stream_processor.is_connected
            reconnecting = self.explorer.stream_processor.parser._is_reconnecting
            label_text = self.ui.ft_label_device_3.text()

            if sp_connected and reconnecting:
                if label_text != reconnecting_label:
                    self.ui.ft_label_device_3.setText(reconnecting_label)
                    self.ui.ft_label_device_3.repaint()
                    # self.vis_funct._vis_time_offset = None
            elif sp_connected and reconnecting is False:
                if label_text != connected_label:
                    self.ui.ft_label_device_3.setText(connected_label)
                    self.ui.ft_label_device_3.repaint()
            elif sp_connected is False and reconnecting is False:
                if label_text != not_connected_label:
                    self.ui.ft_label_device_3.setText(not_connected_label)
                    self.ui.ft_label_device_3.repaint()
                    self.funct.is_connected = False
                    self.bt_funct.is_connected = False
                    self.reset_vars()
                    self.bt_funct.on_connection_change()
                    self.change_page(btn_name="btn_bt")
        else:
            return

    def check_connection(self):
        """Timer to check the connection every 2 seconds
        """
        self.timer_con = QTimer(self)
        self.timer_con.setInterval(2000)
        self.timer_con.timeout.connect(self.print_connection)
        self.timer_con.start()

    def set_permissions(self):
        """
        Set data sharing permission to explorepy config file
        """
        share = self.ui.cb_permission.isChecked()
        write_config("user settings", "share_logs", str(share))

    def check_permissions(self):
        """Check current data sharing permission

        Returns:
            bool: whether permission exist in config file
        """
        exist = False
        config = read_config("user settings", "share_logs")
        if config != "":
            config = True if config == "True" else False
            self.ui.cb_permission.setChecked(config)
            exist = True
        return exist


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
