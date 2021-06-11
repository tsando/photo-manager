#! /usr/bin/env python3

import os
import datetime


def validate_user_inputs():
    """
        Checks user has provided a valid directory path
    :return:
        _dir: the validated directory which the user provided
        name_tag: the name tag provided by the user to rename the files
    """
    _dir = None
    while True:
        try:
            _dir = str(input("Enter the full path to the photo directory:\n"))
            if '/' not in _dir or ' ' in _dir:
                raise ValueError
            break
        except ValueError:
            print("-> ERROR: That is not a valid directory. Example valid input: \
            '/Users/username/Pictures/mydirectory'")
        except FileNotFoundError:
            print("-> ERROR: That directory doesn't exist")

    name_tag = str(input('Enter a name tag for all the photos and video files:\n'))
    name_tag = name_tag.replace(' ', '_')
    print('-> INFO: Modified name tag to:\t{}'.format(name_tag))
    return _dir, name_tag


def rename_photos(_dir, name_tag):
    #  consider only image and movie files
    extensions = ['jpg', 'jpeg', 'mov']
    time_tag_list = []
    counter = 2  # for the rare case when 2 or more photos have the same timestamp (see below)
    for fn in os.listdir(_dir):
        # Check if files has the above extensions, else ignore
        if any(fn.lower().endswith(ext) for ext in extensions):
            ext = fn.lower().split('.')[-1]
            oldpath = os.path.join(_dir, fn)
            ctime = os.stat(oldpath).st_birthtime  # creation date time stamp
            time_tag = datetime.datetime.fromtimestamp(ctime).strftime('%Y%m%d-%H%M%S')

            # Check the rare case when we have duplicate time tag and if so, append counter to name
            if time_tag in time_tag_list:
                name_tag_new = name_tag + '_' + str(counter)
                counter += 1
            else:
                name_tag_new = name_tag
                time_tag_list += [time_tag]
                #  reset
                counter = 2
            newpath = os.path.join(_dir, '{}-{}.{}'.format(time_tag, name_tag_new, ext))
            print('---------\nOLD:\t{}\nNEW:\t{}'.format(oldpath, newpath))
            os.rename(oldpath, newpath)
    print("""\
                                           ._ o o
                                           \_`-)|_
                                        ,""       \ 
                                      ,"  ## |   o o. 
                                    ," ##   ,-\__    `.
                                  ,"       /     `--._;)
                                ,"     ## /
                              ,"   ##    /
                        """)
    print('-> INFO: FINISHED!')
    pass


if __name__ == "__main__":
    _dir, name_tag = validate_user_inputs()
    rename_photos(_dir, name_tag)

    pass

# ---------------------------
# NOTES
# ---------------------------

# though note below doesn't get all the mac related attributes
# info = os.stat(oldpath)
# instead using xattr module (installed via pip) - this doesn't get the created and modified times,
# it's for other attributes, see https://stackoverflow.com/questions/33181948/how-to-get-extended-macos-attributes-of-a-file-using-python
# info = xattr.xattr(_path + '/' + fn)

# Get created time
# WARNING: https://docs.python.org/2/library/stat.html#stat.ST_CTIME
# On some systems (like Unix) is the time of the last metadata change, and, on others (like Windows), is the creation time
# In this mac it seems to be also the first case
# ctime = os.path.getctime(oldpath)
# time_tag = datetime.datetime.fromtimestamp(ctime).strftime('%Y%m%d-%H%M%S')
