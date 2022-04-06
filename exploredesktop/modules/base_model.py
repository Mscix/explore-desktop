import explorepy
from PySide6.QtCore import (
    QObject,
    Signal
)


class SignalsContainer(QObject):
    """Class containig signals used in the GUI
    """
    # Impedance related signals
    impedanceChanged = Signal(dict)
    btnImpMeasureChanged = Signal(str)
    displayDefaultImp = Signal()

    # Footer related signals
    envInfoChanged = Signal(dict)
    connectionStatus = Signal(str)


class BaseModel():
    """Base class for models
    """
    signals = SignalsContainer()
    # TODO: change to explore interface
    explorer = explorepy.Explore()

    def __init__(self) -> None:
        # TODO: the connection will be handled by the Bluetooh module
        dev_name = input("Device name to connect: ")
        self.explorer.connect(device_name=dev_name)

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