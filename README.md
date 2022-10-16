# ExploreDesktop

## Installation

### Windows
Use the installer file found [here](https://wiki.mentalab.com/explore-desktop-guide/)

### Linux
#### Requirements
 - Python 3.8
 - Bluetooth header files (use this command: `sudo apt-get install libbluetooth-dev`)

#### How to install

1. Download the code or clone the repository
2. Create conda env with python 3.8:  `conda create -n myenv python=3.8`
3. Activate virtual environment: `conda activate myenv`
4. Install liblsl: `conda install -c conda-forge liblsl`
5. Navigate to the explroe-desktop folder `cd path/to/explore-desktop`
6. Run the command `pip install .`


#### Launch the app
**Option 1**
1. Launch the terminal
2. Navigate to the explroedesktop folder `cd path/to/explore-desktop/exploredesktop`
3. Run `python main.py`

**Option 2**
1. Launch the terminal
2. Run `exploredesktop`

