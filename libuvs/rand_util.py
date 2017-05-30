
import os
import hashlib
import log

from cryptdefaults import is_in_insecure_rand_mode



def get_new_random_salt_for_current_mode():
    """ Return a new salt for key derivation. Based on the defaults of the current crypt mode.
     """
    log.fefrv("get_new_random_salt_for_current_mode() called")

    size = 32

    if is_in_insecure_rand_mode():
        temp = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        factor = (size // len(temp)) + 1
        temp2 = temp * factor
        return temp2[:size]

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
