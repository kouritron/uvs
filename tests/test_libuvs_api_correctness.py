


import os
import sys
import  shutil

# if you got module not found errors, uncomment these. PyCharm IDE does not need it.
# get the abs version of . and .. and append them to this process's path.
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('.'))

#print sys.path

import unittest
import subprocess

import testutils as tu
import libuvs.systemdefaults as sdef
from libuvs import uvsmanager


class TestUVS(unittest.TestCase):


    repo_root_path = None
    repo_root_cksums_file = None

    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestUVS, cls).setUpClass()

        cwd = os.getcwd()
        print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> setUpClass() called from cwd: " + str(cwd)


        tests_folder_abs_path = os.path.dirname(tu.find_file_within_this_project('test_libuvs_api_correctness.py'))

        print "Found tests directory path to be: " + str(tests_folder_abs_path)

        cls.repo_root_path = os.path.join(tests_folder_abs_path, 'ignoreme')
        cls.repo_root_cksums_file = os.path.join(tests_folder_abs_path, "ignoreme_md5sums")

        print "repo root path: " + cls.repo_root_path
        print "repo root cksums file: " + cls.repo_root_cksums_file

        # delete previous test repo if it existed.
        cls.remove_test_repo()

        print "creating test uvs repo at: " + cls.repo_root_path

        # make and populate the repo root ith some random dirs and files to
        # be treated as a test uvs repository.
        # tu.populate_directory_with_random_files_and_subdirs(dirpath=cls.repo_root_path)
        tu.populate_directory_with_random_files_and_subdirs(dirpath=cls.repo_root_path)


        # now save md5 of what we created.
        cmd = "find " + cls.repo_root_path
        cmd += " -type f -print0 | xargs -0 md5sum > " + cls.repo_root_cksums_file
        subprocess.call(cmd, shell=True)

    @classmethod
    def tearDownClass(cls):
        super(TestUVS, cls).tearDownClass()
        print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> tearDownClass() called"

        #cls.remove_test_repo()


    @classmethod
    def remove_test_repo(cls):
        """ Delete all files set up for test repo. """

        print "remove_test_repo() called, deleting everything that was set up for test repo"

        try:
            shutil.rmtree(cls.repo_root_path)
        except:
            print "could not delete repo root path, skipping."

        try:
            os.remove(cls.repo_root_cksums_file)
        except:
            print "could not delete repo root cksum file, skipping."


    @classmethod
    def empty_test_repo(cls):
        """ Clear the test repo, that is delete the checked out copy, but not delete the uvs internal files. """

        print "empty_test_repo() called, emptying the checked out files at test repo, but not uvs internals."

        #  delete everything at repo_root_path except uvs internal files.
        repo_root_members = os.listdir(cls.repo_root_path)

        paths_to_remove = []

        dont_remove = set()
        dont_remove.add(sdef.TEMP_DIR_NAME)
        dont_remove.add(sdef.SHADOW_FOLDER_NAME)
        dont_remove.add(sdef.SHADOW_DB_FILE_NAME)

        for repo_root_member in repo_root_members:
            if repo_root_member not in dont_remove:
                paths_to_remove.append(os.path.join(cls.repo_root_path, repo_root_member))

        for path in paths_to_remove:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)



    # setUp will run once before every test case
    def setUp(self):
        pass


    # tearDown will run once after every test case
    def tearDown(self):
        pass


    def test_compute_directory_tree_id_has_no_side_effects(self):

        test_pass = "123"
        # ---------------- init uvs repo on   self.repo_root_path
        uvsmanager.init_new_uvs_repo_overwrite(repo_pass=test_pass, repo_root_path=self.repo_root_path)

        # ---------------- make a commit
        uvsmgr = uvsmanager.UVSManager(repo_pass=test_pass, repo_root_path=self.repo_root_path)
        uvsmgr.take_snapshot(snapshot_msg='test commit', author_name="n/a", author_email="n/a")

        # get md5 of 'uvs.db' file inside the shadow.
        shadow_file_path = os.path.join(self.repo_root_path, sdef.SHADOW_FOLDER_NAME, sdef.SHADOW_DB_FILE_NAME)
        print "shadow_file_path is: " + shadow_file_path

        shadow_file_hash_before_compute_tree_id = tu.get_file_hash(shadow_file_path)
        print "shadow_file_hash_before_compute_tree_id is: " + shadow_file_hash_before_compute_tree_id

        # ---------------- compute some tree id multiple times.
        uvsmgr.compute_repo_root_tree_id()
        uvsmgr.compute_repo_root_tree_id()
        uvsmgr.compute_repo_root_tree_id()

        # check that compute tree id had no side effects on 'uvs.db'
        self.assertEquals(shadow_file_hash_before_compute_tree_id, tu.get_file_hash(shadow_file_path))

        skip_paths = set()
        skip_paths.add(sdef.TEMP_DIR_NAME)
        skip_paths.add(sdef.SHADOW_FOLDER_NAME)
        skip_paths.add(sdef.SHADOW_DB_FILE_NAME)

        repo_root_members = os.listdir(self.repo_root_path)
        for repo_root_member in repo_root_members:

            if repo_root_member in skip_paths:
                continue

            repo_root_member_path = os.path.join(self.repo_root_path, repo_root_member)

            if os.path.isdir(repo_root_member_path):
                uvsmgr.compute_tree_id_for_directory(repo_root_member_path)
                uvsmgr.compute_tree_id_for_directory(repo_root_member_path)
                uvsmgr.compute_tree_id_for_directory(repo_root_member_path)


        # check again that no side effects have occurred on 'uvs.db'
        self.assertEquals(shadow_file_hash_before_compute_tree_id, tu.get_file_hash(shadow_file_path))


    def test_compute_directory_tree_id_is_deterministic(self):

        test_pass = "123"
        # ---------------- init uvs repo on   self.repo_root_path
        uvsmanager.init_new_uvs_repo_overwrite(repo_pass=test_pass, repo_root_path=self.repo_root_path)

        # ---------------- make a commit
        uvsmgr = uvsmanager.UVSManager(repo_pass=test_pass, repo_root_path=self.repo_root_path)
        snapid = uvsmgr.take_snapshot(snapshot_msg='test commit', author_name="n/a", author_email="n/a")

        # ----------------
        root_tid_1 = uvsmgr.compute_repo_root_tree_id()
        root_tid_2 = uvsmgr.compute_repo_root_tree_id()
        root_tid_3 = uvsmgr.compute_repo_root_tree_id()

        print "repo root tid_1: " + str(root_tid_1)
        print "repo root tid_2: " + str(root_tid_2)
        print "repo root tid_3: " + str(root_tid_3)

        # check that every time we got the same thing.
        self.assertEquals(root_tid_1, root_tid_2)
        self.assertEquals(root_tid_2, root_tid_3)

        skip_paths = set()
        skip_paths.add(sdef.TEMP_DIR_NAME)
        skip_paths.add(sdef.SHADOW_FOLDER_NAME)
        skip_paths.add(sdef.SHADOW_DB_FILE_NAME)

        repo_root_members = os.listdir(self.repo_root_path)
        for repo_root_member in repo_root_members:

            if repo_root_member in skip_paths:
                continue

            repo_root_member_path = os.path.join(self.repo_root_path, repo_root_member)

            if os.path.isdir(repo_root_member_path):

                tree_id_1 = uvsmgr.compute_tree_id_for_directory(repo_root_member_path)
                tree_id_2 = uvsmgr.compute_tree_id_for_directory(repo_root_member_path)
                tree_id_3 = uvsmgr.compute_tree_id_for_directory(repo_root_member_path)

                # print "found repo root subdir at path: " + repo_root_member_path + " its tree id: "
                # print tree_id_1
                # print tree_id_2
                # print tree_id_3

                self.assertEquals(tree_id_1, tree_id_2)
                self.assertEquals(tree_id_2, tree_id_3)



    def test_init_make_3_commits_checkout_all_and_verify(self):


        # first modularize the code that creates some random tree
        # call it multiple times, each time commit and save the md5sums, repeat at least 3 times.
        #

        pass


    def test_init_then_make_one_commit_then_recover(self):

        test_pass = "123"
        # ---------------- init uvs repo on   self.repo_root_path
        uvsmanager.init_new_uvs_repo_overwrite(repo_pass=test_pass, repo_root_path=self.repo_root_path)

        # ---------------- make a commit
        uvsmgr = uvsmanager.UVSManager(repo_pass=test_pass, repo_root_path=self.repo_root_path)
        snapid = uvsmgr.take_snapshot(snapshot_msg='test commit', author_name="n/a", author_email="n/a")

        # ---------------- delete the checked out copy.
        self.empty_test_repo()


        # ---------------- now checkout last commit
        uvsmgr.checkout_reference_at_repo_root(snapshot_ref=snapid, clear_dest=True)


        # ---------------- now check to see if we recovered correctly.
        check_cmd = "md5sum -c " + self.repo_root_cksums_file

        # if exit code is non-zero (md5 failed) check output should raise error.
        # subprocess.check_output(check_cmd,  shell=True)

        # call will return the exit code.
        blackhole = open(os.devnull, 'wb')
        check_cmd_exit_code = subprocess.call(check_cmd, stdout=blackhole, stderr=blackhole, shell=True)
        self.assertEquals(check_cmd_exit_code, 0)



if __name__ == '__main__':

    unittest.main()