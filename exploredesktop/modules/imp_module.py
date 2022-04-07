# -*- coding: utf-8 -*-
"""
Module containing impedance related functionalities
"""
import logging

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox


from exploredesktop.modules.app_settings import (  # isort: skip
    ImpModes,
    Messages,
    Settings,
    Stylesheets,
)
from exploredesktop.modules.tools import display_msg  # isort: skip
from exploredesktop.modules.base_model import BaseModel  # isort: skip

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)
logger = logging.getLogger("explorepy." + __name__)


class ImpedanceGraph(pg.GraphItem):
    """Reimplementation of pyqtgraph.GraphItem
    """
    def __init__(self, model) -> None:
        self.text_items = []
        super().__init__()
        self.model = model
        self.signals = self.model.get_signals()
        self.signals.impedanceChanged.connect(self.on_new_data)
        self.signals.displayDefaultImp.connect(self.display_default_imp)
        self.display_default_imp()

    def display_default_imp(self) -> None:
        """Initialize impedance graph
        """
        chan_dict = self.model.explorer.get_chan_dict()
        n_chan = list(chan_dict.values()).count(1)
        pos = np.array([[0 + i * 3, 0] for i in range(n_chan)], dtype=float)
        texts = [f"{key}\nNA" for key in chan_dict if chan_dict[key] == 1]
        brushes = [Stylesheets.GRAY_IMPEDANCE_STYLESHEET for i in range(n_chan)]

        self.setData(pos=pos, symbolBrush=brushes, text=texts)

    def get_model(self):
        """Retrun impedance model

        Returns:
            ImpModel: impedance data model
        """
        return self.model

    def setData(self, **kwds) -> None:
        """Set data to graph.
        Args:
            pos (np.array): (N,2)  array of the positions of each node in the graph.
            texts (list): list of labels to add to each node
            brushes (list): list of colors to paint each node
        """
        text = kwds.pop('text', [])
        data = kwds
        if 'pos' in data:
            npts = data['pos'].shape[0]
            data['data'] = np.empty(npts, dtype=[('index', int)])
            data['data']['index'] = np.arange(npts)
        self.set_texts(text)
        symbols = ['o'] * len(text)
        super().setData(**data, symbols=symbols, size=2, pxMode=False)
        for id_item, item in enumerate(self.text_items):
            item.setPos(*data['pos'][id_item])

    def set_texts(self, texts: list) -> None:
        """Set text labels to graph

        Args:
            text (list): list of labels to be added to the graph
        """
        for item in self.text_items:
            item.scene().removeItem(item)

        self.text_items = []  # this keep only remove texts
        for txt in texts:
            t_chan, t_val = txt.split("\n")
            txt_html = f'<div style="text-align: center; color: #FFFFFF"><b>{t_chan}<br>{t_val}</b></div>'
            item = pg.TextItem(html=txt_html, anchor=(0.5, 0.5))
            self.text_items.append(item)
            item.setParentItem(self)

    @Slot(dict)
    def on_new_data(self, data: dict) -> None:
        """Fetch new incoming data and update the graph

        Args:
            data (dict): dict containing text, position, symbols and brush style
        """
        texts = data["texts"]
        pos = data["pos"]
        brushes = data["brushes"]
        self.setData(pos=pos, symbolBrush=brushes, text=texts)


