import threading
import pickle
import re
import os
import socket
import network
import time
import random
import sys


class SiteCLI(threading.Thread):
    def __init__(self, hostname, port, sites, siteID):
        threading.Thread.__init__(self)
        self.failLock = threading.Event()
        self.failLock.set()
        self.locks = { 'printLock': threading.RLock(), 'failLock': self.failLock }
        self.hostname = hostname
        self.port = port
        self.sites = sites
        self.network = network.Network(hostname, port, sites, siteID, self.locks)
        self.siteID = siteID

    def run(self):
        self.network.start()
        while True:
            userInput = raw_input("Please Enter One of the Following and Press Enter:\n(1) Fail\n(2) Recover\n(3) Exit\n")
            if userInput == '1':
                self.failLock.clear()
                print ("Site going down.")
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect(self.sites[self.siteID])
                    sock.send(pickle.dumps(""))
                    sock.close()
                except:
                    pass


            elif userInput == '2':
                print("Site coming back up!")
                self.failLock.set()
            elif userInput == '3':
                self.failLock.clear()
                sys.exit()

            else:
                print("Incorrect input type\n")
