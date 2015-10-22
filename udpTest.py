from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class Echo(DatagramProtocol):

    def datagramReceived(self, data, (host, port)):
        print "received %r from %s:%d" % (data, host, port)
        self.transport.write(data, (host, port))


class portTestUDPProtocol(DatagramProtocol):
    ''' Server UDP protocol for taking what is received from the client and tossing it back. '''
    

    def datagramReceived(self, datagram, (client, port)):
        print "Datagram received from: %s:%d" % (client, port)
        datagram = datagram + ", from %s:%d" % (client, port)
        self.transport.write(datagram)



reactor.listenUDP(8000, portTestUDPProtocol())
reactor.run()