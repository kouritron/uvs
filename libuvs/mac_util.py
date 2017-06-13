
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat import backends

import systemdefaults as sdef



def get_tag(message, signing_key):
    """ Given a byte array as message, and a signing key, compute a secure MAC tag for it and return the tag.
     The signing key must be kept private at all times otherwise an attacker can sign arbitrary messages and
     produce correct tags to verify them. """

    pass


def verify_tag(message, tag):
    """ Given a message and its tag verify that the tag could not have been produced by anyone not in possession
    of the key. Raises exception if tag verification fails """

    pass
