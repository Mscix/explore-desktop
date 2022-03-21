#!/usr/bin/env bash

# Check we are in master branch
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "master" ]]
then
  echo "Please checkout to master branch and try again!"
  exit
fi

# Install Bluetooth headers on Ubuntu
uname=$(uname);
if [[ "$uname" == "Linux" ]]
then
  echo "Installing bluetooth headers!"
  sudo apt-get update -yq
  sudo apt-get install -yq libbluetooth-dev
fi

# Conda virtual env
conda config --append channels conda-forge
if [[ "$uname" == "Linux" ]]
then
  conda install -y gcc
fi
conda create -n gui_installer python=3.8.10 -y
source activate gui_installer
python -m pip install --upgrade pip

# Install qt and qt-ifw (TO BE USED IN FUTURE)
#mkdir temp || rm -rfv temp/*
#cd temp
#pip install aqtinstall
#aqt install-qt linux desktop 6.2.1
#aqt install-tool linux desktop tools_ifw
#aqt install-tool linux desktop tools_maintenance
#cd ..

# Install Pyinstaller
pip install pyinstaller==4.7

# Install ExploreDesktop
conda install -c conda-forge liblsl==1.15.2 -y
pip install pylsl
pip install -e .
pip uninstall explorepy -y
pip install git+https://github.com/Mentalab-hub/explorepy.git@71df00a704b4a76676ee4e861da56cd0796e3b15

# Copy files to data dir
exploredesktop_path="installer/ExploreDesktopInstaller/ExploreDesktop/packages/com.Mentalab.ExploreDesktop/"

# Clean required directories
rm -rfv "$exploredesktop_path"data/*
rm -rfv dist/*

# Create executable files
pyinstaller --onedir --console ExploreDesktop.spec



if [[ "$uname" == "Linux" ]]
then
  cp -r dist/ExploreDesktop "$exploredesktop_path"data
  cp "$exploredesktop_path"extras/MentalabLogo.png "$exploredesktop_path"data/
  cp "$exploredesktop_path"extras/exploredesktop.desktop "$exploredesktop_path"data/
else
  cp -r dist/ExploreDesktop.app "$exploredesktop_path"data
fi


# Extensions
if [[ "$uname" == "Linux" ]]
then
  extension=".run"
  binarycreator_path=/home/"$(whoami)"/Qt/QtIFW-4.2.0/bin/
else
  extension=""
  binarycreator_path=/Users/"$(whoami)"/Qt/QtIFW-4.2.0/bin/
fi
"$binarycreator_path"binarycreator -c "$exploredesktop_path"../../config/config.xml -p "$exploredesktop_path"../ --verbose ExploreDesktopInstaller_x64"$extension"
