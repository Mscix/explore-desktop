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
which python
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

# Install ExploreGUI
pip install -e .

# Copy files to data dir
exploregui_path="installer/ExploreGuiInstaller/ExploreGUI/packages/com.Mentalab.ExploreGUI/"

# Clean required directories
rm -rfv "$exploregui_path"data/*
rm -rfv dist/*

# Create executable files
pyinstaller --onedir --console ExploreGUI.spec



if [[ "$uname" == "Linux" ]]
then
  cp -r dist/ExploreGUI "$exploregui_path"data
  cp "$exploregui_path"extras/MentalabLogo.png "$exploregui_path"data/
  cp "$exploregui_path"extras/exploregui.desktop "$exploregui_path"data/
else
  cp -r dist/ExploreGUI.app "$exploregui_path"data
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
"$binarycreator_path"binarycreator -c "$exploregui_path"../../config/config.xml -p "$exploregui_path"../ --verbose ExploreGUIInstaller"$extension"
