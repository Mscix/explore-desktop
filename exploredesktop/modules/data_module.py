
from enum import Enum
import logging
from abc import abstractmethod

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QIntValidator


from exploredesktop.modules import BaseModel  # isort:skip
from exploredesktop.modules.app_settings import (  # isort:skip
    ExGAttributes,
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
            try:
                val.put(idxs, data[key], mode='wrap')
            except KeyError:
                val.put(idxs, [np.NaN for i in range(n_new_points)], mode='wrap')

    def update_pointer(self, data, signal):
        """update pointer"""
        self.pointer += self.get_n_new_points(data)

        if self.pointer >= len(self.t_plot_data):
            self.pointer -= len(self.t_plot_data)
            self.t_plot_data[self.pointer:] += self.timescale
            # self.signals.tRangeChanged.emit(np.nanmin(self.t_plot_data))
            signal.emit(np.nanmin(self.t_plot_data))

    def new_t_axis(self, signal):
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
        signal.emit([vals, ticks])


class ORNData(DataContainer):
    """_summary_"""
    def __init__(self) -> None:
        super().__init__()
        self.plot_data = {k: np.array([np.NaN] * 200) for k in Settings.ORN_LIST}
        self.t_plot_data = np.array([np.NaN] * 200)

    def new_t_axis(self, signal=None):
        signal = self.signals.tAxisORNChanged
        return super().new_t_axis(signal)

    def update_pointer(self, data, signal=None):
        signal = self.signals.tRangeORNChanged
        return super().update_pointer(data, signal)

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


class ExGData(DataContainer):
    """_summary_"""
    def __init__(self) -> None:
        super().__init__()

        self._baseline = None
        self.offsets = np.array([])
        self.y_unit = Settings.DEFAULT_SCALE
        self.y_string = '1 mV'
        self.last_t = 0

        self.packet_count = 0
        self.bt_drop_warning_displayed = False
        self.t_bt_drop = None

        self.rr_estimator = None
        self.r_peak = {'t': [], 'r_peak': [], 'points': []}
        self.r_peak_replot = {'t': [], 'r_peak': [], 'points': []}
        self.rr_warning_displayed = False

        self.signals.updateDataAttributes.connect(self.update_attributes)

    def new_t_axis(self, signal=None):
        signal = self.signals.tAxisEXGChanged
        return super().new_t_axis(signal)

    def update_pointer(self, data, signal=None):
        signal = self.signals.tRangeEXGChanged
        return super().update_pointer(data, signal)

    @Slot(list)
    def update_attributes(self, attributes: list):
        """_summary_

        Args:
            attribute (str): _description_
        """
        n_chan = self.explorer.n_active_chan
        active_chan = self.explorer.active_chan_list
        if ExGAttributes.OFFSETS in attributes:
            self.offsets = np.arange(1, n_chan + 1)[:, np.newaxis].astype(float)
        if ExGAttributes.BASELINE in attributes:
            self._baseline = None
        if ExGAttributes.DATA in attributes:
            # TODO: reset data
            points = self.plot_points()
            self.plot_data = {ch: np.array([np.NaN] * points) for ch in active_chan}
            self.t_plot_data = np.array([np.NaN] * points)
        # if ExGAttributes.INIT in attributes:
        #     self.

    def callback(self, packet):
        """_summary_"""
        chan_list = self.explorer.active_chan_list
        exg_fs = self.explorer.sampling_rate
        timestamp, exg = packet.get_data(exg_fs)

        # TODO in fft data - Original data
        # orig_exg = dict(zip(chan_list, exg))
        # self.add_original_exg(orig_exg)

        # TODO: handle disconnection errors (through conn status signal)
        # if self._vis_time_offset is not None and timestamp[0] < self._vis_time_offset:
        #     self.reset_vis_vars()
        #     new_size = self.plot_points()
        #     self.exg_plot_data[0] = np.array([np.NaN] * new_size)
        #     self.exg_plot_data[1] = {
        #         ch: np.array([np.NaN] * new_size) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
        #     self.exg_plot_data[2] = {
        #         ch: np.array([np.NaN] * self.plot_points(downsampling=False)
        #                         ) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}

        #     t_min = 0
        #     t_max = t_min + self.get_timeScale()
        #     self.ui.plot_exg.setXRange(t_min, t_max, padding=0.01)

        # From timestamp to seconds
        if self._vis_time_offset is None:
            self._vis_time_offset = timestamp[0]

        time_vector = timestamp - self._vis_time_offset

        # Downsampling
        if Settings.DOWNSAMPLING:
            time_vector, exg = self.downsampling(time_vector, exg, exg_fs)

        # Baseline Correction
        # TODO change if condition when filters are implemented
        # if self.plotting_filters is not None and self.plotting_filters['offset']:
        # pylint: disable=using-constant-test
        if True:
            exg = self.baseline_correction(exg)

        exg = self.update_unit(exg)
        data = dict(zip(chan_list, exg))
        data['t'] = time_vector

        self.insert_new_data(data)
        self.update_pointer(data)
        self.new_t_axis()

        self.last_t = data['t'][-1]

        try:
            self.signals.exgChanged.emit([self.t_plot_data, self.plot_data])
        except ValueError:
            pass

    def downsampling(self, time_vector, exg, exg_fs):
        """Downsample"""
        # Correct packet for 4 chan device
        if len(time_vector) == 33 and self.decide_drop(exg_fs):
            exg = exg[:, 1:]
            time_vector = time_vector[1:]

        # Downsample
        exg = exg[:, ::int(exg_fs / Settings.EXG_VIS_SRATE)]
        time_vector = time_vector[::int(exg_fs / Settings.EXG_VIS_SRATE)]
        return time_vector, exg

    def decide_drop(self, exg_fs: int) -> bool:
        """Decide whether to drop a data point from the packet based on the sampling rate

        Args:
            exg_fs (int): sampling rate

        Returns:
            bool: whether to drop a data point
        """
        drop = True
        if exg_fs == 1000 and self.packet_count % 8 == 0:
            drop = False
        elif exg_fs == 500 and self.packet_count % 4 == 0:
            drop = False
        elif exg_fs == 250 and self.packet_count % 2 == 0:
            drop = False
        return drop

    def baseline_correction(self, exg):
        """baseline correction"""
        samples_avg = exg.mean(axis=1)

        if self._baseline is None:
            self._baseline = samples_avg
        else:
            try:
                self._baseline = self._baseline - (
                    (self._baseline - samples_avg) / Settings.BASELINE_MA_LENGTH * exg.shape[1]
                )
            except ValueError:
                self._baseline = samples_avg

        exg = exg - self._baseline[:, np.newaxis]

        return exg

    def update_unit(self, exg):
        """_summary_

        Args:
            exg (_type_): _description_

        Returns:
            _type_: _description_
        """
        exg = self.offsets + exg / self.y_unit
        return exg


class BasePlots:
    """_summary_
    """
    def __init__(self, ui) -> None:
        self.ui = ui
        self.model = ""

        # self.time_scale = 10
        self.lines = []
        self.plots_list = []

        self.set_dropdowns()

    @property
    def time_scale(self):
        """Return timescale set in GUI
        """
        t_str = self.ui.value_timeScale.currentText()
        t = int(Settings.TIME_RANGE_MENU[t_str])
        return t

    @time_scale.setter
    def time_scale(self, value):
        # TODO revisit this
        if isinstance(value, str):
            value = Settings.TIME_RANGE_MENU[value]
        self.model.timescale = value

    def set_dropdowns(self):
        """Initialize dropdowns"""
        # Avoid double initialization
        if self.ui.value_signal.count() > 0:
            return

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

    @abstractmethod
    def init_plot(self):
        """initialize the plot"""
        raise NotImplementedError

    @abstractmethod
    def swipe_plot(self, data):
        """swipping plot"""
        raise NotImplementedError

    # TODO implement later and have option in gui
    # @abstractmethod
    # def moving_plot(self):
    #     """moving window plot"""
    #     raise NotImplementedError

    def add_active_curves(self, all_curves: list, plot_widget: pg.PlotWidget) -> list:
        """Add curves from a list to a plot widget if the corresponding channel is active

        Args:
            all_curves (list): list of all potential curves
            chan_dict (dict): dictionary with active channels
            plot_widget (pg.PlotWidget): pyqtgraph plotWidget

        Returns:
            list: list of curves added to plot
        """
        # Verify curves and chan dict have the same length, if not reset chan_dict
        chan_dict = self.model.explorer.get_chan_dict()

        # TODO: check if this is needed
        # if len(all_curves) != len(list(chan_dict.values())):
        #     self.set_chan_dict()

        active_curves = []
        for curve, act in zip(all_curves, list(chan_dict.values())):
            if act == 1:
                plot_widget.addItem(curve)
                active_curves.append(curve)
        return active_curves

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
        connection[self.model.pointer - int(n_nans / 2): self.model.pointer + int(n_nans / 2)] = 0
        first_key = list(self.model.plot_data.keys())[0]
        connection[np.argwhere(np.isnan(self.model.plot_data[first_key]))] = 0
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

    def _add_pos_line(self, t_vector: list):
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

        if None in self.lines:
            for idx, plt in enumerate(self.plots_list):
                self.lines[idx] = plt.addLine(pos, pen=Stylesheets.POS_LINE_COLOR)
        else:
            for line in self.lines:
                try:
                    line.setPos(pos)
                except RuntimeError:
                    self.lines = [None for i in range(len(self.lines))]

        return self.lines


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

        if self.ui.plot_orn.getItem(0, 0) is not None:
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
    def swipe_plot(self, data):
        """plot orientation data"""
        t_vector, plot_data = data

        # Reset plot if position line is not properly set
        if None in self.lines:
            self.ui.plot_orn.clear()
            self.init_plot()

        # position line
        self._add_pos_line(t_vector)

        # connection vector
        connection = self._connection_vector(len(t_vector), n_nans=2)

        self.curve_ax.setData(t_vector, plot_data['accX'], connect=connection)
        self.curve_ay.setData(t_vector, plot_data['accY'], connect=connection)
        self.curve_az.setData(t_vector, plot_data['accZ'], connect=connection)
        self.curve_gx.setData(t_vector, plot_data['gyroX'], connect=connection)
        self.curve_gy.setData(t_vector, plot_data['gyroY'], connect=connection)
        self.curve_gz.setData(t_vector, plot_data['gyroZ'], connect=connection)
        self.curve_mx.setData(t_vector, plot_data['magX'], connect=connection)
        self.curve_my.setData(t_vector, plot_data['magY'], connect=connection)
        self.curve_mz.setData(t_vector, plot_data['magZ'], connect=connection)


class ExGPlot(BasePlots):
    """_summary_
    """
    def __init__(self, ui) -> None:
        super().__init__(ui)
        self.model = ExGData()

        self.lines = [None]

        self.y_string = "1mV"
        self.plots_list = [self.ui.plot_exg]

    def reset_vars(self):
        pass

    def init_plot(self):
        plot_wdgt = self.ui.plot_exg

        n_chan = self.model.explorer.n_active_chan
        timescale = self.time_scale

        if self.ui.plot_orn.getItem(0, 0) is not None:
            plot_wdgt.clear()
            self.lines = [None]

        # TODO move to exg data
        # Create offsets for each chan line
        # self.offsets = np.arange(1, n_chan + 1)[:, np.newaxis].astype(float)

        # Set Background color
        plot_wdgt.setBackground(Stylesheets.PLOT_BACKGROUND)

        # Disable zoom
        plot_wdgt.setMouseEnabled(x=False, y=False)

        # Add chan ticks to y axis
        # Left axis
        plot_wdgt.setLabel('left', 'Voltage')
        self.add_left_axis_ticks()
        plot_wdgt.getAxis('left').setWidth(60)
        plot_wdgt.getAxis('left').setPen(color=(255, 255, 255, 50))
        plot_wdgt.getAxis('left').setGrid(50)

        # Right axis
        plot_wdgt.showAxis('right')
        plot_wdgt.getAxis('right').linkToView(plot_wdgt.getViewBox())
        self.add_right_axis_ticks()
        plot_wdgt.getAxis('right').setGrid(200)

        # Add range of time axis
        plot_wdgt.setRange(yRange=(-0.5, n_chan + 1), xRange=(0, int(timescale)), padding=0.01)
        plot_wdgt.setLabel('bottom', 'time (s)')

        all_curves_list = [
            pg.PlotCurveItem(pen=Stylesheets.EXG_LINE_COLOR) for i in range(self.model.explorer.device_chan)]
        self.active_curves_list = self.add_active_curves(all_curves_list, plot_wdgt)

    def add_right_axis_ticks(self):
        """
        Add upper and lower lines delimiting the channels in exg plot
        """
        active_chan = self.model.explorer.active_chan_list

        ticks_right = [(idx + 1.5, '') for idx, _ in enumerate(active_chan)]
        ticks_right += [(0.5, '')]

        self.ui.plot_exg.getAxis('right').setTicks([ticks_right])

    def add_left_axis_ticks(self):
        """
        Add central lines and channel name ticks in exg plot
        """
        active_chan = self.model.explorer.active_chan_list

        ticks = [
            (idx + 1, f'{ch}\n' + '(\u00B1' + f'{self.y_string})') for idx, ch in enumerate(active_chan)]
        self.ui.plot_exg.getAxis('left').setTicks([ticks])

    @Slot(dict)
    def swipe_plot(self, data):
        t_vector, plot_data = data

        # TODO implement bt drop handling
        # self.handle_bt_drop()

        # TODO: if wrap handle
        # 1. check id_th (check if necessary)
        # 2. Remove marker line and replot in the new axis
        # 3. Remove rr peaks and replot in new axis

        # position line
        self._add_pos_line(t_vector)

        # connection vector
        connection = self._connection_vector(len(t_vector))

        # Paint curves
        for curve, chan in zip(self.active_curves_list, self.model.explorer.active_chan_list):
            try:
                curve.setData(t_vector, plot_data[chan], connect=connection)
            except KeyError:
                pass

        # TODO:
        # remove reploted markers
        # remove reploted r_peaks

    # def set_t_axis(self, t):
        
    #     if np.nanmax(t) < self.time_scale:
    #         return

    #     t_ticks = t.copy()
    #     t_ticks[self.model.pointer:] -= self.time_scale
    #     t_ticks = t_ticks.astype(int)
    #     l_points = int(len(t) / int(self.time_scale))
    #     vals = t[::l_points]
    #     ticks = t_ticks[::l_points]
    #     for plt in self.plots_list:
    #         plt.getAxis('bottom').setTicks([[(t, str(tick)) for t, tick in zip(vals, ticks)]])

    def handle_bt_drop(self):
        """_summary_
        """
        # TODO implement
        # if data['t'][0] < self.last_t and self.bt_drop_warning_displayed is False:
        #     self.bt_drop_warning_displayed = True
        #     self.t_drop = data['t'][0]
        #     msg = (
        #         "The bluetooth connection is unstable. This may affect the ExG visualization."
        #         "\nPlease read the troubleshooting section of the user manual for more."
        #     )
        #     title = "Unstable Bluetooth connection"
        #     self.display_msg(msg_text=msg, title=title, type="info")

        # elif (self.t_drop is not None) and (data['t'][0] > self.last_t) and \
        #         (data['t'][0] - self.t_drop > 10) and self.bt_drop_warning_displayed is True:
        #     self.bt_drop_warning_displayed = False
        pass
        