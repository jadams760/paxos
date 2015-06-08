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
        self.locks = { 'printLock': threading.RLock(), 'failLock': self.failLock }
        self.hostname = hostname
        self.port = port
        self.sites = sites
        self.network = network.Network(hostname, port, sites, siteID, self.locks)

    def run(self):
        self.network.start()
        while True:
            userInput = input("Please Enter One of the Following and Press Enter:\n(1) Fail\n(2) Recover\n")
            if userInput == 1:
                self.failLock.clear()

            elif userInput == 2:
                self.failLock.set()

            else:
                print("Incorrect input type\n")
