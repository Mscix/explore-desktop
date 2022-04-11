"""Module with app settings, stylesheets and messages displayed in the app
"""
from enum import Enum


class EnvVariables(Enum):
    """Enum for environmental keys
    """
    BATTERY = "battery"
    TEMPERATURE = "temperature"
    LIGHT = "light"

    DEVICE_NAME = "device_name"
    FIRMWARE = "firmware"


class ConnectionStatus(Enum):
    """Enum for connection status
    """
    CONNECTED = "Connected to dev_name"
    RECONNECTING = "Reconnecting ..."
    DISCONNECTED = "Not connected"


class ImpModes(Enum):
    """Enum for impedance measuring modes
    """
    WET = "Wet Electrodes"
    DRY = "Dry Electrodes"

    @classmethod
    def all_values(cls):
        """Returns a list of all the values in the Enumeration
        """
        return [m.value for m in cls]


class Stylesheets():
    """
    Class containig stylesheets for GUI
    """
    #########################
    # Buttons stylesheets
    #########################
    DISABLED_BTN_STYLESHEET = """
    background-color: rgb(89,90,111);
    color: rgb(155,155,155);
    """
    BTN_LEFT_MENU_SELECTED_STYLESHEET = """
    background-color: rgb(113, 120, 159);
    """

    #########################
    # Impedance stylesheets
    #########################
    GRAY_IMPEDANCE_STYLESHEET = "#A9A9A9"

    BLACK_IMPEDANCE_STYLESHEET = "#111111"

    RED_IMPEDANCE_STYLESHEET = "#CB0000"

    ORANGE_IMPEDANCE_STYLESHEET = "#CF8F25"

    YELLOW_IMPEDANCE_STYLESHEET = "#C5C527"

    GREEN_IMPEDANCE_STYLESHEET = "#2B851A"

    #########################
    # Battery stylesheet
    #########################
    BATTERY_STYLESHEETS = {
        "low": "color: #FD0000;",
        "medium": "color: #CDB900;",
        "high": "color: #00FD19;",
        "na": "color: #000000"
    }

    #########################
    # Plot colors
    #########################
    EXG_LINE_COLOR = "#42C4F7"

    FFT_LINE_COLORS = [
        '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78',
        '#2ca02c', '#98df8a', '#d62728', '#ff9896']

    MARKER_LINE_COLOR = '#7AB904'  # ALPHA = 1

    MARKER_LINE_COLOR_ALPHA = '#7AB90480'  # ALPHA = .5

    ORN_LINE_COLORS = ["#00FF00", "#42C4F7", "#FF0000"]

    PLOT_BACKGROUND = "#120b28"

    #########################
    # Not in use for now
    #########################
    # Start button stylesheet
    START_BUTTON_STYLESHEET = """
    QPushButton{
        border: 1px solid 25541C;
        border-radius: 5px;
        background-color: #2B851A;
        color: #FFF;}
    QPushButton:hover{
        border: 2px solid #25541C;
        border-radius: 5px;
        background-color: #2B851A;
        color: #FFF;
    }
    QPushButton:pressed{
        border: 2px solid #25541C;
        border-radius: 5px;
        background-color: #4D9033;
        color: #FFF;
    }
    """

    STOP_BUTTON_STYLESHEET = """
    QPushButton{
        border: 1px solid #7D0101;
        border-radius: 5px;
        background-color: #EA0000;
        color: #FFF;
    }
    QPushButton:hover{
        border: 2px solid #FFF;
        border-radius: 5px;
        background-color: #EA0000;
        color: #FFF;
    }
    QPushButton:pressed{
        border: 2px solid #7D0101;
        border-radius: 5px;
        background-color: rgb(215, 74, 61);
        color: #FFF;
    }"""

    POPUP_STYLESHEET = """
    QMessageBox {
    background-color: rgb(28, 30, 42);
    }

    QMessageBox QLabel {
        color: rgb(200, 200, 200);
    }
        """


