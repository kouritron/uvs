

import psycopg2


import log
from cryptmanager import get_uvs_fingerprint_size



class DAO(object):

    def __init__(self):
        super(DAO, self).__init__()

        log.dao("++++++++++++++++++++++++++++++++ Init called on Postgres DAO.")

        # TODO remove the hard codes or at least move to system defaults.
        # like there would be a default backend there and a dict of info required to use it.
        self._connection = psycopg2.connect(user='uvsusr1', database='uvsdb', password='IwantRISCVryzen8761230110',
                                            host='192.168.24.120', port=5432)

        log.dao("created psql connection: " + str(self._connection))

        self._create_schema()


    def _drop_schema(self):
        """ Lose all information the in the uvs database. """

        log.dao("_drop_schema() called on Postgres DAO.")

        # use this;
        cursor = self._connection.cursor()
        cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        self._connection.commit()

    def _clear_tables(self):
        """ Clear tables without dropping schema. """

        log.dao("_clear_tables() called on Postgres DAO.")

        cursor = self._connection.cursor()

        # clear table in case previous records are there.
        # cursor.execute(""" DELETE FROM uvs_schema.public; """)
        cursor.execute(""" DELETE FROM uvs_schema.snapshots; """)
        cursor.execute(""" DELETE FROM uvs_schema.trees; """)
        cursor.execute(""" DELETE FROM uvs_schema.files; """)
        cursor.execute(""" DELETE FROM uvs_schema.segments; """)

        self._connection.commit()



    def _create_schema(self):
        """ Create empty Tables in the Postgres database to which this object is connected to.. """

        log.dao("_create_schema() called on Postgres DAO.")

        cursor = self._connection.cursor()

        # TODO if not exists maybe??

        #cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        self._clear_tables()

        cursor.execute(""" CREATE SCHEMA IF NOT EXISTS uvs_schema; """)
        cursor.execute(""" SET search_path TO uvs_schema; """)

        fp_size = get_uvs_fingerprint_size()
        log.v("fp size is: " + str(fp_size) + " bytes")

        # wee need two symbols for each byte in hex encoding so
        fp_size_hex_enc = fp_size * 2



        # postgres text data types:
        # varchar(n)  ---> variable len with limit
        # char(n)     ---> fixed len blank padded
        # text        ---> variable unlimited len

        # IMPORTANT: never use str concat (+) or python format specifiers (old style or new) to
        # put values into queries, neglecting this will open u up to SQL injection attack. Instead
        # pass a tuple or named key value pairs to psycopg2 and it will do the right thing.
        # tuple example:            execute( "%s", (132,) )
        # named k,v pairs example:  execute( "%(tickets_left)s", {tickets_left: 132} )
        cursor.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        snapid char(%(fp_size)s) NOT NULL,
        snapinfo_json BYTEA,
        PRIMARY KEY (snapid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # Trees table, i dont believe postgres table names are case sensitive.
        # tid is the uvs fp the tree contents
        # tree is json that describes whats in this tree.
        cursor.execute("""CREATE TABLE IF NOT EXISTS trees (
        tid char(%(fp_size)s) NOT NULL,
        tree_json BYTEA,
        PRIMARY KEY (tid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # BYTEA type has 1 GB max size limit in postgres
        # fid is the uvs fp of the file content
        # finfo is json of information about this fid. Most important part is a list of segments that make up this file
        # dereference the segments table to find the contents of this file.
        cursor.execute("""CREATE TABLE IF NOT EXISTS files (
        fid char(%(fp_size)s) NOT NULL,
        finfo_json BYTEA,
        PRIMARY KEY (fid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # BYTEA type has 1 GB max size limit in postgres
        # sgid is the uvsfp of this segment
        cursor.execute("""CREATE TABLE IF NOT EXISTS segments (
        sgid char(%(fp_size)s) NOT NULL,
        segment BYTEA,
        PRIMARY KEY (sgid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # just a json record with some public info about this repo
        # (like public name, salt, optional owner email if needed, ....)
        cursor.execute("""CREATE TABLE IF NOT EXISTS public (
        public_json BYTEA
        );
        """ )

        # this will commit the transaction right away. without this call, changes will be lost entirely.
        # Note after calling close on this connection, all cursors derived from it will fail to execute queries.
        # also all cursors derived from the same connection, see each other's changes immediately (are not isolated)
        # multiple connection objects may or may not see each others changes immediately (check ISOLATION LEVEL)
        self._connection.commit()


    def set_repo_public_doc(self, public_doc):
        """ Every repository has exactly one record called public doc.
        This method sets that record to the supplied argument, overwriting a previous existing one, if needed.
        """

        log.dao("set_repo_public_doc() called on Postgres DAO.")

        assert None != public_doc
        assert isinstance(public_doc, str) or isinstance(public_doc, bytes)


        cursor = self._connection.cursor()

        # there can only be one public doc.
        cursor.execute(""" DELETE FROM uvs_schema.public; """)

        cursor.execute(""" INSERT INTO uvs_schema.public(public_json) VALUES (
         %(serialized)s    );""", {'serialized': psycopg2.Binary(public_doc)})

        # Done public record is set
        self._connection.commit()


    def get_repo_public_doc(self):
        """ Retrieve and return this repository's public document. """

        log.dao("get_repo_public_doc() called on Postgres DAO.")

        cursor = self._connection.cursor()

        # get the data back
        cursor.execute(""" SELECT * FROM uvs_schema.public; """)

        # close the transaction
        self._connection.commit()


        # fetchone returns a tuple, and inside the tuple you will find buffer type objects
        query_result = cursor.fetchone()
        if None == query_result:
            return None

        first_row = query_result[0]
        log.vvvv("Got back public json from db, first row type: " + str(type(first_row)))
        log.vvvv('First row as str: ' + str(first_row))

        public_doc_from_db = str(first_row)

        return  public_doc_from_db


    def add_segment(self, sgid, segment_bytes):
        """ Given a new segment as a (sgid, bytes) pair, add this segment to the segments table, if it doesnt
        Already exist. Do nothing if sgid is already present in the data store. 
        For that reason this call is idempotent.
        Normally in uvs segment_bytes is in ciphertext (except perhaps in debug mode). Its not the Data Store's 
        responsibility to handle encryption/decryption, I will store and retrieve whatever you give me.
        """

        log.dao("add_segment() called on Postgres DAO. sgid: " + str(sgid) + " segment_bytes: " + repr(segment_bytes))


        assert sgid != None
        assert isinstance(sgid, str) or isinstance(sgid, bytes)
        assert segment_bytes != None
        assert isinstance(segment_bytes, str) or isinstance(segment_bytes, bytes)

        cursor = self._connection.cursor()

        # ON CONFLICT DO NOTHING was added to postgres as of version 9.5 (google upsert for more info)
        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                       ON CONFLICT DO NOTHING ;""", {'sgid': sgid, 'segment': psycopg2.Binary(segment_bytes)})

        self._connection.commit()


    def add_file(self, fid, finfo):
        """Given a new file as a (fid, finfo) pair, add this file to the files table, if it doesnt
        Already exist. Do nothing if fid is already present in the data store. For this reason this call is idempotent.
        
        Normally in uvs finfo is in ciphertext (as str or bytes) (except perhaps in debug mode). 
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_file() called on Postgres DAO. fid: " + str(fid) + " finfo: " + str(finfo))

        assert None != fid
        assert None != finfo
        assert isinstance(fid, str) or isinstance(fid, bytes)
        assert isinstance(finfo, str) or isinstance(finfo, bytes)

        cursor = self._connection.cursor()

        cursor.execute(""" INSERT INTO uvs_schema.files(fid, finfo_json) VALUES (%(fid)s, %(finfo)s) 
                           ON CONFLICT DO NOTHING ;""", {'fid': fid, 'finfo': psycopg2.Binary(finfo)}  )

        # Done close the transaction
        self._connection.commit()


    def add_tree(self, tid, tree_info):
        """Given a new tree as a (tid, tree info json) pair, add this tree to the trees table, if it doesnt already 
        exist. Do nothing if tid is already present in the data store. For this reason this call is idempotent.

        
        Normally in uvs tree_info is in ciphertext (as str or bytes) (except perhaps in debug mode). 
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_tree() called on Postgres DAO. tid: " + str(tid) + " tree_info: " + str(tree_info))

        assert None != tree_info
        assert isinstance(tree_info, str) or isinstance(tree_info, bytes)
        assert None != tid
        assert isinstance(tid, str) or isinstance(tid, bytes)

        cursor = self._connection.cursor()

        cursor.execute(""" INSERT INTO uvs_schema.trees(tid, tree_json) VALUES (%(tid)s, %(tree_info)s) 
                           ON CONFLICT DO NOTHING; """, {'tid': tid, 'tree_info': psycopg2.Binary(tree_info)})

        # Done close the transaction
        self._connection.commit()


    def add_snapshot(self, snapid, snapshot):
        """Given a new snapshot (commit in other vcs) as a (snapid, snapshot) pair,
         add this snapshot to the snapshots table, if it doesnt already exist. Do nothing if snapid is 
         already present in the data store. For this reason this call is idempotent.
        
         new snapshots should never have snapid that collides with an existing one in the repo. snapids are
         random unique identifiers created every time user makes a new snapshot (commit)
    
        Normally in uvs snapshot is in ciphertext (as str or bytes) (except perhaps in debug mode). 
        Its not the Data Store's responsibility to handle encryption/decryption. 
        I will store and retrieve whatever you give me.
        """

        log.dao("add_snapshot() called on Postgres DAO. snapid: " + str(snapid) + " snapshot: " + str(snapshot))


        assert None != snapid
        assert None != snapshot
        assert isinstance(snapid, str) or isinstance(snapid, bytes)
        assert isinstance(snapshot, str) or isinstance(snapshot, bytes)

        cursor = self._connection.cursor()

        cursor.execute(""" INSERT INTO uvs_schema.snapshots(snapid, snapinfo_json) VALUES (%(snapid)s, %(snapshot)s) 
                           ON CONFLICT DO NOTHING;""", {'snapid': snapid, 'snapshot': psycopg2.Binary(snapshot)})

        # Done close the transaction
        self._connection.commit()



