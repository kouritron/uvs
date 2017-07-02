


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



    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestUVS, cls).setUpClass()
        print "---------------------- setUpClass() called"

        cwd = os.getcwd()
        print "cwd is: " + cwd

        cls.repo_root_cksums_file = "md5sums_tst_repo"
        cls.repo_root_path = './ignoreme'
        # if 'tests' in cwd:
        #     cls.repo_root_path = '../ignoreme'

        print "creating test uvs repo at: " + cls.repo_root_path

        shutil.rmtree(cls.repo_root_path)

        # make and populate the repo root ith some random dirs and files to
        # be treated as a test uvs repository.
        tu.populate_folder_with_random_content(dirpath=cls.repo_root_path)

        # make and populate some subdirs.
        for i in range(0, 5):
            subdir_path = os.path.join(cls.repo_root_path, tu.get_random_filename())
            tu.populate_folder_with_random_content(dirpath=subdir_path)

            for i in range(0, 3):
                subdir_subdir_path = os.path.join(subdir_path, tu.get_random_filename())
                tu.populate_folder_with_random_content(dirpath=subdir_subdir_path)


        # now save md5 of what we created.
        cmd = "find " + cls.repo_root_path
        cmd += " -type f -print0 | xargs -0 md5sum > " + cls.repo_root_cksums_file
        subprocess.call(cmd, shell=True)

    @classmethod
    def tearDownClass(cls):
        super(TestUVS, cls).tearDownClass()
        print "---------------------- tearDownClass() called"

        # use shutil to delete the test trees.
        repo_root_members = []
        #repo_root_members = os.listdir(cls.repo_root_path)

        for path in repo_root_members:
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


        # ---------------- delete everything at repo_root_path.
        repo_root_members = os.listdir(self.repo_root_path)

        paths_to_remove = []

        dont_remove = set()
        dont_remove.add(sdef.CACHE_FOLDER_NAME)
        dont_remove.add(sdef.SHADOW_FOLDER_NAME)
        dont_remove.add(sdef.SHADOW_DB_FILE_NAME)

        for repo_root_member in repo_root_members:
            if repo_root_member not in dont_remove:
                paths_to_remove.append(os.path.join(self.repo_root_path, repo_root_member))

        for path in paths_to_remove:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)



        # ---------------- now checkout last commit
        uvsmgr.checkout_snapshot(snapid=snapid, clear_dest=True)


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