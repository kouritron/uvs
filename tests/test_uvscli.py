


import os
import sys
import  shutil
import io

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


class TestUVSCli(unittest.TestCase):


    repo_root_path = None
    repo_root_cksums_file = None

    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestUVSCli, cls).setUpClass()

        cwd = os.getcwd()
        print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> setUpClass() called from cwd: " + str(cwd)


        tests_folder_abs_path = os.path.dirname(tu.find_file_within_this_project('test_uvscli.py'))

        print "Found tests directory path to be: " + str(tests_folder_abs_path)

        cls.repo_root_path = os.path.join(tests_folder_abs_path, 'ignoreme')
        cls.repo_root_cksums_file = os.path.join(tests_folder_abs_path, "ignoreme_md5sums")

        print "repo root path: " + cls.repo_root_path
        print "repo root cksums file: " + cls.repo_root_cksums_file


    @classmethod
    def tearDownClass(cls):
        super(TestUVSCli, cls).tearDownClass()
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


    def test_cli_init_twice_wont_overwrite(self):

        # delete previous test repo if it existed.
        self.remove_test_repo()

        if not os.path.exists(self.repo_root_path):
            os.makedirs(self.repo_root_path)

        test_pass = '123'

        init_cmd = ['uvs', 'init']

        p = subprocess.Popen(init_cmd, stdin=subprocess.PIPE, cwd=self.repo_root_path)

        p.stdin.write(test_pass)
        p.stdin.close()

        # wait for process to terminate, note that wait is not safe to call
        # if we had set stdout or stderr to PIPE as well as stdin.
        exit_code = p.wait()


        print "$ " + str(init_cmd[0]) + " " + str(init_cmd[1]) + "\nexit code: " + str(exit_code)

        self.assertEquals(exit_code, 0)

        # -------------------------------------------------------------------------- init again check exit code.

        p = subprocess.Popen(init_cmd, stdin=subprocess.PIPE, cwd=self.repo_root_path)

        p.stdin.write(test_pass)
        p.stdin.close()

        # wait for process to terminate, note that wait is not safe to call
        # if we had set stdout or stderr to PIPE as well as stdin.
        exit_code = p.wait()

        result = "# doing it 2nd time. it should not be allowed. expect non-zero exit code.\n$ " + str(init_cmd[0])
        result += " " + str(init_cmd[1]) + "\nexit code: " + str(exit_code)
        print result

        self.assertNotEquals(exit_code, 0)



    def test_cli_init_then_make_one_commit_then_recover(self):


        # delete previous test repo if it existed.
        self.remove_test_repo()

        # this should a folder called ignoreme resident on the same location where this file (test_uvscli.py) resides
        print "creating test uvs repo at: " + self.repo_root_path

        if not os.path.exists(self.repo_root_path):
            os.makedirs(self.repo_root_path)

        # make and populate the repo root ith some random dirs and files to
        # be treated as a test uvs repository.
        tu.populate_directory_with_random_files_and_subdirs(dirpath=self.repo_root_path)

        # now save md5 of what we created.
        cmd = "find " + self.repo_root_path
        cmd += " -type f -print0 | xargs -0 md5sum > " + self.repo_root_cksums_file
        subprocess.call(cmd, shell=True)

        # ---------------------------------------------------------------------------- Repo ready to go


        test_pass = '123'

        init_cmd = ['uvs', 'init']

        # p = subprocess.Popen('cat', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #p = subprocess.Popen(['uvs', 'init'], stdin=subprocess.PIPE, shell=True)
        p = subprocess.Popen(init_cmd, stdin=subprocess.PIPE, cwd=self.repo_root_path)

        p.stdin.write(test_pass)
        p.stdin.close()

        # wait for process to terminate, note that wait is not safe to call if we had set stdout or stderr to PIPE
        # as well as stdin.
        exit_code = p.wait()


        print "$ " + str(init_cmd[0]) + " " + str(init_cmd[1]) + "\nexit code: " + str(exit_code)

        self.assertEquals(exit_code, 0)



        # TODO delete the files and check them back out again then verify using md5



    def _disabled_test_init_then_make_one_commit_then_recover(self):

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