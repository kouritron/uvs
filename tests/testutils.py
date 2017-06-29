
import hashlib
import os
import random

# this should run once when testutils is imported by other test cases.
random.seed(0)


def get_file_hash(filename):
    """ Return a str obj with the hex representation of the hash of the file with the given filename.
    (assuming the file does exist and is readable. exception is raised otherwise)
    """

    READ_SIZE = 8192 * 4
    srcfile = open(filename, 'rb')
    hash_func = hashlib.sha256()
    buf = srcfile.read(READ_SIZE)
    while len(buf) > 0:
        hash_func.update(buf)
        buf = srcfile.read(READ_SIZE)

    return hash_func.hexdigest()


def make_binary_file_with_random_content(filename, size):
    """ Create a binary file on disk filled with random content of size equal to size
    with the given filename.
    """

    # fhandle = open(filename, 'wb')
    with open(filename, 'wb') as fhandle:
        fhandle.write(os.urandom(size))


def make_ascii_file_with_random_content(filename, size):
    """ Create a ascii chars only file on disk filled with random content of size equal to size
    with the given filename.
    """

    # fhandle = open(filename, 'wb')
    with open(filename, 'wb') as fhandle:
        buf = os.urandom(size/2).encode('hex')
        fhandle.write(buf.replace('9', '\n'))


def find_file_within_this_project(filename):
    """ Find and return the full path of the file with the given filename within the uvs project.
     this is just some utility function for uvs test cases, its not some generic re-usable find file
     algorithm. if the structure of uvs source changes this may well break.
    """

    # depending on whether we are running the tests from an IDE or terminal and the value of cwd
    # we are most likely either at uvs/ or uvs/tests.
    # so this is hopefully high enough point to start the search from
    search_root = ".."
    result = None
    # root is a string ( just the prefix of the current directory) (i.e. "/home/u/uvs" )
    # subdirs is list of all subdirs found within the current directory
    # files is a list of all file names found within the current directory
    for dirpath, subdirs, files in os.walk(search_root):
        if filename in files:
            relative_path = os.path.join(dirpath, filename)
            result = os.path.abspath(relative_path)
            print "Found absolute path to be: " + result
            break

    return result


_RAND_NAME_SIZE = 12
_FILE_SIZE_MIN = 20
_FILE_SIZE_MAX = 800

_NUM_FILES_MIN = 2
_NUM_FILES_MAX = 9

def get_random_filename():
    """ Return a random name that can be used as a file or directory name. """

    return "tst_" +  os.urandom(_RAND_NAME_SIZE).encode('hex')


def make_random_repo():
    """

    """

    # For testing lets represent a repo like this:
    # a dict to represent the root.
    # inside the dict you will find str keys and either str or dict values.
    # the str key is the name of the member. if value is a string, its a file and the content of
    # the file are the content of the str.
    # if value is a dict, its a directory with dir name being the key,

    repo_root = make_random_dir()

    # now add some more subdirs.

    # this returns a random integer N such that a <= N <= b.
    num_subdirs = random.randint(a=1, b=5)

    for i in range(0, num_subdirs):

        # come up with a random subdir name.
        subdir_name = get_random_filename()
        repo_root[subdir_name] = make_random_dir()

    return repo_root



def make_random_dir():
    """
    """

    # result is a dict of file names to file content
    result_dir = {}

    # this returns a random integer N such that a <= N <= b.
    num_files = random.randint(a=_NUM_FILES_MIN, b=_NUM_FILES_MAX)

    for i in range(0, num_files):

        # come up with a random file name.
        file_name = get_random_filename()

        # file content should be at least this size:

        rand_size = random.randint(a=_FILE_SIZE_MIN, b=_FILE_SIZE_MAX)

        file_content = os.urandom(rand_size).encode('hex').replace('9', '\n')
        result_dir[file_name] = file_content


    return result_dir


def populate_folder_with_random_content(dirpath):
    """ """


    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    for fname, fcontent in make_random_dir().items():
        fpath = os.path.join(dirpath, fname)

        with open(fpath, 'wb') as fhandle:
            fhandle.write(fcontent)
