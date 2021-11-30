# This Python file uses the following encoding: utf-8
import sys

from exploregui import MainWindow
from PySide6.QtWidgets import QApplication
import faulthandler


def main():
    faulthandler.enable()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
