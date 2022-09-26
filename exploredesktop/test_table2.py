# # # pylint: disable=[missing-class-docstring, missing-function-docstring, invalid-name]
# # import sys

# # from PySide6 import QtCore, QtGui, QtWidgets
# # from PySide6.QtWidgets import QStyleOptionButton, QStyle
# # from PySide6.QtCore import Qt

# # class CustomDelegate(QtWidgets.QStyledItemDelegate):
# #     def initStyleOption(self, option, index):
# #         value = index.data(QtCore.Qt.CheckStateRole)
# #         if value is None:
# #             model = index.model()
# #             model.setData(index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
# #         super().initStyleOption(option, index)
# #         option.direction = QtCore.Qt.RightToLeft
# #         option.displayAlignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter

# #     # def paint(self, painter, option, index):
# #     #     """ Paint a checkbox without the label.
# #     #     """
# #     #     checked = bool(index.model().data(index, Qt.DisplayRole))
# #     #     opts = QStyleOptionButton()
# #     #     opts.state |= QStyle.State_Active
# #     #     if index.flags() & Qt.ItemIsEditable:
# #     #         opts.state |= QStyle.State_Enabled
# #     #     else:
# #     #         opts.state |= QStyle.State_ReadOnly
# #     #     if checked:
# #     #         opts.state |= QStyle.State_On
# #     #     else:
# #     #         opts.state |= QStyle.State_Off
# #     #     opts.rect = self.getCheckBoxRect(option)
# #     #     QtWidgets.QApplication.style().drawControl(QStyle.CE_CheckBox, opts, painter)

# #     # def getCheckBoxRect(self, option):
# #     #     """_summary_

# #     #     Args:
# #     #         option (_type_): _description_

# #     #     Returns:
# #     #         _type_: _description_
# #     #     """
# #     #     check_box_style_option = QStyleOptionButton()
# #     #     check_box_rect = QtWidgets.QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
# #     #     check_box_point = QtCore.QPoint (option.rect.x() +
# #     #                         option.rect.width() / 2 -
# #     #                         check_box_rect.width() / 2,
# #     #                         option.rect.y() +
# #     #                         option.rect.height() / 2 -
# #     #                         check_box_rect.height() / 2)
# #     #     return QtCore.QRect(check_box_point, check_box_rect.size())

# # class Mainwindow(QtWidgets.QMainWindow):
# #     def __init__(self):
# #         super().__init__()

# #         self.table = QtWidgets.QTableView()
# #         self.setCentralWidget(self.table)

# #         self.list = ["item_1", "item_2", "item_3"]
# #         self.data = [
# #             [1, "Blocks γ=500 GOST 31359-2007", self.list[0], 0.18, 0.22],
# #             [2, "Blocks γ=600 GOST 31359-2008", self.list[0], 0.25, 0.27],
# #             [3, "Insulation", self.list[0], 0.041, 0.042],
# #             [3, "Insulation", self.list[0], 0.041, 0.042],
# #         ]

# #         self.model = Materials(self.data)
# #         self.table.setModel(self.model)

# #         self.table.setSelectionBehavior(self.table.SelectRows)
# #         self.table.setSelectionMode(self.table.SingleSelection)

# #         for row in range(len(self.model._data)):
# #             index = self.table.model().index(row, 2)
# #             self.table.setIndexWidget(index, self.setting_combobox(index))

# #         delegate = CustomDelegate(self.table)
# #         self.table.setItemDelegateForColumn(4, delegate)

# #         self.resize(640, 480)

# #     def setting_combobox(self, index):
# #         widget = QtWidgets.QComboBox()
# #         list = self.list
# #         widget.addItems(list)
# #         widget.setCurrentIndex(0)
# #         widget.currentTextChanged.connect(
# #             lambda value: self.model.setData(index, value)
# #         )
# #         return widget


# # class Materials(QtCore.QAbstractTableModel):
# #     def __init__(self, materials=[[]], parent=None):
# #         super(Materials, self).__init__()
# #         self._data = materials

# #         self.check_states = dict()

# #     def rowCount(self, parent):
# #         return len(self._data)

# #     def columnCount(self, parent):
# #         return len(self._data[0])

# #     def data(self, index, role):

# #         if role == QtCore.Qt.DisplayRole:
# #             row = index.row()
# #             column = index.column()
# #             value = self._data[row][column]
# #             return value

# #         if role == QtCore.Qt.EditRole:
# #             row = index.row()
# #             column = index.column()
# #             value = self._data[row][column]
# #             return value

# #         if role == QtCore.Qt.FontRole:
# #             if index.column() == 0:
# #                 boldfont = QtGui.QFont()
# #                 boldfont.setBold(True)
# #                 return boldfont

# #         if role == QtCore.Qt.CheckStateRole:
# #             value = self.check_states.get(QtCore.QPersistentModelIndex(index))
# #             if value is not None:
# #                 return value

