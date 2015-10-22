#!/usr/bin/python
from twisted.internet.protocol import Protocol,ServerFactory,ClientFactory,DatagramProtocol
from twisted.internet import reactor

import xml.etree.ElementTree as ET
import logging, argparse, sys, atexit


def singleton(givenClass):
    instances = {}

    def getInstance(*args, **kwargs):
        if givenClass not in instances:
            instances[givenClass] = givenClass(*args, **kwargs)
        return instances[givenClass]
    return getInstance


def read_xml(xmlfile):

	tree = ET.parse(xmlfile)
	root = tree.getroot()

	profile = {}
	profile['profile_ports'] = []

	profile['applicationName'] = root.find("ApplicationName").text
	profile['vendor'] = root.find("Vendor").text
	profile['version'] = root.find("Version").text

	for entry in root.iter('Entry'):
		profile_entry = {}
		for child in entry:
			profile_entry[child.tag] = child.text
		profile['profile_ports'].append(profile_entry)

	return profile


@singleton
class portTestOutput(object):

    output = []
    def stash(self,protocol,srcaddr,srcport,destaddr,dstport,result):
        instance = {}
        instance['protocol'] = protocol
        instance['srcaddr'] = srcaddr
        instance['srcport'] = srcport
        instance['destaddr'] = destaddr
        instance['dstport'] = dstport
        instance['result'] = result
        self.output.append(instance)

    def write(self):
        import csv

        outputFile = "results.csv"
        fieldnames = ['protocol','srcaddr','srcport','destaddr','dstport','result']
        with open(outputFile,'wb') as csvfile:
            writer = csv.DictWriter(csvfile, dialect='excel', fieldnames=fieldnames)
            writer.writeheader()
            for row in self.output:
                writer.writerow(row)


class portTestTCPProtocol(Protocol):
    ''' Server TCP protocol for taking what is received from the client and tossing it back. '''
    def dataReceived(self, data):
        client = self.transport.getPeer().host
        port = self.transport.getPeer().port
        print "Data received from %s:%d: %s" % (client, port, data)
        data = "%s,%d,%s" % (client, port, data)
        self.transport.write(data)
        self.transport.loseConnection()

    def connectionMade(self): 
        print "Connection from : ", self.transport.getPeer()


class portTestUDPProtocol(DatagramProtocol):
    ''' Server UDP protocol for taking what is received from the client and tossing it back. '''

    def datagramReceived(self, datagram, (client, port)):
        print "Datagram received from: %s:%d" % (client, port)
        datagram = "%s,%d,%s" % (client, port, datagram)
        self.transport.write(datagram, (client,port))
        print "Datagram sent to: %s:%d" % (client, port)

class portTestTCPClient(Protocol):
    ''' Client TCP protocol for Sending a message to a client and then checking to see if that's the message that is received. '''
    host = None
    port = None
    def connectionMade(self):
        self.transport.write("[OK]")

    def dataReceived(self, data):
        logger = portTestOutput()
        self.host = self.transport.getPeer().host
        self.port = self.transport.getPeer().port
        data = data.split(",")
        if len(data) == 3:
            if data[2] == "[OK]":
                print("SUCCESS for TCP connection to %s:%d: %s" % (self.host, self.port, data))
                logger.stash("TCP", data[0], data[1], self.host, self.port, data[2])
                self.transport.loseConnection()
        else:
            print ("FAILED for TCP connection to %s:%d: %s" % (self.host, self.port, data))
            logger.stash("TCP", "unknown", "unknown", self.host, self.port, "[FAILED]")


class portTestUDPClient(DatagramProtocol):
    ''' Client UDP protocol for Sending a message to a client and then checking to see if that's the message that is received. '''
    server = None
    port = None
    response = False
    def startProtocol(self):
        self.transport.connect(self.server, self.port)
        self.sendDatagram()

    def stopProtocol(self):
        if self.response:
            pass
        else:
            logger.stash("UDP", "unknown", "unknown", self.server, self.port, "[FAILED]")

    def sendDatagram(self):
        self.transport.write("[OK]")

    def datagramReceived(self, data, (host, port)):
        self.response = True
        data = data.split(",")
        if len(data) == 3:
            if data[2] == "[OK]":
                print("SUCCESS for UDP connection to %s:%d: %s" % (host, port, data))
                logger.stash("UDP", data[0], data[1], host, port, data[2])
                self.transport.loseConnection()
        else:
            print ("FAILED for UDP connection to %s:%d: %s" % (host, port, data))
            logger.stash("UDP", "unknown", "unknown", host, port, "[FAILED]")



