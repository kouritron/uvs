

import json
import os

import hash_util
import rand_util
import log
import cryptmanager as cm
import systemdefaults as sdef
import _version
import error
import dal_psql

class UVSManager(object):

    def __init__(self):
        super(UVSManager, self).__init__()

        log.fefrv("++++++++++++++++++++++++++++++++ UVSManager init called")





    def checkout_snapshot(self, snapid, dest_dir_path, clear_dest=False):
        """ Given a valid snapshot id, and a directory path with write access,
         checkout the state of the repo at that snapshot and write it in the specified directory. 

         By default it will just overwrite the files that collide with this checkout. if clear_dest is set
         to True it will delete everything at destination except uvs internal subdirs, which are probably
         and by default called ".uvs_shadow", ".uvs_cache" 
        """

        assert isinstance(clear_dest, bool)
        assert snapid != None
        assert dest_dir_path != None
        assert isinstance(snapid, str) or isinstance(snapid, bytes)

        # on windows path names are usually unicode, this might cause problems, be careful.
        assert isinstance(snapid, str) or isinstance(snapid, unicode)

        if not os.path.isdir(dest_dir_path):
            raise error.UVSErrorInvalidDestinationDirectory

            # TODO confirm snap id exists in snapshots table
            # checkout, get the snapshot, find the root tree id. (raise error if decryption fails, or mac failed.)
            # checkout tree recursive function:
            #    assemble the files of this tree, write to disk. (raise error if any objects did decrypt or pass mac)
            #    call itself recursively on subdirs.


if '__main__' == __name__:
    log.vvvv(">> creating DAL")
    dal = dal_psql.DAL()

    dest_dir = "../sample_repo"
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    #checkout_snapshot(snapid="446839f7b3372392e73c9e869b16a93f13161152f02ab2565de6a985", dest_dir_path=dest_dir)

