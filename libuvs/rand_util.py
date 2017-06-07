
import os
import hashlib
import log

import systemdefaults as sdef
import hash_util

import random as rand_src_debug_only

# this is for debug mode only. it will run upon importing this module.
if sdef._NOT_SO_RAND_SNAPSHOT_ID:
    rand_src_debug_only.seed(10)


def get_new_random_salt():
    """ Return a new salt for key derivation. returns a bytes object with the underlying bytes of the salt.
    not hex or base64 encoded. Take the bytes and use it as the salt.
     """
    log.fefrv("get_new_random_salt() called")

    size = 32

    if sdef._INSECURE_RAND_SALT:
        # fixed salt for testing
        return '596381b4268e6811cbf9614c3fa0981515223600f49ab12fc2f783729399a31e'.decode('hex')


    return os.urandom(size)


def get_new_random_filename():
    """ Return a new random filename. This from os urandom in production mode and predictable sequence otherwise.

     When anonymizing filenames from the source directory to its shadow its best to use new random values,
     such as ones given out by os random source, rather than use sha256 fingerprints of filenames. The goal 
     of the shadow folder is to reveal nothing about the source directory, if the filenames are sha256 fingerprints
     an attacker maybe able to guess that file "lib.h" or "readme.md" existed in the source folder and then confirm
     this guess by looking for a file named sha256("lib.h") in the shadow directory. Even though this doesn't 
     reveal much and certainly nothing about the file contents, its best to reveal absolutely nothing. 

     """

    # read a lot of data from os random source then sha256 it to get a random number. (not sha256 of some filename)
    # read a lot of data from os random source in different syscalls for more randomness
    read_size = 8 * 1024

    rand_chunks = []

    for i in range(0, 40):
        rand_chunks.append(os.urandom(read_size))

    hash_func = hashlib.sha512()

    for rand_chunk in rand_chunks:
        hash_func.update(rand_chunk)

    result = hash_func.hexdigest()

    log.fefrv("get_new_random_filename() returning. new file name is: \n " + result)

    return result


def get_new_random_snapshot_id():
    """ Return a new random id to be used as new snapshot id. 
     return value will be hex encoded string. 
     """

    # this is for debug mode only.
    if sdef._NOT_SO_RAND_SNAPSHOT_ID:

        log.vvvv("Random snapshot ids are seeded. This for debug only, don't use this in production.")

        result = hash_util.get_digest_for_bytes(str(rand_src_debug_only.random()) )

        log.fefrv("get_new_random_snapshot_id() returning. new snapid (seeded rand src) is: \n " + result)
        return result

    # read a lot of data from os random source in different syscalls for more randomness
    read_size = 1024

    rand_chunks = []

    for i in range(0, 40):
        rand_chunks.append(os.urandom(read_size))

    result = hash_util.get_digest_for_bytes("".join(rand_chunks))

    log.fefrv("get_new_random_snapshot_id() returning. new snapid (os rand src) is: \n " + result)

    return result


def choose_unique_random_file(dest_directory):
    """ Find a random file path name that does not exist in directory with path dest_directory. 
     Does not check whether the file is writable or not. just that the returned value is pathname not 
     currently existing on this machine.
     """

    rand_read_size = 16

    candidate_fname = "temp_" + str(os.urandom(rand_read_size).encode('hex'))
    candidate_pathname = os.path.join(dest_directory, candidate_fname)

    log.vvvv("candidate path name: " + candidate_pathname)

    while os.path.exists( candidate_pathname ):

        # this should never happen unless the len of random information read is is 2 or 3 bytes
        candidate_fname = "temp_" + str(os.urandom(rand_read_size).encode('hex'))
        candidate_pathname = os.path.join(dest_directory, candidate_fname)

        log.vvvv("Oops candidate file exists. new candidate path name: " + candidate_pathname)

    log.vvvv("found file with unique random pathname: " + candidate_pathname)
    return candidate_pathname


