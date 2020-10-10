# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 17:01:38 2020
Most of this code was written by WouterJansen from https://github.com/WouterJansen/PRDemoStatsParser this repo

I have made some changes, mostly updating the code from Python 2 to Python 3.
This file only parses one PRDemo file so I can test some things.
@author: Nathan
"""
import struct
import zlib
import io
import json
import os, os.path
from collections import namedtuple
import datetime
import numpy as np
import sqlite3
from datetime import datetime
    
def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)
# Helper function to return a null terminated string from pos in buffer
def getString(stream):
    tmp = ''
    while True:
        char = stream.read(1)
        
        #For debugging purposes
        if char == b'\xb8':
            print('Error here')
        
        char = char.decode('utf-8')
        # char = char.decode('ISO-8859-1')
        if char == '\0':
            return tmp
        tmp += str(char)


# Helper function to add to struct.unpack null terminated strings
# Unpacks with null terminated strings when using "s".
# Unpacks "vehicle" structs when using "v".
# Returns a list of [value1,value2,value3...]
def unpack(stream, fmt):
    values = []

    for i in range(0, len(fmt)):
        if fmt[i] == 'v':
            vehid = unpack(stream, "h")
            if vehid >= 0:
                (vehname, vehseat) = unpack(stream, "sb")
                values.append((vehid, vehname, vehseat))
            else:
                values.append((vehid))

        elif fmt[i] == 's':
            string = getString(stream)
            values.append(string)
        else:
            size = struct.calcsize(fmt[i])
            try:
                values.append(struct.unpack("<" + fmt[i], stream.read(size))[0])
            except:
                return -1;
    if len(values) == 1:
        return values[0]
    return values

# Helper function to through a folder and list all files
def walkdir(folder):
    for dirpath, dirs, files in os.walk(folder):
        files.sort()
        for filename in files:
            yield os.path.abspath(os.path.join(dirpath, filename))
            
# Helper function that is used by multiprocessing to start a worker to parse a PRDemo
def parseNewDemo(filepath):
    parsedDemo = demoParser(filepath).getParsedDemo()
    return parsedDemo

#Find the map scale found in /input/maps.json. Used for correctly aggragate positions of players
#to heatmap data.
def findScale(mapName):
    try:
        with open("./input/maps.json", 'r') as f:
            mapInfoData = f.read()
            mapInfo = json2obj(mapInfoData)
            if hasattr(mapInfo, mapName):
                return getattr(mapInfo, mapName).scale
            else:
                return 0
    except:
        return 0

class Flag(object):

    def __init__(self, cpid, x, y, z, radius):
        self.cpid = cpid
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius


class ParsedDemo(object):

    def __init__(self,version=0, date=0, map_=0, gameMode=0, layer=0, duration=0, playerCount=0, ticketsTeam1=0, ticketsTeam2=0,
                 flags=[],heatMap = None):
        self.version = version
        self.serverName = 0
        self.map = map_
        self.date = date
        self.gameMode = gameMode
        self.layer = layer
        self.duration = duration
        self.playerCount = playerCount
        self.ticketsTeam1 = ticketsTeam1
        self.ticketsTeam2 = ticketsTeam2
        self.flags = flags
        self.heatMap = heatMap

    def setData(self, version, date, serverName, map_, gameMode, layer, duration, playerCount, ticketsTeam1, ticketsTeam2, flags,heatMap):
        self.version = version
        self.date = date
        self.serverName = serverName
        self.map = map_
        self.gameMode = gameMode
        self.layer = layer
        self.duration = duration
        self.playerCount = playerCount
        self.ticketsTeam1 = ticketsTeam1
        self.ticketsTeam2 = ticketsTeam2
        self.flags = flags
        self.heatMap = heatMap

    # TODO Implement SGID method
    # Create ID of flag route based on CPID list (placeholder until SGID is available to calculate route ID)
    def getFlagId(self):
        flagCPIDs = []
        for flag in self.flags:
            flagCPIDs.append(flag.cpid)
        flagCPIDs.sort()
        return ("Route " + ", ".join(str(x) for x in flagCPIDs)).strip()

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


class MapList(object):

    def __init__(self):
        self.maps = []
        self.date = str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"))

    # Write object to JSON string
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class Map(object):

    def __init__(self, name):
        self.name = name
        self.gameModes = []
        self.timesPlayed = 0
        self.averageDuration = 0
        self.averageTicketsTeam1 = 0
        self.averageTicketsTeam2 = 0
        self.winsTeam1 = 0
        self.winsTeam2 = 0
        self.draws = 0
        self.versions =  []

    # Write object to JSON string
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class GameMode(object):

    def __init__(self, name):
        self.name = name
        self.layers = []
        self.timesPlayed = 0
        self.averageDuration = 0
        self.averageTicketsTeam1 = 0
        self.averageTicketsTeam2 = 0
        self.winsTeam1 = 0
        self.winsTeam2 = 0
        self.draws = 0


class Layer(object):

    def __init__(self, name):
        self.name = name
        self.routes = []
        self.timesPlayed = 0
        self.averageDuration = 0
        self.averageTicketsTeam1 = 0
        self.averageTicketsTeam2 = 0
        self.winsTeam1 = 0
        self.winsTeam2 = 0
        self.draws = 0

class Route(object):

    def __init__(self, id, updated):
        self.id = id
        self.roundsPlayed = []
        self.timesPlayed = 0
        self.averageDuration = 0
        self.averageTicketsTeam1 = 0
        self.averageTicketsTeam2 = 0
        self.winsTeam1 = 0
        self.winsTeam2 = 0
        self.draws = 0
        self.heatMap = 0
        self.updated = updated

class Player:
    def __init__(self):
        self.isalive = 0

    def __setitem__(self, key, value):
        self.__dict__[key] = value

class demoParser:
    def __init__(self, filename):
        compressedFile = open(filename, 'rb')
        compressedBuffer = compressedFile.read()
        compressedFile.close()
        # Try to decompress or assume its not compressed if it fails
        try:
            buffer = zlib.decompress(compressedBuffer)
        except:
            buffer = compressedBuffer

        # self.stream = cStringIO.StringIO(buffer)
        self.stream = io.BytesIO(buffer)
        self.length = len(buffer)

        self.playerCount = 0
        self.timePlayed = 0
        self.flags = []
        self.parsedDemo = ParsedDemo()
        self.scale = 0
        self.playerDict = {}
        self.PLAYERFLAGS = [
            ('team', 1, 'B'),
            ('squad', 2, 'B'),
            ('vehicle', 4, 'v'),
            ('health', 8, 'b'),
            ('score', 16, 'h'),
            ('twscore', 32, 'h'),
            ('kills', 64, 'h'),
            ('deaths', 256, 'h'),
            ('ping', 512, 'h'),
            ('isalive', 2048, 'B'),
            ('isjoining', 4096, 'B'),
            ('pos', 8192, 'hhh'),
            ('rot', 16384, 'h'),
            ('kit', 32768, 's'),
        ]
        self.heatMap = np.zeros(shape=(512,512))
        timeoutindex = 0
        # parse the first few until serverDetails one to get map info
        while self.runMessage() != 0x00:
            if timeoutindex == 10000:
                break
            timeoutindex += 1
            pass
        self.runToEnd()

        # create ParsedDemo object and set it to complete if it was able to get all data
        try:
            self.parsedDemo.setData(self.version, self.date, self.serverName, self.mapName, self.mapGamemode, self.mapLayer, self.timePlayed / 60,
                                    self.playerCount,
                                    self.ticket1, self.ticket2, self.flags,self.heatMap.astype(int))
            self.parsedDemo.completed = True
        except Exception as e:
            pass

    def getParsedDemo(self):
        return self.parsedDemo

    #Find the next message and analyze it.
    def runMessage(self):
        # Check if end of file
        tmp = self.stream.read(2)
        if len(tmp) != 2:
            return 0x99
        # Get 2 bytes of message length
        messageLength = struct.unpack("H", tmp)[0]
        startPos = self.stream.tell()
        try:
            messageType = struct.unpack("B", self.stream.read(1))[0]
        except Exception as e:
            return 0x99

        if messageType == 0x00:  # server details
            values = unpack(self.stream, "IfssBHHssBssIHH")
            if values == -1:
                return 0x99
            version = values[3].split(']')[0].split(' ')
            self.version = version[1][:-2]
            self.serverName = values[3].split(']')[1][1:]
            self.mapName = values[7]
            self.scale = findScale(self.mapName)
            gamemode = values[8]
            if gamemode == "gpm_cq":
                self.mapGamemode = "Advance & Secure"
            elif gamemode == "gpm_insurgency":
                self.mapGamemode = "Insurgency"
            elif gamemode == "gpm_vehicles":
                self.mapGamemode = "Vehicle Warfare"
            elif gamemode == "gpm_cnc":
                self.mapGamemode = "Command & Control"
            elif gamemode == "gpm_skirmish":
                self.mapGamemode = "Skirmish"
            elif gamemode == "gpm_coop":
                self.mapGamemode = "Co-Operative"
            else:
                self.mapGamemode = values[8]
            self.mapLayer = "Layer " + str(values[9])
            self.date = values[12]
            
            # if the game version is 1.6 or newer, then read in an additional 4 bytes at the end
            if int(self.version[3]) > 5:
                self.stream.read(4)

        elif messageType == 0x52:  # tickets team 1
            while self.stream.tell() - startPos != messageLength:
                values = unpack(self.stream, "H")
                if values == -1:
                    return 0x99
                if values < 9000:
                    self.ticket1 = values
                else:
                    self.ticket1 = 0

        elif messageType == 0x53:  # tickets team 2
            while self.stream.tell() - startPos != messageLength:
                values = unpack(self.stream, "H")
                if values == -1:
                    return 0x99
                if values < 9000:
                    self.ticket2 = values
                else:
                    self.ticket2 = 0

        elif messageType == 0xf1:  # tick
            while self.stream.tell() - startPos != messageLength:
                values = unpack(self.stream, "B")
                if values == -1:
                    return 0x99
                self.timePlayed = self.timePlayed + values * 0.04

        elif messageType == 0x10 and self.scale != 0:  # update player
            while self.stream.tell() - startPos != messageLength:
                flags = unpack(self.stream, "H")
                try:
                    p = self.playerDict[unpack(self.stream, "B")]
                    for tuple in self.PLAYERFLAGS:
                        field, bit, fmt = tuple
                        if flags & bit:
                            p[field] = unpack(self.stream, fmt)
                            if field == "pos":
                                if p.isalive:
                                    if p.pos[0] < 256 * self.scale * 2 and p.pos[0] > -256 * self.scale * 2 and \
                                            p.pos[2] < 256 * self.scale * 2 and p.pos[2] > -256 * self.scale * 2:
                                        x = int(round(p.pos[0] / (self.scale * 4) + 128))
                                        y = int(round(p.pos[2] / (self.scale * -4) + 128))
                                        self.heatMap[(x - 1) * 2, (y - 1) * 2] += 1
                except:
                    return 0x99

        elif messageType == 0x11:  # add player
            while self.stream.tell() - startPos != messageLength:
                values = unpack(self.stream, "Bsss")
                if values == -1:
                    return 0x99
                p = Player()
                p.id = values[0]
                p.name = values[1]
                p.hash = values[2]
                p.ip = values[3]
                self.playerDict[values[0]] = p
                self.playerCount += 1

        elif messageType == 0x12:  # remove player
            while self.stream.tell() - startPos != messageLength:
                values = unpack(self.stream, "B")
                if values == -1:
                    return 0x99
                del self.playerDict[values]
                self.playerCount -= 1

        elif messageType == 0x41:  # flaglist
            while self.stream.tell() - startPos != messageLength:
                values = unpack(self.stream, "HBHHHH")
                if values == -1:
                    return 0x99
                self.flags.append(Flag(values[0], values[2], values[3], values[4], values[5]))

        else:
            self.stream.read(messageLength - 1)
        return messageType

    # Returns when tick or round end recieved.
    # Returns false when roundend message recieved
    def runTick(self):
        while True:
            messageType = self.runMessage()
            if messageType == 0xf1:
                return True
            if messageType == 0xf0:
                return False
            if messageType == 0x99:
                return False

    def runToEnd(self):
        while self.runTick():
            pass
        
# test_dir = 'E:/PR/mods/pr_scraped_data/demos'
# os.chdir(test_dir)

# test_file = 'test.PRdemo'
# test = demoParser(test_file)

# conn = sqlite3.connect(':memory:')
# c = conn.cursor()
# c.execute('''CREATE TABLE demos (
#             date DATE,
#             server TEXT,
#             map TEXT,
#             mode TEXT,
#             layer TEXT,
#             playerCount INT,
#             ticketsTeam1 INT,
#             ticketsTeam2 INT,
#             version TEXT,
#             duration INT
#     )''')
# conn.commit()
# c.execute("INSERT INTO demos VALUES('2020-06-10 11:01:52', 'basrah',100,1,13,'3.1',1)")
# conn.commit()
# c.execute('SELECT * FROM demos')
# print(c.fetchall())

def insertDemo(d):
    readableDate = datetime.fromtimestamp(d.date).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO demos VALUES(:date, :server, :map, :mode, :layer, :playerCount, 
              :ticketsTeam1, :ticketsTeam2, :version, :duration)''', 
    {'date':readableDate, 'server':d.serverName, 'map':d.mapName, 'mode':d.mapGamemode, 'layer':d.mapLayer, 'playerCount':d.playerCount, 'ticketsTeam1':d.ticket1, 'ticketsTeam2':d.ticket2,'version':d.version, 'duration':round(d.timePlayed/60,0)})

# insertDemo(test)
# c.execute('SELECT * FROM demos')
# print(c.fetchall())