class ImpModel(BaseModel):
    """Impedance model
    """
    def __init__(self) -> None:
        # super().__init__()
        self.mode = "wet"

    def get_stylesheet(self, value: str) -> str:
        """Get stylesheet based on impedance value

        Args:
            value (str): impedance value. Can be numeric or text based

        Returns:
            str: stylesheet corresponding to input value
        """
        rules_dict = Settings.COLOR_RULES_DRY if self.mode == "dry" else Settings.COLOR_RULES_WET
        if isinstance(value, str) and not value.replace(".", "", 1).isdigit():
            imp_stylesheet = Stylesheets.GRAY_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["red"]:
            imp_stylesheet = Stylesheets.BLACK_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["orange"]:
            imp_stylesheet = Stylesheets.RED_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["yellow"]:
            imp_stylesheet = Stylesheets.ORANGE_IMPEDANCE_STYLESHEET
        elif float(value) > rules_dict["green"]:
            imp_stylesheet = Stylesheets.YELLOW_IMPEDANCE_STYLESHEET
        else:
            imp_stylesheet = Stylesheets.GREEN_IMPEDANCE_STYLESHEET

        return imp_stylesheet

    def format_imp_value(self, value: float) -> str:
        """Format impedance value to correct display format

        Args:
            value (float): impedance value

        Returns:
            str: formatted impedance value
        """
        if value < 5:
            # TODO: display <5
            str_value = "5 K\u03A9"
            # str_value = "\u003C 5 K\u03A9"
            # str_value = "<5 K\u03A9"
        elif (self.mode == "wet" and value > Settings.COLOR_RULES_WET["open"]) or \
                (self.mode == "dry" and value > Settings.COLOR_RULES_DRY["open"]):
            str_value = "Open"
        else:
            str_value = str(int(round(value, 0))) + " K\u03A9"
        return str_value

    def imp_callback(self, packet) -> None:
        """Impedance callback to get data from explorepy's impedance packet

        Args:
            packet (explorepy.packet.imp): Impedance packet
        """
        chan_dict = self.explorer.get_chan_dict()
        n_chan = list(chan_dict.values()).count(1)

        imp_values = packet.get_impedances()
        texts = []
        brushes = []
        pos = np.array([[0 + i * 3, 0] for i in range(n_chan)], dtype=float)
        # for chan, value in zip([key for key in chan_dict if chan_dict[key] == 1], imp_values):
        for chan, value in zip([item[0] for item in chan_dict.items() if item[1]], imp_values):
            value = value / 2
            brushes.append(self.get_stylesheet(value))
            value = self.format_imp_value(value)
            texts.append(f"{chan}\n{value}")

        data = {"texts": texts, "brushes": brushes, "pos": pos}
        self.signals.impedanceChanged.emit(data)

    def set_mode(self, text: str) -> None:
        """Set impedance mode

        Args:
            text (str): electordes mode
        """
        self.mode = "dry" if text == ImpModes.DRY.value else "wet"
        logger.debug("Impedance measurement mode has been changed to %s", self.mode)

    def reset_vars(self) -> None:
        """reset class variables
        """
        self.mode = "wet"


class ImpFrameView():
    """
    Impedance frame functions
    """
    def __init__(self, ui, imp_model) -> None:
        self.ui = ui

        self.model = imp_model
        self.signals = imp_model.get_signals()
        self.explorer = imp_model.get_explorer()

        self.set_dropdown()

    def set_dropdown(self) -> None:
        """Initialize dropdowns
        """
        self.ui.imp_mode.addItems(ImpModes.all_values())

    def disable_imp(self) -> None:
        """
        Disable impedance measurement and reset GUI
        """
        if not self.explorer.is_connected:
            return
        self.explorer.disable_imp(self.model.imp_callback)
        self.signals.btnImpMeasureChanged.emit("Measure Impedances")
        self.signals.displayDefaultImp.emit()

    @Slot()
    def measure_imp_clicked(self) -> None:
        """
        Slot to run when button impedance measurement is clicked
        """
        if self.explorer.is_measuring_imp:
            self.disable_imp()
            return

        sr_ok = self.verify_s_rate()
        if not sr_ok:
            return

        self.signals.btnImpMeasureChanged.emit("Stop")
        self.explorer.measure_imp(self.model.imp_callback)

    def verify_s_rate(self) -> bool:
        """Check whether sampling rate is set to 250Hz. If not, ask the user if they want to change it

        Returns:
            bool: whether sampling rate is 250Hz
        """
        accept = True
        s_rate = self.explorer.sampling_rate
        if s_rate != 250:
            accept = self.ask_change_s_rate(s_rate)
        return accept

    def ask_change_s_rate(self, s_rate) -> bool:
        """Ask user whether to change sampling rate and change it.

        Args:
            s_rate (int): current sampling rate

        Returns:
            bool: whether sampling rate has chanded to 250
        """
        changed = False
        question = Messages.SET_SR_TO_250_QUESTION.replace("s_rate", str(s_rate))
        response = display_msg(msg_text=question, popup_type="question")
        if response == QMessageBox.StandardButton.Yes:
            self.explorer.set_sampling_rate(sampling_rate=250)
            self.ui.value_sampling_rate.setCurrentText(str(250))
            changed = True
        return changed

    # TODO: implement later when implementing page navigation (change_page in main window)
    # def check_is_imp(self):
    #     """
    #     Check if impedance measurement is active.
    #     If so ask the user whether to disable it.
    #     """
    #     disabled = False
    #     if self.is_imp_measuring:
    #         response = self.display_msg(msg_text=Messages.DISABLE_IMP_QUESTION, type="question")

    #         if response == QMessageBox.StandardButton.Yes:
    #             self.disable_imp()
    #             disabled = True

    #     return disabled

    @staticmethod
    def imp_info_clicked() -> None:
        """Display message when impedance question mark is clicked
        """
        display_msg(Messages.IMP_INFO, popup_type="info")