# #     def setData(self, index, value, role=QtCore.Qt.EditRole):
# #         if role == QtCore.Qt.EditRole:
# #             row = index.row()
# #             column = index.column()
# #             self._data[row][column] = value
# #             self.dataChanged.emit(index, index, (role,))
# #             return True
# #         if role == QtCore.Qt.CheckStateRole:
# #             self.check_states[QtCore.QPersistentModelIndex(index)] = value
# #             self.dataChanged.emit(index, index, (role,))
# #             return True
# #         return False

# #     def flags(self, index):
# #         return (
# #             QtCore.Qt.ItemIsEditable
# #             | QtCore.Qt.ItemIsEnabled
# #             | QtCore.Qt.ItemIsSelectable
# #             | QtCore.Qt.ItemIsUserCheckable
# #         )


# # if __name__ == "__main__":
# #     app = QtWidgets.QApplication([])
# #     application = Mainwindow()
# #     application.show()

# #     sys.exit(app.exec())

# from PySide6 import QtCore, QtGui, QtWidgets

# has_pandas = False
# try:
#   import pandas as pd
#   has_pandas = True
# except:
#   pass

# class TableModel(QtCore.QAbstractTableModel):
#     def __init__(self, parent=None, *args):
#         super(TableModel, self).__init__()
#         self.datatable = None
#         self.headerdata = None

#     def update(self, dataIn):
#         print ('Updating Model')
#         self.datatable = dataIn
#         print ('Datatable : {0}'.format(self.datatable))
#         if has_pandas:
#           headers = dataIn.columns.values
#         else:
#           headers = dataIn.columns
#         header_items = [
#                     str(field)
#                     for field in headers
#         ]
#         self.headerdata = header_items
#         print ('Headers')
#         print (self.headerdata)

#     def rowCount(self, parent=QtCore.QModelIndex()):
#         return len(self.datatable.index)

#     def columnCount(self, parent=QtCore.QModelIndex()):
#         if has_pandas:
#           return len(self.datatable.columns.values)
#         else:
#           return len(self.datatable.columns)

#     def data(self, index, role=QtCore.Qt.DisplayRole):
#         if role == QtCore.Qt.DisplayRole:
#             i = index.row()
#             j = index.column()
#             try:
#                 return str('{0}'.format(self.datatable.values[j][i]))
#             except:
#                 return None
#         else:
#             return None

#     def setData(self, index, value, role=QtCore.Qt.DisplayRole):
#         if index.column() == 4:
#             try:
#                 self.datatable.values[4][index.row()] = value
#             except:
#                 return value
#             # self.datatable.iset_value(index.row(), 4, value)
#             return value
#         return value

#     def headerData(self, col, orientation, role):
#         if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
#             return '{0}'.format(self.headerdata[col])

#     def flags(self, index):
#         if index.column() == 4:
#             return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
#         else:
#             return QtCore.Qt.ItemIsEnabled


# class TableView(QtWidgets.QTableView):
#     """
#     A simple table to demonstrate the QComboBox delegate.
#     """
#     def __init__(self, *args, **kwargs):
#         QtWidgets.QTableView.__init__(self, *args, **kwargs)
#         self.setItemDelegateForColumn(4, CheckBoxDelegate())


# class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
#     """
#     A delegate that places a fully functioning QCheckBox in every
#     cell of the column to which it's applied
#     """
#     def __init__(self):
#         super().__init__()

#     def createEditor(self, parent, option, index):
#         '''
#         Important, otherwise an editor is created if the user clicks in this cell.
#         ** Need to hook up a signal to the model
#         '''
#         return None

#     def paint(self, painter, option, index):
#         '''
#         Paint a checkbox without the label.
#         '''
#         print(f"{index.data()=}")
#         checked = True if index.data() == "True" else False

#         check_box_style_option = QtWidgets.QStyleOptionButton()

#         if (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
#             check_box_style_option.state |= QtWidgets.QStyle.State_Enabled
#         else:
#             check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

#         if checked:
#             check_box_style_option.state |= QtWidgets.QStyle.State_On
#         else:
#             check_box_style_option.state |= QtWidgets.QStyle.State_Off

#         check_box_style_option.rect = self.getCheckBoxRect(option)

#         # this will not run - hasFlag does not exist
#         #if not index.model().hasFlag(index, QtCore.Qt.ItemIsEditable):
#             #check_box_style_option.state |= QtGui.QStyle.State_ReadOnly

#         check_box_style_option.state |= QtWidgets.QStyle.State_Enabled

#         QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_CheckBox, check_box_style_option, painter)

#     def editorEvent(self, event, model, option, index):
#         '''
#         Change the data in the model and the state of the checkbox
#         if the user presses the left mousebutton or presses
#         Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
#         '''
#         print ('Check Box editor Event detected : ')
#         print (event.type())
#         if not (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
#             return False

