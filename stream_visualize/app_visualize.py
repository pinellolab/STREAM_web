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

path_to_zip_file = sys.argv[-1]

zip_ref = zipfile.ZipFile(path_to_zip_file, 'r')
zip_ref.extractall('./unzipped_data/')
zip_ref.close()

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
# stream_logo = get_data('/stream_web/static/stream_logo.png')
stream_logo_image = base64.b64encode(open('./static/stream_logo.png', 'rb').read()).decode('ascii')

# mgh_logo = get_data('/stream_web/static/mgh.png')
mgh_logo_image = base64.b64encode(open('./static/mgh.png', 'rb').read())

# mitbe_logo = get_data('/stream_web/static/mitbe.png')
mitbe_logo_image = base64.b64encode(open('./static/mitbe.png', 'rb').read())

# hms_logo = get_data('/stream_web/static/hms.png')
hms_logo_image = base64.b64encode(open('./static/hms.png', 'rb').read())

# Generate ID to initialize CRISPR-SURF instance
server = Flask(__name__)
server.secret_key = '~x94`zW\sfa24\xa2qdx20g\x9dl\xc0x35x90\kchs\x9c\xceb\xb4'
app2 = Dash_responsive('stream-visualize', server = server, csrf_protect=False)

app2.css.config.serve_locally = True
app2.scripts.config.serve_locally = True

# app2 = Dash_responsive(name = 'stream-app-precomputed', server = server, csrf_protect=False)

