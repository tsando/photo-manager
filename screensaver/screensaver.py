#!/usr/bin/env python3

import subprocess
import os
import logging
import numpy as np

# Create application logger
logging.basicConfig(level=logging.INFO)
app_logger = logging.getLogger('screensaver.py')

# Set global variables from env variables
INPUT_PATH = os.getenv('SCREENSAVER_INPUT_PATH')
OUTPUT_PATH = os.getenv('SCREENSAVER_OUTPUT_PATH')
RSYNC_PORT = os.getenv('SCREENSAVER_RSYNC_PORT')


def get_photo_dirs_list() -> list:
    """
    Get list of directories containing photos from a remote server, whilst filtering some stuff
    using rsync command
    :return: list with directory names
    """
    # Ref: https://stackoverflow.com/questions/14272582/calling-rsync-from-python-subprocess-call
    proc = subprocess.run(["rsync",
                           # verbose + dry-run
                           "-vn",
                           # archive
                           "-a",
                           # use special port
                           "--rsh", "ssh -p" + RSYNC_PORT,
                           # include directories"
                           "--include", "*/",
                           # exclude files:
                           "--exclude", "*",
                           # from:
                           INPUT_PATH,
                           # to:
                           OUTPUT_PATH
                           ],
                          # universal_newlines=True,  # This throws utf-8 error for some dirs
                          stdout=subprocess.PIPE)

    photo_dirs_list = []

    # Convert bytes to string as no longer using universal_newlines
    lines = ''.join(map(chr, proc.stdout)).split('\n')

    for line in lines:
        # Filter all thumbnails files and anything else that doesn't start with year 2000 and is
        # not within a subdir
        if '@eaDir' in line or not line.startswith('20') or line.count('/') < 2:
            continue
        photo_dirs_list.append(line.rstrip())
    return photo_dirs_list


def delete_old_screensaver_photos() -> None:
    """
    Delete old photo files if the screensaver directory exists (using subprocess)
    :return: None
    """
    # First, check it exists by checking the return code of below command
    proc = subprocess.run(["test", "-e", OUTPUT_PATH],
                          # stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT
                          )
    if proc.returncode == 0:
        subprocess.run(["rm", "-rf", OUTPUT_PATH],
                       # stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT
                       )
    pass


def upload_new_screensaver_photos(photo_dirs_list: list) -> None:
    """
    Select a random directory from INPUT_PATH and copy this locally to be
    picked up by the screensaver program
    :param photo_dirs_list: a list of directory names inside paulito's photo directory
                            the output from running  get_photo_dirs_list
    :return: None
    """
    app_logger.info(f'Selecting a random choice from directory list')
    random_dir_choice = np.random.choice(photo_dirs_list)
    app_logger.info(f'Copying **{random_dir_choice}** locally to {OUTPUT_PATH}')

    delete_old_screensaver_photos()

    # Now run rsync
    proc = subprocess.run(["rsync",
                           # verbose
                           "-v",
                           # recursive
                           "-r",
                           # use special port
                           "--rsh", "ssh -p" + RSYNC_PORT,
                           # include files:
                           "--include", "*.jpg",
                           "--include", "*.JPG",
                           "--include", "*.jpeg",
                           "--include", "*.JPEG",
                           # exclude files:
                           "--exclude", "*",
                           # from:
                           f"{INPUT_PATH}'{random_dir_choice}'",
                           # to:
                           OUTPUT_PATH],
                          stdout=subprocess.PIPE,  # required to return names of photos transferred
                          universal_newlines=True  # required to return string, not bytes-like obj
                          # stderr=subprocess.STDOUT
                          )

    # Change mode of newly created directory so photos can be deleted when job runs
    subprocess.run(["chmod", "777", OUTPUT_PATH])

    # Lower case output to handle cases when file extension is in caps
    proc_stdout_lower_case = proc.stdout.lower()

    # Repeat operation while no photos exist in the randomly selected directory
    if not ('.jpg' in proc_stdout_lower_case or '.jpeg' in proc_stdout_lower_case):
        upload_new_screensaver_photos(photo_dirs_list)
    pass


def main() -> None:
    app_logger.info('Getting photo directories list from paulito')
    photo_dirs_list = get_photo_dirs_list()
    app_logger.info('Starting upload_new_screensaver_photos')
    upload_new_screensaver_photos(photo_dirs_list)
    app_logger.info('Finished running screensaver.py!')
    pass


if __name__ == "__main__":
    main()
    pass
