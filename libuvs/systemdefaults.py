
# This module is where all the system defaults live.
# changing a hashing algorithm from sha256 to sha512 should require changes to this file only.
# the entire rest of the system should not assume anything about choice of cipher, hash, length of something .....
# all of these defaults should be set/changed in this module only.
# in addition to cryptographic defaults other default values live here too. these can be anything
# such locale or what name to use for the top level headless repo directory (i.e. '.uvs' or something else)




#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------


# TODO
# NOTE
## ATTENTION: if any of these insecure modes are enabled, the system is not secure.
## They can be set to assist with debug/devel.
_INSECURE_RAND_SRC = False

_INSECURE_LOG_MSGS = True

_NOT_SO_RAND_SNAPSHOT_ID = True

# this is where the ciphertext blobs live,  dont put any source files or anything else that needs protection in here.
# Remember the goal is that this folder + secret passphrase is enough to recover the entire repo and its history
# for a regular user to work with the edvcs, and this folder alone (w/- secret passphrase) reveals no information
# about the source files in this repo or their history
_SHADOW_FOLDER_NAME = '.uvs_shadow'

# this folder may contain information that helps the edvcs do its job and is not part of the source
# but they are not in ciphertext and not to be ever pushed to the cloud.
#
# Ideally it should be lazily generated and regenerated if its deleted by the user ,
# but we are in early alpha stage, so i cant guarantee that is how it will be used.
_CACHE_FOLDER_NAME = '.uvs_cache'


#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------


class HashAlgo(object):
    """" Enumerate different choices for cryptographic hash function. """

    SHA512 = 0
    SHA3_512 = 1

## change this global to use a different hash.
_REPO_HASH_CHOICE = HashAlgo.SHA512





def should_print_insecure_log_msgs():
    """ Return true when insecure log msgs are desired (during development) returns false in production """

    return _INSECURE_LOG_MSGS



def is_in_insecure_rand_mode():
    """ Return true when the system is running in the insecure random source. False otherwise. 
     Also prints warning to console every time mode is queried.
     
     This method should return False in a production environment.
     """

    if _INSECURE_RAND_SRC:
        print "*******  Warning: system is in INSECURE RAND SRC MODE. (use this only in development). "

        return True

    return False
