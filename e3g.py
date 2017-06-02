#! /usr/bin/env python


import os
import sys
import argparse
import getpass


from libuvs import cryptmanager as cm
from libuvs import rand_util
from libuvs import log
from libuvs import util


def _process_checkout_subcommand(dest):
    """ Process the checkout subcommand. Will block and ask user for the passphrase for this secret folder. """

    log.fefr("_process_checkout_subcommand() called with dest: " + str(dest))

    # TODO we probably dont have to delete everything in secret folder and extract them from the shadow.
    # this is a simple early implementation tho.

    sf_name = dest
    shadow_dir = util.get_shadow_name(name=sf_name)
    log.vvv("destination folder is: " + str(sf_name) + " shadow folder: " + str(shadow_dir))

    try:
        plain_files = os.listdir(sf_name)
        for plain_file in plain_files:
            os.remove(os.path.join(sf_name, plain_file))
    except:
        print ("Error: Can not clear secret directory, do i have sufficient permissions? ")
        sys.exit(1)

    # .e3g_public file resides in './sf' and also in './sf_shadow' in plain text. public items go in it. (i.e kdf salt)
    #  read the .e3g_public file from shadow folder and get a py dict from the JSON in it.
    dot_e3g_public = util.get_dict_from_json_at_pathname(src_pathname=os.path.join(shadow_dir, '.e3g_public'))

    # be careful with the dot_e3g_public, its content may now be unicode not str or bytes.
    if not dot_e3g_public.has_key('salt'):
        print "Error: .e3g_public file in " + str(shadow_dir) + " file is inaccessible or corrupted. "

    util.save_dict_as_json_to_pathname(dst_pathname=os.path.join(sf_name, '.e3g_public'), py_dict=dot_e3g_public)

    # this maybe a unicode not str.
    dot_e3g_public['salt'] = str(dot_e3g_public['salt'])
    log.vv(".e3g_public read and decoded: " + str(dot_e3g_public))

    # now ask the user for the passphrase
    user_pass = getpass.getpass(prompt="Passphrase: ")

    # now that we have the salt and the user pass make a transcryptor obj that can encrypt and decrypt things.
    tc = cm.Transcryptor(usr_pass=user_pass, salt=dot_e3g_public['salt'])

    tc.decrypt_file(src=os.path.join(shadow_dir, '.e3g_protected') , dst=os.path.join(sf_name, '.e3g_protected'))

    # now that the .e3g_protected is sitting in secret folder in plain text we can read and decode the JSON.
    dot_e3g_protected = util.get_dict_from_json_at_pathname(src_pathname=os.path.join(sf_name, '.e3g_protected'))

    # now decrypt plaintext back out of shadow files in './sf_shadow' and put them in '.sf'
    for plain_name, annon_name in dot_e3g_protected['filename_mappings']:
        plain_pathname = os.path.join(sf_name, plain_name)
        annon_pathname = os.path.join(shadow_dir, annon_name)
        log.vvv("Decrypting " + annon_pathname[:40] + "...." + ' >>> to: >>> ' + plain_pathname)

        tc.decrypt_file(src=annon_pathname, dst=plain_pathname)


def _process_rdy_subcommand(dest):
    """ Process the rdy subcommand. Will block and ask user for the passphrase for this secret folder. """

    log.fefr("_process_rdy_subcommand() called with dest: " + str(dest))

    # TODO dont delete everything in shadow folder and recreate them (which is what i am doing now in early version)
    # ideally we should read the shadow files, decrypt them, hash their content, hash the secret folder contents
    # and only delete and recreate shadow files for files that actually changed. but for now go with the simpler
    # approach of deleting everything in shadow and recreating it.

    sf_name = dest
    shadow_dir = util.get_shadow_name(name=sf_name)
    log.vvvv("destination folder is: " + str(sf_name) + " shadow folder: " + str(shadow_dir))


    try:
        shadow_files = os.listdir(shadow_dir)
        for shadow_file in shadow_files:
            os.remove(os.path.join(shadow_dir, shadow_file))
    except:
        print ("Error: Can not clear the shadow directory, do i have sufficient permissions? ")
        sys.exit(1)



    # .e3g_public file resides in './sf' and also in './sf_shadow' in plain text. public items go in it. (i.e kdf salt)
    #  read the .e3g_public file from secret folder and get a py dict from the JSON in it.
    dot_e3g_public = util.get_dict_from_json_at_pathname(src_pathname=os.path.join(sf_name, '.e3g_public'))

    # be careful with the dot_e3g_public, its content may now be unicode not str or bytes.
    if not dot_e3g_public.has_key('salt'):
        print "Error: .e3g_public file in " + str(sf_name) + " is inaccessible or corrupted. "

    # this maybe a unicode not str.
    dot_e3g_public['salt'] = str(dot_e3g_public['salt'])
    log.vv(".e3g_public read and decoded: " + str(dot_e3g_public))

    # now ask the user for the passphrase
    user_pass = getpass.getpass(prompt="Passphrase: ")

    # now that we have the salt and the user pass make a transcryptor obj that can encrypt and decrypt things.
    tc = cm.Transcryptor(usr_pass=user_pass, salt=dot_e3g_public['salt'])

    secret_folder_current_files = os.listdir(sf_name)

    plaintext_filenames = []
    for sf_filename in secret_folder_current_files:
        if ('.e3g_public' != sf_filename) and ('.e3g_protected' != sf_filename):
            plaintext_filenames.append(sf_filename)

    log.vvv("list of files found at src(excluding .e3g files): \n" + str(plaintext_filenames))

    # now we have files whose name is in plaintext_filenames list + the two .e3g files.

    # .dot_e3g_protected file resides in './sf' and has its cipher text version in './sf_shadow'
    dot_e3g_protected = {}
    filename_mappings = [(pfname, rand_util.get_new_random_filename()) for pfname in plaintext_filenames]
    dot_e3g_protected['filename_mappings'] = filename_mappings
    #log.vvv("filename mappings are as follows: " + str(dot_e3g_protected['filename_mappings']))


    # now make shadow files in './sf_shadow' for everything that lives in '.sf'
    for src_name, annon_name in dot_e3g_protected['filename_mappings']:
        src_pathname = os.path.join(sf_name, src_name)
        annon_pathname = os.path.join(shadow_dir, annon_name)
        log.vvv("saving " + src_pathname + ' >>> to: >>> ' + annon_pathname[:40] + "....")

        tc.encrypt_file(src=src_pathname, dst=annon_pathname)


    # now save the .e3g_public
    # we just read it from the secret folder so no need to save there.
    # util.save_dict_as_json_to_pathname(dst_pathname=os.path.join(sf_name, '.e3g_public'), py_dict=dot_e3g_public)
    util.save_dict_as_json_to_pathname(dst_pathname=os.path.join(shadow_dir, '.e3g_public'), py_dict=dot_e3g_public)

    # now save the .e3g_protected file into './sf' and its ciphertext version into './sf_shadow' folder
    util.save_dict_as_json_to_pathname(dst_pathname=os.path.join(sf_name, '.e3g_protected'), py_dict=dot_e3g_protected)
    tc.encrypt_file(src=os.path.join(sf_name, '.e3g_protected'), dst=os.path.join(shadow_dir, '.e3g_protected'))



