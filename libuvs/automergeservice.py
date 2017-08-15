
# to do
# handle files that don't exist in all 3 directories


import os
import subprocess
import shutil
import hashlib
import log
from uvsconst import UVSConst


# this is a un-keyed hash, it is not stored anywhere in a uvs repo, its just for temporary comparing 2 files
# to see if they are the same or not. we could also just read them all and do a byte for byte compare.
def _get_file_hash(filepath):
    """ Return a str with the hex representation of the hash of the file with the given filepath.
    (assuming the file does exist and is readable. exception is raised otherwise)
    """

    assert isinstance(filepath, str) or isinstance(filepath, unicode)
    assert os.path.isfile(filepath)

    srcfile = open(filepath, 'rb')
    hash_func = hashlib.sha512()

    buf = srcfile.read(UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION)

    while len(buf) > 0:

        hash_func.update(buf)
        buf = srcfile.read(UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION)

    hex_digest = hash_func.hexdigest()

    log.amsv("computed sha512sum for file: " + str(filepath))
    log.amsv("sha512: " + str(hex_digest))

    return hex_digest


def _are_two_files_identical(file1_pathname, file2_pathname):
    """
    Given pathnames for two files, compare their content and return True if the two files contain the
    exact same bit patterns, False otherwise.

    does not compare file names, creation date, timestamps, etc etc. just file contents
    """

    assert isinstance(file1_pathname, str) or isinstance(file1_pathname, unicode)
    assert isinstance(file2_pathname, str) or isinstance(file2_pathname, unicode)

    assert file1_pathname != file2_pathname

    assert os.path.isfile(file1_pathname)
    assert os.path.isfile(file2_pathname)

    log.amsv("_are_two_files_identical() called with args: ")
    log.amsv("f1: " + str(file1_pathname))
    log.amsv("f2: " + str(file2_pathname))

    f1_hash = _get_file_hash(filepath=file1_pathname)
    f2_hash = _get_file_hash(filepath=file2_pathname)

    return f1_hash == f2_hash




def gui_merge3(base_dirpath, a_dirpath, b_dirpath, out_dirpath):

    assert isinstance(base_dirpath, str) or isinstance(base_dirpath, unicode)
    assert isinstance(a_dirpath, str) or isinstance(a_dirpath, unicode)
    assert isinstance(b_dirpath, str) or isinstance(b_dirpath, unicode)
    assert isinstance(out_dirpath, str) or isinstance(out_dirpath, unicode)

    assert out_dirpath != base_dirpath
    assert out_dirpath != a_dirpath
    assert out_dirpath != b_dirpath

    assert os.path.isdir(base_dirpath)
    assert os.path.isdir(a_dirpath)
    assert os.path.isdir(b_dirpath)
    assert os.path.isdir(out_dirpath)



    # kdiff3 takes the merge base as first arg (or specify it directly with -b or --base option)
    # kdiff3 options:
    # -m or --merge
    # -o or --output             (output path file or dir, this options implies -m)


    diff3_cmd = "kdiff3 " + base_dirpath + " " + a_dirpath + " " + b_dirpath + " -m -o " + out_dirpath
    log.amsv("kdiff3 cmd is: " + diff3_cmd)

    # call will return the exit code.
    cmd_exit_code = subprocess.call(diff3_cmd, shell=True)
    if 0 != cmd_exit_code:
        log.ams("kdiff3 exit code: " + str(cmd_exit_code))



# TODO
# make a function that does auto merge3 for just files in a directory
# handle cases where file is not in all 3.
# recursively call this

