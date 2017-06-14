
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

_INSECURE_RAND_SALT = True

_NOT_SO_RAND_SNAPSHOT_ID = False

_SKIP_ENCRYPTION = True

if _SKIP_ENCRYPTION: print "\033[1;31m" + "\n**** Warning system is set to skip encryption ****\n" + "\033[0;0m"

# this is where the ciphertext blobs live,  dont put any source files or anything else that needs protection in here.
# Remember the goal is that this folder + secret passphrase is enough to recover the entire repo and its history
# for a regular user to work with the edvcs, and this folder alone (w/- secret passphrase) reveals no information
# about the source files in this repo or their history
_SHADOW_FOLDER_NAME = '.uvs_shadow'

_SHADOW_DB_FILE_NAME = 'uvs.db'

# this folder may contain information that helps the edvcs do its job and is not part of the source
# but they are not in ciphertext and not to be ever pushed to the cloud.
#
# Ideally it should be lazily generated and regenerated if its deleted by the user ,
# but we are in early alpha stage, so i cant guarantee that is how it will be used.
_CACHE_FOLDER_NAME = '.uvs_cache'



# this says if i am creating new segments for a new file, break it into segments of size default size
# but if need you can make segments that are smaller than this or larger than this to handle deletions
# and insertions. For more info look at the documentation on segments
_SEGMENT_SIZE_DEFAULT = 4096


# this says dont create segments of larger size than this. if necessary make two smaller chunks
# TODO more research on this
# also consider that each segment gets encrypted with Fernet and we a get a fernet token for each segment
# to be sent to the public server. Now somewhere i read that there are limits to how much data can be
# safely encrypted with a fixed (key, IV) pair. now in fernet a single token (segment in our case)
# will use a single Key, IV pair. so maybe that means that fernet tokens should not get too large.
# at the moment segment size does protect us from unlimited fernet tokens sizes.
_SEGMENT_SIZE_MAX = 8192

# in case pbkdf2 is used for key derivation, this specifies number of iterations
# TODO reset this back to 1 million or higher. i am lowering it now for development
#_PBKDF2_ITERATIONS = 1000 * 1000
_PBKDF2_ITERATIONS = 60000
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------


class HashAlgo(object):
    """" Enumerate different choices for cryptographic hash function. """

    SHA512 = 0
    SHA3_512 = 1
    SHA256 = 2
    SHA3_256 = 3

    # truncated ones: At first glance it might seem that these are weak, bad, or less collision resistant somehow
    # but you would be wrong. truncating sha512 for example down to 300 bits still offers an incredibly
    # strong collision resistant hash, but it also becomes a less revealing hash (good for MAC construction)
    # because now an attacker has even less information about the source message or the internal state
    # of the hash when the hashing was complete, so things like length extension attacks become probably impossible.
    SHA224 = 4
    SHA384 = 5


    # TODO add blake and whirlpool (sha3 finalists) (find a py lib that supports it)





class EncryptionAlgo(object):
    """" Enumerate different choices for the symmetric encryption algorithm. """

    # use Fernet version 0x80 as implemented by the python cryptography library w/- modifications
    FERNET_0x80 = 0

    # use AES 256 in CBC mode for encryption and HMAC sha256 for integrity
    AES_256_HMAC_SHA256 = 1

    # use AES 256 in CBC mode for encryption and HMAC sha384 for integrity
    AES_256_HMAC_SHA384 = 2

    # use camellia 256 in CBC mode for encryption and HMAC sha256 for integrity
    CAMELLIA_256_HMAC_SHA256  = 3

    # use camellia 256 in CBC mode for encryption and HMAC sha384 for integrity
    CAMELLIA_256_HMAC_SHA384  = 4

    # TODO: add more, perhaps fernet first and then another round camellia 256 with no timestamps.






class KDFAlgo(object):
    """" Enumerate different choices for the key derivation function. """

    # use PBKDF2HMAC from RSA labs algo using sha512
    PBKDF2_WITH_SHA512 = 0

    # use PBKDF2HMAC from RSA labs algo using sha256
    PBKDF2_WITH_SHA256 = 1

    # use scrypt (rfc 7914) for key derivation function.
    SCRYPT = 2

    # use argon2 (the winner of password hashing competition of 2015) for key derivation function.
    ARGON2 = 3



## change this global to use a different hash.
_REPO_HASH_CHOICE = HashAlgo.SHA384

## change this global to use a diff kdf.
_REPO_KDF_CHOICE = KDFAlgo.PBKDF2_WITH_SHA256

## change this global to use a different symmetric cipher.
_REPO_ENCRYPTION_ALGO_CHOICE = EncryptionAlgo.FERNET_0x80


def get_digest_size():
    """ Return the digest size of cryptographic hash function used by current repository in bytes.
     i.e. if this repo is using sha512 for hash algorithm then this function should return 64.
     """


    if _REPO_HASH_CHOICE == HashAlgo.SHA512:
        return 64

    if _REPO_HASH_CHOICE == HashAlgo.SHA3_512:
        return 64

    if _REPO_HASH_CHOICE == HashAlgo.SHA3_256:
        return 32

    if _REPO_HASH_CHOICE == HashAlgo.SHA256:
        return 32

    if _REPO_HASH_CHOICE == HashAlgo.SHA224:
        return 28

    if _REPO_HASH_CHOICE == HashAlgo.SHA384:
        return 48



    assert False, 'unknown hash is in use for this repository.'


