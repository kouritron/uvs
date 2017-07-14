

import sqlite3
import os

import log



class DAO(object):

    def __init__(self, db_file_path):
        super(DAO, self).__init__()

        assert db_file_path is not None
        assert isinstance(db_file_path, str) or isinstance(db_file_path, unicode) or isinstance(db_file_path, bytes)
        assert not os.path.isdir(db_file_path)

        log.dao("Initializing new sqlite DAO, db file path:" + str(db_file_path))

        self._connection = sqlite3.connect(db_file_path)
        #self._connection = sqlite3.connect(':memory:')

        log.dao("created sqlite connection: " + repr(self._connection))


    def create_empty_tables(self):
        """ Create empty Tables in the sqlite database to which this object is connected to.. """

        log.dao("create_empty_tables() called on Sqlite DAO.")

        cursor = self._connection.cursor()

        # sqlite data types of interest are most likely just these:
        # TEXT. The value is a text string, stored using the database encoding (UTF-8, UTF-16BE or UTF-16LE).
        # BLOB. The value is a blob of data, stored exactly as it was input.


        # clear table in case previous records are there.
        cursor.execute(""" DROP TABLE IF EXISTS snapshots; """)
        cursor.execute(""" DROP TABLE IF EXISTS trees; """)
        cursor.execute(""" DROP TABLE IF EXISTS files; """)
        cursor.execute(""" DROP TABLE IF EXISTS segments; """)
        cursor.execute(""" DROP TABLE IF EXISTS public; """)

        # IMPORTANT: never use str concat (+) or python format specifiers (old style or new) to
        # put values into queries, neglecting this will open u up to SQL injection attack. Instead do this
        # cursor.execute(""" SELECT * FROM students WHERE gpa > ? """, (2.5, )  )
        cursor.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        snapid TEXT PRIMARY KEY NOT NULL,
        snapinfo_json BLOB NOT NULL ); """)

        # Trees table, i dont believe table names are case sensitive.
        # tid is the uvs fp the tree contents
        # tree is json that describes whats in this tree.
        cursor.execute("""CREATE TABLE IF NOT EXISTS trees (
        tid TEXT PRIMARY KEY NOT NULL,
        tree_json BLOB NOT NULL ); """)

        # fid is the uvs fp of the file content
        # finfo is json of information about this fid. Most important part is a list of segments that make up this file
        # dereference the segments table to find the contents of this file.
        cursor.execute("""CREATE TABLE IF NOT EXISTS files (
        fid TEXT PRIMARY KEY NOT NULL,
        finfo_json BLOB NOT NULL ); """)


        # sgid is the uvsfp of this segment
        cursor.execute("""CREATE TABLE IF NOT EXISTS segments (
        sgid TEXT PRIMARY KEY NOT NULL,
        segment BLOB NOT NULL ); """)


        cursor.execute("""CREATE TABLE IF NOT EXISTS repo_refs (
        references_json BLOB PRIMARY KEY NOT NULL ); """)


        # every repo has single public record, this is just a json record with some public info about this repo
        # (like public name, salt, optional owner email if needed, ....)
        cursor.execute("""CREATE TABLE IF NOT EXISTS public (
        public_record BLOB PRIMARY KEY NOT NULL,
        public_record_mac TEXT NOT NULL ); """)


        # close the transaction
        self._connection.commit()


    def set_repo_public_doc(self, public_doc, public_doc_mac_tag):
        """ Every repository has exactly one record called public record (or public document)
        the public record is not encrypted (has no confidentiality protection), but is MACed (integrity protected)
        an attacker can always see the public record, but can not forge one without failing the MAC, without knowing
        the private password of this repository.

        This method sets that record to the supplied argument, overwriting a previous existing one, if needed.
        """

        log.dao("set_repo_public_doc() called on Sqlite DAO.")

        assert public_doc is not None
        assert public_doc_mac_tag is not None
        assert isinstance(public_doc, str) or isinstance(public_doc, bytes)
        assert isinstance(public_doc_mac_tag, str) or isinstance(public_doc_mac_tag, bytes)


        cursor = self._connection.cursor()

        # there can only be one public doc.
        cursor.execute(""" DELETE FROM public; """)

        # sqlite blobs require buffer objects
        cursor.execute(""" INSERT INTO public(public_record, public_record_mac) VALUES (?, ?);""",
                       (buffer(public_doc), public_doc_mac_tag))

        # Done public record is set
        self._connection.commit()


    def get_repo_public_doc(self):
        """ Retrieve and return this repository's public document and the MAC tag of the public document as
        a 2-tuple (public record, mac_tag)  """

        log.dao("get_repo_public_doc() called on Sqlite DAO.")

        cursor = self._connection.cursor()

        # get the data back
        cursor.execute(""" SELECT * FROM public; """)

        # close the transaction
        self._connection.commit()


        # fetchone returns a tuple of buffers for the blob col and text for the text col
        query_result = cursor.fetchone()

        if query_result is None:
            log.dao("Sqlite DAO Could not find an existing public record.")
            return None

        log.daov("query_result: " + repr(query_result))

        public_record = bytes(query_result[0])
        log.dao("public record buffer, cast to bytes: " + str(public_record))

        pub_rec_mac_tag = query_result[1]
        log.dao("public record mac tag: " + str(pub_rec_mac_tag))

        return public_record, pub_rec_mac_tag



    def set_repo_references_doc(self, ref_doc):
        """ Every repository has exactly one record called references record (or references document)
        This method sets that record to the supplied argument, overwriting a previous existing one, if needed.
        """

        log.dao("set_repo_references_doc() called on Sqlite DAO.")

        assert ref_doc is not None
        assert isinstance(ref_doc, str) or isinstance(ref_doc, bytes)


        cursor = self._connection.cursor()

        # there can only be one public doc.
        cursor.execute(""" DELETE FROM repo_refs; """)

        # sqlite blobs require buffer objects
        cursor.execute(""" INSERT INTO repo_refs(references_json) VALUES (?);""", (buffer(ref_doc), ))

        # Done references doc is set
        self._connection.commit()


    def get_repo_references_doc(self):
        """ Every repository has exactly one record called references record (or references document)
        Retrieve and return that document.
        """

        log.dao("get_repo_references_doc() called on Sqlite DAO.")

        cursor = self._connection.cursor()

        # get the data back
        cursor.execute(""" SELECT * FROM repo_refs; """)

        # close the transaction
        self._connection.commit()


        # fetchone returns a tuple of buffers for the blob col and text for the text col
        query_result = cursor.fetchone()

        if query_result is None:
            log.dao("Sqlite DAO Could not find an existing references record.")
            return None

        log.daov("query_result: " + repr(query_result))

        ref_doc = bytes(query_result[0])
        log.dao("references record buffer, cast to bytes: " + str(ref_doc))


        return ref_doc



    def add_segment(self, sgid, segment_bytes):
        """ Given a new segment as a (sgid, bytes) pair, add this segment to the segments table, if it doesnt
        Already exist. Do nothing if sgid is already present in the data store. 
        For that reason this call is idempotent.
        Normally in uvs segment_bytes is in cipher text (except perhaps in debug mode). Its not the Data Store's
        responsibility to handle encryption/decryption, I will store and retrieve whatever you give me.
        """

        log.dao("add_segment() called on Sqlite DAO. sgid: " + str(sgid) + " segment_bytes: " + repr(segment_bytes))


        assert sgid is not None
        assert isinstance(sgid, str) or isinstance(sgid, bytes)
        assert segment_bytes is not None
        assert isinstance(segment_bytes, str) or isinstance(segment_bytes, bytes)

        cursor = self._connection.cursor()

        cursor.execute("INSERT OR IGNORE INTO segments(sgid, segment) VALUES (?, ? );", (sgid, buffer(segment_bytes)))

        self._connection.commit()




    def get_segment(self, sgid):
        """Given a sgid, find and return the value associated with that key from the segments table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_segment() called on Sqlite DAO. sgid: " + str(sgid) + " -- type(sgid): " + str(type(sgid)))

        assert sgid is not None
        assert isinstance(sgid, str) or isinstance(sgid, bytes) or isinstance(sgid, unicode)

        cursor = self._connection.cursor()

        cursor.execute("SELECT segment FROM  segments WHERE sgid == ?;", (sgid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if query_result is None:
            log.dao("Sqlite DAO Could not find segment with sgid: " + str(sgid))
            return None

        first_row = bytes(query_result[0])
        log.daov("Found segment, cast to bytes look like this: " + str(first_row))

        return first_row



    def add_file(self, fid, finfo):
        """Given a new file as a (fid, finfo_bytes) pair, add this file to the files table, if fid doesnt
        Already exist. Do nothing if fid is already present in the data store. For this reason this call is idempotent.

        Normally in uvs finfo is in cipher text (as str or bytes) (except perhaps in debug mode).
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_file() called on Sqlite DAO. fid: " + str(fid) + " finfo: " + str(finfo))

        assert fid is not None
        assert finfo is not None
        assert isinstance(fid, str) or isinstance(fid, bytes)
        assert isinstance(finfo, str) or isinstance(finfo, bytes)

        cursor = self._connection.cursor()

        cursor.execute("INSERT OR IGNORE INTO files(fid, finfo_json) VALUES (?, ? );", (fid, buffer(finfo)))

        # Done close the transaction
        self._connection.commit()


    def get_file(self, fid):
        """Given a fid, find and return the value associated with that key from the files table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_file() called on Sqlite DAO. tid: " + str(fid) + " -- type(fid): " + str(type(fid)))

        assert fid is not None
        assert isinstance(fid, str) or isinstance(fid, bytes) or isinstance(fid, unicode)

        cursor = self._connection.cursor()

        cursor.execute("SELECT finfo_json FROM  files WHERE fid == ?;", (fid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if query_result is None:
            log.dao("Sqlite DAO Could not find file with fid: " + str(fid))
            return None

        first_row = bytes(query_result[0])
        log.dao("Found file, cast to bytes look like this: " + str(first_row))

        return first_row



    def add_tree(self, tid, tree_info):
        """Given a new tree as a (tid, tree info bytes) pair, add this tree to the trees table, if it doesnt already 
        exist. Do nothing if tid is already present in the data store. For this reason this call is idempotent.

        Normally in uvs tree_info is in cipher text (as str or bytes) (except perhaps in debug mode).
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_tree() called on Sqlite DAO. tid: " + str(tid) + " tree_info: " + str(tree_info))

        assert tree_info is not None
        assert isinstance(tree_info, str) or isinstance(tree_info, bytes)
        assert tid is not None
        assert isinstance(tid, str) or isinstance(tid, bytes)

        cursor = self._connection.cursor()

        cursor.execute("INSERT OR IGNORE INTO trees(tid, tree_json) VALUES (?, ? );", (tid, buffer(tree_info)))

        # Done close the transaction
        self._connection.commit()


    def get_tree(self, tid):
        """Given a tid, find and return the value associated with that key from the trees table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_tree() called on Sqlite DAO. tid: " + str(tid) + " -- type(tid): " + str(type(tid)))

        assert tid is not None
        assert isinstance(tid, str) or isinstance(tid, bytes) or isinstance(tid, unicode)

        cursor = self._connection.cursor()

        cursor.execute("SELECT tree_json FROM trees WHERE tid == ?;", (tid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if query_result is None:
            log.dao("Sqlite DAO Could not find tree with tid: " + str(tid))
            return None

        first_row = bytes(query_result[0])
        log.dao("Found tree, cast to bytes look like this: " + str(first_row))

        return first_row


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

        log.dao("add_snapshot() called on Sqlite DAO. snapid: " + str(snapid) + " snapshot: " + str(snapshot))

        assert snapid is not None
        assert snapshot is not None
        assert isinstance(snapid, str) or isinstance(snapid, bytes)
        assert isinstance(snapshot, str) or isinstance(snapshot, bytes)

        cursor = self._connection.cursor()

        cursor.execute("INSERT OR IGNORE INTO snapshots(snapid, snapinfo_json) VALUES (?, ? );",
                       (snapid, buffer(snapshot)))


        # Done close the transaction
        self._connection.commit()


    def get_snapshot(self, snapid):
        """Given a snapshot id, find and return the value associated with that key from the snapshot table.
        returns None, if no record with that key was found in the table.
        
        """

        log.dao("get_snapshot() called on Sqlite DAO. Snapid: " + str(snapid) + " --type(snapid): " + str(type(snapid)))

        assert snapid is not None
        assert isinstance(snapid, str) or isinstance(snapid, bytes) or isinstance(snapid, unicode)

        cursor = self._connection.cursor()

        cursor.execute("SELECT snapinfo_json FROM snapshots WHERE snapid == ?;", (snapid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if query_result is None:
            log.dao("Sqlite DAO Could not find snapshot with snapid: " + str(snapid))
            return None

        first_row = bytes(query_result[0])
        log.daov("Found snapshot, cast to bytes look like this: " + str(first_row))

        return first_row

    def get_all_snapshots(self):
        """ Find and return all snapshots a list of (snapid, snapinfo ciphertext)
        returns empty list if no snapshots were found
        """

        log.dao("get_all_snapshots() called on Sqlite DAO.")

        cursor = self._connection.cursor()

        cursor.execute("SELECT snapid, snapinfo_json FROM snapshots;")

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of tuples
        query_result = cursor.fetchall()

        log.daov("query result: " + repr(query_result))

        # i should get empty list [] if no records found.
        assert query_result is not None, "Hmmm querying all snapshots returned None, this should not have happened."

        return query_result


#
# if "__main__" == __name__:
#
#     dao = DAO()
#     dao.set_repo_public_doc('hello')
#     dao.get_repo_public_doc()
