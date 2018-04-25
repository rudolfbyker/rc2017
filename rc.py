from ODSReader.ODSReader import ODSReader
import subprocess
import os
import functools
from datetime import datetime, timedelta

info_file = 'rc2017.ods'


def make_slide_video(name):
    parameters = get_parameters()

    slides = read_slide_timings(name)
    slide_mux_filename = os.path.join(parameters['output_folder'], '{}_slides.mux'.format(name))
    write_slide_timings_mux_file(slides, slide_mux_filename)

    slide_video_filename = os.path.join(parameters['output_folder'], '{}_slides.mp4'.format(name))
    subprocess.check_call([
        'ffmpeg',
        # global options:
        '-y',  # overwrite
        # input stream 0:
        '-safe', '0',  # allow absolute paths
        '-f', 'concat',
        '-i', slide_mux_filename,
        # output options:
        '-an',  # no audio
        '-c:v', 'libx264',
        slide_video_filename
    ])  # TODO: scale??


def read_stream_timings(name):
    stream_map = {
        1: 'camera',
        2: 'slides',
    }
    parameters = get_parameters()
    stream_timings_file = os.path.join(parameters['rc_base_folder'], 'timing', name, 'streams_timings--{}.txt'.format(name))
    streams = []
    with open(stream_timings_file, 'r') as f:
        for line in f:
            stream_time, stream_number = line.strip().split('->')
            ref_time = datetime.strptime('0:00:00', '%H:%M:%S')
            streams.append({
                'time': datetime.strptime(stream_time, '%H:%M:%S') - ref_time,
                'name': stream_map[int(stream_number)],
            })

    # If there are duplicate times, keep only the last one
    streams = [streams[i] for i in range(len(streams)) if i == len(streams) - 1 or streams[i]['time'] != streams[i + 1]['time']]

    # If there are duplicate stream names, keep only the first one
    streams = [streams[i] for i in range(len(streams)) if i == 0 or streams[i]['name'] != streams[i - 1]['name']]

    return streams


def read_slide_timings(name):
    parameters = get_parameters()
    slide_timings_file = os.path.join(parameters['rc_base_folder'], 'timing', name, 'slide_timings--{}.txt'.format(name))
    slides = []
    with open(slide_timings_file, 'r') as f:
        for line in f:
            slide_time, slide_filename = line.strip().split('->')
            ref_time = datetime.strptime('0:00:00', '%H:%M:%S')
            slides.append({
                'time': datetime.strptime(slide_time, '%H:%M:%S') - ref_time,
                'filename': os.path.join(parameters['rc_base_folder'], 'slides', name, slide_filename)
            })

    # If there are duplicate times, keep only the last one
    slides = [slides[i] for i in range(len(slides)) if i == len(slides) - 1 or slides[i]['time'] != slides[i + 1]['time']]

    # If there are duplicate filenames, keep only the first one
    slides = [slides[i] for i in range(len(slides)) if i == 0 or slides[i]['filename'] != slides[i - 1]['filename']]

    return slides


def write_stream_timings_cmd_file(stream_timings, output_filename):
    stream_map = {
        'slides': 0,
        'camera': 1,
    }
    with open(output_filename, 'w') as f:
        for stream in stream_timings:
            f.write("{} streamselect map {}\n".format(stream['time'], stream_map[stream['name']]))


def write_slide_timings_mux_file(slide_timings, output_filename):
    """
    Prepare a file for the ffmpeg concat demuxer
    See https://trac.ffmpeg.org/wiki/Slideshow

    :param slide_timings:

    :param output_filename:

    :return:

    """
    with open(output_filename, 'w') as f:
        previous_time = timedelta()
        for slide in slide_timings:
            f.write("file '{}'\n".format(slide['filename']))
            f.write("duration {}\n".format(slide['time'] - previous_time))
            previous_time = slide['time']
        # Due to an issue in ffmpeg, we have to repeat the last filename
        f.write("file '{}'\n".format(slide_timings[-1]['filename']))


def media_length(filename):
    try:
        return int(subprocess.check_output(['mediainfo', '--Inform=General;%Duration%', filename]))
    except:
        raise RuntimeError('Is mediainfo installed? On linux, try: sudo apt install mediainfo')


def extract_talk(name):
    talk_info = load_talk_info(name)
    parameters = get_parameters()

    input_files = [os.path.join(talk_info['input_folder'], "MVI_{:04d}.MP4".format(i)) for i in range(
        talk_info['start_video'],
        talk_info['stop_video'] + 1
    )]
    ffmpeg_ss = talk_info['start_time_ms']
    ffmpeg_to = sum(media_length(f) for f in input_files[:-1]) + talk_info['stop_time_ms']

    camera_mux_filename = os.path.join(parameters['output_dir'], '{}_camera.mux'.format(name))
    with open(camera_mux_filename, 'w') as list_file:
        list_file.write("\n".join("file '{}'".format(f) for f in input_files))

    video_filename = os.path.join(parameters['output_dir'], '{}.mp4'.format(name))
    subprocess.check_call([
        'ffmpeg',
        # global options:
        '-y',  # overwrite
        # input stream 0:
        '-safe', '0',  # allow absolute paths
        '-f', 'concat',
        '-i', camera_mux_filename,
        # output options:
        '-ss', str(ffmpeg_ss / 1000.),
        '-to', str(ffmpeg_to / 1000.),
        '-vf', 'scale=-1:480,pad=iw+640:ih:640',
        '-c:v', 'libx264',
        '-crf', '30',
        '-c:a', 'copy',
        '-preset', 'ultrafast',
        video_filename
    ])


