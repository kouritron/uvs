
# to do
# handle files that don't exist in all 3 directories

import os
import subprocess
import log

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





# TODO validate path names better
# if a path name contains space this may break, we need some os or other module to pre-process path names
def auto_merge3(base_dirpath, a_dirpath, b_dirpath, out_dirpath):

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


    conflicts_found = False


    base_elements = os.listdir(base_dirpath)
    base_filenames = [elem for elem in base_elements if os.path.isfile(os.path.join(base_dirpath, elem))]

    a_elements = os.listdir(a_dirpath)
    a_filenames = [elem for elem in a_elements if os.path.isfile(os.path.join(a_dirpath, elem))]

    b_elements = os.listdir(b_dirpath)
    b_filenames = [elem for elem in b_elements if os.path.isfile(os.path.join(b_dirpath, elem))]

    # print base_elements
    # print base_filenames
    # print a_filenames
    # print b_filenames

    common = set()

    for filename in a_filenames:
        if (filename in base_filenames) and (filename in b_filenames):
            common.add(filename)


    log.ams("common files: " + str(common))

    for filename in common:
        ca_filepath = str(os.path.join(base_dirpath, filename))
        s1_filepath = str(os.path.join(a_dirpath, filename))
        s2_filepath = str(os.path.join(b_dirpath, filename))
        out_filepath = str(os.path.join(out_dirpath, filename))

        diff3_cmd = "diff3 " + s1_filepath + " " + ca_filepath + " " + s2_filepath + " -m > " + out_filepath
        log.amsv("diff3_cmd is: " + diff3_cmd)


        # call will return the exit code.
        # blackhole = open(os.devnull, 'wb')
        diff3_cmd_exit_code = subprocess.call(diff3_cmd, shell=True)
        if 0 != diff3_cmd_exit_code:
            conflicts_found = True


    return conflicts_found





if '__main__' == __name__:

    # res = auto_merge3(base_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/ca',
    #                   a_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/master',
    #                   b_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/mybr',
    #                   out_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/merge_result' )


    res = gui_merge3(base_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/ca',
                      a_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/master',
                      b_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/mybr',
                      out_dirpath='/home/lu/Desktop/merge_test/.uvs_temp/merge_result' )

    print res


















