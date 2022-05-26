from enum import Enum
import queue
from multiprocessing.managers import BaseManager
from multiprocessing.context import BaseContext
from multiprocessing import Queue

import sys, os, signal
import argparse
import configparser

#Should there be need we can extend
class AHCBaseManager(BaseManager): pass

class AHCManagerType(Enum):
    AHC_SERVER = "ahc_server"
    AHC_CLIENT = "ahc_client"

class AHCManager():

    def __init__(self, type:AHCManagerType, argv) -> None:
        self.argv = argv
        self.authkey = b"01032016"
        self.address = self.parse_args(self.argv)
        AHCBaseManager.register('create_and_return_queue', callable=self.create_and_return_queue)
        self.ahcbasemanager = AHCBaseManager(address=self.address, authkey=self.authkey)
        self.queues=[]
        if type==AHCManagerType.AHC_SERVER:
            print(self.address)
            self.ahcbaseserver = self.ahcbasemanager.get_server()
        else:
            if type==AHCManagerType.AHC_CLIENT:
                pass
            else:
                print("Wrong AHC distribution type")

    def connect(self):
        self.ahcbasemanager.connect()

    def get_queue(self, maxsize):
        return self.ahcbasemanager.create_and_return_queue(maxsize)
      
    def create_and_return_queue(self, maxsize):
        q = Queue(maxsize = maxsize)
        #q.put("Deneme")
        self.queues.append(q)
        return q

            
    def parse_args(self, argv):
        config = configparser.ConfigParser()
        if argv is None:
            print(f"Usage: {__name__} -c (--config_file)")
        else:
            argv = sys.argv
            conf_parser = argparse.ArgumentParser(
            description=__doc__, # printed with -h/--help
            # Don't mess with format of description
            formatter_class=argparse.RawDescriptionHelpFormatter,
            # Turn off help, so we print all options in response to -h
            add_help=False
            )
            conf_parser.add_argument("-c", "--conf_file",
                            help="Specify config file", metavar="FILE")
            conf_parser.add_argument("-s", "--section",
                            help="Specify config file", metavar="FILE")
            
            args, remaining_argv = conf_parser.parse_known_args()
            DomainName = "localhost"
            Port = 9000
            if args.conf_file:
                config.read(args.conf_file)
                print(config.sections())
                if (args.section in config):
                    conf = config[args.section]
                    DomainName = conf['DomainName']
                    Port = conf['Port']

            print(f"{DomainName}:{Port}  will be the manager address")
            address = (DomainName, Port)
            return address
    

    def serve_forever(self ):
        self.ahcbaseserver.serve_forever()


def main(argv):
    ahcmanager = AHCManager(AHCManagerType.AHC_SERVER, argv)
    ahcmanager.serve_forever()

if __name__ == "__main__":
   # freeze_support()
    main(sys.argv)