class portTestClientFactory(ClientFactory):
    protocol = portTestTCPClient

    def clientConnectionFailed(self, connector, reason):
        print ("Connection failed to %s:%s, %s" % (connector.host, connector.port, reason.getErrorMessage()))
        logger.stash("TCP", "unknown", "unknown", connector.host, connector.port, "[FAILED]")


    def clientConnectionLost(self, connector, reason):
        if reason.getErrorMessage() == 'Connection was closed cleanly.':
            pass
        else:
            print("Connection lost:", reason.getErrorMessage())



def protocol_runner(protocol, mode, port, f, server=None):
    if mode == "server":
        if protocol == "TCP":
            f.protocol = portTestTCPProtocol
            
            try:
                reactor.listenTCP(port,f)
            except:
                pass
        else:
            udpInstance = portTestUDPProtocol()
            try:
                reactor.listenUDP(port,udpInstance)
            except:
            #    print Exception
                pass
    else:
        #This should catch the CLIENT mode
        if protocol == "TCP":
            f.protocol = portTestTCPClient

            try: 
                reactor.connectTCP(server, port, f)
            except:
                pass
        else:
            #f.protocol = portTestUDPClient
            udpInstance = portTestUDPClient()
            udpInstance.port = port
            udpInstance.server = server
            try:
                reactor.listenUDP(0, udpInstance)
            except Exception as e:
                print "Error! %s" % (e)
                



def run_server(profile):
    listeningPorts = [] 
    
    for i in profile['profile_ports']:
        f = ServerFactory()
        port = int(i['DestinationPort'])
        protocol = i['Protocol']
        if "%s/%s" % (protocol,port) in listeningPorts:
            pass
        else:    
            protocol_runner(protocol, "server", port, f)
            listeningPorts.append("%s/%s" % (protocol,port))
            print "LISTENING %s/%s" % (protocol,port)

    reactor.run()


def run_client(profile,server):
    for i in profile['profile_ports']:
        f = portTestClientFactory()
        port = int(i['DestinationPort'])
        protocol = i['Protocol']
        protocol_runner(protocol, "client", port, f, server)

    reactor.run()






if __name__ == "__main__":
    logger = portTestOutput()
    parser = argparse.ArgumentParser(description='Softchoice pyPortTest for testing application port availability across a network')
    parser.add_argument('--appnetprofile','-a', nargs='?', metavar = 'FILENAME',
                        help='After this flag, provide the location of the application network profile: C:\\Users\\tempuser\\Desktop\\list.csv')

    parser.add_argument('--verbose','-v', action='store_true',
                        help="Use this to provide more verbosity as output is generated.")
    parser.add_argument('--version','-V', action='store_true',
                        help = "Displays the current version.")
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--server','-s', action='store_true',
                        help="Specifies that this instance of the script will use the application network profile and begin listening on ports.")
    group1.add_argument('--client','-c', action='store_true',
                        help="Specifies that this instance of the script will use the application network profile and attempt connections to a given server, with the expectation that it is being run from a client subnet.")
    group1.add_argument('--clientserver','-cs', action='store_true',
                        help="Specifies that this instance of the script will use the application network profile and attempt connections to a given server, but the expectation is that it is being run on a server subnet.")    

    parser.add_argument('--target','-t', nargs='?', metavar = 'IPADDRESS',
                       help='Specify a the destination (if this is being run in client mode) to establish connections to.')

  
    args = parser.parse_args()
    print "\n"



    if args.client and not args.target:
        print "Please provide a target for the client to connect to."
        sys.exit()
    elif args.clientserver and not args.target:
        print "Please provide a target for the client-server to connect to."
        sys.exit()
    elif args.server and args.target:
        print "Target not needed for server mode, ignoring."

    if args.appnetprofile:
        profile = read_xml(args.appnetprofile)
    else:
        print "Please provide an application network profile with the -a flag."
        sys.exit()

    if args.server:
        run_server(profile)
    elif args.client:
        atexit.register(logger.write)
        run_client(profile,args.target)
    elif args.clientserver:
        atexit.register(logger.write)
        run_client(profile,args.target)
    else:
        print "Please provide the mode that you'd like the script to run in."