# TODO validate path names better
# if a path name contains space this may break, we need some os or other module to pre-process path names
def auto_merge3(base_dirpath, a_dirpath, b_dirpath, out_dirpath):


    # TODO: maybe we allow None to be supplied as an argument, and None would indicate an empty
    # folder, (the folder doesnt exist, but treat it as empty, so if None replace listdir() with empty list.
    # output can not be None tho. keep that assertion

    assert isinstance(base_dirpath, str) or isinstance(base_dirpath, unicode)
    assert isinstance(a_dirpath, str) or isinstance(a_dirpath, unicode)
    assert isinstance(b_dirpath, str) or isinstance(b_dirpath, unicode)
    assert isinstance(out_dirpath, str) or isinstance(out_dirpath, unicode)

    assert out_dirpath != base_dirpath
    assert out_dirpath != a_dirpath
    assert out_dirpath != b_dirpath

    assert out_dirpath is not None

    if not os.path.isdir(out_dirpath):
        os.makedirs(out_dirpath)



    # we do this
    # call merge3_files on this level update result
    # find common subdirs. for each common subdir call self with joined pathnames
    # combine results and return them

    results = {}

    # # these need manual resolution
    results['hard_conflicts_found'] = False

    # # these mean something bad happened, i.e. bin files, permission denied ...
    results['trouble_found'] = False

    current_level_results = merge3_all_files(base_dirpath=base_dirpath, a_dirpath=a_dirpath, b_dirpath=b_dirpath,
                                             out_dirpath=out_dirpath)

    if current_level_results['hard_conflicts_found']:
        results['hard_conflicts_found'] = True

    if current_level_results['trouble_found']:
        results['trouble_found'] = True

    # done with this.
    del current_level_results

    log.ams("", label=False)
    log.ams("------------------------------------------------------------------------------")
    log.ams("----------------------------- Done merging current level, recursing. ")


    base_members = []
    if (base_dirpath is not None) and os.path.isdir(base_dirpath):
        base_members = os.listdir(base_dirpath)

    base_subdirnames = [member for member in base_members if os.path.isdir(os.path.join(base_dirpath, member))]
    base_members.sort()
    base_subdirnames.sort()

    a_members = []
    if (a_dirpath is not None) and os.path.isdir(a_dirpath):
        a_members = os.listdir(a_dirpath)

    a_subdirnames = [member for member in a_members if os.path.isdir(os.path.join(a_dirpath, member))]
    a_members.sort()
    a_subdirnames.sort()

    b_members = []
    if (b_dirpath is not None) and os.path.isdir(b_dirpath):
        b_members = os.listdir(b_dirpath)

    b_subdirnames = [member for member in b_members if os.path.isdir(os.path.join(b_dirpath, member))]
    b_members.sort()
    b_subdirnames.sort()

    log.ams("base_members:     " + str(base_members))
    log.ams("base_subdirnames: " + str(base_subdirnames))

    log.ams("a_members:     " + str(a_members))
    log.ams("a_subdirnames: " + str(a_subdirnames))

    log.ams("b_members:     " + str(b_members))
    log.ams("b_subdirnames: " + str(b_subdirnames))

    subdirs = set()

    for subdir in a_subdirnames:
        # if (subdir in base_subdirnames) and (subdir in b_subdirnames): pass
        # if (subdir in b_subdirnames): pass
        subdirs.add(subdir)

    for subdir in b_subdirnames:
        subdirs.add(subdir)

    log.ams("about to visit subdirs: " + str(subdirs))

    for subdir in subdirs:

        log.ams("handling subdir: " + str(subdir))

        base_subdir_path = os.path.join(base_dirpath, subdir)
        a_subdir_path = os.path.join(a_dirpath, subdir)
        b_subdir_path = os.path.join(b_dirpath, subdir)
        out_subdir_path = os.path.join(out_dirpath, subdir)


        # make the directory under merge results
        if not os.path.isdir(out_subdir_path):
            os.makedirs(out_subdir_path)

        # temp_results  = ....
        temp_results = auto_merge3(base_dirpath=base_subdir_path, a_dirpath=a_subdir_path, b_dirpath=b_subdir_path,
                                             out_dirpath=out_subdir_path)

        if temp_results['hard_conflicts_found']:
            results['hard_conflicts_found'] = True

        if temp_results['trouble_found']:
            results['trouble_found'] = True


    return results

