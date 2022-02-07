# This Python file uses the following encoding: utf-8
import sys
import explorepy
import logging
from exploregui import MainWindow
from PySide6.QtWidgets import QApplication

import exploregui

logger = logging.getLogger("explorepy")
logger.debug("Starting ExploreGUI - version: %s", exploregui.__version__)
# print(explorepy.__doc__) uncomment to avoid flake8(F401)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    print(
        "\nPlease do not close this command prompt window."
        "\nIf any error happens, you can use this window to send the report to Mentalab.\n")
    main()
