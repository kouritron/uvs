

import psycopg2
import json

import hash_util
import log
import cryptmanager as cm



class DAL(object):

    def __init__(self):
        super(DAL, self).__init__()

        log.fefrv("++++++++++++++++++++++++++++++++ dal init called")

        # TODO remove the hard codes
        self._connection = psycopg2.connect(user='uvsusr1', database='uvsdb', password='IwantRISCVryzen8761230110',
                                            host='192.168.24.120', port=5432)

        log.vvvv("connection: " + str(self._connection))

        self._create_schema()
        self._populate_db_with_sample_set1()


    def _drop_schema(self):
        """ Lose all information the in the uvs database. """

        # use this;
        cursor = self._connection.cursor()
        cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        self._connection.commit()


    def _create_schema(self):
        """ Create empty Tables in the Postgres database to which this object is connected to.. """

        cursor = self._connection.cursor()

        # TODO if not exists maybe??
        #cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        cursor.execute(""" CREATE SCHEMA IF NOT EXISTS uvs_schema; """)
        cursor.execute(""" SET search_path TO uvs_schema; """)

        fp_size = hash_util.get_uvs_fingerprint_size()
        log.v("fp size is: " + str(fp_size) + " bytes")

        # wee need two symbols for each byte in hex encoding so
        fp_size_hex_enc = fp_size * 2



        # postgres text data types:
        # varchar(n)  ---> variable len with limit
        # char(n)     ---> fixed len blank padded
        # text        ---> variable unlimited len

        # lets make all of our ids refs text and hex encoded values,
        # it will also be easier to view these tables this way.
        # NOTE: %s is not python format specifier, it is the way the psycopg2 substitutes values into query.
        # IMPORTANT: never use str concat (+) or python format specifiers (old style or new) to put values into queries
        # neglecting this will open u up to SQL injection attack. Here
        # %s with a followup__tuple__            i.e    execute( "%s", (132,) )
        # %(name)s with a followup __dict__     i.e.    execute( "%(tickets_left)s", {tickets_left: 132} )
        # the above will do the same thing.

        cursor.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        snapid char(%(fp_size)s) NOT NULL,
        root_tid char(%(fp_size)s) NOT NULL,
        PRIMARY KEY (snapid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # Trees table, i dont believe postgres table names are case sensitive.
        # tid is the fingerprint of r1ct of the tree contents
        # tree is json that describes whats in this tree.
        cursor.execute("""CREATE TABLE IF NOT EXISTS trees (
        tid char(%(fp_size)s) NOT NULL,
        tree BYTEA,
        PRIMARY KEY (tid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # BYTEA type has 1 GB max size limit in postgres
        # fid is the fingerprint of the r1ct (round 1 cipher text) of the file content
        # finfo is json of information about this fid. Most important part is a list of seqments that make up this file
        # dereference the segments table to find the contents of this file.
        cursor.execute("""CREATE TABLE IF NOT EXISTS files (
        fid char(%(fp_size)s) NOT NULL,
        finfo BYTEA,
        PRIMARY KEY (fid)
        );
        """, {'fp_size': fp_size_hex_enc} )


        # BYTEA type has 1 GB max size limit in postgres
        # sid is the fingerprint of the r1ct (round 1 cipher text) of this segment
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


    def _populate_db_with_sample_set1(self):
        """ load data set 1 into the db. """

        cursor = self._connection.cursor()

        # -------------------------------------------------------------------------- sample data for public table
        test_pass = 'weakpass123'

 


        # -------------------------------------------------------------------------- sample data for
        # -------------------------------------------------------------------------- sample data for
        # -------------------------------------------------------------------------- sample data for

        sample_file1_bytes = b'\n\n\n print hello \n\n\n'
        sample_file1_fp =  hash_util.get_uvs_fingerprint(sample_file1_bytes)

        sample_file2_bytes = b'\n\n\n print hahahahaahahahahaha \n\n\n'
        sample_file2_fp =  hash_util.get_uvs_fingerprint(sample_file2_bytes)

        sample_file3_bytes = b'\n\n\n print uvs is cool \n\n\n'
        sample_file3_fp =  hash_util.get_uvs_fingerprint(sample_file3_bytes)




        # cursor.execute(""" INSERT INTO uvs_schema.bit_patterns(bpid, bp) VALUES (
        # %(bpid)s, %(bp)s    );""", {'bpid': sample_file1_fp, 'bp': psycopg2.Binary(sample_file1_bytes) } )
        #
        # cursor.execute(""" INSERT INTO uvs_schema.bit_patterns(bpid, bp) VALUES (
        # %(bpid)s, %(bp)s    );""", {'bpid': sample_file2_fp, 'bp': psycopg2.Binary(sample_file2_bytes) } )
        #
        # cursor.execute(""" INSERT INTO uvs_schema.bit_patterns(bpid, bp) VALUES (
        # %(bpid)s, %(bp)s    );""", {'bpid': sample_file3_fp, 'bp': psycopg2.Binary(sample_file3_bytes) } )


        # ----------------------------------------------------------------------------- sample data for trees  table
        tree1 = {}





        self._connection.commit()


if '__main__' == __name__:
    log.vvvv(">> creating DAL")
    dal = DAL()







