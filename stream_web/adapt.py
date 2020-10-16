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


def move_MACOSX_files(unzipped):

    import os
    import shutil

    unzipped_destination = "/".join(unzipped.split("/")[:-1],)

    shutil.move("./stream-outputs/", unzipped_destination)
    shutil.rmtree("./__MACOSX")


class unzip:
    def web(input_zip, macOSX_linux=True):

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

        unzipped_destination = remove_zip_extension(input_zip)

        if macOSX_linux == True:
            move_MACOSX_files(unzipped_destination)

        return unzipped_destination
    
    def cli(input_zip):
        
        from zipfile import ZipFile
        import shutil
        
        with ZipFile(input_zip, "r") as zip:
            print("Extracting all the files now...")
            zip.extractall()
            print("Done!")
        
        unzipped_destination = remove_zip_extension(input_zip)
        shutil.move("./stream_result/", unzipped_destination)
        
        return unzipped_destination
    
class reformat_metadata:
    
    def web(trimmed_path):
        
        import os
        import pandas as pd

        unformatted_metadata_path = os.path.join(
            trimmed_path, "STREAM_result/cell_info.tsv"
        )
        formatted_metadata_path = os.path.join(trimmed_path, "STREAM_result/metadata.tsv")
        metadata = pd.read_csv(unformatted_metadata_path, sep="\t").iloc[:, 0:3]
        metadata.to_csv(formatted_metadata_path, sep="\t", index=False, header=True)
        os.remove(unformatted_metadata_path)

        print("Metadata has been properly formatted.")
        
        return formatted_metadata_path
        
    def cli(trimmed_path):
        
        import os
        import pandas as pd
        
        unformatted_metadata_path = os.path.join(
            trimmed_path, "cell_info.tsv"
        )
        formatted_metadata_path = os.path.join(trimmed_path, "metadata.tsv")
        metadata = pd.read_csv(unformatted_metadata_path, sep="\t").iloc[:, 0:3]
        metadata.to_csv(formatted_metadata_path, sep="\t", index=False, header=True)
        os.remove(unformatted_metadata_path)
        
        print("Metadata has been properly formatted.")
        
        return formatted_metadata_path

class reformat_json:
    
    def web(trimmed_path):
    
        import os

        old_json_path = os.path.join(trimmed_path, "stream.json")
        new_json_path = os.path.join(trimmed_path, "analysis_description.json")
        os.rename(old_json_path, new_json_path)

        print("Analysis description file has been properly formatted.")
    
    def cli(trimmed_path):
        
        import os
        import json
        
        title = "cmd-line analysis"
        description = "undetermined"
        starting_node = "S0"
        command_used = "STREAM Command Line"
        
        dict_analysis = {}
        dict_analysis['title']= title
        dict_analysis['description'] = description
        dict_analysis['starting_node'] = starting_node
        dict_analysis['command_used'] = command_used
        with open(os.path.join(trimmed_path,'analysis_description.json'), 'w') as file_path:
            json.dump(dict_analysis, file_path,indent=2)
            
        print("Analysis description file has been created.")

def organize_files(trimmed_file):

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
        
def zip_reformatted_result(reformatted_zip):

    import os
    import shutil

    print("Zipping reformatted files...")

    archive_name = os.path.basename(reformatted_zip)
    directory = os.path.split(reformatted_zip)[0]

    shutil.make_archive(base_name=archive_name, format="zip", root_dir=directory)
    shutil.rmtree(unzipped_unconverted_results)
    print("Done!")
    
    
def zip_reformatted_result(trimmed_path, reformatted_zip):

    import os
    import shutil

    print("Zipping reformatted files...")

    archive_name = remove_zip_extension(os.path.basename(reformatted_zip))
    directory = os.path.split(reformatted_zip)[0]

    shutil.make_archive(base_name=archive_name, format="zip", root_dir=trimmed_path)
    shutil.move(os.path.basename(reformatted_zip), reformatted_zip)
    shutil.rmtree(trimmed_path)
    print("Done!")
    
class reformat:
    def web(web_input, reformatted_zip):

        trimmed_path = unzip.web(web_input)
        formatted_metadata_path = reformat_metadata.web(trimmed_path)
        reformat_json.web(trimmed_path)
        zip_reformatted_result(trimmed_path, reformatted_zip)
        
    def cli(cli_input, reformatted_zip):
        
        trimmed_path = unzip.cli(cli_input)
        formatted_metadata_path = reformat_metadata.cli(trimmed_path)
        reformat_json.cli(trimmed_path)
        organize_files(trimmed_path)
        zip_reformatted_result(trimmed_path, reformatted_zip)
        