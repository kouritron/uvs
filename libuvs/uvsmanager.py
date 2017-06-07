

import json
import os
import shutil

import hash_util
import rand_util
import log
import cryptmanager as cm
import systemdefaults as sdef
import _version
import uvs_errors
import dal_psql
import dal_sqlite
from  uvs_errors import *


class UVSManager(object):

    def __init__(self):
        super(UVSManager, self).__init__()

        log.fefrv("++++++++++++++++++++++++++++++++ UVSManager init called")

        #self._dao = dal_psql.DAO()
        self._dao = dal_sqlite.DAO()




    def setup_for_new_repo(self, user_pass):
        """ setup this uvs manager for working with a new empty uvs repository with the supplied password. """

        assert user_pass != None

        log.fefrv("setup_for_new_repo() called")

        public_document = {}

        public_document['salt'] = cm.get_new_random_salt()
        public_document['uvs_version'] = _version.get_version()
        public_document['fingerprinting_algo'] = cm.get_uvs_fingerprinting_algo_desc()

        log.vvv(repr(public_document))

        public_doc_serialized = json.dumps(public_document, ensure_ascii=False, sort_keys=True)

        self._dao.set_repo_public_doc(public_doc=public_doc_serialized)

        self._crypt_helper = cm.UVSCryptHelper(usr_pass=user_pass, salt=public_document['salt'])


    def setup_for_existing_repo(self, user_pass):
        """ setup this uvs manager for working with existing uvs repository with the supplied password. """

        assert user_pass != None

        log.fefrv("setup_for_existing_repo() called")

        public_document =  self._dao.get_repo_public_doc()

        if None == public_document:
            raise uvs_errors.UVSErrorInvalidRepository("No public document found in this repository. ")

        public_doc_dict = json.loads(public_document)

        if not public_doc_dict.has_key('salt'):
            raise uvs_errors.UVSErrorInvalidRepository('invalid repo, public document does not have a salt in it.')

        log.v("dao returned this public document: " + str(public_document))

        self._crypt_helper = cm.UVSCryptHelper(usr_pass=user_pass, salt= str(public_doc_dict['salt']))



    def make_sample_snapshot_1(self):
        """ Create a test snapshot (commit in other vcs) """

        assert None != self._dao
        assert None != self._crypt_helper

        crypt_help = self._crypt_helper

        # -------------------------------------------------------- some sample segments and files
        #  we have files hello.py morning.py afternoon.py

        f1_bytes = b'''\n\n\n print "hello" \n\n\n'''
        f1_fp =  crypt_help.get_uvsfp(f1_bytes)

        f2_bytes =  b'''\n\n\n print "good morning" \n\n\n'''
        f2_fp =  crypt_help.get_uvsfp(f2_bytes)

        f3_bytes =  b'''\n\n\n print "good afternoon" \n\n\n'''
        f3_fp =  crypt_help.get_uvsfp(f3_bytes)

        # break file1 into segments
        f1_s1 = f1_bytes[:7]
        f1_s2 = f1_bytes[7:]

        f2_s1 = f2_bytes[:7]
        f2_s2 = f2_bytes[7:]

        f3_s1 = f3_bytes[:7]
        f3_s2 = f3_bytes[7:]

        f1_s1_fp = crypt_help.get_uvsfp(f1_s1)
        f1_s2_fp = crypt_help.get_uvsfp(f1_s2)
        f2_s1_fp = crypt_help.get_uvsfp(f2_s1)
        f2_s2_fp = crypt_help.get_uvsfp(f2_s2)
        f3_s1_fp = crypt_help.get_uvsfp(f3_s1)
        f3_s2_fp = crypt_help.get_uvsfp(f3_s2)

        f1_s1_ct = crypt_help.encrypt_bytes(message=f1_s1)
        f1_s2_ct = crypt_help.encrypt_bytes(message=f1_s2)
        f2_s1_ct = crypt_help.encrypt_bytes(message=f2_s1)
        f2_s2_ct = crypt_help.encrypt_bytes(message=f2_s2)
        f3_s1_ct = crypt_help.encrypt_bytes(message=f3_s1)
        f3_s2_ct = crypt_help.encrypt_bytes(message=f3_s2)

        self._dao.add_segment(sgid=f1_s1_fp, segment_bytes=f1_s1_ct)
        self._dao.add_segment(sgid=f1_s2_fp, segment_bytes=f1_s2_ct)
        self._dao.add_segment(sgid=f2_s1_fp, segment_bytes=f2_s1_ct)
        self._dao.add_segment(sgid=f2_s2_fp, segment_bytes=f2_s2_ct)
        self._dao.add_segment(sgid=f3_s1_fp, segment_bytes=f3_s1_ct)
        self._dao.add_segment(sgid=f3_s2_fp, segment_bytes=f3_s2_ct)



        # -------------------------------------------------------------------------- lets add some files.

        file1_info = {}

        # verify fid is there to make sure records don't get reordered by an attacker.
        # fid is the uvs fingerprint of the content of the file.
        file1_info['verify_fid'] = f1_fp

        # 'segments' is a list of 2-tuples, (sgid, offset)
        # i.e. (sg001, 0)  means segment sg001 contains len(sg001) many bytes of this file starting from offset 0
        # i.e. (sg002, 2100) means segment sg002 contains len(sg002) many bytes of this file starting from offset 2100
        file1_info['segments'] = []
        file1_info['segments'].append((f1_s1_fp, 0))
        file1_info['segments'].append((f1_s2_fp, len(f1_s1)))

        file2_info = {}
        file2_info['verify_fid'] = f2_fp

        # 'segments' is a list of 3-tuples, (sgid, offset)
        file2_info['segments'] = []
        file2_info['segments'].append((f2_s1_fp, 0))
        file2_info['segments'].append((f2_s2_fp, len(f2_s1)))

        file3_info = {}
        file3_info['verify_fid'] = f3_fp

        # 'segments' is a list of 3-tuples, (sgid, offset)
        file3_info['segments'] = []
        file3_info['segments'].append((f3_s1_fp, 0))
        file3_info['segments'].append((f3_s2_fp, len(f3_s1)))

        file1_info_serial = json.dumps(file1_info, ensure_ascii=False, sort_keys=True)
        file2_info_serial = json.dumps(file2_info, ensure_ascii=False, sort_keys=True)
        file3_info_serial = json.dumps(file3_info, ensure_ascii=False, sort_keys=True)

        file1_info_ct = crypt_help.encrypt_bytes(message=file1_info_serial)
        file2_info_ct = crypt_help.encrypt_bytes(message=file2_info_serial)
        file3_info_ct = crypt_help.encrypt_bytes(message=file3_info_serial)

        self._dao.add_file(fid=f1_fp, finfo=file1_info_ct)
        self._dao.add_file(fid=f2_fp, finfo=file2_info_ct)
        self._dao.add_file(fid=f3_fp, finfo=file3_info_ct)

        # -------------------------------------------------------------------------- lets add some sample trees

        tree1_info = {}
        tree1_info['tids'] = []             # add subtrees if this directory has sub directories
        tree1_info['fids'] = []             # add files if this directory has files in it.

        # fids is a list of 2-tuples (name, fid) the list has to be sorted
        tree1_info['fids'].append(("hello.py", f1_fp))
        tree1_info['fids'].append(("morning.py", f2_fp))
        tree1_info['fids'].append(("afternoon.py", f3_fp))

        # it doesnt matter much what order things get sorted in, as long as it is deterministic.

        # this says sort by elem[0] first and in case of ties sort by elem[1], i think just sort woulda done the same.
        tree1_info['fids'].sort(key=lambda elem: (elem[0], elem[1]))
        # tree1_info['fids'].sort()

        tree1_json_serial = json.dumps(tree1_info, ensure_ascii=False, sort_keys=True)

        # get the fingerprint and ciphertext
        tree1_fp = crypt_help.get_uvsfp(tree1_json_serial)
        tree1_ct = crypt_help.encrypt_bytes(tree1_json_serial)

        log.vvvv('tree1 fp: ' + tree1_fp + "\ntree1 json: " + tree1_json_serial)

        self._dao.add_tree(tid=tree1_fp, tree_info=tree1_ct)

        # -------------------------------------------------------------------------- sample snapshots (commits)

        snapshot1_id = rand_util.get_new_random_snapshot_id()

        snapshot1_info = {}
        snapshot1_info['verify_snapid'] = snapshot1_id
        snapshot1_info['root'] = tree1_fp
        snapshot1_info['msg'] = 'First commit into uvs'
        snapshot1_info['author_name'] = 'kourosh'
        snapshot1_info['author_email'] = 'kourosh.sc@gmail.com'
        snapshot1_info['snapshot_signature'] = "put gpg signature here to prove the author's identity."

        snapshot1_json_serial = json.dumps(snapshot1_info, ensure_ascii=False, sort_keys=True)
        snapshot1_ct = crypt_help.encrypt_bytes(snapshot1_json_serial)

        log.vvvv('snapshot1 id: ' + snapshot1_id + "\nsnapshot1 json: " + snapshot1_ct)
        self._dao.add_snapshot(snapid=snapshot1_id, snapshot=snapshot1_ct)


    def _checkout_file(self, fname, fid, dest_dir_path):
        """ Given destination directory path, make a new file called fname (or overwrite fname if already existing)
        and fill it up with contents so that the file will have uvs fingerprint equal to fid. 
        after this operation the newly created file's uvsfp should equal to fid, if it does not this operation 
        will abort. Note that uvs fingerprints are deterministic for a given key, message pair. 
        the key is derived from this repo's key.
        """

        assert None != fname
        assert None != fid
        assert None != dest_dir_path
        assert isinstance(fname, str) or isinstance(fname, bytes) or isinstance(fname, unicode)

        log.vvv("checking out file. fname: " + str(fname) + " dst path: " + str(dest_dir_path) + " fid: " + str(fid))

        finfo_ct = self._dao.get_file(fid)

        log.vvvv("finfo ciphertext: " + str(finfo_ct))

        if None == finfo_ct:
            raise UVSErrorInvalidTree("No such file found for the given file id.")

        finfo_serial = self._crypt_helper.decrypt_bytes(ct=finfo_ct)

        log.vvv("finfo decrypted: " + str(finfo_serial))

        finfo = json.loads(finfo_serial)

        if ('segments' not in finfo) or ('verify_fid' not in finfo):
            raise UVSErrorInvalidFile("File json does not contain all expected keys.")

        if fid != finfo['verify_fid']:
            raise UVSErrorTamperDetected("Tamper detected, fid does not match verify fid.")

        # next open a file with temporary filename. write segments into it.
        temp_pathname = rand_util.choose_unique_random_file(dest_directory=dest_dir_path)

        # open the file in binary mode to write to.
        fhandle = open(temp_pathname, "wb")

        for sgid, offset in finfo['segments']:
            log.vvv(">>> (sgid, offset): " + str(sgid) + ", " + str(offset))

            segment_ct = self._dao.get_segment(sgid)

            if None == segment_ct:
                # TODO close and remove that file we opened.
                raise UVSErrorInvalidTree("No such segment found for the given sgid.")

            # TODO do segment decrypt in try, so we can delete the temp file. if we didn't have a temp file to
            # delete we could just let possible tamper errors propagate to the caller
            # alternative approach would be to write to system temp, but i dont like that. if these files
            # are sensitive enough to warrant encryption dont write them all over the hard disk and in /tmp and what not
            segment_bytes = self._crypt_helper.decrypt_bytes(ct=finfo_ct)

            # now seek to offset and write these bytes, 2nd argument (whence or from_what) == 0 means that
            # offset is calculated from start of the file, look at seek's pydoc
            fhandle.seek(offset,  0)
            fhandle.write(segment_bytes)

        # now change the filename from temp name to fname.

        shutil.move(src=temp_pathname, dst=os.path.join(dest_dir_path, fname))








    def _recursively_checkout_tree(self, tid, dest_dir_path):
        """ Given a tree id, and dest directory, this method will checkout the files of this tree node 
        into destination directory, and recursively call itself for any sub trees that might exist. """


        tree_info_ct = self._dao.get_tree(tid)

        log.vvvv("tree info ciphertext: " + str(tree_info_ct))

        if None == tree_info_ct:
            raise UVSErrorInvalidTree("No such tree found for the given tid.")

        tree_info_serial = self._crypt_helper.decrypt_bytes(ct=tree_info_ct)

        log.vvv("tree info decrypted: " + str(tree_info_serial))

        tree_info = json.loads(tree_info_serial)

        if ('fids' not in tree_info) or ('tids' not in tree_info):
            raise UVSErrorInvalidTree("Tree json does not contain all expected keys.")

        for fname, fid in tree_info['fids']:
            log.vvvv("fname: " + str(fname) +  " fid: " + str(fid))
            self._checkout_file(fname=fname, fid=fid, dest_dir_path=dest_dir_path)





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

        if clear_dest:
            # TODO
            # delete dest with all its files. and mkdir again.
            pass

        if not os.path.isdir(dest_dir_path):
            raise uvs_errors.UVSErrorInvalidDestinationDirectory("dest directory does not exist or i cant write to.")

        # To checkout, get the snapshot, find the root tree id. (raise error if decryption fails, or mac failed.)
        # checkout tree recursive function:
        #    assemble the files of this tree, write to disk. (raise error if any objects did decrypt or pass mac)
        #    call itself recursively on subdirs.
        snapshot_info_ct = self._dao.get_snapshot(snapid=snapid)

        if None == snapshot_info_ct:
            raise UVSErrorInvalidSnapshot("DAO could not find such snapshot with the given snapid.")

        snapshot_info_serial = self._crypt_helper.decrypt_bytes(ct=snapshot_info_ct)

        log.vvv("snapshot decrypted: " + str(snapshot_info_serial))

        snapshot_info = json.loads(snapshot_info_serial)

        if ('verify_snapid' not in snapshot_info) or ('root' not in snapshot_info) or ('msg' not in snapshot_info) \
                or ('author_name' not in snapshot_info) or ('author_email' not in snapshot_info) :
            raise UVSErrorInvalidSnapshot("Snapshot json does not contain all expected keys.")

        if snapid != snapshot_info['verify_snapid']:
            raise UVSErrorTamperDetected('Detected data structure tampering. Perhaps some1 tried to reorder snapshots')


        root_tid = snapshot_info['root']

        log.vvvv("root tid is: " + str(root_tid))

        self._recursively_checkout_tree(tid=root_tid, dest_dir_path=dest_dir_path)




if '__main__' == __name__:
    # log.vvvv(">> creating DAL")
    # dao = dal_psql.DAO()

    uvs_mgr = UVSManager()
    uvs_mgr.setup_for_new_repo(user_pass= 'weakpass123')
    #uvs_mgr.setup_for_existing_repo(user_pass= 'weakpass123')
    uvs_mgr.make_sample_snapshot_1()


    dest_dir = "../../sample_repo"
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    uvs_mgr.checkout_snapshot(snapid="446839f7b3372392e73c9e869b16a93f13161152f02ab2565de6a985", dest_dir_path=dest_dir,
                      clear_dest=False)

