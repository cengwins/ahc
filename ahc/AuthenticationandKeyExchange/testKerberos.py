#!/usr/bin/env python

"""
Implementation of the "Kerberos" as described in the textbook
"Schneier, Bruce. Applied cryptography: protocols, algorithms,
 and source code in C. John Wiley & Sons, 2007 (20th Anniversary Edition)"
"""
import random
import string

from Ahc import ConnectorTypes, Topology, registry
from AuthenticationandKeyExchange.Kerberos import *
from time import sleep
from cryptography.hazmat.primitives import *
from cryptography.hazmat.primitives.asymmetric import rsa
import matplotlib.pyplot as plt


def main():
    topo = Topology()
    topo.construct_single_node(Node,0)
    topo.start()
    while (True):pass


if __name__ == "__main__":
    main()

'''

def main():
    Kerb = Kerberos()

    Clients = []
    for x in range(0,20):
        name = (''.join(random.choice(string.ascii_lowercase) for i in range(10)))
        id = x
        temp = Client(name , id )
        print("Client created as ",temp.unique_name())
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,

        )
        public_key = private_key.public_key()
        temp.privatekey = private_key
        Kerb.add_key_with_client(temp, public_key)

        Clients.append(temp)

        Kerb.connectMeToComponent(ConnectorTypes.DOWN, temp)
        temp.connectMeToComponent(ConnectorTypes.UP, Kerb)

        for y in Clients:
            temp.connectMeToComponent(ConnectorTypes.PEER, y)
            y.connectMeToComponent(ConnectorTypes.PEER, temp)

    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    start_times = {}
    paddingsize = [64,128,256,512,1024]
    keysize= [16,24,32]

    cellvalue = []

    done = []
    for x in keysize:
        temp = []
        for y in paddingsize:
            counter = 0
            time = 0
            while counter != 3:
                vals = random.sample(Clients,2)
                if vals not in done and [vals[1],vals[0]] not in done:
                    done.append(vals)
                    print("Connection from",vals[0].unique_name()," to ",vals[1].unique_name())

                    start_times[vals[0].unique_name()] = datetime.datetime.now()
                    vals[0].create_connection_to_client(vals[1],y,x)
                    sleep(1)
                    time += (vals[0].finishtime-start_times[vals[0].unique_name()]).total_seconds()* 1000
                    print((vals[0].finishtime-start_times[vals[0].unique_name()]).total_seconds()* 1000,"time for Connection from",vals[0].unique_name()," to ",vals[1].unique_name(), )
                    counter+=1
            temp.append(round(time/3, 3))

        cellvalue.append(temp)


    column_labels = list( ("Padding Length:"+x.__str__()+" bit") for x in paddingsize)
    row_labels = list( ("Key Length:"+(x*8).__str__()+" bit") for x in keysize)
    ax.table(cellText=cellvalue,rowLabels=row_labels, colLabels=column_labels, loc='center')
    fig.tight_layout()
    fig.set_dpi(300)
    plt.show()
    for x in Clients:
        print(x.unique_name(),x.keypairs)
    sleep(10000.0 )
    pass


if __name__ == "__main__":
    main()
'''