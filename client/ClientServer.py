import threading
import socket
import pickle


class ClientServer(threading.Thread):
    def __init__(self, hostname, port):
        threading.Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        self.daemon = True
        

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverAddress = (self.hostname, self.port)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(serverAddress)
        sock.listen(1)
        
        while 1:
            print(self.hostname + str(self.port))
            recSock, addr = sock.accept()
            print('starting thread')
            thread = threading.Thread(target=self.receive,args=(recSock,))
            thread.start()
            print('started')

    def myReceive(self,rSock):
        receive = rSock.recv(4096)
        return pickle.loads(receive)
    
    def receive(self, recSock):
        print('before receive')
        receive = self.myReceive(recSock)
        print('received')

        if(receive['action'] == 'read'):
            if(receive['success'] == False):
                print("Read Unsuccessful\n")
            else:
                for item in receive['contents']:
                    print(item)

        elif(receive['action'] == 'post'):
            if(receive['success'] == False):
                print("Post Unsuccessful for (ID,Msg): (" + receive['contents'][0] + ', "' + receive['contents'][1] + "\")\n")
            else:
                print("Post Successful (ID,Msg): (" + receive['contents'][0] + ', "' + receive['contents'][1] + "\")\n")

                            
