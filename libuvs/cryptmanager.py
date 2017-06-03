


from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac

import base64

import log
import rand_util
import kdf_util
import systemdefaults as sdef


def get_uvs_fingerprint_size():
    """ returns the size of uvs fingerprints. this is not necessarily the same size as the underlying message
    digest size. 
    
    uvs fingerprints are a way of producing small fingerprints that identify large objects. They are to be assumed
    collision free in practice, similar to cryptographic hash functions. 
    
    the main difference between uvs fingerprint of a given object and say for example sha256 or sha512 fingerprint
    of that object is that uvs fingerprints are also dependent on each repository's key and salt. 
    
    sha512(b'hello world') is always the same universally.
    uvs_fingerprint(b'hello world') is different in two different repositories with diff passwords and salts.
     
    this helps uvs edvcs hide which files live in each repo. whereas if the non-keyed algorithm was used 
    to fingerprint objects an attacker could tell whether or not some particular plaintext file exists in a repo or
    not. for example an attacker could tell whether or not "react.min.js" is in a repo by looking at the list
    of fingerprints even if he cant access the content of the files which are encrypted.  
    """


    return sdef.get_digest_size()


def get_new_random_salt():
    """ Find a suitable random bit pattern to be used as salt for key derivation, and return it.
     
     Result is hex encoded for easy transport and/or viewing. It should be hex decoded back down to bytes before 
     getting passed to the cryptography library functions. This module takes care of that. Functions of this module 
     return hex encoded values, and hex decode their argument values whenever suitable.
     
     Note the salt need not be secret. Just something to be passed to kdf along with 
     user password, to make the encryption keys coming out of kdf, not pre-computable 
     (i.e. an attack against a 2nd repository should start from scratch and not benefit from another attack against 
     a different repository from a different time). 
     """

    result = rand_util.get_new_random_salt_for_current_mode().encode('hex')

    log.fefrv("get_new_random_salt() returning. result (as hex encoded): ")
    log.fefrv(str(result), label=False)
    return result


class UVSCryptHelper(object):
    """ Helper class for performing the necessary encryption decryption and fingerprint of objects tracked
    by the uvs encrypted distributed version control system.
    
    """

    def __init__(self, usr_pass, salt):
        """ Init a new crypt helper object. Applies the key derivation function to 
        user password, and saves it in this object for future operations. 
        
        To lose the keys simply destroy this object from memory. 
        
        Since the key derivation function is intentionally compute-intensive this init call might take 
        a while and/or use a lot of memory before returning. 
        """

        super(UVSCryptHelper, self).__init__()

        fernet_key_len = 32

        # the len of the key that will be used to derive the uvs fingerprints for any object
        uvsfp_key_len = sdef.get_digest_size()

        total_key_len = fernet_key_len + uvsfp_key_len

        # derive key returns a bytes object (no hex or base64 encoding here)
        kdf_output_key = kdf_util.derive_key(key_material=usr_pass, salt=salt.decode('hex'), key_len=total_key_len)

        log.hazard('kdf produced key in hex: \n' + str(kdf_output_key.encode('hex')))

        # the first uvsfp_key_len many bytes are for keyed fingerprinting of objects
        self.uvsfp_key_bytes = kdf_output_key[:uvsfp_key_len]

        # fernet wants a 256 bit key
        # the 1st 128 bits of this are used for AES 128 CBC
        # the 2nd 128 bits of this are used for authenticating tokens (HMAC part of fernet)
        fernet_key_bytes = kdf_output_key[uvsfp_key_len: uvsfp_key_len + fernet_key_len]

        log.hazard('uvs fp key in hex: \n' + str(self.uvsfp_key_bytes.encode('hex')))
        log.hazard('fernet key in hex: \n' + str(fernet_key_bytes.encode('hex')))

        # create a new fernet instance
        # fernet wants key to be encoded with the URL safe variant of base64
        self._fernet = Fernet(key=base64.urlsafe_b64encode(fernet_key_bytes))



    def encrypt_bytes(self, message):
        """ Encrypt and return ciphertext for the given message. message is a byte array (bytes or str object) 
         The cipher text includes authentication codes such that in the future it can be both verified 
         and decrypted to recover the original message by someone who posses the key. 
        """

        log.fefr('encrypt_bytes() called, with message: ' + str(message) )

        assert isinstance(message, str) or isinstance(message, bytes)

        fernet_token = self._fernet.encrypt(message)

        log.v( "fernet ciphertext in hex: " + base64.urlsafe_b64decode(fernet_token).encode('hex'))

        return fernet_token


    def decrypt_bytes(self, ct):
        """ Decrypt and return the plaintext message that was used to construct the supplied argument.
        The argument is a bytes or str object.
        
        Raise error if ciphertext has been tampered with (MAC fails) or if the key is invalid. 
        """

        log.fefrv('decrypt_bytes() called, with ciphertext: ' + str(ct))

        assert isinstance(ct, str) or isinstance(ct, bytes)

        original_message = self._fernet.decrypt(ct)

        log.hazard( "Decrypted the token, original plaintext in hex: " +
                    base64.urlsafe_b64decode(original_message).encode('hex'))

        return original_message


    def get_uvs_fingerprint_of_bytes(self, message):
        """ Compute and return the uvs fingerprint for the given message. 
        message is a byte array (str or bytes object)
        """


        hash_func = None

        if sdef._REPO_HASH_CHOICE == sdef.HashAlgo.SHA512:
            hash_func = hashes.SHA512()

        if sdef._REPO_HASH_CHOICE == sdef.HashAlgo.SHA256:
            hash_func = hashes.SHA256()

        if None == hash_func:
            raise NotImplementedError('un-supported or not implemented hash choice')



        hmac_func = hmac.HMAC(self.uvsfp_key_bytes, hash_func, backend=default_backend())

        hmac_func.update(message)
        uvsfp = hmac_func.finalize()

        log.v('>> computed uvs fp, message was (in hex): ' + str(message.encode('hex')))
        log.v('>> uvs fp (in hex): ' + str(uvsfp.encode('hex')))

        return uvsfp
