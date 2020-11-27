# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import clean_up
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly
from dash.dependencies import Input, Output
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = clean_up.explore('pr.db').df

unformattedMapNames = np.sort(df['map'].unique())
formattedMapNames = [clean_up.formatMapName(mapName) for mapName in unformattedMapNames]

mapOptions = []
for i in range(len(unformattedMapNames)):
    mapOptions.append(dict(label = formattedMapNames[i], value = unformattedMapNames[i]))

allMapModes = {name : df.loc[df['map'] == name,'mode'].unique()  for name in unformattedMapNames}
allLayers = {}
for mapName, mapModes in allMapModes.items():
    for mapMode in mapModes:
        allLayers[(mapName,mapMode)] = df.loc[(df['map'] == mapName) & (df['mode'] == mapMode),'layer'].unique()

app.layout = html.Div([
    dcc.Graph(id='top-maps'),
    dcc.Slider(
        id='top-slider',
        min=1,
        max=40,
        value=10,
        step=1
    ),
    dcc.Graph(id='describe-map'),
    dcc.Dropdown(
        id='describe-dropdown',
        options=mapOptions,
        value='muttrah_city_2',
        clearable=False
    ),
    dcc.Dropdown(
        id='describe-dropdown-mode',
        value = 'Advance & Secure'
        ),
    dcc.Dropdown(
        id='describe-dropdown-layer',
        value = 'Standard'
        )
])

@app.callback(
    Output(component_id='top-maps', component_property='figure'),
    Input(component_id='top-slider', component_property='value')
)
def updateTopMaps(value):
    N = value
    topMaps = df.groupby(['map','mode','layer']).count()['date'].sort_values(ascending=False).iloc[:N].index.values
    
    labels = clean_up.shortAll(topMaps)
    opforWins = []
    bluforWins = []
    for i in range(N):
        validRounds = df.loc[df[['map','mode','layer']].isin(topMaps[i]).all(axis=1)]
        opforWins.append(sum(validRounds['winningTeam'] == 1))
        bluforWins.append(sum(validRounds['winningTeam'] == 2))
        
    fig = go.Figure(data=[
        go.Bar(name='opfor', x=labels, y=opforWins, marker_color='red'),
        go.Bar(name='blufor', x=labels, y=bluforWins, marker_color='blue')
    ])
    titleText = f'Top {value} Played PR Maps (1.6.x)'
    fig.update_layout(title_text = titleText, barmode='stack')
    return fig

@app.callback(
    Output(component_id='describe-dropdown-mode', component_property='options'),
    Input(component_id='describe-dropdown', component_property='value')
)
def updateModeDropdown(mapName):
    modes = df.loc[df['map'] == mapName,'mode'].unique()
    modesList = [{'label': k, 'value': k} for k in modes]
    return modesList

@app.callback(
    Output(component_id='describe-dropdown-mode',
            component_property='value'),
    Input(component_id='describe-dropdown-mode', component_property='options')
    )
def setModeValue(modeChosen):
    return modeChosen[0]['value']

@app.callback(
    Output(component_id='describe-dropdown-layer', component_property='options'),
    Input(component_id='describe-dropdown', component_property='value'),
    Input(component_id='describe-dropdown-mode', component_property='value')
)
def updateLayerDropdown(mapName,modeName):
    layers = df.loc[(df['map'] == mapName) & (df['mode'] == modeName),'layer'].unique()
    return [{'label': k, 'value': k} for k in layers]

@app.callback(
    Output(component_id='describe-dropdown-layer',
            component_property='value'),
    Input(component_id='describe-dropdown-layer', component_property='options')
    )
def setLayerValue(layerChosen):
    return 'Standard'

@app.callback(
    Output(component_id='describe-map', component_property='figure'),
    Input(component_id = 'describe-dropdown', component_property='value'),
    Input(component_id='describe-dropdown-mode', component_property='value'),
    Input(component_id='describe-dropdown-layer', component_property='value')
)
def updateDescribeMap(mapName, mode, layer):
    cols = plotly.colors.DEFAULT_PLOTLY_COLORS
    fig = make_subplots(rows=1, cols=4,
                        subplot_titles=('Match Length (min)','Remaining Tickets of the Winner','Player Count',''))
    testdf = df.loc[(df['map'] == mapName) & 
                        (df['mode'] == mode) & 
                        (df['layer'] == layer), ['playerCount','winningTeam','duration','winningTeamName', 'winningTickets']]
    team1Wins = testdf.loc[testdf['winningTeam']==1]
    team2Wins = testdf.loc[testdf['winningTeam']==2]
    
    trace0, trace1, trace2, trace3, trace4, trace5 = go.Box(),go.Box(),go.Box(),go.Box(),go.Box(),go.Box()
    
    team2HasWins = True
    if len(team2Wins) > 0:
        trace0 = go.Box(y=team2Wins['duration'],
                        name=f'{team2Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[0]))
        trace2 = go.Box(y=team2Wins['winningTickets'],
                        name=f'{team2Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[0]), showlegend=False)
        trace4 = go.Box(y=team2Wins['playerCount'],
                        name=f'{team2Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[0]), showlegend=False)
    else:
        team2Wins = False
    
    team1HasWins = True    
    if len(team1Wins) > 0:
        trace1 = go.Box(y=team1Wins['duration'],
                        name=f'{team1Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[3]))
        trace3 = go.Box(y=team1Wins['winningTickets'],
                        name=f'{team1Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[3]), showlegend=False)
        trace5 = go.Box(y=team1Wins['playerCount'],
                        name=f'{team1Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[3]), showlegend=False)
    else:
        team1HasWins = False
        
    winningTeamCounts = pd.value_counts(testdf['winningTeamName'].values, sort=True)
    if sum(testdf['winningTeam'] == 1) > sum(testdf['winningTeam'] == 2):
        winningTeamCounts = winningTeamCounts[::-1]
    trace6 = go.Bar(x=winningTeamCounts.index, y=winningTeamCounts.values,
                    marker_color=[cols[0],cols[3]],
                    showlegend=False)
    if team2HasWins:
        fig.add_trace(trace0,row=1,col=1)
        fig.add_trace(trace2,row=1,col=2)
        fig.add_trace(trace4,row=1,col=3)
    
    if team1HasWins:
        fig.add_trace(trace1,row=1,col=1)
        fig.add_trace(trace3,row=1,col=2)
        fig.add_trace(trace5,row=1,col=3)
    fig.add_trace(trace6,row=1,col=4)
    titleText = f'Winner Statistics: {clean_up.formatMapName(mapName)} - {mode} - {layer}'
    fig.update_layout(title_text = titleText)    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)