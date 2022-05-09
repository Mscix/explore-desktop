
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QIntValidator

from exploredesktop.modules.app_settings import (  # isort: skip
    Messages,
    Stylesheets
)
from exploredesktop.modules.base_data_module import (  # isort: skip
    BasePlots,
    DataContainer
)
from exploredesktop.modules.tools import display_msg  # isort: skip


class MarkerData(DataContainer):
    def __init__(self) -> None:
        super().__init__()
        self.mrk_plot = {'t': [], 'code': [], 'lines': []}
        self.mrk_replot = {'t': [], 'code': [], 'lines': []}

    def callback(self, packet):
        """
        Get marker data from packet and emit signal
        """
        timestamp, code = packet.get_data()
        if DataContainer.vis_time_offset is None:
            DataContainer.vis_time_offset = timestamp[0]
        time_vector = list(np.asarray(timestamp) - DataContainer.vis_time_offset)
        data = [time_vector[0], str(code[0]), False]
        self.signals.mkrAdd.emit(data)

    @Slot(list)
    def add_mkr(self, data: list) -> None:
        """Add marker data to marker dictionary

        Args:
            data (list): list of data containing marker time, code and whether to replot
        """
        t_point, code, replot = data
        if replot is False:
            mrk_dict = self.mrk_plot
        else:
            mrk_dict = self.mrk_replot

        mrk_dict['t'].append(t_point)
        mrk_dict['code'].append(code)
        self.signals.mkrPlot.emit(data)

    @Slot(float)
    def add_mkr_replot(self, t_thr: float) -> None:
        for idx_t in range(len(self.mrk_plot['t'])):
            if self.mrk_plot['t'][idx_t] < t_thr:
                t_point = self.mrk_plot['t'][idx_t] + self.timescale
                code = self.mrk_plot['code'][idx_t]
                self.mrk_replot['t'].append(t_point)
                self.mrk_replot['code'].append(code)
                self.signals.mkrPlot.emit([t_point, code, True])


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
    def plot_marker(self, data):
        """
        Plot and update marker data
        """
        t_point, code, replot = data
        if replot is False:
            mrk_dict = self.model.mrk_plot
            color = Stylesheets.MARKER_LINE_COLOR
        else:
            mrk_dict = self.model.mrk_replot
            color = Stylesheets.MARKER_LINE_COLOR_ALPHA

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

        mrk_dict['lines'].append(lines)
        if replot:
            idx_remove = self.model.mrk_plot['t'].index([t_point - self.model.timescale])
            for line in self.model.mrk_plot['lines'][idx_remove]:
                self.ui.plot_orn.getItem(0, 0).removeItem(line)
                self.ui.plot_orn.getItem(1, 0).removeItem(line)
                self.ui.plot_orn.getItem(2, 0).removeItem(line)
                self.ui.plot_exg.removeItem(line)

    @Slot(float)
    def remove_old_item(self, last_t: float) -> None:
        """Remove old item from the plot

        Args:
            last_t (float): last time point
        """
        item_dict = self.model.mrk_replot
        item_type = 'lines'
        to_remove = super().remove_old_item(item_dict, last_t, item_type)
        self.model.mrk_replot, to_remove = self.model.remove_dict_item(item_dict, item_type, to_remove)
