# This is our network 'sub-thread' for a site.
import threading
import socket
import pickle
import time
import sys
from pprint import pprint

class Network(threading.Thread):
    def __init__(self, ipAddr, port, siteDirectory, siteID, lockDictionary):
        threading.Thread.__init__(self)
        self.portNum = port
        self.daemon = True
        self.ipAddr = ipAddr
        # format is {}[siteID] = (ip, port)
        self.siteDirectory = siteDirectory
        self.siteID = siteID
        # contains all locks shared w/ CLI
        self.lockDictionary = lockDictionary
        self.printLock = lockDictionary['printLock']
        self.failLock = lockDictionary['failLock']
        self.failLock.set()
        self.successMessages = set()
        self.failedMessages = set()

        self.logLock = threading.RLock()
        self.log = {}

        self.requestLock = threading.RLock()
        self.activeClientRequests = {}

        self.ballotNum = (0,0, self.siteID)
        self.acceptVal = None
        self.acceptNum = (0,0, 0)

        self.accepted = {}

    def run(self):
        gc = threading.Thread(target=self.garbageCollect)
        gc.start()
        # In this loop, we generate a new socket.
        while 1:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverAddress = (self.ipAddr, self.portNum)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(serverAddress)
            self.failLock.wait()
            sock.listen(1)
            # we accept connections until we get a fail event, then we close the socket and don't accept anything.
            while self.failLock.isSet():
                conn, addr = sock.accept()
                message = pickle.loads(conn.recv(2048))
                conn.close()
                thread = threading.Thread(target=self.handle,args=(message,))
                if self.failLock.isSet():
                    thread.start()
            sock.close()


    def handle(self, message):
        messageType = message['source']
        # We are either going to be receiving a message from a client or from another site.
        if (messageType == 'site'):
            action = message['action']
            returnAddress = message['return']
            # make sure we reset paxos settings when slot goes up
            if (action == 'prepare'):
                if message['ballotNum'][0] > len(self.log):
                    # If the spot being competed for is larger than the length of our log, then we are missing at least one entry and so we pretend we are a client and ask everyone to send us a log
                    self.broadcast({'source':'client', 'action':'read', 'return':self.siteDirectory[self.siteID], 'request':None})
                # otherwise, if someone is proposing for a spot that's already taken, we send them our log.
                elif message['ballotNum'][0] < len(self.log):
                    self.clientTalk({'action': 'read', 'success': True, 'contents':self.log, 'source':'site', 'return':self.siteDirectory[self.siteID], 'request':None}, returnAddress)

                if message['ballotNum'] >= self.ballotNum:
                    self.ballotNum = message['ballotNum']
                    # We are now competing for a NEW slot, so reset PAXOS conditions
                    if message['ballotNum'][0] > self.ballotNum[0]:
                        self.acceptNum = (message['ballotNum'][0], 0, 0)
                        self.acceptVal = None
                    self.sendAckPaxos(message)
                else:
                    self.sendNackPaxos(message)
            if (action == 'accept'):
                messageUniqueID = message['uniqueID']
                if message['ballotNum'] >= self.ballotNum:
                    self.acceptVal = message['value']
                    self.acceptNum = message['ballotNum']
                    if messageUniqueID in self.accepted:
                        self.accepted[messageUniqueID] += 1
                        # Deciding below. Decide on majority of acceptances.
                        if self.accepted[messageUniqueID] == 3:
                            with self.printLock:
                                print("Deciding! Taking %s for slot %i on %i" % (message['value'], message['ballotNum'][0], self.siteID) )
                            with self.logLock:
                                self.log[message['ballotNum'][0]] = message['value']
                                # Reset ballotNum, acceptVal, acceptNum because this round is over!
                                self.ballotNum = (len(self.log), 0, self.siteID)
                                self.acceptVal = None
                                self.acceptNum = (len(self.log), 0, 0)
                            # IF we were the original site to send out this request and we just decided, send back to the client that we did mannnng
                            # Only send success if the message that got posted is the one they originally requested. Otherwise we lost
                            # the round and we will tell the client we failed :(
                            # The other situation is that we won the election, but subsequently another winner beat us and had to adopt our value so we still succeeded.
                            with self.requestLock:
                                if any(map(lambda x: self.activeClientRequests[x]['initialValue'] == message['value'], self.activeClientRequests)) or message['uniqueID'] in self.activeClientRequests:
                                    with self.printLock:
                                        print ("I'm responsible for telling the client!")
                                    #please don't ask
                                    uniqueID = message['uniqueID'] if message['uniqueID'] in self.activeClientRequests else self.activeClientRequests[filter(lambda x: self.activeClientRequests[x]['initialValue'] == message['value'], self.activeClientRequests)[0]]['uniqueID']

                                    clientReturn = self.activeClientRequests[uniqueID]['return']
                                    initialValue = self.activeClientRequests[uniqueID]['initialValue']
                                    if initialValue == message['value']:
                                        self.clientTalk({'action': 'post', 'success':True, 'contents': (message['ballotNum'][0], initialValue), 'request':self.activeClientRequests[uniqueID]['request']}, clientReturn)
                                    else:
                                        self.clientTalk({'action': 'post', 'success':False, 'contents': (0, initialValue), 'request':self.activeClientRequests[uniqueID]['request']}, clientReturn)

                    # If this is the first time we've recieved an accept for this message, broadcast it to everyone
                    else:
                        self.accepted[messageUniqueID] = 0
                        self.broadcast(message)

            if (action == 'ack') and message['uniqueID'] in self.activeClientRequests:
                with self.lockDictionary['printLock']:
                    pprint(message)
                messageUniqueID = message['uniqueID']
                with self.requestLock:
                    if message['uniqueID'] in self.activeClientRequests:
                        self.activeClientRequests[messageUniqueID]['acks'].append(message)
                        # If we get 3 acks, then we have a majority so we start the accept phase. Guaranteed to only do this once because of the lock.
                        if (len(self.activeClientRequests[messageUniqueID]['acks']) == 3):
                            print("Received a majority of ACKs on site %i" % self.siteID)
                            # take the acceptVal with the highest acceptNum, or if they are all None simply take the initial vlaue.
                            highestVal = reduce(lambda acc, x1: x1 if (x1['acceptNum'] > acc['acceptNum'] and x1['acceptVal'] != None) else acc, self.activeClientRequests[messageUniqueID]['acks'], self.activeClientRequests[messageUniqueID]['acks'][0])
                            self.activeClientRequests[messageUniqueID]['value'] = highestVal['acceptVal'] if highestVal['acceptVal'] != None else self.activeClientRequests[messageUniqueID]['value']
                            # Then send our accepts
                            self.sendAcceptPaxos(self.activeClientRequests[messageUniqueID])
            if (action == 'nack'):
                messageUniqueID = message['uniqueID']
                with self.requestLock:
                    if message['uniqueID'] in self.activeClientRequests:
                        self.activeClientRequests[messageUniqueID]['nacks'].append(message)
                        # if 3 servers tell us our ballot number is too low, we will redo.
                        if(len(self.activeClientRequests[messageUniqueID]['nacks']) == 3):
                            self.sendPreparePaxos(self.activeClientRequests[messageUniqueID]['initialValue'], self.activeClientRequests[messageUniqueID]['return'],self.activeClientRequests[messageUniqueID]['request'] )
                            del self.activeClientRequests[messageUniqueID]
            if (action == 'read'):
                with self.logLock:
                    self.log = max(self.log, message['contents'], key=len)



        if (messageType == 'client'):
            action = message['action']
            returnAddress = message['return']
            # A client will either read from a site, or it will attempt to post a new message in which case we initiate PAXOS
            if (action == 'read'):
                self.clientTalk({'action': 'read', 'success': True, 'contents':self.log, 'source':'site', 'return':self.siteDirectory[self.siteID], 'request':message['request'] }, returnAddress)
            elif (action == 'post'):
                post = message['message']
                self.sendPreparePaxos(post, returnAddress, message['request'])

    def sendPreparePaxos(self, message, returnAddress, clientRequestID):
        with self.logLock, self.requestLock:
            uniqueID = hash(time.time())
            with self.printLock:
                print("UniqueID: %s for message %s" % (uniqueID, message))
            slot, num, ID = self.ballotNum
            # If the slot number is less than the length of our log, then we know it will not pass. So we set it to the max of the past slots and the length of our log. If slot is larger, then there are some values we don't know about it. If the log is larger, then...nothing makes sense?
            slot = max(slot, len(self.log))
            self.ballotNum = (slot, num + 1, self.siteID)
            clientRequest = {'return': returnAddress, 'value' : message, 'ballotNum': self.ballotNum, 'initialValue': message, 'acks' : [], 'nacks' : [], 'uniqueID':uniqueID, 'request':clientRequestID}
            self.activeClientRequests[uniqueID] = clientRequest
            prepareRequest = {'source': 'site', 'action':'prepare', 'return':self.siteDirectory[self.siteID], 'ballotNum': self.ballotNum, 'uniqueID':uniqueID}
            # here we automatically fail if we can't hit at least three sites with our prepare
            if (self.broadcast(prepareRequest) < 3):
                self.clientTalk({'action': 'post', 'success':False, 'contents': (0, message), 'request':clientRequestID}, returnAddress)
                del self.activeClientRequests[uniqueID]

    def sendAcceptPaxos(self, clientRequest):
        with self.requestLock:
            acceptRequest = {'source':'site', 'action':'accept', 'return':self.siteDirectory[self.siteID], 'ballotNum': clientRequest['ballotNum'], 'value':clientRequest['value'], 'uniqueID':clientRequest['uniqueID'] }
            if (self.broadcast(acceptRequest) < 3):
                self.clientTalk({'request':clientRequest['request'], 'action': 'post', 'success':False, 'contents': (0, clientRequest['initialValue'])}, clientRequest['return'])
                self.activeClientRequests.remove(clientRequest)

    def sendAckPaxos(self, acceptMessage):

        dest = acceptMessage['return']
        with self.logLock:
            ackMessage = {'source':'site', 'action':'ack', 'return':self.siteDirectory[self.siteID], 'ballotNum': acceptMessage['ballotNum'], 'acceptVal':self.acceptVal, 'acceptNum':self.acceptNum, 'uniqueID':acceptMessage['uniqueID'] }
            self.clientTalk(ackMessage, dest)

    def recoverLog(self):
        pass
    def garbageCollect(self):
        while 1:
            time.sleep(2)
            with self.requestLock, self.logLock:
                old = []
                for request in self.activeClientRequests:
                    clientRequest = self.activeClientRequests[request]
                    if clientRequest['ballotNum'][0] < len(self.log) and self.log[clientRequest['ballotNum'][0]] != clientRequest['initialValue']:
                        self.clientTalk({'action': 'post', 'success':False, 'contents': (0, clientRequest['initialValue']), 'request':clientRequest['request']}, clientRequest['return'])
                        old.append(request)
                for i in old:
                    del self.activeClientRequests[i]

    def sendNackPaxos(self, acceptMessage):
        dest = acceptMessage['return']
        with self.logLock:
            nackMessage = {'source':'site', 'action':'nack', 'return':self.siteDirectory[self.siteID], 'ballotNum': acceptMessage['ballotNum'], 'acceptVal':self.acceptVal, 'acceptNum':self.acceptNum, 'uniqueID':acceptMessage['uniqueID'] }
            self.clientTalk(nackMessage, dest)
    # Broadcast to everyone including yourself
    def broadcast(self, message):
        numSuccessful = 0
        for site in self.siteDirectory:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect(self.siteDirectory[site])
                sock.sendall(pickle.dumps(message))
                sock.close()
                numSuccessful += 1
            except:
                pass
        return numSuccessful
    def clientTalk(self, message, clientAddress):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(clientAddress)
            sock.sendall(pickle.dumps(message))
            sock.close()
        except:
            pass









