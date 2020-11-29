# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly
from dash.dependencies import Input, Output
import numpy as np
import re
import sqlite3

def formatMapName(mapName):
    uniqueMapNames = {
        'hill_488' : 'Hill 488',
        'iron_thunder': 'Operation Thunder',
        'jabal': 'Jabal Al Burj',
        'op_barracuda': 'Operation Barracuda',
        'route': 'Route E-106'
        }
    if mapName in uniqueMapNames:
        formattedMapName = uniqueMapNames[mapName]
    else:
        nonCapitalizedWords = ['on','of','el']
        mapName = re.sub('\d', '',mapName)
        formattedMapWords = []
        for word in mapName.split('_'):
            if len(word) > 0:
                newWord = (word[0].upper() + word[1:]) if word not in nonCapitalizedWords else word
                formattedMapWords.append(newWord)
        formattedMapName = ' '.join(formattedMapWords)
    return formattedMapName

def shortMode(mode):
    shortModes = {'Advance & Secure': 'AAS',
                 'Insurgency': 'Ins'}
    return shortModes[mode]

def shortLayer(layer):
    shortLayers = {'Standard': 'Std',
                   'Alternative': 'Alt',
                   'Infantry': 'Inf',
                   'Large': 'Lrg'}
    return shortLayers[layer]

def shortAll(mapList):
    returnText = []
    for entry in mapList:
        returnText.append(formatMapName(entry[0]) + '\n' + shortMode(entry[1]) + '\n' + shortLayer(entry[2]))
    return returnText

def readData(dbLocation, minPlayers = 50, ticketWinThreshold = 20):
    conn = sqlite3.connect(dbLocation)
    
    df = pd.read_sql_query('SELECT * FROM demos;',conn)
    conn.close()
    
    
    mapTeams = pd.read_csv('map_modes_tickets.csv')
    mapTeams.dropna(inplace=True)
    mapTeams['startingTickets1'] = mapTeams['startingTickets1'].astype(int)
    mapTeams['startingTickets2'] = mapTeams['startingTickets2'].astype(int)
    layerNames = {
        'Layer 64' : 'Standard',
        'Layer 32' : 'Alternative',
        'Layer 16' : 'Infantry',
        'Layer 128': 'Large'
    }
    df.replace({'layer':layerNames},inplace=True)
    df = pd.merge(df,mapTeams, how='left',left_on=['map','mode','layer'],right_on=['map','mode','layer'])
    df = df.loc[(df['mode'].isin(['Advance & Secure','Insurgency']))               ]
    df.loc[df['server'].str.startswith('PRTA.co'), 'server'] = 'PRTA.co'
    df.loc[df['server'].str.startswith('Gamma Group'), 'server'] = 'Gamma Group'
    df.loc[df['server'].str.startswith('[DIVSUL'), 'server'] = 'DIVSUL'
    df.loc[df['server'].str.startswith('PRSC'), 'server'] = 'DIVSUL'
    df.loc[df['server'].str.startswith('CSA'), 'server'] = 'CSA'
    df.loc[df['server'].str.startswith('=SF='), 'server'] = 'SF'
    df.loc[df['server'].str.startswith("'(SSG)"), 'server'] = 'SSG'
    
    df = df.loc[df['playerCount'] >= minPlayers]
    df['date'] = pd.to_datetime(df['date'])
    
    df['winningTeam'] = 0
    df.loc[df['ticketsTeam1'] == 0, 'winningTeam'] = 2
    df.loc[df['ticketsTeam2'] == 0, 'winningTeam'] = 1
    
    df.loc[(df['winningTeam'] == 0) &
           (df['mode'] != 'Insurgency') &
           (df['ticketsTeam1'] <= ticketWinThreshold) &
           (df['ticketsTeam2'] >= ticketWinThreshold),
           'winningTeam'] = 2
    df.loc[(df['winningTeam'] == 0) &
           (df['mode'] != 'Insurgency') &
           (df['ticketsTeam1'] >= ticketWinThreshold) &
           (df['ticketsTeam2'] <= ticketWinThreshold),
           'winningTeam'] = 1
    
    df.loc[(df['winningTeam'] == 0) &
           (df['mode'] == 'Insurgency') &
           (df['ticketsTeam1'] >= 1) &
           (df['ticketsTeam2'] <= ticketWinThreshold),
           'winningTeam'] = 1
    df = df.loc[df['winningTeam'] > 0]
    
    df['winningTickets'] = 0
    df['winningTeamName'] = ''
    team2df = df.loc[df['winningTeam'] == 2]
    team1df = df.loc[df['winningTeam'] == 1]
    df.loc[df['winningTeam'] == 2, ['winningTeamName','winningTickets']] = team2df[['team2','ticketsTeam2']].values
    df.loc[df['winningTeam'] == 1, ['winningTeamName','winningTickets']] = team1df[['team1','ticketsTeam1']].values
    return df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

