

## UVSError handling guidelines:

# 1- don't use OOP exceptions, NEVER NEVER NEVER use inheritance in exceptions
#       i dont like exception X that inherits from Y and 2mrw is a G then suddenly catches an F blah blah
#       doing the above makes it harder not easier to figure out what the hell happened.
#       just use one exception class. return a descriptive msg as to what happened. and if more specifity is needed
#       associate an error code with that exception and enumerate the errors
#       (i.e. 1 means permission denied, 2 means mac failed ..... ) this is so far not needed.
#       if it was needed we code add something like uvs_error_no field to this class and enumerate the
#       the different error codes in this module.
#       (python shamefully has no constants but there is trick to be done with properties, and raise Error on set
#       that pretty much gives us the same thing as language enforced constants, google it)
#
# 2- exceptions are not return values, dont ever use exceptions to communicate results from a sub-routine.
#       exceptions are meant to indicate a catastrophic situation that required an immediate termination
#       to whatever was happening. for example if a key was not found do NOT raise an exception, return None
#       an exception must terminate something. sometimes it should terminate the process. sometimes
#       it terminates a thread, sometimes it should terminate a web request. its not a return value.
#       it should be used like golang's panic call.
#
#




class UVSError(Exception):
    pass
