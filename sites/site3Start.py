from network import *
from pprint import pprint
import threading
import SiteCLI
import time

printLock = threading.RLock()
class Dummy(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverAddress = ('localhost', 9999)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(serverAddress)
        sock.listen(1)
        while 1:
            conn, addr = sock.accept()
            message = pickle.loads(conn.recv(4092))
            conn.send('ack')
            with printLock:
                pprint(message)
            conn.close()



if __name__ == '__main__':

    sites = { 5:('54.94.238.121', 10000), 1:('52.1.255.120', 10000), 2:('52.8.104.33', 10000), 3:('52.74.168.17', 10000), 4:('52.64.98.238', 10000) }
    site = SiteCLI.SiteCLI( '52.74.168.17', 10000, sites, 3)
    site.start()
    site.join()
