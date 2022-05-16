
import logging
from abc import abstractmethod

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QIntValidator


from exploredesktop.modules import BaseModel  # isort:skip
from exploredesktop.modules.app_settings import (  # isort:skip
    ORNLegend,
    Settings,
    Stylesheets
)


logger = logging.getLogger("explorepy." + __name__)


class DataContainer(BaseModel):
    """_summary_
    """
    def __init__(self) -> None:
        super().__init__()
        self.plot_data = {}
        self.t_plot_data = np.array([])

        self.pointer = 0

        self.mrk_plot = {'t': [], 'code': [], 'line': []}
        self.mrk_replot = {'t': [], 'code': [], 'line': []}

        self._vis_time_offset = None

        self.timescale = 10

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

    def plot_points(self, orn=False, downsampling=Settings.DOWNSAMPLING):
        """_summary_

        Args:
            orn (bool, optional): _description_. Defaults to False.
            downsampling (_type_, optional): _description_. Defaults to Settings.DOWNSAMPLING.

        Returns:
            _type_: _description_
        """
        time_scale = self.timescale
        sr = self.explorer.sampling_rate

        if not orn:
            if downsampling:
                points = (time_scale * sr) / (sr / Settings.EXG_VIS_SRATE)
            else:
                points = (time_scale * sr)
        else:
            points = time_scale * Settings.ORN_SRATE

        return int(points)

    @staticmethod
    def get_n_new_points(data):
        """get indexes where to insert new data"""
        n_new_points = len(data['t'])
        return n_new_points

    def insert_new_data(self, data):
        """insert new data"""
        n_new_points = self.get_n_new_points(data)
        idxs = np.arange(self.pointer, self.pointer + n_new_points)

        self.t_plot_data.put(idxs, data['t'], mode='wrap')  # replace values with new points

        for key, val in self.plot_data.items():
            val.put(idxs, data[key], mode='wrap')

    def update_pointer(self, data):
        """update pointer"""
        self.pointer += self.get_n_new_points(data)

        if self.pointer >= len(self.t_plot_data):
            self.pointer -= len(self.t_plot_data)
            self.t_plot_data[self.pointer:] += self.timescale
            self.signals.tRangeChanged.emit(np.nanmin(self.t_plot_data))

    def new_t_axis(self):
        """
        Update t-axis

        Args:
            t_vector (np.array): time vector
            pointer (int): index with current position in time
        """
        if np.nanmax(self.t_plot_data) < self.timescale:
            return

        t_ticks = self.t_plot_data.copy()
        t_ticks[self.pointer:] -= self.timescale
        t_ticks = t_ticks.astype(int)
        l_points = int(len(self.t_plot_data) / int(self.timescale))
        vals = self.t_plot_data[::l_points]
        ticks = t_ticks[::l_points]
        self.signals.tAxisChanged.emit([vals, ticks])


class ORNData(DataContainer):
    """_summary_
    """
    def __init__(self) -> None:
        super().__init__()
        self.plot_data = {k: np.array([np.NaN] * 200) for k in Settings.ORN_LIST}
        self.t_plot_data = np.array([np.NaN] * 200)

    def callback(self, packet):
        """ORN callback"""
        timestamp, orn_data = packet.get_data()
        if self._vis_time_offset is None:
            self._vis_time_offset = timestamp[0]
        time_vector = list(np.asarray(timestamp) - self._vis_time_offset)

        data = dict(zip(Settings.ORN_LIST, np.array(orn_data)[:, np.newaxis]))
        data['t'] = time_vector

        self.insert_new_data(data)
        self.update_pointer(data)
        self.new_t_axis()

        try:
            self.signals.ornChanged.emit([self.t_plot_data, self.plot_data])
        except RuntimeError as error:
            logger.warning("RuntimeError: %s", str(error))


class BasePlots:
    """_summary_
    """
    def __init__(self, ui) -> None:
        self.ui = ui
        self.model = ""

        # self.time_scale = 10
        self.lines = []
        self.set_dropdowns()
        self.plots_list = []

    @property
    def time_scale(self):
        """Return timescale set in GUI
        """
        t_str = self.ui.value_timeScale.currentText()
        t = int(Settings.TIME_RANGE_MENU[t_str])
        return t

    def set_dropdowns(self):
        """Initialize dropdowns"""
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
        # self.time_scale = value
        self.model.timescale = value

    @abstractmethod
    def init_plot(self):
        raise NotImplementedError

    def add_active_curves(self):
        pass

    @Slot(float)
    def set_t_range(self, data):
        """set t range"""
        t_min = data
        t_max = t_min + self.time_scale
        for plt in self.plots_list:
            plt.setXRange(t_min, t_max, padding=0.01)

    # TODO> check this when implementing exg plot
    @Slot(list)
    def set_t_axis(self, data):
        """_summary_

        Args:
            data (_type_): _description_
        """
        values, ticks = data
        for plt in self.plots_list:
            plt.getAxis('bottom').setTicks([[(t, str(tick)) for t, tick in zip(values, ticks)]])

    def _connection_vector(self, length, n_nans=10, id_th=None):
        """
        Create connection vector to connect old and new data with a gap

        Args:
            length (int): length of the connection vector. Must be the same as the array to plot
            id_th (int): threshold obtained when dev is disconnected
            n_nans (int): number of nans to introduce
        """
        connection = np.full(length, 1)
        # connection = np.full(length, 1)
        connection[self.model.pointer - int(n_nans / 2): self.model.pointer + int(n_nans / 2)] = 0
        if id_th is not None and id_th > 100:
            connection[:id_th] = 0

        return connection

    def plot_marker(self):
        pass

    def replot_marker(self):
        pass

    def remove_markers(self, mrk_dict):
        pass

    def remove_old_item(self, item_dict, t_vector, item_type):
        pass

    def _add_pos_line(self, lines: list, plot_widgets: list, t_vector: list):
        """
        Add position line to plot based on last value in the time vector

        Args:
            lines (list): list of position line
            plot_widget (list): list of pyqtgraph PlotWidget to add the line
            t_vector (list): time vector used as reference for the position

        Return:
            lines (list): position line with updated time pos
        """
        # pos = t_vector[-1]
        # pos = np.nanmax(t_vector)
        pos = t_vector[self.model.pointer - 1]

        if None in lines:
            for idx, plt in enumerate(plot_widgets):
                lines[idx] = plt.addLine(pos, pen=Stylesheets.POS_LINE_COLOR)
        else:
            for line in lines:
                try:
                    line.setPos(pos)
                except RuntimeError:
                    lines = [None for i in range(len(lines))]

        return lines


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

    @Slot(dict)
    def plot(self, data):
        """plot orientation data"""
        t, y = data

        # position line
        if None in self.lines:
            self.ui.plot_orn.clear()
            self.init_plot()
        self._add_pos_line(self.lines, self.plots_list, t)

        connection = self._connection_vector(len(t), n_nans=2)

        self.curve_ax.setData(t, y['accX'], connect=connection)
        self.curve_ay.setData(t, y['accY'], connect=connection)
        self.curve_az.setData(t, y['accZ'], connect=connection)
        self.curve_gx.setData(t, y['gyroX'], connect=connection)
        self.curve_gy.setData(t, y['gyroY'], connect=connection)
        self.curve_gz.setData(t, y['gyroZ'], connect=connection)
        self.curve_mx.setData(t, y['magX'], connect=connection)
        self.curve_my.setData(t, y['magY'], connect=connection)
        self.curve_mz.setData(t, y['magZ'], connect=connection)
