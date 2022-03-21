from exploredesktop.modules.imp_functions import ImpTableModel
from PySide6 import QtWidgets
import sys

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.impTable = QtWidgets.QTableView()
        # data = [5 for i in range(1,9)]
        # print(data)
        self.model = ImpTableModel()
        self.impTable.setModel(self.model)
        self.impTable.setStyleSheet("QHeaderView {background-color: transparent;}")
        self.setCentralWidget(self.impTable)


app=QtWidgets.QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()