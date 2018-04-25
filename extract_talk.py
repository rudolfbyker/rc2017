#!/usr/bin/env python

import rc
import sys

talk_name = sys.argv[1]

print("Extracting talk {}".format(talk_name))

rc.extract_talk(talk_name)
