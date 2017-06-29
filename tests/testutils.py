
import hashlib
import os


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