# just files, no looking into recursive subdirs.
def merge3_all_files(base_dirpath, a_dirpath, b_dirpath, out_dirpath):


    # TODO: maybe we allow None to be supplied as an argument, and None would indicate an empty
    # folder, (the folder doesnt exist, but treat it as empty, so if None replace listdir() with empty list.
    # output can not be None tho. keep that assertion

    assert isinstance(base_dirpath, str) or isinstance(base_dirpath, unicode)
    assert isinstance(a_dirpath, str) or isinstance(a_dirpath, unicode)
    assert isinstance(b_dirpath, str) or isinstance(b_dirpath, unicode)
    assert isinstance(out_dirpath, str) or isinstance(out_dirpath, unicode)

    assert out_dirpath != base_dirpath
    assert out_dirpath != a_dirpath
    assert out_dirpath != b_dirpath

    assert out_dirpath is not None

    if not os.path.isdir(out_dirpath):
        os.makedirs(out_dirpath)


    log.ams("", label=False)
    log.ams("------------------------------------------------------------------------------")
    log.ams("------------------------------------------------------------------------------")
    log.ams("------------------------------------------------------------------------------")
    log.ams("----------------------------------------------------------- merge3_all_files()")
    log.ams("----- base_dirpath: " + str(base_dirpath))
    log.ams("----- a_dirpath: " + str(a_dirpath))
    log.ams("----- b_dirpath: " + str(b_dirpath))
    log.ams("----- out_dirpath: " + str(out_dirpath))
    log.ams("", label=False)


    res = {}

    # these need manual resolution
    res['hard_conflicts_found'] = False

    # these mean something bad happened, i.e. bin files, permission denied ...
    res['trouble_found'] = False



    base_members = []
    if (base_dirpath is not None) and os.path.isdir(base_dirpath):
        base_members = os.listdir(base_dirpath)

    base_filenames = [member for member in base_members if os.path.isfile(os.path.join(base_dirpath, member))]
    base_members.sort()
    base_filenames.sort()

    a_members = []
    if (a_dirpath is not None) and os.path.isdir(a_dirpath):
        a_members = os.listdir(a_dirpath)

    a_filenames = [member for member in a_members if os.path.isfile(os.path.join(a_dirpath, member))]
    a_members.sort()
    a_filenames.sort()

    b_members = []
    if (b_dirpath is not None) and os.path.isdir(b_dirpath):
        b_members = os.listdir(b_dirpath)

    b_filenames = [member for member in b_members if os.path.isfile(os.path.join(b_dirpath, member))]
    b_members.sort()
    b_filenames.sort()

    log.ams("base_members:   " + str(base_members))
    log.ams("base_filenames: " + str(base_filenames))

    log.ams("a_members:   " + str(a_members))
    log.ams("a_filenames: " + str(a_filenames))

    log.ams("b_members:   " + str(b_members))
    log.ams("b_filenames: " + str(b_filenames))
    log.ams("---------------------------------------------------------------------------------------------")


    # There are 3 main Cases
    # 1- a file is in just 1 dir
    # 2- a file is in 2 dirs
    # 3- a file is in all three dirs

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------- case 1: filenames that exist in only 1 directory.
    # case 1 subcases:
    #       subcase 1: file is in base
    #       subcase 2: file is in A.
    #       subcase 3: file is in B.

    log.ams("", label=False)
    log.ams("CASE 1, files that exist in only 1 out 3 directory.")


    # -------
    # subcase 1: file is in base
    #       ignore the file, both branches have deleted it.

    log.ams("ignoring case1 subcase1: files that exist only in base. nothing to be done on these.")

    # -------
    # subcase 2: file is in A.
    #       branch A has added a file that did not exist in Base or other branch, merge3 should copy it over.
    only_in_a_filenames = set()

    for candidate_filename in a_filenames:
        if (candidate_filename not in base_filenames) and (candidate_filename not in b_filenames):
            only_in_a_filenames.add(candidate_filename)

    log.ams("files found only in a: " + str(only_in_a_filenames))

    # now copy these files over
    for only_in_a_filename in only_in_a_filenames:

        log.ams("case1 subcase2: file existed only in A, filename: " + str(only_in_a_filename))

        only_in_a_filepath = os.path.join(a_dirpath, only_in_a_filename)
        out_filepath = os.path.join(out_dirpath, only_in_a_filename)

        try:
            # shutil.copyfile(src='/da31das2/3dfgasf3hjj/a4312dadssdds', dst=out_filepath)
            shutil.copyfile(src=only_in_a_filepath, dst=out_filepath)
        except IOError as e:
            log.ams("IOError occurred.")
            log.ams("repr(e): " + repr(e))
            res['trouble_found'] = True


    # -------
    # subcase 3: file is in B.
    only_in_b_filenames = set()

    for candidate_filename in b_filenames:
        if (candidate_filename not in base_filenames) and (candidate_filename not in a_filenames):
            only_in_b_filenames.add(candidate_filename)

    log.ams("files found only in b: " + str(only_in_b_filenames))

    # now copy these files over
    for only_in_b_filename in only_in_b_filenames:

        log.ams("case1 subcase3: file existed only in B, filename: " + str(only_in_b_filename))

        only_in_b_filepath = os.path.join(b_dirpath, only_in_b_filename)
        out_filepath = os.path.join(out_dirpath, only_in_b_filename)

        try:
            # shutil.copyfile(src='/da31das2/3dfgasf3hjj/a4312dadssdds', dst=out_filepath)
            shutil.copyfile(src=only_in_b_filepath, dst=out_filepath)
        except IOError as e:
            log.ams("IOError occurred.")
            log.ams("repr(e): " + repr(e))
            res['trouble_found'] = True

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------- case 2: filenames that exist in 2 out of 3 dirs.
    # case 2  subcases:
    #
    # subcase 1: file is in base and A.
    # subcase 2: file is in base and B.
    # subcase 3: file is in A and B.
    #
    # TODO: subcase 1 and 2 are somewhat complicated situation. maybe loot at what git is doing
    # we are not sure if we should let deletions propagate or look at changes versus base.
    # we have two options
    # option 1: copy over the files. one branch has kept it (either unmodified or modified)
    # option 2: copy over if one branch has kept but modified it, otherwise delete it. (kind of like merge3 with lines)


    log.ams("", label=False)
    log.ams("CASE 2, files that exist in 2 out 3 directory.")


    # subcase 1: file is in base and A.
    base_and_a_only_filenames = set()

    for candidate_filename in a_filenames:
        if (candidate_filename in base_filenames) and (candidate_filename not in b_filenames):
            base_and_a_only_filenames.add(candidate_filename)

    log.ams("files found in base and a only: " + str(base_and_a_only_filenames))

    # now deal with subcase1
    for base_and_a_only_filename in base_and_a_only_filenames:

        log.ams("case2 subcase1: file existed only in Base and A, filename: " + str(base_and_a_only_filename))
        base_and_a_only_filepath = os.path.join(a_dirpath, base_and_a_only_filename)
        out_filepath = os.path.join(out_dirpath, base_and_a_only_filename)

        try:
            shutil.copyfile(src=base_and_a_only_filepath, dst=out_filepath)
        except IOError as e:
            log.ams("IOError occurred.")
            log.ams("repr(e): " + repr(e))
            res['trouble_found'] = True


    # subcase 2: file is in base and B.
    base_and_b_only_filenames = set()

    for candidate_filename in b_filenames:
        if (candidate_filename in base_filenames) and (candidate_filename not in a_filenames):
            base_and_b_only_filenames.add(candidate_filename)

    log.ams("files found in base and b only: " + str(base_and_b_only_filenames))

    # now deal with subcase2
    for base_and_b_only_filename in base_and_b_only_filenames:

        log.ams("case2 subcase2: file existed only in Base and B, filename: " + str(base_and_b_only_filename))
        base_and_b_only_filepath = os.path.join(b_dirpath, base_and_b_only_filename)
        out_filepath = os.path.join(out_dirpath, base_and_b_only_filename)

        try:
            shutil.copyfile(src=base_and_b_only_filepath, dst=out_filepath)
        except IOError as e:
            log.ams("IOError occurred.")
            log.ams("repr(e): " + repr(e))
            res['trouble_found'] = True


    # subcase 3: file is in A and B.
    # in this subcase, we dont have a base for the merge so no merge3 is possible, we can just
    # create a new file, put the markers down for one big merge conflict and copy a and b to it
    # this is what diff3 merge would do, if we provided empty file for base.
    a_and_b_only_filenames = set()

    for candidate_filename in a_filenames:
        if (candidate_filename in b_filenames) and (candidate_filename not in base_filenames):
            a_and_b_only_filenames.add(candidate_filename)

    log.ams("files found in a and b only: " + str(a_and_b_only_filenames))

    for a_and_b_only_filename in a_and_b_only_filenames:

        log.ams("case2 subcase3: file existed only in A and B, filename: " + str(a_and_b_only_filename))

        try:
            filepath_thru_a = os.path.join(a_dirpath, a_and_b_only_filename)
            filepath_thru_b = os.path.join(b_dirpath, a_and_b_only_filename)
            out_filepath = os.path.join(out_dirpath, a_and_b_only_filename)

            if _are_two_files_identical(file1_pathname=filepath_thru_a, file2_pathname=filepath_thru_b):

                log.ams("both branches introduced an identical file, not present in merge base.")
                shutil.copyfile(src=filepath_thru_a, dst=out_filepath)

            else:

                log.ams("the two branches introduced different file with same name, not present in merge base.")

                # in this case we dont have a base for merge3, even diff3 would do nothing but a show a big merge
                # conflict, so lets manually do that.
                # print UVSConst.MERGE3_CONFLICT_DELIMITER_START

                # open the file for writing. write in binary mode and add the new line char manually
                # i hate the stupid CRLF sequence on windows, just add a \n for newline, all self-respecting
                # editors on windows can handle it.

                # TODO: if we ever wanted to have a global setting that allows user to say checkout files
                # with windows line ending edit this chunk to support that.

                a_filehandle = open(filepath_thru_a, 'rb')
                b_filehandle = open(filepath_thru_b, 'rb')

                outfile_handle = open(out_filepath, 'wb')

                # write the start delimiter for big conflict
                outfile_handle.write(str(UVSConst.MERGE3_CONFLICT_DELIMITER_START) + str(filepath_thru_a) + '\n')

                # copy over contents of the version from a
                # read it chunk by chunk and copy over to out file.
                temp_buf = a_filehandle.read(UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION)

                while len(temp_buf) > 0:
                    outfile_handle.write(temp_buf)
                    temp_buf = a_filehandle.read(UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION)

                # now common ancestor delimiters, remember CA does not exist in this case
                outfile_handle.write(str(UVSConst.MERGE3_CONFLICT_DELIMITER_MIDDLE_1) +
                                     str("No common ancestor found for this file.") + '\n')

                outfile_handle.write(str(UVSConst.MERGE3_CONFLICT_DELIMITER_MIDDLE_2) + '\n')

                # copy over contents of the version from b
                # read it chunk by chunk and copy over to out file.
                temp_buf = b_filehandle.read(UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION)

                while len(temp_buf) > 0:
                    outfile_handle.write(temp_buf)
                    temp_buf = b_filehandle.read(UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION)

                outfile_handle.write(str(UVSConst.MERGE3_CONFLICT_DELIMITER_END) + str(filepath_thru_b) + '\n')

                # this case needs manual resolution
                # remember to set this, since we set conflict markers to be resolved by the user,
                res['hard_conflicts_found'] = True

        except IOError as e:
            log.ams("IOError occurred.")
            log.ams("repr(e): " + repr(e))
            res['trouble_found'] = True



    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------- case 3: filenames in common in all 3 dirs of the 3 way merge.

    log.ams("", label=False)
    log.ams("CASE 3, files that exist in all 3 out 3 directory.")

    common = set()

    for filename in a_filenames:
        if (filename in base_filenames) and (filename in b_filenames):
            common.add(filename)

    log.ams("common files: " + str(common))

    # launch diff3 external program to do the 3 way merging.

    for filename in common:
        ca_filepath = str(os.path.join(base_dirpath, filename))
        s1_filepath = str(os.path.join(a_dirpath, filename))
        s2_filepath = str(os.path.join(b_dirpath, filename))
        out_filepath = str(os.path.join(out_dirpath, filename))

        diff3_cmd = "diff3 " + s1_filepath + " " + ca_filepath + " " + s2_filepath + " -m > " + out_filepath
        log.ams("diff3_cmd is: " + diff3_cmd)

        # call will return the exit code.
        # blackhole = open(os.devnull, 'wb')
        diff3_cmd_exit_code = subprocess.call(diff3_cmd, shell=True)

        # diff3 exit code 0 means no conflicts found or conflicts were auto resolved
        # diff3 exit code 1 means conflicts that require manual resolution
        # diff3 exit code 2 means trouble (bin files, no permissions, ....)


        if 1 == diff3_cmd_exit_code:
            res['hard_conflicts_found'] = True

        elif 2 == diff3_cmd_exit_code:
            res['trouble_found'] = True


    # Done return result
    return res



# TODO add some unit tests for this module.

if '__main__' == __name__:



    # res = auto_merge3(base_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/ca',
    #                   a_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/master',
    #                   b_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/mybr',
    #                   out_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/merge_result' )


    # res = gui_merge3(base_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/ca',
    #                   a_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/master',
    #                   b_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/mybr',
    #                   out_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/merge_result' )

    # m3 = gui_merge3
    m3 = auto_merge3


    # res = m3(base_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/ca',
    #          a_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/master',
    #          b_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/mybr',
    #          out_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/merge_result' )


    res = m3(base_dirpath='/home/lu/m3_test/ca',
             a_dirpath='/home/lu/m3_test/br1',
             b_dirpath='/home/lu/m3_test/br2',
             out_dirpath='/home/lu/m3_test/merge_res',)

    print res


    #
    # print "test file compare:"
    # print _are_two_files_identical('/home/lu/m3_test/br1/in_all', '/home/lu/m3_test/br2/in_all')

    # print "test file compare:"
    # print _are_two_files_identical('/home/lu/m3_test/br1/br1_and_br2', '/home/lu/m3_test/br2/br1_and_br2')

















