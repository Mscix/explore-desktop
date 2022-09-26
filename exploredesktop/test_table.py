# pylint: disable=invalid-name
import sys

from exploredesktop.modules.app_settings import (
    ExGModes,
    GUISettings,
    Settings
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)


'''class MyApp(QWidget):
    """_summary_

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self) -> None:
        """_summary_
        """
        super().__init__()
        self.window_width, self.window_height = 700, 500
        self.resize(700, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.btn = QPushButton("Retrieve Values", clicked=self.retrieve_values)
        self.layout.addWidget(self.btn)

        self.table = QTableWidget(3, 3)
        self.layout.addWidget(self.table)
        # self.btn.clicked.connect(self.retrieve_values)

        for row in range(3):
            for col in range(3):
                if col % 3 == 0:
                    item = QTableWidgetItem(f"Item {row} - {col}")
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    item.setCheckState(Qt.CheckState.Checked)
                    self.table.setItem(row, col, item)

                else:
                    self.table.setItem(row, col, QTableWidgetItem(f"Item {row} - {col}"))

    def retrieve_values(self):
        """
        ds
        """
        print("fdsd")
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).checkState() == Qt.Checked:
                print( [self.table.item(row,col).text() for col in range(self.table.columnCount())])



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myApp = MyApp()
    myApp.show()

    sys.exit(app.exec())
'''
import sys

import numpy as np
from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets
)
from PySide6.QtCore import (
    QMetaType,
    QModelIndex,
    Qt
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QPushButton,
    QSpinBox,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)


class TableModel(QtCore.QAbstractTableModel):
    """_summary_
    """
    def __init__(self, data):
        """_summary_

        Args:
            data (_type_): _description_
        """
        super(TableModel, self).__init__()
        self._data = data

        # column description
        self.columns = [{'property':'input', 'header':'Channel', 'edit':False, 'editor':'default'},
                        {'property':'enable', 'header':'Enable', 'edit':True, 'editor':'checkbox'},
                        {'property':'name', 'header':'Name', 'edit':True, 'editor':'default'},
                        {'property':'type', 'header':'Type', 'edit':True, 'editor':'combobox'},
                       ]

    def change_column_edit(self, col_name, new_val):
        next(item for item in self.columns if item["property"] == col_name)["edit"] = new_val

    def change_column_editor(self, col_name, new_val):
        next(item for item in self.columns if item["property"] == col_name)["editor"] = new_val


    def data(self, index, role):
        """_summary_
        """
        value = self._getitem(index.row(), index.column())

        if (role == Qt.DisplayRole) or (role == Qt.EditRole):
            return value

        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            display_role_value = self._data[index.row()][index.column()]
            print(f"{display_role_value=}")
            return display_role_value

    def rowCount(self, index):
        """_summary_
        """
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        """_summary_
        """
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

    def headerData(self, col, orientation, role):
        ''' Abstract method from QAbstactItemModel to get the column header
        @param col: column number
        @param orientation: Qt.Horizontal = column header, Qt.Vertical = row header
        @param role: given role for the item referred to by the index
        @return: header
        '''
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
                return self.columns[col]['header']

    def comboBoxList(self, column):
        ''' Get combo box item list for column 'highpass' or 'lowpass'
        @param column: table column number
        @return: combo box item list as QVariant 
        '''
        if column >= len(self.columns):
            return None
        if self.columns[column]['property'] == 'type':
            return ExGModes.all_values()
        if self.columns[column]['property'] == 'name':
            return GUISettings.ELECTRODES_10_20

    def editorType(self, column):
        ''' Get the columns editor type from column description
        @param column: table column number
        @return: editor type as QVariant (string)
        ''' 
        if column >= len(self.columns):
            return None
        return str(self.columns[column]['editor'])
    
    def is_editable(self, column):
        ''' Get the columns editor type from column description
        @param column: table column number
        @return: editor type as QVariant (string)
        ''' 
        if column >= len(self.columns):
            return None
        return str(self.columns[column]['edit'])

    def flags(self, index):
        ''' Abstract method from QAbstactItemModel
        @param index: QModelIndex table cell reference
        @return: the item flags for the given index
        '''
        if not index.isValid():
            return Qt.ItemIsEnabled
        if not self.columns[index.column()]['edit']:
            return Qt.NoItemFlags
        if self.columns[index.column()]['header'] == "Enable":
            n_active = sum(item["enable"] for item in self._data)
            if n_active == 1:
                ch_active = next(item for item in self._data if item["enable"] == 1)["input"]
                row_active = int(ch_active.replace("ch", "")) - 1
                if index.column() == 1 and index.row() == row_active:
                    return Qt.NoItemFlags

        return QtCore.QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable

    def _setitem(self, row, column, value):
        ''' Set amplifier property item based on table row and column
        @param row: row number
        @param column: column number
        @param value: QVariant value object
        @return: True if property value was set, False if not
        ''' 
        if (row >= len(self._data)) or (column >= len(self.columns)):
            return False
        # get channel properties
        property = self._data[row]
        # get property name from column description
        property_name = self.columns[column]['property']
        # set channel property
        if property_name == 'enable':
            property["enable"] = value
            return True

        if property_name == 'name':
            n = value
            if "".join(n.split()) == "":
                return False
            property["name"] = value
            return True

        if property_name == 'type':
            n = value
            property["type"] = value
            return True

        return False

    def _getitem(self, row, column):
        ''' Get amplifier property item based on table row and column
        @param row: row number
        @param column: column number
        @return:  QVariant property value
        ''' 
        if (row >= len(self._data)) or (column >= len(self.columns)):
            return None
        
        # get channel properties
        property = self._data[row]
        # print(f"{property=}")  # {'input': 'ch5', 'enable': True, 'name': 'custom', 'type': 'EEG'}
        # get property name from column description
        property_name = self.columns[column]['property']
        # get property value
        if property_name == 'input':
            d = str(property["input"])
        elif property_name == 'enable':
            d = str(property["enable"])
        elif property_name == 'name':
            d = str(property["name"])
        elif property_name == 'type':
            d = str(property["type"])
        else:
            d = None
        return d

    def setData(self, index, value, role):
        ''' Abstract method from QAbstactItemModel to set cell data based on role
        @param index: QModelIndex table cell reference
        @param value: QVariant new cell data
        @param role: given role for the item referred to by the index
        @return: true if successful; otherwise returns false.
        '''
        if index.isValid(): 
            if role == Qt.EditRole:
                if not self._setitem(index.row(), index.column(), value):
                    return False
                return True
            elif role == Qt.CheckStateRole:
                if not self._setitem(index.row(), index.column(), Qt.QVariant(value == Qt.Checked)):
                    return False
                return True
        return False


