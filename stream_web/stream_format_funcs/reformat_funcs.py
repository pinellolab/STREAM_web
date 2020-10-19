import os
import pandas as pd

class reformat_metadata:
    def web(trimmed_path):

        unformatted_metadata_path = os.path.join(
            trimmed_path, "STREAM_result/cell_info.tsv"
        )
        formatted_metadata_path = os.path.join(
            trimmed_path, "STREAM_result/metadata.tsv"
        )
        metadata = pd.read_csv(unformatted_metadata_path, sep="\t").iloc[:, 0:3]
        metadata.to_csv(formatted_metadata_path, sep="\t", index=False, header=True)
        os.remove(unformatted_metadata_path)

        print("Metadata has been properly formatted.")

        return formatted_metadata_path

    def cli(trimmed_path):

        import os
        import pandas as pd

        unformatted_metadata_path = os.path.join(trimmed_path, "cell_info.tsv")
        formatted_metadata_path = os.path.join(trimmed_path, "metadata.tsv")
        if os.path.exists(formatted_metadata_path) == False:
            metadata = pd.read_csv(unformatted_metadata_path, sep="\t").iloc[:, 0:3]
            metadata.to_csv(formatted_metadata_path, sep="\t", index=False, header=True)
            os.remove(unformatted_metadata_path)
            print("Metadata has been properly formatted.")

        else:
            print("Metadata file already exists.")

        return formatted_metadata_path

class reformat_json:
    def web(trimmed_path):

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
        dict_analysis["title"] = title
        dict_analysis["description"] = description
        dict_analysis["starting_node"] = starting_node
        dict_analysis["command_used"] = command_used
        with open(
            os.path.join(trimmed_path, "../analysis_description.json"), "w"
        ) as file_path:
            json.dump(dict_analysis, file_path, indent=2)


        print("Analysis description file has been created.")
