

import psycopg2


class DAL(object):

    def __init__(self):
        super(DAL, self).__init__()

        print "++++++++++++++++++++++++++++++++ dal init called"

        # TODO remove the hard codes
        self._connection = psycopg2.connect(user='uvsusr1', database='uvsdb', password='IwantRISCVryzen8761230110',
                                            host='192.168.24.120', port=5432)

        print "connetion: " + str(self._connection)


        self._create_schema()
        self._populate_db_with_sample_set1()


    def _drop_schema(self):
        """ Lose all information the in the uvs database. """

        # use this;
        cursor = self._connection.cursor()
        cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        self._connection.commit()


    def _create_schema(self):
        """ Create empyt Tables. """

        cursor = self._connection.cursor()

        # TODO if not exists maybe??
        cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        cursor.execute(""" CREATE SCHEMA uvs_schema """)
        cursor.execute('SET search_path TO uvs_schema;')

        cursor.execute("""CREATE TABLE IF NOT EXISTS Snapshots (
        sid TEXT NOT NULL,
        fid TEXT NOT NULL,
        is_dead BOOLEAN NOT NULL DEFAULT false,
        PRIMARY KEY (sid,fid)
        );
        """)


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








