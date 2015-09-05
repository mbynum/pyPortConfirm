#!/usr/bin/python

from twisted.internet.protocol import Protocol,ServerFactory
from twisted.internet import reactor

testPorts = [25, 80, 110, 143, 389, 993, 995, 587, 50636]


class QuickDisconnectProtocol(Protocol): 
    def connectionMade(self): 
        print "Connection from : ", self.transport.getPeer()
        self.transport.loseConnection() # terminate connection


f = ServerFactory()
f.protocol = QuickDisconnectProtocol


for i in testPorts:
    reactor.listenTCP(i,f)

reactor.run()