# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 01:34:10 2020

@author: Nathan

Note: There is considerable hang-time when connecting to the FCV servers, but it will connect eventually'
"""

import requests
from bs4 import BeautifulSoup
import urllib.request
import shutil
import regex as re
import datetime
import sqlite3
import time
import sys

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

class Server:
    def __init__(self, name, linkUrl, trackerUrl, searchTerm='',waitTime=0, db_location = 'pr.db'):
        self.name = name
        self.linkUrl = linkUrl
        self.trackerUrl = trackerUrl
        self.searchTerm = searchTerm
        self.waitTime = waitTime
        self.db_location = db_location
        self.headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
            }
        self.downloadDemos()
        
    def getLatestDemo(self):
        conn = sqlite3.connect(self.db_location)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS lastDownload (
            server TEXT,
            date DATE,
            PRIMARY KEY(server)
            )''')
        conn.commit()
        c.execute('SELECT COUNT(*) FROM lastDownload WHERE server ==:serverName',{'serverName':self.name})
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO lastDownload (server, date)
                      VALUES(:server,:date)''', {'server':self.name, 'date': '2000-01-01 00:00:00'})
            conn.commit()
        c.execute('SELECT date FROM lastDownload WHERE server ==:serverName ', {'serverName':self.name})
        returnDate = c.fetchone()[0]
        conn.close()
        return returnDate
    
    def updateLatestDemo(self, newDate):
        conn = sqlite3.connect(self.db_location)
        c = conn.cursor()
        c.execute('''UPDATE lastDownload
                  SET date = :newDate
                  WHERE server = :serverName''', {'newDate': newDate, 'serverName': self.name})
        conn.commit()
        conn.close()
    
    def downloadDemos(self):
        req = requests.get(self.linkUrl, self.headers)
        soup = BeautifulSoup(req.content, 'html.parser')
        tags = soup.find_all('a', text=re.compile(self.searchTerm))
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        findFileName = re.compile('tracker_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}.+PRdemo$')
        findDate = re.compile('\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}')
        lastDemoDate = self.getLatestDemo()
        newDateToUpdate = '2000-01-01 00:00:00'
        demosToDownload = []
        for tagIndex,tag in enumerate(tags):
            filename = re.search(findFileName, tag['href']).group(0)
            fileDate = re.search(findDate, filename).group(0)
            fileDateFormatted = datetime.datetime.strptime(fileDate, '%Y_%m_%d_%H_%M_%S').strftime('%Y-%m-%d %H:%M:%S')
            if fileDateFormatted > lastDemoDate:
                if fileDateFormatted > newDateToUpdate:
                    newDateToUpdate = fileDateFormatted
                demosToDownload.append(filename)
                
        if len(demosToDownload) > 0:
            print(f'Downloading from {self.name}')
        for demoIndex,demo in enumerate(demosToDownload):
            update_progress((demoIndex+1), len(demosToDownload))
            demoDestFileName = str("demos/" + demo)
            demoUrl = str(self.trackerUrl + demo)
            try:
                time.sleep(self.waitTime)
                page = urllib.request.Request(demoUrl,headers={'User-Agent': user_agent}) 
                response = urllib.request.urlopen(page)
                with open(demoDestFileName, 'wb') as out_file:
                    shutil.copyfileobj(response,out_file)
            except urllib.request.HTTPError as e:
                print(e)
                break
        if newDateToUpdate != '2000-01-01 00:00:00':
            self.updateLatestDemo(newDateToUpdate)

def downloadAllDemos():
    Server('Gamma','http://gammagroup.wtf/br/main/tracker/','http://gammagroup.wtf/br/main/tracker/', '.PRdemo\Z')
    Server('Free Candy Van', 'http://www.fcv-pr.com/?srv=1','http://www.fcv-pr.com/tracker/', 'Tracker')
    Server('PRTA', 'https://eu3.prta.co/servers/prbf2/1/tracker/','https://eu3.prta.co/servers/prbf2/1/tracker/')
    Server('DIVSUL', 'http://usaserver.divsul.org:666/PRServer/BattleRecorder/Server01/tracker/','http://usaserver.divsul.org:666/PRServer/BattleRecorder/Server01/tracker/', 'tracker_')
    Server('=HOG=', 'http://br.hogclangaming.com/pr1/','http://br.hogclangaming.com/pr1/','tracker_',1)
    Server('SSG', 'http://br.ssg-clan.com/?srv=1','http://br.ssg-clan.com/tracker/', 'Tracker')    

def main():
    downloadAllDemos()

if __name__ == '__main__':
    main()

# TO-DO: find a way to scrape demos from the below links
# ru = Server('Russian', 'C:/Users/Nathan/Downloads/RussianReality.html','http://www.realitymod.ru/tracker/records/download.php?file=')
# sf = Server('=SF=', 'http://18.229.154.12/tracker/','http://18.229.154.12/tracker/','^ tracker_.*')       
# csa -- 'http://csapr.duckdns.org/tracker/'