def _process_init_subcommand(dest):
    """ Process the init subcommand. May block and ask user some questions. 
    dest is the name of the new secret folder to be inited. 
    
    """

    log.fefr("_process_init_subcommand() called with dest: " + str(dest))

    sf_name = dest
    log.v("destination folder is: " + str(sf_name))

    if None == sf_name:
        print "Error: No destination name supplied. Plz supply a name for your encrypted secret folder."
        sys.exit(2)


    assert (isinstance(sf_name, str) or isinstance(sf_name, unicode))

    # example sf_name: "./sf"  shadow >>> "./sf_shadow"

    # if "./sf" is a file - error cant init.
    if os.path.isfile(sf_name):
        print "Error: Supplied name exists and is a file."
        sys.exit(2)

    shadow_dir = util.get_shadow_name(name=sf_name)

    # if "./sf_shadow" is a file - error cant init.
    if os.path.isfile(shadow_dir):
        print "Error: Can't accept the supplied name, because its shadow is a file."
        sys.exit(2)

    # if "./sf_shadow" is a non-empty directory - error cant init.
    if os.path.isdir(shadow_dir) and (0 != len(os.listdir(shadow_dir))):
        print "Error: Can't accept the supplied name, because its shadow is a non-empty folder."
        sys.exit(2)

    # make the secret folder and its shadow.
    if not os.path.isdir(sf_name):
        os.makedirs(sf_name)

    if not os.path.isdir(shadow_dir):
        os.makedirs(shadow_dir)


    # .e3g_public file resides in './sf' and also in './sf_shadow' in plain text. public items go in it. (i.e kdf salt)
    dot_e3g_public = {}
    dot_e3g_public['salt'] = cm.get_new_random_salt()


    # now save the .e3g_public file into both './sf' and './sf_shadow' folder
    util.save_dict_as_json_to_pathname(dst_pathname=os.path.join(sf_name, '.e3g_public'), py_dict=dot_e3g_public)

    # now make a gitignore for './sf' to make sure git does not track the plaintext files.
    sf_gitignore_fh = open(os.path.join(sf_name, '.gitignore'), 'wb')
    sf_gitignore_fh.write('## Git should not track the content of your secret directory. Only its shadow version. \n')
    sf_gitignore_fh.write('*\n\n')
    sf_gitignore_fh.flush()
    sf_gitignore_fh.close()


def _parse_cmdline():
    """ Given command line arguments to the program are in the arguments list, parse and process them. """

    parser = argparse.ArgumentParser(description='E3G - End to End Encrypted Git')
    parser.add_argument("subcmd1", help="what should e3g do", choices=['init', 'rdy', 'checkout'])
    parser.add_argument("destination", help="which folder to init, or rdy 4 commit, or checkout", nargs='?')
    args = parser.parse_args()

    # print type(args) returns  <class 'argparse.Namespace'>
    if 'init' == args.subcmd1:
        log.vvvv(">>>> init sub command called.")
        _process_init_subcommand(dest=args.destination)

    elif 'rdy' == args.subcmd1:
        log.vvvv(">>>> rdy sub command called.")
        _process_rdy_subcommand(dest=args.destination)

    elif 'checkout' == args.subcmd1:
        log.vvvv(">>>> checkout sub command called.")
        _process_checkout_subcommand(dest=args.destination)

    #log.vvv("argparse args: " + str(args))





if "__main__" == __name__:
    _parse_cmdline()


