# exploreGUI

## Installation
### Requirements
 - Python 3.8.10
 - Bluetooth header files (only Linux -> use this command: `sudo apt-get install libbluetooth-dev`)

### How to install

1. Create conda env with python 3.8.10:  `conda create -n myenv python=3.8.10`
2. Activate virtual environment: `conda activate myenv`
3. `cd path/to/explorepy-gui`
4. `pip install -e .`

5. Launch the app: `python main.py` or `exploregui`
If there is any error with liblsl try to install it manually: `conda install -c conda-forge liblsl`

## Create installer file
### Requirements
 - Anaconda
 - Qt Installer Framework v4.2 (download the appropriate setup file 
[here](https://download.qt.io/official_releases/qt-installer-framework/4.2.0/)). **NOTE: Leave the default installation
path, e.g.:**
    - Ubuntu: `/home/<USER-NAME>/Qt/QtIFW-4.2.0/`
    - macOS: `/Users/"$(whoami)"/Qt/QtIFW-4.2.0/`
    - Windows: `C:\Qt\QtIFW-4.2.0`

### Windows
1. Open cmd
2. `cd path\to\explorepy-gui`
3. `create-setup-file-windows.bat`
4. `ExploreGUIInstaller.exe` will be created in the `explorepy-gui` directory.

### Ubuntu
1. Open a terminal
2. `cd path\to\explorepy-gui`
3. `bash ./create-setup-file.sh`
4. `ExploreGUIInstaller.run` will be created in the `explorepy-gui` directory.

### macOS
1. Open a terminal
2. `cd path\to\explorepy-gui`
3. `bash ./create-setup-file.sh` 
4. `ExploreGUIInstaller` will be created in the `explorepy-gui` directory.