### STREAM Dash Application
import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from upload_button import FilesUpload, upload_files
from flask import Flask, request, redirect, url_for, render_template, jsonify, send_from_directory, send_file, session
import requests
import re
import subprocess as sb
import numpy as np
import pandas as pd
import sys
import os
import glob
import base64
import urllib
import ast
import random
import gzip
import uuid
import json
#import cPickle as cp
import csv
import time
import zipfile
from slugify import slugify
import reformat_stream as rs
# from adapt import reformat as ref
import io

_ROOT = os.path.abspath(os.path.dirname(__file__))

class Dash_responsive(dash.Dash):
    def __init__(self, *args, **kwargs):
        super(Dash_responsive,self).__init__(*args, **kwargs)

    def index(self, *args, **kwargs):  # pylint: disable=unused-argument
        scripts = self._generate_scripts_html()
        css = self._generate_css_dist_html()
        config = self._generate_config_html()
        title = getattr(self, 'title', 'STREAM')
        return '''
        <!DOCTYPE html>
        <html>
            <head>
            <!-- Global site tag (gtag.js) - Google Analytics -->
            <script async src='https://www.googletagmanager.com/gtag/js?id=UA-117917519-1'></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());

              gtag('config', 'UA-117917519-1');
            </script>
            '''+'''

                <meta charset="UTF-8">
                <title>{}</title>
                {}
                <link rel="stylesheet" href="/static/STREAM.css">
                <link rel="stylesheet" href="/static/Loading-State.css">
                <script src="/static/jquery-3.3.1.min.js"></script>
            </head>
            <body>
                <div id="react-entry-point">
                    <div class="_dash-loading">
                        Loading...
                    </div>
                </div>
                <footer>
                    {}
                    {}
                </footer>
            </body>
        </html>
        '''.format(title, css, config, scripts)

def get_data(path):
        return os.path.join(_ROOT, path)

# STREAM logo
stream_logo = get_data('/stream_web/static/stream_logo.png')
stream_logo_image = base64.b64encode(open(stream_logo, 'rb').read()).decode('ascii')

mgh_logo = get_data('/stream_web/static/mgh.png')
mgh_logo_image = base64.b64encode(open(mgh_logo, 'rb').read())

mitbe_logo = get_data('/stream_web/static/mitbe.png')
mitbe_logo_image = base64.b64encode(open(mitbe_logo, 'rb').read())

hms_logo = get_data('/stream_web/static/hms.png')
hms_logo_image = base64.b64encode(open(hms_logo, 'rb').read())

# Generate ID to initialize CRISPR-SURF instance
server = Flask(__name__)
server.secret_key = '~x94`zW\sfa24\xa2qdx20g\x9dl\xc0x35x90\kchs\x9c\xceb\xb4'
app = Dash_responsive('stream-compute', server = server, url_base_pathname = '/compute/', csrf_protect=False)

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

app2 = Dash_responsive(name = 'stream-app-precomputed', server = server, url_base_pathname = '/precomputed/', csrf_protect=False)

app2.css.config.serve_locally = True
app2.scripts.config.serve_locally = True

app.server.config['UPLOADS_FOLDER']='/tmp/UPLOADS_FOLDER'
app.server.config['RESULTS_FOLDER']='/tmp/RESULTS_FOLDER'
app.server.config['VISUALIZE_FOLDER']='/tmp/VISUALIZE_FOLDER'
app.server.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 #200 Mb max

# app2.server.config['UPLOADS_FOLDER']='/tmp/UPLOADS_FOLDER'
# app2.server.config['RESULTS_FOLDER']='/tmp/RESULTS_FOLDER'
# app2.server.config['VISUALIZE_FOLDER']='/tmp/VISUALIZE_FOLDER'
# app2.server.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 #200 Mb max

@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)

# @app2.server.route('/static/<path:path>')
# def static_file(path):
#     static_folder = os.path.join(os.getcwd(), 'static')
#     return send_from_directory(static_folder, path)

@server.route('/help')
def help():
	return render_template('help.html')

# @app2.server.route("/static/<path:path>")@app.server.route('/static/<path:path>')
# def static_file(path):
#     static_folder = os.path.join(os.getcwd(), 'static')
#     return send_from_directory(static_folder, path)

# def download(path):
#     static_folder = os.path.join(os.getcwd(), 'static')
#     return send_from_directory(static_folder, path)

# @server.route('/help')
# def help():
# 	return render_template('help.html')

@server.route('/')
def index():
	newpath = 'STREAM_' + str(uuid.uuid4())

	UPLOADS_FOLDER = os.path.join(app.server.config['UPLOADS_FOLDER'], newpath)
	RESULTS_FOLDER = os.path.join(app.server.config['RESULTS_FOLDER'], newpath)
	# VISUALIZE_FOLDER = os.path.join(app.server.config['VISUALIZE_FOLDER'], newpath)

	if not os.path.exists(UPLOADS_FOLDER):
		os.makedirs(UPLOADS_FOLDER)

	if not os.path.exists(RESULTS_FOLDER):
		os.makedirs(RESULTS_FOLDER)

	# if not os.path.exists(VISUALIZE_FOLDER):
	# 	os.makedirs(VISUALIZE_FOLDER)

	param_dict = {'compute-clicks':0, 'sg-clicks':0, 'discovery-clicks':0, 'correlation-clicks':0, 'leaf-clicks':0, 'starting-nodes':['S0'],
	'sg-genes':['False'], 'discovery-genes':['False'], 'correlation-genes':['False'], 'leaf-genes':['False'],'sg-gene':'False', 'discovery-gene':'False', 'correlation-gene':'False', 'leaf-gene':'False',
	'compute-run':False,'sg-run':False,'discovery-run':False, 'correlation-run':False, 'leaf-run':False, 'required_files': ['Data Matrix', 'Cell Labels', 'Cell Label Colors'],
	'checkbutton1':1, 'checkpoint1':True,'checkbutton2':1, 'checkpoint2':True,'checkbutton3':1, 'checkpoint3':True,'checkbutton4':1, 'checkpoint4':True,'checkbutton5':1, 'checkpoint5':True,
	'matrix-update':'Data Matrix: No Upload (Required)', 'cl-update':'Cell Labels File: No Upload (Optional)', 'clc-update':'Cell Label Colors File: No Upload (Optional)', 'compute-disable':True, 'compute-update':'Load Personal or Example Data (Step 1)', 'visualize-update':'Press button above to visualize your data!'} #'zip-update':'STREAM Results (.zip): No Upload',

	with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
		json_string = json.dumps(param_dict)
		f.write(json_string + '\n')

	# UPLOADS_FOLDER = os.path.join(app2.server.config['UPLOADS_FOLDER'], newpath)
	# RESULTS_FOLDER = os.path.join(app2.server.config['RESULTS_FOLDER'], newpath)
	# VISUALIZE_FOLDER = os.path.join(app2.server.config['VISUALIZE_FOLDER'], newpath)

	# if not os.path.exists(UPLOADS_FOLDER):
	# 	os.makedirs(UPLOADS_FOLDER)

	# if not os.path.exists(RESULTS_FOLDER):
	# 	os.makedirs(RESULTS_FOLDER)

	# if not os.path.exists(VISUALIZE_FOLDER):
	# 	os.makedirs(VISUALIZE_FOLDER)

	return render_template('index.html',newpath=newpath)
	#return redirect('/compute/' + newpath)

#Import some other useful functions
def generate_table(dataframe, max_rows = 100):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

# # Upload file
# upload_url2='/uploadajax2'

# @app2.server.route(upload_url2, methods = ['POST'])
# def save_files2():

# 	folder_location = request.referrer
# 	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(folder_location.split('/')[-1])

# 	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
# 		json_string = f.readline().strip()
# 		param_dict = json.loads(json_string)

# 	try:
# 		sb.call('rm %s/STREAM_Results_*zip' % UPLOADS_FOLDER, shell = True)
# 	except:
# 		pass

# 	upload_files(['STREAM Results .zip'], UPLOADS_FOLDER)

# 	stream_zip = glob.glob(UPLOADS_FOLDER + '/STREAM_Results_*zip')

# 	if len(stream_zip) > 0:

# 		for i in stream_zip:

# 			new_folder_name = 'USER_UPLOAD_%s' % str(folder_location.split('/')[-1])

# 			sb.call('rm -rf /stream_web/precomputed/%s' % new_folder_name, shell = True)

# 			sb.call('mkdir /stream_web/precomputed/%s' % new_folder_name, shell = True)

# 			zip_ref = zipfile.ZipFile(i, 'r')
# 			zip_ref.extractall('/stream_web/precomputed/%s/' % new_folder_name)
# 			zip_ref.close()

# 			try:
# 				sb.call('mkdir /stream_web/precomputed/%s/stream_report' % new_folder_name, shell = True)
# 			except:
# 				pass

# 			sb.call('mv /stream_web/precomputed/%s/*/*json /stream_web/precomputed/%s' % (new_folder_name, new_folder_name), shell = True)
# 			sb.call('mv /stream_web/precomputed/%s/*/stream_report/* /stream_web/precomputed/%s/stream_report' % (new_folder_name, new_folder_name), shell = True)
# 			sb.call('rm -rf /stream_web/precomputed/%s/*/stream_report' % new_folder_name, shell = True)

# 			try:
# 				sb.call('rm -rf /stream_web/precomputed/%s/__MACOSX' % new_folder_name, shell = True)
# 			except:
# 				pass

# 			# json_list = glob.glob('/stream_web/precomputed/*/*json')

# 			# for j in  json_list:

# 			# 	previous_folder_name = j.strip('\n').split('/')[-1].replace('.json','')
# 			# 	new_folder_name = j.strip('\n').split('/')[-1].replace('.json','')

# 			# 	print(previous_folder_name)
# 			# 	print(new_folder_name)

# 			# 	sb.call('mkdir /stream_web/precomputed/%s' % folder_name, shell = True)
# 			# 	sb.call('mv /stream_web/precomputed/%s.json stream_report /stream_web/precomputed/%s' % (folder_name, folder_name), shell = True)

# 		param_dict['zip-update'] = 'Successfully loaded STREAM Results (.zip)'

# 		with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
# 			new_json_string = json.dumps(param_dict)
# 			f.write(new_json_string + '\n')

# 		# print('Completed upload ...')

# 		return 'Completed upload ...'

# 	else:

# 		wrong_files = glob.glob(UPLOADS_FOLDER + '/STREAM_Results_*')

# 		for i in wrong_files:

# 			sb.call('rm %s' % (i), shell = True)

# 		param_dict['zip-update'] = 'Failed to load STREAM Results. Please upload correct file format (.zip).'

# 		with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
# 			new_json_string = json.dumps(param_dict)
# 			f.write(new_json_string + '\n')

# 		# print('Upload Failed. Please upload .zip file.')

# 		return 'Upload Failed. Please upload .zip file.'


upload_url1='/uploadajax1'

@app.server.route(upload_url1, methods = ['POST'])
def save_files1():

	folder_location = request.referrer
	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(folder_location.split('/')[-1])

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	rem_files = []
	for i in param_dict['required_files']:
		rem_file = glob.glob(UPLOADS_FOLDER + '/' + '_'.join(map(str, i.split())) + '*')
		try:
			rem_files.append(rem_file[0])
		except:
			continue

	for i in rem_files:
		sb.call('rm %s' % i, shell = True)

	upload_files(param_dict['required_files'], UPLOADS_FOLDER)

	# Detect files
	matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
	cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
	cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

	# Matrix reporting
	matrix_update = 'initialize'
	if len(matrix) > 0:

		if matrix[0].endswith('tsv') or matrix[0].endswith('tsv.gz'):

			df = pd.read_table(matrix[0], sep = '\t', header = None, low_memory = False, compression = 'infer')
			if str(df.get_value(0,0)) == 'nan':

				df = pd.read_table(matrix[0], index_col = 0, sep = '\t', compression = 'infer')

			else:
				matrix_update = 'Data Matrix: [ERROR] Column and row IDs must be present ...'

		elif matrix[0].endswith('txt') or matrix[0].endswith('txt.gz'):

			df = pd.read_table(matrix[0], sep = '\t', header = None, low_memory = False, compression = 'infer')
			if str(df.get_value(0,0)) == 'nan':

				df = pd.read_table(matrix[0], index_col = 0, sep = '\t', compression = 'infer')

			else:
				matrix_update = 'Data Matrix: [ERROR] Column and row IDs must be present ...'

		elif matrix[0].endswith('csv') or matrix[0].endswith('csv.gz'):

			df = pd.read_table(matrix[0], sep = ',', header = None, low_memory = False, compression = 'infer')
			if str(df.get_value(0,0)) == 'nan':

				df = pd.read_table(matrix[0], index_col = 0, sep = ',', compression = 'infer')

			else:
				matrix_update = 'Data Matrix: [ERROR] Column and row IDs must be present ...'

		else:
			matrix_update = 'Data Matrix: [ERROR] File format needs to be .tsv, .csv, or .txt ...'

		if '[ERROR]' not in matrix_update:

			if len(df.columns) > 2500:
				matrix_update = 'Data Matrix: [ERROR] Limit of 2500 cells (Detected %s Cells) ...' % len(df.columns)

			elif df.isnull().values.any():
				matrix_update = 'Data Matrix: [ERROR] NaN values detected in matrix ...'

			elif df._get_numeric_data().size != df.size:
				matrix_update = 'Data Matrix: [ERROR] Matrix contains non-numeric values ...'

			else:
				matrix_update = 'Data Matrix: Upload Successful'

	else:
		matrix_update = 'Data Matrix: No Upload (Required)'

	# Cell Labels File and Cell Label Colors File reporting
	if len(cell_label) > 0:

		if len(matrix) > 0:

			if len(cell_label_colors) > 0:
				cl = pd.read_table(cell_label[0], header = None, low_memory = False, compression = 'infer')
				clc = pd.read_table(cell_label_colors[0], header = None, low_memory = False, compression = 'infer')

				# cl = pd.read_table('Cell_Labels_cell_label.tsv.gz', header = None, low_memory = False, compression = 'infer')
				# clc = pd.read_table('Cell_Label_Colors_cell_label_color.tsv.gz', header = None, low_memory = False, compression = 'infer')


				if len(cl.columns) == 1 and cl.size == len(df.columns):
					matches = []
					for i in clc.iloc[:,1].tolist():
						if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', i):
							matches.append(1)

					if sorted(list(set(clc.iloc[:,0]))) == sorted(list(set(cl.iloc[:,0]))) and sum(matches) == len(clc.iloc[:,1].tolist()):
						cl_update = 'Cell Labels File: Upload Successful'
						clc_update = 'Cell Label Colors File: Upload Successful'

					elif sorted(list(set(clc.iloc[:,0]))) == sorted(list(set(cl.iloc[:,0]))):
						cl_update = 'Cell Labels File: Upload Successful'
						clc_update = 'Cell Label Colors File: [ERROR] Cell Label Colors file does not provide HEX color code ...'

					else:
						cl_update = 'Cell Labels File: [ERROR] Disagreement between number of Cell Labels and Cell Label Colors ...'
						clc_update = 'Cell Label Colors File: [ERROR] Disagreement between number of Cell Labels and Cell Label Colors ...'

				else:
					cl_update = 'Cell Labels File: [ERROR] Cell Labels file contains incorrect number of labels (%s Labels for %s Cells) ...' % (cl.size, len(df.columns))

					matches = []
					for i in clc.iloc[:,1].tolist():
						if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', i):
							matches.append(1)

					if list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])) and sum(matches) == len(clc.iloc[:,1].tolist()):
						clc_update = 'Cell Label Colors File: Upload Successful'

					elif list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])):
						clc_update = 'Cell Label Colors File: [ERROR] Cell Label Colors file does not provide HEX color code ...'

					else:
						clc_update = 'Cell Label Colors File: [ERROR] Disagreement between number of Cell Labels and Cell Label Colors ...'

			else:
				clc_update = 'Cell Label Colors File: No Upload (Optional)'

				cl = pd.read_table(cell_label[0], header = None, low_memory = False, compression = 'infer')
				if len(cl.columns) == 1 and cl.size == len(df.columns):
					cl_update = 'Cell Labels File: Upload Successful'

				else:
					cl_update = 'Cell Labels File: [ERROR] Cell Labels file contains incorrect number of labels (%s Labels for %s Cells)' % (cl.size, len(df.columns))

		else:
			cl_update = 'Cell Labels File: [ERROR] No input Data Matrix ...'

			if len(cell_label_colors) > 0:
				clc_update = 'Cell Label Colors File: [ERROR] No input Data Matrix ...'
			else:
				clc_update = 'Cell Label Colors File: No Upload (Optional)'

	elif len(cell_label_colors) > 0:
		cl_update = 'Cell Labels File: No Upload (Optional)'
		clc_update = 'Cell Label Colors File: [ERROR] No associated Cell Labels File ...'

	else:
		cl_update = 'Cell Labels File: No Upload (Optional)'
		clc_update = 'Cell Label Colors File: No Upload (Optional)'

	# Update JSON
	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

	param_dict['matrix-update'] = matrix_update
	param_dict['cl-update'] = cl_update
	param_dict['clc-update'] = clc_update

	if matrix_update == 'Data Matrix: Upload Successful' and ('[ERROR]' not in cl_update) and ('[ERROR]' not in clc_update):
		param_dict['compute-disable'] = False
		param_dict['compute-update'] = 'Compute'
	else:
		param_dict['compute-disable'] = True
		param_dict['compute-update'] = 'Load Personal or Example Data (Step 1)'

	with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
		new_json_string = json.dumps(param_dict)
		f.write(new_json_string + '\n')

	return 'Completed upload ...'

