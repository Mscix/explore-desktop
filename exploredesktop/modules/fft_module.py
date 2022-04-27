"""FFT visualization module"""
import numpy as np
from exploredesktop.modules.app_settings import Stylesheets
from scipy.ndimage.filters import gaussian_filter1d


from exploredesktop.modules.base_data_module import (  # isort:skip
    BasePlots,
    DataContainer
)


class FFTData(DataContainer):
    def __init__(self) -> None:
        super().__init__()
        self.raw_exg_data = {}

    def callback(self):
        pass

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
            plot_wdgt.getPlotItem().plot(pen=Stylesheets.FFT_LINE_COLORS[i], name=f'ch{i+1}', skipFiniteCheck=True) for i in range(self.model.explorer.device_chan)]
        self.active_curves_list = self.add_active_curves(all_curves_list, plot_wdgt)

    def plot(self):
        pass
