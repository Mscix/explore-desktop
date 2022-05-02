"""ExG visualization module"""
import logging

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot


from exploredesktop.modules.app_settings import (  # isort:skip
    ExGAttributes,
    Settings,
    Stylesheets
)
from exploredesktop.modules.base_data_module import BasePlots, DataContainer   # isort:skip


logger = logging.getLogger("explorepy." + __name__)


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


class ExGPlot(BasePlots):
    """_summary_
    """
    def __init__(self, ui) -> None:
        super().__init__(ui)
        self.model = ExGData()

        self.lines = [None]

        self.plots_list = [self.ui.plot_exg]
        self.bt_drop_warning_displayed = False

    def reset_vars(self):
        pass

    def init_plot(self):
        plot_wdgt = self.ui.plot_exg

        n_chan = self.model.explorer.n_active_chan
        timescale = self.time_scale

        if self.ui.plot_orn.getItem(0, 0) is not None:
            plot_wdgt.clear()
            self.lines = [None]

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
            (idx + 1, f'{ch}\n' + '(\u00B1' + f'{self.model.y_string})') for idx, ch in enumerate(active_chan)]
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
        return
