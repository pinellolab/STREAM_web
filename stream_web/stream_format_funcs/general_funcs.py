import os
import shutil
import random
import string

def get_random_string(length):

    """generate a string of random length"""

    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))

    return result_str


def make_random_dir():

    """"""

    tempdir = get_random_string(12)
    original_dir = os.getcwd()
    os.makedirs(tempdir)
    tempdir = os.path.join(original_dir, tempdir)

    return original_dir, tempdir


def move_files_move_wd(zipped_infile):

    """Move the zipped files to the tempdir as well as change your wd to that dir."""

    original_dir, tempdir = make_random_dir()
    shutil.copy(zipped_infile, tempdir)
    temp_zipfile = os.path.join(tempdir, os.path.basename(zipped_infile))
    os.chdir(tempdir)

    print("Input file moved to tempdir:", os.getcwd(), "This is the current wd.")

    return original_dir, temp_zipfile, tempdir

def remove_zip_extension(path):

    """
    Parameters:
    -----------
    path
        any file that ends in the extension, ".zip"

    Returns:
    --------
    Returns the path of a file taking away ".zip"
    """

    if path[-4:] == ".zip":
        trimmed_path = path[:-4]

    return trimmed_path


def remove_MACOSX_files(unzipped):

    unzipped_destination = "/".join(
        unzipped.split("/")[:-1],
    )

    # shutil.move("./stream-outputs/", unzipped_destination)
    shutil.rmtree("./__MACOSX")


def move_MACOSX_files(unzipped):

    unzipped_destination = "/".join(
        unzipped.split("/")[:-1],
    )

    shutil.move("./stream-outputs/", unzipped_destination)
    shutil.rmtree("./__MACOSX")

def archive_fixed_report(archive):

    archive_name = remove_zip_extension(os.path.basename(archive))
    root = os.path.basename(os.getcwd())
    try:
        os.rename("stream_result", "stream_report")
    except:
        pass
    os.chdir("../")
    shutil.make_archive(base_name=archive_name, format="zip", root_dir=root)
    shutil.move(os.path.basename(archive), archive)
    shutil.rmtree(root)

def move_contents(source_dir, target_dir):

    file_names = os.listdir(source_dir)

    for file_name in file_names:
        shutil.move(os.path.join(source_dir, file_name), target_dir)

    shutil.rmtree(source_dir)

def organize_clifiles(trimmed_file):

    """
    Moves files into a new subdirectory such that it is formatted properly for the next step.
    """

    import os
    import shutil

    results_subdirectory = os.path.join(trimmed_file, "STREAM_result")
    print("Reorganizing results into:", results_subdirectory)
    try:
        os.makedirs(results_subdirectory)
    except:

        for file in os.listdir(trimmed_file):
            if file[-4:] != "json":
                old_file_path = os.path.join(trimmed_file, file)
                new_file_path = os.path.join(results_subdirectory, file)
                try:
                    shutil.move(old_file_path, new_file_path)
                except:
                    continue
