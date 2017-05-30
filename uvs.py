#! /usr/bin/env python


import os
import sys
import argparse
import getpass


from libuvs import cryptmanager as cm
from libuvs import cryptdefaults
from libuvs import log
from libuvs import util



def _parse_cmdline():
    """ Given command line arguments to the program are in the arguments list, parse and process them. """

    parser = argparse.ArgumentParser(description='UVSource - End to End Encrypted Distributed Version Control System')
    parser.add_argument("subcmd1", help="what should uvs do", choices=['init', 'stage', 'commit', 'branch', 'merge'])
    args = parser.parse_args()

    # print type(args) returns  <class 'argparse.Namespace'>
    #log.vvv("argparse args: " + str(args))

    if 'init' == args.subcmd1:
        log.vvv(">>>> init sub command called.")

    elif 'stage' == args.subcmd1:
        log.vvv(">>>> stage sub command called.")

    elif 'commit' == args.subcmd1:
        log.vvv(">>>> commit sub command called.")

    elif 'branch' == args.subcmd1:
        log.vvv(">>>> branch sub command called.")

    elif 'merge' == args.subcmd1:
        log.vvv(">>>> merge sub command called.")







if "__main__" == __name__:
    _parse_cmdline()
