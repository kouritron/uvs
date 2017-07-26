

# TODO: this file is to be demolished/removed or at least refactored down to a minimum along with usage of exceptions
# i have decided that exceptions are evil. and object oriented exceptions are truly a remarkable category of crap.
# assign a an error number to each specific error case, return error codes and handle them
# separately and in due time. Its better to just return error codes (along with optional msgs) from function calls
# than to use exceptions. most of golang community also agrees with me on this.
# exceptions should be used for truly exceptional cases. they should almost always be pretty close
# to log something onto the correct output; exit();
# if you are raising and recovering from exceptions frequently, you are probably doing something very wrong
# notwithstanding the BS pythonic culture of using exceptions overly and often.
# i cant explain too much more here, than to say keep exceptions for truly catastrophic situations, there is no
# need to use exceptions to duplicate ways to return values from function calls




class UVSError(Exception):
    pass


class UVSErrorInvalidSnapshot(UVSError):
    pass


class UVSErrorInvalidTree(UVSError):
    pass


class UVSErrorInvalidFile(UVSError):
    pass


class UVSErrorInvalidDestinationDirectory(UVSError):
    pass


class UVSErrorInvalidRepository(UVSError):
    pass


class UVSErrorTableDoesNotHaveSuchKey(UVSError):
    pass


class UVSErrorTamperDetected(UVSError):
    pass