"""FFT visualization module"""
import numpy as np
from exploredesktop.modules.app_settings import ExGAttributes, Stylesheets
from scipy.ndimage.filters import gaussian_filter1d


from exploredesktop.modules.base_data_module import (  # isort:skip
    BasePlots,
    DataContainer
)

from PySide6.QtCore import Slot, QTimer
from datetime import datetime as dt


class FFTData(DataContainer):
    def __init__(self) -> None:
        super().__init__()

        self.timer = QTimer()
        self.signals.updateDataAttributes.connect(self.update_attributes)

    def start_timer(self, fn):
        if self.timer.isActive():
            print("timer is active")
            return
        self.timer.setInterval(2000)
        self.timer.timeout.connect(fn)
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    @Slot(list)
    def update_attributes(self, attributes: list):
        """_summary_

        Args:
            attributes (list): _description_
        """
        active_chan = self.explorer.active_chan_list
        if ExGAttributes.DATA in attributes:
            points = self.plot_points()
            self.plot_data = {ch: np.array([np.NaN] * points) for ch in active_chan}

    def get_fft(self, exg, s_rate):
        """
        Compute FFT
        Args:
            exg: exg data from ExG packet
            s_rate (int): sampling rate
        """
        n_point = 1024
        exg -= exg.mean(axis=1)[:, np.newaxis]
        freq = s_rate * np.arange(int(n_point / 2)) / n_point
        fft_content = np.fft.fft(exg, n=n_point) / n_point
        fft_content = np.abs(fft_content[:, range(int(n_point / 2))])
        fft_content = gaussian_filter1d(fft_content, 1)
        return fft_content[:, 1:], freq[1:]

    def callback(self, packet):
        chan_list = self.explorer.active_chan_list
        exg_fs = self.explorer.sampling_rate

        _, exg = packet.get_data(exg_fs)
        orig_exg = dict(zip(chan_list, exg))
        first_chan = list(self.plot_data.keys())[0]
        n_new_points = len(orig_exg[list(orig_exg.keys())[0]])

        idxs = np.arange(self.pointer, self.pointer + n_new_points)

        for chan in self.plot_data.keys():
            try:
                chan_data = orig_exg[chan]
            except KeyError:
                chan_data = np.array([np.NaN for i in range(n_new_points)])
            self.plot_data[chan].put(idxs, chan_data, mode='wrap')

        self.pointer += n_new_points
        if self.pointer >= len(self.plot_data[first_chan]):
            self.pointer -= len(self.plot_data[first_chan])

        exg_data = np.array(
            [self.plot_data[key][~np.isnan(self.plot_data[key])] for key in self.plot_data.keys()], dtype=object)

        if (len(exg_data.shape) == 1) or (exg_data.shape[1] < exg_fs * 5):
            return

        fft_content, freq = self.get_fft(exg_data, exg_fs)
        data = dict(zip(self.plot_data.keys(), fft_content))
        data['f'] = freq

        def emit_fft(data):
            self.signals.fftChanged.emit(data)

        try:
            self.start_timer(emit_fft(data))
        except ValueError:
            pass


class FFTPlot(BasePlots):
    def __init__(self, ui) -> None:
        super().__init__(ui)
        self.model = FFTData()

    def init_plot(self):
        if self.ui.plot_orn.getItem(0, 0) is not None:
            self.ui.plot_fft.clear()

        plot_wdgt = self.ui.plot_fft
        plot_wdgt.setBackground(Stylesheets.PLOT_BACKGROUND)

        plot_wdgt.showGrid(x=True, y=True, alpha=0.5)
        plot_wdgt.addLegend(horSpacing=20, colCount=2, brush='k', offset=(0, -300))
        plot_wdgt.setLabel('left', 'Amplitude (uV)')
        plot_wdgt.setLabel('bottom', 'Frequency (Hz)')
        plot_wdgt.setLogMode(x=False, y=True)
        plot_wdgt.setMouseEnabled(x=False, y=False)

        all_curves_list = [
            plot_wdgt.getPlotItem().plot(
                pen=Stylesheets.FFT_LINE_COLORS[i], name=f'ch{i+1}', skipFiniteCheck=True
            ) for i in range(self.model.explorer.device_chan)
        ]
        self.active_curves_list = self.add_active_curves(all_curves_list, plot_wdgt)

    @Slot(dict)
    def plot(self, data):
        plot_wdgt = self.ui.plot_fft
        plot_wdgt.setXRange(0, 70, padding=0.01)
        print(dt.now())
        # for curve, chan in zip(self.active_curves_list, self.model.explorer.active_chan_list):
        #     try:
        #         curve.setData(data['f'], data[chan])
        #     except KeyError:
        #         pass
