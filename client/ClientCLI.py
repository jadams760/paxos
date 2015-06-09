import threading
import pickle
import re
import os
import socket
import time
import random
import ClientServer
import sys


sites = [('localhost',10001),('localhost',10002),('localhost',10003),('localhost',10004),('localhost',10005)]


class ClientCLI(threading.Thread):
    def __init__(self, hostname, port, sites, clientNum):
        self.thread = threading.Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        self.sites = sites
        self.leader =0
        self.server = ClientServer.ClientServer(self.hostname,self.port)
        self.requestNum = 0
        self.clientNum = clientNum

        
    def myConnect(self,sock,host,port):
        sock.connect((host,port))

    def mySend(self,sock,send):
        sock.send(pickle.dumps(send, protocol=2))



    def run(self):
        self.server.start()
        while True:

            userInput = input("Please Enter One of the Following and Press Enter:\n(1) Read\n(2) Post\n(3) Exit\n")
            if userInput == "1":
                leaderFound = False
                while leaderFound == False:
                    print("Connecting to Site " + str(self.leader))
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.myConnect(sock, self.sites[self.leader][0], self.sites[self.leader][1])
                        leaderFound = True
                    except ConnectionRefusedError:
                        self.leader = random.randint(0,4)
                        print('connection refused')

                    
                request = str(self.clientNum) + "_" + str(self.requestNum)
                send = {'time':time.time(), 'request':request, 'action':'read', 'return':(self.hostname, self.port), 'message':'', 'source':'client'}
                self.requestNum += 1
                self.server.requests.append(send)
                self.mySend(sock,send)
                sock.close()
                time.sleep(2)
                
            elif userInput == "2":
                userInput = input("Please enter a message to append:\n")
                userInput = userInput[:140]
                leaderFound = False
                while leaderFound == False:
                    print("Connecting to Site " + str(self.leader))
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.myConnect(sock, self.sites[self.leader][0], self.sites[self.leader][1])
                        leaderFound = True
                    except ConnectionRefusedError:
                        self.leader = random.randint(0,4)
                        print('connection refused')

                print('connected to site ' + str(self.leader))
                request = str(self.clientNum) + "_" + str(self.requestNum)
                send = {'time': time.time(), 'request':request, 'action':'post', 'return':(self.hostname, self.port), 'message':userInput, 'source':'client'}
                self.server.requests.append(send)
                self.requestNum += 1
                self.mySend(sock,send)
                print('send to site ' + str(self.leader))
                sock.close()
                time.sleep(2)
                    
            elif userInput == "3":
                return False

            else:
                print("Incorrect input type\n")
