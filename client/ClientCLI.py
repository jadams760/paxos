import threading
import pickle
import re
import os
import socket
import time
import random
import ClientServer
import sys


sites = [('localhost',9001),('localhost',9002),('localhost',9003),('localhost',9004),('localhost',9005)]
#sites = [('localhost',9001)]


class ClientCLI(threading.Thread):
    def __init__(self, hostname, port, sites):
        self.thread = threading.Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        self.sites = sites
        self.leader =0
        self.server = ClientServer.ClientServer(self.hostname,self.port)
        
        
    def myConnect(self,sock,host,port):
        sock.connect((host,port))

    def mySend(self,sock,send):
        sock.send(pickle.dumps(send))



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
                        print('connection refused')

                    self.leader = random.randint(0,4)
  
                send = {'action':'read', 'return':(self.hostname, self.port), 'message':'', 'source':'client'}
                self.mySend(sock,send)
                sock.close()
            
                
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
                        print('connection refused')

                    self.leader = random.randint(0,4)

                send = {'action':'post', 'return':(self.hostname, self.port), 'message':userInput, 'source':'client'}
                self.mySend(sock,send)
                sock.close()
                    
            elif userInput == "3":
                return False

            else:
                print("Incorrect input type\n")