all_df = readData('pr.db')
df = all_df
unformattedMapNames = np.sort(df['map'].unique())
formattedMapNames = [formatMapName(mapName) for mapName in unformattedMapNames]

versionOptions = [{'label':version,'value':version}for version in np.sort(all_df['version'].unique())]
mapOptions = []
for i in range(len(unformattedMapNames)):
    mapOptions.append(dict(label = formattedMapNames[i], value = unformattedMapNames[i]))

app.layout = html.Div([
    dcc.Graph(id='top-maps'),
    dcc.Slider(
        id='top-slider',
        min=1,
        max=40,
        value=10,
        step=1
    ),
    dcc.Checklist(id='version-chklst',
              options = versionOptions,
              value = [version['value'] for version in versionOptions],
              labelStyle = {'display': 'inline-block'}
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
    Input(component_id='top-slider', component_property='value'),
    Input(component_id='version-chklst', component_property='value')
)
def updateTopMaps(N, version):
    dfVersions = df.loc[df['version'].isin(version)]
    topMaps = dfVersions.groupby(['map','mode','layer']).count()['date'].sort_values(ascending=False).iloc[:N].index.values
    
    labels = shortAll(topMaps)
    opforWins = []
    bluforWins = []
    for i in range(N):
        validRounds = dfVersions.loc[dfVersions[['map','mode','layer']].isin(topMaps[i]).all(axis=1)]
        opforWins.append(sum(validRounds['winningTeam'] == 1))
        bluforWins.append(sum(validRounds['winningTeam'] == 2))
        
    fig = go.Figure(data=[
        go.Bar(name='opfor', x=labels, y=opforWins, marker_color='red'),
        go.Bar(name='blufor', x=labels, y=bluforWins, marker_color='blue')
    ])
    titleText = f'Top {N} Played PR Maps'
    fig.update_layout(title_text = titleText, barmode='stack')
    return fig

@app.callback(
    Output(component_id='describe-dropdown', component_property='options'),
    Input(component_id='version-chklst', component_property='value'))
def updateMaps(versionList):
    dfVersions = df.loc[df['version'].isin(versionList)]
    return [{'label':formatMapName(mapName), 'value':mapName} for mapName in np.sort(dfVersions['map'].unique())]

@app.callback(
    Output(component_id='describe-dropdown-mode', component_property='options'),
    Input(component_id='describe-dropdown', component_property='value'),
    Input(component_id='version-chklst', component_property='value')
)
def updateModeDropdown(mapName, versionList):
    dfVersions = df.loc[df['version'].isin(versionList)]
    modes = dfVersions.loc[dfVersions['map'] == mapName,'mode'].unique()
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
    Input(component_id='describe-dropdown-mode', component_property='value'),
    Input(component_id='version-chklst', component_property='value')
)
def updateLayerDropdown(mapName,modeName, versionList):
    dfVersions = df.loc[df['version'].isin(versionList)]
    layers = dfVersions.loc[(dfVersions['map'] == mapName) & 
                            (dfVersions['mode'] == modeName),'layer'].unique()
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
    Input(component_id='describe-dropdown-layer', component_property='value'),
    Input(component_id='version-chklst', component_property='value')
)
def updateDescribeMap(mapName, mode, layer, versionList):
    cols = plotly.colors.DEFAULT_PLOTLY_COLORS
    fig = make_subplots(rows=1, cols=4,
                        subplot_titles=('Match Length (min)','Remaining Tickets of the Winner','Player Count',''))
    testdf = df.loc[(df['map'] == mapName) & 
                        (df['mode'] == mode) & 
                        (df['layer'] == layer) &
                        (df['version'].isin(versionList)), ['playerCount','winningTeam','duration','winningTeamName', 'winningTickets']]
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
    team1WinTickets = team1Wins['winningTickets']
    if mode == 'Insurgency':
        team1WinTickets = 100 * team1WinTickets
    if len(team1Wins) > 0:
        trace1 = go.Box(y=team1Wins['duration'],
                        name=f'{team1Wins["winningTeamName"].iloc[0]}',
                        line=dict(width=2, color=cols[3]))
        trace3 = go.Box(y=team1WinTickets,
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
    markerColors = [cols[0],cols[3]]
    if sum(testdf['winningTeam'] == 2) == 0:
        markerColors = [cols[3]]
    trace6 = go.Bar(x=winningTeamCounts.index, y=winningTeamCounts.values,
                    marker_color=markerColors,
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
    titleText = f'Winner Statistics: {formatMapName(mapName)} - {mode} - {layer}'
    fig.update_layout(title_text = titleText)    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)