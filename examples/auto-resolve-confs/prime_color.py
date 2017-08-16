

def is_even(x):
    """ Return True if x is an even number. False if x is odd.
    """

    assert isinstance(x, int)
    assert x > 1

    if (x % 2) == 0:
        return True

    # if not even that odd.
    return False




def is_prime(x):
    """ Return True if x is a prime number. False otherwise.
    """

    assert isinstance(x, int)
    assert x > 1

    if is_even(x):
        return False

    for i in xrange(2, x):

        # print "i: " + str(i)
        if (x % i) == 0:
            return False

    return True




if '__main__' == __name__:


    for i in range(2, 20):

        if is_prime(i):

            term_color = "\033[0;94m"
            term_reset = "\033[0;0m"
            print term_color + "number " + str(i) + " is prime." + term_reset

        else:
            print "number " + str(i) + " is NOT prime."








