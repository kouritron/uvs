


from cryptography.fernet import Fernet

import base64

import log
import rand_util
import kdf_util



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


class UVSTwoStageCryptHelper(object):
    """ Helper class for applying the uvs 2 stage encryption scheme, (where the first round is
     deterministic, and 2nd is randomized using random IVs, and MACed)
    
     The user of this class provides a password (secret) and a salt (public but random).
     This class then provides methods for performing 1st stage (deterministic stage) 
     and 2nd stage (randomized with IV and MACed) encryption and decryption and MAC verification.
    """

    def __init__(self, usr_pass, salt, progress_callback=None):
        """ Init a new crypt helper object. Applies the key derivation function to 
        user password, and saves it in this object for future operations. 
        
        To lose the keys simply destroy this object from memory. 
        
        Since the key derivation function is intentionally compute-intensive this init call might take 
        a while to return. 
        """

        super(UVSTwoStageCryptHelper, self).__init__()

        # derive key returns a bytes object (no hex or base64 encoding here)
        kdf_output_key = kdf_util.derive_key(key_material=usr_pass, salt=salt.decode('hex'), key_len=48)

        log.hazard('kdf produced key in hex: \n' + str(kdf_output_key.encode('hex')))

        # the first 128 bits (16  bytes) are for stage 1 (deterministic stage) encryption
        self.stage1_key = kdf_output_key[:16]

        # the 2nd 128 bits are key for the AES 128 CBC part of fernet
        # the 3rd 128 bits are the key for HMAC part of fernet
        # fernet wants a 256 bit key
        fernet_key_bytes = kdf_output_key[16:48]

        # fernet wants key to be encoded with the URL safe variant of base64
        fernet_key = base64.urlsafe_b64encode(fernet_key_bytes)



        log.hazard('fernet key in urlsafe base 64: \n' + fernet_key)
        log.hazard('fernet key in hex: \n' + str(fernet_key_bytes.encode('hex')))

        # create a new fernet instance
        self._fernet = Fernet(key=fernet_key)



    def perform_final_stage_encryption_then_mac_on_bytes(self, plaintext_stage2):
        """ In the uvs 2 stage encryption scheme, (where the first round is deterministic, and 2nd is randomized
         using random IVs, and MACed), perform the final stage encryption then MAC, and return the result. 
         Given a bunch of bytes in the first argument (plain_text), 
         encrypt it, and return the ciphertext (with mac) as another bytes object. 
        
         This encryption is performed in CBC mode with random IVs so as to reveal nothing about src. 
         This is a encrypt then mac scheme. 
        """

        log.fefr(' () called, with message: ' + str(plaintext_stage2) )

        assert isinstance(plaintext_stage2, str) or isinstance(plaintext_stage2, bytes)

        final_ciphertext = self._fernet.encrypt(plaintext_stage2)

        log.v( "final stage ciphertext in hex: " + base64.urlsafe_b64decode( final_ciphertext ).encode('hex') )

        return final_ciphertext


    def verify_mac_and_remove_final_stage_encryption_on_bytes(self, final_stage_ciphertext):
        """ In the uvs 2 stage encryption scheme, (where the first round is deterministic, and 2nd is randomized
         using random IVs, and MACed), verify the MAC, and then if passed, remove the 2nd stage encryption and return
         the result. Raise an error if MAC fails. 
         
         The argument to this method is a bytes object containing the the output of the 2nd stage. 
        """

        log.fefrv(' () called, with ciphertext: ' + str(final_stage_ciphertext))

        assert isinstance(final_stage_ciphertext, str) or isinstance(final_stage_ciphertext, bytes)

        #
        plaintext_stage2 = self._fernet.decrypt(final_stage_ciphertext)

        log.hazard( "Decrypted the token, the plaintext of stage 2 (which is the ciphertext of stage 1) in hex: " +
                    base64.urlsafe_b64decode(plaintext_stage2).encode('hex'))

        return plaintext_stage2


    def perform_deterministic_stage_encryption_on_bytes(self, dt_stage_plaintext):
        """ In the uvs 2 stage encryption scheme, (where the first round is deterministic, and 2nd is randomized
         using random IVs, and MACed) perform the first stage encryption, on the supplied byte array and 
         return the resulting ciphertext.
        """

        pass


    def perform_deterministic_stage_decryption_on_bytes(self, dt_stage_ciphertext):
        """ In the uvs 2 stage encryption scheme, (where the first round is deterministic, and 2nd is randomized
         using random IVs, and MACed) remove the first stage encryption on the supplied byte array and
          return the resulting plaintext.
        """

        pass



