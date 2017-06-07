

import sqlite3
import os
import errno

import log
from cryptmanager import get_uvs_fingerprint_size





class DAO(object):

    def __init__(self):
        super(DAO, self).__init__()

        log.dao("++++++++++++++++++++++++++++++++ Init called on SQLite DAO.")

        self._dbfile_pathname = "../uvs.db"

        #self._drop_db()

        self._connection = sqlite3.connect(self._dbfile_pathname)
        #self._connection = sqlite3.connect(':memory:')

        log.dao("created sqlite connection: " + repr(self._connection))

        #self._reset_uvs_tables()

        self._create_schema()


    def _drop_db(self):
        """ Delete the database file using os.remove """

        log.dao("_drop_db() called on SQLite DAO.")

        # delete the file, suppress "file not found" exception, re-raise all other exceptions
        try:
            os.remove(self._dbfile_pathname)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise



    def _reset_uvs_tables(self):
        """ Clears all uvs tables except the public record. """

        log.dao("_reset_uvs_tables() called on SQLite DAO.")

        cursor = self._connection.cursor()

        # clear table in case previous records are there.
        cursor.execute(""" DROP TABLE IF EXISTS snapshots; """)
        cursor.execute(""" DROP TABLE IF EXISTS trees; """)
        cursor.execute(""" DROP TABLE IF EXISTS files; """)
        cursor.execute(""" DROP TABLE IF EXISTS segments; """)

        self._connection.commit()


    def _create_schema(self):
        """ Create empty Tables in the sqlite database to which this object is connected to.. """

        log.dao("_create_schema() called on Sqlite DAO.")

        cursor = self._connection.cursor()

        # sqlite data types of interest are most likely just these:
        # TEXT. The value is a text string, stored using the database encoding (UTF-8, UTF-16BE or UTF-16LE).
        # BLOB. The value is a blob of data, stored exactly as it was input.

        # IMPORTANT: never use str concat (+) or python format specifiers (old style or new) to
        # put values into queries, neglecting this will open u up to SQL injection attack. Instead do this
        # cursor.execute(""" SELECT * FROM students WHERE gpa > ? """, (2.5, )  )
        cursor.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        snapid TEXT PRIMARY KEY NOT NULL,
        snapinfo_json BLOB NOT NULL ); """ )


        # Trees table, i dont believe table names are case sensitive.
        # tid is the uvs fp the tree contents
        # tree is json that describes whats in this tree.
        cursor.execute("""CREATE TABLE IF NOT EXISTS trees (
        tid TEXT PRIMARY KEY NOT NULL,
        tree_json BLOB NOT NULL ); """ )


        # fid is the uvs fp of the file content
        # finfo is json of information about this fid. Most important part is a list of segments that make up this file
        # dereference the segments table to find the contents of this file.
        cursor.execute("""CREATE TABLE IF NOT EXISTS files (
        fid TEXT PRIMARY KEY NOT NULL,
        finfo_json BLOB NOT NULL ); """ )


        # sgid is the uvsfp of this segment
        cursor.execute("""CREATE TABLE IF NOT EXISTS segments (
        sgid TEXT PRIMARY KEY NOT NULL,
        segment BLOB NOT NULL ); """ )


        # every repo has single public record, this is just a json record with some public info about this repo
        # (like public name, salt, optional owner email if needed, ....)
        cursor.execute("""CREATE TABLE IF NOT EXISTS public (
        public_json BLOB PRIMARY KEY NOT NULL ); """ )

        # close the transaction
        self._connection.commit()


    def set_repo_public_doc(self, public_doc):
        """ Every repository has exactly one record called public doc.
        This method sets that record to the supplied argument, overwriting a previous existing one, if needed.
        """

        log.dao("set_repo_public_doc() called on Sqlite DAO.")

        assert None != public_doc
        assert isinstance(public_doc, str) or isinstance(public_doc, bytes)


        cursor = self._connection.cursor()

        # there can only be one public doc.
        cursor.execute(""" DELETE FROM public; """)

        # sqlite blobs require buffer objects
        cursor.execute(""" INSERT INTO public(public_json) VALUES (?);""", (buffer(public_doc),) )

        # Done public record is set
        self._connection.commit()


    def get_repo_public_doc(self):
        """ Retrieve and return this repository's public document. """

        log.dao("get_repo_public_doc() called on Sqlite DAO.")

        cursor = self._connection.cursor()

        # get the data back
        cursor.execute(""" SELECT * FROM public; """)

        # close the transaction
        self._connection.commit()


        # fetchone returns a tuple of buffers, (in this case just one buffer)
        query_result = cursor.fetchone()

        if None == query_result:
            log.dao("Sqlite DAO Could not find an existing public record.")
            return None

        first_row = bytes(query_result[0])
        log.daov("Got back public record buffer, cast to bytes look like this: " + str(first_row))

        return  first_row


    def add_segment(self, sgid, segment_bytes):
        """ Given a new segment as a (sgid, bytes) pair, add this segment to the segments table, if it doesnt
        Already exist. Do nothing if sgid is already present in the data store. 
        For that reason this call is idempotent.
        Normally in uvs segment_bytes is in ciphertext (except perhaps in debug mode). Its not the Data Store's 
        responsibility to handle encryption/decryption, I will store and retrieve whatever you give me.
        """

        log.dao("add_segment() called on Sqlite DAO. sgid: " + str(sgid) + " segment_bytes: " + repr(segment_bytes))


        assert sgid != None
        assert isinstance(sgid, str) or isinstance(sgid, bytes)
        assert segment_bytes != None
        assert isinstance(segment_bytes, str) or isinstance(segment_bytes, bytes)

        cursor = self._connection.cursor()

        cursor.execute("INSERT OR IGNORE INTO segments(sgid, segment) VALUES (?, ? );", (sgid, buffer(segment_bytes)))

        self._connection.commit()




    def get_segment(self, sgid):
        """Given a sgid, find and return the value associated with that key from the segments table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_segment() called on Sqlite DAO. sgid: " + str(sgid))

        assert None != sgid
        assert isinstance(sgid, str) or isinstance(sgid, bytes) or isinstance(sgid, unicode), \
            "tid is not str/bytes/unicode, type(tid): " + str(type(sgid))

        cursor = self._connection.cursor()

        cursor.execute("SELECT segment FROM  segments WHERE sgid == ?;", (sgid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if None == query_result:
            log.dao("Sqlite DAO Could not find segment with sgid: " + str(sgid))
            return None

        first_row = bytes(query_result[0])
        log.daov("Found segment, cast to bytes look like this: " + str(first_row))

        return first_row



    def add_file(self, fid, finfo):
        """Given a new file as a (fid, finfo_bytes) pair, add this file to the files table, if fid doesnt
        Already exist. Do nothing if fid is already present in the data store. For this reason this call is idempotent.

        Normally in uvs finfo is in ciphertext (as str or bytes) (except perhaps in debug mode). 
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_file() called on Sqlite DAO. fid: " + str(fid) + " finfo: " + str(finfo))

        assert None != fid
        assert None != finfo
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

        log.dao("get_file() called on Sqlite DAO. tid: " + str(fid))

        assert None != fid
        assert isinstance(fid, str) or isinstance(fid, bytes) or isinstance(fid, unicode), \
            "tid is not str/bytes/unicode, type(tid): " + str(type(fid))

        cursor = self._connection.cursor()

        cursor.execute("SELECT finfo_json FROM  files WHERE fid == ?;", (fid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if None == query_result:
            log.dao("Sqlite DAO Could not find file with fid: " + str(fid))
            return None

        first_row = bytes(query_result[0])
        log.dao("Found file, cast to bytes look like this: " + str(first_row))

        return first_row



    def add_tree(self, tid, tree_info):
        """Given a new tree as a (tid, tree info bytes) pair, add this tree to the trees table, if it doesnt already 
        exist. Do nothing if tid is already present in the data store. For this reason this call is idempotent.

        Normally in uvs tree_info is in ciphertext (as str or bytes) (except perhaps in debug mode). 
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_tree() called on Sqlite DAO. tid: " + str(tid) + " tree_info: " + str(tree_info))

        assert None != tree_info
        assert isinstance(tree_info, str) or isinstance(tree_info, bytes)
        assert None != tid
        assert isinstance(tid, str) or isinstance(tid, bytes)

        cursor = self._connection.cursor()

        cursor.execute("INSERT OR IGNORE INTO trees(tid, tree_json) VALUES (?, ? );", (tid, buffer(tree_info)))

        # Done close the transaction
        self._connection.commit()


    def get_tree(self, tid):
        """Given a tid, find and return the value associated with that key from the trees table.
        returns None, if no record with that key was found in the table.
        """

        log.dao("get_tree() called on Sqlite DAO. tid: " + str(tid))

        assert None != tid
        assert isinstance(tid, str) or isinstance(tid, bytes) or isinstance(tid, unicode), \
            "tid is not str/bytes/unicode, type(tid): " + str(type(tid))

        cursor = self._connection.cursor()

        cursor.execute("SELECT tree_json FROM trees WHERE tid == ?;", (tid,))

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if None == query_result:
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

        Normally in uvs snapshot is in ciphertext (as str or bytes) (except perhaps in debug mode). 
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_snapshot() called on Sqlite DAO. snapid: " + str(snapid) + " snapshot: " + str(snapshot))

        assert None != snapid
        assert None != snapshot
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

        log.dao("get_snapshot() called on Sqlite DAO. snapid: " + str(snapid))

        assert None != snapid
        assert isinstance(snapid, str) or isinstance(snapid, bytes)

        cursor = self._connection.cursor()

        cursor.execute("SELECT snapinfo_json FROM snapshots WHERE snapid == ?;", (snapid,) )

        # close the transaction
        self._connection.commit()

        # fetchone returns a tuple of buffers
        query_result = cursor.fetchone()

        log.daov("query result: " + repr(query_result))

        if None == query_result:
            log.dao("Sqlite DAO Could not find snapshot with snapid: " + str(snapid))
            return None

        first_row = bytes(query_result[0])
        log.daov("Found snapshot, cast to bytes look like this: " + str(first_row))

        return first_row



#
# if "__main__" == __name__:
#
#     dao = DAO()
#     dao.set_repo_public_doc('hello')
#     dao.get_repo_public_doc()