def extract_qa(name, dry_run=False):
    qa_info = load_qa_info(name)
    parameters = get_parameters()
    
    cam1_input_files = [os.path.join(
        qa_info['cam1_input_folder'],
        "MVI_{:04d}.MP4".format(i)
    ) for i in range(qa_info['cam1_start_video'], qa_info['cam1_stop_video'] + 1)]
    cam2_input_files = [os.path.join(
        qa_info['cam2_input_folder'],
        "MVI_{:04d}.MP4".format(i)
    ) for i in range(qa_info['cam2_start_video'], qa_info['cam2_stop_video'] + 1)]
    
    ffmpeg_ss = qa_info['cam1_start_time_ms']
    ffmpeg_to = sum(media_length(f) for f in cam1_input_files[:-1]) + qa_info['cam1_stop_time_ms']
    
    cam1_list_filename = os.path.join(parameters['output_dir'], '{}_camera1.mux'.format(name))
    with open(cam1_list_filename, 'w') as list_file:
        list_file.write("\n".join("file '{}'".format(f) for f in cam1_input_files))
        
    cam2_list_filename = os.path.join(parameters['output_dir'], '{}_camera2.mux'.format(name))
    with open(cam2_list_filename, 'w') as list_file:
        list_file.write("\n".join("file '{}'".format(f) for f in cam2_input_files))

    video_filename = os.path.join(parameters['output_dir'], '{}.mp4'.format(name))
    
    ffmpeg_command = [
        'ffmpeg',
        # global options:
        '-y',  # overwrite
    ]
    
    if qa_info['sync_delay_ms'] > 0:
        # cam1 starts first
        ffmpeg_command.extend([
            # input stream 0:
            '-safe', '0',  # allow absolute paths
            '-f', 'concat',
            '-i', cam1_list_filename,
            # input stream 1:
            '-itsoffset', str(qa_info['sync_delay_ms'] / 1000.),
            '-safe', '0',  # allow absolute paths
            '-f', 'concat',
            '-i', cam2_list_filename,
            # processing:
            '-filter_complex',
            ';'.join([
                '[0:v]pad=iw*2:ih[padded]',  # pad cam1, put it on the left
                '[padded][1:v]overlay=W/2:0[sidebyside]',  # overlay cam2 on the right
                '[sidebyside]scale=-2:480[v]',
                '[0:a][1:a]amix[a]',
            ]),
        ])
    elif qa_info['sync_delay_ms'] < 0:
        # cam2 starts first
        ffmpeg_command.extend([
            # input stream 0:
            '-itsoffset', str(-qa_info['sync_delay_ms'] / 1000.),
            '-safe', '0',  # allow absolute paths
            '-f', 'concat',
            '-i', cam1_list_filename,
            # input stream 1:
            '-safe', '0',  # allow absolute paths
            '-f', 'concat',
            '-i', cam2_list_filename,
            # processing:
            '-filter_complex',
            ';'.join([
                '[1:v]pad=iw*2:ih:iw:0[padded]',  # pad cam2, put it on the right
                '[padded][0:v]overlay=0:0[sidebyside]',  # overlay cam1 on the left
                '[sidebyside]scale=-2:480[v]',
                '[0:a][1:a]amix[a]',
            ]),
        ])
    else:
        # cam1 and cam2 are already synchronised
        ffmpeg_command.extend([
            # input stream 0:
            '-safe', '0',  # allow absolute paths
            '-f', 'concat',
            '-i', cam1_list_filename,
            # input stream 1:
            '-safe', '0',  # allow absolute paths
            '-f', 'concat',
            '-i', cam2_list_filename,
            # processing:
            '-filter_complex',
            ';'.join([
                '[0:v]pad=iw*2:ih[padded]',  # pad cam1, put it on the left
                '[padded][1:v]overlay=W/2:0[sidebyside]',  # overlay cam2 on the right
                '[sidebyside]scale=-2:480[v]',
                '[0:a][1:a]amix[a]',
            ]),
        ])
    
    ffmpeg_command.extend([
        # output options:
        '-map', '[v]',
        '-map', '[a]',
        '-ac', '2',
        '-ss', str(ffmpeg_ss / 1000.),
        '-to', str(ffmpeg_to / 1000.),
        '-c:v', 'libx264',
        '-crf', '30',
        '-preset', 'ultrafast',
        '-async', '1',
        video_filename
    ])
    
    if dry_run:
        return subprocess.list2cmdline(ffmpeg_command)
    else:
        return subprocess.check_call(ffmpeg_command)

    
def load_talk_info(name):
    return load_all_talk_info()[name]


@functools.lru_cache(maxsize=1, typed=False)
def load_all_talk_info():
    sheet = ODSReader(info_file).getSheet('talks')
    keys = sheet[0]
    return {values[0]: dict(zip(keys, values)) for values in sheet[1:]}


def load_qa_info(name):
    return load_all_qa_info()[name]


@functools.lru_cache(maxsize=1, typed=False)
def load_all_qa_info():
    sheet = ODSReader(info_file).getSheet('qa')
    keys = sheet[0]
    return {values[0]: dict(zip(keys, values)) for values in sheet[1:]}


@functools.lru_cache(maxsize=1, typed=False)
def get_parameters():
    return {x[0]: x[1] for x in ODSReader(info_file).getSheet('parameters')}
