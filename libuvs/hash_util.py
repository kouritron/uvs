


import hashlib
import systemdefaults as sdef


def get_digest_for_file(src_pathname):
    """ Given a pathname to a src file, compute its hash digest (aka fingerprint) and return it. 
    The choice of hash function depends on system defaults. 
    """

    assert False, 'implement me'


def get_digest_for_bytes(src_bytes):
    """ Given a bit pattern as a bytes object, compute its hash (aka hash digest, aka fingerprint) 
      and return it as a hex encoded string. 
      the choice of cryptographic hash function depends on system defaults. 
      """


    assert isinstance(src_bytes, str) or isinstance(src_bytes, bytes)

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA512:
        hf = hashlib.sha512()
        hf.update(src_bytes)

        return hf.hexdigest()

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA256:
        hf = hashlib.sha256()
        hf.update(src_bytes)

        return hf.hexdigest()

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA224:
        hf = hashlib.sha224()
        hf.update(src_bytes)

        return hf.hexdigest()

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA384:
        hf = hashlib.sha384()
        hf.update(src_bytes)

        return hf.hexdigest()

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA3_512:
        assert False, 'sha3 512 is not implemented yet.'

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA3_256:
            assert False, 'sha3 512 is not implemented yet.'

    assert False, 'unknown hash is in use for this repository.'
