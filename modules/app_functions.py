import time
from typing import NewType
from explorepy import stream_processor
from explorepy.stream_processor import TOPICS
from scipy.ndimage.measurements import label
from main import *
import numpy as np
from modules.app_settings import Settings
from explorepy.tools import bt_scan
import numpy as np
from scipy.ndimage import gaussian_filter1d
import pandas as pd
from PySide6.QtWidgets import QApplication

class AppFunctions(MainWindow):

    def __init__(self):
        super().__init__()

    # ///////////////////////////////////
    # ///// START GENERAL FUNCTIONS/////

    def init_dropdowns(self):
        '''
        Initilize the GUI dropdowns with the values specified above
        '''
        # value_signal_type
        self.ui.value_signal.addItems(Settings.MODE_LIST)

        # value_yaxis
        self.ui.value_yAxis.addItems(Settings.SCALE_MENU.keys())
        self.ui.value_yAxis.setCurrentText("1 mV")

        # value_time_scale
        self.ui.value_timeScale.addItems(Settings.TIME_RANGE_MENU.keys())

        # value_sampling_rate
        self.ui.value_sampling_rate.addItems([str(int(sr)) for sr in Settings.SAMPLING_RATES])

        self.ui.value_event_code.setValidator(QIntValidator(8, 65535))

        # self.ui.cb_swipping_rec.setChecked(True)

        self.ui.imp_mode.addItems(["Wet electrodes", "Dry electrodes"])

    def change_footer(self):
        """
        Change the fields for device and firmware in the GUI footer
        """
        if self.is_connected:
            dev_name = self.explorer.stream_processor.device_info[
                "device_name"]
            device_lbl = f"Connected to {dev_name}"
            firmware = self.explorer.stream_processor.device_info[
                "firmware_version"]
        else:
            device_lbl = "Not connected"
            firmware = "NA"

        self.ui.ft_label_device_3.setText(device_lbl)
        self.ui.ft_label_firmware_value.setText(firmware)

    # ///// END GENERAL FUNCTIONS/////

    # //////////////////// ///////////////
    # ///// START FUNCTIONS SETTINGS PAGE /////

    def change_btn_connect(self):
        '''
        Change connect buttonn to Connect/Disconnect depending on explore status
        '''
        if self.is_connected:
            self.ui.btn_connect.setText("Disconnect")
        else:
            self.ui.btn_connect.setText("Connect")


    def update_frame_dev_settings(self):
        """
        Update the frame with the device settings.
        Only shown if a device is connected
        """
        self.explorer._check_connection()

        if self.is_connected:
            explore = self.explorer
            stream_processor = explore.stream_processor

            # ///// CONFIGURE DEVICE FRAME /////
            # Set device name
            self.ui.label_explore_name.setText(
                stream_processor.device_info["device_name"])

            # Set active channels
            n_chan = stream_processor.device_info['adc_mask']
            n_chan = [i for i in reversed(n_chan)]

            self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))

            for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
                w.setChecked(self.chan_dict[w.objectName().replace("cb_", "")])

            self.exg_plot = {ch:[] for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}

            # Set sampling rate (value_sampling_rate)
            sr = stream_processor.device_info['sampling_rate']
            self.ui.value_sampling_rate.setCurrentText(str(int(sr)))
            # ////////

            # Show the device frame
            self.ui.frame_device.show()
            self.ui.line_2.show()

        else:
            self.ui.frame_device.hide()
            self.ui.line_2.hide()

    def scan_devices(self):
        """"
        Scans for available explore devices.
        """

        self.ui.list_devices.clear()
        explore_devices = bt_scan()
        explore_devices = [dev[0] for dev in explore_devices]
        if len(explore_devices) == 0:
            print("No explore devices found. Please make sure it is turn on and click on reescan")

        self.ui.list_devices.addItems(explore_devices)

    def connect2device(self):
        """
        Connect to the explore device
        """
        if self.is_connected is False:
            device_name = self.ui.list_devices.selectedItems()[0].text()
            print(device_name)
            self.ui.ft_label_device_3.setText(f"Connecting ...")
            QApplication.processEvents()

            self.explorer.connect(device_name=device_name)
            self.is_connected = True

        else:
            self.explorer.disconnect()
            self.is_connected = False

        print(self.is_connected)
        # change footer & button text:                
        AppFunctions.change_footer(self)
        AppFunctions.change_btn_connect(self)
        # if self.is_connected:
            # AppFunctions.info_device(self)
        AppFunctions.info_device(self)
        # (un)hide settings frame
        AppFunctions.update_frame_dev_settings(self)

    def info_device(self):
        r"""
        Update device information
        """
        self.explorer._check_connection()

        def callback(packet):
            # print(packet)
            new_info = packet.get_data()
            # print(new_info)
            for key in new_info.keys():
                if key == "temperature":
                    new_value = str(new_info[key][0]) if self.is_connected else "NA"
                    AppFunctions._update_temperature(self, new_value=new_value)
                    # print("\n\ntemperature", new_info[key])

                elif key == "battery":
                    self.battery_percent_list.append(new_info[key][0])
                    if len(self.battery_percent_list) > Settings.BATTERY_N_MOVING_AVERAGE:
                        del self.battery_percent_list[0]
                    value = int(np.mean(self.battery_percent_list))
                    value = 1 if value < 1 else value
                    new_value = value if self.is_connected else "NA"
                    stylesheet = AppFunctions._battery_stylesheet(self, value=new_value)
                    AppFunctions._update_battery(self, new_value=str(new_value), new_stylesheet=stylesheet)

                elif key == "fimrware":
                    # print("firmware callback: ", new_info[key])
                    new_value = new_info[key] if self.is_connected else "NA"
                    AppFunctions._update_firmware(self, new_value=new_value)

                elif key == "device_name":
                    # print("name callback: ", new_info[key])
                    connected_lbl = f"Connected to {new_info[key]}"
                    not_connected_lbl = "Not connected"
                    new_value = connected_lbl if self.is_connected else not_connected_lbl
                    AppFunctions._update_device_name(self, new_value=new_value)

            QApplication.processEvents()

        self.explorer.stream_processor.subscribe(callback=callback, topic=TOPICS.device_info)
        self.explorer.stream_processor.subscribe(callback=callback, topic=TOPICS.env)

    def format_memory(self):
        r"""
        Display a popup asking for confirmation.
        If yes, memory is formatted.
        """

        question = "Are you sure you want to format the memory?"
        response = QMessageBox.question(self, "Confirmation", question)
        if response == QMessageBox.StandardButton.Yes:
            self.explorer.format_memory()
        else:
            return

    def reset_settings(self):
        r"""
        Display a popup asking for confirmation.
        If yes, the settinngs are set to default.
        """

        question = "Are you sure you want to reset your settings?"
        response = QMessageBox.question(self, "Confirmation", question)
        if response == QMessageBox.StandardButton.Yes:
            self.explorer.reset_soft()
            print(self.explorer.stream_processor.device_info['sampling_rate'])
        else:
            return

    def calibrate_orn(self):
        r"""
        Calibrate the orientation
        """
        question = ("Do you want to continue with the orientation sensors calibration?\n"
            "This will overwrite the calibration data if it already exists\n\n"
            "If yes, you would need to move and rotate the device for 100 seconds\n"
            )
        response = QMessageBox.question(self, "Confirmation", question)
        

        if response == QMessageBox.StandardButton.Yes:
            self.explorer.calibrate_orn(do_overwrite=True)
            QMessageBox.information(self, "Done", "Calibration Complete")
        else:
            return

    def change_sampling_rate(self):
        """
        Change the sampling rate
        """
        sr = self.explorer.stream_processor.device_info['sampling_rate']
        str_value = self.ui.value_sampling_rate.currentText()
        value = int(str_value)
        if int(sr) != value:
            # print(value)
            print(
                "Old Sampling rate: ",
                self.explorer.stream_processor.device_info['sampling_rate'])
            self.explorer.set_sampling_rate(sampling_rate=value)
            print(
                "New Sampling rate: ",
                self.explorer.stream_processor.device_info['sampling_rate'])
        else:
            print("Same sampling rate")


    def change_active_channels(self):
        """
        Read selected checkboxes and set the channel mask of the device
        """
        active_chan = []

        for w in self.ui.frame_cb_channels.findChildren(QCheckBox):
            status = str(1) if w.isChecked() else str(0)
            active_chan.append(status)
            # print(w.objectName(), w.isChecked())
            # w.setChecked(self.chan_dict[w.objectName().replace("cb_", "")])
        active_chan_int = [int(i) for i in active_chan]
        active_chan = [i for i in reversed(active_chan)]

        if active_chan_int != self.explorer.stream_processor.device_info['adc_mask']:
            mask = "".join(active_chan)
            int_mask = int(mask, 2)
            self.explorer.set_channels(int_mask)

            print(self.explorer.stream_processor.device_info['adc_mask'])
            n_chan = self.explorer.stream_processor.device_info['adc_mask']
            n_chan = [i for i in reversed(n_chan)]
            self.chan_dict = dict(
                    zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
            self.exg_plot = {ch:[] for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1}
        else:
            print("Same channel mask")

    def change_settings(self):
        """
        Apply changes in device settings
        """
        stream_processor = self.explorer.stream_processor
        AppFunctions.change_active_channels(self)
        AppFunctions.change_sampling_rate(self)
        act_chan = ", ".join([ch for ch in self.chan_dict if self.chan_dict[ch]==1])
        title = "!"
        msg = (
            "Device settings have been changed:"
            f"\nSampling Rate: {int(stream_processor.device_info['sampling_rate'])}"
            f"\nActive Channels: {act_chan}"
        )
        QMessageBox.information(self, title, msg)

    # ///// END SETTINGS PAGE FUNCTIONS /////

    # //////////////////// ///////////////
    # ///// START PLOT PAGE FUNCTIONS/////

    def start_stop_streaming(self):
        '''
        Start or stop acquiring signal
        '''
        # if self.is_connected:
        if self.is_streaming is False:
            self.ui.btn_stream.setText("Stop Data Stream")
            print(Settings.START_BUTTON_STYLESHEET)
            self.ui.btn_stream.setStyleSheet(Settings.STOP_BUTTON_STYLESHEET)
            self.explorer.acquire()
            self.is_streaming = True
        else:
            self.ui.btn_stream.setText("Start Data Stream")
            self.ui.btn_stream.setStyleSheet(Settings.START_BUTTON_STYLESHEET)
            self.is_streaming = False

    def set_marker(self):
        '''
        Get the value for the event code and mark it
        '''
        event_code = self.ui.value_event_code.text()
        self.explorer.set_marker(int(event_code))

    # ///// END PLOT PAGE FUNCTIONS/////

    # ////////////////////////////////////////
    # ///// START IMPEDANCE PAGE FUNCTIONS/////
    def disable_imp(self):
        if self.is_connected:
            self.explorer.stream_processor.disable_imp()
        else:
            return

    def emit_imp(self):
        """
        Update impedances
        """

        stream_processor = self.explorer.stream_processor
        n_chan = stream_processor.device_info['adc_mask']
        self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
        chan_list = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]
        data = {ch: ["", AppFunctions._impedance_stylesheet_wet(self, "")] for ch in chan_list}

        def callback(packet):
            packet_imp = stream_processor.imp_calculator.measure_imp(packet=packet)

            imp_values = packet_imp.get_impedances()
            for chan, value in zip(chan_list, imp_values):
                # print(chan, value)
                value = value/2
                # print(value)
                if value < 5:
                    str_value = "<5"
                elif value > 500:
                    str_value = ">500"
                else:
                    str_value = str(round(value, 0))
                # str_value = "<5" if value < 5 else str(round(value, 0))
                str_value += " K\u03A9"
                if self.ui.imp_mode.currentText() == "Dry electrodes":
                    ch_stylesheet = AppFunctions._impedance_stylesheet_dry(self, value=value)
                else: 
                    ch_stylesheet = AppFunctions._impedance_stylesheet_wet(self, value=value)

                data[chan] = [str_value, ch_stylesheet]

            self.signal_imp.emit(data)

        if self.is_connected is False:
            return

        else:
            # if self.is_imp_measuring is False: 
            # print("start")
            self.explorer._check_connection()
            if int(stream_processor.device_info["sampling_rate"]) != 250:
                question = (
                    "Impedance mode only works in 250 Hz sampling rate!"
                    "\nThe current sampling rate is "
                    f"{int(stream_processor.device_info['sampling_rate'])}."
                    "Click on Confirm to change the sampling rate.")

                response = QMessageBox.question(self, "Confirmation", question)
                if response == QMessageBox.StandardButton.Yes:
                    self.explorer.set_sampling_rate(sampling_rate=250)
                    self.ui.value_sampling_rate.setCurrentText(str(250))
                else:
                    return

            stream_processor.imp_initialize(notch_freq=50)
            stream_processor.subscribe(callback=callback, topic=TOPICS.imp)
            self.is_imp_measuring = True

            # else:
            #    print("stop")
            #    self.is_imp_measuring = False
            #    self.signal_imp.disconnect()

    # ///// END IMPEDANCE PAGE FUNCTIONS/////

    # ////////////////////////////////////////
    # ///// START INTEGRATION PAGE FUNCTIONS/////

    def push_lsl(self):
        # TODO theres an error in explrorepy
        duration = self.ui.duration_push_lsl.value()
        self.explorer.push2lsl(duration=duration)
    # ///// END INTEGRATION PAGE FUNCTIONS/////

    # ////////////////////////////////////////
    # ///// START/////
    # ########### Start Plotting Functions ################
    def emit_signals(self):
        AppFunctions.emit_orn(self)
        AppFunctions.emit_exg(self)
        # AppFunctions.emit_fft(self)
        AppFunctions.emit_marker(self)

    def init_plot_orn(self):
        # pw = self.ui.graphicsView #testinng
        pw = self.ui.plot_orn

        plot_acc = pw.addPlot()
        pw.nextRow()
        plot_gyro = pw.addPlot()
        pw.nextRow()
        plot_mag = pw.addPlot()

        plots_orn_list = [plot_acc, plot_gyro, plot_mag]

        plot_acc.setXLink(plot_mag)
        plot_gyro.setXLink(plot_mag)

        plot_acc.getAxis("bottom").setStyle(showValues=False)
        plot_gyro.getAxis("bottom").setStyle(showValues=False)

        for plt,lbl in zip(plots_orn_list, ['Acc [mg/LSB]', 'Gyro [mdps/LSB]', 'Mag [mgauss/LSB]']):
            plt.addLegend(horSpacing=20, colCount=3, brush="k")
            plt.getAxis("left").setWidth(80)
            plt.getAxis("left").setLabel(lbl)

        self.curve_ax = plot_acc.plot(pen=Settings.ORN_LINE_COLORS[0], name="accX")
        self.curve_ay = plot_acc.plot(pen=Settings.ORN_LINE_COLORS[1], name="accY")
        self.curve_az = plot_acc.plot(pen=Settings.ORN_LINE_COLORS[2], name="accZ")

        self.curve_gx = plot_gyro.plot(pen=Settings.ORN_LINE_COLORS[0], name="gyroX")
        self.curve_gy = plot_gyro.plot(pen=Settings.ORN_LINE_COLORS[1], name="gyroY")
        self.curve_gz = plot_gyro.plot(pen=Settings.ORN_LINE_COLORS[2], name="agyro")

        self.curve_mx = plot_mag.plot(pen=Settings.ORN_LINE_COLORS[0], name="magX")
        self.curve_my = plot_mag.plot(pen=Settings.ORN_LINE_COLORS[1], name="magY")
        self.curve_mz = plot_mag.plot(pen=Settings.ORN_LINE_COLORS[2], name="magZ")


    def init_plot_exg(self):
        # pw = self.ui.graphicsView #testinng
        pw = self.ui.plot_exg
        self.plot_ch8 = pw.addPlot()
        pw.nextRow()
        self.plot_ch7 = pw.addPlot()
        pw.nextRow()
        self.plot_ch6 = pw.addPlot()
        pw.nextRow()
        self.plot_ch5 = pw.addPlot()
        pw.nextRow()
        self.plot_ch4 = pw.addPlot()
        pw.nextRow()
        self.plot_ch3 = pw.addPlot()
        pw.nextRow()
        self.plot_ch2 = pw.addPlot()
        pw.nextRow()
        self.plot_ch1 = pw.addPlot()

        self.plots_list = [
            self.plot_ch1, self.plot_ch2, self.plot_ch3, self.plot_ch4,
            self.plot_ch5, self.plot_ch6, self.plot_ch7, self.plot_ch8
        ]

        for idx, plt in enumerate(self.plots_list):
            plt.getAxis("left").setTicks([[(0, f"ch{idx+1}")]])
            plt.getAxis("left").setWidth(80)
            plt.showGrid(x=False, y=True, alpha=0.5)
            if idx != 0:
                plt.setXLink(self.plot_ch1)
                plt.getAxis("bottom").setStyle(showValues=False)
                plt.hideAxis("bottom")
            
        self.curve_ch1 = self.plot_ch1.plot(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch2 = self.plot_ch2.plot(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch3 = self.plot_ch3.plot(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch4 = self.plot_ch4.plot(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch5 = self.plot_ch5.plot(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch6 = self.plot_ch6.plot(pen=Settings.EXG_LINE_COLOR)
        self.curve_ch7 = self.plot_ch7.plot(pen=Settings.EXG_LINE_COLOR)
        # self.plots_list = [self.plot_ch8]
        self.curve_ch8 = self.plot_ch8.plot(pen=Settings.EXG_LINE_COLOR)



    def emit_exg(self):
        """
        Get EXG data and plot
        """
        stream_processor = self.explorer.stream_processor
        chan_list = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]

        #TODO: change if not testing
        '''stream_processor.add_filter(
                cutoff_freq=(.5, 30), filter_type='bandpass')
        stream_processor.add_filter(cutoff_freq=50, filter_type='notch')'''
        
        notch_freq = self.plotting_filters["notch"]
        high_freq = self.plotting_filters["highpass"]
        low_freq = self.plotting_filters["lowpass"]

        if notch_freq is not None:
            stream_processor.add_filter(cutoff_freq=notch_freq, filter_type='notch')

        if high_freq is not None and low_freq is not None:
            stream_processor.add_filter(
                cutoff_freq=(low_freq, high_freq), filter_type='bandpass')
        elif high_freq is not None:
            stream_processor.add_filter(cutoff_freq=high_freq, filter_type='highpass')
        elif low_freq is not None:
            stream_processor.add_filter(cutoff_freq=low_freq, filter_type='lowpass')

        print(self.plotting_filters)

        def callback(packet):
            exg_fs = stream_processor.device_info['sampling_rate']
            timestamp, exg = packet.get_data(exg_fs)

            # From timestamp to seconds
            if self._vis_time_offset is None:
                self._vis_time_offset = timestamp[0]
            time_vector = timestamp - self._vis_time_offset
            
            # Downsampling
            exg = exg[:, ::int(exg_fs / Settings.EXG_VIS_SRATE)]
            time_vector = time_vector[::int(exg_fs / Settings.EXG_VIS_SRATE)]

            # Baseline correction
            if self.plotting_filters["offset"]:
            # if True:
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

            # exg_simple = exg[0]
            # data = [time_vector, exg_simple]
            # exg_chan = dict(zip(chan_list, exg))

            # Update ExG unit
            # exg = self.offsets + exg / self.y_unit
            exg /= self.y_unit

            data = dict(zip(chan_list, exg))
            data['t'] = time_vector
            self.signal_exg.emit(data)
            # time.sleep(0.5)

        stream_processor.subscribe(topic=TOPICS.filtered_ExG, callback=callback)

    def plot_exg(self, data):
        
        # max_points = 100
        max_points = AppFunctions._plot_points(self) / 2
        # print(data["t"])
        # t_nosc = [t*10e9 for t in data["t"]]
        # print(t_nosc)
        # print(data)

        if len(self.t_exg_plot)>max_points:
            # self.plot_ch8.clear()
            # self.curve_ch8 = self.plot_ch8.plot(pen=Settings.EXG_LINE_COLOR)
            self.t_exg_plot = self.t_exg_plot[8:]
            for ch in self.exg_plot.keys():
                self.exg_plot[ch] = self.exg_plot[ch][8:]
            
            for idx_t in range(len(self.mrk_plot["t"])):
                if self.mrk_plot["t"][idx_t] < self.t_exg_plot[0]:
                    # self.plot_ch8.removeItem(self.mrk_plot["line"][idx_t])
                    for i, plt in enumerate(self.plots_list):
                        plt.removeItem(self.mrk_plot["line"][idx_t][i])
                    
        self.t_exg_plot.extend(data["t"])
        for ch in self.exg_plot.keys():
            self.exg_plot[ch].extend(data[ch])

        self.curve_ch1.setData(self.t_exg_plot, self.exg_plot["ch1"])
        self.curve_ch2.setData(self.t_exg_plot, self.exg_plot["ch2"])
        self.curve_ch3.setData(self.t_exg_plot, self.exg_plot["ch3"])
        self.curve_ch4.setData(self.t_exg_plot, self.exg_plot["ch4"])
        self.curve_ch5.setData(self.t_exg_plot, self.exg_plot["ch5"])
        self.curve_ch6.setData(self.t_exg_plot, self.exg_plot["ch6"])
        self.curve_ch7.setData(self.t_exg_plot, self.exg_plot["ch7"])
        self.curve_ch8.setData(self.t_exg_plot, self.exg_plot["ch8"])
        
        # self.curve_ch8.setData(self.t_exg_plot, self.exg_plot["ch1"])


    def emit_fft(self):
        """
        Get FFT data and plot it
        """
        stream_processor = self.explorer.stream_processor
        n_chan = stream_processor.device_info['adc_mask']
        self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
        chan_list = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]

        def callback(packet):
            exg_fs = stream_processor.device_info['sampling_rate']
            _, exg = packet.get_data(exg_fs)
            print(exg)
            print(type(exg))
            print(len(exg))
            '''if exg.shape[1] < exg_fs * 5:
                return'''
            fft_content, freq = AppFunctions.get_fft(exg, exg_fs)

            data = dict(zip(chan_list, fft_content))
            data['f'] = freq
            # print(data)
            # print(len(data))

            self.signal_fft.emit(data)

        stream_processor.subscribe(topic=TOPICS.filtered_ExG, callback=callback)
        '''time.sleep(0.5)
        stream_processor.unsubscribe(topic=TOPICS.filtered_ExG, callback=callback)'''



    def plot_fft(self, data):
        pw = self.ui.graphicsView
        pw.setLabel("bottom", "Frequency", units="Hz")
        pw.setLabel("left", "Amplitude", units="V")
        pw.setLogMode(x=True)
        pw.showGrid(True, True, alpha=0.3)

        for i in range(len(data.keys())):
            key = list(data.keys())[i]
            if key != "f":
                pw.plot(data["f"], data[key], pen=Settings.FFT_LINE_COLORS[i], name=key)
        pw.addLegend()


    def get_fft(exg, s_rate):
        """
        Compute FFT
        Args:
            exg: exg data froom ExG packet
            s_rate (int): sampling rate
        """
        n_point = 1024
        exg -= exg.mean(axis=1)[:, np.newaxis]
        freq = s_rate * np.arange(int(n_point / 2)) / n_point
        fft_content = np.fft.fft(exg, n=n_point) / n_point
        fft_content = np.abs(fft_content[:, range(int(n_point / 2))])
        fft_content = gaussian_filter1d(fft_content, 1)
        return fft_content[:, 1:], freq[1:]

    

    def emit_orn(self):
        """"
        Get orientation data
        """
        stream_processor = self.explorer.stream_processor
        chan_list = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]
        import pandas as pd
        self.df = pd.DataFrame(columns=chan_list.append("t"))
        def callback(packet):
            timestamp, orn_data = packet.get_data()
            # if self._vis_time_offset is None:
            #     self._vis_time_offset = timestamp[0]
            # timestamp -= self._vis_time_offset
            # timestamp -= timestamp[0]
            data = dict(zip(Settings.ORN_LIST, np.array(orn_data)[:, np.newaxis]))
            data['t'] = timestamp
            dftemp = pd.DataFrame.from_dict(data)
            self.df = self.df.append(dftemp)
            
            self.signal_orn.emit(data)

        stream_processor.subscribe(topic=TOPICS.raw_orn, callback=callback)

    def plot_orn(self, data):
        
        # sr = self.explorer.stream_processor.device_info['sampling_rate']
        # time_scale = Settings.TIME_RANGE_MENU[self.ui.value_timeScale.currentText()]

        max_points = AppFunctions._plot_points(self)
        # max_points = 100
        if len(self.t_orn_plot)>max_points:
            self.t_orn_plot = self.t_orn_plot[1:]
            for k in self.orn_plot.keys():
                self.orn_plot[k] = self.orn_plot[k][1:]

        self.t_orn_plot.extend(data["t"])
        for k in self.orn_plot.keys():
            self.orn_plot[k].extend(data[k])

        self.curve_ax.setData(self.t_orn_plot, self.orn_plot["accX"])
        self.curve_ay.setData(self.t_orn_plot, self.orn_plot["accY"])
        self.curve_az.setData(self.t_orn_plot, self.orn_plot["accZ"])
        self.curve_gx.setData(self.t_orn_plot, self.orn_plot["gyroX"])
        self.curve_gy.setData(self.t_orn_plot, self.orn_plot["gyroY"])
        self.curve_gz.setData(self.t_orn_plot, self.orn_plot["gyroZ"])
        self.curve_mx.setData(self.t_orn_plot, self.orn_plot["magX"])
        self.curve_my.setData(self.t_orn_plot, self.orn_plot["magY"])
        self.curve_mz.setData(self.t_orn_plot, self.orn_plot["magZ"])
        
    def emit_marker(self):
        '''
        '''
        stream_processor = self.explorer.stream_processor

        def callback(packet):
            timestamp, _ = packet.get_data()
            if self._vis_time_offset is None:
                self._vis_time_offset = timestamp[0]
            timestamp -= self._vis_time_offset

            '''new_data = dict(zip(['marker', 't', 'code'], [np.array([0.01, self.n_chan + 0.99, None], dtype=np.double),
                                                        np.array([timestamp[0], timestamp[0], None], dtype=np.double)]))'''

            data = [timestamp[0], self.ui.value_event_code.text()]
            self.signal_marker.emit(data)

        stream_processor.subscribe(topic=TOPICS.marker, callback=callback)
    
    def plot_marker(self, data):
        t, code = data
        self.mrk_plot["t"].append(data[0])
        self.mrk_plot["code"].append(data[1])

        pen_marker = pg.mkPen(color='#7AB904', dash=[4,4])
        
        lines = []
        for plt in self.plots_list:
        # plt = self.plot_ch8
            line = plt.addLine(t, label=code, pen=pen_marker)
            lines.append(line)
        self.mrk_plot["line"].append(lines)

    def _change_scale(self):
        old = Settings.SCALE_MENU[self.y_string]
        new = Settings.SCALE_MENU[self.ui.value_yAxis.currentText()]

        old_unit = 10 ** (-old)
        new_unit = 10 ** (-new)

        self.y_string = self.ui.value_yAxis.currentText()
        self.y_unit = new_unit

        for chan, val in self.exg_plot.items():
            if self.chan_dict[chan] == 1:
                self.exg_plot[chan] = [i * (old_unit / new_unit) for i in val]
        
        # self._r_peak_source.data['r_peak'] = (np.array(self._r_peak_source.data['r_peak']) - self.offsets[0]) * \
                                            #  (old_unit / self.y_unit) + self.offsets[0]

    # ////////////////////////////////////////
    # ///// END TESTING/////

    # ////////////////////////////////////////
    # ///// START FUNCTIONS/////

    def _battery_stylesheet(self, value):
        if value > 60:
            stylesheet = Settings.BATTERY_STYLESHEETS["high"]
        elif value > 30:
            stylesheet = Settings.BATTERY_STYLESHEETS["medium"]
        elif value > 0:
            stylesheet = Settings.BATTERY_STYLESHEETS["low"]
        else:
            stylesheet = Settings.BATTERY_STYLESHEETS["na"]
        return stylesheet

    def _impedance_stylesheet_wet(self, value):
        """
        Return the stylesheet corresponding to the impedance value
        """
        if type(value) == str:
            imp_stylesheet = Settings.GRAY_IMPEDANCE_STYLESHEET
        elif value > 500:
            imp_stylesheet = Settings.BLACK_IMPEDANCE_STYLESHEET
        elif value > 100:
            imp_stylesheet = Settings.RED_IMPEDANCE_STYLESHEET
        elif value > 50:
            imp_stylesheet = Settings.ORANGE_IMPEDANCE_STYLESHEET
        elif value > 10:
            imp_stylesheet = Settings.YELLOW_IMPEDANCE_STYLESHEET
        else:
            imp_stylesheet = Settings.GREEN_IMPEDANCE_STYLESHEET

        return imp_stylesheet

    def _impedance_stylesheet_dry(self, value):
        """
        Return the stylesheet corresponding to the impedance value
        """
        if type(value) == str:
            imp_stylesheet = Settings.GRAY_IMPEDANCE_STYLESHEET
        elif value > 500:
            imp_stylesheet = Settings.BLACK_IMPEDANCE_STYLESHEET
        elif value > 200:
            imp_stylesheet = Settings.RED_IMPEDANCE_STYLESHEET
        # elif value > 50:
        #     imp_stylesheet = Settings.ORANGE_IMPEDANCE_STYLESHEET
        elif value > 100:
            imp_stylesheet = Settings.YELLOW_IMPEDANCE_STYLESHEET
        else:
            imp_stylesheet = Settings.GREEN_IMPEDANCE_STYLESHEET

        return imp_stylesheet
    def _update_temperature(self, new_value):
        self.ui.ft_label_temp_value.setText(new_value)

    def _update_light(self, new_value):
        self.ui.ft_label_lux_value.setText(new_value)

    def _update_battery(self, new_value, new_stylesheet):
        self.ui.ft_label_battery_value.setText(new_value)
        self.ui.ft_label_battery_value.setStyleSheet(new_stylesheet)

    def _update_device_name(self, new_value):
        self.ui.ft_label_device_3.setText(new_value)

    def _update_firmware(self, new_value):
        self.ui.ft_label_firmware_value.setText(new_value)
        
    def _update_impedance(self, chan_dict):
        for chan in chan_dict.keys():
            new_stylesheet = chan_dict[chan][1]
            frame_name = f"frame_{chan}_color"
            ch_frame = AppFunctions._get_widget_by_objName(self, frame_name)
            ch_frame.setStyleSheet(new_stylesheet)

            new_value = chan_dict[chan][0]
            label_name = f"label_{chan}_value"
            ch_label = AppFunctions._get_widget_by_objName(self, label_name)
            ch_label.setText(new_value)

    def _reset_impedance(self):
        if self.is_connected:
            stream_processor = self.explorer.stream_processor
            n_chan = stream_processor.device_info['adc_mask']
            self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], n_chan))
            chan_list = [ch for ch in self.chan_dict.keys() if self.chan_dict[ch] == 1]
            chan_dict = {ch: ["NA", AppFunctions._impedance_stylesheet_wet(self, "NA")] for ch in chan_list}

            for chan in chan_dict.keys():
                new_stylesheet = chan_dict[chan][1]
                frame_name = f"frame_{chan}_color"
                ch_frame = AppFunctions._get_widget_by_objName(self, frame_name)
                ch_frame.setStyleSheet(new_stylesheet)

                new_value = chan_dict[chan][0]
                label_name = f"label_{chan}_value"
                ch_label = AppFunctions._get_widget_by_objName(self, label_name)
                ch_label.setText(new_value)
        else:
            return

    def _get_widget_by_objName(self, name):
        widgets = QApplication.instance().allWidgets()
        for x in widgets:
            # print(x)
            if str(x.objectName()) == name:
                return x
        print(f"Could not find {name}")
        return None

    def _get_timeScale(self):
        t_str = self.ui.value_timeScale.currentText()
        t = Settings.TIME_RANGE_MENU[t_str]
        return t

    def _get_samplinRate(self):
        stream_processor = self.explorer.stream_processor
        sr = stream_processor.device_info['sampling_rate']
        return sr

    def _plot_points(self):
        time_scale = AppFunctions._get_timeScale(self)
        sr = AppFunctions._get_samplinRate(self)
        points = time_scale * sr
        return points


    # ///// END FUNCTIONS/////


