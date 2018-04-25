#!/usr/bin/env python3

import rc
import sys

talk_name = sys.argv[1]

print("Making slide video for talk {}".format(talk_name))

rc.make_slide_video(talk_name)
