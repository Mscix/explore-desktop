# This Python file uses the following encoding: utf-8

import logging
import os
import sys

import explorepy
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

import exploredesktop  # isort:skip
from exploredesktop import MainWindow
from exploredesktop.version_update import update_version


logger = logging.getLogger("explorepy.exploredesktop.main")
logger.debug("Starting ExploreDesktop (version: %s) with Explorepy (version: %s)",
             exploredesktop.__version__, explorepy.__version__)

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_FONT_DPI"] = "96"


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.Floor)
    app = QApplication(sys.argv)

    update = update_version()
    app.closeAllWindows()
    if update is False:
        window = MainWindow()
        window.show()

    update = update_version()
    if update is True:
        app.closeAllWindows()

    app.exec()
    del window, app


if __name__ == "__main__":
    print(
        "\nPlease do not close this command prompt window."
        "\nIf any error happens, you can use this window to send the report to Mentalab.\n")
    main()
