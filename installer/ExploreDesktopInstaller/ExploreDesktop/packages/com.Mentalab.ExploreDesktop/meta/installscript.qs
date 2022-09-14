
function Component()
{
    // default constructor
}

Component.prototype.createOperations = function()
{
    // call the base create operations function
    component.createOperations();
    
    if (systemInfo.kernelType === "linux") {
        component.addElevatedOperation("LineReplace", "@TargetDir@/exploredesktop.desktop", "Exec=", "Exec=@TargetDir@/ExploreDesktop/ExploreDesktop");
        component.addElevatedOperation("LineReplace", "@TargetDir@/exploredesktop.desktop", "Icon=", "Icon=@TargetDir@/MentalabLogo.png");
        component.addElevatedOperation("Move", "@TargetDir@/exploredesktop.desktop", "/usr/share/applications/exploredesktop.desktop");
    } else if (systemInfo.kernelType === "darwin") {
        // var args = ["sudo cp", "-R", "@TargetDir@/ExploreGUI.app", "/Applications"];
        // component.addElevatedOperation("Execute", args);
        component.addElevatedOperation("Copy", "@TargetDir@/ExploreDesktop.app", "/Applications/ExploreDesktop.app");
    } else if (systemInfo.kernelType === "winnt") {
        component.addElevatedOperation("CreateShortcut", "@TargetDir@/ExploreDesktop/ExploreDesktop.exe", "@StartMenuDir@/ExploreDesktop.lnk", "workingDirectory=@TargetDir@", "iconPath=@TargetDir@/MentalabLogo.ico");
        component.addElevatedOperation("CreateShortcut", "@TargetDir@/ExploreDesktop/ExploreDesktop.exe", "@DesktopDir@/ExploreDesktop.lnk", "workingDirectory=@TargetDir@", "iconPath=@TargetDir@/MentalabLogo.ico");
    }
}
