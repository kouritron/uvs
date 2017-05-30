

import psycopg2

from libuvs import cryptdefaults as cdef
import log



class DAL(object):

    def __init__(self):
        super(DAL, self).__init__()

        print "++++++++++++++++++++++++++++++++ dal init called"

        # TODO remove the hard codes
        self._connection = psycopg2.connect(user='uvsusr1', database='uvsdb', password='IwantRISCVryzen8761230110',
                                            host='192.168.24.120', port=5432)

        print "connection: " + str(self._connection)

        self._create_schema()
        self._populate_db_with_sample_set1()


    def _drop_schema(self):
        """ Lose all information the in the uvs database. """

        # use this;
        cursor = self._connection.cursor()
        cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        self._connection.commit()


    def _create_schema(self):
        """ Create empty Tables. """

        cursor = self._connection.cursor()

        # TODO if not exists maybe??
        #cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        cursor.execute(""" CREATE SCHEMA IF NOT EXISTS uvs_schema; """)
        cursor.execute(""" SET search_path TO uvs_schema; """)

        fp_size = cdef.get_hash_fingerprint_size()
        log.v("fp size is: " + str(fp_size) )

        # wee need two symbols for each byte in hex encoding so
        fp_size_hex_enc = fp_size * 2



        # postgres text data types:
        # varchar(n)  ---> variable len with limit
        # char(n)     ---> fixed len blank padded
        # text        ---> variable unlimited len

        # lets make all of our ids refs text and hex encoded values,
        # it will also be easier to view these tables this way.
        cursor.execute("""CREATE TABLE IF NOT EXISTS Snapshots (
        sid char(%d) NOT NULL,
        root_tnid char(%d) NOT NULL,
        PRIMARY KEY (sid)
        );
        """ % (fp_size_hex_enc, fp_size_hex_enc ) )

        # TreeNodes table
        cursor.execute("""CREATE TABLE IF NOT EXISTS TreeNodes (
        tnid char(%d) NOT NULL,
        tn BYTEA,
        PRIMARY KEY (tnid)
        );
        """ % (fp_size_hex_enc, ) )


        # BitPatterns table
        # BYTEA type has 1 GB max
        cursor.execute("""CREATE TABLE IF NOT EXISTS BitPatterns (
        bpid char(%d) NOT NULL,
        bp BYTEA,
        PRIMARY KEY (bpid)
        );
        """ % (fp_size_hex_enc, ) )


        # this will commit the transaction right away. without this call, changes will be lost entirely.
        # Note after calling close on this connection, all cursors derived from it will fail to execute queries.
        # also all cursors derived from the same connection, see each other's changes immediately (are not isolated)
        # multiple connection objects may or may not see each others changes immediately (check ISOLATION LEVEL)
        self._connection.commit()


    def _populate_db_with_sample_set1(self):
        """ load dataset 1 into the db. """



        pass


if '__main__' == __name__:
    print ">> creating DAL"
    dal = DAL()








