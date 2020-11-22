# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 01:34:10 2020

@author: Nathan
"""

import requests
from bs4 import BeautifulSoup
import urllib.request
import shutil
import regex as re
import datetime
import sqlite3
import time

class Server:
    def __init__(self, name, linkUrl, trackerUrl, searchTerm='',waitTime=0):
        self.name = name
        self.linkUrl = linkUrl
        self.trackerUrl = trackerUrl
        self.searchTerm = searchTerm
        self.waitTime = waitTime
        self.headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
            }
        self.downloadDemos()
        
    def getLatestDemo(self):
        db_location = 'pr.db'
        conn = sqlite3.connect(db_location)
        c = conn.cursor()
        c.execute(f"SELECT MAX(date) FROM demos WHERE server LIKE '%{self.name}%';")
        returnDate = c.fetchone()[0]
        if returnDate is None:
            returnDate = '2000-00-00 00:00:00'
        return returnDate
    
    def downloadDemos(self):
        req = requests.get(self.linkUrl, self.headers)
        soup = BeautifulSoup(req.content, 'html.parser')
        tags = soup.find_all('a', text=re.compile(self.searchTerm))
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        demosToDownload = []
        # findFileName = re.compile('tracker_.+PRdemo$')
        findFileName = re.compile('tracker_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}.+PRdemo$')
        findDate = re.compile('\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}')
        lastDemoDate = self.getLatestDemo()
        for tagIndex,tag in enumerate(tags):
            filename = re.search(findFileName, tag['href']).group(0)
            if filename not in demosToDownload:
                fileDate = re.search(findDate, filename).group(0)
                fileDateFormatted = datetime.datetime.strptime(fileDate, '%Y_%m_%d_%H_%M_%S').strftime('%Y-%m-%d %H:%M:%S')
                if fileDateFormatted > lastDemoDate:
                    demosToDownload.append(filename)
                    demoDestFileName = str("demos/" + filename)
                    demoUrl = str(self.trackerUrl + filename)
                    try:
                        time.sleep(self.waitTime)
                        print(f'Downloading {self.name} {fileDateFormatted}')                
                        page = urllib.request.Request(demoUrl,headers={'User-Agent': user_agent}) 
                        response = urllib.request.urlopen(page)
                        with open(demoDestFileName, 'wb') as out_file:
                            shutil.copyfileobj(response,out_file)
                    except urllib.request.HTTPError as e:
                        print(e)
                        break
                    
Server('Gamma','http://gammagroup.wtf/br/main/tracker/','http://gammagroup.wtf/br/main/tracker/', '.PRdemo\Z')
Server('Free Candy Van', 'http://www.fcv-pr.com/?srv=1','http://www.fcv-pr.com/tracker/', 'Tracker')
Server('PRTA', 'https://eu3.prta.co/servers/prbf2/1/tracker/','https://eu3.prta.co/servers/prbf2/1/tracker/')
Server('DIVSUL', 'http://usaserver.divsul.org:666/PRServer/BattleRecorder/Server01/tracker/','http://usaserver.divsul.org:666/PRServer/BattleRecorder/Server01/tracker/', 'tracker_')
Server('=HOG=', 'http://br.hogclangaming.com/pr1/','http://br.hogclangaming.com/pr1/','tracker_',1)
Server('SSG', 'http://br.ssg-clan.com/?srv=1','http://br.ssg-clan.com/tracker/', 'Tracker')

# ru = Server('Russian', 'C:/Users/Nathan/Downloads/RussianReality.html','http://www.realitymod.ru/tracker/records/download.php?file=')
# sf = Server('=SF=', 'http://18.229.154.12/tracker/','http://18.229.154.12/tracker/','^ tracker_.*')       
# csa -- 'http://csapr.duckdns.org/tracker/'