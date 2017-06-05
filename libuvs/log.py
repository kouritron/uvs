

from systemdefaults import should_print_insecure_log_msgs

# the 1 appears to make it bold, color is after that
term_red   = "\033[1;31m"
term_green = "\033[0;32m"
term_yellow = "\033[1;33m"
term_light_yellow = "\033[0;93m"
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

    if True:
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

    final_msg = None

    if label:
        final_msg = 'fefr: ' + str(msg)
    else:
        final_msg =  str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def vvvv(msg, label=True):
    """ print log msgs that are in "triple verbose and verified" category. """

    if True:
        return

    final_msg = None

    if label:
        final_msg = 'vvv: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg



#-----------------------------------------------------------------------------------------------------------------------
def vvv(msg, label=True):
    """ print log msgs that are in "triple verbose" category. """

    final_msg = None

    if label:
        final_msg = 'vvv: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def vv(msg, label=True):
    """ print log msgs that are in "double verbose" category. """

    final_msg = None

    if label:
        final_msg = 'vv: ' + str(msg)
    else:
        final_msg = str(msg)

    print final_msg


#-----------------------------------------------------------------------------------------------------------------------
def v(msg, label=True):
    """ print log msgs that are in "single verbose" category. """

    final_msg = None

    if label:
        final_msg = 'v: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_cyan + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def fp(msg, label=True):
    """ print log msgs related to objects and their fingerprints . """

    final_msg = None

    if label:
        final_msg = 'fp: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_light_yellow + final_msg + term_reset


#-----------------------------------------------------------------------------------------------------------------------
def hazard(msg, label=True):
    """ print log msgs that are in "hazardous" category. These msgs should not be printed in a production build. """

    if not should_print_insecure_log_msgs:
        return

    final_msg = None

    if label:
        final_msg =  '***** hazardous log: ' + str(msg)
    else:
        final_msg = str(msg)

    print term_red + final_msg + term_reset



