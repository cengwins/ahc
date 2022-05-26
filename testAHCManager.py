

import queue
from multiprocessing.managers import BaseManager
from multiprocessing.context import BaseContext
from multiprocessing import Queue

import sys, os, signal
import argparse
import configparser
from adhoccomputing.Distribution.AHCManager import AHCManager, AHCManagerType


def parse_args(argv):
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


def main(argv):
    ahcmanager = AHCManager(AHCManagerType.AHC_CLIENT, argv)
    ahcmanager.connect()
    queue = ahcmanager.get_queue(10)
    print(queue.get())

if __name__ == "__main__":
   # freeze_support()
    main(sys.argv)