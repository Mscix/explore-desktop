@REM @echo off
@REM Check we are in master branch

@REM git branch | find "* master" > NUL & IF ERRORLEVEL 1 (
@REM     echo "Please checkout to master branch and try again!"
@REM     exit
@REM )


@REM # Conda virtual env
call conda config --append channels conda-forge
call conda create -n gui_installer python=3.8.10 -y
call conda activate gui_installer
call python -m pip install --upgrade pip

@REM Install qt and qt-ifw (TO BE USED IN FUTURE)
@REM mkdir temp || rm -rfv temp/*
@REM cd temp
@REM pip install aqtinstall
@REM aqt install-qt linux desktop 6.2.1
@REM aqt install-tool linux desktop tools_ifw
@REM aqt install-tool linux desktop tools_maintenance
@REM cd ..

@REM Install Pyinstaller
call pip install pyinstaller==4.7

@REM Install ExploreDesktop
call pip install -e .

@REM  Clean required directories
call set exploredesktop_path="installer\ExploreDesktopInstaller\ExploreDesktop\packages\com.Mentalab.ExploreDesktop\"
call rd /S /Q %exploredesktop_path%data
call md %exploredesktop_path%data
call rd /S /Q dist

@REM Create executable files
call pyinstaller --onedir --console ExploreDesktop.spec

@REM Copy files to data dir
call xcopy /I /E /H /R /Q dist\ExploreDesktop %exploredesktop_path%data\ExploreDesktop
call xcopy %exploredesktop_path%extras\MentalabLogo.ico %exploredesktop_path%data


@REM Create installer file
call set config_path= "installer\ExploreDesktopInstaller\ExploreDesktop\config\config.xml"
call set package_path="installer\ExploreDesktopInstaller\ExploreDesktop\packages"
call C:\Qt\QtIFW-4.2.0\bin\binarycreator -c %config_path% -p %package_path% --verbose ExploreDesktopInstaller.exe
