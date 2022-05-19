
import logging
import time
from exploredesktop.modules.base_model import BaseModel
from exploredesktop.modules.dialogs import FiltersDialog
from exploredesktop.modules.tools import display_msg, get_filter_limits, verify_filters

logger = logging.getLogger("explorepy." + __name__)


class Filters(BaseModel):
    def __init__(self, ui) -> None:
        super().__init__()
        self.ui = ui
        self.current_filters = None

    def reset_vars(self):
        self.current_filters = None

    def setup_ui_connections(self):
        self.ui.btn_plot_filters.clicked.connect(self.popup_filters)

    def popup_filters(self):

        # filters_applied = True
        remove = True if self.current_filters is not None else False
        wait = True if self.current_filters is None else False
        dialog = FiltersDialog(self.explorer.sampling_rate, self.current_filters)
        filters = dialog.exec()
        if filters is False:
            return False
        if self._check_same_filters(new_filters=filters):
            return True

        self.current_filters = filters
        if remove:
            self.explorer.remove_filters()
        self.apply_filters()
        if wait:
            time.sleep(1.5)
        return True

    def apply_filters(self):
        notch_freq = self.current_filters["notch"]
        high_freq = self.current_filters["high_cutoff"]
        low_freq = self.current_filters["low_cutoff"]

        if notch_freq is not None:
            self.explorer.add_filter(cutoff_freq=notch_freq, filter_type='notch')

        if high_freq is not None and low_freq is not None:
            self.explorer.add_filter(
                cutoff_freq=(low_freq, high_freq), filter_type='bandpass')
        elif high_freq is not None:
            self.explorer.add_filter(cutoff_freq=high_freq, filter_type='highpass')
        elif low_freq is not None:
            self.explorer.add_filter(cutoff_freq=low_freq, filter_type='lowpass')

        logger.info(f"Applied filters {self.current_filters}")

    def _check_same_filters(self, new_filters):
        """
        Compare new filters to existing ones

        Args:
            new_filters (dict): filters to compare
        """
        same = True if self.current_filters == new_filters else False
        return same

    def check_filters_sr(self, s_rate):
        if self.current_filters is None:
            return

        min_lc_freq, max_hc_freq = get_filter_limits(s_rate)

        warning = ""

        hc_freq_warning = (
            "High cutoff frequency cannot be larger than or equal to the nyquist frequency.\n"
            f"The high cutoff frequency has changed to {max_hc_freq:.1f} Hz!"
        )

        lc_freq_warning = (
            "Transient band for low cutoff frequency was too narrow.\n"
            f"The low cutoff frequency has changed {min_lc_freq:.1f} Hz!"
        )

        filter_ok = verify_filters(
            (self.current_filters['low_cutoff'], self.current_filters['high_cutoff']),
            s_rate)

        if filter_ok['lc_freq'] is False:
            warning += lc_freq_warning
            self.current_filters["low_cutoff"] = min_lc_freq

        if filter_ok['hc_freq'] is False:
            warning += hc_freq_warning
            self.current_filters["high_cutoff"] = max_hc_freq

        if warning != "":
            display_msg(msg_text=warning, popup_type="info")
