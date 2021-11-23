
import time
from PySide6.QtCore import Slot
from explorepy.stream_processor import TOPICS
from explorepy.tools import HeartRateEstimator
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
from modules.app_functions2 import AppFunctions
from modules.app_settings import Settings
from modules.dialogs import PlotDialog
import pyqtgraph as pg


class VisualizationFunctions(AppFunctions):
    def __init__(self, ui, explorer, signals):
        super().__init__(ui, explorer)
        self.signal_exg = signals["exg"]
        self.signal_mkr = signals["mkr"]
        self.signal_orn = signals["orn"]

        self._vis_time_offset = None
        self._baseline_corrector = {"MA_length": 1.5 * Settings.EXG_VIS_SRATE,
                                    "baseline": 0}

        self.y_unit = Settings.DEFAULT_SCALE
        self.y_string = "1 mV"
        self.last_t = 0

        self.line = None
        self.exg_pointer = 0
        self.mrk_plot = {"t": [], "code": [], "line": []}
        self.mrk_replot = {"t": [], "code": [], "line": []}

        self.lines_orn = [None, None, None]
        self.orn_pointer = 0
        self.orn_plot = {k: np.array([np.NaN]*200) for k in Settings.ORN_LIST}
        self.t_orn_plot = np.array([np.NaN]*200)

        self.rr_estimator = None
        self.r_peak = {"t": [], "r_peak": [], "points": []}

    #########################
    # Init Functions
    #########################
    def init_plots(self):
        """
        Initialize EXG, ORN and FFT plots
        """
        if self.ui.plot_orn.getItem(0, 0) is not None:
            self.ui.plot_exg.clear()
            self.ui.plot_fft.clear()
            self.ui.plot_orn.clear()
            print("cleared plots")

        self.init_plot_exg()
        self.init_plot_orn()
        self.init_plot_fft()

    def init_plot_exg(self):
        """
        Initialize EXG plot
        """
        # Count number of active channels
        n_chan_sp = self.explorer.stream_processor.device_info['adc_mask'].count(1)
        n_chan = list(self.chan_dict.values()).count(1)
        if n_chan != n_chan_sp:
            print("ERROR chan count does not match")

        # Create offsets for each chan line
        self.offsets = np.arange(1, n_chan + 1)[:, np.newaxis].astype(float)

        # Set Background color
        pw = self.ui.plot_exg
        pw.setBackground(Settings.PLOT_BACKGROUND)

        # Add chan ticks to y axis
        self.active_chan = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]
        ticks = [(idx+1, ch) for idx, ch in enumerate(self.active_chan)]
        pw.getAxis("left").setTicks([ticks])
        pw.getAxis("left").setWidth(50)

        # Add grid, axis labels and range of time axis
        pw.showGrid(x=False, y=True, alpha=0.5)
        timescale = self.get_timeScale()
        pw.setRange(yRange=(-0.5, n_chan+1), xRange=(0, int(timescale)), padding=0.01)
        pw.setLabel("bottom", "time (s)")
        pw.setLabel("left", "Voltage")

        # Initialize curves for each channel
        self.curve_ch1 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch2 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch3 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch4 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch5 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch6 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch7 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch8 = pg.PlotCurveItem(pen=Settings.EXG_LINE_COLOR)

        all_curves_list = [
            self.curve_ch1, self.curve_ch2, self.curve_ch3, self.curve_ch4,
            self.curve_ch5, self.curve_ch6, self.curve_ch7, self.curve_ch8
        ]

        # Add curves to plot only if channel is active
        self.curves_list = []
        for curve, act in zip(all_curves_list, list(self.chan_dict.values())):
            if act == 1:
                pw.addItem(curve)
                self.curves_list.append(curve)

    def init_plot_orn(self):
        """
        Initialize plot ORN
        """
        pw = self.ui.plot_orn

        # Set Background color
        pw.setBackground(Settings.PLOT_BACKGROUND)

        # Add subplots
        self.plot_acc = pw.addPlot()
        pw.nextRow()
        self.plot_gyro = pw.addPlot()
        pw.nextRow()
        self.plot_mag = pw.addPlot()

        self.plots_orn_list = [self.plot_acc, self.plot_gyro, self.plot_mag]

        # Link all plots to bottom axis
        self.plot_acc.setXLink(self.plot_mag)
        self.plot_gyro.setXLink(self.plot_mag)

        # Remove x axis in upper plots
        self.plot_acc.getAxis("bottom").setStyle(showValues=False)
        self.plot_gyro.getAxis("bottom").setStyle(showValues=False)

        # Add legend, axis label and grid to all the plots
        timescale = int(self.get_timeScale())
        for plt, lbl in zip(self.plots_orn_list, ['Acc [mg/LSB]', 'Gyro [mdps/LSB]', 'Mag [mgauss/LSB]']):
            plt.addLegend(horSpacing=20, colCount=3, brush="k", offset=(0, -125))
            # plt.addLegend(horSpacing=20, colCount=3, brush="k", offset=(0,0))
            plt.getAxis("left").setWidth(80)
            plt.getAxis("left").setLabel(lbl)
            plt.showGrid(x=True, y=True, alpha=0.5)
            plt.setXRange(0, timescale, padding=0.01)

        # Initialize curves for each plot
        self.curve_az = self.plot_acc.plot(pen=Settings.ORN_LINE_COLORS[2], name="accZ")
        self.curve_ay = self.plot_acc.plot(pen=Settings.ORN_LINE_COLORS[1], name="accY")
        self.curve_ax = self.plot_acc.plot(pen=Settings.ORN_LINE_COLORS[0], name="accX")

        self.curve_gx = self.plot_gyro.plot(pen=Settings.ORN_LINE_COLORS[0], name="gyroX")
        self.curve_gy = self.plot_gyro.plot(pen=Settings.ORN_LINE_COLORS[1], name="gyroY")
        self.curve_gz = self.plot_gyro.plot(pen=Settings.ORN_LINE_COLORS[2], name="gyroZ")

        self.curve_mx = self.plot_mag.plot(pen=Settings.ORN_LINE_COLORS[0], name="magX")
        self.curve_my = self.plot_mag.plot(pen=Settings.ORN_LINE_COLORS[1], name="magY")
        self.curve_mz = self.plot_mag.plot(pen=Settings.ORN_LINE_COLORS[2], name="magZ")

    def init_plot_fft(self):
        """
        Initialize FFT plot
        """
        pw = self.ui.plot_fft
        pw.setBackground(Settings.PLOT_BACKGROUND)
        pw.setXRange(0, 70, padding=0.01)
        pw.showGrid(x=True, y=True, alpha=0.5)
        pw.addLegend(horSpacing=20, colCount=2, brush="k", offset=(0, -300))
        pw.setLabel('left', "Amplitude (uV)")
        pw.setLabel('bottom', "Frequency (Hz)")
        pw.setLogMode(x=False, y=True)

    #########################
    # Emit Functions
    #########################
    def emit_signals(self):
        """
        Emit EXG, Marker and ORN signals
        """
        self.emit_orn()
        self.emit_exg()
        self.emit_marker()

    def emit_exg(self, stop=False):
        """
        Get EXG data from packet and emit signal
        """

        stream_processor = self.explorer.stream_processor
        chan_list = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]

        def callback(packet):
            exg_fs = stream_processor.device_info['sampling_rate']
            timestamp, exg = packet.get_data(exg_fs)

            # From timestamp to seconds
            if self._vis_time_offset is None:
                self._vis_time_offset = timestamp[0]
            time_vector = timestamp - self._vis_time_offset

            # Downsampling
            if Settings.DOWNSAMPLING:
                exg = exg[:, ::int(exg_fs / Settings.EXG_VIS_SRATE)]
                time_vector = time_vector[::int(exg_fs / Settings.EXG_VIS_SRATE)]

            # Baseline correction
            # if True: # if testing
            if self.plotting_filters is not None and self.plotting_filters["offset"]:
                samples_avg = exg.mean(axis=1)
                if self._baseline_corrector["baseline"] is None:
                    self._baseline_corrector["baseline"] = samples_avg
                else:
                    self._baseline_corrector["baseline"] -= (
                                (self._baseline_corrector["baseline"] - samples_avg) / self._baseline_corrector["MA_length"] *
                                exg.shape[1])

                exg -= self._baseline_corrector["baseline"][:, np.newaxis]
            else:
                self._baseline_corrector["baseline"] = None

            # Update ExG unit
            try:
                exg = self.offsets + exg / self.y_unit
            # exg /= self.y_unit

                data = dict(zip(chan_list, exg))
                data['t'] = time_vector
                self.signal_exg.emit(data)

            except Exception as e:
                print(e)

        if stop:
            stream_processor.unsubscribe(topic=TOPICS.filtered_ExG, callback=callback)
            print("unsubscribe")
            return

        stream_processor.subscribe(topic=TOPICS.filtered_ExG, callback=callback)

    def emit_orn(self):
        """"
        Get orientation data and emit signal
        """
        stream_processor = self.explorer.stream_processor

        def callback(packet):
            timestamp, orn_data = packet.get_data()
            if self._vis_time_offset is None:
                self._vis_time_offset = timestamp[0]
            time_vector = list(np.asarray(timestamp) - self._vis_time_offset)

            data = dict(zip(Settings.ORN_LIST, np.array(orn_data)[:, np.newaxis]))
            data['t'] = time_vector

            self.signal_orn.emit(data)

        stream_processor.subscribe(topic=TOPICS.raw_orn, callback=callback)

    def emit_marker(self):
        """
        Get marker data from packet and emit signal
        """
        stream_processor = self.explorer.stream_processor

        def callback(packet):
            timestamp, _ = packet.get_data()
            if self._vis_time_offset is None:
                self._vis_time_offset = timestamp[0]
            time_vector = list(np.asarray(timestamp) - self._vis_time_offset)

            data = [time_vector[0], self.ui.value_event_code.text()]
            self.signal_mkr.emit(data)

        stream_processor.subscribe(topic=TOPICS.marker, callback=callback)

    #########################
    # Swipping Plot Functions
    #########################
    @Slot(dict)
    def plot_exg(self, data):
        """
        Plot and update exg data
        """

        n_new_points = len(data["t"])
        # n_new_points = len(data["t"]) + 1
        idxs = np.arange(self.exg_pointer, self.exg_pointer+n_new_points)

        self.exg_plot_data[0].put(idxs, data["t"], mode="wrap")  # replace values with new points
        # self.t_exg_plot.put(idxs, data["t"], mode="wrap")  # replace values with new points
        self.last_t = data["t"][-1]

        # for i, ch in enumerate(self.exg_plot.keys()):
        for i, ch in enumerate(self.exg_plot_data[1].keys()):
            d = data[ch]
            # d = np.concatenate((data[ch], np.array([np.NaN])))
            self.exg_plot_data[1][ch].put(idxs, d, mode="wrap")
            # self.exg_plot[ch][self.exg_pointer+n_new_points]=np.NaN

        self.exg_pointer += n_new_points

        # if wrap happen -> pointer>length:
        if self.exg_pointer >= len(self.exg_plot_data[0]):
            while self.exg_pointer >= len(self.exg_plot_data[0]):
                self.exg_pointer -= len(self.exg_plot_data[0])

            self.exg_plot_data[0][self.exg_pointer:] += self.get_timeScale()

            t_min = int(round(np.mean(data["t"])))
            # t_min = int(data["t"][-1])
            t_max = int(t_min + self.get_timeScale())
            self.ui.plot_exg.setXRange(t_min, t_max, padding=0.01)

            # Remove marker line and replot in the new axis
            for idx_t in range(len(self.mrk_plot["t"])):
                if self.mrk_plot["t"][idx_t] < self.exg_plot_data[0][0]:
                    self.ui.plot_exg.removeItem(self.mrk_plot["line"][idx_t])
                    new_data = [
                        self.mrk_plot["t"][idx_t] + self.get_timeScale(),
                        self.mrk_plot["code"][idx_t]
                    ]
                    self.plot_mkr(new_data, replot=True)

        # Position line:
        if self.line is not None:
            self.line.setPos(data["t"][-1])

        else:
            self.line = self.ui.plot_exg.addLine(data["t"][-1], pen="#FF0000")

        # connection = np.full(len(self.t_exg_plot), 1)
        # connection[self.exg_pointer-1:self.exg_pointer] = 0

        # Paint curves
        for curve, ch in zip(self.curves_list, self.active_chan):
            # curve.setData(self.t_exg_plot, self.exg_plot[ch], connect=connection)
            # curve.setData(self.t_exg_plot, self.exg_plot[ch])
            curve.setData(self.exg_plot_data[0], self.exg_plot_data[1][ch])

        # Remove reploted markers
        for idx_t in range(len(self.mrk_replot["t"])):
            if self.mrk_replot["t"][idx_t] < data["t"][-1]:
                self.ui.plot_exg.removeItem(self.mrk_replot["line"][idx_t])

    @Slot(dict)
    def plot_mkr(self, data, replot=False):
        """
        Plot and update marker data
        """
        t, code = data

        if replot is False:
            mrk_dict = self.mrk_plot
            color = Settings.MARKER_LINE_COLOR
        else:
            mrk_dict = self.mrk_replot
            color = Settings.MARKER_LINE_COLOR_ALPHA

        mrk_dict["t"].append(t)
        mrk_dict["code"].append(code)
        pen_marker = pg.mkPen(color=color, dash=[4, 4])

        line = self.ui.plot_exg.addLine(t, label=code, pen=pen_marker)
        mrk_dict["line"].append(line)

    @Slot(dict)
    def plot_orn(self, data):
        """
        Plot and update ORN data
        """
        n_new_points = len(data["t"])
        idxs = np.arange(self.orn_pointer, self.orn_pointer+n_new_points)

        self.t_orn_plot.put(idxs, data["t"], mode="wrap")  # replace values with new points

        for k in self.orn_plot.keys():
            self.orn_plot[k].put(idxs, data[k], mode="wrap")

        self.orn_pointer += n_new_points

        # if wrap happen -> pointer>length:
        if self.orn_pointer >= len(self.t_orn_plot):
            while self.orn_pointer >= len(self.t_orn_plot):
                self.orn_pointer -= len(self.t_orn_plot)

            self.t_orn_plot[self.orn_pointer:] += self.get_timeScale()

            t_min = int(round(np.mean(data["t"])))
            # t_min = int(data["t"][-1])
            t_max = int(t_min + self.get_timeScale())
            for plt in self.plots_orn_list:
                plt.setXRange(t_min, t_max, padding=0.01)
        # Position line
        if None in self.lines_orn:
            for i, plt in enumerate(self.plots_orn_list):
                self.lines_orn[i] = plt.addLine(data["t"][-1], pen="#FF0000")
        else:
            for line in self.lines_orn:
                try:
                    line.setPos(data["t"][-1])
                except RuntimeError:
                    self.lines_orn = [None, None, None]
                    # pass

        # Paint curves
        self.curve_ax.setData(self.t_orn_plot, self.orn_plot["accX"])
        self.curve_ay.setData(self.t_orn_plot, self.orn_plot["accY"])
        self.curve_az.setData(self.t_orn_plot, self.orn_plot["accZ"])
        self.curve_gx.setData(self.t_orn_plot, self.orn_plot["gyroX"])
        self.curve_gy.setData(self.t_orn_plot, self.orn_plot["gyroY"])
        self.curve_gz.setData(self.t_orn_plot, self.orn_plot["gyroZ"])
        self.curve_mx.setData(self.t_orn_plot, self.orn_plot["magX"])
        self.curve_my.setData(self.t_orn_plot, self.orn_plot["magY"])
        self.curve_mz.setData(self.t_orn_plot, self.orn_plot["magZ"])

    @Slot()
    def plot_fft(self):

        pw = self.ui.plot_fft
        pw.clear()
        pw.setXRange(0, 70, padding=0.01)

        exg_fs = self.explorer.stream_processor.device_info['sampling_rate']
        # exg_data = np.array([self.exg_plot[key][~np.isnan(self.exg_plot[key])] for key in self.exg_plot.keys()])
        exg_data = np.array(
            [self.exg_plot_data[1][key][~np.isnan(self.exg_plot_data[1][key])] for key in self.exg_plot_data[1].keys()])

        if exg_data.shape[1] < exg_fs * 5:
            return

        fft_content, freq = self.get_fft(exg_data, exg_fs)
        data = dict(zip(self.exg_plot_data[1].keys(), fft_content))
        # data = dict(zip(self.exg_plot.keys(), fft_content))
        data['f'] = freq

        for i in range(len(data.keys())):
            key = list(data.keys())[i]
            if key != "f":
                pw.plot(data["f"], data[key], pen=Settings.FFT_LINE_COLORS[i], name=key)

    #########################
    # Moving Plot Functions
    #########################

    #########################
    # Functions
    #########################
    @Slot()
    def set_marker(self):
        """
        Get the value for the event code from the GUI and set the event.
        """
        event_code = self.ui.value_event_code.text()
        try:
            self.explorer.set_marker(int(event_code))
        except ValueError as e:
            self.display_msg(msg_text=str(e))
            # QMessageBox.critical(self, "Error", str(e))

        # Clean input text box
        self.ui.value_event_code.setText("")

    @Slot()
    def change_timescale(self):
        """
        Change ExG and ORN plots time scale
        """
        t_min = self.last_t
        t_max = int(t_min + self.get_timeScale())
        self.ui.plot_exg.setXRange(t_min, t_max, padding=0.01)
        for plt in self.plots_orn_list:
            plt.setXRange(t_min, t_max, padding=0.01)

        new_size = self.plot_points()
        self.exg_pointer = 0
        self.exg_plot_data[0] = np.array([np.NaN]*new_size)
        self.exg_plot_data[1] = {ch: np.array([np.NaN]*new_size) for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}

        new_size_orn = self.plot_points(orn=True)
        self.orn_pointer = 0
        self.t_orn_plot = np.array([np.NaN]*new_size_orn)
        self.orn_plot = {k: np.array([np.NaN]*new_size_orn) for k in Settings.ORN_LIST}

    @Slot()
    def change_scale(self):
        """
        Change y-axis scale in ExG plot
        """
        old = Settings.SCALE_MENU[self.y_string]
        new = Settings.SCALE_MENU[self.ui.value_yAxis.currentText()]

        old_unit = 10 ** (-old)
        new_unit = 10 ** (-new)

        self.y_string = self.ui.value_yAxis.currentText()
        self.y_unit = new_unit

        stream_processor = self.explorer.stream_processor
        self.chan_key_list = [Settings.CHAN_LIST[i].lower()
                              for i, mask in enumerate(reversed(stream_processor.device_info['adc_mask'])) if
                              mask == 1]

        # for chan, value in self.exg_plot.items():
        for chan, value in self.exg_plot_data[1].items():
            if self.chan_dict[chan] == 1:
                temp_offset = self.offsets[self.chan_key_list.index(chan)]
                # self.exg_plot[chan] = (value - temp_offset) * (old_unit / new_unit) + temp_offset
                self.exg_plot_data[1][chan] = (value - temp_offset) * (old_unit / new_unit) + temp_offset

        self.r_peak['r_peak'] = (np.array(self.r_peak['r_peak']) - self.offsets[0]) * \
            (old_unit / self.y_unit) + self.offsets[0]

    def plot_heart_rate(self):
        if self.ui.value_signal.currentText() == "EEG":
            return

        # if "ch1" not in self.exg_plot.keys():
        if "ch1" not in self.exg_plot_data[1].keys():
            print('Heart rate estimation works only when channel 1 is enabled.')
            msg = "Heart rate estimation works only when channel 1 is enabled."
            # QMessageBox.information(self, "!", msg)
            self.display_msg(msg_text=msg, type="info")
            return

        # first_chan = self.exg_plot.keys()[0]

        exg_fs = self.explorer.stream_processor.device_info['sampling_rate']

        if self.rr_estimator is None:
            self.rr_estimator = HeartRateEstimator(fs=exg_fs)

        # ecg_data = (np.array(self.exg_plot['ch1'])[-2 * Settings.EXG_VIS_SRATE:] - self.offsets[0]) * self.y_unit
        ecg_data = (
            np.array(self.exg_plot_data[1]['ch1'])[-2 * Settings.EXG_VIS_SRATE:] - self.offsets[0]) * self.y_unit
        # ecg_data = (np.array(self.exg_plot[first_chan])[-2 * Settings.EXG_VIS_SRATE:] - self.offsets[0]) * self.y_unit
        # time_vector = np.array(self.t_exg_plot)[-2 * Settings.EXG_VIS_SRATE:]
        time_vector = np.array(self.exg_plot_data[0])[-2 * Settings.EXG_VIS_SRATE:]

        # Check if the peak2peak value is bigger than threshold
        if (np.ptp(ecg_data) < Settings.V_TH[0]) or (np.ptp(ecg_data) > Settings.V_TH[1]):
            print("P2P value larger or less than threshold. Cannot compute heart rate!")
            return

        peaks_time, peaks_val = self.rr_estimator.estimate(ecg_data, time_vector)
        peaks_val = (np.array(peaks_val) / self.y_unit) + self.offsets[0]
        if peaks_time:
            self.r_peak['t'].append(peaks_time)
            list(self.r_peak['r_peak']).append(peaks_val)

            points = self.ui.plot_exg.plot(
                peaks_time, peaks_val, pen=None, symbolBrush=(200, 0, 0), symbol='o', symbolSize=8)

            self.r_peak["points"].extend([points])
            # print(dict(zip(['r_peak', 't'], [peaks_val, peaks_time])))

        # Update heart rate cell
        estimated_heart_rate = self.rr_estimator.heart_rate
        self.ui.value_heartRate.setText(str(estimated_heart_rate))

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

    def popup_filters(self):
        """
        Open plot filter dialog and apply filters
        """

        wait = True if self.plotting_filters is None else False
        sr = self.explorer.stream_processor.device_info['sampling_rate']
        dialog = PlotDialog(sr=sr, current_filters=self.plotting_filters)
        filters = dialog.exec()
        if filters is False:
            return False
        else:
            self.plotting_filters = filters
            AppFunctions.plotting_filters = self.plotting_filters
            self.apply_filters()
            # self.loading = LoadingScreen()
            if wait:
                time.sleep(1.5)
            return True
