import stream_format_funcs

class reformat:

    def reformat_web(web_input, archive_name):

        unzipped_destination=stream_format_funcs.zip_unzip_funcs.move_and_unzip.web_input(web_input)
        stream_format_funcs.reformat_funcs.reformat_metadata.web(unzipped_destination)
        stream_format_funcs.reformat_funcs.reformat_json.web(unzipped_destination)
        stream_format_funcs.web_report_funcs.reorganize_web(web_input)
        stream_format_funcs.general_funcs.archive_fixed_report(archive_name)

    def reformat_cli(cli_input, archive_name):

        trimmed_path = stream_format_funcs.zip_unzip_funcs.move_and_unzip.cli_input(cli_input)
        stream_format_funcs.formatted_metadata_path = stream_format_funcs.reformat_funcs.reformat_metadata.cli(trimmed_path)
        stream_format_funcs.reformat_funcs.reformat_json.cli(trimmed_path)
        stream_format_funcs.general_funcs.organize_clifiles(trimmed_path)
        stream_format_funcs.general_funcs.archive_fixed_report(archive_name)
