
import numpy as np
from exploredesktop.modules.app_settings import Messages, Stylesheets
from exploredesktop.modules.base_data_module import BasePlots, DataContainer
from exploredesktop.modules.tools import display_msg
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Slot
import pyqtgraph as pg


class MarkerData(DataContainer):
    def __init__(self) -> None:
        super().__init__()
        self.mrk_plot = {'t': [], 'code': [], 'line': []}
        self.mrk_replot = {'t': [], 'code': [], 'line': []}

    def callback(self, packet):
        """
        Get marker data from packet and emit signal
        """
        timestamp, code = packet.get_data()
        if DataContainer.vis_time_offset is None:
            DataContainer.vis_time_offset = timestamp[0]
        time_vector = list(np.asarray(timestamp) - DataContainer.vis_time_offset)
        data = [time_vector[0], str(code[0])]
        self.signals.mkrChanged.emit(data)


class MarkerPlot(BasePlots):
    def __init__(self, ui) -> None:
        super().__init__(ui)
        self.model = MarkerData()
        self.plots_list = [
            self.ui.plot_exg,
            self.ui.plot_orn.getItem(0, 0),
            self.ui.plot_orn.getItem(1, 0),
            self.ui.plot_orn.getItem(2, 0)
        ]
        self.setup_validators()

    def setup_ui_connections(self):
        self.ui.btn_marker.clicked.connect(self.set_marker)
        self.ui.value_event_code.returnPressed.connect(self.set_marker)

    def setup_validators(self):
        # validators
        self.ui.value_event_code.setValidator(QIntValidator(0, 65535))
        self.ui.btn_marker.setEnabled(self.ui.value_event_code.text() != "")
        self.ui.value_event_code.textChanged[str].connect(lambda: self.ui.btn_marker.setEnabled(
            (self.ui.value_event_code.text() != "") or (
                (self.ui.value_event_code.text().isnumeric()) and (8 <= int(self.ui.value_event_code.text())))
        )
        )

    def set_marker(self):
        """
        Get the value for the event code from the GUI and set the event.
        """
        # event_code = int(value)
        # TODO catch input here, emit signal and asign marker in data
        event_code = int(self.ui.value_event_code.text())
        if event_code > 65535 or event_code < 0:
            self.display_msg(msg_text=Messages.INVALID_MARKER)
            return
        try:
            self.model.explorer.set_marker(event_code)
        except ValueError as error:
            display_msg(msg_text=str(error))

    @Slot(list)
    def plot_marker(self, data, replot=False):
        """
        Plot and update marker data
        """
        # TODO!!!: Split into set marker (handling dict) and plot_marker(add to plot)

        t_point, code = data
        if replot is False:
            mrk_dict = self.model.mrk_plot
            color = Stylesheets.MARKER_LINE_COLOR
        else:
            mrk_dict = self.model.mrk_replot
            color = Stylesheets.MARKER_LINE_COLOR_ALPHA

        mrk_dict['t'].append(t_point)
        mrk_dict['code'].append(code)
        pen_marker = pg.mkPen(color=color, dash=[4, 4])
        lines = []
        line = self.ui.plot_orn.getItem(0, 0).addLine(t_point, label=code, pen=pen_marker)
        lines.append(line)
        line = self.ui.plot_orn.getItem(1, 0).addLine(t_point, label=code, pen=pen_marker)
        lines.append(line)
        line = self.ui.plot_orn.getItem(2, 0).addLine(t_point, label=code, pen=pen_marker)
        lines.append(line)
        line = self.ui.plot_exg.addLine(t_point, label=code, pen=pen_marker)
        lines.append(line)
        mrk_dict['line'].append(lines)
