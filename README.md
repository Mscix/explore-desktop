# explorepy-qt-gui

## Installation
### Requirements
 - Python 3.8
 - Bluetooth header files (only Linux -> use this command: `sudo apt-get install libbluetooth-dev`)

### How to install

1. Create conda env with python 3.8:  `conda create -n myenv python=3.8`
2. Activate virtual environment: `conda activate myenv`
3. Install required packages: `python -m pip install package_name`
 - `explorepy`
 - `pandas`
 - `pyqtgraph`
 - `PySide6`
 - `mne`
4. Install liblsl with conda: `conda install -c conda-forge liblsl`
5. Launch the app: `python main.py`

Note: Instead of the sum of REF + each channel, now the impedance value is divided by 2. The impedance values shown are only an approximation.
