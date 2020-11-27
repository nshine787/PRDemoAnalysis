# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 18:52:09 2020

@author: Nathan
"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import re

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

class explore:
    def __init__(self, dbLocation, minPlayers = 50, ticketWinThreshold = 20):
        self.dbLocation = dbLocation
        self.minPlayers = minPlayers
        self.ticketWinThreshold = ticketWinThreshold
        self.df = self.readData()
        
    def readData(self):
        conn = sqlite3.connect(self.dbLocation)
        
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
        df = df.loc[(df['version'] != 'v1.5.5') & 
                (df['mode'].isin(['Advance & Secure','Insurgency']))
               ]
        df.loc[df['server'].str.startswith('PRTA.co'), 'server'] = 'PRTA.co'
        df.loc[df['server'].str.startswith('Gamma Group'), 'server'] = 'Gamma Group'
        df.loc[df['server'].str.startswith('[DIVSUL'), 'server'] = 'DIVSUL'
        df.loc[df['server'].str.startswith('PRSC'), 'server'] = 'DIVSUL'
        df.loc[df['server'].str.startswith('CSA'), 'server'] = 'CSA'
        df.loc[df['server'].str.startswith('=SF='), 'server'] = 'SF'
        df.loc[df['server'].str.startswith("'(SSG)"), 'server'] = 'SSG'
        
        df = df.loc[df['playerCount'] >= self.minPlayers]
        df['date'] = pd.to_datetime(df['date'])
        
        df['winningTeam'] = 0
        df.loc[df['ticketsTeam1'] == 0, 'winningTeam'] = 2
        df.loc[df['ticketsTeam2'] == 0, 'winningTeam'] = 1
        
        df.loc[(df['winningTeam'] == 0) &
               (df['mode'] != 'Insurgency') &
               (df['ticketsTeam1'] <= self.ticketWinThreshold) &
               (df['ticketsTeam2'] >= self.ticketWinThreshold),
               'winningTeam'] = 2
        df.loc[(df['winningTeam'] == 0) &
               (df['mode'] != 'Insurgency') &
               (df['ticketsTeam1'] >= self.ticketWinThreshold) &
               (df['ticketsTeam2'] <= self.ticketWinThreshold),
               'winningTeam'] = 1
        
        df.loc[(df['winningTeam'] == 0) &
               (df['mode'] == 'Insurgency') &
               (df['ticketsTeam1'] >= 1) &
               (df['ticketsTeam2'] <= self.ticketWinThreshold),
               'winningTeam'] = 1
        df = df.loc[df['winningTeam'] > 0]
        
        df['winningTickets'] = 0
        df['winningTeamName'] = ''
        team2df = df.loc[df['winningTeam'] == 2]
        team1df = df.loc[df['winningTeam'] == 1]
        df.loc[df['winningTeam'] == 2, ['winningTeamName','winningTickets']] = team2df[['team2','ticketsTeam2']].values
        df.loc[df['winningTeam'] == 1, ['winningTeamName','winningTickets']] = team1df[['team1','ticketsTeam1']].values
        
        return df    

    def describeMap(self, mapName, mode='Advance & Secure', layer='Standard'):
        testdf = self.df.loc[(self.df['map'] == mapName) & 
                        (self.df['mode'] == mode) & 
                        (self.df['layer'] == layer), ['playerCount', 'ticketsTeam1', 'ticketsTeam2','duration','winningTeam','team1','team2']]
        
        testdf['winningTickets'] = 0
        testdf['winningTeamName'] = ''
        team2df = testdf.loc[testdf['winningTeam'] == 2]
        team1df = testdf.loc[testdf['winningTeam'] == 1]
        testdf.loc[testdf['winningTeam'] == 2, ['winningTeamName','winningTickets']] = team2df[['team2','ticketsTeam2']].values
        testdf.loc[testdf['winningTeam'] == 1, ['winningTeamName','winningTickets']] = team1df[['team1','ticketsTeam1']].values
        if testdf['team1'].iloc[0] > testdf['team2'].iloc[0]:
            colors = ['blue','red']
        else:
            colors = ['red','blue']
        testdf = testdf[['playerCount','duration','winningTickets','winningTeamName']]    
        
        testdf = testdf.query('winningTeamName != ""')
        fig, ax_new = plt.subplots(1,4,figsize=(12,6))
    
        bp_dict = testdf.boxplot(
            by="winningTeamName",ax=ax_new[:3],
            color = dict(boxes='black', whiskers='black', medians='black', caps='black'),
            return_type='both',
            patch_artist = True,
            widths=0.5,
            boxprops= dict(linewidth=1.5, color='black'),
            medianprops = dict(linestyle='-', linewidth=2.5, color='darkgoldenrod'),
            whiskerprops=dict(linestyle='-',linewidth=1.25, color='black')
        )
        for row_key, (ax,row) in bp_dict.iteritems():
            ax.set_xlabel('')
            for i,box in enumerate(row['boxes']):
                box.set_facecolor(colors[i])
                
            winningTeamCounts = pd.value_counts(testdf['winningTeamName'].values, sort=True)
            
        indexToPass = winningTeamCounts.index
        valuesToPass = winningTeamCounts.values
        if winningTeamCounts.index[1] < winningTeamCounts.index[0]:
            indexToPass = winningTeamCounts.index.sort_values()
            temp = valuesToPass[0]
            valuesToPass[0] = valuesToPass[1]
            valuesToPass[1] = temp
            
        ax_new[3].bar(indexToPass, valuesToPass, color=colors, edgecolor='black', linewidth='1.5')   
        
        mapNameFormatted = formatMapName(mapName)          
        fig.suptitle(f'{mapNameFormatted} - {mode} - {layer}')                
        ax_new[0].set_title('Match Length (min)')
        ax_new[1].set_title('Player Count')
        ax_new[2].set_title('Remaining Tickets of the Winner')
        ax_new[3].set_title('Total Wins')
        
        plt.show()

    def showTop(self,N=5):
        topMaps = self.df.groupby(['map','mode','layer']).count()['date'].sort_values(ascending=False).iloc[:N].index.values
        opforWins = []
        bluforWins = []
        for i in range(N):
            validRounds = self.df.loc[self.df[['map','mode','layer']].isin(topMaps[i]).all(axis=1)]
            opforWins.append(sum(validRounds['winningTeam'] == 1))
            bluforWins.append(sum(validRounds['winningTeam'] == 2))
    
        ind = np.arange(N)
        width = 0.35
        p1 = plt.bar(ind, opforWins, width, color='red', edgecolor='black', linewidth='1.5')
        p2 = plt.bar(ind, bluforWins, width, color='blue', edgecolor='black', linewidth='1.5',
                 bottom=opforWins)
        plt.title(f'Top {N} Played PR Maps')
        plt.ylabel('Number of Rounds')
        plt.xticks(ind, shortAll(topMaps))
        plt.legend((p1[0], p2[0]), ('Opfor', 'Blufor'))
        plt.show()

# ex = explore('pr.db')
# ex.describeMap('assault_on_grozny')