class Plots(MainWindow):

    def __init__(self, vis_mode, paths, plot_widget, time_scale):
        # super(Plots, self).__init__()
        self.vis_mode = vis_mode
        self.paths = paths
    
        self.data = self.read_data(paths)
        self.layoutWidget = plot_widget
        self.time_scale = time_scale
        self.is_started = False

        if self.vis_mode == "exg":
            self.init_plot_exg()
            self.init_data_exg()
            self.config_plot_exg()
            self.start_curves_exg()

        elif self.vis_mode == "orn":
            self.init_plot_orn()
            self.init_data_orn()
            self.config_plot_orn()
            self.start_curves_orn()

        if self.vis_mode == "fft":
            # self.init_plot_fft()
            self.init_data_fft()
            self.config_plot_fft()
            self.start_curves_fft()



    def init_plot_exg(self):
        '''
        Initialize exg plot
        '''
        self.plot_ch8 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch7 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch6 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch5 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch4 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch3 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch2 = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_ch1 = self.layoutWidget.addPlot()

        self.plots_list = [
            self.plot_ch1, self.plot_ch2, self.plot_ch3, self.plot_ch4,
            self.plot_ch5, self.plot_ch6, self.plot_ch7, self.plot_ch8
        ]

    def init_plot_orn(self):
        '''
        Initialize orientation plot
        '''
        self.plot_acc = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_gyro = self.layoutWidget.addPlot()
        self.layoutWidget.nextRow()
        self.plot_mag = self.layoutWidget.addPlot()


    def init_data_exg(self):
        '''
        Initialize exg data
        '''
        self.data_exg = self.data["exg"]
        self.t_exg = self.data_exg["t"]
        self.ch1 = self.data_exg["ch1"]
        self.ch2 = self.data_exg["ch2"]
        self.ch3 = self.data_exg["ch3"]
        self.ch4 = self.data_exg["ch4"]
        self.ch5 = self.data_exg["ch5"]
        self.ch6 = self.data_exg["ch6"]
        self.ch7 = self.data_exg["ch7"]
        self.ch8 = self.data_exg["ch8"]

        self.data_list = [
            self.t_exg,
            self.ch1, self.ch2, self.ch3, self.ch4,
            self.ch5, self.ch6, self.ch7, self.ch8
        ]

        if self.time_scale is None: 
            self.windowWidth_exg = len(self.t_exg)
        else:
            self.windowWidth_exg = self.time_scale_points(self.t_exg)
        self.t_plot = list(self.t_exg[:self.windowWidth_exg])
        self.ch1_plot = list(self.ch1[:self.windowWidth_exg])
        self.ch2_plot = list(self.ch2[:self.windowWidth_exg])
        self.ch3_plot = list(self.ch3[:self.windowWidth_exg])
        self.ch4_plot = list(self.ch4[:self.windowWidth_exg])
        self.ch5_plot = list(self.ch5[:self.windowWidth_exg])
        self.ch6_plot = list(self.ch6[:self.windowWidth_exg])
        self.ch7_plot = list(self.ch7[:self.windowWidth_exg])
        self.ch8_plot = list(self.ch8[:self.windowWidth_exg])

        print("exg data init")

    def init_data_orn(self):
        '''
        Initialize orientation data
        '''
        self.data_orn = self.data["orn"]
        self.t_orn = self.data_orn["t"]

        self.ax = self.data_orn["ax"]
        self.ay = self.data_orn["ay"]
        self.az = self.data_orn["az"]

        self.gx = self.data_orn["gx"]
        self.gy = self.data_orn["gy"]
        self.gz = self.data_orn["gz"]

        self.mx = self.data_orn["mx"]
        self.my = self.data_orn["my"]
        self.mz = self.data_orn["mz"]

        if self.time_scale is None: 
            self.windowWidth_orn = len(self.t_orn)
        else:
            self.windowWidth_orn = self.time_scale_points(self.t_orn)

        self.t_plot_orn = list(self.t_orn[:self.windowWidth_orn])

        self.ax_plot = list(self.ax[:self.windowWidth_orn])
        self.ay_plot = list(self.ay[:self.windowWidth_orn])
        self.az_plot = list(self.az[:self.windowWidth_orn])

        self.gx_plot = list(self.gx[:self.windowWidth_orn])
        self.gy_plot = list(self.gy[:self.windowWidth_orn])
        self.gz_plot = list(self.gz[:self.windowWidth_orn])

        self.mx_plot = list(self.mx[:self.windowWidth_orn])
        self.my_plot = list(self.my[:self.windowWidth_orn])
        self.mz_plot = list(self.mz[:self.windowWidth_orn])

    def init_data_fft(self):
        '''
        Initialize FFT data
        '''
        self.data_exg = self.data["exg"]
        exg_array = np.array([self.data_exg[i] for i in self.data_exg.columns[1:]])
        self.data_fft, self.f = AppFunctions.get_fft(exg_array, s_rate=250)

        self.ch1 = self.data_fft[1-1]
        self.ch2 = self.data_fft[2-1]
        self.ch3 = self.data_fft[3-1]
        self.ch4 = self.data_fft[4-1]
        self.ch5 = self.data_fft[5-1]
        self.ch6 = self.data_fft[6-1]
        self.ch7 = self.data_fft[7-1]
        self.ch8 = self.data_fft[8-1]

        self.data_list = [
            self.ch1, self.ch2, self.ch3, self.ch4,
            self.ch5, self.ch6, self.ch7, self.ch8
        ]

    def config_plot_fft(self):
        '''
        Styling FFT plot
        '''
        min_y = min([min(ch) for ch in self.data_list])
        max_y = max([max(ch) for ch in self.data_list])

        self.layoutWidget.setYRange(min_y, max_y)
        self.layoutWidget.setXRange(0, 70)
        self.layoutWidget.showGrid(x=True, y=True, alpha=0.5)
        self.layoutWidget.addLegend(horSpacing=20, colCount=2, brush="k", offset=(0,-300))
        self.layoutWidget.setLabel('left', "Amplitude (uV)")
        self.layoutWidget.setLabel('bottom', "Frequency (Hz)")
        self.layoutWidget.setLogMode(x=False, y=True)

    def config_plot_exg(self):
        '''
        Styling exg plot
        '''
        min_y = min([min(ch) for ch in self.data_list[1:]])
        max_y = max([max(ch) for ch in self.data_list[1:]])

        for idx, plt in enumerate(self.plots_list):
            plt.setYRange(min_y, max_y)
            plt.getAxis("left").setTicks([[(0, f"ch{idx+1}")]])
            plt.showGrid(x=False, y=True, alpha=0.5)
            if idx != 0:
                plt.setXLink(self.plot_ch1)
                plt.getAxis("bottom").setStyle(showValues=False)
                plt.hideAxis("bottom")

    def config_plot_orn(self):
        '''
        Styling orientation plot
        '''
        self.plot_acc.setXLink(self.plot_mag)
        self.plot_gyro.setXLink(self.plot_mag)

        self.plot_acc.setYRange(
            min([min(self.ax), min(self.ay), min(self.az)]),
            max([max(self.ax), max(self.ay), max(self.az)]))
        self.plot_acc.getAxis("bottom").setStyle(showValues=False)
        self.plot_acc.addLegend(horSpacing=20, colCount=3, brush="k")

        self.plot_gyro.setYRange(
            min([min(self.gx), min(self.gy), min(self.gz)]),
            max([max(self.gx), max(self.gy), max(self.gz)]))
        self.plot_gyro.getAxis("bottom").setStyle(showValues=False)
        self.plot_gyro.addLegend(horSpacing=20, colCount=3, brush="k")

        self.plot_mag.setYRange(
            min([min(self.mx), min(self.my), min(self.mz)]),
            max([max(self.mx), max(self.my), max(self.mz)]))
        self.plot_mag.addLegend(horSpacing=20, colCount=3, brush="k")

    def start_curves_exg(self):
        '''
        Start curves for exg plot
        '''
        '''for plt in self.plots_list:
            plt.clear()'''

        self.curve_ch1 = self.plot_ch1.plot(self.t_plot, self.ch1_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch2 = self.plot_ch2.plot(self.t_plot, self.ch2_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch3 = self.plot_ch3.plot(self.t_plot, self.ch3_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch4 = self.plot_ch4.plot(self.t_plot, self.ch4_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch5 = self.plot_ch5.plot(self.t_plot, self.ch5_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch6 = self.plot_ch6.plot(self.t_plot, self.ch6_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch7 = self.plot_ch7.plot(self.t_plot, self.ch7_plot, pen=Settings.EXG_LINE_COLOR)
        self.curve_ch8 = self.plot_ch8.plot(self.t_plot, self.ch8_plot, pen=Settings.EXG_LINE_COLOR)

    def start_curves_orn(self):
        '''
        Start curves for orn plot
        '''
        pen = pg.mkPen(color=(255, 0, 0))
        self.curve_ax = self.plot_acc.plot(
            self.t_plot_orn, self.ax_plot, pen=Settings.ORN_LINE_COLORS[0], name="accX")
        self.curve_ay = self.plot_acc.plot(
            self.t_plot_orn, self.ay_plot, pen=Settings.ORN_LINE_COLORS[1], name="accY")
        self.curve_az = self.plot_acc.plot(
            self.t_plot_orn, self.az_plot, pen=Settings.ORN_LINE_COLORS[2], name="accZ")

        self.curve_gx = self.plot_gyro.plot(
            self.t_plot_orn, self.gx_plot, pen=Settings.ORN_LINE_COLORS[0], name="gyroX")
        self.curve_gy = self.plot_gyro.plot(
            self.t_plot_orn, self.gy_plot, pen=Settings.ORN_LINE_COLORS[1], name="gyroY")
        self.curve_gz = self.plot_gyro.plot(
            self.t_plot_orn, self.gz_plot, pen=Settings.ORN_LINE_COLORS[2], name="gyroZ")

        self.curve_mx = self.plot_mag.plot(
            self.t_plot_orn, self.mx_plot, pen=Settings.ORN_LINE_COLORS[0], name="magX")
        self.curve_my = self.plot_mag.plot(
            self.t_plot_orn, self.my_plot, pen=Settings.ORN_LINE_COLORS[1], name="magY")
        self.curve_mz = self.plot_mag.plot(
            self.t_plot_orn, self.mz_plot, pen=Settings.ORN_LINE_COLORS[2], name="magZ")

    def start_curves_fft(self):
        '''
        Start curves for fft plot
        '''
        self.curve_ch1 = self.layoutWidget.plot(self.f, self.ch1, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[0]), name="ch1")
        self.curve_ch2 = self.layoutWidget.plot(self.f, self.ch2, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[1]), name="ch2")
        self.curve_ch3 = self.layoutWidget.plot(self.f, self.ch3, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[2]), name="ch3")
        self.curve_ch4 =  self.layoutWidget.plot(self.f, self.ch4, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[3]), name="ch4")
        self.curve_ch5 = self.layoutWidget.plot(self.f, self.ch5, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[4]), name="ch5")
        self.curve_ch6 = self.layoutWidget.plot(self.f, self.ch6, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[5]), name="ch6")
        self.curve_ch7 = self.layoutWidget.plot(self.f, self.ch7, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[6]), name="ch7")
        self.curve_ch8 = self.layoutWidget.plot(self.f, self.ch8, pen=pg.mkPen(color=Settings.FFT_LINE_COLORS[7]), name="ch8")

    def update_plot_exg(self):
        '''
        Update exg plot
        '''
        self.t_plot = self.t_plot[1:]
        self.t_plot.append(self.t_exg[self.windowWidth_exg + 1]) 

        self.ch1_plot = self.ch1_plot[1:]  # Remove the first 
        self.ch1_plot.append(self.ch1[self.windowWidth_exg + 1])  # Add a new value
        self.curve_ch1.setData(self.t_plot, self.ch1_plot)  # Update the data.

        self.ch2_plot = self.ch2_plot[1:]
        self.ch2_plot.append(self.ch2[self.windowWidth_exg + 1])
        self.curve_ch2.setData(self.t_plot, self.ch2_plot)

        self.ch3_plot = self.ch3_plot[1:]
        self.ch3_plot.append(self.ch3[self.windowWidth_exg + 1])
        self.curve_ch3.setData(self.t_plot, self.ch3_plot)

        self.ch4_plot = self.ch4_plot[1:]
        self.ch4_plot.append(self.ch4[self.windowWidth_exg + 1])
        self.curve_ch4.setData(self.t_plot, self.ch4_plot)

        self.ch5_plot = self.ch5_plot[1:]
        self.ch5_plot.append(self.ch5[self.windowWidth_exg + 1])
        self.curve_ch5.setData(self.t_plot, self.ch5_plot)

        self.ch6_plot = self.ch6_plot[1:]
        self.ch6_plot.append(self.ch6[self.windowWidth_exg + 1])
        self.curve_ch6.setData(self.t_plot, self.ch6_plot)

        self.ch7_plot = self.ch7_plot[1:]
        self.ch7_plot.append(self.ch7[self.windowWidth_exg + 1])
        self.curve_ch7.setData(self.t_plot, self.ch7_plot)

        self.ch8_plot = self.ch8_plot[1:]
        self.ch8_plot.append(self.ch8[self.windowWidth_exg + 1])
        self.curve_ch8.setData(self.t_plot, self.ch8_plot)

        self.windowWidth_exg += 1

        '''if self.windowWidth_exg >= len(self.ch1)-1:
            self.timer_exg.stop()'''


    def update_plot_orn(self):
        '''
        Update orientation plot
        '''
        self.t_plot_orn = self.t_plot_orn[1:]
        self.t_plot_orn.append(self.t_orn[self.windowWidth_orn + 1]) 

        # ########### ACC PLOT ############
        self.ax_plot = self.ax_plot[1:]
        self.ax_plot.append(self.ax[self.windowWidth_orn + 1])
        self.curve_ax.setData(self.t_plot_orn, self.ax_plot)

        self.ay_plot = self.ay_plot[1:]
        self.ay_plot.append(self.ay[self.windowWidth_orn + 1])
        self.curve_ay.setData(self.t_plot_orn, self.ay_plot)

        self.az_plot = self.az_plot[1:]
        self.az_plot.append(self.az[self.windowWidth_orn + 1])
        self.curve_az.setData(self.t_plot_orn, self.az_plot)
        # ###########  ############

        # ########### GYRO PLOT ############
        self.gx_plot = self.gx_plot[1:]
        self.gx_plot.append(self.gx[self.windowWidth_orn + 1])
        self.curve_gx.setData(self.t_plot_orn, self.gx_plot)

        self.gy_plot = self.gy_plot[1:]
        self.gy_plot.append(self.gy[self.windowWidth_orn + 1])
        self.curve_gy.setData(self.t_plot_orn, self.gy_plot)

        self.gz_plot = self.gz_plot[1:]
        self.gz_plot.append(self.gz[self.windowWidth_orn + 1])
        self.curve_gz.setData(self.t_plot_orn, self.gz_plot)
        # ###########  ############

        # ########### MAG PLOT ############
        self.mx_plot = self.mx_plot[1:]
        self.mx_plot.append(self.mx[self.windowWidth_orn + 1])
        self.curve_mx.setData(self.t_plot_orn, self.mx_plot)

        self.my_plot = self.my_plot[1:]
        self.my_plot.append(self.my[self.windowWidth_orn + 1])
        self.curve_my.setData(self.t_plot_orn, self.my_plot)

        self.mz_plot = self.mz_plot[1:]
        self.mz_plot.append(self.mz[self.windowWidth_orn + 1])
        self.curve_mz.setData(self.t_plot_orn, self.mz_plot)
        # ###########  ############

        self.windowWidth_orn += 1

        '''if self.windowWidth_orn >= len(self.ax)-1:
            pass'''

    def read_data(self, paths):
        '''
        Read data from recorded csv or edf files
        Args:
            paths (list): list of files to read
        '''
        data = {}
        for file in paths:
            if file.endswith(".csv"):
                if "ExG" in file:
                    data["exg"] = self._read_csv(file)
                elif "Marker" in file:
                    try:
                        data["marker"] = self._read_csv(file)
                    except:
                        data["marker"] = None
                elif "ORN" in file:
                    data["orn"] = self._read_csv(file)
                else:
                    print("Not a exg, mmarker or ORN file")
            elif file.endswith(".edf"):
                print("Not supported yet")
            else:
                print("Only csv and edf files")

        return data

    def time_scale_points(self, time_vec, time=10):
        '''
        Compute points in window based onn time scale
        '''
        time_str = self.time_scale
        time = Settings.TIME_RANGE_MENU[time_str]
        idx = len(time_vec)-2
        for i in range(len(time_vec)):
            if time_vec[i] > time:
                idx = i
                return idx
        # print(idx)
        return idx

    def _read_csv(self, file):
        df = pd.read_csv(file)
        df["t"] = df["TimeStamp"]-df["TimeStamp"][0]
        return df

    def _read_edf(self, file):
        data = mne.io.read_raw_edf(file)
        raw_data = data.get_data()
        cols = data.ch_names
        data = dict(zip(cols, raw_data))
        df = pd.DataFrame.from_dict(data)
        df["t"] = df["TimeStamp"]-df["TimeStamp"][0]
        return df

    def _read_bin(self, file):
        pass
    
    def _update_plot_data(self, data, data_plot):
        data_plot = data_plot[1:]  # Remove the first 
        data_plot.append(data[self.windowWidth_exg + 1])  # Add a new value