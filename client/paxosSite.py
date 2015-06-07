import threading
import socket
import pickle


class paxosSite(threading.Thread):
    def __init__(self, hostname, port):
        threading.Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        self.log = ['this','that']
        
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverAddress = (self.hostname, self.port)
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(serverAddress)
        sock.listen(1)
        print('keyboard interrupt to block')
        while 1:
            recSock, addr = sock.accept()
            thread = threading.Thread(target=self.receive,args=(recSock,))
            thread.start()

            
    def myConnect(self,sock,host,port):
        sock.connect((host,port))

    def mySend(self,sock,send):
        sock.send(pickle.dumps(send))

    def myReceive(self,sock):
        receive = sock.recv(4096)
        return pickle.loads(receive)
    
    def receive(self, recSock):
        receive = self.myReceive(recSock)


        replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if(receive['action'] == 'read'):
            print('read')
            print(receive['return'][0] + str(receive['return'][1]))
            self.myConnect(replySock, receive['return'][0],receive['return'][1])
            print('connected')
            send = {'action':'read', 'success':True, 'contents':self.log}
            self.mySend(replySock,send)
            replySock.close()

        elif(receive['action'] == 'post'):
            print('post')
            self.log.append(receive['message'])
            self.myConnect(replySock, receive['return'][0],receive['return'][1])
            send = {'action':'read', 'success':True, 'contents':(len(self.log), self.log[len(self.log)-1])}
            self.mySend(replySock,send)
            replySock.close()

   # action, success, contents
