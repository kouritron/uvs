

import log


# A quick queue based on python lists.
class Queue():

    def __init__(self):

        self.queue_items = []


    def is_empty(self):
        return 0 == len(self.queue_items)


    def has_items(self):
        return 0 != len(self.queue_items)


    def size(self):

        return len(self.queue_items)


    def enqueue(self, item):
        log.dagv("enqueuing item: " + str(item))
        self.queue_items.insert(0, item)


    def dequeue(self):
        return self.queue_items.pop()


# a graph class that export a unified interface to get the neighbors of some node, regardless of whether the DAG
# is in memory or on disk, or some combination of that + some utilities like counting DAG lookups (for benchmarking)
class DAG():

    def __init__(self, graph_adjacencies):

        # adjacencies must be a dict of node to a list of its parents
        assert isinstance(graph_adjacencies, dict)

        self.adjacencies = graph_adjacencies

        self.lookup_count = 0


    def reset_lookup_count(self):

        self.lookup_count = 0


    def get_lookup_count(self):

        return self.lookup_count


    def get_neighbors(self, node):

        self.lookup_count = self.lookup_count + 1

        if node in self.adjacencies:
            return self.adjacencies[node]

        else:
            assert False, "Invalid DAG lookup"





# this is a easy to verify but slow algorithm for finding earliest common ancestor in a DAG. we also have a fast one.
# the main point of the slow algo is to test the correctness of the fast one.
# the fast algo has amortized O(1) space and time complexity, worst case O(n) space and time.
# the slow algo has  O(2n) space and time complexity
# considering the graph is sitting on disk, 2n look ups may very well be unacceptable for a repo with
# few hundred kilo commits in it.
def dag_find_eca_slow(dag, node1, node2):
    """ Find the earliest common ancestor of the nodes in a regular DAG (DAG with parent pointers
    as opposed to kid pointers)
    """

    assert isinstance(dag, DAG)

    # parent and node_to_test muse be snapids as str or unicode.
    assert isinstance(node1, str) or isinstance(node1, unicode)
    assert isinstance(node2, str) or isinstance(node2, unicode)

    # make a set of all ancestors
    node1_ancestors = set()

    node1_q = Queue()

    node1_q.enqueue(node1)
    node1_ancestors.add(node1)

    while node1_q.has_items():

        node1_ancestor = node1_q.dequeue()

        for node1_ancestor_parent in dag.get_neighbors(node1_ancestor):

            # if this is a new ancestor
            if node1_ancestor_parent not in node1_ancestors:
                node1_ancestors.add(node1_ancestor_parent)
                node1_q.enqueue(node1_ancestor_parent)


    # now we have all of node1 ancestors.
    node2_q = Queue()
    node2_bfs_seen_before = set()

    node2_bfs_seen_before.add(node2)
    node2_q.enqueue(node2)

    while node2_q.has_items():

        node2_ancestor = node2_q.dequeue()

        if node2_ancestor in node1_ancestors:
            return node2_ancestor

        for node2_ancestor_parent in dag.get_neighbors(node2_ancestor):

            if node2_ancestor_parent not in node2_bfs_seen_before:
                node2_q.enqueue(node2_ancestor_parent)
                node2_bfs_seen_before.add(node2_ancestor_parent)


    # if we have not returned by now,that means that node1 and node2 had no common ancestor.
    # it also means that the DAG does not have a root that is the ancestors of all nodes, and has disconnected
    # partitions, this is an error in case of a uvs repo history DAG
    assert False, "invalid DAG"


# this algo is faster but i am not sure its 100% correct
def dag_find_eca_fast(dag, node1, node2):
    """ Find the earliest common ancestor of the nodes in a regular DAG (DAG with parent pointers
    as opposed to kid pointers).
    """

    assert isinstance(dag, DAG)

    # parent and node_to_test muse be snapids as str or unicode.
    assert isinstance(node1, str) or isinstance(node1, unicode)
    assert isinstance(node2, str) or isinstance(node2, unicode)

    # make a set of all ancestors
    n1_ancestors = set()
    n2_ancestors = set()

    q1 = Queue()
    q1.enqueue(node1)
    n1_ancestors.add(node1)

    q2 = Queue()
    q2.enqueue(node2)
    n2_ancestors.add(node2)

    while q1.has_items() or q2.has_items():

        #
        if q1.has_items():

            # get the next ancestor of node 1
            n1_a = q1.dequeue()

            # if it also is an ancestor of n2, its a common ancestor and
            if n1_a in n2_ancestors:
                return n1_a

            for n1_a_parent in dag.get_neighbors(n1_a):
                if n1_a_parent not in n1_ancestors:
                    q1.enqueue(n1_a_parent)
                    n1_ancestors.add(n1_a_parent)


        #
        if q2.has_items():

            # get the next ancestor of node 2
            n2_a = q2.dequeue()

            # if it also is an ancestor of n2, its a common ancestor and
            if n2_a in n1_ancestors:
                return n2_a

            for n2_a_parent in dag.get_neighbors(n2_a):
                if n2_a_parent not in n2_ancestors:
                    q2.enqueue(n2_a_parent)
                    n2_ancestors.add(n2_a_parent)



    # if we have not returned by now,that means that node1 and node2 had no common ancestor.
    # it also means that the DAG does not have a root that is the ancestors of all nodes, and has disconnected
    # partitions, this is an error in case of a uvs repo history DAG
    assert False, "invalid DAG"





def inv_dag_is_descendant_of(dag, parent, node_to_test):
    """ Given an inverted DAG (graph with parent to kid pointers), return True if node_to_test is
    a descendant of parent. False otherwise.
    """

    assert isinstance(dag, DAG)

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

    while bfs_queue.has_items():

        current_node = bfs_queue.dequeue()

        if current_node == node_to_test:
            return True

        for kid in dag.get_neighbors(current_node):

            if kid not in prev_seen:
                prev_seen.add(kid)
                bfs_queue.enqueue(kid)




if '__main__' == __name__:


    dag1 = {}

    # dag has parent pointers, dvcs nodes have at most 2 parents.
    dag1['n1'] = []
    dag1['n2'] = ['n1']
    dag1['n3'] = ['n1']
    dag1['n4'] = ['n2', 'n3']
    dag1['n5'] = ['n3']
    dag1['n6'] = ['n4', 'n5']
    dag1['n7'] = ['n2']
    dag1['n8'] = ['n7']
    dag1['n9'] = ['n7']
    dag1['n10'] = ['n8', 'n9']


    print dag_find_eca_fast(dag1, node1='n2', node2='n3')