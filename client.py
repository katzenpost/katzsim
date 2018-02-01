from twisted.internet import reactor
from numpy.random import poisson

import requests
import katzenpost

NUM_CLIENTS = 5

PKI_KEY = "900895721381C0756D28954524BB1D090F54C8DD9295F84B1D8A93F1E3C17AD8"
PkI_ADDR ="192.0.2.1:29483"
MINUTE = 60


class Agent(object):
    """
    An that models the scheduling of outgoing messages,
    following a Poisson process.
    """

    name = "client"

    def __init__(self, cid, rate=2, client=None):
        """
        :param cid: client identifier.
        :param rate: the average rate of messages sent for minute.
        """
        self.running = False
        self.cid = cid
        self.rate = msg_rate
        self.client = client

    @property
    def label(self):
        return self.name + str(self.cid)

    def run(self):
        self.schedule()
        self.running = True

    def stop(self):
        self.running = False

    def send(self, recipient="", msg=""):
        print "%s sending a message" % self.label
        if self.client:
            self.client.send(recipient, msg)
        if self.running:
            self.schedule()

    def schedule(self):
        reactor.callLater(self.next_event(), self.send)

    def next_event(self):
        return poisson(MINUTE/self.rate)

    def __repr__(self):
        return self.label + self.cid


def start_all(clients):
    for client in clients:
        client.run()

def stop_all(clients):
    for client in clients:
        client.stop()


class KatzenClient(object):
    """
    A client that handles registration and actual sending of messages.
    """

    def __init__(self, user, provider):
        self.user = user
        self.provider = provider
        self._linkkey = None
        self._client = None
        self.genkey()
        self.register()
        self.initialize()

    def initialize(self):
        key = katzenpost.StringToKey(self._linkKey)
        cfg = katzenpost.Config(
            PkiAddress=PKI_ADDR,
            PkiKey=PKI_KEY,
            User=self.user,
            LinkKey=key,
            Provider=self.provider,
            Log=katzenpost.LogConfig()
        )
        self._client = katzenpost.New(cfg)

    def genkey(self):
        self._linkkey = katzenpost.GenKey()

    def register(self):
        pass

    def send(self, recipient, msg):
        mail = """From: {user}@{provider}
        To: {recipient}@{provider}
        Subject: hello

        {msg}.
        """.format(
            user=self.user,
            provider=self.provider,
            recipient=recipient,
            msg=msg)
        self._client.Send("{recipient}@{provider}".format(
            recipient=recipient,
            provider=self.provider), mail)
        self.receive()

    def receive(self):
        try:
            m = self._client.GetMessage(1)
        except RuntimeError:
            continue
        print("{user} GOT MESSAGE FROM {sender}".format(
            user=self.user, sender=m.Sender))


def simulate():
    agents = []
    for i in range(NUM_CLIENTS):
        client = KatzenClient()
        agents.append(Agent(i))
    start_all(clients)
    reactor.run()



if __name__ == "__main__":
    print ">>> Starting client run"
    simulate()
