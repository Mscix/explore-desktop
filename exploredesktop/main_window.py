"""Main Application"""
import logging
import os
import sys

import exploredesktop
from exploredesktop.modules import (
    BaseModel,
    Settings,
    Stylesheets,
    Ui_MainWindow
)
from exploredesktop.modules.app_settings import (
    ConnectionStatus,
    DataAttributes,
    EnvVariables
)
from exploredesktop.modules.bt_module import BTFrameView
from exploredesktop.modules.exg_module import ExGPlot
from exploredesktop.modules.fft_module import FFTPlot
from exploredesktop.modules.footer_module import FooterFrameView
from exploredesktop.modules.imp_module import ImpFrameView
from exploredesktop.modules.orn_module import ORNPlot
from exploredesktop.modules.settings_module import SettingsFrameView
from exploredesktop.modules.tools import (
    display_msg,
    get_widget_by_obj_name
)
from exploredesktop.modules.mkr_module import MarkerPlot
from explorepy.log_config import (
    read_config,
    write_config
)
from explorepy.stream_processor import TOPICS
from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    Qt,
    QThreadPool,
    QTimer,
    Slot
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon
)
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QMainWindow,
    QPushButton,
    QSizeGrip
)


VERSION_APP = exploredesktop.__version__
WINDOW_SIZE = False

logger = logging.getLogger("explorepy." + __name__)


