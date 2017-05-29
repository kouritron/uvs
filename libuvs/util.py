
import os
import log
import json

def get_shadow_name(name):
    """ Given a directory name or path (like './sf' compute and return the shadow version (like './sf_shadow' """

    log.fefrv("get_shadow_name() called with type(arg), str(arg): " + str(type(name)) + " >>" + str(name) + "<<")

    final_comp = os.path.basename(name)
    dir_comp = os.path.dirname(name)

    # add '.' to the start of final_comp if we wanted to make the shadow a hidden folder.
    #final_comp = '.' + final_comp + '_shadow'
    final_comp = final_comp + '_shadow'

    result = os.path.join(dir_comp, final_comp)

    log.fefrv("get_shadow_name() returning with result: " + str(result))
    return result


def save_dict_as_json_to_pathname(dst_pathname, py_dict):
    """ Given a pathname to a writable file, and a python dict, 
    Serialize the dict as json and save it to the file. """

    log.fefrv('save_dict_as_json_to_pathname() called, args:')
    log.fefrv('dst_pathname: ' + str(dst_pathname) + " py_dict: " + str(py_dict))

    assert isinstance(dst_pathname, str) or isinstance(dst_pathname, unicode)
    assert isinstance(py_dict, dict)

    fhandle = open(dst_pathname, 'wb')

    json.dump(py_dict, fhandle, ensure_ascii=False, indent=4, sort_keys=True)

    # alternative using dumps method.
    # serial_data = json.dumps(py_dict, ensure_ascii=False, indent=4, sort_keys=True)
    # log.vvv('dumping serialized dict to file: ' + str(dst_pathname))
    # log.vvv(serial_data)
    # fhandle.write( serial_data )

    fhandle.flush()
    fhandle.close()

    log.fefrv('save_dict_as_json_to_pathname() returning')

def get_dict_from_json_at_pathname(src_pathname):
    """ Given a pathname to a file containing a JSON serialized object, read it, make a py dict from it 
    and return it. """

    log.fefrv('get_dict_from_json_at_pathname() called, src pathname: ' + str(src_pathname))
    assert isinstance(src_pathname, str) or isinstance(src_pathname, unicode)

    fhandle = open(src_pathname, 'rb')
    result_dict = json.load(fhandle)

    # print type(result_dict)  # returns <type dict>

    log.fefrv('get_dict_from_json_at_pathname() returning with result: ' + str(result_dict))
    return result_dict

if '__main__' == __name__:

    get_shadow_name('./sf')