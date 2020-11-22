# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 22:36:44 2020

@author: Nathan
"""
import sys
import os
import json
import errno
from collections import namedtuple
from bs4 import BeautifulSoup
import requests
import urllib
import datetime
import time
from fnmatch import fnmatch

# Helper functions to turn json files into namedtuple
def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)
# Helper functions to safely create new folders if it doesn't exist already
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
def safe_open_w(path):
    mkdir_p(os.path.dirname(path))
    return open(path, 'w')

def getDemoName(demoUrl):
    if "file=" in demoUrl:
       return demoUrl.split("file=")[1]
    else:
        return os.path.basename(demoUrl)

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
    
class ServerList(object):

    def __init__(self,prpath,webpath):
        self.date = str(datetime.datetime.now())
        if prpath != None:
            self.prpath = prpath
        if webpath != None:
            self.webpath = webpath
        self.servers = []

    # Write object to JSON string
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)    

class Server(object):

    def __init__(self,name,links,demos):
        self.name = name;
        self.links = links
        self.demos = demos;   

def downloadDemos(configFile = './input/config.json'):
    # try:
    with open(configFile, 'r') as f:
        if not os.path.exists("./demos"):
            os.makedirs("./demos")
        config = json2obj(f.read())
        demosToDownload = []
        toDownloadServerNames = []
        serverNameList = []
        if hasattr(config, 'prpath') and hasattr(config, 'webpath'):
            newServerConfig = ServerList(config.prpath,config.webpath)
        elif hasattr(config, 'prpath'):
            newServerConfig = ServerList(config.prpath, None)
        elif hasattr(config, 'webpath'):
            newServerConfig = ServerList(None, config.webpath)
        else:
            newServerConfig = ServerList(None, None)
        for serverIndex, server in enumerate(config.servers, start=0):
            demoDownloadLinks = []
            demos = server.demos
            for linkIndex, link in enumerate(server.links, start=0):
                demoDownloadLinks.append(link)
                if fnmatch(link, "*.json"):
                    crawlers = json2obj(urllib.urlopen(link).read())
                    for crawler in crawlers:
                        for demoUrlIndex, demoUrl in enumerate(crawler.Trackers, start=0):
                            if getDemoName(demoUrl) not in server.demos:
                                if server.name not in serverNameList:
                                    serverNameList.append(server.name)
                                demosToDownload.append(demoUrl)
                                toDownloadServerNames.append(server.name)
                                demos.append(getDemoName(demoUrl))
                else:
                    soup = BeautifulSoup(requests.get(link).text, 'html.parser')
                    for demoUrl in [link + node.get('href') for node in soup.find_all('a') if
                                    node.get('href').endswith('PRdemo')]:
                        if getDemoName(demoUrl) not in server.demos:
                            if server.name not in serverNameList:
                                serverNameList.append(server.name)
                            demosToDownload.append(demoUrl)
                            toDownloadServerNames.append(server.name)
                            demos.append(getDemoName(demoUrl))
            newServerConfig.servers.append(Server(server.name, demoDownloadLinks, demos))
        if len(demosToDownload) != 0:
            print("Downloading available PRDemos from servers(" + ','.join(serverNameList) + ")...")
            for demoIndex, demoUrl in enumerate(demosToDownload, start=0):
                update_progress(demoIndex,len(demosToDownload))
                demoFileName = str("./demos/" + getDemoName(demoUrl))
                try:
                    time.sleep(0.5)
                    urllib.request.urlretrieve(demoUrl, demoFileName)
                except urllib.request.HTTPError as e:
                    pass
            update_progress(len(demosToDownload), len(demosToDownload))
            print("\nAll available PRDemos from servers("+ str(len(demosToDownload)) + ") downloaded.")
        else:
            print("There are no new PRDemos to download.")
        with safe_open_w(configFile) as f:
            f.write(newServerConfig.toJSON())
    # except :
    #     print("/input/config.json file not found. Can't download demos automatically.")
