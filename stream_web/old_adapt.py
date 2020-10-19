##################################################
# overview of python script
##################################################

# This is a script to functionalize the adapter for STREAM
# file name  | adapt.py
# import     | from adapt import reformat as ref
# executable | ref.web(input_zip, output_zip)
#            | or
#            | ref.cmdln(input_zip, output_zip)

##################################################
# import and setup working environment
##################################################

import os
import sys
import json
import shutil
import os.path
import argparse
import numpy as np
import pandas as pd
from os import listdir
from zipfile import ZipFile
from os.path import isfile, join

##################################################
# paths and unzip the files
##################################################

def unzip(zipped_file):
    # opening zip file in read mode
    with ZipFile(zipped_file, 'r') as zip:
        # printing contents of the zip file
        # zip.printdir()
        # extracting all the files
        print('Extracting all the files now...')
        zip.extractall()
        print('Done!')

def pathset(interface, input_zip):
    file = input_zip
    if interface == "web":
        container_folder = os.path.join(os. getcwd(), 'stream-outputs')
        naive_result_folder = os.path.join(container_folder, 'STREAM_result')
    elif interface == "command-line":
        container_folder = os.path.join(os. getcwd(), 'stream_result')
        rootdirFiles = ['stream_report/', 'analysis_description.json']

    zipped_file = os.path.join(os. getcwd(), file)
    unzip(zipped_file)

    return container_folder

##################################################
# make metadata
##################################################

def make_mdata(interface, container_folder):
    if interface == "web":
        naive_result_folder = os.path.join(container_folder, 'STREAM_result')
    else:
        naive_result_folder = container_folder

    meta_tsv = os.path.join(naive_result_folder, 'metadata.tsv')
    if os.path.exists(meta_tsv) == True:
        print("The metadata file is already in place and ready to go")
    else:
        cellinfopath = os.path.join(naive_result_folder, 'cell_info.tsv')
        cellinfo = pd.read_csv(cellinfopath, sep='\t')
        mdata = cellinfo.iloc[:,0:3]
        outpath = os.path.join(naive_result_folder, 'metadata.tsv')
        mdata.to_csv(outpath, sep='\t',index=False,header=True)

    return naive_result_folder

##################################################
# move files around
##################################################

def move_files(container_folder, interface, naive_result_folder, input_zip):

    allfiles = [f for f in listdir(container_folder)]
    mostfiles = []
    for file in allfiles:
        if file != 'stream_report':
            mostfiles.append(file)
    newsub = os.path.join(container_folder,'stream_report')  # give it a var
    print(newsub)
    if interface == "web":
        os.rename(naive_result_folder, newsub)
        moved_cell_labels = os.path.join(newsub, 'cell_label.tsv')
        movedData = os.path.join(newsub, input_zip, '_fixed.tsv.gz')
    elif interface == "command-line":
        print(newsub, "now old", container_folder)
        for file in mostfiles:
            if file.endswith(".json") == False:
                oldfile = os.path.join(container_folder, file)
                newfile = os.path.join(newsub, file)
                os.rename(oldfile, newfile)
            else:
                print("All files are moved to the appropriate directory.")

##################################################
# format the json file
##################################################

def format_json(container_folder):

    old_json=os.path.join(container_folder, 'stream.json')
    new_json=os.path.join(container_folder, 'analysis_description.json')
    if os.path.exists(old_json) == True:  # in the case of the web report output but not the cmd line
        os.rename(old_json, new_json)
    else: # should be used in receiving and adapting the command line output
        dict_analysis = {}
        dict_analysis['title']= title
        dict_analysis['description'] = description
        dict_analysis['starting_node'] = starting_node
        dict_analysis['command_used'] = command_used
        with open(os.path.join(container_folder,'analysis_description.json'), 'w') as fp:
            json.dump(dict_analysis, fp,indent=2)

##################################################
# clean up the tmp junk files
##################################################

def cleanup(container_folder, interface):

    macfiles = os.path.join(os. getcwd(), "__MACOSX") # this is a dir generated upon the unzip function
    if os.path.exists(macfiles) == True:
        shutil.rmtree(macfiles)

    keep_files = ['stream_report/', 'analysis_description.json']
    # list of all files, desired and undesired
    allfiles = [f for f in listdir(container_folder) if isfile(join(container_folder, f))]

    for files in allfiles: # last step - get rid of unnecessary files
        # print(os.path.join(rootdir, files))
        if files in keep_files:
            None
        else:
            os.remove(os.path.join(container_folder, files))

##################################################
# zip the result
##################################################

def zip_res(container_folder, output_zip):
    print('Zipping the files...you will soon be able to begin your visualization by uploading it to the STREAM webpage.')
    shutil.make_archive(base_name=output_zip, format='zip',root_dir=container_folder)
    shutil.rmtree(container_folder)
    # os.chdir(experimentFolder)
    print('Done!')

##################################################
# this is the executable wrapper function
##################################################

# from adapt import reformat
class reformat:
    def web(input_zip, output_zip):

        if output_zip[-4:] == ".zip":
            output_zip = output_zip[:-4]

        interface = "web"
        container_folder = pathset(interface,input_zip)
        naive_result_folder = make_mdata(interface, container_folder)
        move_files(container_folder, interface, naive_result_folder, input_zip)
        format_json(container_folder)
        cleanup(container_folder, interface)
        zip_res(container_folder, output_zip)

    def cmdln(input_zip, output_zip):

        if output_zip[-4:] == ".zip":
            output_zip = output_zip[:-4]

        interface = "command-line"
        container_folder = pathset(interface, input_zip)
        naive_result_folder = make_mdata(interface, container_folder)
        move_files(container_folder, interface, naive_result_folder, input_zip)
        cleanup(container_folder, interface)
        zip_res(container_folder, output_zip)
