#!/usr/bin/env python3

import rc
import sys

talk_name = sys.argv[1]

print("Making video for talk {}".format(talk_name))

rc.make_talk_video(talk_name)
