
import cryptdefaults as cdef
import hashlib



def get_uvs_fingerprint_size():
    """ Return the size of the fingerprints produced by the hash function used by current repository in bytes.
     i.e. if this repo is using sha512 for hash algorithm then this function should return 64.
     """
    if cdef._REPO_HASH_CHOICE == cdef.HashAlgo.SHA512:
        return 64

    if cdef._REPO_HASH_CHOICE == cdef.HashAlgo.SHA3_512:
        return 64

    assert False, 'unknown hash is in use for this repository.'



def get_uvs_fingerprint(src):
    """ Given a bit pattern as a bytes object, compute its hash (aka hash digest, aka fingerprint) 
      and return it as a hex encoded string. 
      the choice of cryptographic hash function depends on the cryptdefaults module. 
      
      """

    assert isinstance(src, str) or isinstance(src, bytes)

    if cdef._REPO_HASH_CHOICE == cdef.HashAlgo.SHA512:

        hf = hashlib.sha512()
        hf.update(src)

        return hf.hexdigest()

    if cdef._REPO_HASH_CHOICE == cdef.HashAlgo.SHA3_512:
        assert False, 'sha3 512 is not implemented yet.'




    assert False, 'unknown hash is in use for this repository.'
