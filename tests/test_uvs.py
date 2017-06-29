


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





class TestRedFileCli(unittest.TestCase):



    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestRedFileCli, cls).setUpClass()
        print "---------------------- setUpClass() called"

        # make directory with random names and random subdirs and random files.
        cls.test_tree = {}


    @classmethod
    def tearDownClass(cls):
        super(TestRedFileCli, cls).tearDownClass()
        print "---------------------- tearDownClass() called"

        # use shutil to delete the test trees.


    # setUp will run once before every testcase
    def setUp(self):
        pass

    # tearDown will run once after every testcase
    def tearDown(self):
        pass



    def test_init_then_make_one_commit(self):

        pass



if __name__ == '__main__':
    unittest.main()