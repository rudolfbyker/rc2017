#!/usr/bin/env python3

import rc
import sys

qa_name = sys.argv[1]

print("Extracting Q&A session {}".format(qa_name))

rc.extract_qa(qa_name)
