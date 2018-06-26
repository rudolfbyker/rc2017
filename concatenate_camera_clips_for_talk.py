#!/usr/bin/env python3

import rc
import sys

talk_name = sys.argv[1]

print("Concatenating camera clips for talk {}".format(talk_name))

rc.concatenate_camera_clips_for_talk(talk_name)