class MainWindow(QMainWindow, BaseModel):
    """
    Main window class. Connect signals and slots
    """

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "MentalabLogo.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('ExploreDesktop')

        self.is_streaming = False

        # Style UI
        self.style_ui()

        # Set UI definitions (close, restore, etc)
        self.ui_definitions()

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

        # Stacked pages - navigation
        for btn_wdgt in self.ui.left_side_menu.findChildren(QPushButton):
            btn_wdgt.clicked.connect(self.left_menu_button_clicked)

        # HOME PAGE
        self.ui.cb_permission.stateChanged.connect(self.set_permissions)

        # IMPEDANCE PAGE
        self.imp_frame = ImpFrameView(self.ui)
        self.imp_frame.setup_ui_connections()

        # BLUETOOTH PAGE
        self.bt_frame = BTFrameView(self.ui)
        self.bt_frame.setup_ui_connections()

        # FOOTER
        self.footer_frame = FooterFrameView(self.ui)

        # SETTINGS PAGE
        self.settings_frame = SettingsFrameView(self.ui)
        self.settings_frame.setup_ui_connections()

        # PLOTS
        self.orn_plot = ORNPlot(self.ui)

        self.exg_plot = ExGPlot(self.ui)
        self.exg_plot.setup_ui_connections()

        self.fft_plot = FFTPlot(self.ui)

        self.mkr_plot = MarkerPlot(self.ui)
        self.mkr_plot.setup_ui_connections()

        # signal connections
        self.setup_signal_connections()

    #########################
    # UI Functions
    #########################

    def on_connection_change(self, connection):
        """Actions to perfom when connection status changes

        Args:
            connection (Enum): connection status
        """
        self.footer_frame.print_connection_status(connection)

        if connection == ConnectionStatus.CONNECTED:
            btn_connect_text = "Disconnect"
            btn_scan_enabled = False

            if self.ui.stackedWidget.currentWidget() == self.ui.page_bt:
                self.signals.pageChange.emit("btn_settings")

            firmware = self.explorer.stream_processor.device_info["firmware_version"]
            data = {EnvVariables.FIRMWARE: firmware}
            self.signals.devInfoChanged.emit(data)

            # initialize impedance
            self.signals.displayDefaultImp.emit()
            # subscribe environmental data callback
            self.footer_frame.get_model().subscribe_env_callback()
            # initialize settings frame
            self.settings_frame.setup_settings_frame()
            # initialize visualization offsets
            self.signals.updateDataAttributes.emit([DataAttributes.OFFSETS, DataAttributes.DATA])

            # TODO: delete when filters are implemented
            self.explorer.add_filter((1, 30), "bandpass")
            self.explorer.add_filter(50, "notch")

        elif connection == ConnectionStatus.DISCONNECTED:
            btn_connect_text = "Connect"
            btn_scan_enabled = True
            self.signals.pageChange.emit("btn_bt")

            # TODO:
            # stop processes
            # reset vars:
            self.exg_plot.reset_vars()
            self.exg_plot.get_model().reset_vars()
            self.is_streaming = False
            self.orn_plot.reset_vars()
            self.orn_plot.get_model().reset_vars()
            self.fft_plot.reset_vars()
            self.footer_frame.get_model().reset_vars()
            self.imp_frame.get_model().reset_vars()

        else:
            return

        self.signals.btnConnectChanged.emit(btn_connect_text)
        self.ui.btn_scan.setEnabled(btn_scan_enabled)

    def setup_signal_connections(self):
        """connect custom signals to corresponding slots
        """
        # change button text
        self.signals.btnImpMeasureChanged.connect(self.ui.btn_imp_meas.setText)
        self.signals.btnConnectChanged.connect(self.ui.btn_connect.setText)

        self.signals.envInfoChanged.connect(self.footer_frame.update_env_info)
        self.signals.devInfoChanged.connect(self.footer_frame.update_dev_info)

        self.signals.connectionStatus.connect(self.on_connection_change)

        self.signals.impedanceChanged.connect(self.imp_frame.get_graph().on_new_data)
        self.signals.displayDefaultImp.connect(self.imp_frame.get_graph().display_default_imp)

        self.signals.pageChange.connect(self.left_menu_button_clicked)

        self.signals.ornChanged.connect(self.orn_plot.swipe_plot)
        self.signals.exgChanged.connect(self.exg_plot.swipe_plot)

        self.signals.tRangeORNChanged.connect(self.orn_plot.set_t_range)
        self.signals.tAxisORNChanged.connect(self.orn_plot.set_t_axis)

        self.signals.tRangeEXGChanged.connect(self.exg_plot.set_t_range)
        self.signals.tAxisEXGChanged.connect(self.exg_plot.set_t_axis)

        self.signals.updateYAxis.connect(self.exg_plot.add_left_axis_ticks)

        self.signals.restartPlot.connect(self.exg_plot.init_plot)
        self.signals.restartPlot.connect(self.fft_plot.init_plot)

        self.signals.mkrPlot.connect(self.mkr_plot.plot_marker)
        self.signals.mkrAdd.connect(self.mkr_plot.model.add_mkr)
        # self.signals.mkrReplot.connect(lambda data: self.mkr_plot.plot_marker(data, replot=True))
        self.signals.replotMkrAdd.connect(self.mkr_plot.model.add_mkr_replot)
        self.signals.mkrRemove.connect(self.mkr_plot.remove_old_item)

    def style_ui(self):
        """Initial style for UI
        """
        # Bold font for device label
        bold_font = QFont()
        bold_font.setBold(True)
        self.ui.ft_label_device_3.setFont(bold_font)
        self.ui.ft_label_device_3.setStyleSheet("font-weight: bold")

        # Hide unnecessary labels
        # TODO: review in QtCreator if labels are needed in the future or can be deleted
        # self.ui.label_3.setHidden(self.file_names is None)

        self.ui.line_2.setHidden(True)

        # plotting page
        self.ui.label_3.setHidden(True)
        self.ui.label_7.setHidden(True)
        self.ui.btn_stream.setHidden(True)
        # imp page
        self.ui.label_6.setHidden(True)
        # settings page
        self.ui.label_warning_disabled.setHidden(True)
        self.ui.label_12.setHidden(True)
        self.ui.n_chan.setHidden(True)
        self.ui.lbl_sr_warning.hide()
        self.ui.btn_calibrate.setHidden(True)
        # connect page
        self.ui.lbl_wdws_warning.hide()
        self.ui.btn_import_data.hide()
        self.ui.le_data_path.hide()
        self.ui.label_16.setHidden(True)
        self.ui.line_2.hide()
        self.ui.lbl_bt_instructions.hide()

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

        # Start with foucus on line edit for device name
        self.ui.dev_name_input.setFocus()

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
        if self.explorer.is_measuring_imp and btn_name != "btn_impedance":
            imp_disabled = self.imp_frame.check_is_imp()
            if not imp_disabled:
                return False

        # If the page requires connection to a Explore device, verify
        if btn_name in Settings.LEFT_BTN_REQUIRE_CONNECTION and self.explorer.is_connected is False:
            msg = "Please connect an Explore device."
            display_msg(msg_text=msg, popup_type="info")
            return False

        # Actions for specific pages
        if btn_name == "btn_settings":
            self.settings_frame.setup_settings_frame()
            self.settings_frame.one_chan_selected()
            # TODO enable settings depending on recording/pushing status
            # enable = not self.explorer.is_recording and not self.explorer.is_pushing_lsl
            # self.settings_frame.enable_settings(enable)
            # self.ui.value_sampling_rate.setEnabled(True)

        # elif btn_name == "btn_impedance":
        #     self.signals.displayDefaultImp.emit()

        elif btn_name == "btn_plots":
            # TODO check filters if not set, display popup
            # filt = True
            # self.ui.stackedWidget.setCurrentWidget(self.ui.page_plotsNoWidget)
            # if self.funct.plotting_filters is None and self.vis_funct.plotting_filters is None:
            #     filt = self.vis_funct.popup_filters()

            # TODO if filters popup is canceled, go to settings
            # TODO instead of going to settings go back to previous page
            # if filt is False:
            #     self.ui.stackedWidget.setCurrentWidget(self.ui.page_settings)
            #     self.highlight_left_button("btn_settings")
            #     return False

            # if not self.is_streaming and filt:
            if not self.is_streaming:
                self.orn_plot.init_plot()
                self.explorer.subscribe(callback=self.orn_plot.model.callback, topic=TOPICS.raw_orn)

                self.exg_plot.init_plot()
                self.explorer.subscribe(callback=self.exg_plot.model.callback, topic=TOPICS.filtered_ExG)

                self.fft_plot.init_plot()
                self.explorer.subscribe(callback=self.fft_plot.model.callback, topic=TOPICS.filtered_ExG)
                self.fft_plot.start_timer()

                self.explorer.subscribe(callback=self.mkr_plot.model.callback, topic=TOPICS.marker)

                # TODO
                # self.vis_funct.emit_signals()
                # self.update_fft()
                # self.update_heart_rate()
                self.is_streaming = True

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
                    default_style = btn_wdgt.styleSheet().replace(Stylesheets.BTN_LEFT_MENU_SELECTED_STYLESHEET, "")
                    btn_wdgt.setStyleSheet(default_style)

            # Apply new style
            btn = get_widget_by_obj_name(btn_name)
            new_style = btn.styleSheet() + (Stylesheets.BTN_LEFT_MENU_SELECTED_STYLESHEET)
            btn.setStyleSheet(new_style)

    def left_menu_button_clicked(self, no_click=False):
        """
        Change style of the button clicked and move to the selected page
        """
        if isinstance(no_click, str):
            btn_name = no_click
        else:
            btn = self.sender()
            btn_name = btn.objectName()

        # Navigate to active page
        if btn_name != "btn_left_menu_toggle":
            change = self.change_page(btn_name)
            if change is False:
                return
        # Apply stylesheet
        self.highlight_left_button(btn_name)

    # pylint: disable=invalid-name
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
        self.ui.btn_close.clicked.connect(self.close)

    def close(self) -> bool:
        """actions to perform on close
        """
        # TODO: add other actions to perform on close, e.g. stop timers
        QThreadPool().globalInstance().waitForDone()
        return super().close()

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
