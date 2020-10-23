import os
import shutil
import pandas as pd
from . import general_funcs
from zipfile import ZipFile

def unzip_webzip(input_zip, macOSX_linux=False):

    """
    Parameters:
    -----------
    input_zip
        path to the zipped file

    Returns:
    --------
    Unzipped file path.
    """

    from zipfile import ZipFile

    with ZipFile(input_zip, "r") as zip:
        print("Extracting all the files now...")
        zip.extractall()
        print("Done!")

    unzipped_destination = general_funcs.remove_zip_extension(input_zip)

    if macOSX_linux == True:
        general_funcs.remove_MACOSX_files(unzipped_destination)

    return unzipped_destination

def unzip_clizip(input_zip):

    from zipfile import ZipFile

    with ZipFile(input_zip, "r") as zip:
        print("Extracting all the files now...")
        zip.extractall()
        print("Done!")

    unzipped_destination = general_funcs.remove_zip_extension(input_zip)

    return unzipped_destination

class move_and_unzip:
    def web_input(input_zip):

        original_dir, temp_zipfile, tempdir = general_funcs.move_files_move_wd(input_zip)
        unzipped_destination = unzip_webzip(temp_zipfile)
        print(unzipped_destination)

        return unzipped_destination


    def cli_input(input_zip):

        original_dir, temp_zipfile, tempdir = general_funcs.move_files_move_wd(input_zip)
        unzipped_destination = unzip_clizip(temp_zipfile)

        return unzipped_destination

        # unzipped_destination = general_funcs.remove_zip_extension(input_zip)
        # shutil.move("./stream_result/", unzipped_destination)

        return unzipped_destination
