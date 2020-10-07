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

# Global variable path validation
if INPUT_PATH[-1] != '/':
    INPUT_PATH += '/'


def get_remote_dirs_list() -> list:
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
                           os.path.join(OUTPUT_PATH, 'photos')
                           ],
                          # universal_newlines=True,  # This throws utf-8 error for some dirs
                          stdout=subprocess.PIPE)

    # Convert bytes to string as no longer using universal_newlines
    lines = ''.join(map(chr, proc.stdout)).split('\n')

    # Filter all thumbnails, bin-content, non-directories, etc.
    photo_dirs_list = []
    for line in lines:
        if '@eaDir' in line or '#recycle' in line or 'bytes/sec' in line or './' in line or 'created directory' in line:
            continue
        if '/' not in line:
            continue
        photo_dirs_list.append(line.rstrip())

    return get_last_level_directories(photo_dirs_list)


def get_local_dirs_list(path) -> list:
    """
    Get local list of directories of given path
    :return: list with directory names
    """
    subdirs = [x[0] for x in os.walk(path)]
    subdirs = get_last_level_directories(subdirs)
    return subdirs


def get_last_level_directories(photo_dirs_list) -> list:
    """
    Only select the last level of subdirectories, and ignore any higher level directories
    :return: list with directory names
    """
    photo_dirs_list_final = []
    for line in photo_dirs_list:
        counter = 0
        for line2 in photo_dirs_list:
            if line in line2:
                counter += 1
        if counter == 1:
            photo_dirs_list_final.append(line.rstrip())
    return photo_dirs_list_final


def delete_old_screensaver_photos() -> None:
    """
    Delete old photo files if the screensaver directory exists (using subprocess)
    :return: None
    """
    # First, check it exists by checking the return code of below command
    proc = subprocess.run(["test", "-e", os.path.join(OUTPUT_PATH, 'photos')],
                          # stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT
                          )
    if proc.returncode == 0:
        subprocess.run(["rm", "-rf", os.path.join(OUTPUT_PATH, 'photos')],
                       # stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT
                       )
    pass


def strip_path(path) -> str:
    return os.path.basename(os.path.normpath(path))


def strip_path_list(dir_list) -> list:
    return [strip_path(x) for x in dir_list]


def get_random_entry(dirs_list) -> str:
    return np.random.choice(dirs_list)


def upload_new_screensaver_photos(photo_dirs_list: list) -> None:
    """
    Select a random directory from INPUT_PATH and copy this locally to be
    picked up by the screensaver program
    :param photo_dirs_list: a list of directory names inside remote servers's directory
                            the output from running get_remote_dirs_list
    :return: None
    """
    app_logger.info(f'Selecting a random choice from directory list')
    random_dir_choice = get_random_entry(photo_dirs_list)
    app_logger.info(f'Copying {random_dir_choice} locally to ' + os.path.join(OUTPUT_PATH, 'photos'))

    delete_old_screensaver_photos()

    # Now run rsync
    proc = subprocess.run(["rsync",
                           # verbose
                           "-v",
                           # recursive
                           "-r",
                           # protect arguments --protect-args equivalent
                           "-s",
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
                           os.path.join(INPUT_PATH, random_dir_choice),
                           # to:
                           os.path.join(OUTPUT_PATH, 'photos')],
                          stdout=subprocess.PIPE,  # required to return names of photos transferred
                          universal_newlines=True  # required to return string, not bytes-like obj
                          # stderr=subprocess.STDOUT
                          )

    # Change mode of newly created directory so photos can be deleted when job runs
    subprocess.run(["chmod", "777", os.path.join(OUTPUT_PATH, 'photos')])

    # Lower case output to handle cases when file extension is in caps
    proc_stdout_lower_case = proc.stdout.lower()

    # Repeat operation while no photos exist in the randomly selected directory
    if not ('.jpg' in proc_stdout_lower_case or '.jpeg' in proc_stdout_lower_case):
        upload_new_screensaver_photos(photo_dirs_list)
    pass


def main() -> None:
    app_logger.info('Getting photo directories list from paulito')
    remote_list = get_remote_dirs_list()
    app_logger.info('Starting upload_new_screensaver_photos')
    upload_new_screensaver_photos(remote_list)
    app_logger.info('Finished running screensaver.py!')

    ##
    #1 check if paulito can be reached. get dir_list. if all of dir_list in already_used, remove all from already_used list.
    #2 choose random directory
    #3 load already_used pickle, and check if it is in there. if yes, choose new one & repeat
    #4 check if dir exists localy
    #  if yes, copy locally from lib, then rsync server with lib after
    #  if not, rysync to screensaver.
    #        check size of lib. if above 15GBP, delete random directory and repeat until <15GB.
    #        then copy to lib (make new dir)
    #5 add dir to already used pickle and save
    #1---> if paulito cannot be reached, choose random folder from list. if all of local in already_used, remove all from already_used list.
    # check if folder in already_used_list. if yes, repeat, until not, then copy to screensaver

    local_list = get_local_dirs_list(os.path.join(OUTPUT_PATH, 'library'))
    a = strip_path_list(local_list)
    b = strip_path_list(remote_list)
    print(get_random_entry(local_list))
    print(strip_path(get_random_entry(local_list)))
    print(set(a).issubset(b))

    size = int(subprocess.check_output(['du', '-shm', os.path.join(OUTPUT_PATH, 'photos')]).split()[0].decode('utf-8'))
    print("Mbytes photos:", size)
    size = int(subprocess.check_output(['du', '-shm', os.path.join(OUTPUT_PATH, 'library')]).split()[0].decode('utf-8'))
    print("Mbytes photos:", size)
    ##
    pass


if __name__ == "__main__":
    main()
    pass
