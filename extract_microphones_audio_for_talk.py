#!/usr/bin/env python3

import rc
import sys

talk_name = sys.argv[1]

print("Extracting microphones audio for talk {}".format(talk_name))

rc.extract_microphones_audio_for_talk(talk_name)
