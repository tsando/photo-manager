#!/usr/bin/env python3

import subprocess
import os
import glob
import json
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
disc_space_max_limit_gb = 20

# Define regular expression for files to be transferred
regex_files = '*.[Jj][Pp]*[Gg]'

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
                          stdout=subprocess.PIPE
                          )

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
    photo_dirs_list = [os.path.join(x[0], '') for x in os.walk(path)]
    return get_last_level_directories(photo_dirs_list)


def trim_path_prefix(path_list, prefix) -> list:
    return [x.split(prefix)[1] for x in path_list]


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


def rsync_directory(source, destination) -> None:

    # run rsync
    proc = subprocess.run(["rsync",
                           # verbose
                           "-v",
                           # recursive
                           "-r",
                           # protect arguments --protect-args equivalent
                           "-s",
                           # skip based on checksum, not mod-time & size
                           "-c",
                           # delete extraneous files from dest dirs
                           "--delete",
                           # use special port
                           "--rsh", "ssh -p" + RSYNC_PORT,
                           # include files:
                           "--include", regex_files,
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
    pass


def copy_directory_locally(source, destination):
    source = os.path.join(source, '', '.')
    subprocess.run(['cp', '-r', source, destination], stdout=subprocess.PIPE)
    pass


def make_directory(path):
    subprocess.run(['mkdir', '-p', path], stdout=subprocess.PIPE)
    pass


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


def get_size_of_dir(path):
    proc = subprocess.run(['du', '-shm', path], stdout=subprocess.PIPE)
    proc_output = proc.stdout
    size = int(proc_output.split()[0].decode('utf-8'))
    return size


def is_remote_available():
    proc = subprocess.run(["rsync",
                           # verbose + dry-run
                           "-vn",
                           # use special port
                           "--rsh", "ssh -p" + RSYNC_PORT,
                           # include directories"
                           "--include", "*/",
                           # exclude files:
                           "--exclude", "*",
                           # from:
                           INPUT_PATH,
                           # to:
                           "."
                           ],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE
                          )
    output_err = str(proc.stderr)
    # print(output_err)
    if "Could not resolve hostname" in output_err:
        return False
    elif "Permission denied" in output_err:
        return False
    elif "Connection closed by" in output_err:
        return False
    elif "connection unexpectedly closed" in output_err:
        return False
    else:
        return True


def get_random_entry(dirs_list) -> str:
    return np.random.choice(dirs_list)


def setup_paths(photos_path, library_path):
    # Delete existing photos
    delete_directory(photos_path)
    # Make new photos folder
    make_directory(photos_path)
    subprocess.run(["chmod", "777", photos_path])

    if not os.path.exists(library_path):
        make_directory(library_path)
        subprocess.run(["chmod", "777", library_path])
    pass


def get_already_used_list():
    # Load list of directories that have already been shown
    # If this is the first time the script runs it will start with an empty one
    app_logger.info('Load already shown directories')
    try:
        json_dic = json.load(open(os.path.join(OUTPUT_PATH, 'already_used.json'), 'r'))
        already_used = json_dic['already_used']
    except:
        already_used = []
    return already_used


def select_from_local(photos_path, library_path, already_used) -> None:
    # Get local entries in library
    local_list = get_local_dirs_list(library_path)
    local_list = trim_path_prefix(local_list, library_path)

    # Check if all directories have already been shown. If yes the list is trimmed down accordingly
    if set(local_list).issubset(already_used):
        already_used = [x for x in already_used if x not in local_list]

    # Choose a random directory that has not been shown yet
    random_dir = get_random_entry(local_list)
    while random_dir in already_used:
        random_dir = get_random_entry(local_list)
    # Add chosen directory to already shown list to exclude it from future selections
    already_used.append(random_dir)
    app_logger.info(f'Chosen directory is: {random_dir}')

    # Dump data to json
    json_dic = {'already_used': already_used,
                'remote_list': 'not available',
                'local_list': local_list,
                'random_dir': random_dir}
    with open(os.path.join(OUTPUT_PATH, 'already_used.json'), 'w') as fp:
        json.dump(json_dic, fp, sort_keys=True, indent=4)

    # Build local path and copy to photos
    local_equivalent = os.path.join(library_path, random_dir, '')
    app_logger.info('Copy from library to photos directory')
    copy_directory_locally(local_equivalent, photos_path)

    # Check if there are any jpgs in the photos directory. If not, start over
    # test with for example library/201X/12\ Mexico/GoPro, which does not have any jpgs..
    files_jpg = glob.glob(os.path.join(photos_path, regex_files))
    if len(files_jpg) > 0:
        app_logger.info('There are photos in the photos directory')
    else:
        app_logger.info('There are no photos in the photos directory, start over again')
        select_from_local(photos_path, library_path, already_used)
    pass


def rsync_with_remote(photos_path, library_path, already_used) -> None:
    # Get list of remote directories.
    app_logger.info('Getting photo directories list from remote location')
    remote_list = get_remote_dirs_list(INPUT_PATH, photos_path)
    # Check if all remote directories have already been shown. If yes the list is trimmed down accordingly
    if set(remote_list).issubset(already_used):
        already_used = [x for x in already_used if x not in remote_list]

    # Choose a random directory that has not been shown yet
    random_dir = get_random_entry(remote_list)
    while random_dir in already_used:
        random_dir = get_random_entry(remote_list)
    remote_path = os.path.join(INPUT_PATH, random_dir, '')
    # Add chosen directory to already shown list to exclude it from future selections
    already_used.append(random_dir)
    app_logger.info(f'Chosen directory is: {random_dir}')

    # Get local entries in library
    local_list = get_local_dirs_list(library_path)
    local_equivalent = os.path.join(library_path, random_dir, '')

    # Dump data to json
    json_dic = {'already_used': already_used,
                'remote_list': remote_list,
                'local_list': local_list,
                'random_dir': random_dir}
    with open(os.path.join(OUTPUT_PATH, 'already_used.json'), 'w') as fp:
        json.dump(json_dic, fp, sort_keys=True, indent=4)

    # If directory already exists locally then copy locally from library to photos
    # Afterwards rsync with remote location in case of changes
    if local_equivalent in local_list:
        app_logger.info(f'{local_equivalent} exists locally')

        app_logger.info('Copy from library to photos directory')
        copy_directory_locally(local_equivalent, photos_path)

        app_logger.info('Rsync remote with photos in case of any changes')
        rsync_directory(remote_path, photos_path)

        app_logger.info('Rsync remote with library in case of any changes')
        rsync_directory(remote_path, local_equivalent)

    # If not then rsync to photos and copy to library
    else:
        app_logger.info(f'{local_equivalent} does not exists locally and is getting copied from remote')
        rsync_directory(remote_path, photos_path)

        # check size of library. If above limit, delete random directory and repeat until <limit
        while get_size_of_dir(library_path) > int(disc_space_max_limit_gb*1024):
            app_logger.info('Library is too big, two random directories are getting deleted')
            delete_directory(get_random_entry(local_list))
            delete_directory(get_random_entry(local_list))

        app_logger.info('Copy photos to local library for future uses')
        make_directory(local_equivalent)
        copy_directory_locally(photos_path, local_equivalent)

    # Check if there are any jpgs in the photos directory. If not, start over
    files_jpg = glob.glob(os.path.join(photos_path, regex_files))
    if len(files_jpg) > 0:
        app_logger.info('There are photos in the photos directory')
    else:
        app_logger.info('There are no photos in the photos directory, start over again')
        rsync_with_remote(photos_path, library_path, already_used)

    pass


def main() -> None:
    # Path definitions
    photos_path = os.path.join(OUTPUT_PATH, 'photos', '')
    library_path = os.path.join(OUTPUT_PATH, 'library', '')
    # Setup of all paths if not existent
    setup_paths(photos_path, library_path)
    # Load already shown albums
    already_used = get_already_used_list()
    # Check if remote server is available
    remote_available = is_remote_available()

    # If the server is available continue with accessing the server
    if remote_available:
        app_logger.info('Remote server available')
        rsync_with_remote(photos_path, library_path, already_used)
    # If not then use photos from the local library only:
    else:
        app_logger.info('Remote server not available, selecting a random path from library')
        select_from_local(photos_path, library_path, already_used)
    pass


if __name__ == "__main__":
    main()
    pass
