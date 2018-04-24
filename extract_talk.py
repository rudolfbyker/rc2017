#!/usr/bin/env python

import rc
import sys
import os

parameters = rc.get_parameters()
talk_name = sys.argv[1]

print "Extracting talk {}".format(talk_name)

t = rc.load_talk_info(talk_name)

rc.extract_talk(
    output_filename=t[0],
    input_dir=os.path.join(parameters['rc_base_folder'], t[1]),
    start_vid=int(t[2]),
    start_time_ms=int(t[3]),
    stop_vid=int(t[4]),
    stop_time_ms=int(t[5]),
    output_dir=parameters['output_folder']
)
