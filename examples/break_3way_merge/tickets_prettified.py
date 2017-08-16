

tickets = []


# allocate new tickets
def make_tickets():

    for i in range(10):
        tickets.append("ticket_" + str(i))


# log all tickets currently in the system to terminal
def show_all_tickets():

    term_light_blue = "\033[0;94m"
    term_reset = "\033[0;0m"

    for ticket in tickets:
        print term_light_blue + ticket + term_reset


if '__main__' == __name__:

    make_tickets()
    show_all_tickets()