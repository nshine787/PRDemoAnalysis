# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 15:17:26 2020

@author: Nathan
"""
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import clean_up
import plotly.offline as pyo
import pandas as pd

pio.renderers.default='browser'

df = clean_up.explore('pr.db').df

# N = 10
# topMaps = df.groupby(['map','mode','layer']).count()['date'].sort_values(ascending=False).iloc[:N].index.values

# labels = clean_up.shortAll(topMaps)
# opforWins = []
# bluforWins = []
# for i in range(N):
#     validRounds = df.loc[df[['map','mode','layer']].isin(topMaps[i]).all(axis=1)]
#     opforWins.append(sum(validRounds['winningTeam'] == 1))
#     bluforWins.append(sum(validRounds['winningTeam'] == 2))
    
# fig = go.Figure(data=[
#     go.Bar(name='opfor', x=labels, y=opforWins, marker_color='red'),
#     go.Bar(name='blufor', x=labels, y=bluforWins, marker_color='blue')
# ])

# titleText = f'Top {N} Played PR Maps'
# fig.update_layout(title_text = titleText, barmode='stack')
# fig.show()

mapName = 'korengal'
mode = 'Advance & Secure'
layer = 'Standard'
testdf = df.loc[(df['map'] == mapName) & 
                        (df['mode'] == mode) & 
                        (df['layer'] == layer), ['playerCount','winningTeam','duration','winningTeamName', 'winningTickets']]

from plotly.subplots import make_subplots
import plotly
cols = plotly.colors.DEFAULT_PLOTLY_COLORS
fig = make_subplots(rows=1, cols=4,
                    subplot_titles=('Match Length (min)','Remaining Tickets of the Winner','Player Count',''))

team1Wins = testdf.loc[testdf['winningTeam']==1]
team2Wins = testdf.loc[testdf['winningTeam']==2]

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
    
pyo.plot(fig)