from analyz import *
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from io import BytesIO
import base64

import flask

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = flask.Flask(__name__)
dash_app = dash.Dash(__name__, server=app, external_stylesheets=external_stylesheets)

# ------------------------------------------------------------------------------
# Menyiapkan data yang telah bersih
chatdf = cleanData('PUT YOUR WHATSAPP CHAT TXT FILE HERE!') # Example: Chat whatsapp grup tkj a.txt

ppList = [{'label': i, 'value': i} for i in chatdf['author'].unique()]

# ------------------------------------------------------------------------------
# App layout
colors = {
		'main-background': '#3a6351', 
		'background': '#9ecca4',
		'background-2': '#f1f1e8', 
		'text': '#1c1427', 
		'text-2': '#cee5d1', 
		'line': '#382933'}

dash_app.layout = html.Div(style={'backgroundColor': colors['main-background']}, children=[
	html.Div(
		id='banner', 
		children=[
			html.H1(
				id='title', 
				children="What'slytic App", 
				style={'margin': 20, 'color': colors['text']}
				)
			],
		style={'height' : '4%', 
			   'background-color' : colors['background'], 
			   'border-block-end': '1rem solid', 
			   'writing-mode': 'horizontal-tb'}, 
		className='row'
	), 

	html.Div(children=[
		html.Center(children=[
			dcc.Dropdown(
				id='slct-ppl', 
				options=ppList, 
				value=ppList[1]['value'], 
				style={'margin': 20, 'width': '80%', 'color': colors['text']}
				)
			] 
		)
		], 
		className='row'
	),

	html.Div(children=[
		html.Div(children=[
			dcc.Dropdown(
				id='slct-time', 
				options=[{'label': 'Hour', 'value': 'hour'}, 
						 {'label': 'Day', 'value': 'day'}, 
						 {'label': 'Month', 'value': 'month'}, 
						 {'label': 'Year', 'value': 'year'}], 
				value='hour', 
				style={'margin': 20, 'width': '60%'}
				)], 
			style={'display': 'inline-block', 
				   'vertical-align': 'top', 
				   'margin-left': '3vw', 
				   'margin-top': '3vw'}), 

		html.Div(children=[
			html.Center(children=[
				dcc.Graph(
					id='message-tseries', 
					figure={'layout': dict(width=758, height=512)}
						), 
					]
				)], 
			style={'display': 'inline-block', 
				   'margin-left': '3vw', 
				   'margin-top': '3vw'})
		], 
		className='row'
	), 

	html.Div(children=[
		html.Div(children=[
			dcc.Graph(
				id='emoji-barh', 
				figure={'layout': dict(width=512, height=1024)})
			], 
			style={'display': 'inline-block', 
				   'margin-left': '3vw', 
				   'margin-top': '3vw'}
		), 

		html.Div(children=[
			dcc.Markdown(
				id='small-summary', 
				children=[], 
				style={'margin': 20, 'color': colors['text-2']}), 
			dcc.Graph(
				id='more-table', 
				figure={'layout': dict(width=512, height=384)})
			], 
			style={'display': 'inline-block', 
				   'vertical-align': 'top', 
				   'margin-left': '3vw', 
				   'margin-top': '3vw'}
		)], 
		className='row'
	), 

	html.Center(children=[
		html.H3(
			id='title-word-cloud', 
			children="Distribution of used Word", 
			style={'margin': 20, 'color': colors['text-2']}
		), 
		html.Img(
			id='word-cloud', 
			style={'margin': 20}
		)]
	), 

	html.Br()
])


# ------------------------------------------------------------------------------
# MengKoneksikan objek Plotly dan objek Visualisasi lainnya 
# dengan komponen-komponen dash
@dash_app.callback(
	[Output(component_id='message-tseries', component_property='figure'), 
	Output(component_id='emoji-barh', component_property='figure'), 
	Output(component_id='small-summary', component_property='children'), 
	Output(component_id='more-table', component_property='figure'), 
	Output(component_id='word-cloud', component_property='src')], 
	[Input(component_id='slct-ppl', component_property='value'), 
	Input(component_id='slct-time', component_property='value')]
	# Input() terkoneksi dengan setiap parameter pada fungsi update_graph().
	# Output() terkoneksi dengan setiap return output pada fungsi update_graph().
)

