from abc import abstractmethod
import logging
from typing import Tuple
import numpy as np

from PySide6.QtCore import Slot

import pyqtgraph as pg
from exploredesktop.modules.app_settings import Settings, Stylesheets
from exploredesktop.modules.base_model import BaseModel

logger = logging.getLogger("explorepy." + __name__)


class DataContainer(BaseModel):
    """_summary_
    """
    vis_time_offset = None

    def __init__(self) -> None:
        super().__init__()
        self.plot_data = {}
        self.t_plot_data = np.array([])

        self.pointer = 0

        self.timescale = 10

    def reset_vars(self):
        self.plot_data = {}
        self.t_plot_data = np.array([])

        self.pointer = 0

        self.vis_time_offset = None

        self.timescale = 10

    @abstractmethod
    def callback(self, packet):
        raise NotImplementedError

    @abstractmethod
    def update_attributes(self, attributes):
        raise NotImplementedError

    def remove_dict_item(self, item_dict: dict, item_type: str, to_remove: list) -> Tuple[dict, list]:
        """Remove item from a dictionary

        Args:
            item_dict (dict): dictionary with the items to remvoe
            item_type (str): type of item to remove.
            to_remove (list): list with the item to remove

        Returns:
            Tuple[dict, list]: `item_dict` and `to_remove` without the removed items

        Raises:
            AssertionError: if `item_type` is neither `lines` or `points`
        """
        assert item_type in ['lines', 'points'], "item_type must be either 'lines' or 'points'"
        # if to_remove is emtpy, return
        if len(to_remove) < 1:
            return item_dict, to_remove

        if item_type == 'lines':
            key = 'code'
        elif item_type == 'points':
            key = 'r_peak'

        for item in to_remove:
            item_dict['t'].remove(item[0])
            item_dict[key].remove(item[1])
            item_dict[item_type].remove(item[2])
            to_remove.remove(item)

        return item_dict, to_remove

    def add_nans(self):
        pass

    def change_timescale(self):
        logger.debug("Time scale has been changed to %.0f", self.timescale)

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
        n_new_points = len(data[list(data.keys())[0]])
        return n_new_points

    def insert_new_data(self, data, fft=False):
        """insert new data"""
        n_new_points = self.get_n_new_points(data)
        idxs = np.arange(self.pointer, self.pointer + n_new_points)

        if fft is False:
            self.t_plot_data.put(idxs, data['t'], mode='wrap')  # replace values with new points

        for key, val in self.plot_data.items():
            try:
                val.put(idxs, data[key], mode='wrap')
            except KeyError:
                val.put(idxs, [np.NaN for i in range(n_new_points)], mode='wrap')

    def update_pointer(self, data, signal=None, fft=False):
        """update pointer"""
        self.pointer += self.get_n_new_points(data)

        if self.pointer >= len(self.t_plot_data):
            self.pointer -= len(self.t_plot_data)
            if fft is False:
                self.t_plot_data[self.pointer:] += self.timescale
                signal.emit(np.nanmin(self.t_plot_data))
                # TODO create signal onWrap to update data and emit6
                self.signals.replotMkrAdd.emit(self.t_plot_data[0])

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
        try:
            signal.emit([vals, ticks])
        except RuntimeError as error:
            logger.warning("RuntimeError: %s", str(error))


class BasePlots:
    """_summary_
    """
    def __init__(self, ui) -> None:
        self.ui = ui
        self.model = DataContainer()

        self.lines = []
        self.plots_list = []

        self.set_dropdowns()

    def setup_ui_connections(self):
        self.ui.value_timeScale.currentTextChanged.connect(self.set_time_scale)

    def get_model(self):
        """Return data model"""
        return self.model

    @property
    def time_scale(self):
        """Return timescale set in GUI
        """
        t_str = self.ui.value_timeScale.currentText()
        t = int(Settings.TIME_RANGE_MENU[t_str])
        return t

    def set_time_scale(self, value):
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
            else:
                plot_widget.removeItem(curve)
        return active_curves

    @Slot(float)
    def set_t_range(self, data):
        """set t range"""
        t_min = data
        t_max = t_min + self.time_scale
        for plt in self.plots_list:
            plt.setXRange(t_min, t_max, padding=0.01)

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

    def remove_old_item(self, item_dict: dict, last_t: np.array, item_type: str) -> list:
        """
        Remove line or point element from plot widget

        Args:
            item_dict (dict): dictionary with items to remove
            t_vector (np.array): time vector used as a condition to remove
            item_type (str): specifies item to remove (line or points).
            plot_widget (pyqtgraph PlotWidget): plot widget containing item to remove

        Retrun:
            list: list with objects to remove
        """
        assert item_type in ['lines', 'points'], 'item type parameter must be line or points'
        assert 't' in item_dict.keys(), 'the items dictionary must have the key \'t\''

        to_remove = []
        for idx_t in range(len(item_dict['t'])):
            if item_dict['t'][idx_t] < last_t:
                for plt_wdgt in self.plots_list:
                    for item in item_dict[item_type][idx_t]:
                        plt_wdgt.removeItem(item)
                to_remove.append([item_dict[key][idx_t] for key in item_dict.keys()])
                # [item_dict['t'][idx_t], item_dict['r_peak'][idx_t], item_dict['points'][idx_t]])
        return to_remove
