

import psycopg2
import json
import os

import hash_util
import rand_util
import log
import cryptmanager as cm
import systemdefaults as sdef
import _version
import error



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

    def _clear_tables(self):
        """ Clear tables without dropping schema. """

        cursor = self._connection.cursor()

        # clear table in case previous records are there.
        cursor.execute(""" DELETE FROM uvs_schema.public; """)
        cursor.execute(""" DELETE FROM uvs_schema.snapshots; """)
        cursor.execute(""" DELETE FROM uvs_schema.trees; """)
        cursor.execute(""" DELETE FROM uvs_schema.files; """)
        cursor.execute(""" DELETE FROM uvs_schema.segments; """)

        self._connection.commit()



    def _create_schema(self):
        """ Create empty Tables in the Postgres database to which this object is connected to.. """

        cursor = self._connection.cursor()

        # TODO if not exists maybe??

        #cursor.execute(""" DROP SCHEMA IF EXISTS uvs_schema CASCADE; """)
        self._clear_tables()

        cursor.execute(""" CREATE SCHEMA IF NOT EXISTS uvs_schema; """)
        cursor.execute(""" SET search_path TO uvs_schema; """)

        fp_size = cm.get_uvs_fingerprint_size()
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


        # TODO add another column (which is encrypted for commit messages)
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


    def _populate_db_with_sample_set1(self):
        """ load data set 1 into the db. """

        cursor = self._connection.cursor()

        # -------------------------------------------------------------------------- sample data for public table
        sample_pass = 'weakpass123'

        public_info = {}

        # fix the salt for sample data set 1 for testing purposes, in a real repo this should come from
        # cm.get_new_random_salt()
        public_info['salt'] = '596381b4268e6811cbf9614c3fa0981515223600f49ab12fc2f783729399a31e'
        public_info['uvs_version'] = _version.get_version()
        public_info['fingerprinting_algo'] = cm.get_uvs_fingerprinting_algo_desc()

        public_info_serialized = json.dumps(public_info, ensure_ascii=False, sort_keys=True)

        log.vvvv(public_info_serialized)


        cursor.execute(""" INSERT INTO uvs_schema.public(public_json) VALUES (
         %(serialized)s    );""", {'serialized': psycopg2.Binary(public_info_serialized)})

        self._connection.commit()

        # get the data back
        cursor.execute(""" SELECT * FROM uvs_schema.public; """)

        # fetchone returns a tuple, and inside the tuple you will find buffer type objects
        first_row = cursor.fetchone()[0]
        log.vvvv("Got back public json from db, first row type: " + str(type(first_row)))
        log.vvvv('First row as str: ' + str(first_row))

        public_info_from_db_serial = str(first_row)

        # it maybe that the one from db has unicode objects in it, but == is str equality so we should still pass
        # this before going forward.
        assert public_info_serialized == public_info_from_db_serial

        public_info_from_db = json.loads(public_info_from_db_serial)

        log.v("public info dict now, after getting it back from db: ")
        log.v( public_info_from_db )


        assert  public_info_from_db.has_key('salt')

        # salt is there, make sure its a str object (or bytes) but not unicode.
        public_info_from_db['salt'] = str(public_info_from_db['salt'])

        crypt_helper = cm.UVSCryptHelper(usr_pass=sample_pass, salt=public_info_from_db['salt'])


        # -------------------------------------------------------- some sample segments and files
        #  we have files hello.py morning.py afternoon.py

        f1_bytes = b'''\n\n\n print "hello" \n\n\n'''
        f1_fp =  crypt_helper.get_uvsfp(f1_bytes)

        f2_bytes =  b'''\n\n\n print "good morning" \n\n\n'''
        f2_fp =  crypt_helper.get_uvsfp(f2_bytes)

        f3_bytes =  b'''\n\n\n print "good afternoon" \n\n\n'''
        f3_fp =  crypt_helper.get_uvsfp(f3_bytes)

        # break file1 into segments
        f1_s1 = f1_bytes[:7]
        f1_s2 = f1_bytes[7:]

        f2_s1 = f2_bytes[:7]
        f2_s2 = f2_bytes[7:]

        f3_s1 = f3_bytes[:7]
        f3_s2 = f3_bytes[7:]

        f1_s1_fp = crypt_helper.get_uvsfp(f1_s1)
        f1_s2_fp = crypt_helper.get_uvsfp(f1_s2)
        f2_s1_fp = crypt_helper.get_uvsfp(f2_s1)
        f2_s2_fp = crypt_helper.get_uvsfp(f2_s2)
        f3_s1_fp = crypt_helper.get_uvsfp(f3_s1)
        f3_s2_fp = crypt_helper.get_uvsfp(f3_s2)


        # ON CONFLICT DO NOTHING was added to postgres as of version 9.5 (google upsert for more info)
        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'sgid': f1_s1_fp,
                        'segment': psycopg2.Binary(crypt_helper.encrypt_bytes(f1_s1))}  )

        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'sgid': f1_s2_fp,
                        'segment': psycopg2.Binary(crypt_helper.encrypt_bytes(f1_s2))}  )

        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'sgid': f2_s1_fp,
                        'segment': psycopg2.Binary(crypt_helper.encrypt_bytes(f2_s1))}  )

        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'sgid': f2_s2_fp,
                        'segment': psycopg2.Binary(crypt_helper.encrypt_bytes(f2_s2))}  )

        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'sgid': f3_s1_fp,
                        'segment': psycopg2.Binary(crypt_helper.encrypt_bytes(f3_s1))}  )

        cursor.execute(""" INSERT INTO uvs_schema.segments(sgid, segment) VALUES (%(sgid)s, %(segment)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'sgid': f3_s2_fp,
                        'segment': psycopg2.Binary(crypt_helper.encrypt_bytes(f3_s2))}  )

        # -------------------------------------------------------------------------- sample data for files table
        # lets add some files.

        file1_json = {}

        # verify fid is there to make sure records don't get reordered by an attacker.
        # fid is the uvs fingerprint of the content of the file.
        file1_json['verify_fid'] = f1_fp

        # 'segments' is a list of 2-tuples, (sgid, offset)
        # i.e. (sg001, 0)  means segment sg001 contains len(sg001) many bytes of this file starting from offset 0
        # i.e. (sg002, 2100) means segment sg002 contains len(sg002) many bytes of this file starting from offset 2100
        file1_json['segments'] = []
        file1_json['segments'].append( (f1_s1_fp, 0) )
        file1_json['segments'].append( (f1_s2_fp, len(f1_s1)) )


        file2_json = {}
        file2_json['verify_fid'] = f2_fp

        # 'segments' is a list of 3-tuples, (sgid, offset)
        file2_json['segments'] = []
        file2_json['segments'].append((f2_s1_fp,  0))
        file2_json['segments'].append((f2_s2_fp, len(f2_s1)))

        file3_json = {}
        file3_json['verify_fid'] = f3_fp

        # 'segments' is a list of 3-tuples, (sgid, offset)
        file3_json['segments'] = []
        file3_json['segments'].append((f3_s1_fp,  0))
        file3_json['segments'].append((f3_s2_fp, len(f3_s1)))


        tmp_json = json.dumps(file1_json, ensure_ascii=False, sort_keys=True)
        tmp_json = crypt_helper.encrypt_bytes(tmp_json)

        cursor.execute(""" INSERT INTO uvs_schema.files(fid, finfo_json) VALUES (%(fid)s, %(finfo_json)s) 
                           ON CONFLICT DO NOTHING ;""", {'fid': f1_fp, 'finfo_json': psycopg2.Binary(tmp_json)}  )

        tmp_json = json.dumps(file2_json, ensure_ascii=False, sort_keys=True)
        tmp_json = crypt_helper.encrypt_bytes(tmp_json)

        cursor.execute(""" INSERT INTO uvs_schema.files(fid, finfo_json) VALUES (%(fid)s, %(finfo_json)s) 
                           ON CONFLICT DO NOTHING ;""", {'fid': f2_fp, 'finfo_json': psycopg2.Binary(tmp_json)})

        tmp_json = json.dumps(file3_json, ensure_ascii=False, sort_keys=True)
        tmp_json = crypt_helper.encrypt_bytes(tmp_json)

        cursor.execute(""" INSERT INTO uvs_schema.files(fid, finfo_json) VALUES (%(fid)s, %(finfo_json)s) 
                           ON CONFLICT DO NOTHING ;""", {'fid': f3_fp, 'finfo_json': psycopg2.Binary(tmp_json)})



        # -------------------------------------------------------------------------- sample data for tree
        # lets add some trees

        tree1_json = {}
        tree1_json['tids'] = []
        tree1_json['fids'] = []

        # fids is a list of 2-tuples (name, fid) the list has to be sorted
        tree1_json['fids'].append( ("hello.py", f1_fp) )
        tree1_json['fids'].append( ("morning.py", f2_fp) )
        tree1_json['fids'].append( ("afternoon.py", f3_fp) )

        # it doesnt matter much what order things get sorted in, as long as it is deterministic.

        # this says sort by elem[0] first and in case of ties sort by elem[1], i think just sort woulda done the same.
        tree1_json['fids'].sort(key=lambda elem: (elem[0], elem[1]) )
        #tree1_json['fids'].sort()


        tree1_json_serial = json.dumps(tree1_json, ensure_ascii=False, sort_keys=True)

        # get the fingerprint and ciphertext
        tree1_fp = crypt_helper.get_uvsfp(tree1_json_serial)
        tree1_ct = crypt_helper.encrypt_bytes(tree1_json_serial)


        log.vvvv('tree1 fp: ' + tree1_fp + "\ntree1 json: " + tree1_json_serial)


        cursor.execute(""" INSERT INTO uvs_schema.trees(tid, tree_json) VALUES (%(tid)s, %(tree_json)s) 
                           ON CONFLICT DO NOTHING ;""", {'tid': tree1_fp, 'tree_json': psycopg2.Binary(tree1_ct)}  )

        # -------------------------------------------------------------------------- sample snapshots (commits)

        snapshot1_id = rand_util.get_new_random_snapshot_id()

        snapshot1_json = {}
        snapshot1_json['verify_snapid'] = snapshot1_id
        snapshot1_json['root'] = tree1_fp
        snapshot1_json['msg'] =  'First commit into uvs'
        snapshot1_json['author_name'] =  'kourosh'
        snapshot1_json['author_email'] =  'kourosh.sc@gmail.com'
        snapshot1_json['snapshot_signature'] =  "put gpg signature here to prove the author's identity."

        snapshot1_json_serial = json.dumps(snapshot1_json, ensure_ascii=False, sort_keys=True)
        snapshot1_json_ct  = crypt_helper.encrypt_bytes(snapshot1_json_serial)

        log.v('snapshot1 id: ' + snapshot1_id + "\nsnapshot1 json: " + snapshot1_json_serial)

        cursor.execute(""" INSERT INTO uvs_schema.snapshots(snapid, snapinfo_json) VALUES (%(snapid)s, %(snap_json)s) 
                           ON CONFLICT DO NOTHING ;""",
                       {'snapid': snapshot1_id, 'snap_json': psycopg2.Binary(snapshot1_json_ct)}  )

        self._connection.commit()









