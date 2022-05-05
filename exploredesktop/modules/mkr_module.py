
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
        self.signals.mkrChanged.emit(data)

    @Slot(list)
    def add_mkr(self, data):
        # print("\nAdding mkr")
        t_point, code, replot = data
        if replot is False:
            mrk_dict = self.mrk_plot
        else:
            mrk_dict = self.mrk_replot

        mrk_dict['t'].append(t_point)
        mrk_dict['code'].append(code)
        # print(f"{self.mrk_plot=}")
        self.signals.mkrPlot.emit(data)

    @Slot(float)
    def add_mkr_replot(self, t_thr):
        # print("\nAdding mkr to replot dict")
        for idx_t in range(len(self.mrk_plot['t'])):
            if self.mrk_plot['t'][idx_t] < t_thr:
                # self.ui.plot_exg.removeItem(self.mrk_plot['line'][idx_t])
                t_point = self.mrk_plot['t'][idx_t] + self.timescale
                code = self.mrk_plot['code'][idx_t]
                # new_data = [
                #     self.mrk_plot['t'][idx_t] + self.get_timeScale(),
                #     self.mrk_plot['code'][idx_t]
                # ]
                # self.plot_mkr(new_data, replot=True)
                self.mrk_replot['t'].append(t_point)
                self.mrk_replot['code'].append(code)
                self.signals.mkrPlot.emit([t_point, code, True])
        # print(f"{self.mrk_replot=}")

    def remove_dict_item(self, item_dict, item_type, to_remove):
        # TODO: move to base class

        if len(to_remove) < 1:
            return item_dict, to_remove
        print("in remove dict item")
        print(f"before {len(to_remove)=}")
        if item_type == 'lines':
            key = 'code'
        else:
            key = 'r_peak'

        for item in to_remove:
            item_dict['t'].remove(item[0])
            item_dict[key].remove(item[1])
            item_dict[item_type].remove(item[2])
            to_remove.remove(item)
        print(f"after {len(to_remove)=}")
        return item_dict, to_remove


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
        # TODO!!!: Split into set marker (handling dict) and plot_marker(add to plot)

        t_point, code, replot = data
        if replot is False:
            mrk_dict = self.model.mrk_plot
            color = Stylesheets.MARKER_LINE_COLOR
        else:
            mrk_dict = self.model.mrk_replot
            color = Stylesheets.MARKER_LINE_COLOR_ALPHA
        # r = "plot" if not replot else "replot"
        # print(f"\n{r}ing marker {t_point=}, {code=}")
        # mrk_dict['t'].append(t_point)
        # mrk_dict['code'].append(code)
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
    def remove_old_item(self, last_t) -> list:
        # TODO also remove item from dict
        item_dict = self.model.mrk_replot
        item_type = 'lines'
        to_remove = super().remove_old_item(item_dict, last_t, item_type)
        self.model.mrk_replot, to_remove = self.model.remove_dict_item(item_dict, item_type, to_remove)
