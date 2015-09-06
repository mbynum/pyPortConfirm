import socket

host = "104.236.3.208"

def DoesServiceExist(port):
    captive_dns_addr = ""
    host_addr = ""

    try:
        captive_dns_addr = socket.gethostbyname("BlahThisDomaynDontExist22.com")
    except:
        pass

    try:
        host_addr = socket.gethostbyname(host)

        if (captive_dns_addr == host_addr):
            return False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
    except:
        return False

    return True


testPorts = [25, 80, 110, 143, 389, 993, 995, 587, 50636]

for port in testPorts:
    print "Testing " + str(port) + "....."
    if DoesServiceExist(port):
        print "[ OK ]"
    else:
        print "[ FAIL ]"