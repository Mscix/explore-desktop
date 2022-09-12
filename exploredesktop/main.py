# This Python file uses the following encoding: utf-8

import logging
import os
import sys

import explorepy
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication


import exploredesktop  # isort:skip
from exploredesktop import MainWindow  # isort:skip
from exploredesktop.version_update import update_version  # isort:skip


logger = logging.getLogger("explorepy.exploredesktop.main")
logger.debug("Starting ExploreDesktop (version: %s) with Explorepy (version: %s)",
             exploredesktop.__version__, explorepy.__version__)

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_FONT_DPI"] = "96"


def main():
    """Launch app"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.Floor)
    app = QApplication(sys.argv)

    update = update_version()
    if update is False:
        window = MainWindow()
        window.show()

    app.exec()
    del window, app


if __name__ == "__main__":
    print(
        "\nPlease do not close this command prompt window."
        "\nIf any error happens, you can use this window to send the report to Mentalab.\n")
    main()