from PySide6.QtWidgets import (
    QStyle,
    QStyleOptionButton
)


class _ConfigItemDelegate(QStyledItemDelegate):  
    ''' Combobox item editor
    '''
    def __init__(self):
        super().__init__()
        
    def createEditor(self, parent, option, index):
        """
        ds
        """

        if index.model().editorType(index.column()) == 'combobox':
            combobox = QComboBox(parent)
            combobox.addItems(index.model().comboBoxList(index.column()))
            combobox.setEditable(False)
            # self.connect(combobox, Qt.SIGNAL('activated(int)'), self.emitCommitData)
            return combobox

        if index.model().editorType(index.column()) == 'checkbox':
            return None
        

        return QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        """_summary_

        Args:
            editor (_type_): _description_
            index (_type_): _description_
        """
        if index.model().columns[index.column()]['editor'] == 'combobox':
            text = index.model().data(index, Qt.DisplayRole)
            i = editor.findText(text)
            if i == -1:
                i = 0
            editor.setCurrentIndex(i)
        QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        """_summary_

        Args:
            editor (_type_): _description_
            model (_type_): _description_
            index (_type_): _description_
        """
        if model.columns[index.column()]['editor'] == 'combobox':
            model.setData(index, editor.currentText(), Qt.EditRole)
            # model.reset()
        QStyledItemDelegate.setModelData(self, editor, model, index)




