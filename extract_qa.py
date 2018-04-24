#!/usr/bin/env python

import rc
import sys
import os

parameters = rc.get_parameters()
qa_name = sys.argv[1]

print("Extracting Q&A session {}".format(qa_name))

qa = rc.load_qa_info(qa_name)

rc.extract_qa(
    output_filename=qa[0],
    output_dir=parameters['output_folder'],
    cam1_input_folder=os.path.join(parameters['rc_base_folder'], qa[1]),
    cam2_input_folder=os.path.join(parameters['rc_base_folder'], qa[2]),
    sync_delay_ms=int(qa[3]),
    cam1_start_video=int(qa[4]),
    cam1_start_time_ms=int(qa[5]),
    cam1_stop_video=int(qa[6]),
    cam1_stop_time_ms=int(qa[7]),
    cam2_start_video=int(qa[8]),
    cam2_stop_video=int(qa[9]),
    dry_run=False
)
