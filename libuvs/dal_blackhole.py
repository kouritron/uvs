
# Blackhole DAO is the uvs Data Access Object that acts similar to
# /dev/null or the zero register in the CPU. if you put things in it they will be discarded.
# if you read from it, you will get back None.

import log


class DAO(object):

    def __init__(self):
        super(DAO, self).__init__()

        log.dao("Initializing new Blackhole DAO.")


    def create_empty_tables(self):
        """ Create empty Tables in the sqlite database to which this object is connected to.. """

        log.dao("create_empty_tables() called on Blackhole DAO.")


    def set_repo_public_doc(self, public_doc, public_doc_mac_tag):
        """ Every repository has exactly one record called public record (or public document)
        the public record is not encrypted (has no confidentiality protection), but is MACed (integrity protected)
        an attacker can always see the public record, but can not forge one without failing the MAC, without knowing
        the private password of this repository.

        This method sets that record to the supplied argument, overwriting a previous existing one, if needed.
        """

        log.dao("set_repo_public_doc() called on Blackhole DAO.")

        assert public_doc is not None
        assert public_doc_mac_tag is not None
        assert isinstance(public_doc, str) or isinstance(public_doc, bytes)
        assert isinstance(public_doc_mac_tag, str) or isinstance(public_doc_mac_tag, bytes)


    def get_repo_public_doc(self):
        """ Retrieve and return this repository's public document and the MAC tag of the public document as
        a 2-tuple (public record, mac_tag)  """

        log.dao("get_repo_public_doc() called on Blackhole DAO.")

        return None, None


    def update_ref_doc(self, ref_doc_id, ref_doc):
        """ set or update the "references document" for the given ref_doc_id.
        """

        log.dao("update_repo_references_doc() called on Blackhole DAO. ref_doc_id: " + str(ref_doc_id))
        log.daov("Tossing ref_doc into blackhole, ref_doc: " + str(ref_doc))

        assert ref_doc is not None
        assert ref_doc_id is not None
        assert isinstance(ref_doc, str) or isinstance(ref_doc, bytes)
        assert isinstance(ref_doc_id, str) or isinstance(ref_doc_id, bytes)


    def get_ref_doc(self, ref_doc_id):
        """ Every repository has exactly one record called references record (or references document)
        Retrieve and return that document.
        """

        log.dao("get_ref_doc() called on Blackhole DAO.")

        assert ref_doc_id is not None
        assert isinstance(ref_doc_id, str) or isinstance(ref_doc_id, bytes)

        return None


    def add_segment(self, sgid, segment_bytes):
        """ Given a new segment as a (sgid, bytes) pair, add this segment to the segments table, if it doesnt
        Already exist. Do nothing if sgid is already present in the data store.
        For that reason this call is idempotent.
        Normally in uvs segment_bytes is in cipher text (except perhaps in debug mode). Its not the Data Store's
        responsibility to handle encryption/decryption, I will store and retrieve whatever you give me.
        """

        log.dao("add_segment() called on Blackhole DAO. sgid: " + str(sgid) + " segment_bytes: " + repr(segment_bytes))

        assert sgid is not None
        assert isinstance(sgid, str) or isinstance(sgid, bytes)
        assert segment_bytes is not None
        assert isinstance(segment_bytes, str) or isinstance(segment_bytes, bytes)


    def get_segment(self, sgid):
        """Given a sgid, find and return the value associated with that key from the segments table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_segment() called on Blackhole DAO. sgid: " + str(sgid) + " -- type(sgid): " + str(type(sgid)))

        assert sgid is not None
        assert isinstance(sgid, str) or isinstance(sgid, bytes) or isinstance(sgid, unicode)

        return None


    def add_file(self, fid, finfo):
        """Given a new file as a (fid, finfo_bytes) pair, add this file to the files table, if fid doesnt
        Already exist. Do nothing if fid is already present in the data store. For this reason this call is idempotent.

        Normally in uvs finfo is in cipher text (as str or bytes) (except perhaps in debug mode).
        Its not the Data Store's responsibility to handle encryption/decryption.
        I will store and retrieve whatever you give me.
        """

        log.dao("add_file() called on Blackhole DAO. fid: " + str(fid) + " finfo: " + str(finfo))

        assert fid is not None
        assert finfo is not None
        assert isinstance(fid, str) or isinstance(fid, bytes)
        assert isinstance(finfo, str) or isinstance(finfo, bytes)


    def get_file(self, fid):
        """Given a fid, find and return the value associated with that key from the files table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_file() called on Blackhole DAO. tid: " + str(fid) + " -- type(fid): " + str(type(fid)))

        assert fid is not None
        assert isinstance(fid, str) or isinstance(fid, bytes) or isinstance(fid, unicode)

        return None



    def add_tree(self, tid, tree_info):
        """Given a new tree as a (tid, tree info bytes) pair, add this tree to the trees table, if it doesnt already
        exist. Do nothing if tid is already present in the data store. For this reason this call is idempotent.

        Normally in uvs tree_info is in cipher text (as str or bytes) (except perhaps in debug mode).
        Its not the Data Store's responsibility to handle encryption/decryption.
        I will store and retrieve whatever you give me.
        """

        log.dao("add_tree() called on Blackhole DAO. tid: " + str(tid) + " tree_info: " + str(tree_info))

        assert tree_info is not None
        assert isinstance(tree_info, str) or isinstance(tree_info, bytes)
        assert tid is not None
        assert isinstance(tid, str) or isinstance(tid, bytes)


    def get_tree(self, tid):
        """Given a tid, find and return the value associated with that key from the trees table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_tree() called on Blackhole DAO. tid: " + str(tid) + " -- type(tid): " + str(type(tid)))

        assert tid is not None
        assert isinstance(tid, str) or isinstance(tid, bytes) or isinstance(tid, unicode)

        return None


    def add_snapshot(self, snapid, snapshot):
        """Given a new snapshot (commit in other vcs) as a (snapid, snapshot_bytes) pair,
         add this snapshot to the snapshots table, if it doesnt already exist. Do nothing if snapid is
         already present in the data store. For this reason this call is idempotent.

         new snapshots should never have snapid that collides with an existing one in the repo. snapids are
         random unique identifiers created every time user makes a new snapshot (commit)

        Normally in uvs snapshot is in cipher text (as str or bytes) (except perhaps in debug mode).
        Its not the Data Store's responsibility to handle encryption/decryption.
        I will store and retrieve whatever you give me.
        """

        log.dao("add_snapshot() called on Blackhole DAO. snapid: " + str(snapid) + " snapshot: " + str(snapshot))

        assert snapid is not None
        assert snapshot is not None
        assert isinstance(snapid, str) or isinstance(snapid, bytes) or isinstance(snapid, unicode)
        assert isinstance(snapshot, str) or isinstance(snapshot, bytes) or isinstance(snapid, unicode)


    def get_snapshot(self, snapid):
        """Given a snapshot id, find and return the value associated with that key from the snapshot table.
        returns None, if no record with that key was found in the table.

        """

        log.dao("get_snapshot() called on Blackhole DAO. snapid: " + str(snapid) + " -- type(snapid): "
                + str(type(snapid)))

        assert snapid is not None
        assert isinstance(snapid, str) or isinstance(snapid, bytes) or isinstance(snapid, unicode)

        return None

    def get_all_snapshots(self):
        """ Find and return all snapshots a list of (snapid, snapinfo ciphertext)
        returns empty list if no snapshots were found
        """

        log.dao("get_all_snapshots() called on Blackhole DAO.")

        return None


    def get_snapshots_count(self):
        """ Find and return the number of snapshots that exist in this repository.
        this is the total number of records found in the snapshots table, the total may include decoy snapshots
        if we wanted to support that.

        this will return 0 if no snapshots exist in this repository.
        """

        log.dao("get_snapshots_count() called on Blackhole DAO.")

        return 0


#
# if "__main__" == __name__:
#
#     dao = DAO()
#     dao.set_repo_public_doc('hello', 'dum tag')
#     print dao.get_repo_public_doc()
