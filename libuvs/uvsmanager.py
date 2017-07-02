

import json
import os
import shutil
import errno

import hash_util
import rand_util
import log
import cryptmanager as cm
import systemdefaults as sdef
import version
import uvs_errors
import dal_psql
import dal_blackhole
import dal_sqlite
from uvs_errors import *






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

    assert repo_root_path is not None
    assert os.path.isdir(repo_root_path)

    log.uvsmgrv("init_new_uvs_repo_overwrite() called, repo root:" + str(repo_root_path))

    shadow_root_path = os.path.join(repo_root_path, sdef.SHADOW_FOLDER_NAME)
    shadow_db_file_path = os.path.join(shadow_root_path, sdef.SHADOW_DB_FILE_NAME)

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
    public_document['uvs_version'] = version.get_version()
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

    # assert (hist_doc['head']['snapid'] is None) or (hist_doc['head']['branch_handle'] is None)
    # assert (hist_doc['head']['state'] != HeadState.ATTACHED) or (hist_doc['head']['branch_handle'] is not None)

    if hist_doc['head']['state'] == HeadState.ATTACHED:
        assert hist_doc['head']['snapid'] is None
        assert hist_doc['head']['branch_handle'] is not None
        pass

    elif hist_doc['head']['state'] == HeadState.DETACHED:
        assert hist_doc['head']['snapid'] is not None
        assert hist_doc['head']['branch_handle'] is None
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

        assert repo_pass is not None
        assert isinstance(repo_pass, str) or isinstance(repo_pass, bytes) or isinstance(repo_pass, unicode)

        assert repo_root_path is not None
        assert os.path.isdir(repo_root_path)

        shadow_root_path = os.path.join(repo_root_path, sdef.SHADOW_FOLDER_NAME)
        shadow_db_file_path = os.path.join(shadow_root_path, sdef.SHADOW_DB_FILE_NAME)

        self._dao = dal_sqlite.DAO(shadow_db_file_path)

        pub_doc, pub_doc_mac_tag = self._dao.get_repo_public_doc()

        log.uvsmgr("dao returned public document: " + str(pub_doc))
        log.uvsmgr("dao returned public document MAC tag: " + str(pub_doc_mac_tag))


        # if any of the pub doc or its mac tag is missing this is an invalid repo.
        if (pub_doc is None) or (pub_doc_mac_tag is None):
            raise uvs_errors.UVSErrorInvalidRepository("No valid public document found in this repository. ")


        # we need to verify this public doc's MAC tag to make sure its not tampered with.
        # here is what we do: assume its a valid public record and try to find the salt in it.
        # use the salt and user pass to derive the keys. now recompute the MAC tag using the keys
        # if the MAC's match then it was valid, otherwise drop our computations and raise error

        public_doc_dict = json.loads(pub_doc)

        if not public_doc_dict.has_key('salt'):
            raise uvs_errors.UVSErrorInvalidRepository('Invalid repo, public document does not have the salt.')

        tmp_crypt_helper = cm.UVSCryptHelper(usr_pass=repo_pass, salt=str(public_doc_dict['salt']))

        mac_tag_recomputed = tmp_crypt_helper.get_uvsfp(pub_doc)

        if mac_tag_recomputed != pub_doc_mac_tag:
            raise UVSErrorTamperDetected("Either the repository was tampered with or you supplied wrong password.")

        self._crypt_helper = tmp_crypt_helper
        self._repo_root_path = repo_root_path


    def _should_skip_directory_with_path(self, dirpath):
        """ Return true if the directory whose path is given in the argument, should NOT be included in
        version control. """

        assert isinstance(dirpath, str) or isinstance(dirpath, unicode) or isinstance(dirpath, bytes)

        ignore_dirnames = ('.uvs_shadow', '.uvs_cache')

        for ignore_dirname in ignore_dirnames:
            if ignore_dirname in dirpath:
                log.uvsmgr("\n**** Skipping dirpath: " + str(dirpath))
                return True

        return False


    def _get_subdirs_list_excluding_ignorables(self, subdir_name_list):
        """ Given a list of subdir names, return a new list including every name in the argument list except those
        that should be excluded from version control. """

        assert isinstance(subdir_name_list, list)

        result = []
        # TODO remove the hard codes, use constants
        ignore_dirnames = ('.uvs_shadow', '.uvs_cache')

        for subdir_name in subdir_name_list:

            should_skip = False

            # with this code we would ignore a subdir called foo_.uvs_shadow_bar
            # right now this is what we want. alternatively we could include these, but make sure change
            # the other functions (such as _should_skip_directory_with_path to not skip those)
            # we could change that to something that splits path names first and does an equality compare
            # to any token of the split (but be careful with how unix/windows paths should be split)
            for ignore_dirname in ignore_dirnames:
                if ignore_dirname in subdir_name:
                    should_skip = True

            if not should_skip:
                result.append(subdir_name)

        return result


    def _get_filename_list_excluding_ignorables(self, file_name_list):
        """ Given a list of file names in some directory, return a new list including every name in the argument
        list except those that should be excluded from version control. """

        assert isinstance(file_name_list, list)

        result = []
        ignore_dirnames = ("",)
        # TODO deal with files to be ignored

        result = file_name_list

        return result


    def _save_file(self, file_path):
        """ Given a path to a file store it in the dao, and return the file id (file fingerprint). .
        """

        curr_file_bytes = open(file_path, 'rb').read()
        curr_file_fp = self._crypt_helper.get_uvsfp(curr_file_bytes)
        curr_file_ct = self._crypt_helper.encrypt_bytes(curr_file_bytes)
        self._dao.add_segment(sgid=curr_file_fp, segment_bytes=curr_file_ct)

        finfo = {}
        finfo['verify_fid'] = curr_file_fp
        finfo['segments'] = []
        finfo['segments'].append((curr_file_fp, 0))

        finfo = json.dumps(finfo, ensure_ascii=False, sort_keys=True)

        finfo_ct = self._crypt_helper.encrypt_bytes(message=finfo)

        self._dao.add_file(fid=curr_file_fp, finfo=finfo_ct)

        return curr_file_fp


    def _make_and_save_tree(self, dirpath, subdir_name_list, file_name_list):
        """ Make a tree object, save it in dao, and return the tid, for the supplied dirpath containing the
        supplied files and subdirs.
        files will be read from disk, subdirs must already have existing trees for them ready. """

        assert isinstance(dirpath, str) or isinstance(dirpath, bytes) or isinstance(dirpath, unicode)
        assert isinstance(subdir_name_list, list) or isinstance(subdir_name_list, tuple)
        assert isinstance(file_name_list, list) or isinstance(file_name_list, tuple)

        assert self._dao is not None
        assert self._crypt_helper is not None
        assert self._curr_snapshot_prev_seen_tree_ids is not None


        # make tree must visit directories and subdirs bottom up. meaning first the deepest subdir must be
        # visited. once a all subdirs of a directory are visited its ok to visit that directory itself.
        # this because the tid (the fingerprint of the tree) depends on the fingerprint of the subdir
        # in order to deterministically identify previously seen trees. (i.e. 2 trees are different if they
        # have subdirs that eventually differ)
        for subdir_name in subdir_name_list:
            subdir_path = os.path.join(dirpath, subdir_name)
            assert self._curr_snapshot_prev_seen_tree_ids.has_key(subdir_path)
            assert os.path.isdir(subdir_path)

        # if we didnt fail the assertions, then we should have a tid for every subdir.
        # Now check that the file names exist on disk.
        for file_name in file_name_list:
            assert os.path.isfile(os.path.join(dirpath, file_name))

        if 0 == len(subdir_name_list):
            log.uvsmgr("Found leave tree node with path: " + str(dirpath))
        else:

            # ok this directory has subdirs, we should have seen them b4 we can deal with this directory
            log.uvsmgr("++ now dealing with directory with subdirs, this dir's path: " + str(dirpath))
            log.uvsmgr("++ prev_seen_dirs: " + repr(self._curr_snapshot_prev_seen_tree_ids))
            log.uvsmgr("++ subdir names: " + str(subdir_name_list))


        # if this is a leave tree node. (dir with no subdirs) make a tree, encrypt and save it.
        # also save the (path, tid) of the directory associated with this tree to a temp dict.
        # if this tree node has subdirs we should have seen them before and made trees for them
        # (find the tids using path as key) and that should be all we need to make trees for dirs with subdirs..

        # now make the actual tree and store it in the dao.
        # tree id is same as tree fingerprint.
        tree_id = None
        crypt_helper = self._crypt_helper

        tree_info = {}

        # fids is a list of 2-tuples (file name, fid) the list has to be sorted to be deterministic
        tree_info['fids'] = []

        # tids is a list of 2-tuples (tree name, tid) the list has to be sorted to be deterministic
        tree_info['tids'] = []

        for file_name in file_name_list:
            file_path = os.path.join(dirpath, file_name)

            # after this call the file should be saved in the repository, and we have its file id (or fingerprint)
            file_fp = self._save_file(file_path=file_path)

            # fids is a list of 2-tuples (name, fid) the list has to be sorted
            tree_info['fids'].append((file_name, file_fp))


        # tree name will be the subdir name not the subdir path.
        for tree_name in subdir_name_list:
            tid = self._curr_snapshot_prev_seen_tree_ids[os.path.join(dirpath, tree_name)]
            tree_info['tids'].append((tree_name, tid))


        # it doesnt matter much what order things get sorted in, as long as it is deterministic.
        # this says sort by elem[0] first and in case of ties sort by elem[1], i think just sort woulda done the same.
        tree_info['fids'].sort(key=lambda elem: (elem[0], elem[1]))
        # tree1_info['fids'].sort()

        # sort the sub trees, again make sure it is deterministic.
        # (that is a given version of uvs always does it, in the same order.)
        tree_info['tids'].sort(key=lambda elem: (elem[0], elem[1]))

        tree_info_serial = json.dumps(tree_info, ensure_ascii=False, sort_keys=True)

        # get the fingerprint and ciphertext
        tree_id = crypt_helper.get_uvsfp(tree_info_serial)
        tree_info_ct = crypt_helper.encrypt_bytes(tree_info_serial)

        log.uvsmgrv('tree fp: ' + tree_id + "\ntree info json: " + tree_info_serial)

        self._dao.add_tree(tid=tree_id, tree_info=tree_info_ct)

        self._curr_snapshot_prev_seen_tree_ids[dirpath] = tree_id

        return tree_id


    def take_snapshot(self, snapshot_msg, author_name, author_email):
        """ Take a snapshot image of this repository  right now and save the cipher text to uvs.shadow db file.
        returns the snapshot id of the newly created snapshot. 
        """
        assert self._dao is not None
        assert self._crypt_helper is not None
        assert isinstance(snapshot_msg, str) or isinstance(snapshot_msg, bytes) or isinstance(snapshot_msg, unicode)
        assert isinstance(author_name, str) or isinstance(author_name, bytes) or isinstance(author_name, unicode)
        assert isinstance(author_email, str) or isinstance(author_email, bytes) or isinstance(author_email, unicode)

        log.uvsmgr("Taking snapshot of repo root: " + str(self._repo_root_path))

        crypt_helper = self._crypt_helper

        # dict of pathname to tid
        # i.e. ./tests/test_suite1/    -->>  tid0001
        self._curr_snapshot_prev_seen_tree_ids = {}

        # walk everything in this path
        # . means simply cwd. this could be abs path or relative path to cwd
        walk_root = self._repo_root_path
        walk_root_tid = None

        for dirpath, unfiltered_subdir_name_list, unfiltered_file_name_list in os.walk(top=walk_root, topdown=False):

            if self._should_skip_directory_with_path(dirpath):
                continue

            # get list of subdirs under version control
            vc_subdir_name_list = self._get_subdirs_list_excluding_ignorables(unfiltered_subdir_name_list)
            vc_file_name_list = self._get_filename_list_excluding_ignorables(unfiltered_file_name_list)

            log.uvsmgr('---------------------------------------------------------------------------------')
            log.uvsmgr(">>>> creating new tree for dirpath: " + str(dirpath))
            log.uvsmgr(">> subtree names: " + str(vc_subdir_name_list))
            log.uvsmgr(">> filenames in this tree: " + str(vc_file_name_list))
            log.uvsmgrv("unfiltered_subdir_name_list: " + str(unfiltered_subdir_name_list))
            log.uvsmgrv("unfiltered_file_name_list: " + str(unfiltered_file_name_list))

            # the last iterations' write of this variable will survive the loop.
            # the last iterations should return the tid of the walk root
            walk_root_tid = self._make_and_save_tree(dirpath=dirpath, subdir_name_list=vc_subdir_name_list,
                                                     file_name_list=vc_file_name_list)

        # out of the loop
        assert walk_root_tid is not None

        # give a random id to the new snapshot.
        new_snapid = rand_util.get_new_random_snapshot_id()

        snapshot_info = {}
        snapshot_info['verify_snapid'] = new_snapid
        snapshot_info['root'] = walk_root_tid
        snapshot_info['msg'] = snapshot_msg
        snapshot_info['author_name'] = author_name
        snapshot_info['author_email'] = author_email
        snapshot_info['snapshot_signature'] = "put gpg signature here to prove the author's identity."

        snapshot_info_serial = json.dumps(snapshot_info, ensure_ascii=False, sort_keys=True)
        snapshot_info_ct = crypt_helper.encrypt_bytes(snapshot_info_serial)

        log.uvsmgr('new snapshot id: ' + new_snapid + "\nnew snapshot json(ct): " + snapshot_info_ct)
        self._dao.add_snapshot(snapid=new_snapid, snapshot=snapshot_info_ct)

        # TODO update repo history

        # drop temp data structures for this snapshot
        self._curr_snapshot_prev_seen_tree_ids = None

        return new_snapid


    def compute_tree_id_for_directory(self, target_path):
        """ Compute the tree id for the given target path, which must be a directory path.
        This is the tree id that target_path would acquire if we tried to take an snapshot right now.

        This method does not take the snapshot, just compute the tree id and return it, without causing any
        side effects.
        """

        assert self._crypt_helper is not None
        assert target_path is not None
        assert isinstance(target_path, str) or isinstance(target_path, bytes) or isinstance(target_path, unicode)
        assert os.path.isdir(target_path)

        log.uvsmgrv("compute_tree_id_for_directory() called.")
        log.uvsmgr("Computing tree id for directory: " + str(target_path))

        # here is what we do: swap out the dao for a blackhole dao temporarily.
        # do mostly the same thing that take snapshot does. than put the original dao back where it was.

        # save the current dao.
        original_dao = self._dao
        self._dao = dal_blackhole.DAO()


        # dict of pathname to tid
        # i.e. ./tests/test_suite1/    -->>  tid0001
        self._curr_snapshot_prev_seen_tree_ids = {}

        # walk everything in this path
        # . means simply cwd. this could be abs path or relative path to cwd
        walk_root = target_path
        walk_root_tid = None

        for dirpath, unfiltered_subdir_name_list, unfiltered_file_name_list in os.walk(top=walk_root, topdown=False):

            if self._should_skip_directory_with_path(dirpath):
                continue

            # get list of subdirs under version control
            vc_subdir_name_list = self._get_subdirs_list_excluding_ignorables(unfiltered_subdir_name_list)
            vc_file_name_list = self._get_filename_list_excluding_ignorables(unfiltered_file_name_list)

            # the last iterations' write of this variable will survive the loop.
            # the last iterations should return the tid of the walk root
            walk_root_tid = self._make_and_save_tree(dirpath=dirpath, subdir_name_list=vc_subdir_name_list,
                                                     file_name_list=vc_file_name_list)

        # out of the loop
        assert walk_root_tid is not None

        log.uvsmgr('Computed tree id: ' + str(walk_root_tid) + "\nFor directory path: " + str(target_path))

        # drop temp data structures for this snapshot
        self._curr_snapshot_prev_seen_tree_ids = None

        # restore the original dao
        self._dao = original_dao

        return walk_root_tid


    def compute_repo_root_tree_id(self):
        """ Compute the tree id for the repo root directory right now.
        this is the tree id that an snapshot taken right now would point to if an snapshot were taken right now.

        This method does not take the snapshot, just compute the tree id and return it, without causing any
        side effects.
        """

        log.uvsmgrv("compute_repo_root_tree_id() called.")
        log.uvsmgr("Computing repo root tree id, repo root path: " + str(self._repo_root_path))

        return self.compute_tree_id_for_directory(target_path=self._repo_root_path)



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

            log.uvsmgr("snapshot: " + str(result_row))
            result_snapshots.append(result_row)

        return result_snapshots


    def _checkout_file(self, fname, fid, dest_dir_path):
        """ Given destination directory path, make a new file called fname (or overwrite fname if already existing)
        and fill it up with contents so that the file will have uvs fingerprint equal to fid. 
        after this operation the newly created file's uvsfp should equal to fid, if it does not this operation 
        will abort. Note that uvs fingerprints are deterministic for a given key, message pair. 
        the key is derived from this repo's key.
        """

        assert fname is not None
        assert fid is not None
        assert dest_dir_path is not None
        assert isinstance(fname, str) or isinstance(fname, bytes) or isinstance(fname, unicode)

        log.uvsmgr("checking out file. fname: " + str(fname) + " dst path: " + str(dest_dir_path) + " fid: " + str(fid))

        finfo_ct = self._dao.get_file(fid)

        log.uvsmgrv("finfo cipher text: " + str(finfo_ct))

        if finfo_ct is None:
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

            if segment_ct is None:
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
        """ Given a tree id, and dest directory, this method will checkout the contents of this tree node
        into destination directory, and recursively call itself for any sub trees that might exist. """


        tree_info_ct = self._dao.get_tree(tid)

        if tree_info_ct is None:
            raise UVSErrorInvalidTree("Cant find the tree to check out. Data structures must be corrupted.")

        tree_info_serial = self._crypt_helper.decrypt_bytes(ct=tree_info_ct)

        log.uvsmgrv("tree info cipher text: " + str(tree_info_ct))
        log.uvsmgr("tree info decrypted: " + str(tree_info_serial))

        tree_info = json.loads(tree_info_serial)

        if ('fids' not in tree_info) or ('tids' not in tree_info):
            raise UVSErrorInvalidTree("Tree json does not contain all expected keys.")

        for fname, fid in tree_info['fids']:
            log.uvsmgrv("fname: " + str(fname) + " fid: " + str(fid))
            self._checkout_file(fname=fname, fid=fid, dest_dir_path=dest_dir_path)

        for tree_name, tree_id in tree_info['tids']:

            log.uvsmgrv("tree_name: " + str(tree_name) + " tree_id: " + str(tree_id))

            # mkdir for tree name. add it to dest path and checkout the tid into it.
            new_tree_path = os.path.join(dest_dir_path, tree_name)
            os.mkdir(new_tree_path)
            self._recursively_checkout_tree(tid=tree_id, dest_dir_path=new_tree_path)





    def checkout_snapshot(self, snapid, clear_dest=True):
        """ Given a valid snapshot id, set the content of working directory to the image of the repository
        at the time this snapshot id was taken.

         By default it will just overwrite the files that collide with this checkout. if clear_dest is set
         to True it will delete everything at destination except uvs internal files/folders.
        """

        assert isinstance(clear_dest, bool)
        assert snapid is not None
        assert self._repo_root_path is not None
        assert isinstance(snapid, str) or isinstance(snapid, bytes)

        # on windows path names are usually unicode, this might cause problems, be careful.
        assert isinstance(snapid, str) or isinstance(snapid, unicode)

        if not os.path.isdir(self._repo_root_path):
            raise uvs_errors.UVSErrorInvalidDestinationDirectory("repo root dir does not exist or i cant write to.")

        # TODO: i think we should not remove files that are not version controlled.
        # study git's behavior on this.
        if clear_dest:

            repo_root_members = os.listdir(self._repo_root_path)
            log.uvsmgr("clearing repo root, repo root members: " + repr(repo_root_members))

            actual_paths_to_remove = []

            dont_remove = set()
            dont_remove.add(sdef.CACHE_FOLDER_NAME)
            dont_remove.add(sdef.SHADOW_FOLDER_NAME)
            dont_remove.add(sdef.SHADOW_DB_FILE_NAME)

            for repo_root_member in repo_root_members:
                if repo_root_member not in dont_remove:
                    actual_paths_to_remove.append(os.path.join(self._repo_root_path, repo_root_member))


            log.uvsmgr("clearing repo root for new checkout, removing: " + repr(actual_paths_to_remove))

            for path in actual_paths_to_remove:
                if os.path.isdir(path):
                    # TODO: perhaps write a manual directory remover that uses os.walk to traverse and
                    # delete a directory similar to rmtree, but skip if we found uvs_shadow down the tree.
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)


        # To checkout, get the snapshot, find the root tree id. (raise error if decryption fails, or mac failed.)
        # checkout tree recursive function:
        #    assemble the files of this tree, write to disk. (raise error if any objects did decrypt or pass mac)
        #    call itself recursively on subdirs.
        snapshot_info_ct = self._dao.get_snapshot(snapid=snapid)

        if snapshot_info_ct is None:
            raise UVSErrorInvalidSnapshot("Could not find that snapshot id.")

        snapshot_info_serial = self._crypt_helper.decrypt_bytes(ct=snapshot_info_ct)

        log.uvsmgr("snapshot decrypted: " + str(snapshot_info_serial))

        snapshot_info = json.loads(snapshot_info_serial)

        if ('verify_snapid' not in snapshot_info) or ('root' not in snapshot_info) or ('msg' not in snapshot_info) \
                or ('author_name' not in snapshot_info) or ('author_email' not in snapshot_info):
            raise UVSErrorInvalidSnapshot("Snapshot json does not contain all expected keys.")

        if snapid != snapshot_info['verify_snapid']:
            raise UVSErrorTamperDetected('Detected data structure tampering. Perhaps some1 tried to reorder snapshots')


        root_tid = snapshot_info['root']

        log.uvsmgrv("root tid is: " + str(root_tid))

        self._recursively_checkout_tree(tid=root_tid, dest_dir_path=self._repo_root_path)



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
#     ### ## tmp_snapid = uvs_mgr.take_snapshot(snapshot_msg="msg1", author_email="n/a", author_name="n/a")
#
#     snapid1 = "446839f7b3372392e73c9e869b16a93f13161152f02ab2565de6a985"
#
#     uvs_mgr.checkout_snapshot(snapid=snapid1, clear_dest=False)
#