def update_graph(slct_ppl, slct_time):
	# --- Mendapatkan Profil lengkap seseorang
	df = getProfile(chatdf, slct_ppl)



	# --- Plotly 'message-tseries' time series plot line
	dftSeries = getTimeSeriesMessage(df['MessageSent'], [slct_time])
	tSeries = go.Figure()
	tSeries.add_trace(
		go.Scatter(x=dftSeries.index, y=dftSeries.values, mode='lines+markers', 
				   line_color=colors['line'], line_shape='spline', 
				   hovertemplate=slct_time+' %{x} <br> Message Count: %{y} </br>')
	)

	tSeries.update_layout(
					title=f'Tren of Message Count Per-{slct_time}', 
					title_font_size=28, 
					xaxis_title=slct_time, 
					yaxis_title='Message Count',
					plot_bgcolor=colors['background'], 
					paper_bgcolor=colors['background'], 
					font_color=colors['text'], 
					showlegend= False)



	# --- Plotly 'top-emoji used' dalam bar chart
	dfEmojiBar = df['EmojiUsed']
	EmojiBar = go.Figure()
	EmojiBar.add_trace(
		go.Bar(x=dfEmojiBar.values, y=dfEmojiBar.index, orientation='h', 
			   hovertemplate='Emoji %{y} <br> Used Count: %{x} </br>')
	)

	EmojiBar.update_traces(marker_color=colors['main-background'], 
						   marker_line_width=1.5, opacity=0.8)

	EmojiBar.update_layout(
					title=f'Top Emoji Used', 
					title_font_size=28, 
					plot_bgcolor=colors['background'], 
					paper_bgcolor=colors['background'], 
					font_color=colors['text'], 
					showlegend= False)



	# --- Ringkasan singkat dalam penulisan Markdown
	summary = []
	# Menambahkan info-info tambahan
	summary.append(f"Active Rank: **{df['ActiveRank']}**")
	actDateStr = map(str, df['ActiveDate'])
	summary.append(f"Active Date: **{' - '.join(actDateStr)}**")
	summary.append(f"Total Media Sent: **{len(df['MediaSent'])}**")
	summary.append(f"Total Deleted Message: **{len(df['MessageDel'])}**")
	summary = '\n\n'.join(summary)



	# --- Plotly 'Tables' Chart
	headerColor = colors['main-background']
	rowEvenColor = '#9ecca4'
	rowOddColor = '#cee5d1'

	figTable = make_subplots(
	    rows=3, cols=1,
	    specs=[[{'type': 'table'}], [{'type': 'table'}], [{'type': 'table'}]], 
	    subplot_titles=('Asked Message', 'Tag Message', 'Link Message')
	    )

	# Tabel untuk menunjukkan pertanyaan yang pernah disampaikan
	dataAsk = df['MessageAsk']
	figTable.add_trace(
		go.Table(header=dict(values=['date', 'message'], 
							 fill_color=headerColor,
							 font_color=colors['text-2']), 
				 cells=dict(values=[dataAsk['date'], dataAsk['messages']], 
				 fill_color=[[rowOddColor, rowEvenColor] * len(dataAsk)])
				 ), 
		row=1, col=1
	)

	# Tabel untuk menunjukkan tag pada seseorang di grup yang pernah dibuat
	dataTag = df['MessageTag']
	figTable.add_trace(
		go.Table(header=dict(values=['date', 'message'], 
							 fill_color=headerColor,
							 font_color=colors['text-2']),
				 cells=dict(values=[dataTag['date'], dataTag['messages']], 
				 fill_color=[[rowOddColor, rowEvenColor] * len(dataTag)]), 
				 ), 
		row=2, col=1
	)

	# Tabel untuk menunjukkan link yang pernah dikirimkan
	dataLink = df['LinkSent']
	figTable.add_trace(
		go.Table(header=dict(values=['date', 'message'], 
							 fill_color=headerColor,
							 font_color=colors['text-2']),
				 cells=dict(values=[dataLink['date'], dataLink['messages']], 
				 fill_color=[[rowOddColor, rowEvenColor] * len(dataLink)]), 
				 ), 
		row=3, col=1
	)

	figTable.update_layout(
					paper_bgcolor=colors['main-background'], 
					font_color=colors['text'], 
					width=512,
    				height=866, 
					showlegend=False)



	# --- Membuat WordCloud
	imgwc = BytesIO()
	wc = getWordCloud(df['MessageSent']['messages'])
	wc.save(imgwc, format='PNG')
	imgwc = 'data:image/png;base64,{}'.format(base64.b64encode(imgwc.getvalue()).decode())


	return tSeries, EmojiBar, summary, figTable, imgwc


# ------------------------------------------------------------------------------
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, port=80)
