

tickets = []


# allocate new tickets
def make_tickets():

    for i in range(10):
        tickets.append("ticket_" + str(i))


# log all tickets currently in the system to terminal
def show_all_tickets():

    for ticket in tickets:
        print ticket


if '__main__' == __name__:

    make_tickets()
    show_all_tickets()