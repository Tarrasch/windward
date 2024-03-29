"""
Module myPlayerBrain: the sample Python AI.  Start with this project but write
your own code as this is a very simplistic implementation of the AI.

Created on January 15, 2013

@author: Windward Studios, Inc. (www.windward.net).

No copyright claimed - do anything you want with this code.
"""

import random
import simpleAStar
import numpy
import networkx as nx
from framework import sendOrders
from api import units, map
from debug import printrap
from pprint import pprint

from xml.etree import ElementTree as ET

NAME = "Guido van Rossum"
SCHOOL = "Tech"

class MyPlayerBrain(object):
    """The Python AI class.  This class must have the methods setup and gameStatus."""
    def __init__(self, name=NAME):
        self.name = name #The name of the player.
        
        #The player's avatar (looks in the same directory that this module is in).
        #Must be a 32 x 32 PNG file.
        try:
            avatar = open("MyAvatar.png", "rb")
            avatar_str = b''
            for line in avatar:
                avatar_str += line
            avatar = avatar_str
        except IOError:
            avatar = None # avatar is optional
        self.avatar = avatar


    def makeId(self,x,y,d):
        (r) = self.ids[x][y] + d
        return r

    def calcDists(self):
        print "start"
        dirs = 4
        width = self.gameMap.width
        height = self.gameMap.height
        self.ids = numpy.zeros( (width,height), int)
        print "start"

        self.nids = 0
        for xi in xrange(width):
            for yi in xrange(height):
                d = self.gameMap.squareOrDefault( (xi,yi) )
                if d.isDriveable():
                    self.ids[xi][yi] = self.nids
                    self.nids += dirs

        print self.nids
        self.G = nx.DiGraph()
        #self.G.add_node(self.nids)
        #self.dists = numpy.empty( (self.nids,self.nids), list)
        for i in xrange(self.nids):
            self.G.add_node(i)
        #    self.dists[i] = []

        for xi in xrange(width):
            for yi in xrange(height):
                #print (xi,yi)
                d = self.gameMap.squareOrDefault( (xi,yi) )
                if d.isDriveable():
                    U = 0
                    L = 1
                    D = 2
                    R = 3
                    rondell = [(U,(0,0),L,3), #"INTERSECTION":2,
                         (L,(0,0),D,3),
                         (D,(0,0),R,3),
                         (R,(0,0),U,3)]
                    funs = [
                        [(U,(0,-1),U,1), (D,(0,1),D,1)], #"NORTH_SOUTH":0,
                        [(L,(-1,0),L,1), (R,(1,0),R,1)], #"EAST_WEST":1,
                        rondell + #"INTERSECTION":2,
                        [(U,(0,1),U,3),
                         (R,(1,0),R,3),
                         (L,(-1,0),L,3),
                         (D,(0,-1),D,3)],
                        [(U,(0,0),D,3), #"NORTH_UTURN":3,
                         (D,(0,-1),D,3)],
                        [(R,(0,0),L,3), #'EAST_UTURN':4,
                         (L,(-1,0),L,3)],
                        [(D,(0,0),U,3), #'SOUTH_UTURN':5,
                         (U,(0,1),U,3)],
                        [(L,(0,0),R,3), #'WEST_UTURN':6,
                         (R,(1,0),R,3)],
                        rondell + #'T_NORTH':7,
                        [(U,(0,1),U,3),
                         (R,(1,0),R,3),
                         (L,(-1,0),L,3)],
                        rondell + #'T_EAST':8,
                        [(U,(0,1),U,3),
                         (R,(1,0),R,3),
                         (D,(0,-1),D,3)],
                        rondell + #'T_SOUTH':9,
                        [(R,(1,0),R,3),
                         (L,(-1,0),L,3),
                         (D,(0,-1),D,3)],
                        rondell + #'T_WEST':10,
                        [(U,(0,1),U,3),
                         (L,(-1,0),L,3),
                         (D,(0,-1),D,3)],
                        [(U,(1,0),R,3), #'CURVE_NE':11,
                         (L,(0,-1),D,3)],
                        [(U,(-1,0),L,3), #'CURVE_NW':12,
                         (R,(0,-1),D,3)],
                        [(D,(1,0),R,3), #'CURVE_SE':13,
                         (L,(0,1),U,3)],
                        [(D,(-1,0),L,3), #'CURVE_SW':14}
                         (R,(0,1),U,3)]
                        ]
                    #stopsign
                    for (d1,(xd,yd),d2,c) in funs[d.dir]:
                        f = self.makeId(xi,yi,d1)
                        t = self.makeId(xi+xd,yi+yd,d2)
                        self.G.add_weighted_edges_from([(f,t,c)])
                        #print (f,t,c+1334)
                    #print nx.shortest_path(self.G, None, None, weight="weight")[f]
                    #return
        self.paths = nx.shortest_path(self.G, None, None, weight="weight")
        self.dists = nx.shortest_path(self.G, None, None, weight="weight")

        #for k in xrange(self.nids):
        #    print (k)
        #    for i in xrange(self.nids):
        #        for j in xrange(self.nids):
        #            self.dists[i][j] = max(
        #            self.dists[i][j],
        #            self.dists[i][k] +
        #            self.dists[k][j])

    def distance( (x1,y1,d1), (x2,y2,d2) ):
        i = self.makeId(x1,y1,d1)
        j = self.makeId(x2,y2,d2)
        d = self.dists[i][j]
        p = self.paths[i][j]
        return (d,p)

    def setup(self, gMap, me, allPlayers, companies, passengers, client):
        """
        Called at the start of the game; initializes instance variables.

        gMap -- The game map.
        me -- Your Player object.
        allPlayers -- List of all Player objects (including you).
        companies -- The companies on the map.
        passengers -- The passengers that need a lift.
        client -- TcpClient to use to send orders to the server.

        """
        self.gameMap = gMap
        self.players = allPlayers
        self.me = me
        self.companies = companies
        self.passengers = passengers
        self.client = client

        self.pickup = pickup = self.allPickups(me, passengers)

        self.calcDists()

        #i = 3 #self.makeId(x1,y1,d1)
        #j = 8 #self.makeId(x2,y2,d2)
        #r = nx.shortest_path(self.G, None, None, weight="weight")
        #print r

        # get the path from where we are to the dest.
        path = self.calculatePathPlus1(me, pickup[0].lobby.busStop)
        sendOrders(self, "ready", path, pickup)

    def gameStatus(self, status, playerStatus, players, passengers):
        """
        Called to send an update message to this A.I.  We do NOT have to send a response.

        status -- The status message.
        playerStatus -- The player this status is about. THIS MAY NOT BE YOU.
        players -- The status of all players.
        passengers -- The status of all passengers.

        """

        # bugbug - Framework.cs updates the object's in this object's Players,
        # Passengers, and Companies lists. This works fine as long as this app
        # is single threaded. However, if you create worker thread(s) or
        # respond to multiple status messages simultaneously then you need to
        # split these out and synchronize access to the saved list objects.

          # bugbug - we return if not us because the below code is only for
          # when we need a new path or our limo hits a bus stop. If you want
          # to act on other players arriving at bus stops, you need to
          # remove this. But make sure you use self.me, not playerStatus for
          # the Player you are updating (particularly to determine what tile
          # to start your path from).
        print("hello")
        self.status = status
        self.playerStatus = playerStatus
        self.players = players
        self.passenger = passengers
        if playerStatus != self.me:
            return

        print("Now i'm me")

        ptDest = None
        pickup = []
        if    status == "UPDATE":
            return
        elif (status == "PASSENGER_NO_ACTION" or
              status == "NO_PATH"):
            if playerStatus.limo.passenger is None:
                pickup = self.allPickups(playerStatus, passengers)
                ptDest = pickup[0].lobby.busStop
            else:
                ptDest = playerStatus.limo.passenger.destination.busStop
        elif (status == "PASSENGER_DELIVERED" or
              status == "PASSENGER_ABANDONED"):
            pickup = self.allPickups(playerStatus, passengers)
            ptDest = pickup[0].lobby.busStop
        elif  status == "PASSENGER_REFUSED":
            ptDest = random.choice(filter(lambda c: c != playerStatus.limo.passenger.destination,
                self.companies)).busStop
        elif (status == "PASSENGER_DELIVERED_AND_PICKED_UP" or
              status == "PASSENGER_PICKED_UP"):
            pickup = self.allPickups(playerStatus, passengers)
            ptDest = playerStatus.limo.passenger.destination.busStop
        else:
            raise TypeError("unknown status %r", status)

        print("1")
        pprint(self.companies)
        pprint(passengers)
        combs = []
        for ceo in passengers:
          for end in self.companies:
            print( "hi")
            combs += [(self.getCost(ceo, end), ceo, end)]
        print("2")

        pprint(combs)

        self.getCost(passengers[0], passengers[0].destination)

        # get the path from where we are to the dest.
        path = self.calculatePathPlus1(playerStatus, ptDest)

        sendOrders(self, "move", path, pickup)

    def getCost(self, ceo, end):
      """
      ceo - ceo aka passenger
      end - company
      """
      pprint(ceo)
      pprint(end)

      isRelevant = self.ceoRelevant(ceo)

      if(not isRelevant): return 99999999999999999
      points = ceo.pointsDelivered
      endPeople = ceo.destination.passengers # People standing there
      relevantEndPeople = filter(self.ceoRelevant, endPeople)
      enemiesAtEnd = set(endPeople).intersection( set(ceo.enemies) )
      distcost = 0

      values = [
          distcost * 1.0,
          points * 1.0,
          len(relevantEndPeople) * -1.0,
          len(enemiesAtEnd) * 1.0
          ]
      pprint(values)
      return sum(values)

    def ceoRelevant(self, ceo):
      return (not ceo in self.me.passengersDelivered) and              (ceo.car == None or ceo == self.me.limo.passenger) and              (ceo.destination != None)

    def calculatePathPlus1 (self, me, ptDest):
        path = simpleAStar.calculatePath(self.gameMap, me.limo.tilePosition, ptDest)
        # add in leaving the bus stop so it has orders while we get the message
        # saying it got there and are deciding what to do next.
        if len(path) > 1:
            path.append(path[-2])
        return path

    def allPickups (self, me, passengers):
            pickup = [p for p in passengers if (not p in me.passengersDelivered and
                                                p != me.limo.passenger and
                                                p.car is None and
                                                p.lobby is not None and p.destination is not None)]
            random.shuffle(pickup)
            return pickup
