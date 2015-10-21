#!/usr/bin/python
from twisted.internet.protocol import Protocol,ServerFactory,ClientFactory,DatagramProtocol
from twisted.internet import reactor

import xml.etree.ElementTree as ET
import cmd2, logging

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


profile = read_xml('application_map_SCOM2012R2.xml')

#run_server(profile)

run_client(profile,'localhost')

'''

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Softchoice pyPortConfirm for testing application port availability across a network')
    parser.add_argument('--appnetprofile','-a', nargs='?', metavar = 'FILENAME',
                        help='After this flag, provide the location of the application network profile: C:\\Users\\tempuser\\Desktop\\list.csv')
    parser.add_argument('--server','-s', nargs='?', metavar = 'IPADDRESS',
                       help='Specify a the destination (if this is being run in client mode) to establish connections to.')
    parser.add_argument('--verbose','-v', action='store_true',
                        help="Use this to provide more verbosity as output is generated.")
    parser.add_argument('--version','-V', action='store_true',
                        help = "Displays the current version.")
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--server','-s', action='store_true',
                        help="Use this to provide more verbosity as output is generated.")
    group2.add_argument('--client','-c', action='store_true',
                        help="Use this to provide more verbosity as output is generated.")
    

    parser.add_argument('--mode','-m', nargs='?',default='privexec',choices=['privexec','config','testprivexec','testconfig','buildconfig'],
                        help='Choose the command mode.  The main ptions are privexec or config, but you can also add the word test on the front of those to simulate what would happen with the other details you have provided.  Defaults to privexec.')
    parser.add_argument('--largeoutput','-l', action='store_true',
                        help='Set this if the output expected from a passed command is that of a full "show run" or "show tech".')
    parser.add_argument('--interactive','-i', action='store_true',
                       help='Use this to be prompted before every action.')
    args = parser.parse_args()
    print "\n"

 '''