"""Explore interface class to be used in Explore Desktop"""
import logging
import time
from collections import namedtuple
from typing import (
    Callable,
    List,
    Optional,
    Tuple,
    Union
)

import explorepy.packet
from explorepy import Explore
from explorepy.stream_processor import TOPICS
from explorepy.tools import bt_scan


from exploredesktop.modules.app_settings import Settings  # isort: skip


logger = logging.getLogger("explorepy." + __name__)

# write below idx of channels to display, e.g. [0,1,2,3,4,5,6,7] for first 8 chan
IDX_CHAN_TO_DISPLAY = [i for i in range(32)]
# IDX_CHAN_TO_DISPLAY = [0, 1, 2, 3, 4, 5, 6, 7]
# IDX_CHAN_TO_DISPLAY = [0]
# write max number of channels
N_CHAN = 32


class ExploreInterface(Explore):
    """Interface class for Explore"""

    def __init__(self):
        super().__init__()
        self.device_chan = None
        self.chan_dict_list = []

    @property
    def sampling_rate(self) -> Optional[int]:
        """Returns the current sampling rate of the device"""
        if self.is_connected:
            return self.stream_processor.device_info['sampling_rate']

        logger.debug("Device is not connected but the sampling rate method is called.")
        return None

    @property
    def n_active_chan(self) -> Optional[int]:
        """Returns number of active channels"""
        if self.is_connected:
            # TODO uncomment when adc mask is implemented
            # return sum(self.stream_processor.device_info['adc_mask'])
            return len(IDX_CHAN_TO_DISPLAY)

        logger.debug("Device is not connected but the number of active channels method is called.")
        return None

    @property
    def is_recording(self) -> bool:
        """Returns recording status"""
        return bool(self.recorders)

    @property
    def is_pushing_lsl(self) -> bool:
        """Returns LSL pushing status"""
        return bool(self.lsl)

    @staticmethod
    def scan_devices() -> List[namedtuple]:
        """This function searches for nearby bluetooth devices and returns a list of advertising Explore devices.

    Note:
        In Windows, this function returns all the paired devices and unpaired advertising devices. The 'is_paired'
        attribute shows if the device is paired. If a device is paired, it will be in the returned list regardless if
        it is currently advertising or not.

    Returns:
            list of nearby devices
    """
        return bt_scan()

    def connect(self, device_name: str) -> bool:
        """

        Args:
            device_name: Device name ("Explore_XXXX")

        Returns:
            True if successful, False otherwise
        """
        try:
            super().connect(device_name=device_name)
        except ConnectionAbortedError as error:
            logger.debug("Could not connect! %s", str(error))
            return False

        # Find if the device is 4-ch or 8-ch
        self.subscribe(topic=TOPICS.raw_ExG, callback=self._set_n_chan)
        while self.device_chan is None:
            time.sleep(.05)
        self.unsubscribe(topic=TOPICS.raw_ExG, callback=self._set_n_chan)

        # Set channel status
        self.set_chan_dict_list()
        return True

    def disconnect(self):
        """Disconnect from explore device and reset variables
        """
        self.device_chan = None
        self.chan_dict_list = []
        return super().disconnect()

    # TODO change to property
    def set_chan_dict_list(self, new_dict=None):
        """Set the channel status dictionary i.e. whether channels are active or inactive
        """
        if self.is_connected:
            # TODO uncomment when adc mask is implemented
            # chan_mask = list(reversed(self.stream_processor.device_info['adc_mask']))
            chan_mask = [1] * N_CHAN

            if new_dict is None:
                custom_names = [f"ch{i}" for i in range(1, self.device_chan + 1)]
                signal_types = ["EEG"] * self.device_chan
            else:
                custom_names = [d["name"] for d in new_dict]
                signal_types = [d["type"] for d in new_dict]

            self.chan_dict_list = [
                {
                    "input": ch, "enable": active, "name": name, "type": sig_type
                } for ch, active, name, sig_type in zip(
                    [c.lower() for c in Settings.CHAN_LIST], chan_mask, custom_names, signal_types)
            ]
            # TODO uncomment when adc mask is implemented
            # self.chan_dict_list = self.chan_dict_list[:self.device_chan]
            self.chan_dict_list = [self.chan_dict_list[i] for i in IDX_CHAN_TO_DISPLAY]

    def get_chan_dict_list(self) -> dict:
        """Retrun channel status dictionary
        """
        return self.chan_dict_list

    def _set_n_chan(self, packet: explorepy.packet.EEG) -> None:
        """Set the number of channels i.e. device type (4-ch or 8-ch)

        Args:
            packet: EEG packet
        """
        exg_fs = self.stream_processor.device_info['sampling_rate']
        timestamp, _ = packet.get_data(exg_fs)
        # TODO uncomment when adc mask is implemented
        # self.device_chan = 4 if timestamp.shape[0] == 33 else 8
        self.device_chan = N_CHAN

    def get_device_chan(self) -> int:
        """Returns number of channels i.e. device type (4-ch or 8-ch)"""
        return self.device_chan

    def active_chan_list(self, custom_name=False):
        """Returns list of active channels

        Args:
            custom_name (bool, optional): whether to return custom names set by user. Defaults to False.
        """
        if custom_name:
            return [one_chan_dict['name'] for one_chan_dict in self.chan_dict_list if one_chan_dict['enable']]
        return [one_chan_dict['input'] for one_chan_dict in self.chan_dict_list if one_chan_dict['enable']]

    # pylint: disable=arguments-differ
    def measure_imp(self, imp_callback: Callable) -> bool:
        """Activate impedance measurement mode and subscribe to impedance topic"""
        try:
            self.stream_processor.imp_initialize(notch_freq=50)
        except ConnectionError:
            return False

        self.subscribe(callback=imp_callback, topic=TOPICS.imp)
        return True

    def disable_imp(self, imp_callback: Callable) -> bool:
        """Disable impedance measurement mode and unsubscribe from impedance topic"""
        self.unsubscribe(callback=imp_callback, topic=TOPICS.imp)
        if self.stream_processor.disable_imp():
            return True

        logger.warning("Failed to disable impedance measurement.")
        return False

    # TODO should be prop setter
    def set_sampling_rate(self, sampling_rate: int) -> Optional[bool]:
        """Change the sampling rate of the device"""
        if sampling_rate == self.sampling_rate:
            return False
        try:
            return super().set_sampling_rate(sampling_rate=int(sampling_rate))
        except (ValueError, ConnectionAbortedError) as error:
            logger.error("Error during set sampling rate: %s", str(error))
            return False

    def subscribe(self, callback: Callable, topic: TOPICS) -> None:
        """Subscribe a callback to a topic"""
        self.stream_processor.subscribe(callback, topic)

    def unsubscribe(self, callback: Callable, topic: TOPICS) -> None:
        """Unsubscribe a callback from a topic"""
        self.stream_processor.unsubscribe(callback, topic)

    def add_filter(self, cutoff_freq: Union[float, tuple], filter_type: str) -> None:
        """Add a filter to filtered_ExG topic

        Args:
            cutoff_freq: Cut-off frequency (frequencies) for the filter
            filter_type: Filter type ['bandpass', 'lowpass', 'highpass', 'notch']
        """
        self.stream_processor.add_filter(cutoff_freq, filter_type)

    def remove_filters(self) -> None:
        """Remove all filters from filtered_ExG topic"""
        self.stream_processor.remove_filters()

    def get_bp_filter_limits(self) -> Tuple[float, float]:
        """Returns minimum low cutoff frequency of the bandpass filter"""
        nyq_freq = self.sampling_rate / 2.

        max_hc_freq = round(nyq_freq - 1, 1)
        min_lc_freq = round(0.0035 * nyq_freq, 1)

        return min_lc_freq, max_hc_freq
