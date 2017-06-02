



#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------


from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat import backends





#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
def make_kdf_for_current_mode(salt):
    """ Make and return kdf object, that can be used to derive encryption keys from a user pass and a salt. 
    Depending on which mode and cryptography defaults the system is running in this will return a suitable kdf.
    """

    assert None != salt

    return _make_kdf_1(salt=salt)


def _make_kdf_1(salt):
    """ Make and return kdf object, using the 1st set of defaults. .
    """

    assert None != salt

    backend = backends.default_backend()
    algorithm = hashes.SHA256()

    # length is the desired length of the derived key.
    length = 32
    iterations = 1000 * 1000   # 1 million rounds of sha256

    kdf = PBKDF2HMAC(algorithm=algorithm, length=length, salt=salt, iterations=iterations, backend=backend)
    return kdf

def _make_kdf_2(salt):
    """ Make and return kdf object, using the 2nd set of defaults. .
    """

    assert None != salt

    backend = backends.default_backend()
    algorithm = hashes.SHA512()

    # length is the desired length of the derived key.
    length = 32
    iterations = 2000 * 1000 # 2 million rounds of sha512

    kdf = PBKDF2HMAC(algorithm=algorithm, length=length, salt=salt, iterations=iterations, backend=backend)
    return kdf


