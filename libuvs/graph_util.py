

import log


# A quick queue based on python lists.
class Queue():

    def __init__(self):

        self.queue_items = []


    def is_empty(self):
        return 0 == len(self.queue_items)


    def size(self):

        return len(self.queue_items)


    def enqueue(self, item):
        log.dagv("enqueuing item: " + str(item))
        self.queue_items.insert(0, item)


    def dequeue(self):
        return self.queue_items.pop()




def is_descendant_of(graph_adjacencies, parent, node_to_test):
    """ Given an inverted DAG (graph with parent to kid pointers), return True if node_to_test is
    a descendant of parent. False otherwise.
    """

    # adjacencies must be a dict of node to a list of its neighbors (kids in this case)
    assert isinstance(graph_adjacencies, dict)

    # parent and node_to_test muse be snapids as str or unicode.
    assert isinstance(parent, str) or isinstance(parent, unicode)
    assert isinstance(node_to_test, str) or isinstance(node_to_test, unicode)

    # it doesnt make sense to merge parent with itself, so this case should've been caught earlier. if in the future
    # this function was needed for something other than merging maybe remove this line.
    assert parent != node_to_test

    # start a bfs search from parent and keep going down until we wither meet node_to_test, or run out of nodes
    # we could comment out all the prev_seen lines, every thing would still work correct
    # since this is supposed to be a inverted DAG, there are no cycles. however we might visit some nodes twice. 

    prev_seen = set()
    bfs_queue = Queue()

    bfs_queue.enqueue(parent)
    prev_seen.add(parent)

    while not bfs_queue.is_empty():

        current_node = bfs_queue.dequeue()

        if current_node == node_to_test:
            return True

        for kid in graph_adjacencies[current_node]:

            # if this does not hold its not really a DAG.
            if kid not in prev_seen:
                prev_seen.add(kid)
                bfs_queue.enqueue(kid)




