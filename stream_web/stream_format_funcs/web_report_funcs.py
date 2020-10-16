from . import general_funcs
import os
import shutil

def reorganize_web(web_input, stream_report_recognize_name = "stream_report"):

    packed = os.path.basename(web_input)
    name = general_funcs.remove_zip_extension(packed)

    # rename stream-outputs to stream_report (within the temp folder)
    old_dir_name = os.path.join(os.getcwd(), name)
    shutil.move(old_dir_name, stream_report_recognize_name)

    # move analysis description.json up parallel to stream_report
    shutil.move("./stream_report/analysis_description.json", ".")

    # leave cell_label.tsv and matrix where it is

    # move everything out of STREAM_result up .. and delete STREAM_result
    STREAM_result_contents = os.path.join(os.getcwd(), stream_report_recognize_name, "STREAM_result/")
    general_funcs.move_contents(STREAM_result_contents, stream_report_recognize_name)

    os.remove(packed)
