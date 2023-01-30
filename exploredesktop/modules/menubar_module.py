
import logging
import os
import shutil
from pathlib import Path

from explorepy.tools import (
    compare_recover_from_bin,
    generate_eeglab_dataset
)
from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox
)


from exploredesktop.modules import (  # isort:skip
    BaseModel
)
from exploredesktop.modules.dialogs import (  # isort:skip
    ConvertBinDialog,
    RepairDataDialog
)
from exploredesktop.modules.utils import (  # isort:skip
    display_msg
)

logger = logging.getLogger("explorepy." + __name__)


class MenuBarActions(BaseModel):
    """Class containing actions triggered by menubar items"""
    def export_eeglab_dataset(self):
        """Export eeglab dataset
        """
        folder_name = self.select_edf_file()
        if folder_name in [False, '']:
            return

        if not os.path.isdir(folder_name):
            display_msg("Directory does not exist. Please select an existing folder")
            return

        folder_bdfs = os.path.join(folder_name, "bdf")
        if not os.path.isdir(folder_bdfs):
            os.mkdir(folder_bdfs)
            logger.info("Creating folder %s to store bdf files" % folder_bdfs)

        folder_datasets = os.path.join(folder_name, "datasets")
        if not os.path.isdir(folder_datasets):
            os.mkdir(folder_datasets)
            logger.info("Creating folder %s to store dataset files" % folder_datasets)

        n_files = 0
        for file in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file)
            if file_path.endswith(".edf") and os.path.isfile(file_path):
                bdf_file = os.path.splitext(file)[0] + ".bdf"
                dataset_file = os.path.splitext(file)[0] + ".set"
                bdf_path = os.path.join(folder_bdfs, bdf_file)
                dataset_path = os.path.join(folder_datasets, dataset_file)
                shutil.copy2(file_path, bdf_path)
                generate_eeglab_dataset(bdf_path, dataset_path)
                n_files += 1
            elif file_path.endswith(".bdf") and os.path.isfile(file_path):
                dataset_file = os.path.splitext(file)[0] + ".set"
                dataset_path = os.path.join(folder_datasets, dataset_file)
                generate_eeglab_dataset(file_path, dataset_path)
                n_files += 1

        if len(os.listdir(folder_bdfs)) == 0:
            os.rmdir(folder_bdfs)
        # folder_bdfs = os.path.dirname(folder_name)
        folder_datasets = folder_datasets.replace("/", "\\")
        msg = f"{n_files} datasets exported in folder {folder_datasets}"
        logger.info(msg)
        display_msg(msg, popup_type="info")

    def select_edf_file(self) -> None:
        """
        Open a dialog to select file name to be saved
        """
        # TODO get path from last used directory

        dialog = QFileDialog()
        file_path = dialog.getExistingDirectory(
            self,
            "Choose Directory containing EDF/BDF files",
            "",
            QFileDialog.ShowDirsOnly)

        return file_path
        # self.ui.le_import_edf.setText(file_path)

    def convert_bin(self) -> None:
        """Convert BIN file to csv/edf
        """
        dialog = ConvertBinDialog()
        data = dialog.exec()
        if data is False:
            return
        self.explorer.convert_bin(
            bin_file=data['bin_path'],
            out_dir=data['dst_folder'],
            file_type=data['file_type'],
            out_dir_is_full=True
        )
        display_msg("Conversion finished", popup_type="info")

    def repair_data(self) -> None:
        """Repair recorded csv file by comparison with the binary file
        """
        dialog = RepairDataDialog()
        data = dialog.exec()

        if data is False:
            return

        folder_path = Path(data['bin_path']).parent.absolute()
        outfile_bin = self._get_filename_repair(data['bin_path'])
        outfile_csv = self._get_filename_repair(data['csv_path'])

        try:
            self.explorer.convert_bin(
                bin_file=data['bin_path'],
                out_dir=folder_path,
                file_type='csv',
                out_dir_is_full=True
            )
        except FileExistsError:
            msg = (
                "A csv file already exists for the selected .BIN file. Do you want to overwite?"
                # "\nOtherwise, the repare will be done with the existing file"
            )
            response = display_msg(msg_text=msg, popup_type="question")

            if response == QMessageBox.StandardButton.Yes:
                self.explorer.convert_bin(
                    bin_file=data['bin_path'],
                    out_dir=folder_path,
                    file_type='csv',
                    out_dir_is_full=True,
                    do_overwrite=True
                )
            # check if this is wanted bbehaviour of continue
            else:
                return
        try:
            compare_recover_from_bin(outfile_csv, outfile_bin)
            display_msg("Repair finished", popup_type="info")
        except Exception as e:
            logger.debug(f"An error occured during csv recovery: {type(e)}: {e}")
            display_msg("An error occured during csv repair")

    @staticmethod
    def _get_filename_repair(path: str) -> str:
        """Return file name for the given path without file extension"""
        _, full_filename = os.path.split(path)
        filename, _ = os.path.splitext(full_filename)
        out_file = os.path.join(Path(path).parent.absolute(), filename)
        out_file = out_file.replace("_ExG", "").replace("_Meta", "").replace("ORN", "").replace("_Marker", "")
        return out_file