

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
import dal_psql
import dal_blackhole
import dal_sqlite
import graph_util
import automergeservice
import validatorservice as vldserv
from uvs_errors import *
from uvsconst import UVSConst


_MAIN_REF_DOC_NAME = 'main'



class HeadState(object):
    """" Enumerate different states a head reference can be in. """


    # DETACHED = 111
    # ATTACHED = 112


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

    public_doc_serialized = json.dumps(public_document, ensure_ascii=True, sort_keys=True)

    crypt_helper = cm.UVSCryptHelper(usr_pass=repo_pass, salt=public_document['salt'])

    # TODO I dont feel good about using uvsfp call to compute a MAC for public record
    # even tho we know uvsfp is a secure hmac, still i would like to call a method called compute hmac or something
    # to get the MAC. uvsfp may not be hmac always. i think this problem is caused due to using fernet for encryption
    # in the golang version of uvs hopefully i will take over and separate the encryption and mac and make them
    # individually configurable
    public_doc_serialized_mac_tag = crypt_helper.get_uvsfp(public_doc_serialized)


    # now make the main references document
    main_refs_doc = {}


    # branch names should be case insensitive, its 2 confusing to have master and MASteR and masTer be actually
    # 3 different branches.
    # users can't create a branch called head (or HEAD) (same as git)
    # other branch names share the namespace with "master" and "head"
    # branches move as new commits (snapshots) are created on them.
    # ref_doc['branch_name']  <----> <str snapid of the latest snapshot of this branch>
    main_refs_doc['master'] = None

    # one of "snapid" or "branch_handle" must always be None, head is either attached
    # in which case snapid should be none, to find the snapshot dereference the branch handle.
    # or head is detached (not attached to any branch) in this case branch handle must be None, snapid
    # is the detached commit id (snapshot id)

    main_refs_doc['head'] = {'state': HeadState.ATTACHED, 'snapid': None, 'branch_handle': 'master'}

    if main_refs_doc['head']['state'] == HeadState.ATTACHED:
        assert main_refs_doc['head']['snapid'] is None
        assert main_refs_doc['head']['branch_handle'] is not None

        # if branch handle exists assert that it points to a valid branch name
        assert main_refs_doc.has_key( main_refs_doc['head']['branch_handle'] )

    elif main_refs_doc['head']['state'] == HeadState.DETACHED:
        assert main_refs_doc['head']['snapid'] is not None
        assert main_refs_doc['head']['branch_handle'] is None
        pass


    main_refs_doc_serialized = json.dumps(main_refs_doc, ensure_ascii=True, sort_keys=True)
    main_refs_doc_ct = crypt_helper.encrypt_bytes(main_refs_doc_serialized)

    temp_dao = dal_sqlite.DAO(shadow_db_file_path)

    # create empty tables.
    temp_dao.create_empty_tables()

    temp_dao.set_repo_public_doc(public_doc=public_doc_serialized, public_doc_mac_tag=public_doc_serialized_mac_tag)
    temp_dao.update_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME, ref_doc=main_refs_doc_ct)


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
            raise UVSError("Invalid repo, No valid public document found in this repository. ")


        # we need to verify this public doc's MAC tag to make sure its not tampered with.
        # here is what we do: assume its a valid public record and try to find the salt in it.
        # use the salt and user pass to derive the keys. now recompute the MAC tag using the keys
        # if the MAC's match then it was valid, otherwise drop our computations and raise error

        public_doc_dict = json.loads(pub_doc)

        if not public_doc_dict.has_key('salt'):
            raise UVSError('Invalid repo, public document does not have the repository salt.')

        tmp_crypt_helper = cm.UVSCryptHelper(usr_pass=repo_pass, salt=str(public_doc_dict['salt']))

        mac_tag_recomputed = tmp_crypt_helper.get_uvsfp(pub_doc)

        if mac_tag_recomputed != pub_doc_mac_tag:
            raise UVSError("Either the repository was tampered with or you supplied wrong password.")

        self._crypt_helper = tmp_crypt_helper
        self._repo_root_path = repo_root_path


    def _should_skip_directory_with_path(self, dirpath):
        """ Return true if the directory whose path is given in the argument, should NOT be included in
        version control. """

        assert isinstance(dirpath, str) or isinstance(dirpath, unicode) or isinstance(dirpath, bytes)

        ignore_dirnames = (sdef.SHADOW_FOLDER_NAME, sdef.TEMP_DIR_NAME)

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

        #
        ignore_dirnames = (sdef.SHADOW_FOLDER_NAME, sdef.TEMP_DIR_NAME)

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

        # TODO break this into smaller segments.
        curr_file_bytes = open(file_path, 'rb').read()
        curr_file_fp = self._crypt_helper.get_uvsfp(curr_file_bytes)
        curr_file_ct = self._crypt_helper.encrypt_bytes(curr_file_bytes)
        self._dao.add_segment(sgid=curr_file_fp, segment_bytes=curr_file_ct)

        finfo = {}
        finfo['verify_fid'] = curr_file_fp
        finfo['segments'] = []
        finfo['segments'].append((curr_file_fp, 0))

        finfo = json.dumps(finfo, ensure_ascii=True, sort_keys=True)

        finfo_ct = self._crypt_helper.encrypt_bytes(message=finfo)

        # careful, file fingerprint must be the fingerprint of the file content, not the fp of finfo dict
        # otherwise we, wouldn't be able to ask "have i seen this file before" type questions.
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

        tree_info_serial = json.dumps(tree_info, ensure_ascii=True, sort_keys=True)

        # get the fingerprint (aka tree id) and the ciphertext
        tree_id = crypt_helper.get_uvsfp(tree_info_serial)
        tree_info_ct = crypt_helper.encrypt_bytes(tree_info_serial)

        log.uvsmgrv('tree fp: ' + tree_id + "\ntree info json: " + tree_info_serial)

        self._dao.add_tree(tid=tree_id, tree_info=tree_info_ct)

        self._curr_snapshot_prev_seen_tree_ids[dirpath] = tree_id

        return tree_id


    def take_snapshot(self, snapshot_msg, author_name, author_email, explicit_parents_for_merge_commit=None):
        """ Take a snapshot image of this repository  right now and save the cipher text to uvs.shadow db file.
        returns the snapshot id of the newly created snapshot. 
        """

        assert (explicit_parents_for_merge_commit is None) or isinstance(explicit_parents_for_merge_commit, list)

        assert self._dao is not None
        assert self._crypt_helper is not None
        assert isinstance(snapshot_msg, str) or isinstance(snapshot_msg, bytes) or isinstance(snapshot_msg, unicode)
        assert isinstance(author_name, str) or isinstance(author_name, bytes) or isinstance(author_name, unicode)
        assert isinstance(author_email, str) or isinstance(author_email, bytes) or isinstance(author_email, unicode)

        log.uvsmgr("Taking snapshot of repo root: " + str(self._repo_root_path))

        # first fetch the main_refs_doc
        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is None) or ('head' not in main_refs_doc):
            raise UVSError("Invalid repo, head does not exist. Are you sure this is a uvs repository.")


        # TODO refactor this function for merge commits where we have more than, one parent.
        # while you are refactoring this maybe abstract some code away for compute tree id function (the blackhole
        # dao trick) and re-use the same code. to lessen code repeat, although its not much.
        # this new snapshot will have one parent, because its not a merge snapshot (commit).
        # the one parent should be:
        # >> empty list ( [] ) if repo is empty.
        # >> [parent_snapid] if one parent
        # >> [parent1_snapid, parent2_snapid, ....] if more than one parent ( i dont  think we ever have more than 2

        parent_snapids = []


        assert main_refs_doc['head'].has_key('state')
        assert main_refs_doc['head'].has_key('snapid')
        assert main_refs_doc['head'].has_key('branch_handle')

        if main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            current_branch = main_refs_doc['head']['branch_handle']
            log.uvsmgr (">>> current_branch: " + str(current_branch))

            # assert that current branch name actually is the branch name of a valid branch.
            assert main_refs_doc.has_key(current_branch)

            # now dereference current branch to get a snapid of the parent.
            if main_refs_doc[current_branch] is not None:
                parent_snapids.append(main_refs_doc[current_branch])

        elif main_refs_doc['head']['state'] == HeadState.DETACHED:
            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            # find the parent snap id.
            head_snapid = main_refs_doc['head']['snapid']
            if head_snapid is not None:
                parent_snapids.append(head_snapid)


        for parent_snapid in parent_snapids:

            log.uvsmgr(">>>> parent_snapid: " + str(parent_snapid) )

            parent_snap_json = self._dao.get_snapshot(snapid=parent_snapid)
            assert parent_snap_json is not None


        # in case parent_snapids is an empty list, assert that the repo has no commits (just got inited)
        if 0 == len(parent_snapids):
            assert 0 == self._dao.get_snapshots_count()



        # TODO, perhaps there is a cleaner way to accomodate merge commits:
        if explicit_parents_for_merge_commit is not None:
            parent_snapids = explicit_parents_for_merge_commit



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

        # TODO move this into another table called digital signatures. its not needed for now.
        #snapshot_info['snapshot_signature'] = "put gpg signature here to prove the author's identity."

        # represent the commit (snapshot) history with adjacency list
        # each snapshot knows its parents (or neighbours in graph speech)
        snapshot_info['parents'] = parent_snapids



        snapshot_info_serial = json.dumps(snapshot_info, ensure_ascii=True, sort_keys=True)
        snapshot_info_ct = crypt_helper.encrypt_bytes(snapshot_info_serial)

        log.uvsmgr('new snapshot id: ' + new_snapid + "\nnew snapshot json(ct): " + snapshot_info_ct)

        # TODO refactor dao.
        # here we wanna say dao.begin_transaction
        # add snapshot to the snapshots table.
        # update head, master or something else.
        # now dao.commit_transaction

        self._dao.add_snapshot(snapid=new_snapid, snapshot=snapshot_info_ct)


        # commit made now update head, master, other branch pointers.

        if main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            # assert that current branch name actually is the branch name of a valid branch.
            current_branch = main_refs_doc['head']['branch_handle']
            assert main_refs_doc.has_key(current_branch)

            # now set the snapshot id on the branch pointer.
            # branches move as new commits (snapshots) are created on them.
            # ref_doc['branch_name']  <----> <str snapid of the latest snapshot of this branch>
            main_refs_doc[current_branch] = new_snapid

        elif main_refs_doc['head']['state'] == HeadState.DETACHED:
            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            main_refs_doc['head']['snapid'] = new_snapid


        # save the main refs
        new_main_refs_serialized = json.dumps(main_refs_doc, ensure_ascii=True, sort_keys=True)

        #log.v("type(new_main_refs_serialized): " + str(type(new_main_refs_serialized)))

        new_main_refs_ct = crypt_helper.encrypt_bytes(new_main_refs_serialized)

        self._dao.update_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME, ref_doc=new_main_refs_ct)


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

        assert not self._should_skip_directory_with_path(target_path), 'cant compute tree id for this target path'

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

    def get_status(self):
        """ Compute and return repository status as a dict.

        the dict will have these key, values:

        "working_dir_clean" : True/False    # true if there are no un-committed changes.
        "head" : commit id     # (snapid) of the repository head, or None if repo empty.
        "detached_head" : True/False

        if  "detached_head" is False: this key, value also present:

        "current_branch" : "branch_name"

        """


        assert self._dao is not None
        assert self._crypt_helper is not None

        log.uvsmgr("checking working directory for un-committed changes. repo root: " + str(self._repo_root_path))

        result = {}

        # first fetch the main_refs_doc
        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is None) or ('head' not in main_refs_doc):
            raise UVSError("Error: head does not exist. Are you sure this is a uvs repository.")


        assert main_refs_doc['head'].has_key('state')
        assert main_refs_doc['head'].has_key('snapid')
        assert main_refs_doc['head'].has_key('branch_handle')

        if main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            current_branch = main_refs_doc['head']['branch_handle']

            # assert that current branch name actually is the branch name of a valid branch.
            assert main_refs_doc.has_key(current_branch)
            log.uvsmgr("Head is attached to branch: " + str(current_branch))

            result['detached_head'] = False
            result['current_branch'] = current_branch

            # follow current branch's handle to get a snapid of repo head.
            result['head'] = main_refs_doc[current_branch]

        elif main_refs_doc['head']['state'] == HeadState.DETACHED:
            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            log.uvsmgr("Repo is in detached head state.")

            result['detached_head'] = True
            result['head'] = main_refs_doc['head']['snapid']

        # if repo is empty working dir is not clean. because none tree_id is different then whatever we would get for
        # empty tree.
        result['working_dir_clean'] = False

        if result['head'] is None:
            return result

        current_root_tree_id = self.compute_repo_root_tree_id()

        # get the root tree id of head. (raise error if decryption fails, or mac failed.)
        snapshot_info_ct = self._dao.get_snapshot(snapid= result['head'])

        if snapshot_info_ct is None:
            raise UVSError("Could not find snapshot with id: " + str(result['head']))

        snapshot_info_serial = self._crypt_helper.decrypt_bytes(ct=snapshot_info_ct)

        log.uvsmgr("head snapshot retrieved and decrypted: " + str(snapshot_info_serial))

        snapshot_info = json.loads(snapshot_info_serial)

        if 'root' not in snapshot_info:
            raise UVSError("invalid snapshot, json does not contain all expected keys.")

        head_root_tid = snapshot_info['root']

        if current_root_tree_id == head_root_tid:
            result['working_dir_clean'] = True

        return result



    def create_new_branch(self, new_branch_name, set_current_branch):
        """ Create a new branch reference and have it point to whatever head is pointing to right now.
        if set_current_branch flag is true, head will point to this branch name after this operation.

        :param new_branch_name: the name of the new branch
        :param set_current_branch: if True the new branch will also become the repository's current branch
        :return: void if successful, might raise error if operation can not be completed.
        """

        assert self._dao is not None
        assert self._crypt_helper is not None

        assert isinstance(new_branch_name, str) or isinstance(new_branch_name, unicode)
        assert isinstance(set_current_branch, bool)


        log.uvsmgr("checking working directory for un-committed changes. repo root: " + str(self._repo_root_path))

        result = {}

        if 'head' == new_branch_name.lower():
            result['op_failed'] = True
            result['op_failed_desc'] = 'It does not make sense to create a branch called head.'
            return result

        # TODO disallow a list of disallowed branch names, store all disallowed under UVSConstants
        # this should include common ancestor head, .....

        # Now look at snapshots table.
        # its crazy to create a branch whose name is the commit id of some other commit.
        # try to get snapshot, if we got something other than none, then snapshot does exist.
        if self._dao.get_snapshot(snapid=new_branch_name) is not None:
            result['op_failed'] = True
            result['op_failed_desc'] = "It makes no sense to create a branch with the name of an existing commit. \n"
            result['op_failed_desc'] += "you supplied branch name: " + str(new_branch_name)
            return result


        # check to see if there already is a branch with this name. in that case return error, branch already exists.
        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is  None) or ('head' not in main_refs_doc):
            result['op_failed'] = True
            result['op_failed_desc'] = 'Cant find head. Is this a uvs repo, path: ' + str(self._repo_root_path)
            return result


        if main_refs_doc.has_key(new_branch_name):
            result['op_failed'] = True
            result['op_failed_desc'] = 'That branch already exists. you supplied: ' + str(new_branch_name)
            return result


        assert main_refs_doc['head'].has_key('state')
        assert main_refs_doc['head'].has_key('snapid')
        assert main_refs_doc['head'].has_key('branch_handle')

        if main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            current_branch = main_refs_doc['head']['branch_handle']

            # assert that current branch name actually is the branch name of a valid branch.
            assert main_refs_doc.has_key(current_branch)
            log.uvsmgr("Head is attached to branch: " + str(current_branch))

            # follow current branch's handle to get a snapid of repo head.
            current_head = main_refs_doc[current_branch]

            # new branch points where head was at the time of its creation. leave previous branch pointer
            # pointing to whatever it was pointing to.
            main_refs_doc[new_branch_name] = current_head


        elif main_refs_doc['head']['state'] == HeadState.DETACHED:
            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            log.uvsmgr("Repo is in detached head state.")

            # in git if head is detached. and you create a new branch (git branch my_branch)
            # my_branch will point to head whatever it is right now. but head will not re-attach.
            # to re-attach head you would run: $ git checkout my_branch
            # In a sense head simply means the current checked out commit. creating a branch does not re-attach
            # anything, check out a branch and head will re-attach.
            main_refs_doc[new_branch_name] = main_refs_doc['head']['snapid']


        if set_current_branch:
            main_refs_doc['head']['state'] = HeadState.ATTACHED
            main_refs_doc['head']['snapid'] = None
            main_refs_doc['head']['branch_handle'] = new_branch_name

        # save the main refs
        new_main_refs_serialized = json.dumps(main_refs_doc, ensure_ascii=True, sort_keys=True)

        #log.uvsmgrv("type(new_main_refs_serialized): " + str(type(new_main_refs_serialized)))

        new_main_refs_ct = self._crypt_helper.encrypt_bytes(new_main_refs_serialized)

        self._dao.update_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME, ref_doc=new_main_refs_ct)

        result['op_failed'] = False
        return result

    def get_commit_detail(self, snapid):
        """ Given a snapid, return its details. Exception if snapid not found.
        """

        assert self._dao is not None
        assert self._crypt_helper is not None

        log.uvsmgr("get_commit_detail_for_snapid() called. snapid: " + str(snapid))

        result = {}

        snapinfo_ct = self._dao.get_snapshot(snapid)

        if snapinfo_ct is None:
            raise UVSError("No such commit found, commit id: " + str(snapid))

        snapinfo_serial = self._crypt_helper.decrypt_bytes(ct=snapinfo_ct)

        log.uvsmgr("snapshot decrypted: " + str(snapinfo_serial))

        snapinfo = json.loads(snapinfo_serial)

        result['commit_id'] = snapid
        result['msg'] = snapinfo['msg']
        result['author_name'] = snapinfo['author_name']
        result['author_email'] = snapinfo['author_email']

        return result


    def list_all_refs(self):
        """ Compute and return of all refs in this repository.
        this list includes head, branches.
        TODO in the future when tags are supported add that in as well.

        """

        assert self._dao is not None
        assert self._crypt_helper is not None


        log.uvsmgr("list_all_refs() called.")

        result = {}

        # get the refs doc.
        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is None) or ('head' not in main_refs_doc):
            raise UVSError('Cant find head. Is this a uvs repo, path: ' + str(self._repo_root_path))

        assert main_refs_doc['head'].has_key('state')
        assert main_refs_doc['head'].has_key('snapid')
        assert main_refs_doc['head'].has_key('branch_handle')

        result['refs'] = {}
        result['commit_msgs'] = {}


        # add all branch names
        for branch_name, branch_snapid in main_refs_doc.items():
            if "head" != branch_name:
                result['refs'][branch_name] = branch_snapid

                branch_snapinfo = self.get_snapinfo_for_snapid(snapid=branch_snapid)

                vldserv.check_snapinfo_dict(snapinfo=branch_snapinfo)

                result['commit_msgs'][branch_name] = branch_snapinfo['msg']



        # add head, (dont de-reference head handle, let head just say master if its attached to master.)
        if main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            current_branch = main_refs_doc['head']['branch_handle']
            log.uvsmgrv("Head is attached to branch: " + str(current_branch))

            # assert that current branch name actually is the branch name of a valid branch.
            assert main_refs_doc.has_key(current_branch)

            result['refs']['head'] = current_branch


        elif main_refs_doc['head']['state'] == HeadState.DETACHED:
            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            log.uvsmgrv("Repo is in detached head state.")

            head_snapid = main_refs_doc['head']['snapid']

            result['refs']['head'] = head_snapid

            head_snapinfo = self.get_snapinfo_for_snapid(snapid=head_snapid)

            vldserv.check_snapinfo_dict(snapinfo=head_snapinfo)

            result['commit_msgs']['head'] = head_snapinfo['msg']


        return result


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

            log.uvsmgrv("snapshot: " + str(result_row))
            result_snapshots.append(result_row)

        return result_snapshots

    def list_reachable_snapshots_for_custom_snapid(self, start_snapid):

        # TODO model this after list all snapshots, bfs visit, to get all snapshots
        # that are reachable from head

        assert self._dao is not None
        assert self._crypt_helper is not None

        log.uvsmgr("list_reachable_snapshots_for_custom_snapid() called. search start snapid: " + str(start_snapid))

        result = {}

        dag = graph_util.DAG(self.get_history_dag()['dag_adjacencies'])

        bfs_order_reachable_nodes = graph_util.get_list_of_bfs_order_nodes(dag=dag, start=start_snapid)


        result['snapshots'] = []

        for next_snapid in bfs_order_reachable_nodes:

            snapinfo_ct = self._dao.get_snapshot(next_snapid)

            assert snapinfo_ct is not None

            snapinfo_serial = self._crypt_helper.decrypt_bytes(ct=snapinfo_ct)

            log.uvsmgr("snapshot decrypted: " + str(snapinfo_serial))

            snapinfo = json.loads(snapinfo_serial)

            log_record = [next_snapid, snapinfo['msg'], snapinfo['author_name'], snapinfo['author_email']]

            result['snapshots'].append(log_record)

        return result



    def list_reachable_snapshots_from_head(self):
        """ Compute and return the list of snapshots that are reachable from head.

        the return is a result dict.
        the result has 'op_failed' and 'op_failed_desc' keys for failure
        on success it has:

        result['snapshots'] >>>>> this is a list of tuples like this:
        <snapid, commit msg, author name, author email>

        The list is ordered, first item (0 == idx) is head snapshot,
        then comes snapshots that are one edge removed from head (in bfs order) then 2 edge, and so on.
         """

        assert self._dao is not None
        assert self._crypt_helper is not None

        log.uvsmgr("list_reachable_snapshots_from_head() called.")

        result = {}
        result['op_failed'] = False

        # get the refs doc.
        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is None) or ('head' not in main_refs_doc):
            result['op_failed'] = True
            result['op_failed_desc'] = 'Cant find head. Is this a uvs repo, path: ' + str(self._repo_root_path)
            return result

        assert main_refs_doc['head'].has_key('state')
        assert main_refs_doc['head'].has_key('snapid')
        assert main_refs_doc['head'].has_key('branch_handle')

        # get head snapid
        head_snapid = None

        if main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            current_branch = main_refs_doc['head']['branch_handle']

            log.uvsmgrv("Head is attached to branch: " + str(current_branch))

            # assert that current branch name actually is the branch name of a valid branch.
            assert main_refs_doc.has_key(current_branch)

            head_snapid = main_refs_doc[current_branch]


        elif main_refs_doc['head']['state'] == HeadState.DETACHED:
            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            log.uvsmgrv("Repo is in detached head state.")
            head_snapid = main_refs_doc['head']['snapid']

        # if we didnt fail, let some1 else get the result.
        return  self.list_reachable_snapshots_for_custom_snapid(start_snapid=head_snapid)


    def get_history_dag(self):
        """ Compute and return the history dag (regular dag, kids point to parents).

        If operation fails, the result dict will have 'op_failed' set to True
        if operation succeeds, result['dag_adjacencies'] will have the DAG as an adjacency list.

        dict of <str snapid, [list of neighbors, parents in this case]>
        """

        assert self._dao is not None
        assert self._crypt_helper is not None

        log.uvsmgrv("get_history_dag() called.")

        result = {}

        # dict of <str snapid, [list of neighbors, parents in this case]>
        dag_adjacencies = {}

        snapshots = self._dao.get_all_snapshots()

        if (snapshots is None) or (0 == len(snapshots)):

            log.uvsmgr("No snapshots found in this repo, can't really give you a dag.")
            raise UVSError('there are no commits in this repository')


        for snapid, snapinfo_json_ct in snapshots:

            # if this node has not been seen before, create an empty adj list for it.
            if not dag_adjacencies.has_key(snapid):
                dag_adjacencies[snapid] = []

            snapinfo_json_pt = self._crypt_helper.decrypt_bytes(ct=bytes(snapinfo_json_ct))

            parents = json.loads(snapinfo_json_pt)['parents']

            assert isinstance(parents, list)

            # no parent means, initial commit, 1 parent means regular commit, 2 parents means a merge commit.
            # i dont think we should allow such a thing as a commit with 3 or 4 or 5 parents. If we allowed
            # it there could be massive complications when it comes to finding common ancestor for 3 way merge
            # i can't think of a dvcs operation that requires a commit with more than 2 parents.
            num_parents = len(parents)

            assert num_parents <= 2, "Found a snapshot with more than 2 parents, this should not have happened."

            #
            for parent in parents:
                dag_adjacencies[snapid].append(parent)


        result['dag_adjacencies'] = dag_adjacencies

        return result


    def get_inverted_history_dag(self):
        """ Compute and return the history dag with the parent pointers reversed to kid pointers.

        If operation fails, the result dict will have 'op_failed' set to True
        if operation succeeds, result['dag_root'] will have the snapid of the first commit in the repo (inv dag root)
        result['dag_adjacencies'] will have a set of snapids, that are the kids of that node in the DAG.
        """

        assert self._dao is not None
        assert self._crypt_helper is not None

        log.uvsmgrv("get_inverted_history_dag() called. Computing inverted dag.")

        result = {}


        # lets implement an adjacency list as a dict of < node, [list of neighbors] >
        inverted_dag_adjacencies = {}

        inverted_dag_root_snapid = None

        # get all snapshots. each snapshot should have a pointer to its parent(s).
        # there should only be one snapshot with no parents, that is the initial commit.
        # you can assert that here if u want.

        snapshots = self._dao.get_all_snapshots()

        if (snapshots is None) or (0 == len(snapshots)):

            log.uvsmgr("No snapshots found in this repo, can't really give you an inverted dag.")
            raise UVSError('there are no commits in this repository')


        for snapid, snapinfo_json_ct in snapshots:

            # if this node has not been seen before, create an empty adj list for it.
            if not inverted_dag_adjacencies.has_key(snapid):
                inverted_dag_adjacencies[snapid] = []

            snapinfo_json_pt = self._crypt_helper.decrypt_bytes(ct=bytes(snapinfo_json_ct))

            parents = json.loads(snapinfo_json_pt)['parents']

            assert isinstance(parents, list)

            # no parent means, initial commit, 1 parent means regular commit, 2 parents means a merge commit.
            # i dont think we should allow such a thing as a commit with 3 or 4 or 5 parents. If we allowed
            # it there could be massive complications when it comes to finding common ancestor for 3 way merge
            # i can't think of a dvcs operation that requires a commit with more than 2 parents.
            num_parents = len(parents)

            assert num_parents <= 2, "Found a snapshot with more than 2 parents, this should not have happened."

            # if parent_list is an empty list, this is the initial commit.
            if (0 == num_parents):

                # there should only be one root commit. we must not find more than one snapshot
                # with zero parents
                assert inverted_dag_root_snapid is None

                inverted_dag_root_snapid = snapid

            else:

                # there is at most 2 parents
                for parent in parents:

                    # now we have a inverted pointer from parent (parent) to kid (snapid)
                    # if this node has not been seen before, create an empty adj list for it.
                    if not inverted_dag_adjacencies.has_key(parent):
                        inverted_dag_adjacencies[parent] = []

                    # now there is an adj list for this node, either empty just created or existing one from
                    # another snapshot. either case just add a pointer to the kid. (note a node can have many kids)
                    inverted_dag_adjacencies[parent].append(snapid)


        # now we have root of the inverted DAG and the adj list
        result['dag_root'] = inverted_dag_root_snapid
        result['dag_adjacencies'] = inverted_dag_adjacencies

        return result


    def merge(self, mrg_src_branch):
        """ Merge changes from the supplied branch name to current branch """

        # the user ran something like:
        # $ uvs merge -n br2
        # meaning we want to merge the changes from br2 to current branch

        assert self._dao is not None
        assert self._crypt_helper is not None
        assert self._repo_root_path is not None

        assert isinstance(mrg_src_branch, str) or isinstance(mrg_src_branch, unicode)

        log.uvsmgr("merge() called.")

        result = {}

        # first we need to know current branch. fetch the main refs doc.
        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is None) or ('head' not in main_refs_doc):
            raise UVSError('Cant find head. Is this a uvs repo, path: ' + str(self._repo_root_path))

        if mrg_src_branch not in main_refs_doc:
            raise UVSError("Merge failed. Can't find merge src branch: " + str(mrg_src_branch))

        assert main_refs_doc['head'].has_key('state')
        assert main_refs_doc['head'].has_key('snapid')
        assert main_refs_doc['head'].has_key('branch_handle')


        # merge source is the supplied argument,
        # merge destination will be current branch.
        # at the moment and maybe later as well, we dont support merging to a destination of detached head.
        # TODO: study git behaviour on this, should we allow merges to detached head,
        # and if so what should we do in that case

        # this is current branch, after this operation head should point to this.
        mrg_dst_branch_aka_curr_br = None

        if main_refs_doc['head']['state'] == HeadState.DETACHED:

            assert main_refs_doc['head']['snapid'] is not None
            assert main_refs_doc['head']['branch_handle'] is None

            raise UVSError("Merging to a detached head is un-supported. Switch to a branch u wish to merge into first.")


        elif main_refs_doc['head']['state'] == HeadState.ATTACHED:
            assert main_refs_doc['head']['snapid'] is None
            assert main_refs_doc['head']['branch_handle'] is not None

            # follow current branch's handle to get a snapid of repo head.
            mrg_dst_branch_aka_curr_br = main_refs_doc['head']['branch_handle']
            assert mrg_dst_branch_aka_curr_br in main_refs_doc


        # corner case1: what if user is on master branch and tried to merge master into master.
        # return some kinda error
        if mrg_src_branch == mrg_dst_branch_aka_curr_br:
            raise UVSError("Can't merge a branch into itself.")


        dag = graph_util.DAG(graph_adjacencies=self.get_history_dag()['dag_adjacencies'])
        inv_dag = graph_util.DAG(graph_adjacencies=self.get_inverted_history_dag()['dag_adjacencies'])

        # ok now we have, inv dag, we got, merge src and merge dst, several possibilities arise for merge.
        # *** scenario 1: merge src, is an ancestor of merge dest.
        #             In this case nothing to do, git prints "Already up-to-date."


        case_1_temp = graph_util.inv_dag_is_descendant_of(invdag=inv_dag, parent=main_refs_doc[mrg_src_branch],
                                            node_to_test=main_refs_doc[mrg_dst_branch_aka_curr_br])

        if case_1_temp:
            result['merge_msg'] = "Already up-to-date."
            return result


        # *** scenario 2: merge dest, is an ancestor of merge src.
        #             In this case just fast forward, meaning set the mrg_dst pointer to point to mrg_src

        case_2_temp = graph_util.inv_dag_is_descendant_of(invdag=inv_dag,
                                                          parent=main_refs_doc[mrg_dst_branch_aka_curr_br],
                                                          node_to_test=main_refs_doc[mrg_src_branch])

        if case_2_temp:

            main_refs_doc['head']['state'] = HeadState.ATTACHED
            main_refs_doc['head']['snapid'] = None
            main_refs_doc['head']['branch_handle'] = mrg_dst_branch_aka_curr_br
            main_refs_doc[mrg_dst_branch_aka_curr_br] = main_refs_doc[mrg_src_branch]

            # now save the new main refs
            new_main_refs_serialized = json.dumps(main_refs_doc, ensure_ascii=True, sort_keys=True)
            new_main_refs_ct = self._crypt_helper.encrypt_bytes(new_main_refs_serialized)
            self._dao.update_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME, ref_doc=new_main_refs_ct)


            result['merge_msg'] = "Fast Forwarded.\nupdating " + str(mrg_dst_branch_aka_curr_br) + \
                                  " to point to " + str(mrg_src_branch) + "\nThey are now both at commit: " + \
                                  str(main_refs_doc[mrg_src_branch])
            return result

        # *** scenario 3: same as 2 but with -no-ff option set.
        #             >> In this case create a new snapshot, with 2 parents, mrg src and dst.
        #             >> use the repo root tree id of mrg_src for the new snapshot.

        # maybe skip this case for now.


        # *** scenario 4: merge dest, is sibling (or cousin or ... just not ancestor/desc) of merge src,
        #             In this case:
        #                          >> check out merge src to '.uvs_temp/mrg_src'
        #                          >> check out merge dst to '.uvs_temp/mrg_dst'
        #                          >> find and check out the common ancestor to '.uvs_temp/ca'


        log.vvvv("merge case4. nodes are not each others ancestor/descendant .")

        # if none of case1 or case2 happened mrg_dst and mrg_src must be siblings.

        # use graph util. we have src and dst snapid, get the ca snapid

        s1_snapid = main_refs_doc[mrg_dst_branch_aka_curr_br]
        s2_snapid = main_refs_doc[mrg_src_branch]

        eca_set = graph_util.dag_find_eca_three_color(dag=dag, node_1=s1_snapid, node_2=s2_snapid)

        log.vvvv("repr(eca_set): " + repr(eca_set))

        ca_snapid = eca_set.pop()
        # now we have all 3 snapids, fetch their snapinfos, deserialize and decrypt them all.

        s1_snapinfo_ct = self._dao.get_snapshot(snapid=s1_snapid)
        s2_snapinfo_ct = self._dao.get_snapshot(snapid=s2_snapid)
        ca_snapinfo_ct = self._dao.get_snapshot(snapid=ca_snapid)

        if s1_snapinfo_ct is None:
            raise UVSError("Could not find snapshot with id: " + str(s1_snapinfo_ct))

        if s2_snapinfo_ct is None:
            raise UVSError("Could not find snapshot with id: " + str(s2_snapinfo_ct))

        if ca_snapinfo_ct is None:
            raise UVSError("Could not find snapshot with id: " + str(ca_snapinfo_ct))

        # got snapinfo now decrypt them
        s1_snapinfo_serial = self._crypt_helper.decrypt_bytes(ct=s1_snapinfo_ct)
        s2_snapinfo_serial = self._crypt_helper.decrypt_bytes(ct=s2_snapinfo_ct)
        ca_snapinfo_serial = self._crypt_helper.decrypt_bytes(ct=ca_snapinfo_ct)

        log.uvsmgr("s1 decrypted: " + str(s1_snapinfo_serial))
        log.uvsmgr("s2 decrypted: " + str(s2_snapinfo_serial))
        log.uvsmgr("ca decrypted: " + str(ca_snapinfo_serial))

        # now deserialize them
        s1_snapinfo = json.loads(s1_snapinfo_serial)
        s2_snapinfo = json.loads(s2_snapinfo_serial)
        ca_snapinfo = json.loads(ca_snapinfo_serial)

        s1_root_treeid = s1_snapinfo['root']
        s2_root_treeid = s2_snapinfo['root']
        ca_root_treeid = ca_snapinfo['root']


        log.uvsmgrv("s1 root tree id is: " + str(s1_root_treeid))
        log.uvsmgrv("s2 root tree id is: " + str(s2_root_treeid))
        log.uvsmgrv("ca root tree id is: " + str(ca_root_treeid))

        # now we got 3 tree ids. get the temp dir paths for where these 3 tree ids should be checked out to.

        merge_temp_dirpath = os.path.join(self._repo_root_path, sdef.TEMP_DIR_NAME)

        merge_s1_dirpath = os.path.join(merge_temp_dirpath, mrg_dst_branch_aka_curr_br)
        merge_s2_dirpath = os.path.join(merge_temp_dirpath, mrg_src_branch)
        merge_ca_dirpath = os.path.join(merge_temp_dirpath, UVSConst.AMS_CA_FOLDER_NAME)

        # TODO the above line means that we must disallow the user from creating a branch called, common_ancestor.
        # in create branch fail with error that says that name is reserved try something else for new branch name.


        # TODO move this name to init, and set it to a constant.
        merge_result_dirpath = os.path.join(merge_temp_dirpath, UVSConst.AMS_MERGE_RESULT_FOLDER_NAME)

        if not os.path.exists(merge_s1_dirpath):
            os.makedirs(merge_s1_dirpath)

        if not os.path.exists(merge_s2_dirpath):
            os.makedirs(merge_s2_dirpath)

        if not os.path.exists(merge_ca_dirpath):
            os.makedirs(merge_ca_dirpath)

        if not os.path.exists(merge_result_dirpath):
            os.makedirs(merge_result_dirpath)

        # now we got 3 tree ids and the respective temp dirs.
        self._recursively_checkout_tree(tid=s1_root_treeid, dest_dir_path=merge_s1_dirpath)
        self._recursively_checkout_tree(tid=s2_root_treeid, dest_dir_path=merge_s2_dirpath)
        self._recursively_checkout_tree(tid=ca_root_treeid, dest_dir_path=merge_ca_dirpath)

        # now call auto merge service
        ams_result = automergeservice.auto_merge3(base_dirpath=merge_ca_dirpath, a_dirpath=merge_s1_dirpath,
                                                       b_dirpath=merge_s2_dirpath, out_dirpath= merge_result_dirpath)

        if ams_result['hard_conflicts_found']:

            result['merge_msg'] = ("conflicts found that require manual resolution. \nyour merge results along " +
                                   "with conflict markers are under: " + str(merge_result_dirpath) +
                                   "\nresolve these and make sure that folder has the final version " +
                                   "that you want. \n" +
                                   "then run the merge-finalize command to commit the merge.")
        else:
            # result['op_failed'] = False
            result['merge_msg'] = ("\nSuccessfully merged your files using the 3 way merge algorithm.\n" +
                                   "There are no conflicts that need manual resolution.\nHowever this does not mean " +
                                   "that the merge result is necessarily what you want. \nIt is possible that two " +
                                   "perfectly bug-free branches get merged,\nand the 3 way merge algorithm introduces " +
                                   "a bug \nthat did not exist in any of the two branches involved in the merge. \n" +
                                   "This is true of all 3 way merging programs or dvcs including git. \n" +
                                   "Such situations arise when the two branches have overlapping side effects,\n" +
                                   "but have only changed lines from well-separated parts of your source. \n" +
                                   "check your merge results under: " + str(merge_result_dirpath) +
                                   "\nconfirm that this is what you want. " +
                                   "then run the merge-finalize command to commit the merge.")



        # save ongoing merge state to a temp location for merge finalize command.
        ongoing_merge = {}
        ongoing_merge['mrg_parent1_snapid'] = s1_snapid
        ongoing_merge['mrg_parent2_snapid'] = s2_snapid
        ongoing_merge['mrg_src_branch'] = mrg_src_branch
        ongoing_merge['mrg_dst_branch_aka_curr_br'] = mrg_dst_branch_aka_curr_br

        # serialize and save.
        ongoing_merge_serialized = json.dumps(ongoing_merge, ensure_ascii=True, sort_keys=True, indent=4)

        ongoing_merge_filepath = os.path.join(merge_temp_dirpath, UVSConst.AMS_ONGOING_MERGE_TEMP_FILENAME)

        # get a file handle in write mode.
        ongoing_merge_fhandle = open(ongoing_merge_filepath, 'wb')

        ongoing_merge_fhandle.write(ongoing_merge_serialized)

        return result


    def finalize_merge(self, snapshot_msg, author_name, author_email):
        """ Finalize an ongoing merge.  """


        # for this function we do this:
        # recover the merge json saved somewhere.


        # clear repo root (except uvs internals) (refactor this to a private helper if needed)
        # copy the contents of merge_result to repo root.
        # delete uvs_temp folder
        # call take snapshot with snap msg and so on.
        # also pass in the merge parents to the take snapshot (will require refactoring, to use these)
        # return its return value and modify the UI caller to read and print those


        merge_temp_dirpath = os.path.join(self._repo_root_path, sdef.TEMP_DIR_NAME)

        ongoing_merge_filepath = os.path.join(merge_temp_dirpath, UVSConst.AMS_ONGOING_MERGE_TEMP_FILENAME)

        if not os.path.isdir(merge_temp_dirpath):
            raise UVSError("There is no ongoing merge directory to finalize.")

        if not os.path.isfile(ongoing_merge_filepath):
            raise UVSError("There is no ongoing merge to finalize.")

        # get a file handle in read mode and read it.
        ongoing_merge_serialized = open(ongoing_merge_filepath, 'rb').read()

        ongoing_merge = json.loads(ongoing_merge_serialized)


        log.vvvv("clearing repo root.\n")

        # clear repo root (except uvs internals)
        self.clear_directory_keep_uvs_internals(dest_dirpath=self._repo_root_path)

        # now copy the contents of merge_result to repo root.
        merge_result_dirpath = os.path.join(merge_temp_dirpath, UVSConst.AMS_MERGE_RESULT_FOLDER_NAME)



        from distutils.dir_util import copy_tree

        copy_tree(merge_result_dirpath, self._repo_root_path)

        try:
            shutil.rmtree(merge_temp_dirpath, ignore_errors=True)
        except:
            # TODO, deal with this.
            pass

        merge_parents = []
        merge_parents.append(ongoing_merge['mrg_parent1_snapid'])
        merge_parents.append(ongoing_merge['mrg_parent2_snapid'])

        return self.take_snapshot(snapshot_msg=snapshot_msg, author_name=author_name, author_email=author_email,
                                  explicit_parents_for_merge_commit=merge_parents)




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
            raise UVSError("No such file exists with file id: " + str(fid))

        finfo_serial = self._crypt_helper.decrypt_bytes(ct=finfo_ct)

        log.uvsmgr("finfo decrypted: " + str(finfo_serial))

        finfo = json.loads(finfo_serial)

        # TODO get rid of these stupid verify_fids, its so ugly. we need a proper AEAD crypto module Fernet sucks.
        # by not allowing us to supply associated data to be included into the tag.
        if ('segments' not in finfo) or ('verify_fid' not in finfo):
            raise UVSError("invalid finfo, json does not contain all expected keys.")

        if fid != finfo['verify_fid']:
            raise UVSError("Tamper detected, fid does not match verify fid.")

        # next open a file with temporary filename. write segments into it.
        temp_pathname = rand_util.choose_unique_random_file(dest_directory=dest_dir_path)

        # open the file in binary mode to write to.
        fhandle = open(temp_pathname, "wb")

        for sgid, offset in finfo['segments']:
            log.uvsmgr(">>> (sgid, offset): " + str(sgid) + ", " + str(offset))

            segment_ct = self._dao.get_segment(sgid)

            if segment_ct is None:
                # TODO close and remove that file we opened.
                raise UVSError("No such segment exists with sgid:" + str(sgid))

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

        assert self._dao is not None
        assert self._crypt_helper is not None


        tree_info_ct = self._dao.get_tree(tid)

        if tree_info_ct is None:
            raise UVSError("No such tree exists, tree_id: " + str(tid) )

        tree_info_serial = self._crypt_helper.decrypt_bytes(ct=tree_info_ct)

        log.uvsmgrv("tree info cipher text: " + str(tree_info_ct))
        log.uvsmgr("tree info decrypted: " + str(tree_info_serial))

        tree_info = json.loads(tree_info_serial)

        if ('fids' not in tree_info) or ('tids' not in tree_info):
            raise UVSError("invalid treeinfo, json does not contain all expected keys.")

        for fname, fid in tree_info['fids']:
            log.uvsmgrv("fname: " + str(fname) + " fid: " + str(fid))
            self._checkout_file(fname=fname, fid=fid, dest_dir_path=dest_dir_path)

        for tree_name, tree_id in tree_info['tids']:

            log.uvsmgrv("tree_name: " + str(tree_name) + " tree_id: " + str(tree_id))

            # mkdir for tree name. add it to dest path and checkout the tid into it.
            new_tree_path = os.path.join(dest_dir_path, tree_name)
            os.mkdir(new_tree_path)
            self._recursively_checkout_tree(tid=tree_id, dest_dir_path=new_tree_path)


    # TODO add support here to check out tags as well branch names.
    # that is after adding tags to uvs
    def checkout_reference_at_repo_root(self, snapshot_ref, clear_dest=True):
        """
         Given a valid reference (snapshot id or branch name) check out the given reference
         set the contents of the repository root to whatever that snapshot has.

         if clear_dest is set, all files at the repo root (except uvs internal files) will be replaced, even those
         not under version control (i.e. uvsignore files). Otherwise only files that exist in the snapshot will
         be overwritten and restored to what they were at the time the snapshot was taken.


        :param snapshot_ref: an snapshot reference. either a snapshot id (checked first) or branch name.
        :param clear_dest:
        :return:
        """


        assert self._dao is not None
        assert self._crypt_helper is not None
        assert self._repo_root_path is not None


        assert clear_dest is not None
        assert isinstance(clear_dest, bool)

        assert snapshot_ref is not None
        assert isinstance(snapshot_ref, str) or isinstance(snapshot_ref, unicode)

        assert os.path.isdir(self._repo_root_path)

        log.uvsmgr("Checking out to repo root. Check out reference is:" + str(snapshot_ref))

        result = {}

        main_refs_doc_ct = self._dao.get_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME)

        main_refs_doc_serial = self._crypt_helper.decrypt_bytes(main_refs_doc_ct)

        main_refs_doc = json.loads(main_refs_doc_serial)

        if (main_refs_doc is  None):
            result['op_failed'] = True
            result['op_failed_desc'] = 'Cant find head. Is this a uvs repo, path: ' + str(self._repo_root_path)
            return result

        # First see if this snapshot_ref is a snapshot id
        # get the snapshot, if we got something other than none, then snapshot does exist.
        if self._dao.get_snapshot(snapid=snapshot_ref) is not None:

            # if snapshot_ref was a key in the snapshots table, this is a snapid (commit id)
            self.checkout_snapshot_bare(snapid=snapshot_ref, dest_dirpath=self._repo_root_path, clear_dest=clear_dest)

            # the user just did a checkout with a commit id, head should be detached.
            assert main_refs_doc.has_key('head')

            main_refs_doc['head']['state'] = HeadState.DETACHED
            main_refs_doc['head']['snapid'] = snapshot_ref
            main_refs_doc['head']['branch_handle'] = None

            result['op_failed'] = False
            result['detached_head'] = True


        # next handle snapshot_ref == 'head' or 'Head' or 'HEAD' separately,
        # the user could have said, uvs checkout head hoping to  discard his changes and check out last commit.
        # in git however this action would require -f option, for example if status says we have some changes
        # that we want to discard, one could say
        # $ git checkout -f HEAD
        # its sorta equivalent to saying $ git stash + $ git stash drop
        elif 'head' == snapshot_ref.lower():

            # get head snap id, direct or indirect
            current_head_snapid = None

            if main_refs_doc['head']['state'] == HeadState.ATTACHED:
                assert main_refs_doc['head']['snapid'] is None
                assert main_refs_doc['head']['branch_handle'] is not None

                # follow current branch's handle to get a snapid of repo head.
                current_branch = main_refs_doc['head']['branch_handle']
                current_head_snapid = main_refs_doc[current_branch]

                result['detached_head'] = False
                result['head_attached_to'] = current_branch

            elif main_refs_doc['head']['state'] == HeadState.DETACHED:
                assert main_refs_doc['head']['snapid'] is not None
                assert main_refs_doc['head']['branch_handle'] is None

                current_head_snapid = main_refs_doc['head']['snapid']
                result['detached_head'] = True


            self.checkout_snapshot_bare(snapid=current_head_snapid, dest_dirpath=self._repo_root_path,
                                        clear_dest=clear_dest)

            result['op_failed'] = False
            # head did not change in this case, if it was detached it should still be detached, if it was
            # attached to a branch (say master) it should still be attached to it.
            # not sure if we need tp tell user something like, you are still detached, or you are still on master
            # but included in result anyway.

        elif snapshot_ref in main_refs_doc:
            self.checkout_snapshot_bare(snapid=main_refs_doc[snapshot_ref], dest_dirpath=self._repo_root_path,
                                        clear_dest=clear_dest)

            # now update references.
            # the user just did a checkout with a ref (like master), head should be attached to master now.
            main_refs_doc['head']['state'] = HeadState.ATTACHED
            main_refs_doc['head']['snapid'] = None
            main_refs_doc['head']['branch_handle'] = snapshot_ref

            result['op_failed'] = False
            result['detached_head'] = False
            result['head_attached_to'] = snapshot_ref

        elif False:
            pass
            # TODO maybe also check to see if there is a tag with this reference. (later when we add tags)

        else:
            result['op_failed'] = True
            result['op_failed_desc'] = "Invalid reference: " + str(snapshot_ref)
            return result


        # now save the main refs
        new_main_refs_serialized = json.dumps(main_refs_doc, ensure_ascii=True, sort_keys=True)
        new_main_refs_ct = self._crypt_helper.encrypt_bytes(new_main_refs_serialized)
        self._dao.update_ref_doc(ref_doc_id=_MAIN_REF_DOC_NAME, ref_doc=new_main_refs_ct)

        return result


    def clear_directory_keep_uvs_internals(self, dest_dirpath):
        """ Delete everything at the supplied dirpath except uvs internal directories/files .
        """

        if not os.path.isdir(dest_dirpath):
            raise UVSError("Invalid destination directory.")

        # TODO: i think we should not remove files that are not version controlled.
        # study git's behavior on this.

        dest_members = os.listdir(dest_dirpath)
        log.uvsmgr("clearing destination directory: all destination members: " + repr(dest_members))

        actual_paths_to_remove = []

        dont_remove = set()
        dont_remove.add(sdef.TEMP_DIR_NAME)
        dont_remove.add(sdef.SHADOW_FOLDER_NAME)
        dont_remove.add(sdef.SHADOW_DB_FILE_NAME)

        for dest_member in dest_members:
            if dest_member not in dont_remove:
                actual_paths_to_remove.append(os.path.join(dest_dirpath, dest_member))


        log.uvsmgr("clearing destination directory: dest members to be removed: " + repr(actual_paths_to_remove))

        for path in actual_paths_to_remove:
            if os.path.isdir(path):
                # TODO: perhaps write a manual directory remover that uses os.walk to traverse and
                # delete a directory similar to rmtree, but skip if we found uvs_shadow down the tree.
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)


    def checkout_snapshot_bare(self, snapid, dest_dirpath, clear_dest=True):
        """ Given a valid snapshot id, set the content of the directory identified by dest_dirpath to the
        image of the repository at the time this snapshot id was taken.

        By default it will just overwrite the files that collide with this checkout. if clear_dest is set
        to True it will delete everything at destination except uvs internal files/folders.

        this is the bare version of checkout. It will just write the snapshot to destination, without updating
        any references i.e. changing head or anything else. As far repository history and internal data structures
        are concerned this is a nullipotent operation.
        """

        assert self._dao is not None
        assert self._crypt_helper is not None

        assert clear_dest is not None
        assert isinstance(clear_dest, bool)

        snapid = vldserv.check_snapid_and_get_std(snapid=snapid)

        assert dest_dirpath is not None
        assert isinstance(dest_dirpath, str) or isinstance(snapid, unicode)


        log.uvsmgr("bare checking out, snapshot id: " + str(snapid) + "\nTo directory at: " + str(dest_dirpath))


        # TODO if path does not exist try to create it  ignoring all errors

        # now check again to see if it does exist or not. if still does not exist, i cant proceed. error

        if clear_dest:
            self.clear_directory_keep_uvs_internals(dest_dirpath=dest_dirpath)


        # To checkout, get the snapshot, find the root tree id. (raise error if decryption fails, or mac failed.)
        # checkout tree recursive function:
        #    assemble the files of this tree, write to disk. (raise error if any objects did decrypt or pass mac)
        #    call itself recursively on subdirs.
        snapshot_info_ct = self._dao.get_snapshot(snapid=snapid)

        if snapshot_info_ct is None:
            raise UVSError("Could not find an snapshot with id: " + str(snapid))

        snapshot_info_serial = self._crypt_helper.decrypt_bytes(ct=snapshot_info_ct)

        log.uvsmgr("snapshot decrypted: " + str(snapshot_info_serial))

        snapshot_info = json.loads(snapshot_info_serial)

        vldserv.check_snapinfo_dict(snapinfo=snapshot_info)

        # TODO this should be MAC failed
        # if snapid != snapshot_info['verify_snapid']:
        #    raise UVSError('Detected data structure tampering. Perhaps some1 tried to reorder snapshots')


        snapshot_root_tid = snapshot_info['root']

        log.uvsmgrv("snapshot root tid is: " + str(snapshot_root_tid))

        self._recursively_checkout_tree(tid=snapshot_root_tid, dest_dir_path=dest_dirpath)


    def get_snapinfo_for_snapid(self, snapid):
        """ Given a snapid, return the snapinfo dict containing information such as root tree id, commit msg,
        time, author etc etc.

        returns none, if snapshot with that id does not exist.
        """

        assert self._dao is not None
        assert self._crypt_helper is not None

        snapid = vldserv.check_snapid_and_get_std(snapid=snapid)

        snapshot_info_ct = self._dao.get_snapshot(snapid=snapid)

        if snapshot_info_ct is None:
            return None

        snapshot_info_serial = self._crypt_helper.decrypt_bytes(ct=snapshot_info_ct)

        snapshot_info = json.loads(snapshot_info_serial)

        vldserv.check_snapinfo_dict(snapinfo=snapshot_info)

        return snapshot_info







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
