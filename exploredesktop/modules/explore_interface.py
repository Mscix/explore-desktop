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


class ExploreInterface(Explore):
    """Interface class for Explore"""
    def __init__(self):
        super().__init__()
        self.is_measuring_imp = False
        self.device_chan = None

        self.chan_dict = {}

    @property
    def sampling_rate(self) -> Optional[int]:
        """Returns the current sampling rate of the device"""
        if self.is_connected:
            return self.stream_processor.device_info['sampling_rate']

        logger.debug("Device is not connected but the sampling rate method is called.")
        return None

    @property
    def n_active_chan(self) -> Optional[int]:
        """Retruns number of active channels"""
        if self.is_connected:
            return sum(self.stream_processor.device_info['adc_mask'])

        logger.debug("Device is not connected but the number of active channels method is called.")
        return None
    # def is_connected(self) -> bool:
    #     """Connection status property"""
    #     return self.is_connected

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
        self.set_chan_dict()
        return True

    def set_chan_dict(self):
        """Set the channel status dictionary i.e. whether channels are active or inactive
        """
        if self.is_connected:
            chan_mask = list(reversed(self.stream_processor.device_info['adc_mask']))
            self.chan_dict = dict(zip([c.lower() for c in Settings.CHAN_LIST], chan_mask))

    def get_chan_dict(self) -> dict:
        """Retrun channel status dictionary
        """
        return self.chan_dict

    def _set_n_chan(self, packet: explorepy.packet.EEG) -> None:
        """Set the number of channels i.e. device type (4-ch or 8-ch)

        Args:
            packet: EEG packet
        """
        exg_fs = self.stream_processor.device_info['sampling_rate']
        timestamp, _ = packet.get_data(exg_fs)
        self.device_chan = 4 if timestamp.shape[0] == 33 else 8

    def get_n_chan(self) -> int:
        """Returns number of channels i.e. device type (4-ch or 8-ch)"""
        return self.device_chan

    def measure_imp(self, imp_callback: Callable) -> bool:
        """Activate impedance measurement mode and subscribe to impedance topic"""
        try:
            self.stream_processor.imp_initialize(notch_freq=50)
            self.is_measuring_imp = True
        except ConnectionError:
            return False

        self.subscribe(callback=imp_callback, topic=TOPICS.imp)
        return True

    def disable_imp(self, imp_callback: Callable) -> bool:
        """Disable impedance measurement mode and unsubscribe from impedance topic"""
        self.unsubscribe(callback=imp_callback, topic=TOPICS.imp)
        if self.stream_processor.disable_imp():
            self.is_measuring_imp = False
            return True

        logger.warning("Failed to disable impedance measurement.")
        return False

    def set_sampling_rate(self, sampling_rate: int) -> Optional[bool]:
        """Change the sampling rate of the device"""
        if sampling_rate == self.sampling_rate:
            return True
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
