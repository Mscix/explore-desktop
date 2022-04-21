
from abc import abstractmethod
import logging
import numpy as np
from exploredesktop.modules import BaseModel
from exploredesktop.modules.app_settings import ORNLegend, Settings, Stylesheets
import pyqtgraph as pg

from PySide6.QtGui import (
    QIntValidator
)

logger = logging.getLogger("explorepy." + __name__)


class DataContainer(BaseModel):
    """_summary_
    """
    def __init__(self) -> None:
        super().__init__()
        self.plot_data = {}
        self.t_plot_data = np.array([])

        self.pointer = {}

        self.mrk_plot = {'t': [], 'code': [], 'line': []}
        self.mrk_replot = {'t': [], 'code': [], 'line': []}

        self._vis_time_offset = None

    @abstractmethod
    def callback(self, packet):
        raise NotImplementedError

    def set_marker(self):
        pass

    def reset_marker(self):
        pass

    def remove_marker(self):
        pass

    def add_nans(self):
        pass

    def change_timescale(self):
        pass

    def plot_points(self):
        pass


class ORNData(DataContainer):
    """_summary_
    """
    def __init__(self) -> None:
        super().__init__()

    def callback(self, packet):
        """ORN callback"""
        timestamp, orn_data = packet.get_data()
        if self._vis_time_offset is None:
            self._vis_time_offset = timestamp[0]
        time_vector = list(np.asarray(timestamp) - self._vis_time_offset)

        data = dict(zip(Settings.ORN_LIST, np.array(orn_data)[:, np.newaxis]))
        data['t'] = time_vector
        try:
            print(data)
            # self.signal_orn.emit(data)
        except RuntimeError as error:
            logger.warning("RuntimeError: %s", str(error))


class BasePlots:
    """_summary_
    """
    def __init__(self, ui) -> None:
        self.ui = ui

        # self.time_scale = 10
        self.lines = []
        self.setup_dropdowns()

    @property
    def time_scale(self):
        """Return timescale set in GUI
        """
        t_str = self.ui.value_timeScale.currentText()
        t = int(Settings.TIME_RANGE_MENU[t_str])
        return t

    def setup_dropdowns(self):
        # value_signal_type
        self.ui.value_signal.addItems(Settings.MODE_LIST)
        self.ui.value_signal_rec.addItems(Settings.MODE_LIST)

        # value_yaxis
        self.ui.value_yAxis.addItems(Settings.SCALE_MENU.keys())
        self.ui.value_yAxis.setCurrentText("1 mV")

        self.ui.value_yAxis_rec.addItems(Settings.SCALE_MENU.keys())
        self.ui.value_yAxis_rec.setCurrentText("1 mV")

        # value_time_scale
        self.ui.value_timeScale.addItems(Settings.TIME_RANGE_MENU.keys())
        self.ui.value_timeScale_rec.addItems(Settings.TIME_RANGE_MENU.keys())

        self.ui.value_event_code.setValidator(QIntValidator(8, 65535))

    @time_scale.setter
    def time_scale(self, value):
        # TODO revisit this
        if isinstance(value, str):
            value = Settings.TIME_RANGE_MENU[value]
        self.time_scale = value

    @abstractmethod
    def init_plot(self):
        raise NotImplementedError

    def add_active_curves(self):
        pass

    def set_t_axis(self, t_vector, pointer):
        pass

    def connection_vector(self, length, n_nans):
        pass

    def plot_marker(self):
        pass

    def replot_marker(self):
        pass

    def remove_markers(self, mrk_dict):
        pass

    def remove_old_item(self, item_dict, t_vector, item_type):
        pass

    def add_pos_line(self, lines, plot_wdgt, t_vector):
        pass


class ORNPlot(BasePlots):
    """_summary_
    """
    def __init__(self, ui) -> None:
        super().__init__(ui)
        self.model = ORNData()

        self.plot_acc = None
        self.plot_gyro = None
        self.plot_mag = None

        self.plots_list = [self.plot_acc, self.plot_gyro, self.plot_mag]

        self.lines = [None, None, None]

    def reset_vars(self):
        """Reset attributes"""
        self.plot_acc = None
        self.plot_gyro = None
        self.plot_mag = None

        self.plots_list = [self.plot_acc, self.plot_gyro, self.plot_mag]

        self.lines = [None, None, None]

    def init_plot(self):
        layout_wdgt = self.ui.plot_orn

        if None in self.plots_list:
            layout_wdgt.clear()
            self.lines = [None, None, None]

        # Set Background color
        layout_wdgt.setBackground(Stylesheets.PLOT_BACKGROUND)

        # Add subplots
        self.plot_acc = layout_wdgt.addPlot()
        layout_wdgt.nextRow()
        self.plot_gyro = layout_wdgt.addPlot()
        layout_wdgt.nextRow()
        self.plot_mag = layout_wdgt.addPlot()

        self.plots_list = [self.plot_acc, self.plot_gyro, self.plot_mag]

        # Link all plots to bottom axis
        self.plot_acc.setXLink(self.plot_mag)
        self.plot_gyro.setXLink(self.plot_mag)

        # Remove x axis in upper plots
        self.plot_acc.getAxis('bottom').setStyle(showValues=False)
        self.plot_gyro.getAxis('bottom').setStyle(showValues=False)

        # Add legend, axis label and grid to all the plots
        timescale = self.time_scale
        for plt, lbl in zip(self.plots_list, ORNLegend.all_values()):
            # plt.addLegend(horSpacing=20, colCount=3, brush='k', offset=(0, -125))
            plt.addLegend(horSpacing=20, colCount=3, brush='k', offset=(0, 0))
            plt.getAxis('left').setWidth(80)
            plt.getAxis('left').setLabel(lbl)
            plt.showGrid(x=True, y=True, alpha=0.5)
            plt.setXRange(0, timescale, padding=0.01)
            plt.setMouseEnabled(x=False, y=False)

        # Initialize curves for each plot
        self.curve_ax = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[0], name=' accX ')
        self.curve_ay = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[1], name=' accY ')
        self.curve_az = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[2], name=' accZ ')
        self.plot_acc.addItem(self.curve_ax)
        self.plot_acc.addItem(self.curve_ay)
        self.plot_acc.addItem(self.curve_az)

        self.curve_gx = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[0], name='gyroX')
        self.curve_gy = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[1], name='gyroY')
        self.curve_gz = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[2], name='gyroZ')
        self.plot_gyro.addItem(self.curve_gx)
        self.plot_gyro.addItem(self.curve_gy)
        self.plot_gyro.addItem(self.curve_gz)

        self.curve_mx = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[0], name='magX ')
        self.curve_my = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[1], name='magY ')
        self.curve_mz = pg.PlotCurveItem(pen=Stylesheets.ORN_LINE_COLORS[2], name='magZ ')
        self.plot_mag.addItem(self.curve_mx)
        self.plot_mag.addItem(self.curve_my)
        self.plot_mag.addItem(self.curve_mz)