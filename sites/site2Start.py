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

    sites = { 5:('localhost', 10005), 1:('localhost', 10001), 2:('localhost', 10002), 3:('localhost', 10003), 4:('localhost', 10004) }
    site = SiteCLI( 'localhost', 10002, sites, 2)
    site.start()
