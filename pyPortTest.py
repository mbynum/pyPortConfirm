#!/usr/bin/python
from twisted.internet.protocol import Protocol,ServerFactory,ClientFactory,DatagramProtocol
from twisted.internet import reactor

import xml.etree.ElementTree as ET
import logging, argparse, sys

def read_xml(xmlfile):
	xmlfile = "application_map_SCOM2012R2.xml"

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

def setup_logger(profile, level=logging.INFO,formatter='messageonly', output_dir='', file_prefix='softchoice_', file_suffix='_report.csv'):
    
    logger_tag = profile['applicationName']
    logger_name = profile['applicationName']+"_"+profile['version']
    

    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        if formatter == 'default':
            formatter = logging.Formatter('%(asctime)s : %(message)s',"%Y-%m-%d %H:%M:%S")
        if formatter == 'messageonly':
            formatter = logging.Formatter('%(message)s')
        fileHandler = logging.FileHandler(output_dir + file_prefix + logger_name + file_suffix)
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)

    logger.setLevel(level)
    return logger_name, logger_tag, logging.getLogger(logger_name)



class portTestTCPProtocol(Protocol):
   def dataReceived(self, data):
    data = data #+ ", " + str(self.transport.getPeer())
    self.transport.write(data)
    self.transport.loseConnection()
   
   def connectionMade(self): 
        print "Connection from : ", self.transport.getPeer()
        #self.transport.loseConnection() # terminate connection


class portTestUDPProtocol(DatagramProtocol):

    def sendDatagram(self,datagram):
        self.transport.write(datagram)
    

    def datagramReceived(self, datagram, host):
        print 'Datagram received from: ', self.transport.getPeer()
        datagram = datagram #+ ", " + str(self.transport.getPeer())
        self.sendDatagram(datagram)

class portTestClient(Protocol):
    def connectionMade(self):
        self.transport.write("Test!")

    def dataReceived(self, data):
        print("receive:", data)
        if data:
            print "Server said: ", data
            self.transport.loseConnection()

class portTestClientFactory(ClientFactory):
    protocol = portTestClient

    def clientConnectionFailed(self, connector, reason):
        print ("Connection failed:", reason.getErrorMessage())


    def clientConnectionLost(self, connector, reason):
        print("Connection lost:", reason.getErrorMessage())



def protocol_runner(protocol,port,f):
    
    if protocol == "TCP":
        f.protocol = portTestTCPProtocol
        
        try:
            reactor.listenTCP(port,f)
        except:
            pass
    else:
        f.protocol = portTestUDPProtocol
        try:
            reactor.listenUDP(port,f)
        except:
            pass


def run_server(profile):
    listeningPorts = [] 
    
    for i in profile['profile_ports']:
        f = ServerFactory()
        port = int(i['DestinationPort'])
        protocol = i['Protocol']
        if "%s/%s" % (protocol,port) in listeningPorts:
            pass
        else:    
            protocol_runner(protocol,port,f)
            listeningPorts.append("%s/%s" % (protocol,port))
            print "LISTENING %s/%s" % (protocol,port)

    reactor.run()


def run_client(profile,server):
    for i in profile['profile_ports']:
        f = portTestClientFactory()
        port = int(i['DestinationPort'])
        protocol = i['Protocol']

        reactor.connectTCP(server, port, f)
    reactor.run()





if __name__ == "__main__":

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
        profile = read_xml('application_map_SCOM2012R2.xml')
    else:
        print "Please provide an application network profile with the -a flag."
        sys.exit()

    if args.server:
        run_server(profile)
    elif args.client:
        run_client(profile,args.target)
    elif args.clientserver:
        run_client(profile,args.target)
    else:
        print "Please provide the mode that you'd like the script to run in."


