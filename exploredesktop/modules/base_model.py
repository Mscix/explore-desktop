"""Implement base model and define custom PySide6 signals used in GUI

Classes:
    BaseModel
    SignalsConatiner
"""
from enum import Enum
from PySide6.QtCore import (
    QObject,
    Signal
)

from exploredesktop.modules.explore_interface import ExploreInterface  # isort: skip


class SignalsContainer(QObject):
    """Class containig signals used in the GUI
    """
    # Impedance related signals
    impedanceChanged = Signal(dict)
    btnImpMeasureChanged = Signal(str)
    displayDefaultImp = Signal()

    # Footer related signals
    envInfoChanged = Signal(dict)
    devInfoChanged = Signal(dict)
    connectionStatus = Signal(Enum)

    # BT related signals
    btnConnectChanged = Signal(str)


class BaseModel():
    """Base class for models
    """
    signals = SignalsContainer()
    explorer = ExploreInterface()

    def __init__(self) -> None:
        pass

    def get_signals(self):
        """Returns model signals

        Returns:
            SignalsContainer: QObject containing signals used in GUI
        """
        return self.signals

    def get_explorer(self):
        """Returns explore interface

        Returns:
            ExploreInterface: interface class for explore
        """
        return self.explorer
