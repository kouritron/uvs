



_DISABLE_ALL_LOGS = True


##----------------------------------------------------------------------------------------------------------------------
##----------------------------------------------------------------------------------------------------------------------
##----------------------------------------------------------------------------------------------------------------------
##----------------------------------------------------------------------------------------------------------------------

_DISABLE_LOG_CLASS_HAZARD = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_V = _DISABLE_ALL_LOGS or False

_DISABLE_LOG_CLASS_VV = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_VVV = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_VVVV = _DISABLE_ALL_LOGS or True
_DISABLE_LOG_CLASS_FEFR = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_FEFRV = _DISABLE_ALL_LOGS or True
_DISABLE_LOG_CLASS_FP = _DISABLE_ALL_LOGS or True

_DISABLE_LOG_CLASS_DAO = _DISABLE_ALL_LOGS or True
_DISABLE_LOG_CLASS_DAOV = _DISABLE_ALL_LOGS or True

# CM and CMV are logs for crypt manager module.
_DISABLE_LOG_CLASS_CM = _DISABLE_ALL_LOGS or True
_DISABLE_LOG_CLASS_CMV = _DISABLE_ALL_LOGS or True

# CLI and CLIV are logs for command line UI
_DISABLE_LOG_CLASS_CLI = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_CLIV = _DISABLE_ALL_LOGS or True

# UVSMGR and UVSMGRV are logs for command line UI
_DISABLE_LOG_CLASS_UVSMGR = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_UVSMGRV = _DISABLE_ALL_LOGS or True


# history DAG related msgs
_DISABLE_LOG_CLASS_DAG = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_DAGV = _DISABLE_ALL_LOGS or True

# history DAG related msgs
_DISABLE_LOG_CLASS_AMS = _DISABLE_ALL_LOGS or False
_DISABLE_LOG_CLASS_AMSV = _DISABLE_ALL_LOGS or True


# re enable a couple temp ones:
_DISABLE_LOG_CLASS_V = False

# _DISABLE_LOG_CLASS_AMS = False






# the 1 appears to make it bold, color is after that
term_red   = "\033[1;31m"
term_light_red   = "\033[0;91m"
term_green = "\033[0;32m"
term_light_green = "\033[5;49;92m"

term_yellow = "\033[1;33m"
term_light_yellow = "\033[0;93m"
term_light_blue = "\033[0;94m"
term_light_cyan = "\033[0;96m"

term_blue  = "\033[1;34m"
term_purple = "\033[0;35m"
term_cyan  = "\033[1;36m"
term_white_bold = "\033[1;38m"


term_reset = "\033[0;0m"
term_bold    = "\033[;1m"
term_reverse = "\033[;7m"
term_warning = '\033[93m'
term_fail = '\033[91m'
term_endc = '\033[0m'
term_underline = '\033[4m'

#-----------------------------------------------------------------------------------------------------------------------
def fefrv(msg, label=True):
    """ Print log msgs for "function entry, function return verified" category. """

    if _DISABLE_LOG_CLASS_FEFRV:
        return

    final_msg = None

    if label:
        final_msg = 'fefrv: ' + str(msg)
    else:
        final_msg =  str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def fefr(msg, label=True):
    """ Print log msgs for "function entry, function return" category. """

    if _DISABLE_LOG_CLASS_FEFR:
        return

    final_msg = None

    if label:
        final_msg = 'fefr: ' + str(msg)
    else:
        final_msg =  str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def vvvv(msg, label=True):
    """ print log msgs that are in "triple verbose and verified" category. """

    if _DISABLE_LOG_CLASS_VVVV:
        return

    final_msg = None

    if label:
        final_msg = 'vvvv: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg



