from network import *
from pprint import pprint
import threading
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

    sites = { 5:('localhost', 10000), 1:('localhost', 10001), 2:('localhost', 10002), 3:('localhost', 10003), 4:('localhost', 10004) }
    failLock1 = threading.Event()
    failLock2 = threading.Event()
    failLock3 = threading.Event()
    failLock4 = threading.Event()
    failLock5 = threading.Event()
    network5 = Network( 'localhost', 10000, sites, 5, {'printLock':printLock, 'failLock': failLock5})
    network1 = Network( 'localhost', 10001, sites, 1, {'printLock':printLock, 'failLock':failLock1})
    network2 = Network( 'localhost', 10002, sites, 2, {'printLock':printLock, 'failLock':failLock2})
    network3 = Network( 'localhost', 10003, sites, 3, {'printLock':printLock, 'failLock':failLock3})
    network4 = Network( 'localhost', 10004, sites, 4, {'printLock':printLock, 'failLock':failLock4})
    dummy = Dummy()
    dummy.start()
    network1.start()
    network2.start()
    network3.start()
    network4.start()
    network5.start()
    failLock4.clear()
    failLock5.clear()

    network1.sendPreparePaxos('140 characters', ('localhost', 9999))
    time.sleep(5)
    failLock5.set()
    network2.sendPreparePaxos('240 characters', ('localhost', 9999))
    failLock1.clear()
    time.sleep(2)
    network3.sendPreparePaxos('340 characters', ('localhost', 9999))
    failLock4.set()

    failLock1.clear()
    failLock2.clear()
    failLock3.clear()
    time.sleep(3)
    network4.sendPreparePaxos('440 characters', ('localhost', 9999))
    network5.sendPreparePaxos('540 characters', ('localhost', 9999))
    dummy.join()
