


import base64
import log
import rand_util
import kdf_util



from cryptography.fernet import Fernet

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


class Transcryptor(object):
    """ Helper class for encrypting and decrypting files safely with a symmetric cipher and  user provided  
     password (user pass, is the pass b4 kdf applied) and salt.
     
     The password must be kept secret, otherwise cipher text produced by this class no better than plaintext.  
     The salt need not be kept secret. 
    """

    def __init__(self, usr_pass, salt, progress_callback=None):
        """ Init a new Transcryptor object. Applies the key derivation function to user password, and 
        saves it in this object for future encrypt, decrypt operations. 
        
        To lose the key simply destroy this object from memory. 
        
        Since the key derivation function is intentionally compute-intensive this init call might take 
        a while to return. 
        """

        super(Transcryptor, self).__init__()

        kdf = kdf_util.make_kdf_for_current_mode(salt=salt.decode('hex'))

        # kdf.derive returns a str (bytes object) (which is not encoded in hex or b64 or anything else)
        # Fernet requires  urlsafe_b64encode
        encryption_key = base64.urlsafe_b64encode( kdf.derive(key_material=usr_pass))

        log.hazard('encryption key in urlsafe base 64: \n' + encryption_key)
        log.hazard('encryption key in hex: \n' + str(base64.urlsafe_b64decode(encryption_key).encode('hex')))

        # create a new fernet instance
        self._fernet = Fernet(key=encryption_key)

        # now to transcrypt simply:
        # ciphertext_token = self._fernet.encrypt(b"my deep dark secrets")
        # plaintext =  self._fernet.decrypt(ciphertext_token)


        # this returns None if ok, else raises InvalidKey error, also u need a new kdf object,
        # they destroy themselves after one use.
        # kdf = cryptmode.make_kdf_for_current_mode(salt=salt.decode('hex'))
        # kdf.verify(key_material=usr_pass, expected_key=self.encryption_key)


    def encrypt_file(self, src, dst):
        """ Given the pathname to a source file, encrypt it and save it into another file whose pathname is dst.  """

        log.fefrv('encrypt_file() called, with src: >>{}<< dst: >>{}<<'.format(src, dst))

        src_fhandle = open(src, 'rb')
        dst_fhandle = open(dst, 'wb')

        src_bytes = src_fhandle.read()

        dst_bytes = self._fernet.encrypt(src_bytes)

        # log.vvv('src_bytes: ' + src_bytes)
        # log.vvv('dst_bytes: ' + dst_bytes)
        # log.v( "dst_bytes in hex: " + base64.urlsafe_b64decode( dst_bytes ).encode('hex') )

        dst_fhandle.write(dst_bytes)





    def decrypt_file(self, src, dst):
        """ Given the pathname to a source file, decrypt it and save it into another file whose pathname is dst.  """


        log.fefrv('decrypt_file() called, with src: >>{}<< dst: >>{}<<'.format(src, dst))

        src_fhandle = open(src, 'rb')
        dst_fhandle = open(dst, 'wb')

        src_bytes = src_fhandle.read()

        dst_bytes = self._fernet.decrypt(src_bytes)

        # log.vvv('src_bytes: ' + src_bytes)
        # log.vvv('dst_bytes: ' + dst_bytes)
        # log.v( "dst_bytes in hex: " + base64.urlsafe_b64decode( dst_bytes ).encode('hex') )

        dst_fhandle.write(dst_bytes)


