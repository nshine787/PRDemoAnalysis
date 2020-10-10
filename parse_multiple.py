# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 17:09:08 2020

@author: Nathan
"""
import helper_functions as hf
import parse_one
import multiprocessing as mp
import os
import time
import sqlite3
from datetime import datetime

def insertDemo(cursor, d):
    readableDate = datetime.fromtimestamp(d.date).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''INSERT INTO demos VALUES(:date, :server, :map, :mode, :layer, :playerCount, 
              :ticketsTeam1, :ticketsTeam2, :version, :duration)''', 
    {'date':readableDate, 'server':d.serverName, 'map':d.map, 'mode':d.gameMode, 'layer':d.layer, 'playerCount':d.playerCount, 'ticketsTeam1':d.ticketsTeam1, 'ticketsTeam2':d.ticketsTeam2,'version':d.version, 'duration':round(d.duration,0)})

def main():
    didOne = False
    demosLocation = 'C:\\Users\\Nathan\\Desktop\\PetProjects\\ProjectReality\\demos'
    errors = 0
    
    demoLocations = []
    for subdir, dirs, files in os.walk(demosLocation):
        demoLocations = [os.path.join(subdir,filename) for filename in files]
    
    
    '''
    Use multiprocessing to speed up parsing
    '''
    start = time.time()
    results = []
    with mp.Pool(processes=mp.cpu_count()) as pool:
        parsedDemos = pool.map_async(parse_one.parseNewDemo, demoLocations)
        while (True):
            hf.update_progress(len(demoLocations) - parsedDemos._number_left,len(demoLocations))
            time.sleep(0.5)
            if (parsedDemos.ready()): break
        parsedDemos.wait()
        hf.update_progress(len(demoLocations), len(demoLocations))
        try:
            results = parsedDemos.get()
        except Exception as e:
            print(e)
    finish = time.time()
    print(f' Finished parsing in {round((finish-start),2)} second(s)')
    
    '''
    test one at a time parsed
    '''
    # bad_result = 'C:\\Users\\Nathan\\Desktop\\PetProjects\\ProjectReality\\demos\\tracker_2020_07_20_15_01_52_masirah_gpm_skirmish_16.PRdemo'
    # results = []
    # results.append(parse_one.parseNewDemo(demoLocations[0]))
    # results.append(parse_one.parseNewDemo(demoLocations[1]))
    # results.append(parse_one.parseNewDemo(bad_result))

    
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('''CREATE TABLE demos (
                date DATE,
                server TEXT,
                map TEXT,
                mode TEXT,
                layer TEXT,
                playerCount INT,
                ticketsTeam1 INT,
                ticketsTeam2 INT,
                version TEXT,
                duration INT,
                PRIMARY KEY(date, server)
        )''')
    conn.commit()    
    
    for result in results:
        if result.serverName != 0:
            insertDemo(c, result)

    c.execute('SELECT * FROM demos ORDER BY date LIMIT 10')
    firstN = c.fetchall()
    for row in firstN:
        print(row, '\n')
    c.execute("SELECT COUNT(*) FROM demos WHERE server <> '0'")
    print(c.fetchall())
    
    c.execute("SELECT map, COUNT(map) FROM demos GROUP BY map ORDER BY COUNT(map)")
    print('\n'.join(' '.join(map(str,row)) for row in c.fetchall()))
    
    print('end')
if __name__ == '__main__':
    main()