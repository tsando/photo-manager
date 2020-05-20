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


def get_photo_dirs_list_from_paulito() -> list:
    """
    Get list of directories containing photos from a remote server, whilst filtering some stuff
    using rsync command
    :return: list with directory names
    """
    # Ref: https://stackoverflow.com/questions/14272582/calling-rsync-from-python-subprocess-call
    proc = subprocess.Popen(["rsync",
                             # verbose + dry-run
                             "-vn",
                             # archive
                             "-a",
                             # include directories"
                             "--include", "*/",
                             # exclude files:
                             "--exclude", "*",
                             # from:
                             INPUT_PATH,
                             # to:
                             OUTPUT_PATH
                             ],
                            stdout=subprocess.PIPE,
                            universal_newlines=True)

    photo_dirs_list = []

    while True:
        line = proc.stdout.readline()
        if not line:
            break
        # Filter all thumbnails files and anything else that doesn't start with year 2000 and is
        # not within a subdir
        if '@eaDir' in line or not line.startswith('20') or line.count('/') < 2:
            continue
        photo_dirs_list.append(line.rstrip())
    #     print(line.rstrip())
    return photo_dirs_list


def delete_old_photos() -> None:
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


def copy_photos_dir_from_paulito_to_local(photo_dirs_list: list) -> None:
    """
    Select a random directory from INPUT_PATH and copy this locally to be
    picked up by the screensaver program
    :param photo_dirs_list: a list of directory names inside paulito's photo directory
                            the output from running  get_photo_dirs_list_from_paulito
    :return: None
    """
    app_logger.info(f'Selecting a random choice from directory list')
    random_dir_choice = np.random.choice(photo_dirs_list)
    app_logger.info(f'Copying **{random_dir_choice}** locally to {OUTPUT_PATH}')

    delete_old_photos()

    # Now run rsync
    proc = subprocess.run(["rsync",
                           # verbose
                           "-v",
                           # recursive
                           "-r",
                           # include files:
                           "--include", "*.jpg",
                           "--include", "*.jpeg",
                           # exclude files:
                           "--exclude", "*",
                           # from:
                           f"{INPUT_PATH}'{random_dir_choice}'",
                           # to:
                           OUTPUT_PATH],
                          stdout=subprocess.PIPE,
                          universal_newlines=True  # required to return string, not bytes-like obj
                          # stderr=subprocess.STDOUT
                          )

    # Repeat operation while no photos exist in the randomly selected directory
    if not ('.jpg' in proc.stdout or '.jpeg' in proc.stdout):
        copy_photos_dir_from_paulito_to_local(photo_dirs_list)
    pass


def main() -> None:
    app_logger.info('Getting photo directories list from paulito')
    photo_dirs_list = get_photo_dirs_list_from_paulito()
    app_logger.info('Starting copy_photos_dir_from_paulito_to_local')
    copy_photos_dir_from_paulito_to_local(photo_dirs_list)
    app_logger.info('Finished running screensaver.py!')
    pass


if __name__ == "__main__":
    main()
    pass
