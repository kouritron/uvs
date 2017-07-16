


from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac

import base64

import log
import rand_util
import kdf_util
import systemdefaults as sdef


def get_encryption_algo_desc():
    """ Return a string representation of the system's current default encryption algorithm. """

    log.cmv("get_encryption_algo_desc() called. ")

    if sdef.REPO_ENCRYPTION_ALGO_CHOICE == sdef.EncryptionAlgo.FERNET_0x80:
        return "FERNET_0x80"

    if sdef.REPO_ENCRYPTION_ALGO_CHOICE == sdef.EncryptionAlgo.AES_256_HMAC_SHA256:
        return "AES_256_HMAC_SHA256"

    if sdef.REPO_ENCRYPTION_ALGO_CHOICE == sdef.EncryptionAlgo.AES_256_HMAC_SHA384:
        return "AES_256_HMAC_SHA384"

    if sdef.REPO_ENCRYPTION_ALGO_CHOICE == sdef.EncryptionAlgo.CAMELLIA_256_HMAC_SHA256:
        return "CAMELLIA_256_HMAC_SHA256"

    if sdef.REPO_ENCRYPTION_ALGO_CHOICE == sdef.EncryptionAlgo.CAMELLIA_256_HMAC_SHA384:
        return "CAMELLIA_256_HMAC_SHA384"




def get_uvs_fingerprinting_algo_desc():
    """ Return a string mentioning the current fingerprinting algorithm in use by the system. """

    log.cmv("get_uvs_fingerprinting_algo_desc() called. ")

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA512:
        return  "SHA512_HMAC"

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA256:
        return  "SHA256_HMAC"

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA224:
        return  "SHA224_HMAC"

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA384:
        return  "SHA384_HMAC"

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA3_256:
        return  "SHA3_256"

    if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA3_512:
        return  "SHA3_512"

    raise NotImplementedError('unknown or un-implemented hash algo in use. ')



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

    log.cmv("get_uvs_fingerprint_size() called. ")

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

    result = rand_util.get_new_random_salt().encode('hex')

    log.cmv("get_new_random_salt() returning. result (as hex encoded): ")
    log.cmv(str(result), label=False)
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

        # the storage engine uses keyed hash as fingerprints of previously seen objects.
        # there will be empty or guessable objects in the repository (such as an empty folder, or
        # a file with known content, such as a license file) an attacker may guess the content of certain files.
        # if this key len is too small (i.e. 8 bytes or 64 bits, attacker can brute force search for this key)
        # and then he can test for membership of other files. uvs should protect users from membership tests
        # (meaning if an attacker has a file, he should not be able to confirm or deny its membership in the repo)
        # rfc2104 recommends this key be at least as large as the digest size, i recommend it be larger than
        # both 16 bytes and the digest size.
        assert uvsfp_key_len >= 16, 'storage engine fp key needs to be large.'

        total_key_len = fernet_key_len + uvsfp_key_len

        # derive key returns a bytes object (no hex or base64 encoding here)
        kdf_output_key = kdf_util.derive_key(key_material=usr_pass, salt=salt.decode('hex'), key_len=total_key_len)

        #log.hazard('kdf produced key in hex: \n' + str(kdf_output_key.encode('hex')))

        # the first uvsfp_key_len many bytes are for keyed fingerprinting of objects
        self.uvsfp_key_bytes = kdf_output_key[:uvsfp_key_len]

        # fernet wants a 256 bit key
        # the 1st 128 bits of this are used for AES 128 CBC
        # the 2nd 128 bits of this are used for authenticating tokens (HMAC part of fernet)
        fernet_key_bytes = kdf_output_key[uvsfp_key_len: uvsfp_key_len + fernet_key_len]
        fernet_key_b64 = base64.urlsafe_b64encode(fernet_key_bytes)

        log.hazard('user pass: \n' + str(usr_pass))
        log.hazard('uvs fp key in hex: \n' + str(self.uvsfp_key_bytes.encode('hex')))
        log.hazard('fernet key in hex: \n' + str(fernet_key_bytes.encode('hex')))
        log.hazard('fernet key in b64: \n' + str(fernet_key_b64))

        # create a new fernet instance
        # fernet wants key to be encoded with the URL safe variant of base64
        self._fernet = Fernet(key=fernet_key_b64)



    def encrypt_bytes(self, message):
        """ Encrypt and return ciphertext for the given message. message is a byte array (bytes or str object) 
         The cipher text includes authentication codes such that in the future it can be both verified 
         and decrypted to recover the original message by someone who posses the key. 
        """

        log.cmv('encrypt_bytes() called, with message: ' + repr(message) )

        assert isinstance(message, str) or isinstance(message, bytes) or isinstance(message, unicode)

        # this is just for debugging.
        if sdef.SKIP_ENCRYPTION:
            return message

        fernet_token = self._fernet.encrypt(message)

        log.cmv("fernet ciphertext b64: " + str(fernet_token))

        return fernet_token


    def decrypt_bytes(self, ct):
        """ Decrypt and return the plaintext message that was used to construct the supplied argument.
        The argument is a bytes or str object.
        
        Raise error if ciphertext has been tampered with (MAC fails) or if the key is invalid. 
        """

        log.cmv('decrypt_bytes() called, with ciphertext: ' + str(ct))

        assert isinstance(ct, str) or isinstance(ct, bytes) or isinstance(ct, unicode)

        # this is just for debugging.
        if sdef.SKIP_ENCRYPTION:
            return ct

        original_message = self._fernet.decrypt(ct)

        # this is not really hazard log. running on the client the plaintext is to be checkout to disk.
        # printing keys is hazard log.
        log.cm("Decrypted the token: " + str(original_message) )

        return original_message


    def get_uvsfp(self, message):
        """ Compute and return the uvs fingerprint for the given message. 
        message is a byte array (str or bytes object)
        """

        log.cmv('get_uvsfp() called.')


        assert isinstance(message, str) or isinstance(message, bytes) or isinstance(message, unicode)



        hash_func = None

        if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA512:
            hash_func = hashes.SHA512()

        if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA256:
            hash_func = hashes.SHA256()

        if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA224:
            hash_func = hashes.SHA224()

        if sdef.REPO_HASH_CHOICE == sdef.HashAlgo.SHA384:
            hash_func = hashes.SHA384()


        if None == hash_func:
            raise NotImplementedError('un-supported or not implemented hash choice')


        # cryptography library recommends that the key to the HMAC be same size as the digest_size of the underlying
        # PRF. For detailed discussion read rfc2104. RFC2104 recommends that the key be at least as long as
        # the digest size. It also says if the key is larger than the block size of underlying algo, it will be
        # hashed first and then use the result for HMAC key.
        hmac_func = hmac.HMAC(self.uvsfp_key_bytes, hash_func, backend=default_backend())

        hmac_func.update(message)
        uvsfp = hmac_func.finalize()

        uvsfp = uvsfp.encode('hex')

        log.fp('++++++ computed fp: ' + str(uvsfp) + '   ++++ for message (repr): \n' + repr(message))

        return uvsfp