app2.layout = html.Div([

	dcc.Location(id='url2', refresh=False),

	html.Div(id = 'custom-loading-states-11',
		children = [

		html.Div(id = 'custom-loading-state11', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Img(src='data:image/png;base64,{}'.format(stream_logo_image), width = '50%'),
	html.H2('Single-cell Trajectory Reconstruction Exploration And Mapping'),

	# html.Hr(),

	# html.H3('Choose Precomputed Data Set'),

	# dcc.Dropdown(
	# 	id = 'precomp-',
	#     options=[
	#         {'label': 'Nestorowa, S. et al. 2016', 'value': 'Nestorowa'},
	#     ],
	#     value = 'Nestorowa',
	#     style = {'display':'none'}
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
		        {'label': 'S0', 'value': 'S0'},
		    ],
		    value='S0'
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


################################# COMPUTE TRAJECTORIES #################################

@app2.callback(
	Output('custom-loading-states-11', 'style'),
	[
	Input('rainbow-plot2', 'src'),
	Input('url2', 'pathname')],
	state = [State('root2', 'value')])

def update_container( stream_plot_src, pathname, root):

	rainbow_plot = './unzipped_data/stream_result/%s/stream_plot.png' % (root)
	rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read()).decode('ascii')

	if 'data:image/png;base64,{}'.format(rainbow_plot_image) == stream_plot_src:

		return {'display': 'none'}
		# return {'display': 'block'}
	else:
		return {'display': 'block'}

@app2.callback(
    Output('3d-scatter2', 'figure'),
    [Input('buffer8', 'style')])

def compute_trajectories(style):

	traces = []

	try:

		cell_label = glob.glob('./unzipped_data/stream_result/cell_label.tsv.gz*' )
		cell_label_colors = glob.glob('./unzipped_data/stream_result/cell_label_color.tsv.gz*' )

		edges = './unzipped_data/stream_result/edges.tsv' 
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

		color_plot = 0
		if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
			color_plot = 1
		elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
			color_plot = 0.5

		cell_coords = './unzipped_data/stream_result/coord_cells.csv' 
		coord_states = './unzipped_data/stream_result/coord_states.csv' 
		path_coords = glob.glob('./unzipped_data/stream_result/coord_curve*csv' )

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

@app2.callback(
    Output('flat-tree-scatter2', 'figure'),
    [Input('buffer9', 'style')])

def compute_trajectories(buffer):

	traces = []

	# try:

	cell_label = glob.glob('./unzipped_data/stream_result/cell_label.tsv.gz*' )
	cell_label_colors = glob.glob('./unzipped_data/stream_result/cell_label_color.tsv.gz*' )

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

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1
	elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
		color_plot = 0.5

	cell_coords = './unzipped_data/stream_result/flat_tree_coord_cells.csv' 
	nodes = './unzipped_data/stream_result/nodes.csv' 
	edges = './unzipped_data/stream_result/edges.tsv' 

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

@app2.callback(
    Output('root2', 'options'),
    [Input('buffer1', 'style')])

def num_clicks_compute(buffer):

	node_list_tmp = glob.glob('./unzipped_data/stream_result/S*' )

	node_list = [x.split('/')[-1] for x in node_list_tmp if len(x.split('/')[-1]) == 2]

	return [{'label': i, 'value': i} for i in node_list]

# @app2.callback(
#     Output('root2', 'value'),
#     [])

# def num_clicks_compute():

# 	json_entry = './unzipped_data/stream_result/%s.json' % ( )
# 	data = json.load(open(json_entry))

# 	return data['starting_node']

@app2.callback(
    Output('2d-subway2', 'figure'),
    [Input('root2', 'value'),
    ])

def num_clicks_compute(root, ):

	traces = []

	# try:

	cell_coords = './unzipped_data/stream_result/%s/subway_coord_cells.csv' % (root)
	path_coords = glob.glob('./unzipped_data/stream_result/%s/subway_coord_line*csv' % (root))

	cell_label = glob.glob('./unzipped_data/stream_result/cell_label.tsv.gz' )
	cell_label_colors = glob.glob('./unzipped_data/stream_result/cell_label_color.tsv.gz' )

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

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1
	elif len(cell_label_list) > 0 and len(cell_label_colors_dict) == 0:
		color_plot = 0.5

	edges = './unzipped_data/stream_result/edges.tsv' 
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
	# except:
	# 	pass

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
    Output('rainbow-plot2', 'src'),
    [Input('root2', 'value'),
    ])

def num_clicks_compute(root, ):

	try:

		rainbow_plot = './unzipped_data/stream_result/%s/stream_plot.png' % (root)
		rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(rainbow_plot_image)

	except:
		pass

############################# SINGLE GENE VISUALIZATION #############################

@app2.callback(
	Output('sg-plot-button2', 'children'),
	[Input('sg-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'

@app2.callback(
	Output('sg-plot-container2', 'style'),
	[Input('sg-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app2.callback(
    Output('sg-gene2', 'options'),
    [Input('buffer2', 'style')])

def num_clicks_compute(buffer):

	gene_list_tmp = glob.glob('./unzipped_data/stream_result/S0/stream_plot_*png' )

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('./unzipped_data/stream_result/gene_conversion.tsv', 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# return [{'label': i, 'value': i} for i in gene_list]

@app2.callback(
    Output('2d-subway-sg2', 'figure'),
    [
    Input('sg-gene2', 'value'),
    Input('root2', 'value')])

def compute_trajectories( gene, root):

	traces = []

	cell_coords = './unzipped_data/stream_result/%s/subway_coord_cells.csv' % (root)
	path_coords = glob.glob('./unzipped_data/stream_result/%s/subway_coord_line*csv' % (root))
	gene_coords = './unzipped_data/stream_result/%s/subway_coord_%s.csv' % (root, gene)

	cell_label = './unzipped_data/stream_result/cell_label.tsv.gz' 
	cell_label_colors = './unzipped_data/stream_result/cell_label_color.tsv.gz' 

	edges = './unzipped_data/stream_result/edges.tsv' 
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
    Output('sg-plot2', 'src'),
    [
    Input('sg-gene2', 'value'),
    Input('root2', 'value')])

def num_clicks_compute( gene, root):

	try:

		discovery_plot = './unzipped_data/stream_result/%s/stream_plot_%s.png' % (root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')
		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:

		pass

######################################## GENE DISCOVERY ########################################
@app2.callback(
	Output('discovery-plot-button2', 'children'),
	[Input('discovery-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'

@app2.callback(
	Output('discovery-plot-container2', 'style'),
	[Input('discovery-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app2.callback(
    Output('discovery-gene2', 'options'),
    [Input('buffer3', 'style')])

def num_clicks_compute(buffer):

	gene_list_tmp = glob.glob('./unzipped_data/stream_result/S0/stream_plot_*png' )

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('./unzipped_data/stream_result/gene_conversion.tsv', 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# return [{'label': i, 'value': i} for i in gene_list]

@app2.callback(
    Output('2d-subway-discovery2', 'figure'),
    [
    Input('root2', 'value'),
    Input('discovery-gene2', 'value')])

def compute_trajectories( root, gene):

	traces = []

	cell_coords = './unzipped_data/stream_result/%s/subway_coord_cells.csv' % (root)
	path_coords = glob.glob('./unzipped_data/stream_result/%s/subway_coord_line*csv' % (root))
	gene_coords = './unzipped_data/stream_result/%s/subway_coord_%s.csv' % (root, gene)

	cell_label = './unzipped_data/stream_result/cell_label.tsv.gz' 
	cell_label_colors = './unzipped_data/stream_result/cell_label_color.tsv.gz' 

	edges = './unzipped_data/stream_result/edges.tsv' 
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

@app2.callback(
    Output('discovery-plot2', 'src'),
    [Input('root2', 'value'),
    Input('discovery-gene2', 'value'),
    ])

def num_clicks_compute(root, gene, ):

	try:

		discovery_plot = './unzipped_data/stream_result/%s/stream_plot_%s.png' % (root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app2.callback(
    Output('de-branches2', 'options'),
    [Input('buffer4', 'style')])

def num_clicks_compute(buffer):

	combined_branches = []
	find_tables = glob.glob('./unzipped_data/stream_result/DE_Genes/*.tsv' )
	for table in find_tables:
		# branch1 = table.split(' and ')[0].split('greater_')[1]
		# branch2 = table.split(' and ')[1].strip('.tsv')

		branch1 = table.split(' and ')[0].split('_')[-2] + '_' + table.split(' and ')[0].split('_')[-1]
		branch2 = table.split(' and ')[1].strip('.tsv')

		combined_branch = branch1 + ' and ' + branch2

		if combined_branch not in combined_branches:
			combined_branches.append(combined_branch)

	return [{'label': i, 'value': i} for i in combined_branches]

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

@app2.callback(
	Output('discovery-table2', 'children'),
	[Input('de-slider2', 'value'),
	Input('de-branches2', 'value'),
	Input('de-direction2', 'value'),
	])

def update_table(slider, branches, direction, ):

	use_this_table = ''

	try:

		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		if direction == branch1:
			direction_classify = '_greater_'
		elif direction == branch2:
			direction_classify = '_less_'

		find_table = glob.glob('./unzipped_data/stream_result/DE_Genes/*.tsv' )
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

### GENE CORRELATION
@app2.callback(
	Output('correlation-plot-button2', 'children'),
	[Input('correlation-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(-) Show'

@app2.callback(
	Output('correlation-plot-container2', 'style'),
	[Input('correlation-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app2.callback(
    Output('correlation-gene2', 'options'),
    [Input('buffer5', 'style')])

def num_clicks_compute(buffer):

	gene_list_tmp = glob.glob('./unzipped_data/stream_result/S0/stream_plot_*png' )

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('./unzipped_data/stream_result/gene_conversion.tsv', 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# return [{'label': i, 'value': i} for i in gene_list]

@app2.callback(
    Output('2d-subway-correlation2', 'figure'),
    [
    Input('root2', 'value'),
    Input('correlation-gene2', 'value')])

def compute_trajectories( root, gene):

	traces = []

	cell_coords = './unzipped_data/stream_result/%s/subway_coord_cells.csv' % (root)
	path_coords = glob.glob('./unzipped_data/stream_result/%s/subway_coord_line*csv' % (root))
	gene_coords = './unzipped_data/stream_result/%s/subway_coord_%s.csv' % (root, gene)

	cell_label = './unzipped_data/stream_result/cell_label.tsv.gz' 
	cell_label_colors = './unzipped_data/stream_result/cell_label_color.tsv.gz' 

	edges = './unzipped_data/stream_result/edges.tsv' 
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
    Output('correlation-plot2', 'src'),
    [Input('root2', 'value'),
    Input('correlation-gene2', 'value'),
    ])

def num_clicks_compute(root, gene, ):

	try:

		discovery_plot = './unzipped_data/stream_result/%s/stream_plot_%s.png' % (root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app2.callback(
    Output('corr-branches2', 'options'),
    [Input('buffer6', 'style')])

def num_clicks_compute(buffer):

	branches = []
	find_tables = glob.glob('./unzipped_data/stream_result/transition_genes/*.tsv' )
	for table in find_tables:
		branch = table.split('_genes_')[1].strip('.tsv')

		if branch not in branches:
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
	Output('correlation-table2', 'children'),
	[Input('corr-slider2', 'value'),
	Input('corr-branches2', 'value'),
	])

def update_table(slider, branch, ):

	use_this_table = ''

	find_table = glob.glob('./unzipped_data/stream_result/transition_genes/*.tsv' )
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
    [Input('buffer7', 'style')])

def num_clicks_compute(buffer):

	gene_list_tmp = glob.glob('./unzipped_data/stream_result/S0/stream_plot_*png' )

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	gene_conversion_dict = {}
	with open('./unzipped_data/stream_result/gene_conversion.tsv', 'r') as f:
		next(f)
		for line in f:
			orig, new = line.split('\t')
			gene_conversion_dict[new.strip('\n')] = orig.strip('\n')

	return [{'label': gene_conversion_dict[i], 'value': i} for i in gene_list if i != 'False']

	# return [{'label': i, 'value': i} for i in gene_list]

@app2.callback(
    Output('2d-subway-leaf2', 'figure'),
    [
    Input('root2', 'value'),
    Input('leaf-gene2', 'value')])

def compute_trajectories( root, gene):

	traces = []

	cell_coords = './unzipped_data/stream_result/%s/subway_coord_cells.csv' % (root)
	path_coords = glob.glob('./unzipped_data/stream_result/%s/subway_coord_line*csv' % (root))
	gene_coords = './unzipped_data/stream_result/%s/subway_coord_%s.csv' % (root, gene)

	cell_label = './unzipped_data/stream_result/cell_label.tsv.gz' 
	cell_label_colors = './unzipped_data/stream_result/cell_label_color.tsv.gz' 

	edges = './unzipped_data/stream_result/edges.tsv' 
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
    [Input('root2', 'value'),
    Input('leaf-gene2', 'value'),
    ])

def num_clicks_compute(root, gene, ):

	try:

		discovery_plot = './unzipped_data/stream_result/%s/stream_plot_%s.png' % (root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read()).decode('ascii')

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app2.callback(
    Output('leaf-branches2', 'options'),
    [Input('buffer8', 'style')])

def num_clicks_compute(buffer):

	branches = []
	find_tables = glob.glob('./unzipped_data/stream_result/leaf_genes/*.tsv' )
	for table in find_tables:
		branch = table.split('_genes')[-1].strip('.tsv')

		if (branch not in branches) and (len(branch) > 0):
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
	Output('leaf-table2', 'children'),
	[Input('leaf-slider2', 'value'),
	Input('leaf-branches2', 'value'),
	])

def update_table(slider, branch, ):

	use_this_table = ''

	find_table = glob.glob('./unzipped_data/stream_result/leaf_genes/*.tsv' )
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

# DOWNLOAD PORTION

def main():
    # app2.run_server(debug = True, processes = 5, port = 9992, host = '0.0.0.0')
    app2.run_server(debug = True, port = 9992, host = '0.0.0.0')

if __name__ == '__main__':
	main()