class Settings():
    """Class containing GUI settings
    """
    CUSTOM_TITLE_BAR = True

    DOWNSAMPLING = True

    LEFT_MENU_MIN = 60
    LEFT_MENU_MAX = 200

    ORN_SRATE = 20  # Hz
    EXG_VIS_SRATE = 125
    WIN_LENGTH = 10  # Seconds
    MODE_LIST = ['EEG', 'ECG']

    CHAN_LIST = [f'ch{i}' for i in range(1, 9)]
    DEFAULT_SCALE = 10 ** 3  # Volt
    BATTERY_N_MOVING_AVERAGE = 60
    V_TH = [10, 5 * 10 ** 3]  # Noise threshold for ECG (microVolt)
    ORN_LIST = [
        'accX', 'accY', 'accZ', 'gyroX', 'gyroY', 'gyroZ',
        'magX', 'magY', 'magZ']

    SCALE_MENU = {
        "1 uV": 0, "5 uV": -0.66667, "10 uV": -1, "100 uV": -2,
        "200 uV": -2.33333, "500 uV": -2.66667, "1 mV": -3,
        "5 mV": -3.66667, "10 mV": -4, "100 mV": -5}

    TIME_RANGE_MENU = {"10 s": 10., "5 s": 5., "20 s": 20.}
    SAMPLING_RATES = [250, 500, 1000]
    N_CHAN_LIST = ["4", "8"]

    # Max value for each color
    COLOR_RULES_DRY = {
        "green": 20,
        "yellow": 35,
        "orange": 50,
        "red": 70,
        "open": 500
    }
    COLOR_RULES_WET = {
        "green": 10,
        "yellow": 20,
        "orange": 30,
        "red": 50,
        "open": 100
    }

    LEFT_BTN_REQUIRE_CONNECTION = ["btn_settings", "btn_plots", "btn_impedance", "btn_integration"]


class Messages():
    """Class containing GUI messages
    """
    #########################
    # bt functions
    #########################
    NO_BT_CONNECTION = "No Bluetooth connection available.\nPlease make sure the bluetooth is on."
    NO_EXPLORE_DEVICES = "No explore devices found. Please make sure your device is turned on."
    WARNING_PAIRED_DEV_WINDOWS = "Note: Listed paired devices might not be advertising"
    INVALID_EXPLORE_NAME = "Please select a device or provide a valid name (Explore_XXXX or XXXX) before connecting."
    WINDOWS_PAIR_INSTRUCTIONS = "Follow Windows' instructions to pair your device."

    #########################
    # config functions
    #########################
    FORMAT_MEM_QUESTION = "Are you sure you want to format the memory?"
    CALIBRATE_ORN_QUESTION = ("Do you want to continue with the orientation sensors calibration?\n"
                    "This will overwrite the calibration data if it already exists\n\n"
                    "If yes, you would need to move and rotate the device for 100 seconds\n")
    RESET_SETTINGS_QUESTION = ("Are you sure you want to reset your settings?\n"
            "The Explore device will disconnect after the soft reset.")
    SELECT_1_CHAN = "At least one channel must be active."
    DISABLED_SETTINGS = "Changing the settings during recording and LSL streaming is not possible"
    DISABLED_RESET = "Resetting the settings during recording and LSL streaming is not possible"
    DISABLED_FORMAT_MEM = "Formatting the memory during recording and LSL streaming is not possible"

    #########################
    # dialogs
    #########################
    OFFSET_EXPLANATION = "Remove the DC offset of the signal based on the previous signal values"

    #########################
    # imp functions
    #########################
    DISABLE_IMP_QUESTION = "Impedance mode will be disabled. Do you want to continue?"
    SET_SR_TO_250_QUESTION = (
        "Impedance mode only works in 250 Hz sampling rate!"
        "\nThe current sampling rate is s_rate. "
        "Click on Yes to change the sampling rate.")

    #########################
    # vis functions
    #########################
    INVALID_MARKER = 'Marker code value is not valid. Please select a value in the range 8 - 65535'

    #########################
    # main window functions
    #########################
    IMP_NOISE = (
        "Impedance measurement will introduce noise to the signal"
        " and affect the visualization, recording, and LSL stream."
        "\nAre you sure you want to continue?")
    IMP_INFO = "The displayed values are an approximation. Please refer to the manual for more information."
    CONNECTION_REQUIRED = "Please connect an Explore device."
