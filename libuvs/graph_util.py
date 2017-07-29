

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


# a graph class that export a unified interface to get the neighbors of some node, regardless of whether the DAG
# is in memory or on disk, or some combination of that.
class DAG():
    pass



# this is a easy to verify but slow algorithm for finding earliest common ancestor in a DAG. we also have a fast one.
# the main point of the slow algo is to test the correctness of the fast one.
# the fast algo has amortized O(1) space and time complexity, worst case O(n) space and time.
# the slow algo has  O(2n) space and time complexity
# considering the graph is sitting on disk, 2n look ups may very well be unacceptable for a repo with
# few hundred kilo commits in it.
def dag_find_eca_slow(graph_adjacencies, node1, node2):
    """ Find the earliest common ancestor of the nodes in a regular DAG (DAG with parent pointers
    as opposed to kid pointers)
    """

    # adjacencies must be a dict of node to a list of its parents
    assert isinstance(graph_adjacencies, dict)

    # parent and node_to_test muse be snapids as str or unicode.
    assert isinstance(node1, str) or isinstance(node1, unicode)
    assert isinstance(node2, str) or isinstance(node2, unicode)

    # make a set of all ancestors
    node1_ancestors = set()

    node1_q = Queue()

    node1_q.enqueue(node1)

    while not node1_q.is_empty():

        node1_ancestor = node1_q.dequeue()

        node1_ancestors.add(node1_ancestor)

        for node1_ancestor_parent in graph_adjacencies[node1_ancestor]:

            # if this is a new ancestor
            if node1_ancestor_parent not in node1_ancestors:
                node1_ancestors.add(node1_ancestor_parent)
                node1_q.enqueue(node1_ancestor_parent)


    # now we have all of node1 ancestors.
    node2_q = Queue()
    node2_bfs_seen_before = set()

    node2_q.enqueue(node2)

    while not node2_q.is_empty():

        node2_ancestor = node2_q.dequeue()

        if node2_ancestor in node1_ancestors:
            return node2_ancestor

        for node2_ancestor_parent in graph_adjacencies[node2_ancestor]:

            if node2_ancestor_parent not in node2_bfs_seen_before:
                node2_q.enqueue(node2_ancestor_parent)
                node2_bfs_seen_before.add(node2_ancestor_parent)


    # if we have not returned by now,that means that node1 and node2 had no common ancestor.
    # it also means that the DAG does not have a root that is the ancestors of all nodes, and has disconnected
    # partitions, this is an error in case of a uvs repo history DAG
    assert False, "invalid DAG"




def inv_dag_is_descendant_of(graph_adjacencies, parent, node_to_test):
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

            if kid not in prev_seen:
                prev_seen.add(kid)
                bfs_queue.enqueue(kid)




