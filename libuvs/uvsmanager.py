

import json
import os
import shutil
import errno

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






class HeadState(object):
    """" Enumerate different states a head reference can be in. """


    # UNINITIALIZED = 101
    # DETACHED = 102
    # ATTACHED = 103

    # means repo is empty head has never pointed to anything.
    UNINITIALIZED = "UNINITIALIZED"

    # means head reference is to a snapshot id.
    DETACHED = "DETACHED"

    # means head reference is to a branch name, the branch name eventually references a snapshot id.
    ATTACHED = "ATTACHED"







def init_new_uvs_repo_overwrite(repo_pass, repo_root_path):
    """ Initialize a new empty uvs repository. this function creates a new empty repo overwriting existing
    shadow files if any is present
    """

    assert repo_root_path != None
    assert os.path.isdir(repo_root_path)

    log.uvsmgrv("init_new_uvs_repo_overwrite() called, repo root:" + str(repo_root_path))

    shadow_root_path = os.path.join(repo_root_path, sdef._SHADOW_FOLDER_NAME)
    shadow_db_file_path = os.path.join(shadow_root_path, sdef._SHADOW_DB_FILE_NAME)

    # delete the file, suppress "file not found" exception, re-raise all other exceptions
    try:
        log.uvsmgr("Trying to remove uvs shadow db file if it exists. file path: " + shadow_db_file_path)
        os.remove(shadow_db_file_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            log.uvsmgr("uvs shadow db file was not found.")
        else:
            raise

    # create the shadow directory if it does not exist.
    try:
        os.makedirs(shadow_root_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            log.uvsmgr("repo_root/shadow_directory already exists")
            pass

    public_document = {}

    public_document['salt'] = cm.get_new_random_salt()
    public_document['uvs_version'] = _version.get_version()
    public_document['fingerprinting_algo'] = cm.get_uvs_fingerprinting_algo_desc()
    public_document['encryption'] = cm.get_encryption_algo_desc()

    log.uvsmgr("public doc: " + repr(public_document))

    public_doc_serialized = json.dumps(public_document, ensure_ascii=False, sort_keys=True)

    crypt_helper = cm.UVSCryptHelper(usr_pass=repo_pass, salt=public_document['salt'])

    # TODO I dont feel good about using uvsfp call to compute a MAC for public record
    # even tho we know uvsfp is a secure hmac, still i would like to call a method called compute hmac or something
    # to get the MAC. uvsfp may not be hmac always. i think this problem is caused due to using fernet for encryption
    # in the golang version of uvs hopefully i will take over and separate the encryption and mac and make them
    # individually configurable
    public_doc_serialized_mac_tag = crypt_helper.get_uvsfp(public_doc_serialized)


    # now make the history record
    hist_doc = {}

    # represent the commit (snapshot) history with adjacency list
    # parents -> a dict of <str snapid> to <list of parent snapids of this snapshot (adj list or neibors list)>
    hist_doc['parents'] = {}


    # one of "snapid" or "branch_handle" must always be None, head is either attached
    # in which case snapid should be none, to find the snapshot dereference the branch handle.
    # or head is detached (not attached to any branch) in this case branch handle must be None, snapid
    # is the detached commit id (snapshot id)

    # hist_doc['head'] = {'state': HeadState.UNINITIALIZED, 'snapid': None, 'branch_handle': None}
    # hist_doc['head'] = {'state': HeadState.ATTACHED, 'snapid': None, 'branch_handle': 'master'}

    hist_doc['head'] = {'state': HeadState.ATTACHED, 'snapid': None, 'branch_handle': 'master'}

    #assert (hist_doc['head']['snapid'] == None) or (hist_doc['head']['branch_handle'] == None)
    #assert (hist_doc['head']['state'] != HeadState.ATTACHED) or (hist_doc['head']['branch_handle'] != None)

    if hist_doc['head']['state'] == HeadState.ATTACHED:
        assert hist_doc['head']['snapid'] == None
        assert hist_doc['head']['branch_handle'] != None
        pass

    elif hist_doc['head']['state'] == HeadState.DETACHED:
        assert hist_doc['head']['snapid'] != None
        assert hist_doc['head']['branch_handle'] == None
        pass


    # i think we should separate branches and tags rather than treat them both as "refs" tags are fixed pointers
    # branches move as new commits (snapshots) are created on them.
    # branches is a dict from <str branch_name> to <str snapid of the latest snapshot of this branch>
    hist_doc['branches'] = {'master': None}



    hist_doc_serialized = json.dumps(hist_doc, ensure_ascii=False, sort_keys=True)
    hist_doc_ct = crypt_helper.encrypt_bytes(hist_doc_serialized)

    temp_dao = dal_sqlite.DAO(shadow_db_file_path)

    # create empty tables.
    temp_dao.create_empty_tables()

    temp_dao.set_repo_public_doc(public_doc=public_doc_serialized, public_doc_mac_tag=public_doc_serialized_mac_tag)
    temp_dao.set_repo_history_doc(history_doc=hist_doc_ct)



class UVSManager(object):

    def __init__(self, repo_pass, repo_root_path):
        """ Initialize a new uvs manager for interacting with an existing uvs repository with the given repo pass.

        supplied password. """

        super(UVSManager, self).__init__()

        log.uvsmgrv("++++++ initializing new uvs manager")

        assert repo_pass != None
        assert isinstance(repo_pass, str) or isinstance(repo_pass, bytes) or isinstance(repo_pass, unicode)

        assert repo_root_path != None
        assert os.path.isdir(repo_root_path)

        shadow_root_path = os.path.join(repo_root_path, sdef._SHADOW_FOLDER_NAME)
        shadow_db_file_path = os.path.join(shadow_root_path, sdef._SHADOW_DB_FILE_NAME)

        self._dao = dal_sqlite.DAO(shadow_db_file_path)

        pub_doc, pub_doc_mac_tag =  self._dao.get_repo_public_doc()

        log.uvsmgr("dao returned public document: " + str(pub_doc))
        log.uvsmgr("dao returned public document MAC tag: " + str(pub_doc_mac_tag))


        # if any of the pub doc or its mac tag is missing this is an invalid repo.
        if (None == pub_doc) or (None == pub_doc_mac_tag):
            raise uvs_errors.UVSErrorInvalidRepository("No valid public document found in this repository. ")


        # we need to verify this public doc's MAC tag to make sure its not tampered with.
        # here is what we do: assume its a valid public record and try to find the salt in it.
        # use the salt and user pass to derive the keys. now recompute the MAC tag using the keys
        # if the MAC's match then it was valid, otherwise drop our computations and raise error

        public_doc_dict = json.loads(pub_doc)

        if not public_doc_dict.has_key('salt'):
            raise uvs_errors.UVSErrorInvalidRepository('Invalid repo, public document does not have the salt.')

        tmp_crypt_helper = cm.UVSCryptHelper(usr_pass=repo_pass, salt= str(public_doc_dict['salt']))

        mac_tag_recomputed = tmp_crypt_helper.get_uvsfp(pub_doc)

        if mac_tag_recomputed != pub_doc_mac_tag:
            raise UVSErrorTamperDetected("Either the repository was tampered with or you supplied wrong password.")

        self._crypt_helper = tmp_crypt_helper
        self._repo_root_path = repo_root_path


    def take_snapshot(self, snapshot_msg, author_name, author_email):
        """ Take a snapshot image of this repository  right now and save the cipher text to uvs.shadow db file.
        returns the snapshot id of the newly created snapshot. 
        """
        assert None != self._dao
        assert None != self._crypt_helper
        assert isinstance(snapshot_msg, str) or isinstance(snapshot_msg, bytes) or isinstance(snapshot_msg, unicode)
        assert isinstance(author_name, str) or isinstance(author_name, bytes) or isinstance(author_name, unicode)
        assert isinstance(author_email, str) or isinstance(author_email, bytes) or isinstance(author_email, unicode)

        crypt_helper = self._crypt_helper

        names = os.listdir(self._repo_root_path )

        curr_dir_filenames = [fname for fname in names if os.path.isfile(os.path.join(self._repo_root_path , fname))]

        log.uvsmgr("Taking snapshot of repo root: " + str(self._repo_root_path))
        log.uvsmgr("Files to be included in this snapshot: " + repr(curr_dir_filenames) )

        tree_info = {}
        tree_info['tids'] = []  # add subtrees if this directory has sub directories
        tree_info['fids'] = []  # add files if this directory has files in it.

        for src_filename in curr_dir_filenames:
            src_pathname = os.path.join(self._repo_root_path, src_filename)

            curr_file_bytes = open(src_pathname, 'rb').read()
            curr_file_fp = crypt_helper.get_uvsfp(curr_file_bytes)
            curr_file_ct = crypt_helper.encrypt_bytes(curr_file_bytes)
            self._dao.add_segment(sgid=curr_file_fp, segment_bytes=curr_file_ct)

            finfo = {}
            finfo['verify_fid'] = curr_file_fp
            finfo['segments'] = []
            finfo['segments'].append((curr_file_fp, 0))

            finfo = json.dumps(finfo, ensure_ascii=False, sort_keys=True)

            finfo_ct = crypt_helper.encrypt_bytes(message=finfo)

            self._dao.add_file(fid=curr_file_fp, finfo=finfo_ct)



            # fids is a list of 2-tuples (name, fid) the list has to be sorted
            tree_info['fids'].append((src_filename, curr_file_fp))

        # it doesnt matter much what order things get sorted in, as long as it is deterministic.
        # this says sort by elem[0] first and in case of ties sort by elem[1], i think just sort woulda done the same.
        tree_info['fids'].sort(key=lambda elem: (elem[0], elem[1]))
        # tree1_info['fids'].sort()

        tree_info_serial = json.dumps(tree_info, ensure_ascii=False, sort_keys=True)

        # get the fingerprint and ciphertext
        tree_info_fp = crypt_helper.get_uvsfp(tree_info_serial)
        tree_info_ct = crypt_helper.encrypt_bytes(tree_info_serial)

        log.uvsmgrv('tree fp: ' + tree_info_fp + "\ntree info json: " + tree_info_serial)

        self._dao.add_tree(tid=tree_info_fp, tree_info=tree_info_ct)

        # give a random id to the new snapshot.
        new_snapid = rand_util.get_new_random_snapshot_id()

        snapshot_info = {}
        snapshot_info['verify_snapid'] = new_snapid
        snapshot_info['root'] = tree_info_fp
        snapshot_info['msg'] = snapshot_msg
        snapshot_info['author_name'] = author_name
        snapshot_info['author_email'] = author_email
        snapshot_info['snapshot_signature'] = "put gpg signature here to prove the author's identity."

        snapshot_info_serial = json.dumps(snapshot_info, ensure_ascii=False, sort_keys=True)
        snapshot_info_ct = crypt_helper.encrypt_bytes(snapshot_info_serial)

        log.uvsmgr('new snapshot id: ' + new_snapid + "\nnew snapshot json(ct): " + snapshot_info_ct)
        self._dao.add_snapshot(snapid=new_snapid, snapshot=snapshot_info_ct )

        # TODO update repo history


        return new_snapid





    def list_all_snapshots(self):
        """ Compute and return a list of all snapshots. this is a list of tuples like this:
         <snapid, commit msg, author name, author email>

         """

        snapshots = self._dao.get_all_snapshots()

        result_snapshots = []

        for snapid, snapinfo_json_ct in snapshots:

            snapinfo_json_pt = self._crypt_helper.decrypt_bytes(ct=bytes(snapinfo_json_ct))

            snapinfo_dict = json.loads(snapinfo_json_pt)

            result_row = [snapid, snapinfo_dict['msg'], snapinfo_dict['author_name'], snapinfo_dict['author_email']]

            log.uvsmgr("snapshot: " + str(result_row) )
            result_snapshots.append(result_row)

        return result_snapshots



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

        # get the fingerprint and cipher text
        tree1_fp = crypt_help.get_uvsfp(tree1_json_serial)
        tree1_ct = crypt_help.encrypt_bytes(tree1_json_serial)

        log.uvsmgrv('tree1 fp: ' + tree1_fp + "\ntree1 json: " + tree1_json_serial)

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

        log.uvsmgrv('snapshot1 id: ' + snapshot1_id + "\nsnapshot1 json: " + snapshot1_ct)
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

        log.uvsmgr("checking out file. fname: " + str(fname) + " dst path: " + str(dest_dir_path) + " fid: " + str(fid))

        finfo_ct = self._dao.get_file(fid)

        log.uvsmgrv("finfo cipher text: " + str(finfo_ct))

        if None == finfo_ct:
            raise UVSErrorInvalidTree("No such file found for the given file id.")

        finfo_serial = self._crypt_helper.decrypt_bytes(ct=finfo_ct)

        log.uvsmgr("finfo decrypted: " + str(finfo_serial))

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
            log.uvsmgr(">>> (sgid, offset): " + str(sgid) + ", " + str(offset))

            segment_ct = self._dao.get_segment(sgid)

            if None == segment_ct:
                # TODO close and remove that file we opened.
                raise UVSErrorInvalidTree("No such segment found for the given sgid.")

            # TODO do segment decrypt in try, so we can delete the temp file. if we didn't have a temp file to
            # delete we could just let possible tamper errors propagate to the caller
            # alternative approach would be to write to system temp, but i dont like that. if these files
            # are sensitive enough to warrant encryption dont write them all over the hard disk and in /tmp and what not
            segment_bytes = self._crypt_helper.decrypt_bytes(ct=segment_ct)

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

        log.uvsmgrv("tree info cipher text: " + str(tree_info_ct))

        if None == tree_info_ct:
            raise UVSErrorInvalidTree("No such tree found for the given tid.")

        tree_info_serial = self._crypt_helper.decrypt_bytes(ct=tree_info_ct)

        log.uvsmgr("tree info decrypted: " + str(tree_info_serial))

        tree_info = json.loads(tree_info_serial)

        if ('fids' not in tree_info) or ('tids' not in tree_info):
            raise UVSErrorInvalidTree("Tree json does not contain all expected keys.")

        for fname, fid in tree_info['fids']:
            log.uvsmgrv("fname: " + str(fname) +  " fid: " + str(fid))
            self._checkout_file(fname=fname, fid=fid, dest_dir_path=dest_dir_path)





    def checkout_snapshot(self, snapid, clear_dest=False):
        """ Given a valid snapshot id, set the content of working directory to the image of the repository
        at the time this snapshot id was taken.

         By default it will just overwrite the files that collide with this checkout. if clear_dest is set
         to True it will delete everything at destination except uvs internal files/folders.
        """

        assert isinstance(clear_dest, bool)
        assert snapid != None
        assert self._repo_root_path != None
        assert isinstance(snapid, str) or isinstance(snapid, bytes)

        # on windows path names are usually unicode, this might cause problems, be careful.
        assert isinstance(snapid, str) or isinstance(snapid, unicode)

        if clear_dest:
            # TODO
            # delete dest with all its files. and mkdir again.
            pass

        if not os.path.isdir(self._repo_root_path):
            raise uvs_errors.UVSErrorInvalidDestinationDirectory("repo root dir does not exist or i cant write to.")

        # To checkout, get the snapshot, find the root tree id. (raise error if decryption fails, or mac failed.)
        # checkout tree recursive function:
        #    assemble the files of this tree, write to disk. (raise error if any objects did decrypt or pass mac)
        #    call itself recursively on subdirs.
        snapshot_info_ct = self._dao.get_snapshot(snapid=snapid)

        if None == snapshot_info_ct:
            raise UVSErrorInvalidSnapshot("DAO could not find such snapshot with the given snapid.")

        snapshot_info_serial = self._crypt_helper.decrypt_bytes(ct=snapshot_info_ct)

        log.uvsmgr("snapshot decrypted: " + str(snapshot_info_serial))

        snapshot_info = json.loads(snapshot_info_serial)

        if ('verify_snapid' not in snapshot_info) or ('root' not in snapshot_info) or ('msg' not in snapshot_info) \
                or ('author_name' not in snapshot_info) or ('author_email' not in snapshot_info) :
            raise UVSErrorInvalidSnapshot("Snapshot json does not contain all expected keys.")

        if snapid != snapshot_info['verify_snapid']:
            raise UVSErrorTamperDetected('Detected data structure tampering. Perhaps some1 tried to reorder snapshots')


        root_tid = snapshot_info['root']

        log.uvsmgrv("root tid is: " + str(root_tid))

        self._recursively_checkout_tree(tid=root_tid, dest_dir_path=self._repo_root_path )



# if '__main__' == __name__:
#
#     repo_dir = "/home/lu/kouritron/repo1"
#     if not os.path.exists(repo_dir):
#         os.makedirs(repo_dir)
#
#     init_new_uvs_repo_overwrite(repo_root_path=repo_dir)
#
#     uvs_mgr = UVSManager(repo_pass='weakpass123', repo_root_path=repo_dir)
#
#
#
#     uvs_mgr.make_sample_snapshot_1()
#
#     ### ## tmp_snapid = uvs_mgr.take_snapshot(snapshot_msg="dumb commit", author_email="kourosh.sc@gmail.com", author_name="kourosh")
#
#     snapid1 = "446839f7b3372392e73c9e869b16a93f13161152f02ab2565de6a985"
#
#     uvs_mgr.checkout_snapshot(snapid=snapid1, clear_dest=False)
#