app2.layout = html.Div([

	dcc.Interval(id='common-interval2', interval=5000),

	dcc.Location(id='url2', refresh=False),

	html.Div(id = 'custom-loading-states-11',
		children = [

		html.Div(id = 'custom-loading-state11', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Img(src='data:image/png;base64,{}'.format(stream_logo_image), width = '50%'),
	html.H2('Single-cell Trajectory Reconstruction Exploration And Mapping'),

	html.Hr(),

	html.Div(

		id = 'precomputed-container1',
		children = [

		html.Div(

			id = 'precomputed-container2',
			children = [

			html.H3('Choose Loaded Data Set'),

			dcc.Dropdown(
				id = 'precomp-dataset',
			    options=[
			        {'label': 'Nestorowa, S. et al. 2016', 'value': 'Nestorowa'},
			    ],
			    value = 'Nestorowa'
			),

			html.Label(id = 'title', children = ''),
			html.Label(id = 'description', children = ''),
			html.Label(id = 'startingnode', children = ''),
			html.Label(id = 'commandline', children = ''),

			], className = 'six columns'),

		html.Div(

			id = 'upload-container',
			children = [

			html.H3('Upload Personal Data (.zip)'),

			dcc.Upload(
	            id='upload-data',
	            children=html.Div([
	                'Drag and Drop or ',
	                html.A('Select Files')
	            ], style = {'font-weight':'bold', 'font-size': 20}),
	            style={
	                'width': '100%',
	                'height': '60px',
	                'lineHeight': '60px',
	                'borderWidth': '1px',
	                'borderStyle': 'dashed',
	                'borderRadius': '5px',
	                'textAlign': 'center',
	            },
	            multiple=False),

			# FilesUpload(
		 #        id='upload-files',
		 #        label = 'tmp1',
		 #        uploadUrl=upload_url2,
			#     ),

			html.Label(id = 'upload-log', children = 'STREAM Results (.zip): No Upload', style = {'font-weight':'bold'}),

			# html.Hr(),

			# html.Button(id = 'visualize-data', children = 'Visualize STREAM Results', n_clicks = 0),

			], className = 'six columns'),

		], className = 'row'),

	# html.H3('Choose Precomputed Data Set'),

	# dcc.Dropdown(
	# 	id = 'precomp-dataset',
	#     options=[
	#         {'label': 'Nestorowa, S. et al. 2016', 'value': 'Nestorowa'},
	#     ],
	#     value = 'Nestorowa'
	# ),

	# html.Label(id = 'title', children = ''),
	# html.Label(id = 'description', children = ''),
	# html.Label(id = 'startingnode', children = ''),
	# html.Label(id = 'commandline', children = ''),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Trajectories'),

	# html.Button(id = 'graph-button2', children = '(+) Show', n_clicks = 0),

	html.Div(

		id = 'graph-container2',
		children = [

		html.Div(

			id = '3d-scatter-container',
			children = [

				html.H4('3D Scatter Plot'),
				dcc.Graph(id='3d-scatter2', animate=False),

				# html.Br(),

				# html.Label('Select Starting Branch', style = {'font-weight':'bold', 'padding-right':'10px'}),
				# dcc.Dropdown(
				# 		id = 'root2',
				# 	    options=[
				# 	        {'label': 'S0', 'value': 'S0'},
				# 	    ],
				# 	    value='S0'
				# 	),

				# html.H4('2D Subway Map'),
				# dcc.Graph(id='2d-subway2', animate=False),

			], className = 'six columns'),

		html.Div(

			id = '2d-subway-container',
			children = [

				html.H4('Flat Tree Plot'),
				dcc.Graph(id='flat-tree-scatter2', animate=False),

				# html.Br(),
				# html.Br(),

				# html.H4('Stream Plot'),
				# html.Img(id = 'rainbow-plot2', src = None, width = '70%', style = {'align':'middle'}),

			], className = 'six columns'),

		], className = 'row'),

	html.Hr(),

	html.Label('Select Starting Node', style = {'font-weight':'bold', 'padding-right':'10px'}),
	dcc.Dropdown(
			id = 'root2',
		    options=[
		        {'label': 'S5', 'value': 'S5'},
		    ],
		    value='S5'
		),

	html.Div(

		id = 'graph-container2',
		children = [

		html.Div(

			id = '3d-scatter-container',
			children = [

				# html.H4('3D Scatter Plot'),
				# dcc.Graph(id='3d-scatter2', animate=False),

				# html.Br(),

				# html.Label('Select Starting Branch', style = {'font-weight':'bold', 'padding-right':'10px'}),
				# dcc.Dropdown(
				# 		id = 'root2',
				# 	    options=[
				# 	        {'label': 'S0', 'value': 'S0'},
				# 	    ],
				# 	    value='S0'
				# 	),

				html.H4('2D Subway Map'),
				dcc.Graph(id='2d-subway2', animate=False),

			], className = 'six columns'),

		html.Div(

			id = '2d-subway-container',
			children = [

				# html.H4('Flat Tree Plot'),
				# dcc.Graph(id='flat-tree-scatter2', animate=False),

				# html.Br(),
				# html.Br(),

				html.H4('Stream Plot'),
				html.Img(id = 'rainbow-plot2', src = None, width = '90%', style = {'align':'middle'}),

			], className = 'six columns'),

		], className = 'row'),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Genes of Interest'),

	html.Button(id = 'sg-plot-button2', children = '(+) Show', n_clicks = 0),

	html.Div(

		id = 'sg-plot-container2',
		children = [

		html.Div([

			html.Br(),

			html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
			dcc.Dropdown(
					id = 'sg-gene2',
				    options=[
				        {'label': 'Choose gene!', 'value': 'False'}
				    ],
				    value = 'False'
				),

			html.Br(),

			]),

		html.Div([

			html.Div([

				html.H4('2D Subway Plot'),
				dcc.Graph(id='2d-subway-sg2', animate=False)

				], className = 'six columns'),


			html.Div([

				html.H4('Stream Plot'),
				html.Img(id = 'sg-plot2', src = None, width = '90%', style = {'align':'middle'}),

				], className = 'six columns'),

			], className = 'row'),

		]),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Diverging Genes'),

	html.Button(id = 'discovery-plot-button2', children = '(+) Show', n_clicks = 0),

	html.Div(
		id = 'discovery-container2',
		children = [

		html.Br(),

		html.Div(

			id = 'discovery-plot-container2',
			children = [

			html.Div([

				html.Label('Branches for Diverging Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Dropdown(
						id = 'de-branches2',
					    options=[
					        {'label': 'Choose branch!', 'value': 'False'}
					    ],
					    value = 'False'
					),

		        html.Br(),

		        html.Label('Relatively Highly Expressed On:', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.RadioItems(
			    	id = 'de-direction2',
			        options=[
			            {'label': 'Choose branch pair above', 'value': 'False'}
			        ]),

		        html.Br(),

				html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Slider(
			        id='de-slider2',
			        min=0,
			        max=50,
			        value=10,
			        step=1
		        ),

		        html.Br(),

				html.Div(id = 'discovery-table2', style = {'font-family': 'courier', 'align':'center'}),

				], className = 'five columns'),


			html.Div([

				html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Dropdown(
						id = 'discovery-gene2',
					    options=[
					        {'label': 'Choose gene!', 'value': 'False'}
					    ],
					    value = 'False'
					),

				html.H4('2D Subway Map'),
				dcc.Graph(id='2d-subway-discovery2', animate=False),

				html.H4('Stream Plot'),
				html.Img(id = 'discovery-plot2', src = None, width = '90%', style = {'align':'middle'}),

				], className = 'seven columns'),

			], className = 'row'),

		]),

	html.Hr(),

	html.H3('Visualize Transition Genes'),

	html.Button(id = 'correlation-plot-button2', children = '(+) Show', n_clicks = 0),

	html.Div(
		id = 'correlation-container2',
		children = [

		html.Br(),

		html.Div(

			id = 'correlation-plot-container2',
			children = [

			html.Div([

				html.Label('Branch for Transition Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Dropdown(
						id = 'corr-branches2',
					    options=[
					        {'label': 'Choose branch!', 'value': 'False'}
					    ],
					    value = 'False'
					),

		        html.Br(),

				html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Slider(
			        id='corr-slider2',
			        min=0,
			        max=50,
			        value=10,
			        step=1
		        ),

		        html.Br(),

				html.Div(id = 'correlation-table2', style = {'font-family': 'courier', 'align':'center'}),

				], className = 'five columns'),


			html.Div([

				html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Dropdown(
						id = 'correlation-gene2',
					    options=[
					        {'label': 'Choose gene!', 'value': 'False'}
					    ],
					    value = 'False'
					),

				html.H4('2D Subway Map'),
				dcc.Graph(id='2d-subway-correlation2', animate=False),

				html.H4('Stream Plot'),
				html.Img(id = 'correlation-plot2', src = None, width = '90%', style = {'align':'middle'}),

				], className = 'seven columns'),

			], className = 'row'),

		]),

		html.Hr(),

		html.H3('Visualize Leaf Genes'),

		html.Button(id = 'leaf-plot-button2', children = '(+) Show', n_clicks = 0),

		html.Div(
			id = 'leaf-container2',
			children = [

			html.Br(),

			html.Div(

				id = 'leaf-plot-container2',
				children = [

				html.Div([

					html.Label('Branch for Transition Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Dropdown(
							id = 'leaf-branches2',
						    options=[
						        {'label': 'Choose branch!', 'value': 'False'}
						    ],
						    value = 'False'
						),

			        html.Br(),

					html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Slider(
				        id='leaf-slider2',
				        min=0,
				        max=50,
				        value=10,
				        step=1
			        ),

			        html.Br(),

					html.Div(id = 'leaf-table2', style = {'font-family': 'courier', 'align':'center'}),

					], className = 'five columns'),


				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'leaf-gene2',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					html.H4('2D Subway Map'),
					dcc.Graph(id='2d-subway-leaf2', animate=False),

					html.H4('Stream Plot'),
					html.Img(id = 'leaf-plot2', src = None, width = '90%', style = {'align':'middle'}),

					], className = 'seven columns'),

				], className = 'row'),

		]),

	html.Div(id = 'buffer1', style = {'align':'none'}),
	html.Div(id = 'buffer2', style = {'align':'none'}),
	html.Div(id = 'buffer3', style = {'align':'none'}),
	html.Div(id = 'buffer4', style = {'align':'none'}),
	html.Div(id = 'buffer5', style = {'align':'none'}),
	html.Div(id = 'buffer6', style = {'align':'none'}),
	html.Div(id = 'buffer7', style = {'align':'none'}),
	html.Div(id = 'buffer8', style = {'align':'none'}),
	html.Div(id = 'buffer9', style = {'align':'none'}),
	html.Div(id = 'buffer10', style = {'align':'none'})

	])




app.layout = html.Div([

	dcc.Location(id='url', refresh=False),

	dcc.Interval(id='common-interval', interval=5000),

	dcc.Interval(id='common-interval-1', interval=2000000000),
	dcc.Interval(id='common-interval-2', interval=2000000000),
	dcc.Interval(id='common-interval-3', interval=2000000000),
	dcc.Interval(id='common-interval-4', interval=2000000000),
	dcc.Interval(id='common-interval-5', interval=2000000000),

	html.Div(id = 'custom-loading-states-1',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-2',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-3',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-4',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-5',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Img(src='data:image/png;base64,{}'.format(stream_logo_image), width = '50%'),
	html.H2('Single-cell Trajectory Reconstruction Exploration And Mapping'),

	html.Hr(),

	html.Div([

		html.Div([

			html.H3(id = 'buffer1', children = 'Step 1: Input Files'),

			], className = 'six columns'),

		# html.Div([

		# 	html.H3(id = 'buffer2', children ='Basic Parameters'),

		# 	], className = 'six columns'),

		], className = 'row'),

	html.Div([

		# Input files
		html.Div([

			# html.H3(id = 'buffer5', children = 'Personal Files'),

			html.Div([

				html.Div([

					html.H3(id = 'buffer5', children = 'Personal Files'),

					FilesUpload(
						        id='required-files',
						        label = 'tmp',
						        uploadUrl=upload_url1,
							    ),

					html.Label(id = 'max-cells', children = 'IMPORTANT: Maximum of 2500 Cells', style = {'font-weight':'bold'}),

					html.Br(),
					html.Br(),

					html.Label(id = 'matrix-update', children = 'Data Matrix: No Upload (Required)', style = {'font-weight':'bold'}),
					html.Label(id = 'cl-update', children = 'Cell Labels File: No Upload (Optional)', style = {'font-weight':'bold'}),
					html.Label(id = 'clc-update', children = 'Cell Label Colors File: No Upload (Optional)', style = {'font-weight':'bold'}),

					], className = 'six columns'),

				html.Div([

					html.H3(id = 'buffer5', children = 'Example Files'),
					html.Button(id = 'load_example_data', children = 'Load Example Data', n_clicks = 0),

					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),

					html.H4(id = 'ready-to-compute', children = 'Ready for Step 2: No'),

					], className = 'six columns')

				], className = 'row'),

			# html.Hr(),

			# html.Label(id = 'matrix-upload', children = 'Data Matrix: None', style = {'font-weight':'bold'}),
			# html.Label(id = 'cl-upload', children = 'Cell Labels File: None', style = {'font-weight':'bold'}),
			# html.Label(id = 'clc-upload', children = 'Cell Label Colors File: None', style = {'font-weight':'bold'}),

			# html.Label(id = 'matrix-update', children = 'Data Matrix: No Upload (Required)', style = {'font-weight':'bold'}),
			# html.Label(id = 'cl-update', children = 'Cell Labels File: No Upload (Optional)', style = {'font-weight':'bold'}),
			# html.Label(id = 'clc-update', children = 'Cell Label Colors File: No Upload (Optional)', style = {'font-weight':'bold'}),

			# html.Br(),

			# html.H6(id = 'ready-to-compute', children = 'Ready for Step 2: No')

			# html.Hr(),

			# html.H3(id = 'buffer5', children = 'Example Files'),

			# html.Button(id = 'load_example_data', children = 'Load Example Data', n_clicks = 0),

			], className = 'six columns', style = {'border-style':'solid','border-width':'2px', 'border-color':'#DCDCDC','border-radius':'10px','border-spacing':'15px','padding':'10px','padding-bottom':'3.8em'}),

		# Input Parameters
		html.Div([

			html.H3(id = 'buffer2', children ='Basic Parameters'),

			html.Div([

				html.Div([

					html.Label('Perform Log2 Transformation', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'log2',
				        options=[
				            {'label': 'Yes', 'value': 'True'},
				            {'label': 'No', 'value': 'False'}
				        ],
				        value = 'False',
				        labelStyle={'display': 'inline-block'}),

					html.Label('Normalize Data on Library Size', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'norm',
				        options=[
				            {'label': 'Yes', 'value': 'True'},
				            {'label': 'No', 'value': 'False'}
				        ],
				        value = 'False',
				        labelStyle={'display': 'inline-block'}),

					html.Label('ATAC-seq Data', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'atac',
				        options=[
				            {'label': 'Yes', 'value': 'True'},
				            {'label': 'No', 'value': 'False'}
				        ],
				        value = 'False',
				        labelStyle={'display': 'inline-block'}),

					html.Label('Feature Selection', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'select',
				        options=[
				            {'label': 'LOESS', 'value': 'LOESS'},
				            {'label': 'PCA', 'value': 'PCA'},
				            {'label': 'All', 'value': 'all'}
				        ],
				        value = 'LOESS',
				        labelStyle={'display': 'inline-block'}),

					], className = 'six columns'),


				html.Div([

					html.Label('LOESS Fraction', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Input(id = 'loess_frac', value = 0.1),

					html.Label('LLE Neighbours', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Input(id = 'lle-nbs', value = 0.1),

					html.Label('LLE Components', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Input(id = 'lle-dr', value = 3),

					], className = 'six columns'),

				], className = 'row'),

				html.Hr(),

				html.Div([

					html.H3('Advanced Parameters'),

					html.Button(children = '(+) Show', id = 'advanced-params-button', n_clicks = 0, style = {'margin-bottom':'0.5cm'}),

					html.Div(id = 'advanced-params-container', children = [

						html.Div([

							html.Div([

								html.Label('Number of PCs', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'pca_n_PC', value = 15),

								html.Label('Keep First PC', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'pca_first_PC',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								# html.Label('Feature Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
								# dcc.Input(id = 'feature_genes', value = None),

								html.Label('Clustering Method', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
									id = 'clustering',
									options=[
								        {'label': 'affinity propagation', 'value': 'ap'},
							            {'label': 'k-means', 'value': 'kmeans'},
							            {'label': 'spectral clustering', 'value': 'sc'}
									],
									value = 'kmeans'),

								html.Label('Number of Clusters', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'n_clusters', value = 10),

								html.Label('Damping Factor', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'damping', value = 0.75),

								], className = 'three columns'),

							html.Div([

								html.Label('EPG Nodes', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_n_nodes', value = 50),

								html.Label('EPG Lambda', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_lambda', value = 0.02),

								html.Label('EPG Mu', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_mu', value = 0.1),

								html.Label('EPG Trimming Radius', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_trimmingradius', value = 1000000),

								# html.Label('EPG Final Energy', style = {'font-weight':'bold', 'padding-right':'10px'}),
								# dcc.RadioItems(
							    # 	id = 'EPG_finalenergy',
							    #     options=[
								#         {'label': 'Penalized', 'value': 'Penalized'},
							    #         {'label': 'Base', 'value': 'Base'},
							    #     ],
							    #     value = 'Penalized'),

								html.Label('EPG Alpha', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_alpha', value = 0.02),

                                html.Label('Disable EPG Finetune', style = {'font-weight':'bold', 'padding-right':'10px'}),
                                dcc.RadioItems(
							    	id = 'disable_EPG_optimize',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),


								], className = 'three columns'),

							html.Div([

								html.Label('EPG Collapse', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_collapse',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								html.Label('EPG Collapse Mode', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Dropdown(
							    	id = 'EPG_collapse_mode',
							        options=[
								        {'label': 'Point Number', 'value': 'PointNumber'},
							            {'label': 'Point Number Extrema', 'value': 'PointNumber_Extrema'},
							            {'label': 'Point Number Leaves', 'value': 'PointNumber_Leaves'},
							            {'label': 'Edges Number', 'value': 'EdgesNumber'},
							            {'label': 'Edges Length', 'value': 'EdgesLength'},
							        ],
							        value = 'PointNumber'),

								html.Label('EPG Collapse Parameter', style = {'font-weight':'bold', 'padding-right':'10px'}),
                                dcc.Input(id = 'EPG_collapse_par', value = 5),

								], className = 'three columns'),

							html.Div([

								html.Label('EPG Shift', style = {'font-weight':'bold', 'padding-right':'10px'}),
                                dcc.Dropdown(
							    	id = 'EPG_shift',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False'),

								html.Label('EPG Shift Mode', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_shift_mode',
							        options=[
								        {'label': 'Node Density', 'value': 'NodeDensity'},
							            {'label': 'Node Points', 'value': 'NodePoints'},
							        ],
							        value = 'NodeDensity'),

								html.Label('EPG Shift DR', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_shift_DR', value = 0.05),

								html.Label('EPG Max Shift', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_shift_maxshift', value = 5),

								html.Label('Disable EPG Extend', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'disable_EPG_ext',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								html.Label('EPG Extend Mode', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Dropdown(
							    	id = 'EPG_ext_mode',
							        options=[
								        {'label': 'Quant Dists', 'value': 'QuantDists'},
							            {'label': 'Quant Centroid', 'value': 'QuantCentroid'},
							            {'label': 'Weighted Centroid', 'value': 'WeightedCentroid'},
							        ],
							        value = 'QuantDists'),

								html.Label('EPG Extend Parameter', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_ext_par', value = 0.5),

                                # html.Label('Disable EPG Finetune', style = {'font-weight':'bold', 'padding-right':'10px'}),
                                # dcc.RadioItems(
							    # 	id = 'disable_EPG_optimize',
							    #     options=[
							    #         {'label': 'Yes', 'value': 'True'},
							    #         {'label': 'No', 'value': 'False'}
							    #     ],
							    #     value = 'False',
							    #     labelStyle={'display': 'inline-block'}),

								], className = 'three columns'),

							], className = 'row')

						]),

					]),

			], className = 'six columns', style = {'border-style':'solid','border-width':'2px', 'border-color':'#DCDCDC','border-radius':'10px','border-spacing':'15px','padding':'10px'})

		], className = 'row'),

	html.Hr(),

	html.H3(id = 'buffer3', children = 'Step 2: Compute Trajectories (~5 Minutes)'),

	html.Button('Compute', id='compute-button'),

	# html.Br(),

	html.Div(id = 'compute-container',
		children = [

		html.Br(),
		html.Br(),

		# html.Button(id = 'graph-button', children = '(-) Hide Graphs', n_clicks = 0),

		html.Div(

			id = 'graph-container1',
			children = [

			html.Div(

				id = '3d-scatter-container',
				children = [

					html.H3('3D Scatter Plot'),
					dcc.Graph(id='3d-scatter', animate=False),

					# html.Label('Select Starting Branch', style = {'font-weight':'bold', 'padding-right':'10px'}),
					# dcc.Dropdown(
					# 		id = 'root',
					# 	    options=[
					# 	        {'label': 'S0', 'value': 'S0'},
					# 	    ],
					# 	    value='S0'
					# 	),

					# html.H3('2D Subway Map'),
					# dcc.Graph(id='2d-subway', animate=False),

				], className = 'six columns'),

			html.Div(

				id = '2d-subway-container',
				children = [

					html.H3('Flat Tree Plot'),
					dcc.Graph(id='flat-tree-scatter', animate=False),

					# html.Br(),
					# html.Br(),

					# html.H3('Stream Plot'),
					# html.Img(id = 'rainbow-plot', src = None, width = '70%', style = {'align':'middle'}),

				], className = 'six columns'),

			], className = 'row'),

		html.Hr(),

		html.Label('Select Starting Node', style = {'font-weight':'bold', 'padding-right':'10px'}),
		dcc.Dropdown(
				id = 'root',
			    options=[
			        {'label': 'S5', 'value': 'S5'},
			    ],
			    value='S5'
			),

		html.Div(

			id = 'graph-container2',
			children = [

			html.Div(

				id = '3d-scatter-container',
				children = [

					# html.H3('3D Scatter Plot'),
					# dcc.Graph(id='3d-scatter', animate=False),

					# html.Label('Select Starting Branch', style = {'font-weight':'bold', 'padding-right':'10px'}),
					# dcc.Dropdown(
					# 		id = 'root',
					# 	    options=[
					# 	        {'label': 'S0', 'value': 'S0'},
					# 	    ],
					# 	    value='S0'
					# 	),

					html.H3('2D Subway Map'),
					dcc.Graph(id='2d-subway', animate=False),

				], className = 'six columns'),

			html.Div(

				id = '2d-subway-container',
				children = [

					# html.H3('Flat Tree Plot'),
					# dcc.Graph(id='flat-tree-scatter', animate=False),

					# html.Br(),
					# html.Br(),

					html.H3('Stream Plot'),
					html.Img(id = 'rainbow-plot', src = None, width = '90%', style = {'align':'middle'}),



				], className = 'six columns'),

			], className = 'row'),

		html.Br(),
		html.Br(),

		]),

	html.Hr(),

	html.Div([

		html.H3('Step 3A: Visualize Genes of Interest (~1 Minute)'),
		html.Button(id = 'sg-button', children = 'Get Started!', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'sg-container',
			children = [

			html.Button(id = 'sg-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'sg-plot-container',
				children = [

				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'sg-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					html.Br(),
					# html.Br(),

					html.Button(id = 'sg-compute', children = 'Visualize Gene', n_clicks = 0),

					]),

				html.Div([

					html.Div([

						dcc.Graph(id='2d-subway-sg', animate=False)

						], className = 'six columns'),


					html.Div([

						html.Img(id = 'sg-plot', src = None, width = '90%', style = {'align':'middle'}),

						], className = 'six columns'),

					], className = 'row'),

				]),

			])

		]),

	html.Hr(),

	html.Div([

		html.H3(id = 'buffer4', children = 'Step 3B: Identify Diverging Genes (~10 Minutes)'),
		html.Button(id = 'discovery-button', children = 'Compute', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'discovery-container',
			children = [

			html.Button(id = 'discovery-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'discovery-plot-container',
				children = [

				html.Div([

					html.Label('Branches for Diverging Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Dropdown(
							id = 'de-branches',
						    options=[
						        {'label': 'Choose branch!', 'value': 'False'}
						    ],
						    value = 'False'
						),

			        html.Br(),

			        html.Label('Relatively Highly Expressed On:', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.RadioItems(
				    	id = 'de-direction',
				        options=[
				            {'label': 'Choose branch pair above', 'value': 'False'}
				        ]),

			        html.Br(),

					html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Slider(
				        id='de-slider',
				        min=0,
				        max=50,
				        value=10,
				        step=1
			        ),

			        html.Br(),

					html.Div(id = 'discovery-table', style = {'font-family': 'courier', 'align':'center'}),

					], className = 'five columns'),


				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'discovery-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					dcc.Graph(id='2d-subway-discovery', animate=False),

					html.Img(id = 'discovery-plot', src = None, width = '90%', style = {'align':'middle'}),

					], className = 'seven columns'),

				], className = 'row'),

			])

		]),

	html.Hr(),

	html.Div([

		html.H3(id = 'buffer6', children = 'Step 3C: Identify Transition Genes (~10 Minutes)'),
		html.Button(id = 'correlation-button', children = 'Compute', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'correlation-container',
			children = [

			html.Button(id = 'correlation-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'correlation-plot-container',
				children = [

				html.Div([

					html.Label('Branch for Transition Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Dropdown(
							id = 'corr-branches',
						    options=[
						        {'label': 'Choose branch!', 'value': 'False'}
						    ],
						    value = 'False'
						),

			        html.Br(),

					html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Slider(
				        id='corr-slider',
				        min=0,
				        max=50,
				        value=10,
				        step=1
			        ),

			        html.Br(),

					html.Div(id = 'correlation-table', style = {'font-family': 'courier', 'align':'center'}),

					], className = 'five columns'),


				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'correlation-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					dcc.Graph(id='2d-subway-correlation', animate=False),

					html.Img(id = 'correlation-plot', src = None, width = '90%', style = {'align':'middle'}),

					], className = 'seven columns'),

				], className = 'row'),

			])

		]),

	html.Hr(),

	# LOOK HERE FOR LEAF!!!!!

	html.Div([

		html.H3(id = 'buffer10', children = 'Step 3D: Identify Leaf Genes (~10 Minutes)'),
		html.Button(id = 'leaf-button', children = 'Compute', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'leaf-container',
			children = [

			html.Button(id = 'leaf-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'leaf-plot-container',
				children = [

				html.Div([

					html.Label('Branch for Leaf Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Dropdown(
							id = 'leaf-branches',
						    options=[
						        {'label': 'Choose branch!', 'value': 'False'}
						    ],
						    value = 'False'
						),

			        html.Br(),

					html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Slider(
				        id='leaf-slider',
				        min=0,
				        max=50,
				        value=10,
				        step=1
			        ),

			        html.Br(),

					html.Div(id = 'leaf-table', style = {'font-family': 'courier', 'align':'center'}),

					], className = 'five columns'),


				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'leaf-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					dcc.Graph(id='2d-subway-leaf', animate=False),

					html.Img(id = 'leaf-plot', src = None, width = '90%', style = {'align':'middle'}),

					], className = 'seven columns'),

				], className = 'row'),

			])

		]),

	html.Hr(),

	html.Div([

		html.H3(id = 'buffer5', children = 'Step 4: Download Current Analysis'),

		html.Div(
			id = 'download-container',
			children = [

			html.Div([

				html.Label('Experiment Title', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Input(id = 'title-input', value = ''),

				html.Label('Experiment Description', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Input(id = 'description-input', value = ''),

				]),

			html.Br(),

			html.Div([

				html.A(
					html.Button('Download Files'),
					id='download-total',
					download = "stream-outputs.zip",
					href="",
					target="_blank",
					n_clicks = 0,
					style = {'font-weight':'bold', 'font-size':'100%', 'text-align':'center'}
					),

				]),

			])

		]),

	html.Hr(),

	# html.Div([

	# 	html.Div([

	# 		html.Img(src='data:image/png;base64,{}'.format(hms_logo_image), width = '25%'),

	# 		], className = 'four columns'),

	# 	html.Div([

	# 		html.Img(src='data:image/png;base64,{}'.format(mitbe_logo_image), width = '40%'),

	# 		html.H3([html.Center([html.A('Pinello Lab', href='http://www.pinellolab.org/')])]),

	# 		html.Label('Credits: H Chen, L Albergante, JY Hsu, CA Lareau, GL Bosco, J Guan, S Zhou, AN Gorban, DE Bauer, MJ Aryee, DM Langenau, A Zinovyev, JD Buenrostro, GC Yuan, L Pinello', style = {'font-weight':'bold'})

	# 		], className = 'four columns'),

	# 	html.Div([

	# 		html.Img(src='data:image/png;base64,{}'.format(mgh_logo_image), width = '26%'),

	# 		], className = 'four columns'),
	# 	], className = 'row', style = {'text-align':'center'})

	])

# Precomputed folders
@app2.callback(
    Output('precomp-dataset', 'options'),
    [Input('upload-log','children'),
    Input('url2', 'pathname')])

def num_clicks_compute(n_clicks, pathname):

	unique_id = pathname.strip('\n').split('/')[-1]

	precomputed_json_list = glob.glob('/stream_web/precomputed/PRECOMPUTED*/*json')
	userupload_json_list = glob.glob('/stream_web/precomputed/USER_UPLOAD_%s/*json' % (unique_id))

	json_list = precomputed_json_list + userupload_json_list

	dataset_list = []
	for json_entry in json_list:
		data = json.load(open(json_entry))
		dataset_list.append([data['title'], json_entry.split('/')[-2]])

	return [{'label': i[0], 'value': i[1]} for i in dataset_list]

@app2.callback(
    Output('precomp-dataset', 'value'),
    [Input('precomp-dataset', 'options'),
    Input('url2', 'pathname')])

def num_clicks_compute(options, pathname):

	unique_id = pathname.strip('\n').split('/')[-1]

	precomputed_json_list = glob.glob('/stream_web/precomputed/PRECOMPUTED*/*json')
	userupload_json_list = glob.glob('/stream_web/precomputed/USER_UPLOAD_%s/*json' % (unique_id))

	json_list = precomputed_json_list + userupload_json_list

	dataset_list = []
	for json_entry in json_list:
		data = json.load(open(json_entry))
		dataset_list.append([data['title'], json_entry.split('/')[-2]])

	# print(dataset_list)

	return dataset_list[-1][1]

@app2.callback(
    Output('title', 'children'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	json_entry = glob.glob('/stream_web/precomputed/%s/*.json' % (dataset))
	data = json.load(open(json_entry[0]))

	return 'Title: ' + data['title']

@app2.callback(
    Output('description', 'children'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	json_entry = glob.glob('/stream_web/precomputed/%s/*.json' % (dataset))
	data = json.load(open(json_entry[0]))

	return 'Description: ' + data['description']

@app2.callback(
    Output('startingnode', 'children'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	json_entry = glob.glob('/stream_web/precomputed/%s/*.json' % (dataset))
	data = json.load(open(json_entry[0]))

	return 'Starting Node: ' + data['starting_node']

@app2.callback(
    Output('commandline', 'children'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	json_entry = glob.glob('/stream_web/precomputed/%s/*.json' % (dataset))
	data = json.load(open(json_entry[0]))

	return 'Command Used: ' + data['command_used']

# @app2.callback(
# 	Output('zip-update', 'children'),
# 	[Input('url2', 'pathname')],
# 	events=[Event('common-interval2', 'interval')])

# def update_matrix_log(pathname):

# 	if pathname:

# 		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
# 		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

# 		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
# 			json_string = f.readline().strip()
# 			param_dict = json.loads(json_string)

# 		return param_dict['zip-update']

# @app2.callback(
# 	Output('visualize-data', 'children'),
# 	[Input('zip-update', 'children'),
# 	Input('url2', 'pathname')])

# def update_visualize_button(zip_update, pathname):

# 	if 'Successfully' in zip_update:
# 		return 'Visualize STREAM Results'
# 	else:
# 		return 'Upload Step Incomplete'

# @app2.callback(
#     Output('visualize-data', 'disabled'),
#     [Input('zip-update', 'children'),
# 	Input('url2', 'pathname')])

# def num_clicks_compute(zip_update, pathname):

# 	if 'Successfully' in zip_update:
# 		return False
# 	else:
# 		return True


#### INPUT FILES ######
@app.callback(
    Output('required-files', 'label'),
    [Input('url', 'pathname')])

def update_input_files(pathname):

	file_names = ['Data Matrix', 'Cell Labels', 'Cell Label Colors']

	return ','.join(file_names)

# @app2.callback(
#     Output('upload-files', 'label'),
#     [Input('url2', 'pathname')])

# def update_input_files(pathname):

# 	file_names = ['STREAM Results .zip']

# 	return ','.join(file_names)

#### Load exmample data
@app.callback(
    Output('select', 'value'),
    [Input('url', 'pathname'),
    Input('load_example_data', 'n_clicks'),
    Input('atac', 'value')])

def update_select_features(pathname, n_clicks, atac):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if n_clicks > 0:
			return 'all'

		elif str(atac) == 'True':
			return 'PCA'

		else:
			return 'LOESS'

	else:
		return 'LOESS'

@app.callback(
    Output('load_example_data', 'children'),
    [Input('url', 'pathname'),
    Input('load_example_data', 'n_clicks')])

def update_input_files(pathname, n_clicks):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if n_clicks > 0:
			sb.call('cp ./exampleDataset/data_guoji.tsv %s/Data_Matrix_data_guoji.tsv' % (UPLOADS_FOLDER), shell = True)
			sb.call('cp ./exampleDataset/cell_label.tsv %s/Cell_Labels_cell_label.tsv' % (UPLOADS_FOLDER), shell = True)
			sb.call('cp ./exampleDataset/cell_label_color.tsv %s/Cell_Label_Colors_cell_label_color.tsv' % (UPLOADS_FOLDER), shell = True)
			return 'Example Data Loaded'

		else:
			return 'Load Example Data'

	else:
		return 'Load Example Data'

@app.callback(
    Output('buffer5', 'style'),
    [Input('url', 'pathname'),
    Input('load_example_data', 'n_clicks')])

def update_input_files(pathname, n_clicks):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > 0:
			param_dict['compute-update'] = 'Compute'
			param_dict['compute-disable'] = False

			with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
				new_json_string = json.dumps(param_dict)
				f.write(new_json_string + '\n')

	return {'display': 'block'}


# Advanced parameters
@app.callback(
	Output('advanced-params-button', 'children'),
	[Input('advanced-params-button', 'n_clicks')])

def update_advanced_params_button(n_clicks):

	if n_clicks%2 == 0:
		return '(+) Show'
	else:
		return '(-) Hide'

@app.callback(
	Output('advanced-params-container', 'style'),
	[Input('advanced-params-button', 'n_clicks')])

def update_advanced_params_container(n_clicks):

	if n_clicks%2 == 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

################################# COMPUTE TRAJECTORIES #################################
@app.callback(
    Output('compute-container', 'style'),
    [Input('3d-scatter', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
	Output('matrix-update', 'children'),
	[Input('url', 'pathname')],
	events=[Event('common-interval', 'interval')])

def update_matrix_log(pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['matrix-update']

@app.callback(
	Output('cl-update', 'children'),
	[Input('url', 'pathname')],
	events=[Event('common-interval', 'interval')])

def update_cl_log(pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['cl-update']

@app.callback(
	Output('clc-update', 'children'),
	[Input('url', 'pathname')],
	events=[Event('common-interval', 'interval')])

def update_clc_log(pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['clc-update']

@app.callback(
    Output('ready-to-compute', 'children'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-disable']:
			return 'Ready for Step 2: No'
		else:
			return 'Ready for Step 2: Yes'

@app.callback(
    Output('compute-button', 'disabled'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['compute-disable']

@app.callback(
    Output('compute-button', 'children'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['compute-update']

# @app.callback(
# 	Output('graph-button', 'children'),
# 	[Input('graph-button', 'n_clicks')])

# def update_score_params_button(n_clicks):

# 	if n_clicks%2 != 0:
# 		return '(+) Show Graphs'
# 	else:
# 		return '(-) Hide Graphs'

# @app.callback(
# 	Output('graph-container', 'style'),
# 	[Input('graph-button', 'n_clicks')])

# def update_score_params_visual(n_clicks):

# 	if n_clicks%2 != 0:
# 		return {'display': 'none'}
# 	else:
# 		return {'display': 'block'}

@app.callback(
    Output('buffer1', 'style'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    state=[State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    # State('feature_genes', 'value'),
    State('clustering', 'value'),
    State('n_clusters', 'value'),
    State('damping', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    # State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    # State('EPG_beta', 'value'),
    State('EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('disable_EPG_optimize', 'value')])

def compute_trajectories(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,clustering,n_clusters,damping,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_alpha,EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,disable_EPG_optimize):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['compute-clicks']:

			matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			# cell_label_list = []
			# if len(cell_label) > 0:
			# 	if cell_label[0].endswith('.gz'):
			# 		with gzip.open(cell_label[0], 'r') as f:
			# 			for line in f:
			# 				cell_label_list.append(line.strip())
			# 	else:
			# 		with open(cell_label[0], 'r') as f:
			# 			for line in f:
			# 				cell_label_list.append(line.strip())

			# cell_label_colors_dict = {}
			# if len(cell_label_colors) > 0:
			# 	if cell_label_colors[0].endswith('.gz'):
			# 		with gzip.open(cell_label_colors[0], 'r') as f:
			# 			for line in f:
			# 				line = line.strip().split('\t')
			# 				cell_label_colors_dict[str(line[1])] = str(line[0])

			# 	else:
			# 		with open(cell_label_colors[0], 'r') as f:
			# 			for line in f:
			# 				line = line.strip().split('\t')
			# 				cell_label_colors_dict[str(line[1])] = str(line[0])

			# color_plot = []
			# if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
			# 	color_plot = [cell_label_colors_dict[x] for x in cell_label_list]

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--clustering':[clustering],'--n_clusters':[n_clusters],'--damping':[damping],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_alpha':[EPG_alpha],'--EPG_collapse':[EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par],'--disable_EPG_optimize':[disable_EPG_optimize]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			# if not param_dict['compute-run']:
			sb.call('stream --for_web ' + ' '.join(map(str, arguments_final)) + ' > %s/log1.txt' % (RESULTS_FOLDER), shell = True)

			with open(RESULTS_FOLDER + '/command_line_used.txt', 'w') as f:
				f.write('stream --for_web ' + ' '.join(map(str, arguments_final)))

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-1', 'style'),
	[Input('compute-button', 'n_clicks'),
	Input('compute-container', 'style'),
	Input('url', 'pathname')])

def update_container(n_clicks, segmentation_container, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton1']:

		return {'display': 'block'}

	elif not param_dict['checkpoint1']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app2.callback(
	Output('custom-loading-states-11', 'style'),
	[Input('precomp-dataset', 'value'),
	Input('rainbow-plot2', 'src'),
	Input('url2', 'pathname')],
	state = [State('root2', 'value')])

def update_container(dataset, stream_plot_src, pathname, root):

	rainbow_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot.png' % (dataset, root)
	rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read()).decode('ascii')

	if 'data:image/png;base64,{}'.format(rainbow_plot_image) == stream_plot_src:

		return {'display': 'none'}
		# return {'display': 'block'}
	else:
		return {'display': 'block'}

@app.callback(
	Output('common-interval-1', 'interval'),
	[Input('compute-button', 'n_clicks'),
	Input('compute-container', 'style'),
	Input('url', 'pathname')])

def update_container(n_clicks, segmentation_container, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton1']:

		return 10000

	elif not param_dict['checkpoint1']:

		return 10000

	else:

		return 2000000000

@app.callback(
    Output('3d-scatter', 'figure'),
    [Input('url', 'pathname')],
    state=[State('compute-button', 'n_clicks')],
    events=[Event('common-interval-1', 'interval')])

def compute_trajectories(pathname, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log1.txt'):


			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/log1.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				edges = RESULTS_FOLDER + '/edges.tsv'
				edge_list = []

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append([str(line[0]), str(line[1])])

				cell_label_list = []
				# if len(cell_label) > 0:
				# 	if cell_label[0].endswith('.gz'):
				# 		with gzip.open(cell_label[0], 'r') as f:
				# 			for line in f:
				# 				cell_label_list.append(line.strip())
				# 	else:
				# 		with open(cell_label[0], 'r') as f:
				# 			for line in f:
				# 				cell_label_list.append(line.strip())
				if len(cell_label) > 0:
					cell_label_df = pd.read_csv(cell_label[0],sep='\t',header=None,index_col=None,compression= 'gzip' if cell_label[0].split('.')[-1]=='gz' else None)
					cell_label_list = cell_label_df[0].tolist()

				cell_label_colors_dict = {}
				# if len(cell_label_colors) > 0:
				# 	if cell_label_colors[0].endswith('.gz'):
				# 		with gzip.open(cell_label_colors[0], 'r') as f:
				# 			for line in f:
				# 				line = line.strip().split('\t')
				# 				cell_label_colors_dict[str(line[1])] = str(line[0])

				# 	else:
				# 		with open(cell_label_colors[0], 'r') as f:
				# 			for line in f:
				# 				line = line.strip().split('\t')
				# 				cell_label_colors_dict[str(line[1])] = str(line[0])
				if len(cell_label_colors) > 0:
					cell_label_colors_df = pd.read_csv(cell_label_colors[0],sep='\t',header=None,dtype={0:np.str},compression= 'gzip' if cell_label_colors[0].split('.')[-1]=='gz' else None)
					cell_label_colors_dict = cell_label_colors_df.set_index(1)[0].to_dict()

				color_plot = 0
				if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
					color_plot = 1
				elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
					color_plot = 0.5

				param_dict['compute-clicks'] = n_clicks
				param_dict['checkbutton1'] += 1
				param_dict['checkpoint1'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				cell_coords = RESULTS_FOLDER + '/coord_cells.csv'
				coord_states = RESULTS_FOLDER + '/coord_states.csv'
				path_coords = glob.glob(RESULTS_FOLDER + '/coord_curve*csv')

				path_coords_reordered = []
				for e in edge_list:
					entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
					path_coords_reordered.append(entry[0])

				traces = []
				roots = []
				for path in path_coords_reordered:
					x_p = []
					y_p = []
					z_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = sorted([s1, s2])
					path_name = '-'.join(map(str, s_3))
					roots.append(s1)
					roots.append(s2)
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))
							z_p.append(float(line[2]))
						traces.append(

							go.Scatter3d(
									    x=x_p, y=y_p, z=z_p,
									    # text = [s1, s2],
									    mode = 'lines',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width=10
									    ),
									)

							)

				x = []
				y = []
				z = []
				c = []
				labels = []
				with open(cell_coords, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						c.append(str(line[1]))
						x.append(float(line[2]))
						y.append(float(line[3]))
						z.append(float(line[4]))
						try:
							labels.append(cell_label_colors_dict[str(line[1])])
						except:
							pass

				cell_types = {}
				if color_plot == 0:
					cell_types['Single Cells'] = [x, y, z, 'unlabeled', 'grey']
				elif color_plot == 0.5:
					for label, x_c, y_c, z_c, color in zip(labels, x, y, z, c):
						if label not in cell_types:
							cell_types[label] = [[],[],[],[],[]]
						cell_types[label][0].append(x_c)
						cell_types[label][1].append(y_c)
						cell_types[label][2].append(z_c)
						cell_types[label][3].append(label)
						cell_types[label][4].append('grey')
				else:
					for label, x_c, y_c, z_c, color in zip(labels, x, y, z, c):
						if label not in cell_types:
							cell_types[label] = [[],[],[],[],[]]
						cell_types[label][0].append(x_c)
						cell_types[label][1].append(y_c)
						cell_types[label][2].append(z_c)
						cell_types[label][3].append(label)
						cell_types[label][4].append(color)

				for label in cell_types:
					traces.append(
						go.Scatter3d(
									x=cell_types[label][0],
									y=cell_types[label][1],
									z=cell_types[label][2],
									mode='markers',
									opacity = 0.5,
									name = label,
									text = cell_types[label][3],
									marker = dict(
										size = 5,
										color = cell_types[label][4]
										)
								)
							)

				coord_states_list = {}
				with open(coord_states, 'r') as f:
					next(f)
					for line in f:
						line = line.strip('\n').split('\t')
						coord_states_list[line[0]] = [float(line[1]), float(line[2]), float(line[3])]

				annotations = []
				for coord_state in coord_states_list:
					annotations.append(
					dict(
				        showarrow = False,
				        x = coord_states_list[coord_state][0],
				        y = coord_states_list[coord_state][1],
				        z = coord_states_list[coord_state][2],
				        text = coord_state,
				        xanchor = "left",
				        xshift = 10,
				        opacity = 0.7
				      )
					)
					# traces.append(

					# 	go.Scatter3d(
					# 			    x=coord_states_list[coord_state][0], y=coord_states_list[coord_state][1], z=coord_states_list[coord_state][2],
					# 			    text = coord_state,
					# 			    mode = 'text+markers',
					# 			    textfont=dict(
					# 					size = 20
					# 				),
					# 			    # opacity = 0.7,
					# 			    name = coord_state,
					# 			    # line=dict(
					# 			    #     width=10
					# 			    # ),
					# 			)

					# 		)

				roots = sorted(list(set(roots)))

				df = pd.read_table(matrix[0])
				sg_genes = list(np.unique(df.iloc[:,0].values))
				param_dict['starting-nodes'] = roots
				param_dict['compute-run'] = True
				param_dict['sg-genes'] = sg_genes

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	# annotations = annotations,
        	dragmode = "turntable",
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            scene = dict(
                    xaxis = dict(showgrid = False, zeroline=True, title = 'Dim.1', ticks='', showticklabels=False),
                    yaxis = dict(showgrid = False, zeroline=True, title = 'Dim.2', ticks='', showticklabels=False),
                    zaxis = dict(showgrid = False, zeroline=True, title = 'Dim.3', ticks='', showticklabels=False))
        )
    }

@app2.callback(
    Output('3d-scatter2', 'figure'),
    [Input('precomp-dataset', 'value')])

def compute_trajectories(dataset):

	traces = []

	try:

		cell_label = glob.glob('/stream_web/precomputed/%s/cell_label.tsv.gz*' % dataset)
		cell_label_colors = glob.glob('/stream_web/precomputed/%s/cell_label_color.tsv.gz*' % dataset)

		edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
		edge_list = []

		with open(edges, 'r') as f:
			for line in f:
				line = line.strip().split('\t')
				edge_list.append([str(line[0]), str(line[1])])

		cell_label_list = []
		if len(cell_label) > 0:
			if cell_label[0].endswith('.gz'):
				with gzip.open(cell_label[0], 'r') as f:
					for line in f:
						cell_label_list.append(line.strip())
			else:
				with open(cell_label[0], 'r') as f:
					for line in f:
						cell_label_list.append(line.strip())

		cell_label_colors_dict = {}
		if len(cell_label_colors) > 0:
			if cell_label_colors[0].endswith('.gz'):
				with gzip.open(cell_label_colors[0], 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						cell_label_colors_dict[str(line[1])] = str(line[0])

			else:
				with open(cell_label_colors[0], 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						cell_label_colors_dict[str(line[1])] = str(line[0])

		# color_plot = 0
		# if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		# 	color_plot = 1
		# elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
		# 	color_plot = 0.5

		cell_coords = '/stream_web/precomputed/%s/stream_report/coord_cells.csv' % dataset
		coord_states = '/stream_web/precomputed/%s/stream_report/coord_states.csv' % dataset
		metadata = '/stream_web/precomputed/%s/stream_report/metadata.tsv' % dataset
		path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/coord_curve*csv' % dataset)

		path_coords_reordered = []
		for e in edge_list:
			entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
			path_coords_reordered.append(entry[0])

		roots = []
		for path in path_coords_reordered:
			x_p = []
			y_p = []
			z_p = []
			s1 = path.strip().split('_')[-2]
			s2 = path.strip().split('_')[-1].strip('.csv')
			s_3 = sorted([s1, s2])
			path_name = '-'.join(map(str, s_3))
			roots.append(s1)
			roots.append(s2)
			with open(path, 'r') as f:
				next(f)
				for line in f:
					line = line.strip().split('\t')
					x_p.append(float(line[0]))
					y_p.append(float(line[1]))
					z_p.append(float(line[2]))
				traces.append(

					go.Scatter3d(
							    x=x_p, y=y_p, z=z_p,
							    # text = [s1, s2],
							    mode = 'lines',
							    opacity = 0.7,
							    name = path_name,
							    line=dict(
							        width=10
							    ),
							)

					)

		color2cell = {}
		with open(metadata, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				color2cell[str(line[2])] = str(line[1])

		x = []
		y = []
		z = []
		c = []
		labels = []
		with open(cell_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[1]))
				x.append(float(line[2]))
				y.append(float(line[3]))
				z.append(float(line[4]))
				# try:
				labels.append(color2cell[str(line[1])])
				# except:
					# pass

		cell_types = {}
		# if color_plot == 0:
		# 	cell_types['Single Cells'] = [x, y, z, 'unlabeled', 'grey']
		# elif color_plot == 0.5:
		# 	for label, x_c, y_c, z_c, color in zip(labels, x, y, z, c):
		# 		if label not in cell_types:
		# 			cell_types[label] = [[],[],[],[],[]]
		# 		cell_types[label][0].append(x_c)
		# 		cell_types[label][1].append(y_c)
		# 		cell_types[label][2].append(z_c)
		# 		cell_types[label][3].append(label)
				# cell_types[label][4].append('grey')
		# else:
		for label, x_c, y_c, z_c, color in zip(labels, x, y, z, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(z_c)
			cell_types[label][3].append(label)
			cell_types[label][4].append(color)

		for label in cell_types:
			traces.append(
				go.Scatter3d(
							x=cell_types[label][0],
							y=cell_types[label][1],
							z=cell_types[label][2],
							mode='markers',
							opacity = 0.5,
							name = label,
							text = cell_types[label][3],
							marker = dict(
								size = 5,
								color = cell_types[label][4]
								)
						)
					)

		coord_states_list = {}
		with open(coord_states, 'r') as f:
			next(f)
			for line in f:
				line = line.strip('\n').split('\t')
				coord_states_list[line[0]] = [float(line[1]), float(line[2]), float(line[3])]

		annotations = []
		for coord_state in coord_states_list:
			annotations.append(
					dict(
				        showarrow = False,
				        x = coord_states_list[coord_state][0],
				        y = coord_states_list[coord_state][1],
				        z = coord_states_list[coord_state][2],
				        text = coord_state,
				        xanchor = "left",
				        xshift = 10,
				        opacity = 0.7
				      )
					)

			# traces.append(

			# 	go.Scatter3d(
			# 			    x=coord_states_list[coord_state][0], y=coord_states_list[coord_state][1], z=coord_states_list[coord_state][2],
			# 			    text = coord_state,
			# 			    mode = 'text+markers',
			# 			    textfont=dict(
			# 					size = 20
			# 				),
			# 			    # opacity = 0.7,
			# 			    name = coord_state,
			# 			    # line=dict(
			# 			    #     width=10
			# 			    # ),
			# 			)

			# 		)

	except:
		pass

	return {
        'data': traces,
        'layout': go.Layout(
        	# annotations = annotations,
        	dragmode = "turntable",
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            scene = dict(
                    xaxis = dict(showgrid = False, zeroline=True, title = 'Dim.1', ticks='', showticklabels=False),
                    yaxis = dict(showgrid = False, zeroline=True, title = 'Dim.2', ticks='', showticklabels=False),
                    zaxis = dict(showgrid = False, zeroline=True, title = 'Dim.3', ticks='', showticklabels=False))
        )
    }

@app.callback(
    Output('flat-tree-scatter', 'figure'),
    [Input('url', 'pathname'),
    Input('3d-scatter', 'figure')],
    state=[State('compute-button', 'n_clicks')],)
    # events=[Event('common-interval-1', 'interval')])

def compute_trajectories(pathname, threed_scatter, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log1.txt'):
			f = open(RESULTS_FOLDER + '/log1.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_label_list = []
				# if len(cell_label) > 0:
				# 	if cell_label[0].endswith('.gz'):
				# 		with gzip.open(cell_label[0], 'r') as f:
				# 			for line in f:
				# 				cell_label_list.append(line.strip())
				# 	else:
				# 		with open(cell_label[0], 'r') as f:
				# 			for line in f:
				# 				cell_label_list.append(line.strip())
				if len(cell_label) > 0:
					cell_label_df = pd.read_csv(cell_label[0],sep='\t',header=None,index_col=None,compression= 'gzip' if cell_label[0].split('.')[-1]=='gz' else None)
					cell_label_list = cell_label_df[0].tolist()

				cell_label_colors_dict = {}
				# if len(cell_label_colors) > 0:
				# 	if cell_label_colors[0].endswith('.gz'):
				# 		with gzip.open(cell_label_colors[0], 'r') as f:
				# 			for line in f:
				# 				line = line.strip().split('\t')
				# 				cell_label_colors_dict[str(line[1])] = str(line[0])

				# 	else:
				# 		with open(cell_label_colors[0], 'r') as f:
				# 			for line in f:
				# 				line = line.strip().split('\t')
				# 				cell_label_colors_dict[str(line[1])] = str(line[0])
				if len(cell_label_colors) > 0:
					cell_label_colors_df = pd.read_csv(cell_label_colors[0],sep='\t',header=None,dtype={0:np.str},compression= 'gzip' if cell_label_colors[0].split('.')[-1]=='gz' else None)
					cell_label_colors_dict = cell_label_colors_df.set_index(1)[0].to_dict()

				color_plot = 0
				if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
					color_plot = 1
				elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
					color_plot = 0.5

				cell_coords = RESULTS_FOLDER + '/flat_tree_coord_cells.csv'
				nodes = RESULTS_FOLDER + '/nodes.csv'
				edges = RESULTS_FOLDER + '/edges.tsv'

				node_list = {}
				edge_list = []

				with open(nodes, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						node_list[str(line[0])] = [float(line[1]), float(line[2])]

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append(sorted([str(line[0]), str(line[1])]))

				path_coords = {}
				path_coords_reordered = []
				for edge in edge_list:
					edge_name = '-'.join(map(str, edge))
					path_coords_reordered.append(edge_name)
					x_values = [node_list[edge[0]][0], node_list[edge[1]][0]]
					y_values = [node_list[edge[0]][1], node_list[edge[1]][1]]
					path_coords[edge_name] = [x_values, y_values]

				traces = []
				for path in path_coords_reordered:
					path_name = path
					x_p = path_coords[path][0]
					y_p = path_coords[path][1]

					text_tmp = [path.split('-')[0], path.split('-')[1]]

					traces.append(

						go.Scatter(
								    x=x_p, y=y_p,
								    text = text_tmp,
								    mode = 'lines+markers+text',
								    opacity = 0.7,
								    name = path_name,
								    line=dict(
								        width=7
								    ),
								    textfont=dict(
										size = 20
									)
								)
						)

				x = []
				y = []
				c = []
				labels = []
				with open(cell_coords, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						c.append(str(line[1]))
						x.append(float(line[2]))
						y.append(float(line[3]))
						try:
							labels.append(cell_label_colors_dict[str(line[1])])
						except:
							pass

				cell_types = {}
				if color_plot == 0:
					cell_types['Single Cells'] = [x, y, cell_label_list, 'grey']
				elif color_plot == 0.5:
					for label, x_c, y_c, color in zip(labels, x, y, c):
						if label not in cell_types:
							cell_types[label] = [[],[],[],[]]
						cell_types[label][0].append(x_c)
						cell_types[label][1].append(y_c)
						cell_types[label][2].append(label)
						cell_types[label][3].append('grey')
				else:
					for label, x_c, y_c, color in zip(labels, x, y, c):
						if label not in cell_types:
							cell_types[label] = [[],[],[],[]]
						cell_types[label][0].append(x_c)
						cell_types[label][1].append(y_c)
						cell_types[label][2].append(label)
						cell_types[label][3].append(color)

				for label in cell_types:
					traces.append(

						go.Scatter(
								x=cell_types[label][0],
								y=cell_types[label][1],
								mode='markers',
								opacity = 0.6,
								name = label,
								text = cell_types[label][2],
								marker = dict(
									size = 6,
									color = cell_types[label][3]
									)
								)
							)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app2.callback(
    Output('flat-tree-scatter2', 'figure'),
    [Input('precomp-dataset', 'value')])

def compute_trajectories(dataset):

	traces = []

	# try:

	cell_label = glob.glob('/stream_web/precomputed/%s/cell_label.tsv.gz*' % dataset)
	cell_label_colors = glob.glob('/stream_web/precomputed/%s/cell_label_color.tsv.gz*' % dataset)

	cell_label_list = []
	if len(cell_label) > 0:
		if cell_label[0].endswith('.gz'):
			with gzip.open(cell_label[0], 'r') as f:
				for line in f:
					cell_label_list.append(line.strip())
		else:
			with open(cell_label[0], 'r') as f:
				for line in f:
					cell_label_list.append(line.strip())

	cell_label_colors_dict = {}
	if len(cell_label_colors) > 0:
		if cell_label_colors[0].endswith('.gz'):
			with gzip.open(cell_label_colors[0], 'r') as f:
				for line in f:
					line = line.strip().split('\t')
					cell_label_colors_dict[str(line[1])] = str(line[0])

		else:
			with open(cell_label_colors[0], 'r') as f:
				for line in f:
					line = line.strip().split('\t')
					cell_label_colors_dict[str(line[1])] = str(line[0])

	# color_plot = 0
	# if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
	# 	color_plot = 1
	# elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
	# 	color_plot = 0.5

	cell_coords = '/stream_web/precomputed/%s/stream_report/flat_tree_coord_cells.csv' % dataset
	nodes = '/stream_web/precomputed/%s/stream_report/nodes.csv' % dataset
	edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
	metadata = '/stream_web/precomputed/%s/stream_report/metadata.tsv' % dataset

	node_list = {}
	edge_list = []

	with open(nodes, 'r') as f:
		next(f)
		for line in f:
			line = line.strip().split('\t')
			node_list[str(line[0])] = [float(line[1]), float(line[2])]

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append(sorted([str(line[0]), str(line[1])]))

	path_coords = {}
	path_coords_reordered = []
	for edge in edge_list:
		edge_name = '-'.join(map(str, edge))
		path_coords_reordered.append(edge_name)
		x_values = [node_list[edge[0]][0], node_list[edge[1]][0]]
		y_values = [node_list[edge[0]][1], node_list[edge[1]][1]]
		path_coords[edge_name] = [x_values, y_values]

	for path in path_coords_reordered:
		path_name = path
		x_p = path_coords[path][0]
		y_p = path_coords[path][1]

		text_tmp = [path.split('-')[0], path.split('-')[1]]

		traces.append(

			go.Scatter(
					    x=x_p, y=y_p,
					    text = text_tmp,
					    mode = 'lines+markers+text',
					    opacity = 0.7,
					    name = path_name,
					    line=dict(
					        width=7
					    ),
					    textfont=dict(
							size = 20
						)
					)
			)

	color2cell = {}
	with open(metadata, 'r') as f:
		next(f)
		for line in f:
			line = line.strip().split('\t')
			color2cell[str(line[2])] = str(line[1])

	x = []
	y = []
	c = []
	labels = []
	with open(cell_coords, 'r') as f:
		next(f)
		for line in f:
			line = line.strip().split('\t')
			c.append(str(line[1]))
			x.append(float(line[2]))
			y.append(float(line[3]))
			# try:
			labels.append(color2cell[str(line[1])])
			# except:
			# 	pass

	cell_types = {}
	# if color_plot == 0:
	# 	cell_types['Single Cells'] = [x, y, 'unlabeled', 'grey']
	# elif color_plot == 0.5:
	# 	for label, x_c, y_c, color in zip(labels, x, y, c):
	# 		if label not in cell_types:
	# 			cell_types[label] = [[],[],[],[]]
	# 		cell_types[label][0].append(x_c)
	# 		cell_types[label][1].append(y_c)
	# 		cell_types[label][2].append(label)
	# 		cell_types[label][3].append('grey')
	# else:
	for label, x_c, y_c, color in zip(labels, x, y, c):
		if label not in cell_types:
			cell_types[label] = [[],[],[],[]]
		cell_types[label][0].append(x_c)
		cell_types[label][1].append(y_c)
		cell_types[label][2].append(label)
		cell_types[label][3].append(color)

	for label in cell_types:
		traces.append(

			go.Scatter(
					x=cell_types[label][0],
					y=cell_types[label][1],
					mode='markers',
					opacity = 0.6,
					name = label,
					text = cell_types[label][2],
					marker = dict(
						size = 6,
						color = cell_types[label][3]
						)
					)
				)
	# except:
	# 	pass

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app.callback(
    Output('root', 'options'),
    [Input('3d-scatter', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	return [{'label': i, 'value': i} for i in param_dict['starting-nodes']]

@app2.callback(
    Output('root2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	node_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S*' % dataset)

	node_list = [x.split('/')[-1] for x in node_list_tmp if len(x.split('/')[-1]) == 2]

	return [{'label': i, 'value': i} for i in node_list]

@app2.callback(
    Output('root2', 'value'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	json_entry = glob.glob('/stream_web/precomputed/%s/*.json' % (dataset))
	data = json.load(open(json_entry[0]))

	return data['starting_node']

@app.callback(
    Output('2d-subway', 'figure'),
    [Input('root', 'value'),
    Input('3d-scatter', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(root, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	cell_coords = RESULTS_FOLDER + '/%s/subway_coord_cells.csv' % root
	path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)

	cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
	cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

	cell_label_list = []
	# if len(cell_label) > 0:
	# 	if cell_label[0].endswith('.gz'):
	# 		with gzip.open(cell_label[0], 'r') as f:
	# 			for line in f:
	# 				cell_label_list.append(line.strip())
	# 	else:
	# 		with open(cell_label[0], 'r') as f:
	# 			for line in f:
	# 				cell_label_list.append(line.strip())
	if len(cell_label) > 0:
		cell_label_df = pd.read_csv(cell_label[0],sep='\t',header=None,index_col=None,compression= 'gzip' if cell_label[0].split('.')[-1]=='gz' else None)
		cell_label_list = cell_label_df[0].tolist()


	cell_label_colors_dict = {}
	# if len(cell_label_colors) > 0:
	# 	if cell_label_colors[0].endswith('.gz'):
	# 		with gzip.open(cell_label_colors[0], 'r') as f:
	# 			for line in f:
	# 				line = line.strip().split('\t')
	# 				cell_label_colors_dict[str(line[1])] = str(line[0])

	# 			# for line in f:
	# 			# 	print(line)
	# 			# 	line = line.decode("utf-8")
	# 			# 	print(line)
	# 			# 	# line = line.strip().split('\t')
	# 			# 	cell_label_colors_dict[str(line[1].strip('\n'))] = str(line[0].strip('\n'))

	# 	else:
	# 		with open(cell_label_colors[0], 'r') as f:
	# 			for line in f:
	# 				line = line.strip().split('\t')
	# 				cell_label_colors_dict[str(line[1])] = str(line[0])
	if len(cell_label_colors) > 0:
		cell_label_colors_df = pd.read_csv(cell_label_colors[0],sep='\t',header=None,dtype={0:np.str},compression= 'gzip' if cell_label_colors[0].split('.')[-1]=='gz' else None)
		cell_label_colors_dict = cell_label_colors_df.set_index(1)[0].to_dict()

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1
	elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
		color_plot = 0.5

	edges = RESULTS_FOLDER + '/edges.tsv'
	edge_list = []

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append([str(line[0]), str(line[1])])

	path_coords_reordered = []
	for e in edge_list:
		entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
		path_coords_reordered.append(entry[0])

	for path in path_coords:
		if path not in path_coords_reordered:
			path_coords_reordered.append(path)

	traces = []
	for path in path_coords_reordered:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x=x_p, y=y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width=7
						    ),
						    textfont=dict(
								size = 20
							)
						)
				)

	x = []
	y = []
	c = []
	labels = []

	try:
		with open(cell_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[1]))
				x.append(float(line[2]))
				y.append(float(line[3]))
				try:
					labels.append(cell_label_colors_dict[str(line[1])])
				except:
					pass
	except:
		pass

	cell_types = {}
	if color_plot == 0:
		cell_types['Single Cells'] = [x, y, 'unlabeled', 'grey']
	elif color_plot == 0.5:
		for label, x_c, y_c, color in zip(labels, x, y, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(label)
			cell_types[label][3].append('grey')
	else:
		for label, x_c, y_c, color in zip(labels, x, y, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(label)
			cell_types[label][3].append(color)

	for label in cell_types:
		traces.append(
			go.Scatter(
						x=cell_types[label][0],
						y=cell_types[label][1],
						mode='markers',
						opacity = 0.6,
						name = label,
						text = cell_types[label][2],
						marker = dict(
							size = 6,
							color = cell_types[label][3]
							)
					)
				)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app2.callback(
    Output('2d-subway2', 'figure'),
    [Input('root2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, dataset):

	traces = []

	try:

		cell_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_cells.csv' % (dataset, root)
		path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/%s/subway_coord_line*csv' % (dataset, root))

		cell_label = glob.glob('/stream_web/precomputed/%s/cell_label.tsv.gz' % dataset)
		cell_label_colors = glob.glob('/stream_web/precomputed/%s/cell_label_color.tsv.gz' % dataset)

		cell_label_list = []
		if len(cell_label) > 0:
			if cell_label[0].endswith('.gz'):
				with gzip.open(cell_label[0], 'r') as f:
					for line in f:
						cell_label_list.append(line.strip())
			else:
				with open(cell_label[0], 'r') as f:
					for line in f:
						cell_label_list.append(line.strip())

		cell_label_colors_dict = {}
		if len(cell_label_colors) > 0:
			if cell_label_colors[0].endswith('.gz'):
				with gzip.open(cell_label_colors[0], 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						cell_label_colors_dict[str(line[1])] = str(line[0])

			else:
				with open(cell_label_colors[0], 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						cell_label_colors_dict[str(line[1])] = str(line[0])

		# color_plot = 0
		# if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		# 	color_plot = 1
		# elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
		# 	color_plot = 0.5

		edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
		edge_list = []

		with open(edges, 'r') as f:
			for line in f:
				line = line.strip().split('\t')
				edge_list.append([str(line[0]), str(line[1])])

		path_coords_reordered = []
		for e in edge_list:
			entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
			path_coords_reordered.append(entry[0])

		for path in path_coords:
			if path not in path_coords_reordered:
				path_coords_reordered.append(path)

		for path in path_coords_reordered:
			x_p = []
			y_p = []
			s1 = path.strip().split('_')[-2]
			s2 = path.strip().split('_')[-1].strip('.csv')
			s_3 = [s1, s2]
			path_name = '-'.join(map(str, s_3))
			with open(path, 'r') as f:
				next(f)
				for line in f:
					line = line.strip().split('\t')
					x_p.append(float(line[0]))
					y_p.append(float(line[1]))

				if len(x_p) == 2:
					text_tmp = [s1, s2]
				elif len(x_p) == 4:
					text_tmp = [s1, None, None, s2]
				elif len(x_p) == 6:
					text_tmp = [s1, None, None, None, None, s2]

				traces.append(

					go.Scatter(
							    x=x_p, y=y_p,
							    text = text_tmp,
							    mode = 'lines+markers+text',
							    opacity = 0.7,
							    name = path_name,
							    line=dict(
							        width=7
							    ),
							    textfont=dict(
									size = 20
								)
							)
					)

		metadata = '/stream_web/precomputed/%s/stream_report/metadata.tsv' % dataset

		color2cell = {}
		with open(metadata, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				color2cell[str(line[2])] = str(line[1])

		x = []
		y = []
		c = []
		labels = []

		try:
			with open(cell_coords, 'r') as f:
				next(f)
				for line in f:
					line = line.strip().split('\t')
					c.append(str(line[1]))
					x.append(float(line[2]))
					y.append(float(line[3]))
					# try:
					labels.append(color2cell[str(line[1])])
					# except:
					# 	pass
		except:
			pass

		cell_types = {}
		# if color_plot == 0:
		# 	cell_types['Single Cells'] = [x, y, 'unlabeled', 'grey']
		# elif color_plot == 0.5:
		# 	for label, x_c, y_c, color in zip(labels, x, y, c):
		# 		if label not in cell_types:
		# 			cell_types[label] = [[],[],[],[]]
		# 		cell_types[label][0].append(x_c)
		# 		cell_types[label][1].append(y_c)
		# 		cell_types[label][2].append(label)
		# 		cell_types[label][3].append('grey')
		# else:
		for label, x_c, y_c, color in zip(labels, x, y, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(label)
			cell_types[label][3].append(color)

		for label in cell_types:
			traces.append(
				go.Scatter(
							x=cell_types[label][0],
							y=cell_types[label][1],
							mode='markers',
							opacity = 0.6,
							name = label,
							text = cell_types[label][2],
							marker = dict(
								size = 6,
								color = cell_types[label][3]
								)
						)
					)
	except:
		pass

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app.callback(
    Output('rainbow-plot', 'src'),
    [Input('root', 'value'),
    Input('2d-subway', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(root, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	# try:
	rainbow_plot = RESULTS_FOLDER + '/%s/stream_plot.png' % root
	rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read()).decode('ascii')

	return 'data:image/png;base64,{}'.format(rainbow_plot_image)

	# except:
	# 	pass

@app2.callback(
    Output('rainbow-plot2', 'src'),
    [Input('root2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, dataset):

	try:

		rainbow_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot.png' % (dataset, root)
		rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(rainbow_plot_image)

	except:
		pass

############################# SINGLE GENE VISUALIZATION #############################
@app.callback(
	Output('sg-plot-button', 'children'),
	[Input('sg-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

@app2.callback(
	Output('sg-plot-button2', 'children'),
	[Input('sg-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'

@app.callback(
	Output('sg-plot-container', 'style'),
	[Input('sg-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('sg-plot-container2', 'style'),
	[Input('sg-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('sg-gene', 'options'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		gene_conversion_dict = {}
		gene_list_new = []
		with open(RESULTS_FOLDER + '/gene_conversion.tsv', 'r') as f:
			next(f)
			for line in f:
				orig, new = line.split('\t')
				gene_conversion_dict[new.strip('\n')] = orig.strip('\n')
				gene_list_new.append([new.strip('\n'), orig.strip('\n')])

		return [{'label': i[1], 'value': i[1]} for i in gene_list_new if i != 'False']

	# if pathname:

	# 	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	# 	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	# 	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
	# 		json_string = f.readline().strip()
	# 		param_dict = json.loads(json_string)

	# 	return [{'label': i, 'value': i} for i in param_dict['sg-genes']]

@app2.callback(
    Output('sg-gene2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('/stream_web/precomputed/%s/stream_report/gene_conversion.tsv' % dataset, 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

	# gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	# return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('sg-gene', 'value'),
    [Input('sg-gene', 'options'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['sg-genes'][0]

@app.callback(
    Output('sg-compute', 'children'),
    [Input('sg-compute', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['sg-clicks'] and param_dict['compute-run']:
			return 'Running...'
		else:
			return 'Visualize'

	else:
		return 'Visualize'

@app.callback(
    Output('sg-container', 'style'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('sg-button', 'disabled'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['sg-clicks']:
				return True
			else:
				return False

		else:
			return True

	return True

@app.callback(
    Output('sg-button', 'children'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:
			return 'Get Started'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer2', 'style'),
    [Input('sg-compute', 'n_clicks'),
    Input('url', 'pathname')],
    state=[State('root', 'value'),
    State('sg-gene', 'value'),
    State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    # State('feature_genes', 'value'),
    State('clustering', 'value'),
    State('n_clusters', 'value'),
    State('damping', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    # State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    # State('EPG_beta', 'value'),
    State('EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('disable_EPG_optimize', 'value')])

def compute_single_gene(n_clicks, pathname, root, gene, norm, log2, atac, lle_dr, lle_nbs, select, loess_frac,pca_n_PC,pca_first_PC,clustering,n_clusters,damping,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_alpha,EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,disable_EPG_optimize):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if (n_clicks > param_dict['sg-clicks'] or param_dict['sg-gene'] != gene):

			matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--clustering':[clustering],'--n_clusters':[n_clusters],'--damping':[damping],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_alpha':[EPG_alpha],'--EPG_collapse':[EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par],'--disable_EPG_optimize':[disable_EPG_optimize]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if param_dict['compute-run']:
				sb.call('stream --for_web -p -g %s ' % gene + ' '.join(map(str, arguments_final)) + ' > %s/log2.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}


@app.callback(
	Output('custom-loading-states-2', 'style'),
	[Input('sg-compute', 'n_clicks'),
	Input('2d-subway-sg', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton2']:

		return {'display': 'block'}

	elif not param_dict['checkpoint2']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-2', 'interval'),
	[Input('sg-compute', 'n_clicks'),
	Input('2d-subway-sg', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton2']:

		return 5000

	elif not param_dict['checkpoint2']:

		return 5000

	else:

		return 2000000000

@app.callback(
    Output('2d-subway-sg', 'figure'),
    [Input('url', 'pathname')],
    state=[State('sg-compute', 'n_clicks'),
    State('root', 'value'),
    State('sg-gene', 'value')],
    events=[Event('common-interval-2', 'interval')])

def compute_trajectories(pathname, n_clicks, root, gene):

	traces = []

	if pathname:

		gene = slugify(gene)

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log2.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/log2.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_coords = RESULTS_FOLDER + '/%s/subway_coord_cells.csv' % root
				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				edges = RESULTS_FOLDER + '/edges.tsv'
				edge_list = []

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append([str(line[0]), str(line[1])])

				path_coords_reordered = []
				for e in edge_list:
					entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
					path_coords_reordered.append(entry[0])

				for path in path_coords:
					if path not in path_coords_reordered:
						path_coords_reordered.append(path)

				traces = []
				for path in path_coords_reordered:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)
							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				# try:
				with open(gene_coords, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						c.append(str(line[0]))
						x_c.append(float(line[1]))
						y_c.append(float(line[2]))
						exp_scaled.append(float(line[3]))
						# exp_scaled.append(float(line[4]))
				# except:
				# 	pass

				exp_labels = ['Expression: ' + str(x) for x in exp_scaled]
				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'Single Cells',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['sg-clicks'] = n_clicks
				param_dict['sg-gene'] = gene
				param_dict['sg-run'] = True
				param_dict['checkbutton2'] += 1
				param_dict['checkpoint2'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app2.callback(
    Output('2d-subway-sg2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('sg-gene2', 'value'),
    Input('root2', 'value')])

def compute_trajectories(dataset, gene, root):

	traces = []

	cell_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/%s/subway_coord_line*csv' % (dataset, root))
	gene_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_%s.csv' % (dataset, root, gene)

	cell_label = '/stream_web/precomputed/%s/cell_label.tsv.gz' % dataset
	cell_label_colors = '/stream_web/precomputed/%s/cell_label_color.tsv.gz' % dataset

	edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
	edge_list = []

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append([str(line[0]), str(line[1])])

	path_coords_reordered = []
	for e in edge_list:
		entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
		path_coords_reordered.append(entry[0])

	for path in path_coords:
		if path not in path_coords_reordered:
			path_coords_reordered.append(path)

	traces = []
	for path in path_coords_reordered:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)
				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp_scaled]
	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'Single Cells',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }


@app.callback(
    Output('sg-plot', 'src'),
    [Input('2d-subway-sg', 'figure'),
    Input('url', 'pathname')],
    state=[State('root', 'value'),
    State('sg-gene', 'value')])

def num_clicks_compute(figure, pathname, root, gene):

	if pathname:

		gene = slugify(gene)

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
		genes = [x for x in genes if len(x.split('_')) == 4]
		genes = [x.split('_')[3].strip('.csv') for x in genes]

		if gene != 'False':

			try:

				discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
				discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

				return 'data:image/png;base64,{}'.format(discovery_plot_image)

			except:

				pass

@app2.callback(
    Output('sg-plot2', 'src'),
    [Input('precomp-dataset', 'value'),
    Input('sg-gene2', 'value'),
    Input('root2', 'value')])

def num_clicks_compute(dataset, gene, root):

	try:

		discovery_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot_%s.png' % (dataset, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')
		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:

		pass

######################################## GENE DISCOVERY ########################################
@app.callback(
	Output('discovery-plot-button', 'children'),
	[Input('discovery-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

@app2.callback(
	Output('discovery-plot-button2', 'children'),
	[Input('discovery-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'

@app.callback(
	Output('discovery-plot-container', 'style'),
	[Input('discovery-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('discovery-plot-container2', 'style'),
	[Input('discovery-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('discovery-gene', 'options'),
    [Input('2d-subway-discovery', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		gene_conversion_dict = {}
		with open(RESULTS_FOLDER + '/gene_conversion.tsv', 'r') as f:
			next(f)
			for line in f:
				orig, new = line.split('\t')
				gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

		return [{'label': gene_conversion_dict[i], 'value': i} for i in param_dict['discovery-genes'] if i != 'False']

@app2.callback(
    Output('discovery-gene2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	# print(gene_list)

	gene_conversion_dict = {}
	with open('/stream_web/precomputed/%s/stream_report/gene_conversion.tsv' % dataset, 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

	# gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	# return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('discovery-container', 'style'),
    [Input('2d-subway-discovery', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['discovery-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('discovery-button', 'disabled'),
    [Input('discovery-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['discovery-clicks']:
				return True
			else:
				return False

		else:
			return True

	else:
		return True

@app.callback(
    Output('discovery-button', 'children'),
    [Input('discovery-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['discovery-clicks'] and param_dict['compute-run']:
			return 'Running...'
		elif param_dict['compute-run']:
			return 'Perform Analysis'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer3', 'style'),
    [Input('discovery-button', 'n_clicks'),
    Input('url', 'pathname')],
    state = [State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    # State('feature_genes', 'value'),
    State('clustering', 'value'),
    State('n_clusters', 'value'),
    State('damping', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    # State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    # State('EPG_beta', 'value'),
    State('EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('disable_EPG_optimize', 'value'),
    State('root', 'value'),
    State('discovery-gene', 'value')])

def compute_discovery(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,clustering,n_clusters,damping,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_alpha,EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,disable_EPG_optimize,root,gene):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['discovery-clicks'] or param_dict['discovery-gene'] != gene:

			matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--clustering':[clustering],'--n_clusters':[n_clusters],'--damping':[damping],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_alpha':[EPG_alpha],'--EPG_collapse':[EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par],'--disable_EPG_optimize':[disable_EPG_optimize]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if not param_dict['discovery-run']:
				sb.call('stream --for_web --DE -p ' + ' '.join(map(str, arguments_final)) + ' > %s/log3.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-3', 'style'),
	[Input('discovery-button', 'n_clicks'),
	Input('2d-subway-discovery', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton3']:

		return {'display': 'block'}

	elif not param_dict['checkpoint3']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-3', 'interval'),
	[Input('discovery-button', 'n_clicks'),
	Input('2d-subway-discovery', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton3']:

		return 5000

	elif not param_dict['checkpoint3']:

		return 5000

	else:

		return 2000000000

@app.callback(
    Output('2d-subway-discovery', 'figure'),
    [Input('url', 'pathname'),
    Input('root', 'value'),
    Input('discovery-gene', 'value')],
    state=[State('discovery-button', 'n_clicks')],
    events=[Event('common-interval-3', 'interval')])

def compute_trajectories(pathname, root, gene, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log3.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/log3.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_coords = RESULTS_FOLDER + '/%s/subway_coord_cells.csv' % root
				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				lowercase_genes = [x.lower() for x in param_dict['sg-genes']]
				param_dict['discovery-genes'] = [x for x in genes if x.lower() in lowercase_genes]

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				edges = RESULTS_FOLDER + '/edges.tsv'
				edge_list = []

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append([str(line[0]), str(line[1])])

				path_coords_reordered = []
				for e in edge_list:
					entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
					path_coords_reordered.append(entry[0])

				for path in path_coords:
					if path not in path_coords_reordered:
						path_coords_reordered.append(path)

				traces = []
				for path in path_coords_reordered:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)

							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				try:
					with open(gene_coords, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							c.append(str(line[0]))
							x_c.append(float(line[1]))
							y_c.append(float(line[2]))
							exp_scaled.append(float(line[3]))
							# exp_scaled.append(float(line[4]))
				except:
					pass

				exp_labels = ['Expression: ' + str(x) for x in exp_scaled]
				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'Single Cells',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['discovery-clicks'] = n_clicks
				param_dict['discovery-gene'] = gene
				param_dict['discovery-run'] = True
				param_dict['checkbutton3'] += 1
				param_dict['checkpoint3'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app2.callback(
    Output('2d-subway-discovery2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('root2', 'value'),
    Input('discovery-gene2', 'value')])

def compute_trajectories(dataset, root, gene):

	traces = []

	cell_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/%s/subway_coord_line*csv' % (dataset, root))
	gene_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_%s.csv' % (dataset, root, gene)

	cell_label = '/stream_web/precomputed/%s/cell_label.tsv.gz' % dataset
	cell_label_colors = '/stream_web/precomputed/%s/cell_label_color.tsv.gz' % dataset

	edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
	edge_list = []

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append([str(line[0]), str(line[1])])

	path_coords_reordered = []
	for e in edge_list:
		entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
		path_coords_reordered.append(entry[0])

	for path in path_coords:
		if path not in path_coords_reordered:
			path_coords_reordered.append(path)

	for path in path_coords_reordered:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)

				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp_scaled]
	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'Single Cells',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app.callback(
    Output('discovery-plot', 'src'),
    [Input('root', 'value'),
    Input('discovery-gene', 'value'),
    Input('url', 'pathname')])

def num_clicks_compute(root, gene, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if gene != 'False':

			try:

				discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
				discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

				return 'data:image/png;base64,{}'.format(discovery_plot_image)

			except:
				pass

@app2.callback(
    Output('discovery-plot2', 'src'),
    [Input('root2', 'value'),
    Input('discovery-gene2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, gene, dataset):

	try:

		discovery_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot_%s.png' % (dataset, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app.callback(
    Output('de-branches', 'options'),
    [Input('2d-subway-discovery', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		combined_branches = []
		find_tables = glob.glob(RESULTS_FOLDER + '/de_genes/*.tsv')
		for table in find_tables:
			branch1 = table.split(' and ')[0].split('_')[-2] + '_' + table.split(' and ')[0].split('_')[-1]
			branch2 = table.split(' and ')[1].strip('.tsv')

			combined_branch = branch1 + ' and ' + branch2

			if combined_branch not in combined_branches:
				combined_branches.append(combined_branch)

		return [{'label': i, 'value': i} for i in combined_branches]

@app2.callback(
    Output('de-branches2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	combined_branches = []
	find_tables = glob.glob('/stream_web/precomputed/%s/stream_report/de_genes/*.tsv' % dataset)
	for table in find_tables:
		# branch1 = table.split(' and ')[0].split('greater_')[1]
		# branch2 = table.split(' and ')[1].strip('.tsv')

		branch1 = table.split(' and ')[0].split('_')[-2] + '_' + table.split(' and ')[0].split('_')[-1]
		branch2 = table.split(' and ')[1].strip('.tsv')

		combined_branch = branch1 + ' and ' + branch2

		if combined_branch not in combined_branches:
			combined_branches.append(combined_branch)

	return [{'label': i, 'value': i} for i in combined_branches]

	# combined_branches = []
	# find_tables = glob.glob('/stream_web/precomputed/%s/stream_report/DE_Genes/*.tsv' % dataset)
	# for table in find_tables:
	# 	branch1 = table.split(' and ')[0].split('genes_')[1]
	# 	branch2 = table.split(' and ')[1].strip('.tsv')

	# 	combined_branch = branch1 + ' and ' + branch2

	# 	if combined_branch not in combined_branches:
	# 		combined_branches.append(combined_branch)

	# return [{'label': i, 'value': i} for i in combined_branches]

@app.callback(
    Output('de-direction', 'options'),
    [Input('de-branches', 'value')])

def num_clicks_compute(branches):

	try:
		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		branches = [branch1, branch2]
	except:
		branches = ['Choose branch pair above']
		pass

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
    Output('de-direction2', 'options'),
    [Input('de-branches2', 'value')])

def num_clicks_compute(branches):

	try:
		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		branches = [branch1, branch2]
	except:
		branches = ['Choose branch pair above']
		pass

	return [{'label': i, 'value': i} for i in branches]

@app.callback(
	Output('discovery-table', 'children'),
	[Input('de-slider', 'value'),
	Input('de-branches', 'value'),
	Input('de-direction', 'value'),
	Input('2d-subway-discovery', 'figure'),
	Input('url', 'pathname')])

def update_table(slider, branches, direction, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	use_this_table = ''


	try:

		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		if direction == branch1:
			direction_classify = '_greater_'
		elif direction == branch2:
			direction_classify = '_less_'

		find_table = glob.glob(RESULTS_FOLDER + '/de_genes/*.tsv')
		for table in find_table:
			if (branch1 in table) and (branch2 in table) and (direction_classify in table):
				use_this_table = table
				break
	except:
		pass

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','z_score','U','logfc','mean_up','mean_down','pval','qval']

		mapper =  {'z_score': '{0:.2f}',
		           'logfc': '{0:.2f}',
		           'pval': '{:.2g}',
		           'qval': '{:.2g}'}
		for key, value in mapper.items():
			df[key] = df[key].apply(value.format)

		dff = df.head(n = slider)[['gene', 'z_score', 'logfc','pval', 'qval']] # update with your own logic

		return generate_table(dff)

@app2.callback(
	Output('discovery-table2', 'children'),
	[Input('de-slider2', 'value'),
	Input('de-branches2', 'value'),
	Input('de-direction2', 'value'),
	Input('precomp-dataset', 'value')])

def update_table(slider, branches, direction, dataset):

	use_this_table = ''

	try:

		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		if direction == branch1:
			direction_classify = '_greater_'
		elif direction == branch2:
			direction_classify = '_less_'

		find_table = glob.glob('/stream_web/precomputed/%s/stream_report/de_genes/*.tsv' % dataset)
		for table in find_table:
			if (branch1 in table) and (branch2 in table) and (direction_classify in table):
				use_this_table = table
				break
	except:
		pass

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','z_score','U','diff','mean_up','mean_down','pval','qval']

		mapper =  {'z_score': '{0:.2f}',
		           'diff': '{0:.2f}',
		           'pval': '{:.2g}',
		           'qval': '{:.2g}'}
		for key, value in mapper.items():
			df[key] = df[key].apply(value.format)

		dff = df.head(n = slider)[['gene', 'z_score', 'diff','pval', 'qval']] # update with your own logic

		return generate_table(dff)

	# use_this_table = ''

	# try:

	# 	branch1 = branches.split(' and ')[0]
	# 	branch2 = branches.split(' and ')[1]

	# 	if direction == branch1:
	# 		direction_classify = '_up_'
	# 	elif direction == branch2:
	# 		direction_classify = '_down_'

	# 	find_table = glob.glob('/stream_web/precomputed/%s/stream_report/DE_Genes/*.tsv' % dataset)
	# 	for table in find_table:
	# 		if (branch1 in table) and (branch2 in table) and (direction_classify in table):
	# 			use_this_table = table
	# 			break
	# except:
	# 	pass

	# if len(use_this_table) > 0:

	# 	df = pd.read_table(use_this_table).fillna('')
	# 	df.columns = ['gene','z_score','U','diff','mean_up','mean_down','pval','qval']

	# 	mapper =  {'z_score': '{0:.2f}',
	# 	           'diff': '{0:.2f}',
	# 	           'pval': '{:.2g}',
	# 	           'qval': '{:.2g}'}
	# 	for key, value in mapper.items():
	# 		df[key] = df[key].apply(value.format)

	# 	dff = df.head(n = slider)[['gene', 'z_score', 'diff','pval', 'qval']] # update with your own logic

	# 	return generate_table(dff)

### GENE CORRELATION
@app.callback(
	Output('correlation-plot-button', 'children'),
	[Input('correlation-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

@app2.callback(
	Output('correlation-plot-button2', 'children'),
	[Input('correlation-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(-) Show'

@app.callback(
	Output('correlation-plot-container', 'style'),
	[Input('correlation-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('correlation-plot-container2', 'style'),
	[Input('correlation-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('correlation-gene', 'options'),
    [Input('2d-subway-correlation', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		gene_conversion_dict = {}
		with open(RESULTS_FOLDER + '/gene_conversion.tsv', 'r') as f:
			next(f)
			for line in f:
				orig, new = line.split('\t')
				gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

		return [{'label': gene_conversion_dict[i], 'value': i} for i in param_dict['correlation-genes'] if i != 'False']

@app2.callback(
    Output('correlation-gene2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('/stream_web/precomputed/%s/stream_report/gene_conversion.tsv' % dataset, 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

	# gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	# return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('correlation-container', 'style'),
    [Input('2d-subway-correlation', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['correlation-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('correlation-button', 'disabled'),
    [Input('correlation-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['correlation-clicks']:
				return True
			else:
				return False

		else:
			return True

	else:
		return True

@app.callback(
    Output('correlation-button', 'children'),
    [Input('correlation-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['correlation-clicks'] and param_dict['compute-run']:
			return 'Running...'
		elif param_dict['compute-run']:
			return 'Perform Analysis'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer4', 'style'),
    [Input('correlation-button', 'n_clicks'),
    Input('url', 'pathname')],
    state = [State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    # State('feature_genes', 'value'),
    State('clustering', 'value'),
    State('n_clusters', 'value'),
    State('damping', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    # State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    # State('EPG_beta', 'value'),
    State('EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('disable_EPG_optimize', 'value'),
    State('root', 'value'),
    State('correlation-gene', 'value')])

def compute_correlation(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,clustering,n_clusters,damping,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_alpha,EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,disable_EPG_optimize,root,gene):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['correlation-clicks'] or param_dict['correlation-gene'] != gene:

			matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--clustering':[clustering],'--n_clusters':[n_clusters],'--damping':[damping],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_alpha':[EPG_alpha],'--EPG_collapse':[EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par],'--disable_EPG_optimize':[disable_EPG_optimize]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if not param_dict['correlation-run']:
				sb.call('stream --for_web --TG -p ' + ' '.join(map(str, arguments_final)) + ' > %s/log4.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-4', 'style'),
	[Input('correlation-button', 'n_clicks'),
	Input('2d-subway-correlation', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton4']:

		return {'display': 'block'}

	elif not param_dict['checkpoint4']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-4', 'interval'),
	[Input('correlation-button', 'n_clicks'),
	Input('2d-subway-correlation', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton4']:

		return 5000

	elif not param_dict['checkpoint4']:

		return 5000

	else:

		return 2000000000

@app.callback(
    Output('2d-subway-correlation', 'figure'),
    [Input('url', 'pathname'),
    Input('root', 'value'),
    Input('correlation-gene', 'value')],
    state=[State('correlation-button', 'n_clicks')],
    events=[Event('common-interval-4', 'interval')])

def compute_trajectories(pathname, root, gene, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log4.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/log4.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				lowercase_genes = [x.lower() for x in param_dict['sg-genes']]
				param_dict['correlation-genes'] = [x for x in genes if x.lower() in lowercase_genes]

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				edges = RESULTS_FOLDER + '/edges.tsv'
				edge_list = []

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append([str(line[0]), str(line[1])])

				path_coords_reordered = []
				for e in edge_list:
					entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
					path_coords_reordered.append(entry[0])

				for path in path_coords:
					if path not in path_coords_reordered:
						path_coords_reordered.append(path)

				traces = []
				for path in path_coords_reordered:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)

							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				try:
					with open(gene_coords, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							c.append(str(line[0]))
							x_c.append(float(line[1]))
							y_c.append(float(line[2]))
							exp_scaled.append(float(line[3]))
							# exp_scaled.append(float(line[4]))
				except:
					pass

				exp_labels = ['Expression: ' + str(x) for x in exp_scaled]

				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'Single Cells',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['correlation-clicks'] = n_clicks
				param_dict['correlation-gene'] = gene
				param_dict['correlation-run'] = True
				param_dict['checkbutton4'] += 1
				param_dict['checkpoint4'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app2.callback(
    Output('2d-subway-correlation2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('root2', 'value'),
    Input('correlation-gene2', 'value')])

def compute_trajectories(dataset, root, gene):

	traces = []

	cell_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/%s/subway_coord_line*csv' % (dataset, root))
	gene_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_%s.csv' % (dataset, root, gene)

	cell_label = '/stream_web/precomputed/%s/cell_label.tsv.gz' % dataset
	cell_label_colors = '/stream_web/precomputed/%s/cell_label_color.tsv.gz' % dataset

	edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
	edge_list = []

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append([str(line[0]), str(line[1])])

	path_coords_reordered = []
	for e in edge_list:
		entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
		path_coords_reordered.append(entry[0])

	for path in path_coords:
		if path not in path_coords_reordered:
			path_coords_reordered.append(path)

	traces = []
	for path in path_coords_reordered:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)

				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp_scaled]

	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'Single Cells',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app.callback(
    Output('correlation-plot', 'src'),
    [Input('root', 'value'),
    Input('correlation-gene', 'value'),
    Input('url', 'pathname')])

def num_clicks_compute(root, gene, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	if gene != 'False':

		try:

			discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
			discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

			return 'data:image/png;base64,{}'.format(discovery_plot_image)

		except:
			pass

@app2.callback(
    Output('correlation-plot2', 'src'),
    [Input('root2', 'value'),
    Input('correlation-gene2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, gene, dataset):

	try:

		discovery_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot_%s.png' % (dataset, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app.callback(
    Output('corr-branches', 'options'),
    [Input('2d-subway-correlation', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	branches = []
	find_tables = glob.glob(RESULTS_FOLDER + '/transition_genes/*.tsv')
	for table in find_tables:
		branch = table.split('_genes_')[1].strip('.tsv')

		if branch not in branches:
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
    Output('corr-branches2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	branches = []
	find_tables = glob.glob('/stream_web/precomputed/%s/stream_report/transition_genes/*.tsv' % dataset)
	for table in find_tables:
		branch = table.split('_genes_')[1].strip('.tsv')

		if branch not in branches:
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

	# branches = []
	# find_tables = glob.glob('/stream_web/precomputed/%s/stream_report/Transition_Genes/*.tsv' % dataset)
	# for table in find_tables:
	# 	branch = table.split('_Genes_')[1].strip('.tsv')

	# 	if branch not in branches:
	# 		branches.append(branch)

	# return [{'label': i, 'value': i} for i in branches]

@app.callback(
	Output('correlation-table', 'children'),
	[Input('corr-slider', 'value'),
	Input('corr-branches', 'value'),
	Input('2d-subway-correlation', 'figure'),
	Input('url', 'pathname')])

def update_table(slider, branch, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	use_this_table = ''

	find_table = glob.glob(RESULTS_FOLDER + '/transition_genes/*.tsv')
	for table in find_table:
		if branch in table:
			use_this_table = table
			break

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','stat','logfc','pval','qval']

		mapper =  {'stat': '{0:.2f}',
		           'logfc': '{0:.2f}',
		           'pval': '{:.2g}',
		           'qval': '{:.2g}'}
		for key, value in mapper.items():
			df[key] = df[key].apply(value.format)

		dff = df.head(n = slider)[['gene', 'stat', 'logfc', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

@app2.callback(
	Output('correlation-table2', 'children'),
	[Input('corr-slider2', 'value'),
	Input('corr-branches2', 'value'),
	Input('precomp-dataset', 'value')])

def update_table(slider, branch, dataset):

	use_this_table = ''

	find_table = glob.glob('/stream_web/precomputed/%s/stream_report/transition_genes/*.tsv' % dataset)
	for table in find_table:
		if branch in table:
			use_this_table = table
			break

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','stat','diff','pval','qval']

		mapper =  {'stat': '{0:.2f}',
		           'diff': '{0:.2f}',
		           'pval': '{:.2g}',
		           'qval': '{:.2g}'}
		for key, value in mapper.items():
			df[key] = df[key].apply(value.format)

		dff = df.head(n = slider)[['gene', 'stat', 'diff', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

### LEAF GENE PART!!!!!

@app.callback(
	Output('leaf-plot-button', 'children'),
	[Input('leaf-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

# @app2.callback(
# 	Output('leaf-plot-button2', 'children'),
# 	[Input('leaf-plot-button2', 'n_clicks')])

# def update_score_params_button(n_clicks):

# 	if n_clicks%2 != 0:
# 		return '(-) Hide'
# 	else:
# 		return '(-) Show'

@app.callback(
	Output('leaf-plot-container', 'style'),
	[Input('leaf-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

# @app2.callback(
# 	Output('leaf-plot-container2', 'style'),
# 	[Input('leaf-plot-button2', 'n_clicks')])

# def update_score_params_visual(n_clicks):

# 	if n_clicks%2 != 0:
# 		return {'display': 'block'}
# 	else:
# 		return {'display': 'none'}

@app.callback(
    Output('leaf-gene', 'options'),
    [Input('2d-subway-leaf', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		gene_conversion_dict = {}
		with open(RESULTS_FOLDER + '/gene_conversion.tsv', 'r') as f:
			next(f)
			for line in f:
				orig, new = line.split('\t')
				gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

		return [{'label': gene_conversion_dict[i], 'value': i} for i in param_dict['leaf-genes'] if i != 'False']

# @app2.callback(
#     Output('leaf-gene2', 'options'),
#     [Input('precomp-dataset', 'value')])

# def num_clicks_compute(dataset):

# 	gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % dataset)

# 	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

# 	return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('leaf-container', 'style'),
    [Input('2d-subway-leaf', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['leaf-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('leaf-button', 'disabled'),
    [Input('leaf-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['leaf-clicks']:
				return True
			else:
				return False

		else:
			return True

	else:
		return True

@app.callback(
    Output('leaf-button', 'children'),
    [Input('leaf-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['leaf-clicks'] and param_dict['compute-run']:
			return 'Running...'
		elif param_dict['compute-run']:
			return 'Perform Analysis'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer10', 'style'),
    [Input('leaf-button', 'n_clicks'),
    Input('url', 'pathname')],
    state = [State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    # State('feature_genes', 'value'),
    State('clustering', 'value'),
    State('n_clusters', 'value'),
    State('damping', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    # State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    # State('EPG_beta', 'value'),
    State('EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('disable_EPG_optimize', 'value'),
    State('root', 'value'),
    State('leaf-gene', 'value')])

def compute_leaf(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,clustering,n_clusters,damping,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_alpha,EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,disable_EPG_optimize,root,gene):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['leaf-clicks'] or param_dict['leaf-gene'] != gene:

			matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--clustering':[clustering],'--n_clusters':[n_clusters],'--damping':[damping],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_alpha':[EPG_alpha],'--EPG_collapse':[EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par],'--disable_EPG_optimize':[disable_EPG_optimize]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if not param_dict['leaf-run']:
				sb.call('stream --for_web --LG -p ' + ' '.join(map(str, arguments_final)) + ' > %s/log5.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-5', 'style'),
	[Input('leaf-button', 'n_clicks'),
	Input('2d-subway-leaf', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton5']:

		return {'display': 'block'}

	elif not param_dict['checkpoint5']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-5', 'interval'),
	[Input('leaf-button', 'n_clicks'),
	Input('2d-subway-leaf', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton5']:

		return 5000

	elif not param_dict['checkpoint5']:

		return 5000

	else:

		return 2000000000

@app.callback(
    Output('2d-subway-leaf', 'figure'),
    [Input('url', 'pathname'),
    Input('root', 'value'),
    Input('leaf-gene', 'value')],
    state=[State('leaf-button', 'n_clicks')],
    events=[Event('common-interval-5', 'interval')])

def compute_trajectories(pathname, root, gene, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log5.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/log5.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				lowercase_genes = [x.lower() for x in param_dict['sg-genes']]
				param_dict['leaf-genes'] = [x for x in genes if x.lower() in lowercase_genes]

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				edges = RESULTS_FOLDER + '/edges.tsv'
				edge_list = []

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append([str(line[0]), str(line[1])])

				path_coords_reordered = []
				for e in edge_list:
					entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
					path_coords_reordered.append(entry[0])

				for path in path_coords:
					if path not in path_coords_reordered:
						path_coords_reordered.append(path)

				traces = []
				for path in path_coords_reordered:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)

							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				try:
					with open(gene_coords, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							c.append(str(line[0]))
							x_c.append(float(line[1]))
							y_c.append(float(line[2]))
							exp_scaled.append(float(line[3]))
							# exp_scaled.append(float(line[4]))
				except:
					pass

				exp_labels = ['Expression: ' + str(x) for x in exp_scaled]

				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'Single Cells',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['leaf-clicks'] = n_clicks
				param_dict['leaf-gene'] = gene
				param_dict['leaf-run'] = True
				param_dict['checkbutton5'] += 1
				param_dict['checkpoint5'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

# @app2.callback(
#     Output('2d-subway-leaf2', 'figure'),
#     [Input('precomp-dataset', 'value'),
#     Input('root2', 'value'),
#     Input('leaf-gene2', 'value')])

# def compute_trajectories(dataset, root, gene):

# 	traces = []

# 	cell_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_cells.csv' % (dataset, root)
# 	path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/%s/subway_coord_line*csv' % (dataset, root))
# 	gene_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_%s.csv' % (dataset, root, gene)

# 	cell_label = '/stream_web/precomputed/%s/cell_label.tsv.gz' % dataset
# 	cell_label_colors = '/stream_web/precomputed/%s/cell_label_color.tsv.gz' % dataset

# 	edges = '/stream_web/precomputed/%s/stream_report/edges.tsv' % dataset
# 	edge_list = []

# 	with open(edges, 'r') as f:
# 		for line in f:
# 			line = line.strip().split('\t')
# 			edge_list.append([str(line[0]), str(line[1])])

# 	path_coords_reordered = []
# 	for e in edge_list:
# 		entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
# 		path_coords_reordered.append(entry[0])

# 	for path in path_coords:
# 		if path not in path_coords_reordered:
# 			path_coords_reordered.append(path)

# 	traces = []
# 	for path in path_coords_reordered:
# 		x_p = []
# 		y_p = []
# 		s1 = path.strip().split('_')[-2]
# 		s2 = path.strip().split('_')[-1].strip('.csv')
# 		s_3 = [s1, s2]
# 		path_name = '-'.join(map(str, s_3))
# 		with open(path, 'r') as f:
# 			next(f)
# 			for line in f:
# 				line = line.strip().split('\t')
# 				x_p.append(float(line[0]))
# 				y_p.append(float(line[1]))

# 			if len(x_p) == 2:
# 				text_tmp = [s1, s2]
# 			elif len(x_p) == 4:
# 				text_tmp = [s1, None, None, s2]
# 			elif len(x_p) == 6:
# 				text_tmp = [s1, None, None, None, None, s2]

# 			traces.append(

# 				go.Scatter(
# 						    x = x_p, y = y_p,
# 						    text = text_tmp,
# 						    mode = 'lines+markers+text',
# 						    opacity = 0.7,
# 						    name = path_name,
# 						    line=dict(
# 						        width = 3,
# 						        color = 'grey'
# 						    ),
# 						    textfont=dict(
# 								size = 20
# 							)
# 						)

# 				)

# 	x_c = []
# 	y_c = []
# 	c = []
# 	exp = []
# 	exp_scaled = []

# 	try:
# 		with open(gene_coords, 'r') as f:
# 			next(f)
# 			for line in f:
# 				line = line.strip().split('\t')
# 				c.append(str(line[0]))
# 				x_c.append(float(line[1]))
# 				y_c.append(float(line[2]))
# 				exp_scaled.append(float(line[3]))
# 				# exp_scaled.append(float(line[4]))
# 	except:
# 		pass

# 	exp_labels = ['Expression: ' + str(x) for x in exp_scaled]

# 	traces.append(
# 		go.Scatter(
# 					x = x_c,
# 					y = y_c,
# 					mode='markers',
# 					opacity = 0.6,
# 					name = 'Single Cells',
# 					text = exp_labels,
# 					marker = dict(
# 						size = 6,
# 						color = exp_scaled,
# 						colorscale = 'RdBu'
# 						)
# 				)
# 			)

# 	return {
#         'data': traces,
#         'layout': go.Layout(
#         	autosize = True,
#         	margin=dict(l=0,r=0,t=0),
#             hovermode='closest',
#             xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
#             yaxis = dict(showgrid = False, zeroline=False, title = ''),
#         )
#     }

@app.callback(
    Output('leaf-plot', 'src'),
    [Input('root', 'value'),
    Input('leaf-gene', 'value'),
    Input('url', 'pathname')])

def num_clicks_compute(root, gene, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	if gene != 'False':

		try:

			discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
			discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

			return 'data:image/png;base64,{}'.format(discovery_plot_image)

		except:
			pass

# @app2.callback(
#     Output('leaf-plot2', 'src'),
#     [Input('root2', 'value'),
#     Input('leaf-gene2', 'value'),
#     Input('precomp-dataset', 'value')])

# def num_clicks_compute(root, gene, dataset):

# 	try:

# 		discovery_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot_%s.png' % (dataset, root, gene)
# 		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

# 		return 'data:image/png;base64,{}'.format(discovery_plot_image)

# 	except:
# 		pass

@app.callback(
    Output('leaf-branches', 'options'),
    [Input('2d-subway-leaf', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	branches = []
	find_tables = glob.glob(RESULTS_FOLDER + '/leaf_genes/*.tsv')
	for table in find_tables:
		branch = table.split('_genes')[-1].strip('.tsv')

		if (branch not in branches) and (len(branch) > 0):
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

# @app2.callback(
#     Output('leaf-branches2', 'options'),
#     [Input('precomp-dataset', 'value')])

# def num_clicks_compute(dataset):

# 	branches = []
# 	find_tables = glob.glob('/stream_web/precomputed/%s/stream_report/Leaf_Genes/*.tsv' % dataset)
# 	for table in find_tables:
# 		branch = table.split('_Genes')[1].strip('.tsv')

# 		if branch not in branches:
# 			branches.append(branch)

# 	return [{'label': i, 'value': i} for i in branches]

@app.callback(
	Output('leaf-table', 'children'),
	[Input('leaf-slider', 'value'),
	Input('leaf-branches', 'value'),
	Input('2d-subway-leaf', 'figure'),
	Input('url', 'pathname')])

def update_table(slider, branch, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	use_this_table = ''

	find_table = glob.glob(RESULTS_FOLDER + '/leaf_genes/*.tsv')
	for table in find_table:
		if branch in table:
			use_this_table = table
			break

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')

		pvals = [x for x in df.columns if 'pvalue' in x]

		mapper =  {'zscore': '{0:.2f}',
		           'H_statistic': '{0:.2f}'}

		for i in pvals:
			mapper[i] = '{:.2g}'

		for key, value in mapper.items():
			df[key] = df[key].apply(value.format)

		dff = df.head(n = slider)#[['gene', 'stat', 'diff', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

# @app2.callback(
# 	Output('leaf-table2', 'children'),
# 	[Input('leaf-slider2', 'value'),
# 	Input('leaf-branches2', 'value'),
# 	Input('precomp-dataset', 'value')])

# def update_table(slider, branch, dataset):

# 	use_this_table = ''

# 	find_table = glob.glob('/stream_web/precomputed/%s/stream_report/Transition_Genes/*.tsv' % dataset)
# 	for table in find_table:
# 		if branch in table:
# 			use_this_table = table
# 			break

# 	if len(use_this_table) > 0:

# 		df = pd.read_table(use_this_table).fillna('')
# 		df.columns = ['gene','stat','diff','pval','qval']

# 		mapper =  {'stat': '{0:.2f}',
# 		           'diff': '{0:.2f}',
# 		           'pval': '{:.2g}',
# 		           'qval': '{:.2g}'}
# 		for key, value in mapper.items():
# 			df[key] = df[key].apply(value.format)

# 		dff = df.head(n = slider)[['gene', 'stat', 'diff', 'pval', 'qval']] # update with your own logic

# 		return generate_table(dff)

# DOWNLOAD PORTION

@app.callback(
	Output('download-container', 'style'),
	[Input('3d-scatter', 'figure'),
	Input('url', 'pathname')])

def download_container(figure, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/log1.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/log1.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation.\n' in f_data:
				return {'display': 'block'}

			else:
				return {'display': 'none'}

		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}


# def bash_command(cmd):
#     sb.Popen(cmd, shell=True, executable='/bin/bash')

@app.callback(
    Output('download-total', 'href'),
    [Input('download-total', 'n_clicks'),
    Input('url', 'pathname')],
    state = [State('title-input', 'value'),
    State('description-input', 'value'),
    State('root', 'value')])

def zip_dir(n_clicks, pathname, title_input, description_input, starting_node):

	if pathname:
		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		overview_folder = 'stream-outputs'
		results_folder = 'STREAM_result'

		if n_clicks > 0:

			with open(RESULTS_FOLDER + '/command_line_used.txt', 'r') as f:
				command_line_used = f.readline()

			json_file = {'title': title_input,
						'description': description_input,
						'starting_node': starting_node,
						'command_used': command_line_used}

			with open('%s/stream.json' % (RESULTS_FOLDER), 'w') as f:
				json_string = json.dumps(json_file)
				f.write(json_string + '\n')

			full_path = RESULTS_FOLDER + '/' + 'stream-outputs.zip'

			return '/dash/urldownload%s' % full_path

			# UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
			# RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

			# if os.path.exists(RESULTS_FOLDER + '/log1.txt'):

			# 	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			# 		json_string = f.readline().strip()
			# 		param_dict = json.loads(json_string)

			# 	f = open(RESULTS_FOLDER + '/log1.txt', 'r')
			# 	f_data = f.readlines()
			# 	f.close()

			# 	if 'Finished computation...\n' in f_data:

			# 		overview_folder = 'stream-outputs'
			# 		results_folder = 'STREAM_result'

			# 		if os.path.exists('%s/%s' % (RESULTS_FOLDER, overview_folder)):
			# 			sb.call('rm -r %s/%s' % (RESULTS_FOLDER, overview_folder), shell = True)

			# 		sb.call('mkdir %s/%s' % (RESULTS_FOLDER, overview_folder), shell = True)
			# 		sb.call('mkdir %s/%s/%s' % (RESULTS_FOLDER, overview_folder, results_folder), shell = True)

			# 		matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
			# 		cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			# 		cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			# 		sb.call('cp %s %s/%s/' % (matrix[0], RESULTS_FOLDER, overview_folder), shell = True)

			# 		if len(cell_label) > 0:
			# 			sb.call('cp %s %s/%s/cell_label.tsv' % (cell_label[0], RESULTS_FOLDER, overview_folder), shell = True)

			# 		if len(cell_label_colors) > 0:
			# 			sb.call('cp %s %s/%s/cell_label_color.tsv' % (cell_label_colors[0], RESULTS_FOLDER, overview_folder), shell = True)

			# 		with open(RESULTS_FOLDER + '/command_line_used.txt', 'r') as f:
			# 			command_line_used = f.readline()

			# 		json_file = {'title': title_input,
			# 					'description': description_input,
			# 					'starting_node': starting_node,
			# 					'command_used': command_line_used}

			# 		with open('%s/%s/stream.json' % (RESULTS_FOLDER, overview_folder), 'w') as f:
			# 			json_string = json.dumps(json_file)
			# 			f.write(json_string + '\n')

			# 		sb.call('cp -r %s/*tsv %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
			# 		sb.call('cp -r %s/*csv %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
			# 		sb.call('cp -r %s/*pdf %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
			# 		sb.call('cp -r %s/*png %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
			# 		sb.call('cp -r %s/S* %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
			# 		sb.call('cp -r %s/*_Genes %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
			# 		sb.call('cp -r %s/Precomputed %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)

			# 		proc = sb.Popen('pushd %s && zip -r %s.zip %s && popd' % (RESULTS_FOLDER, overview_folder, overview_folder), shell=True, executable='/bin/bash')
			# 		proc.wait()

			# 		full_path = RESULTS_FOLDER + '/' + 'stream-outputs.zip'
			# 		return '/dash/urldownload%s' % full_path

					# send_file('%s/stream-outputs.zip' % (RESULTS_FOLDER), attachment_filename = 'stream-outputs.zip', as_attachment = True)

					# bash_command('pushd %s && zip -r %s.zip %s && popd' % (RESULTS_FOLDER, overview_folder, overview_folder))

					# return {'display': 'block'}

		else:
			full_path = RESULTS_FOLDER + '/' + 'stream-outputs.zip'
			return '/dash/urldownload%s' % full_path



# @app.callback(
#     Output('download-total', 'href'),
#     [Input('buffer6', 'style'),
#     Input('url', 'pathname')],
#     state = [State('download-total', 'n_clicks')])

# def generate_report_url(buffer, pathname, n_clicks):

# 	if n_clicks == 0:

# 		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
# 		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

# 		full_path = RESULTS_FOLDER + '/' + 'stream-outputs.zip'

# 		return '/dash/urldownload%s' % full_path

# LEAF GENE PART FOR VISUALIZATION

### LEAF GENE PART!!!!!
@app2.callback(
	Output('leaf-plot-button2', 'children'),
	[Input('leaf-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(-) Show'

@app2.callback(
	Output('leaf-plot-container2', 'style'),
	[Input('leaf-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app2.callback(
    Output('leaf-gene2', 'options'),
    [Input('precomp-dataset', 'value'),
    Input('buffer7', 'style')])

def num_clicks_compute(precomp, buffer):

	gene_list_tmp = glob.glob('/stream_web/precomputed/%s/stream_report/S0/stream_plot_*png' % precomp)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('/stream_web/precomputed/%s/stream_report/gene_conversion.tsv' % precomp, 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# return [{'label': i, 'value': i} for i in gene_list]

@app2.callback(
    Output('2d-subway-leaf2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('root2', 'value'),
    Input('leaf-gene2', 'value')])

def compute_trajectories(precomp, root, gene):

	traces = []

	cell_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_cells.csv' % (precomp, root)
	path_coords = glob.glob('/stream_web/precomputed/%s/stream_report/%s/subway_coord_line*csv' % (precomp, root))
	gene_coords = '/stream_web/precomputed/%s/stream_report/%s/subway_coord_%s.csv' % (precomp, root, gene)

	cell_label = '/stream_web/precomputed/%s/stream_report/cell_label.tsv.gz'  % (precomp)
	cell_label_colors = '/stream_web/precomputed/%s/stream_report/cell_label_color.tsv.gz'  % (precomp)

	edges = '/stream_web/precomputed/%s/stream_report/edges.tsv'  % (precomp)
	edge_list = []

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append([str(line[0]), str(line[1])])

	path_coords_reordered = []
	for e in edge_list:
		entry = [x for x in path_coords if ((e[0] in x.split('/')[-1]) and (e[1] in x.split('/')[-1]))]
		path_coords_reordered.append(entry[0])

	for path in path_coords:
		if path not in path_coords_reordered:
			path_coords_reordered.append(path)

	traces = []
	for path in path_coords_reordered:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)

				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp_scaled]

	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'Single Cells',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, showline=True, title = 'Pseudotime'),
            yaxis = dict(showgrid = False, zeroline=False, title = ''),
        )
    }

@app2.callback(
    Output('leaf-plot2', 'src'),
    [Input('precomp-dataset', 'value'),
    Input('root2', 'value'),
    Input('leaf-gene2', 'value'),
    ])

def num_clicks_compute(precomp, root, gene):

	try:

		discovery_plot = '/stream_web/precomputed/%s/stream_report/%s/stream_plot_%s.png' % (precomp, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app2.callback(
    Output('leaf-branches2', 'options'),
    [Input('precomp-dataset', 'value'),
    Input('buffer8', 'style')])

def num_clicks_compute(precomp, buffer):

	branches = []
	find_tables = glob.glob('/stream_web/precomputed/%s/stream_report/leaf_genes/*.tsv' % precomp)
	for table in find_tables:
		branch = table.split('_genes')[-1].strip('.tsv')

		if (branch not in branches) and (len(branch) > 0):
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
	Output('leaf-table2', 'children'),
	[Input('precomp-dataset', 'value'),
	Input('leaf-slider2', 'value'),
	Input('leaf-branches2', 'value'),
	])

def update_table(precomp, slider, branch):

	use_this_table = ''

	find_table = glob.glob('/stream_web/precomputed/%s/stream_report/leaf_genes/*.tsv' % precomp)
	for table in find_table:
		if branch in table:
			use_this_table = table
			break

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')

		pvals = [x for x in df.columns if 'pvalue' in x]

		mapper =  {'zscore': '{0:.2f}',
		           'H_statistic': '{0:.2f}'}

		for i in pvals:
			mapper[i] = '{:.2g}'

		for key, value in mapper.items():
			df[key] = df[key].apply(value.format)

		dff = df.head(n = slider)#[['gene', 'stat', 'diff', 'pval', 'qval']] # update with your own logic
		column_names = list(dff)
		column_names[0] = "gene"

		dff.columns = column_names

		return generate_table(dff)

@app.server.route('/dash/urldownload/tmp/RESULTS_FOLDER/<directory>/stream-outputs.zip')
def generate_report_url(directory):

	overview_folder = 'stream-outputs'
	results_folder = 'STREAM_result'

	RESULTS_FOLDER = '/tmp/RESULTS_FOLDER/%s' % directory
	UPLOADS_FOLDER = '/tmp/UPLOADS_FOLDER/%s' % directory

	if os.path.exists('%s/%s' % (RESULTS_FOLDER, overview_folder)):
		sb.call('rm -r %s/%s' % (RESULTS_FOLDER, overview_folder), shell = True)

	sb.call('mkdir %s/%s' % (RESULTS_FOLDER, overview_folder), shell = True)
	sb.call('mkdir %s/%s/%s' % (RESULTS_FOLDER, overview_folder, results_folder), shell = True)

	matrix = glob.glob(UPLOADS_FOLDER + '/Data_Matrix*')
	cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
	cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

	sb.call('cp %s %s/%s/' % (matrix[0], RESULTS_FOLDER, overview_folder), shell = True)

	if len(cell_label) > 0:
		sb.call('cp %s %s/%s/cell_label.tsv' % (cell_label[0], RESULTS_FOLDER, overview_folder), shell = True)

	if len(cell_label_colors) > 0:
		sb.call('cp %s %s/%s/cell_label_color.tsv' % (cell_label_colors[0], RESULTS_FOLDER, overview_folder), shell = True)

	sb.call('cp %s/stream.json %s/%s/' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder), shell = True)
	sb.call('cp -r %s/*tsv %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
	sb.call('cp -r %s/*csv %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
	sb.call('cp -r %s/*pdf %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
	sb.call('cp -r %s/*png %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
	sb.call('cp -r %s/S* %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
	sb.call('cp -r %s/*_genes %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)
	sb.call('cp -r %s/Precomputed %s/%s/%s' % (RESULTS_FOLDER, RESULTS_FOLDER, overview_folder, results_folder), shell = True)

	proc = sb.Popen('pushd %s && zip -r %s.zip %s && popd' % (RESULTS_FOLDER, overview_folder, overview_folder), shell=True, executable='/bin/bash')
	proc.wait()
    rs.reformat.reformat_web('/tmp/RESULTS_FOLDER/%s/stream-outputs.zip' % (directory), '/tmp/RESULTS_FOLDER/%s/stream-outputs.zip' % (directory))
	# ref.web('/tmp/RESULTS_FOLDER/%s/stream-outputs.zip' % (directory), '/tmp/RESULTS_FOLDER/%s/stream-outputs.zip' % (directory))

	return send_file('/tmp/RESULTS_FOLDER/%s/stream-outputs.zip' % (directory), attachment_filename = 'stream-outputs.zip', as_attachment = True)


# Add drag and drop upload for visualization
@app2.callback(Output('upload-log', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')],
               state = [State('url2', 'pathname')])

def download_file(contents, filename, pathname):

	if pathname:

		content_type, content_string = contents.split(',')

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if filename.endswith('.zip'):

			# upload_files(['STREAM Results .zip'], UPLOADS_FOLDER)
			with open('%s/STREAM_Results.zip' % UPLOADS_FOLDER, 'wb') as fh:
				decoded = base64.b64decode(content_string)
				fh.write(decoded)

			stream_zip = glob.glob(UPLOADS_FOLDER + '/STREAM_Results*.zip')

			if len(stream_zip) > 0:

				for i in stream_zip:

					# print('zip file: %s' % i)

					new_folder_name = 'USER_UPLOAD_%s' % str(str(pathname).split('/')[-1])

					sb.call('rm -rf /stream_web/precomputed/%s' % new_folder_name, shell = True)

					sb.call('mkdir /stream_web/precomputed/%s' % new_folder_name, shell = True)

					zip_ref = zipfile.ZipFile(i, 'r')
					zip_ref.extractall('/stream_web/precomputed/%s/' % new_folder_name)
					zip_ref.close()

					try:
						sb.call('mkdir /stream_web/precomputed/%s/stream_report' % new_folder_name, shell = True)
					except:
						pass

					sb.call('mv /stream_web/precomputed/%s/*/*json /stream_web/precomputed/%s' % (new_folder_name, new_folder_name), shell = True)
					sb.call('mv /stream_web/precomputed/%s/*/stream_report/* /stream_web/precomputed/%s/stream_report' % (new_folder_name, new_folder_name), shell = True)
					sb.call('rm -rf /stream_web/precomputed/%s/*/stream_report' % new_folder_name, shell = True)

					try:
						sb.call('rm -rf /stream_web/precomputed/%s/__MACOSX' % new_folder_name, shell = True)
					except:
						pass

				return 'Upload Status: Complete'

		else:
			return 'Upload Status: Incomplete - .zip format required'

	return 'Upload Status: Incomplete - No upload'

def main():
    app.run_server(debug = True, processes = 5, port = 9992, host = '0.0.0.0')

if __name__ == '__main__':
	main()
