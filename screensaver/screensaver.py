#!/usr/bin/env python3

import subprocess
import os
import pickle
import logging
import numpy as np

# Create application logger
logging.basicConfig(level=logging.INFO)
app_logger = logging.getLogger('screensaver.py')

# Set global variables from env variables
INPUT_PATH = os.getenv('SCREENSAVER_INPUT_PATH')
OUTPUT_PATH = os.getenv('SCREENSAVER_OUTPUT_PATH')
RSYNC_PORT = os.getenv('SCREENSAVER_RSYNC_PORT')

# SD card size in GByte. 3/4 of that will be used for library space
SD_card_space = 32

# Global variable path validation
INPUT_PATH = os.path.join(INPUT_PATH, '')


def get_remote_dirs_list(source, destination) -> list:
    """
    Get list of directories containing photos from a remote location, whilst filtering some stuff
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
                           source,
                           # to:
                           destination
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
            final_dir = os.path.join(line.rstrip(), '')
            photo_dirs_list_final.append(final_dir)
    return photo_dirs_list_final


def delete_directory(path) -> None:
    """
    Deletes a directory if given path exists
    :return: None
    """
    # First, check it exists by checking the return code of below command
    proc = subprocess.run(["test", "-e", path],
                          # stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT
                          )
    if proc.returncode == 0:
        subprocess.run(["rm", "-rf", path],
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


def rsync_directory(source, destination) -> None:

    # run rsync
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
                           source,
                           # to:
                           destination
                           ],
                          stdout=subprocess.PIPE,  # required to return names of photos transferred
                          universal_newlines=True  # required to return string, not bytes-like obj
                          # stderr=subprocess.STDOUT
                          )

    # Lower case output to handle cases when file extension is in caps
    #proc_stdout_lower_case = proc.stdout.lower()

    # Repeat operation while no photos exist in the randomly selected directory
    #if not ('.jpg' in proc_stdout_lower_case or '.jpeg' in proc_stdout_lower_case):
    #    upload_new_screensaver_photos(photo_dirs_list)
    pass


def copy_directory_locally(source, destination):
    subprocess.check_output(['cp', '-r', source, destination])
    pass


def make_directory(path):
    subprocess.check_output(['mkdir', '-p', path])
    pass


def get_size_of_dir(dir):
    return int(subprocess.check_output(['du', '-shm', dir]).split()[0].decode('utf-8'))


def main() -> None:

    #TODO:
    # check if server can be reached.
    # what if folder empty?
    # remove strip_path_list function, not needed

    photos_path = os.path.join(OUTPUT_PATH, 'photos', '')
    library_path = os.path.join(OUTPUT_PATH, 'library', '')

    # Delete existing photos
    delete_directory(photos_path)
    # Make new photos folder
    make_directory(photos_path)
    subprocess.run(["chmod", "777", photos_path])

    if not os.path.exists(library_path):
        make_directory(library_path)
        subprocess.run(["chmod", "777", library_path])

    # Load list of directories that have already been shown
    # If this is the first time the script runs it will not find such a file. We then start with an empty one
    app_logger.info('Load already shown directories')
    try:
        already_used = pickle.load(open("already_used.p", "rb"))
    except:
        already_used = []
    # Manual over-write to reset list
    # already_used = []

    # Get list of remote directories.
    app_logger.info('Getting photo directories list from remote location')
    remote_list = get_remote_dirs_list(INPUT_PATH, photos_path)

    # Check if all remote directories have already been shown. If yes the list is reset
    if set(remote_list).issubset(already_used):
        already_used = []

    # Choose a random directory that has not been shown yet
    random_dir = get_random_entry(remote_list)
    while random_dir in already_used:
        random_dir = get_random_entry(remote_list)
    remote_path = os.path.join(INPUT_PATH, random_dir, '')
    app_logger.info(f'Chosen directory is: {random_dir}')

    # Add chosen directory to already shown list to exclude it from future selections
    already_used.append(random_dir)
    pickle.dump(already_used, open("already_used.p", "wb"))

    # Check if directory already exists locally
    local_list = get_local_dirs_list(library_path)
    local_equivalent = os.path.join(library_path, random_dir, '')

    print("----------")
    #print(already_used)
    #print(local_list)
    print(local_list)

    local_equivalent = '/Users/paulschaack/Downloads/coding/photo-manager/screensaver/library/2020/02 Norway/'
    print(local_equivalent)

    # If directory already exists locally then copy locally from library to photos
    # Afterwards rsync with remote location in case of changes
    if local_equivalent in local_list:
        app_logger.info(f'{local_equivalent} exists locally')
        copy_directory_locally(local_equivalent, photos_path)
        #rsync_directory(remote_path, photos_path) # check if redownloads? then delete
        #rsync_directory(remote_path, local_equivalent) # check if redownloads? then delete

        # Change mode of newly created directory so photos can be deleted when job runs
        #subprocess.run(["chmod", "777", photos_path])
        #subprocess.run(["chmod", "777", local_equivalent])
    # If not then rsync to photos and library
    else:
        app_logger.info(f'{local_equivalent} does not exists locally and is getting copied from remote')
        rsync_directory(remote_path, photos_path)
        # check size of library. If above limit, delete random directory and repeat until <limit
        while get_size_of_dir(library_path) > int(SD_card_space*1024*0.75):
            delete_directory(get_random_entry(local_list))

        make_directory(local_equivalent)
        copy_directory_locally(photos_path, local_equivalent)


    # 1---> if paulito cannot be reached, choose random folder from list. if all of local in already_used, remove all from already_used list.
    # check if folder in already_used_list. if yes, repeat, until not, then copy to screensaver

    #a = strip_path_list(local_list)
    #b = strip_path_list(remote_list)
    #print(get_random_entry(local_list))
    #print(strip_path(get_random_entry(local_list)))
    #size = int(subprocess.check_output(['du', '-shm', photos_path]).split()[0].decode('utf-8'))
    #print("Mbytes photos:", size)
    #size = int(subprocess.check_output(['du', '-shm', os.path.join(OUTPUT_PATH, 'library')]).split()[0].decode('utf-8'))
    #print("Mbytes photos:", size)

    pass


if __name__ == "__main__":
    main()
    pass
