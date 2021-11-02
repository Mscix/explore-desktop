'''import explorepy as xpy
import time
explorer = xpy.Explore()
explorer.connect(device_name="Explore_CA18")
stream_processor = explorer.stream_processor
stream_processor.add_filter(cutoff_freq=50, filter_type='notch')
time.sleep(5)
stream_processor.add_filter(cutoff_freq=None, filter_type='notch')'''

import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QMovie

class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        self.label_animation = QLabel(self)

        self.movie = QMovie('images/loading.gif')
        self.label_animation.setMovie(self.movie)

        timer = QTimer(self)
        self.startAnimation()
        timer.singleShot(2000, self.stopAnimation)

        self.show()

    def startAnimation(self):
        self.movie.start()

    def stopAnimation(self):
        self.movie.stop()
        self.close()