#         print ('Check Box editor Event detected : passed first check')
#         # Do not change the checkbox-state
#         if event.type() == QtCore.QEvent.MouseButtonPress:
#           return False
#         if event.type() == QtCore.QEvent.MouseButtonRelease or event.type() == QtCore.QEvent.MouseButtonDblClick:
#             if event.button() != QtCore.Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
#                 return False
#             if event.type() == QtCore.QEvent.MouseButtonDblClick:
#                 return True
#         elif event.type() == QtCore.QEvent.KeyPress:
#             if event.key() != QtCore.Qt.Key_Space and event.key() != QtCore.Qt.Key_Select:
#                 return False
#         else:
#             return False

#         # Change the checkbox-state
#         self.setModelData(None, model, index)
#         return True

#     def setModelData (self, editor, model, index):
#         '''
#         The user wanted to change the old state in the opposite.
#         '''
#         print ('SetModelData')
#         newValue = True if index.data() == "True" else False
#         print ('New Value : {0}'.format(newValue))
#         model.setData(index, newValue, QtCore.Qt.EditRole)

#     def getCheckBoxRect(self, option):
#         check_box_style_option = QtWidgets.QStyleOptionButton()
#         check_box_rect = QtWidgets.QApplication.style().subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
#         check_box_point = QtCore.QPoint (option.rect.x() +
#                             option.rect.width() / 2 -
#                             check_box_rect.width() / 2,
#                             option.rect.y() +
#                             option.rect.height() / 2 -
#                             check_box_rect.height() / 2)
#         return QtCore.QRect(check_box_point, check_box_rect.size())


# ###############################################################################################################################
# class Dataframe(dict):
#   def __init__(self, columns, values):
#     if len(values) != len(columns):
#       raise Exception("Bad values")
#     self.columns = columns
#     self.values = values
#     self.index = values[0]
#     super(Dataframe, self).__init__(dict(zip(columns, values)))
#     pass

#   def iget_value(self, i, j):
#     return(self.values[j][i])

#   def iset_value(self, i, j, value):
#     self.values[j][i] = value


# if __name__=="__main__":
#     from sys import argv, exit

#     class Widget(QtWidgets.QWidget):
#         """
#         A simple test widget to contain and own the model and table.
#         """
#         def __init__(self, parent=None):
#             QtWidgets.QWidget.__init__(self, parent)

#             l=QtWidgets.QVBoxLayout(self)
#             cdf = self.get_data_frame()
#             self._tm=TableModel(self)
#             self._tm.update(cdf)
#             self._tv=TableView(self)
#             self._tv.setModel(self._tm)
#             for row in range(0, self._tm.rowCount()):
#                 self._tv.openPersistentEditor(self._tm.index(row, 4))
#             self.setGeometry(300, 300, 550, 200)
#             l.addWidget(self._tv)

#         def get_data_frame(self):
#             if has_pandas:
#               df = pd.DataFrame({'Name':['a','b','c','d'],
#               'First':[2.3,5.4,3.1,7.7], 'Last':[23.4,11.2,65.3,88.8], 'Class':[1,1,2,1], 'Valid':[True, False, True, False]})
#             else:
#               columns = ['Name', 'First', 'Last', 'Class', 'Valid']
#               values = [['a','b','c','d'], [2.3,5.4,3.1,7.7], [23.4,11.2,65.3,88.8], [1,1,2,1], [True, False, True, False]]
#               df = Dataframe(columns, values)
#             return df

#     a=QtWidgets.QApplication(argv)
#     w=Widget()
#     w.show()
#     w.raise_()
#     exit(a.exec_())

from PySide6 import (
    QtCore,
    QtWidgets
)
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QTableView
)


class CheckBoxDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox cell of the column to which it's applied.
    """
    def __init__(self, parent):
        QtWidgets.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        self.drawCheck(painter, option, option.rect, QtCore.Qt.Unchecked if int(index.data()) == 0 else QtCore.Qt.Checked)

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable. Otherwise do nothing.
        '''
        if not int(index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            return False

        if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
            # Change the checkbox-state
            self.setModelData(None, model, index)
            return True

        return False


    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        model.setData(index, 1 if int(index.data()) == 0 else 0, QtCore.Qt.EditRole)



if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    model = QStandardItemModel(4, 3)
    tableView = QTableView()
    tableView.setModel(model)

    delegate = CheckBoxDelegate(None)
    tableView.setItemDelegateForColumn(1, delegate)
    for row in range(4):
        for column in range(3):
            index = model.index(row, column, QModelIndex())
            model.setData(index, 1)

    tableView.setWindowTitle("Check Box Delegate")
    tableView.show()
    sys.exit(app.exec_())