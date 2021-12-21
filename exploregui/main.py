# This Python file uses the following encoding: utf-8
import logging
import sys

from exploregui import MainWindow
from PySide6.QtWidgets import QApplication
import faulthandler
import cgitb 
import cProfile

from exploregui.modules.app_settings import Settings


def main():
    faulthandler.enable()
    cgitb.enable(format = 'text')
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# conda activate gui3810 && cd Documents/Mentalab/explorepy-gui/exploregui && python main.py
if __name__ == "__main__":
    # main()
    logging.basicConfig(level=logging.INFO)
    cProfile.run("main()", sort="tottime", filename="prof_results")
    import pstats, io, datetime
    s = io.StringIO()
    p = pstats.Stats('prof_results', stream=s)
    p.sort_stats('cumulative').print_stats()
    file_name = Settings.TEST+'_stats.txt'

    with open(file_name, 'w+') as f:
        f.write(s.getvalue())
