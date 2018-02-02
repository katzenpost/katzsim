from twisted.internet import reactor
from numpy.random import poisson

import requests
import katzenpost

# ------- TUNING PARAMETERS ---------
NUM_CLIENTS = 2
RATE = 10
# -----------------------------------

PKI_ADDR ="37.218.242.147:29485"
PKI_KEY ="DFD5E1A26E9B3EF7B3DA0102002B93C66FC36B12D14C608C3FBFCA03BF3EBCDC"
MINUTE = 60.0
COMMON_IDKEY = "2FE57DA347CD62431528DAAC5FBB290730FFF684AFC4CFC2ED90995F58CB3B74"


class Agent(object):
    """
    An agent that models the scheduling of outgoing messages,
    following a Poisson process.
    """

    name = "client"

    def __init__(self, cid, rate=RATE, client=None):
        """
        :param cid: client identifier.
        :param rate: the average rate of messages sent for minute.
        """
        self.running = False
        self.cid = cid
        self.rate = rate
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


class KatzenClient(object):
    """
    A client that handles registration and actual sending of messages.
    """

    def __init__(self, user, provider, register=True):
        self.user = user
        self.provider = provider
        self._linkkey = None
        self._client = None
        self._counter = 0
        self.genkey()
        if register:
            self.register()
        self.initialize()

    def initialize(self):
        print "USER", self.user
        cfg = katzenpost.Config(
            PkiAddress=PKI_ADDR,
            PkiKey=PKI_KEY,
            User=str(self.user),
            LinkKey=self._linkkey,
            Provider=self.provider,
            Log=katzenpost.LogConfig()
        )
        self._client = katzenpost.New(cfg)

    def genkey(self):
        self._linkkey = katzenpost.GenKey()

    def register(self):
        idkey = katzenpost.StringToKey(COMMON_IDKEY)
        r = requests.post('http://{provider}:7900/register'.format(
            provider=self.provider),
            {'linkkey': self._linkkey.Public,
             'idkey': idkey.Public})
        username = r.json().get('register')
        print("Registered username for {client}: {username}".format(
            client=self.user,
            username=username))
        self.user = username

    def send(self, recipient, msg=None):
        print "RECIPIENT", recipient
        recipient = 'embarrassedlynx71'
        self._counter += 1
        if msg is None:
            msg = str(self._counter)
        mail = """From: <{user}@{provider}>
        To: <{recipient}@{provider}>
        Subject: hello

        {msg}.
        """.format(
            user=self.user,
            provider=self.provider,
            recipient=recipient,
            msg=msg)
        # print(">>>SENDING msg", mail)
        self._client.Send(str("<{recipient}@{provider}>").format(
            recipient=recipient,
            provider=self.provider), str(mail))
        self.receive()

    def receive(self):
        try:
            m = self._client.GetMessage(1)
            print("{user} GOT MESSAGE FROM {sender}".format(
                user=self.user, sender=m.Sender))
        except RuntimeError:
            pass


def simulate():
    agents = []
    for i in range(NUM_CLIENTS):
        client = None
        client = KatzenClient('client'+str(i), 'idefix', register=True)
        agents.append(Agent(i, client=client))
    start_all(agents)
    reactor.run()


def start_all(clients):
    for client in clients:
        client.run()


def stop_all(clients):
    for client in clients:
        client.stop()


if __name__ == "__main__":
    print ">>> Starting client run"
    simulate()