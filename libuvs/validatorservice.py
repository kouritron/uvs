# This module abstracts argument validations, assertions etc etc
# instead of copy pasting tons of assert lines all over the code, factor them out here.




def check_snapid_and_get_std(snapid):
    """ Given a snapshot id, check that it is a valid snapshot id (not that it exists within a given repository or not)
    and return the standardized version of it (everything converted to lowercase and as a str) .
     """

    assert snapid is not None

    # snapid should usually be str, if its read from command line or arrived from some other source
    # it could be unicode. either case it must only be hex encoded text.
    assert isinstance(snapid, str) or isinstance(snapid, unicode)

    legal_chars = set("0123456789abcdefABCDEF")

    chars = set(snapid)

    # there should be no characters left after we took out 0-9 a-f A-F
    assert 0 == len(chars - legal_chars)

    return str(snapid.lower())



def check_snapinfo_dict(snapinfo):
    """ assert that a snapshot is in a valid shape and form. (i.e. have the necessary keys ....)
    """

    assert isinstance(snapinfo, dict)

    assert 'root' in snapinfo, "Snapshot json does not contain all expected keys."
    assert 'msg' in snapinfo, "Snapshot json does not contain all expected keys."
    assert 'author_name' in snapinfo, "Snapshot json does not contain all expected keys."
    assert 'author_email' in snapinfo, "Snapshot json does not contain all expected keys."




if '__main__' == __name__:

    from uvs_errors import *

    try:
        raise UVSError('Hi')
    except UVSError as e:
        print str(e)
        print e.message
        print e.args
