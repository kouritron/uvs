
import hashlib
import os
import random

# this should run once when test utils is imported by other test cases.
random.seed(0)


_RAND_NAME_SIZE = 12
_FILE_SIZE_MIN = 20
_FILE_SIZE_MAX = 800

_NUM_FILES_MIN = 2
_NUM_FILES_MAX = 9




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


def get_random_filename():
    """ Return a random name that can be used as a file or directory name. """

    return "tst_" +  os.urandom(_RAND_NAME_SIZE).encode('hex')


def save_random_files_to_directory(dirpath):
    """ Given the path to directory make and save some random files to it.
        if path does not exist it will be created.
    :param dirpath: path to the directory to be populated with random content
    :return: None
    """

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


    # this returns a random integer N such that a <= N <= b.
    num_files = random.randint(a=_NUM_FILES_MIN, b=_NUM_FILES_MAX)

    for i in range(0, num_files):

        # come up with a random file name.
        file_name = get_random_filename()

        # file content should be at least this size:

        rand_size = random.randint(a=_FILE_SIZE_MIN, b=_FILE_SIZE_MAX)

        file_content = os.urandom(rand_size).encode('hex').replace('9', '\n')

        fpath = os.path.join(dirpath, file_name)

        with open(fpath, 'wb') as fhandle:
            fhandle.write(file_content)



def populate_directory_with_random_files_and_subdirs(dirpath):
    """ Given the path to a directory make and save some random files and subdirs with random content to it.
        if path does not exist it will be created.

    :param dirpath: path to the directory to be populated with random content
    :return: None
    """

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    save_random_files_to_directory(dirpath=dirpath)

    # make and populate some subdirs.
    for i in range(0, 5):
        subdir_path = os.path.join(dirpath, get_random_filename())
        save_random_files_to_directory(dirpath=subdir_path)

        for i in range(0, 3):
            subdir_subdir_path = os.path.join(subdir_path, get_random_filename())
            save_random_files_to_directory(dirpath=subdir_subdir_path)




