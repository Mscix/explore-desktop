"""Main Application"""
import os
import sys

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


from exploredesktop.modules.tools import display_msg, get_widget_by_obj_name  # isort: skip
import exploredesktop  # isort: skip
from exploredesktop.modules import (  # isort: skip
    Settings,
    Ui_MainWindow,
    BaseModel,
    Stylesheets
)
from exploredesktop.modules.imp_module import ImpedanceGraph, ImpFrameView, ImpModel  # isort: skip

VERSION_APP = exploredesktop.__version__
WINDOW_SIZE = False


class MainWindow(QMainWindow):
    """
    Main window class. Connect signals and slots
    Args:
        QMainWindow (PySide.QtWidget.QMainWindow): MainWindow widget
    """

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "MentalabLogo.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('ExploreDesktop')

        # define signals
        self.signals = BaseModel().get_signals()
        # Style UI
        self.style_ui()

        # Set UI definitions (close, restore, etc)
        self.ui_definitions()

        # Slidable left panel
        self.ui.btn_left_menu_toggle.clicked.connect(self.slide_left_menu)

        # Stacked pages - default open connect or home if permissions are not set
        existing_permission = self.check_permissions()
        if existing_permission:
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_impedance)
            self.highlight_left_button("btn_impedance")
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
        self.imp_graph = ImpedanceGraph(ImpModel())
        self.setup_imp_graph()

        # ImpFrame
        self.imp_frame = ImpFrameView(self.ui, self.imp_graph.get_model())
        # change impedance mode
        self.ui.imp_mode.currentTextChanged.connect(lambda data: self.imp_graph.get_model().set_mode(data))
        # change button text
        self.signals.btnImpMeasureChanged.connect(self.ui.btn_imp_meas.setText)
        # start/stop impedance measurement
        self.ui.btn_imp_meas.clicked.connect(self.imp_frame.measure_imp_clicked)
        # question mark button clicked
        self.ui.imp_meas_info.clicked.connect(self.imp_frame.imp_info_clicked)

    #########################
    # UI Functions
    #########################
    def setup_imp_graph(self):
        """Add impedance graph to GraphicsLayoutWidget
        """
        view_box = self.ui.imp_graph_layout.addViewBox()
        view_box.setAspectLocked()
        view_box.addItem(self.imp_graph)
        view_box.setMouseEnabled(x=False, y=False)
        self.ui.imp_graph_layout.setBackground("transparent")

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
        # plotting page
        self.ui.label_3.setHidden(True)
        self.ui.label_7.setHidden(True)
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

        # Temp code:
        implemented_pages = ["btn_home", "btn_impedance"]

        if btn_name not in implemented_pages:
            display_msg("still not implemented")
            return False
        # End temp code

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

    def left_menu_button_clicked(self):
        """
        Change style of the button clicked and move to the selected page
        """
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
