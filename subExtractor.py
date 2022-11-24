import multiprocessing

import glob
import time
import logging
import datetime
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler


def extractSubtitles(file_path):
    file_path_without_ext = file_path.rsplit('.', 1)[0]
    escaped_glob = glob.escape(file_path_without_ext) + '.ex*.srt'
    found_subs = glob.glob(escaped_glob)
    if not found_subs:
        logging.warning('NO found subs for: {}'.format(file_path))
        file_name = file_path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        file_folder = file_path.rsplit('/', 1)[0]

        result = subprocess.run(['ffprobe', '-loglevel', 'error', '-select_streams', 's', '-show_entries',
                                'stream=index:stream_tags=language', '-of', 'csv=p=0', file_path], stdout=subprocess.PIPE)
        for index, subtitle in enumerate(result.stdout.decode('utf-8').splitlines()):
            sub_language = subtitle.split(',')[-1]
            if (sub_language == 'eng'):
                subprocess.run(['ffmpeg', '-i', file_path, '-map', '0:s:{}'.format(index), '{}/{}.ex-{}.{}.srt'.format(
                    file_folder, file_name, index, sub_language)], stdout=subprocess.PIPE)
    else:
        logging.warning("Found subs for: {}".format(file_path))


class Event(LoggingEventHandler):
    def dispatch(self, event):
        logging.warning(event)
        file_type = event.src_path.split('.')[-1]
        if (file_type == 'mkv'):
            if (event.event_type == 'created' and not queue.get(event.src_path)):
                queue[event.src_path] = datetime.datetime.now()
            if (event.event_type == 'modified' and queue.get(event.src_path)):
                queue[event.src_path] = datetime.datetime.now()


queue = {}
watch_path = './watchFolder'

if __name__ == "__main__":
    logging.warning("App stared:")
    for subdir, dirs, files in os.walk(watch_path):
        for file in files:
            file_type = file.rsplit('.', 1)[-1]
            if (file_type == 'mkv'):
                file_path = os.path.join(subdir, file)
                extractSubtitles(file_path)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = Event()
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
            for key in queue.copy():
                if (datetime.datetime.now() - queue[key]).total_seconds() > 15:
                    queue.pop(key)
                    logging.warning(
                        "File has finished copying: {}".format(key))
                    p = multiprocessing.Process(
                        target=extractSubtitles, args=(key,))
                    p.start()
                    p.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
