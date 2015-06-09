import threading
from pprint import pprint
import socket
import pickle
import time

class ClientServer(threading.Thread):
    def __init__(self, hostname, port):
        threading.Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        self.daemon = True
        self.requests = []

    def garbageCollect(self):
        while 1:
            tmp = []
            time.sleep(1)
            for req in self.requests:
                if (time.time() - req['time'] > 5):
                    tmp.append(req)
            for i in tmp:
                print("Removing %s\n retry request\n" % str(i))
                self.requests.remove(i)
            


    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverAddress = (self.hostname, self.port)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(serverAddress)
        sock.listen(1)
        gc = threading.Thread(target=self.garbageCollect,args=())
        gc.start()
        while 1:
            recSock, addr = sock.accept()
            thread = threading.Thread(target=self.receive,args=(recSock,))
            thread.start()

    def myReceive(self,rSock):
        receive = rSock.recv(4096)
        return pickle.loads(receive)
    
    def receive(self, recSock):

        receive = self.myReceive(recSock)

        if(receive['action'] == 'read'):
            if(receive['success'] == False):
                for req in self.requests:
                    if receive['request'] == req['request']:
                        self.requests.remove(req)
                print("Read Unsuccessful\n")
            else:
                 for req in self.requests:
                    if receive['request'] == req['request']:
                        self.requests.remove(req)

                 for item in receive['contents']:
                    print(str(item) + "\t" + receive['contents'][item])
                 print('\n')
                

        elif(receive['action'] == 'post'):
            if(receive['success'] == False):
                for req in self.requests:
                    if receive['request'] == req['request']:
                        self.requests.remove(req)
                print("Post Unsuccessful for (ID,Msg): (" +  str(receive['contents'][0]) + ', "' + receive['contents'][1] + "\")\n")
                
            else:
                 for req in self.requests:
                    if receive['request'] == req['request']:
                        self.requests.remove(req)
                        
                 print("Post Successful (ID,Msg): (" + str(receive['contents'][0]) + ', "' + receive['contents'][1] + "\")\n")



                            