#-----------------------------------------------------------------------------------------------------------------------
def vvv(msg, label=True):
    """ print log msgs that are in "triple verbose" category. """

    if _DISABLE_LOG_CLASS_VVV:
        return

    final_msg = None

    if label:
        final_msg = 'vvv: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def vv(msg, label=True):
    """ print log msgs that are in "double verbose" category. """

    if _DISABLE_LOG_CLASS_VV:
        return

    final_msg = None

    if label:
        final_msg = 'vv: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def v(msg, label=True):
    """ print log msgs that are in "single verbose" category. """

    if _DISABLE_LOG_CLASS_V:
        return

    final_msg = None

    if label:
        final_msg = 'v: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_cyan + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def fp(msg, label=True):
    """ print log msgs related to objects and their fingerprints . """

    if _DISABLE_LOG_CLASS_FP:
        return

    final_msg = None

    if label:
        final_msg = 'fp: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_yellow + final_msg + term_reset

#-----------------------------------------------------------------------------------------------------------------------
def dao(msg, label=True):
    """ print log msgs belonging to the data access objects. """

    if _DISABLE_LOG_CLASS_DAO:
        return

    final_msg = None

    if label:
        final_msg = 'dao: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_green + final_msg + term_reset

#-----------------------------------------------------------------------------------------------------------------------
def daov(msg, label=True):
    """ print the verbose log msgs belonging to the data access objects. """

    if _DISABLE_LOG_CLASS_DAOV:
        return

    final_msg = None

    if label:
        final_msg = 'dao verbose: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_green + final_msg + term_reset

#-----------------------------------------------------------------------------------------------------------------------
def cmv(msg, label=True):
    """ print the verbose log msgs belonging to the crypt manager. """

    if _DISABLE_LOG_CLASS_CMV:
        return

    final_msg = None

    if label:
        final_msg = 'cm verbose: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_red + final_msg + term_reset

#-----------------------------------------------------------------------------------------------------------------------
def cm(msg, label=True):
    """ print the  log msgs belonging to the crypt manager. """

    if _DISABLE_LOG_CLASS_CM:
        return

    final_msg = None

    if label:
        final_msg = 'cm: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_red + final_msg + term_reset

#-----------------------------------------------------------------------------------------------------------------------
def hazard(msg, label=True):
    """ print log msgs that are in "hazardous" category. These msgs should not be printed in a production build. """

    if _DISABLE_LOG_CLASS_HAZARD:
        return

    final_msg = None

    if label:
        final_msg =  '***** hazardous log: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_red + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def cli(msg, label=True):
    """ print the log msgs belonging to the cmd line interface . """

    if _DISABLE_LOG_CLASS_CLI:
        return

    final_msg = None

    if label:
        final_msg = 'cli: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg

#-----------------------------------------------------------------------------------------------------------------------
def cliv(msg, label=True):
    """ print the log msgs belonging to the cmd line interface verbose category . """

    if _DISABLE_LOG_CLASS_CLIV:
        return

    final_msg = None

    if label:
        final_msg = 'cli verbose: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg

#-----------------------------------------------------------------------------------------------------------------------
def uvsmgr(msg, label=True):
    """ print the log msgs belonging to the uvs manager. """

    if _DISABLE_LOG_CLASS_UVSMGR:
        return

    final_msg = None

    if label:
        final_msg = 'uvs manager: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_blue + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def uvsmgrv(msg, label=True):
    """ print the log msgs belonging to the uvs manager verbose category . """

    if _DISABLE_LOG_CLASS_UVSMGRV:
        return

    final_msg = None

    if label:
        final_msg = 'uvs manager verbose: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_blue + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def dag(msg, label=True):
    """ print DAG related log msgs. """

    if _DISABLE_LOG_CLASS_DAG:
        return

    final_msg = None

    if label:
        final_msg = 'DAG: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_green + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def dagv(msg, label=True):
    """ print the verbose DAG related log msgs. """

    if _DISABLE_LOG_CLASS_DAGV:
        return

    final_msg = None

    if label:
        final_msg = 'DAG verbose: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_green + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def ams(msg, label=True):
    """ print Auto Merge Service related log msgs. """

    if _DISABLE_LOG_CLASS_AMS:
        return

    final_msg = None

    if label:
        final_msg = 'AMS: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_green + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def amsv(msg, label=True):
    """ print the verbose Auto Merge Service related log msgs. """

    if _DISABLE_LOG_CLASS_AMSV:
        return

    final_msg = None

    if label:
        final_msg = 'AMSV verbose: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_green + final_msg + term_reset