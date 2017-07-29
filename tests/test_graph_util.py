
import os
import sys

# if you got module not found errors, uncomment these. PyCharm IDE does not need it.
# get the abs version of . and .. and append them to this process's path.
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('.'))

#print sys.path

import unittest

from libuvs import graph_util as gu


class TestGraphUtil(unittest.TestCase):



    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestGraphUtil, cls).setUpClass()

        # set up some sample DAGs
        cls.invdag1 = {}

        cls.invdag1['n1'] = ['n2', 'n3']
        cls.invdag1['n2'] = ['n22', 'n7']
        cls.invdag1['n3'] = ['n4']
        cls.invdag1['n4'] = ['n7', 'n10', 'n92']
        cls.invdag1['n22'] = []
        cls.invdag1['n7'] = ['n71']
        cls.invdag1['n10'] = ['n71']
        cls.invdag1['n92'] = ['n81', 'n82', 'n85', 'n87']
        cls.invdag1['n71'] = []
        cls.invdag1['n81'] = []
        cls.invdag1['n82'] = []
        cls.invdag1['n85'] = []
        cls.invdag1['n87'] = []


        # set up some sample DAGs
        cls.dag1 = {}

        # dag has parent pointers, dvcs nodes have at most 2 parents.
        cls.dag1['n1'] = []
        cls.dag1['n2'] = ['n1']
        cls.dag1['n3'] = ['n1']
        cls.dag1['n4'] = ['n2', 'n3']
        cls.dag1['n5'] = ['n3']
        cls.dag1['n6'] = ['n4', 'n5']
        cls.dag1['n7'] = ['n2']
        cls.dag1['n8'] = ['n7']
        cls.dag1['n9'] = ['n7']
        cls.dag1['n10'] = ['n8', 'n9']






    @classmethod
    def tearDownClass(cls):

        super(TestGraphUtil, cls).tearDownClass()

        print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> tearDownClass() called"


    # setUp will run once before every test case
    def setUp(self):
        pass


    # tearDown will run once after every test case
    def tearDown(self):
        pass

    def test_dag_eca(self):
        
        self.assertEquals('n1', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n2', node2='n3' ))
        self.assertEquals('n1', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n1', node2='n2' ))
        self.assertEquals('n1', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n2', node2='n1' ))
        self.assertEquals('n1', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n1', node2='n5' ))
        self.assertEquals('n1', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n2', node2='n5' ))

        self.assertEquals('n2', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n10', node2='n6' ))
        self.assertEquals('n1', gu.dag_find_eca_slow(graph_adjacencies=self.dag1, node1='n10', node2='n5' ))



    def test_inv_dag_is_descendant_of_search(self):

        # every node is descendant of root
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n2'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n3'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n22'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n7'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n4'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n10'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n71'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n92'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n81'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n82'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n85'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n1', node_to_test='n87'))

        # root is descendant of no1
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n2'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n3'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n22'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n7'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n4'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n10'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n71'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n92'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n81'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n82'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n85'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n1', parent='n87'))


        # a couple others
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n4', node_to_test='n71'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n4', node_to_test='n10'))
        self.assertTrue(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, parent='n4', node_to_test='n85'))

        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n3', parent='n10'))
        self.assertFalse(gu.inv_dag_is_descendant_of(graph_adjacencies=self.invdag1, node_to_test='n22', parent='n4'))


if __name__ == '__main__':

    unittest.main()