class _CheckBoxItemDelegate(QStyledItemDelegate):  
    ''' Combobox item editor
    '''
    def __init__(self):
        super().__init__()
        
    def createEditor(self, parent, option, index):
        """
        ds
        """
        if index.model().editorType(index.column()) == 'checkbox':
            # checkbox = QCheckBox(parent)
            # print(index.data())
            # checkbox.setEnabled(eval(index.data()))
            # # checkbox.setEditable(False)
            # # self.connect(combobox, Qt.SIGNAL('activated(int)'), self.emitCommitData)
            # return checkbox
            return None
        
        return QStyledItemDelegate.createEditor(self, parent, option, index)

    def paint(self, painter, option, index):
        '''
        Paint a checkbox without the label.
        '''
        if index.model().editorType(index.column()) == 'checkbox':
            # checked = eval(index.data())
            checked = index.model().data(index, QtCore.Qt.DisplayRole) == 'True'
            check_box_style_option = QStyleOptionButton()

            if (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
                check_box_style_option.state |= QStyle.State_Enabled
            else:
                check_box_style_option.state |= QStyle.State_ReadOnly

            if checked:
                check_box_style_option.state |= QStyle.State_On
            else:
                check_box_style_option.state |= QStyle.State_Off

            check_box_style_option.rect = self.getCheckBoxRect(option)

            # this will not run - hasFlag does not exist
            #if not index.model().hasFlag(index, QtCore.Qt.ItemIsEditable):
                #check_box_style_option.state |= QtGui.QStyle.State_ReadOnly

            check_box_style_option.state |= QStyle.State_Enabled

            QApplication.style().drawControl(QStyle.CE_CheckBox, check_box_style_option, painter)


    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton or presses
        Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
        '''
        print ('Check Box editor Event detected : ', event.type())
        if not (index.flags() and QtCore.Qt.ItemIsEditable) > 0:
            return False

        print ('Check Box editor Event detected : passed first check')
        # Do not change the checkbox-state
        if event.type() == QtCore.QEvent.MouseButtonPress:
          return False
        if event.type() == QtCore.QEvent.MouseButtonRelease or event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() != QtCore.Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.position().toPoint()):
                return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                return True
        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() != QtCore.Qt.Key_Space and event.key() != QtCore.Qt.Key_Select:
                return False
        else:
            return False

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True


    def setEditorData(self, editor, index) -> None:
        text = index.model().data(index, Qt.EditRole)
        print(f"{text=}")
        QStyledItemDelegate.setEditorData(editor, index)


    def setModelData(self, editor, model, index):
        """_summary_

        Args:
            editor (_type_): _description_
            model (_type_): _description_
            index (_type_): _description_
        """
        if model.columns[index.column()]['editor'] == 'checkbox':
            print ('SetModelData')
            print(f"{index.data()=}")
            newValue = not eval(index.data())
            print ('New Value : {0}'.format(newValue))
            model.setData(index, newValue, QtCore.Qt.EditRole)
        QStyledItemDelegate.setModelData(self, editor, model, index)


    def getCheckBoxRect(self, option):
        """_summary_

        Args:
            option (_type_): _description_

        Returns:
            _type_: _description_
        """
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QtCore.QPoint (option.rect.x() +
                            option.rect.width() / 2 -
                            check_box_rect.width() / 2,
                            option.rect.y() +
                            option.rect.height() / 2 -
                            check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())


class SpinBoxDelegate(QStyledItemDelegate):
    """

    Args:
        QStyledItemDelegate (_type_): _description_
    """
    def __init__(self) -> None:
        super().__init__()

    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setMaximum(100)
        return editor

    def setEditorData(self, editor, index) -> None:
        # value = index.model().data(index, Qt.EditRole).toBool()
        value = int(index.model().data(index, Qt.EditRole))
        spinBox = QSpinBox(editor)
        spinBox.setValue(value)

    def setModelData(self, editor, model, index) -> None:
        spinBox = QSpinBox(editor)
        spinBox.interpretText()
        value = spinBox.value()
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index) -> None:
        editor.setGeometry(option.rect)


from PySide6.QtCore import (
    QEvent,
    QPoint,
    QRect,
    Qt
)


class CheckBoxDelegateQt(QStyledItemDelegate):
    """ Delegate for editing bool values via a checkbox with no label centered in its cell.
    Does not actually create a QCheckBox, but instead overrides the paint() method to draw the checkbox directly.
    Mouse events are handled by the editorEvent() method which updates the model's bool value.
    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """ Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """ Paint a checkbox without the label.
        """
        checked = bool(index.model().data(index, Qt.DisplayRole))
        opts = QStyleOptionButton()
        opts.state |= QStyle.State_Active
        if index.flags() & Qt.ItemIsEditable:
            opts.state |= QStyle.State_Enabled
        else:
            opts.state |= QStyle.State_ReadOnly
        if checked:
            opts.state |= QStyle.State_On
        else:
            opts.state |= QStyle.State_Off
        opts.rect = self.getCheckBoxRect(option)
        QApplication.style().drawControl(QStyle.CE_CheckBox, opts, painter)

    def editorEvent(self, event, model, option, index):
        """ Change the data in the model and the state of the checkbox if the
        user presses the left mouse button and this cell is editable. Otherwise do nothing.
        """
        if not (index.flags() & Qt.ItemIsEditable):
            return False
        if event.button() == Qt.LeftButton:
            print("Left button event")
            if event.type() == QEvent.MouseButtonRelease:
                print("Button release event")
                if self.getCheckBoxRect(option).contains(event.position().toPoint()):
                    print("Event contains position")
                    self.setModelData(None, model, index)
                    print("Data set")
                    return True
            elif event.type() == QEvent.MouseButtonDblClick:
                print("Double clicke event")
                if self.getCheckBoxRect(option).contains(event.position().toPoint()):
                    return True
        return False

    def setModelData(self, editor, model, index):
        """ Toggle the boolean state in the model.
        """
        checked = not bool(index.model().data(index, Qt.DisplayRole))
        model.setData(index, checked, Qt.EditRole)

    def getCheckBoxRect(self, option):
        """ Get rect for checkbox centered in option.rect.
        """
        # Get size of a standard checkbox.
        opts = QStyleOptionButton()
        checkBoxRect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, opts, None)
        # Center checkbox in option.rect.
        x = option.rect.x()
        y = option.rect.y()
        w = option.rect.width()
        h = option.rect.height()
        checkBoxTopLeftCorner = QPoint(x + w / 2 - checkBoxRect.width() / 2, y + h / 2 - checkBoxRect.height() / 2)
        return QRect(checkBoxTopLeftCorner, checkBoxRect.size())


from exploredesktop.modules.ui.ui_main_window_redisign import Ui_MainWindow


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


class MainWindow(QtWidgets.QMainWindow):
    """_summary_

    Args:
        QtWidgets (_type_): _description_
    """
    def __init__(self):
        super().__init__()

        # self.table = QtWidgets.QTableView()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.table = self.ui.table_settings
        self.ui.stackedWidget.setCurrentWidget(self.ui.page__testing)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        data = [
          ["Ch1", True, "custom", "EEG"],
          ["Ch1", True, "custom", "EEG"],
          ["Ch1", True, "custom", "EEG"],
          ["Ch1", True, "custom", "EEG"],
          ["Ch1", True, "custom", "EEG"],
        ]
        # data = {"ch1": {"enabled": True, }}
        data = [
            {"input": "ch1", "enable": 1, "name": "ch1", "type": "EEG"},
            {"input": "ch2", "enable": 1, "name": "ch2", "type": "EEG"},
            {"input": "ch3", "enable": 1, "name": "ch3", "type": "EEG"},
            {"input": "ch4", "enable": 1, "name": "ch4", "type": "EEG"},
            {"input": "ch5", "enable": 1, "name": "ch5", "type": "EEG"}
        ]

        stylesheet = """
        QTableWidget::item:read-only {
            background-color: rgb(255, 0, 0) 
        }
        """
        # self.table.setStyleSheet(stylesheet)
        self.model = TableModel(data)
        self.table.setModel(self.model)
        self.table.setItemDelegate(_ConfigItemDelegate())
        
        def on_table_click(data: list, table=self.table) -> None:
    
            if data.column() != 1:
                return
            n_active = sum(item["enable"] for item in data.model()._data)
            if n_active == 1:
                # print(data)
                # print(data.model()._data)
                ch_active = next(item for item in data.model()._data if item["enable"] == 1)["input"]
                col_active = 1
                row_active = int(ch_active.replace("ch", "")) - 1
                # active_item = table.model().index(row_active, col_active)
                # active_item.setFlags(Qt.NoItemFlags)
                print()
                print()

                # data.model().change_column_edit("Enable", False)
        self.table.clicked.connect(on_table_click)
        # self.table.setItemDelegateForColumn(1, _CheckBoxItemDelegate())
        self.ui.btn_apply_settings_2.clicked.connect(lambda: print(self.model._data))
        self.table.setItemDelegateForColumn(1, CheckBoxDelegate(None))

        self.ui.cb_multitype_signal.stateChanged.connect(self.multisignal_clicked)

        self.ui.dropdown_signal_type.addItems(ExGModes.all_values())
        self.ui.dropdown_signal_type.currentTextChanged.connect(self.signal_type_changed)
    
    def multisignal_clicked(self):
        print(f"{self.ui.cb_multitype_signal.isChecked()=}")
        multitype = self.ui.cb_multitype_signal.isChecked()

        self.ui.dropdown_signal_type.setHidden(multitype)
        self.table.model().change_column_edit("type", multitype)
        self.table.viewport().update()

    def signal_type_changed(self):
        if self.ui.dropdown_signal_type.currentText() == ExGModes.EEG.value:
            new_value = ExGModes.EEG.value
            print("All signals exg")
        else:
            new_value = ExGModes.ECG.value
            print("All signals eCg")

        for ch_dict in self.table.model()._data:
            ch_dict["type"] = new_value
        self.table.viewport().update()

app=QtWidgets.QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec()