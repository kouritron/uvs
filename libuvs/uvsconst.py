

# this module tries to implement a replacement for python's lack of language enforced constants.

class _UVSConst(object):


    # ------------------------------------------------------------------------------------------------------------------
    # save the constants here
    def _PASSWORD_PROMPT(self):
        return ">>> Enter Password: "


    def _MERGE3_CONFLICT_DELIMITER_START(self):
        return "<<<<<<< "


    def _MERGE3_CONFLICT_DELIMITER_MIDDLE_1(self):
        return "||||||| "


    def _MERGE3_CONFLICT_DELIMITER_MIDDLE_2(self):
        return "======= "


    def _MERGE3_CONFLICT_DELIMITER_END(self):
        return ">>>>>>> "


    def _AMS_MERGE_RESULT_FOLDER_NAME(self):
        return "merge_result"


    def _AMS_CA_FOLDER_NAME(self):
        return "common_ancestor"


    def _AMS_ONGOING_MERGE_TEMP_FILENAME(self):
        return "ongoing_merge"


    def _DISK_IO_READ_SIZE_RECOMMENDATION(self):
        """ For performance reasons when reading data from a file its better to
        read this many bytes at a time, rather than 1 byte at a time. """

        return 8192

    # ------------------------------------------------------------------------------------------------------------------
    # a single setter for all of our properties
    def _set_any_const(self, value):
        """ Raises a ValueError exception to emulate language enforced constants. """

        raise ValueError("Can't change constants, don't try.")


    # ------------------------------------------------------------------------------------------------------------------
    # declare them here for outside use
    PASSWORD_PROMPT = property(_PASSWORD_PROMPT, _set_any_const)

    MERGE3_CONFLICT_DELIMITER_START = property(_MERGE3_CONFLICT_DELIMITER_START, _set_any_const)
    MERGE3_CONFLICT_DELIMITER_MIDDLE_1 = property(_MERGE3_CONFLICT_DELIMITER_MIDDLE_1, _set_any_const)
    MERGE3_CONFLICT_DELIMITER_MIDDLE_2 = property(_MERGE3_CONFLICT_DELIMITER_MIDDLE_2, _set_any_const)
    MERGE3_CONFLICT_DELIMITER_END = property(_MERGE3_CONFLICT_DELIMITER_END, _set_any_const)

    DISK_IO_READ_SIZE_RECOMMENDATION = property(_DISK_IO_READ_SIZE_RECOMMENDATION, _set_any_const)

    AMS_MERGE_RESULT_FOLDER_NAME = property(_AMS_MERGE_RESULT_FOLDER_NAME, _set_any_const)
    AMS_CA_FOLDER_NAME = property(_AMS_CA_FOLDER_NAME, _set_any_const)
    AMS_ONGOING_MERGE_TEMP_FILENAME = property(_AMS_ONGOING_MERGE_TEMP_FILENAME, _set_any_const)


UVSConst = _UVSConst()


if '__main__' == __name__:

    print UVSConst.PASSWORD_PROMPT

    # this will raise error
    # UVSConst.PASSWORD_PROMPT = 10

    print UVSConst.MERGE3_CONFLICT_DELIMITER_START
    print UVSConst.MERGE3_CONFLICT_DELIMITER_MIDDLE_1
    print UVSConst.MERGE3_CONFLICT_DELIMITER_MIDDLE_2
    print UVSConst.MERGE3_CONFLICT_DELIMITER_END

    print UVSConst.DISK_IO_READ_SIZE_RECOMMENDATION

