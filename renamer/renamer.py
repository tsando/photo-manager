#! /usr/bin/env python3

import os
import datetime
import argparse
import sys


def validate_user_inputs():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('path', metavar='path', type=str,
                        help='path to photo directory')
    parser.add_argument('name', metavar='name', type=str,
                        help='common name to add to photo files')
    args = parser.parse_args()
    args_values = vars(args)

    name_tag = args_values['name']
    cwd = os.getcwd()
    _dir = os.path.join(cwd, args_values['path'])

    try:
        fList = os.listdir(_dir)
    except OSError:
        sys.exit("-> ERROR: That directory doesn't exist")

    return _dir, name_tag


def rename_photos(_dir, name_tag):
    #  consider only image and movie files
    extensions = ['jpg', 'jpeg', 'mov', 'mp4']
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
