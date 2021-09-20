
# MAIN FILE
# ///////////////////////////////////////////////////////////////

from main import *

'''
# GLOBALS
# ///////////////////////////////////////////////////////////////
GLOBAL_STATE = False
GLOBAL_TITLE_BAR = True
'''
# Global value for the windows status
# This will help us determine is the window is minnimized or maximized
# default value is False to show size is not maximized
WINDOW_SIZE = False


class UIFunctions(MainWindow):

    # Restore or maximize window
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

    # Get window status
    def getWindowStatus(self):
        return WINDOW_SIZE

    # set status
    def setWindowStatus(self, status):
        global WINDOW_SIZE
        WINDOW_SIZE = status

    # Slide left menu
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

    # UI Definitions
    def ui_definitions(self):
        # Double click onn bar to maximize/restore the window
        def doubleClickMaximize(e):
            if e.type() == QEvent.MouseButtonDblClick:
                QTimer.singleShot(
                    250, lambda: UIFunctions.restore_or_maximize(self))
        self.ui.main_header.mouseDoubleClickEvent = doubleClickMaximize

        # Move Winndow poisitionn
        def moveWindow(e):
            '''
            Move window on mouse drag event on the title bar
            '''
            # if maximized restore to normal
            if UIFunctions.getWindowStatus(self):
                UIFunctions.restore_or_maximize(self)

            if e.buttons() == Qt.LeftButton:
                # Move window:
                self.move(self.pos() + e.globalPos() - self.clickPosition)
                self.clickPosition = e.globalPos()
                e.accept()

        if Settings.CUSTOM_TITLE_BAR:
            # Add click/move/drag event to the top header to move the window
            self.ui.main_header.mouseMoveEvent = moveWindow
        else:
            self.ui.top_right_btns.hide()

        # Drop Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
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
        self.ui.btn_restore.clicked.connect(
            lambda: UIFunctions.restore_or_maximize(self))
        # Restore/Maximize
        self.ui.btn_close.clicked.connect(lambda: self.close())
    
    '''def resize_grips(self):
        # if Settings.ENABLE_CUSTOM_TITLE_BAR:
        self.left_grip.setGeometry(0, 10, 10, self.height())
        self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height())
        self.top_grip.setGeometry(0, 0, self.width(), 10)
        self.bottom_grip.setGeometry(0, self.height() - 10, self.width(), 10)'''
