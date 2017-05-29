#! /usr/bin/env python

# script to erase .pyc files from current working directory and all its kids.

import os


def _try_delete_file(fpath):

    try:
        os.remove(fpath)
    except:
        print 'could not delete: ' + str(fpath)


def _delete_all_pyc_files():

    for root, dirs, files in os.walk('.'):

        if ('.git' in root) or ('.idea' in root):
            continue

        print '-------------------------------------------'
        print 'root: ' + str(root)
        print 'files: ' + str(files)
        print 'dirs: ' + str(dirs)
        for f in files:
            fpath = os.path.join(root, f)
            if '.pyc' == fpath[len(fpath)-4:len(fpath)]:
                print 'Trying to delete: ' + str(fpath)
                _try_delete_file(fpath=fpath)



if '__main__' == __name__:

    _delete_all_pyc_files()


