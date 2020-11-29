# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 17:09:08 2020

@author: Nathan
"""
import parse_one
import multiprocessing as mp
import os
import sys
import time
import sqlite3
from datetime import datetime

def update_progress(currentCount,totalCount):
    barLength = 20
    progress = float(currentCount) / totalCount
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
    block = int(round(barLength*progress))
    text = "\r[{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100,2), " (" + str(currentCount) + "/" + str(totalCount) + ")")
    sys.stdout.write(text)
    sys.stdout.flush()

def insertDemo(cursor, d):
    readableDate = datetime.fromtimestamp(d.date).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''INSERT INTO demos VALUES(:date, :server, :map, :mode, :layer, :playerCount, 
              :ticketsTeam1, :ticketsTeam2, :version, :duration)''', 
    {'date':readableDate, 'server':d.serverName, 'map':d.map, 'mode':d.gameMode, 'layer':d.layer, 'playerCount':d.playerCount, 'ticketsTeam1':d.ticketsTeam1, 'ticketsTeam2':d.ticketsTeam2,'version':d.version, 'duration':round(d.duration,0)})

class StatsParser:
    def __init__(self,demosLocation = './demos', dbLocation = 'pr.db'):
        self.demosLocation = demosLocation
        self.dbLocation = dbLocation
        self.parsedDemos = self.parallelParse()
        
    def parallelParse(self):
        demoLocations = []
        for subdir, dirs, files in os.walk(self.demosLocation):
            demoLocations = [os.path.join(subdir,filename) for filename in files]
        start = time.time()
        results = []
        with mp.Pool(processes=mp.cpu_count()) as pool:
            parsedDemos = pool.map_async(parse_one.parseNewDemo, demoLocations)
            while (True):
                update_progress(len(demoLocations) - parsedDemos._number_left,len(demoLocations))
                time.sleep(0.5)
                if (parsedDemos.ready()): break
            parsedDemos.wait()
            update_progress(len(demoLocations), len(demoLocations))
            try:
                results = parsedDemos.get()
            except Exception as e:
                print(e)
                
        for demoLocation in demoLocations: os.remove(demoLocation) 
              
        finish = time.time()
        print(f' Finished parsing in {round((finish-start),2)} second(s)')
        return results 
       
def main():
    demosLocation = './demos'
    db_location = 'pr.db'
    
    sp = StatsParser(demosLocation, db_location)
    
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS demos (
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
        
    duplicateRows = 0
    numRowsInserted = 0
    for result in sp.parsedDemos:
        if result.serverName != 0:
            try:
                insertDemo(c, result)
                numRowsInserted += 1
            except sqlite3.IntegrityError:
                duplicateRows +=1
                
    print(f'Demos inserted: {numRowsInserted}')
    
    conn.commit()
    conn.close()
    
if __name__ == '__main__':
    main()