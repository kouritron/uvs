
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
        invdag1_adjacencies = {}

        invdag1_adjacencies['n1'] = ['n2', 'n3']
        invdag1_adjacencies['n2'] = ['n22', 'n7']
        invdag1_adjacencies['n3'] = ['n4']
        invdag1_adjacencies['n4'] = ['n7', 'n10', 'n92']
        invdag1_adjacencies['n22'] = []
        invdag1_adjacencies['n7'] = ['n71']
        invdag1_adjacencies['n10'] = ['n71']
        invdag1_adjacencies['n92'] = ['n81', 'n82', 'n85', 'n87']
        invdag1_adjacencies['n71'] = []
        invdag1_adjacencies['n81'] = []
        invdag1_adjacencies['n82'] = []
        invdag1_adjacencies['n85'] = []
        invdag1_adjacencies['n87'] = []

        cls.invdag1 = gu.DAG(invdag1_adjacencies)

        # set up some sample DAGs
        dag1_adjacencies = {}

        # dag has parent pointers, dvcs nodes have at most 2 parents.
        dag1_adjacencies['n1'] = []
        dag1_adjacencies['n2'] = ['n1']
        dag1_adjacencies['n3'] = ['n1']
        dag1_adjacencies['n4'] = ['n2', 'n3']
        dag1_adjacencies['n5'] = ['n3']
        dag1_adjacencies['n6'] = ['n4', 'n5']
        dag1_adjacencies['n7'] = ['n2']
        dag1_adjacencies['n8'] = ['n7']
        dag1_adjacencies['n9'] = ['n7']
        dag1_adjacencies['n10'] = ['n8', 'n9']

        cls.dag1 = gu.DAG(dag1_adjacencies)




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

        test_cases = []

        test_cases.append(['n1', 'n2', 'n3'])

        test_cases.append(['n1', 'n1', 'n2'])
        test_cases.append(['n1', 'n2', 'n1'])
        test_cases.append(['n1', 'n1', 'n5'])
        test_cases.append(['n1', 'n2', 'n5'])

        test_cases.append(['n2', 'n10', 'n6'])
        test_cases.append(['n1', 'n10', 'n5'])

        test_cases.append(['n1', 'n1', 'n1'])
        test_cases.append(['n2', 'n2', 'n2'])
        test_cases.append(['n3', 'n3', 'n3'])
        test_cases.append(['n4', 'n4', 'n4'])
        test_cases.append(['n5', 'n5', 'n5'])
        test_cases.append(['n6', 'n6', 'n6'])
        test_cases.append(['n7', 'n7', 'n7'])
        test_cases.append(['n8', 'n8', 'n8'])
        test_cases.append(['n9', 'n9', 'n9'])
        test_cases.append(['n10', 'n10', 'n10'])

        self.dag1.reset_lookup_count()
        for test_case in test_cases:

            #print "testing (expected, ref1, ref2): " + str(test_case)

            # unpack test case 3-tuple
            eca_expected, ref1, ref2 = test_case

            eca_slow = gu.dag_find_eca_slow(dag=self.dag1, node1=ref1, node2=ref2)

            self.assertEquals(eca_expected, eca_slow)

        # now get the counter
        slow_cost = self.dag1.get_lookup_count()
        print "the slow algo made: " + str(slow_cost) + " many look ups"

        self.dag1.reset_lookup_count()
        for test_case in test_cases:

            #print "testing (expected, ref1, ref2): " + str(test_case)

            # unpack test case 3-tuple
            eca_expected, ref1, ref2 = test_case

            eca_found = gu.dag_find_eca_fast(dag=self.dag1, node1=ref1, node2=ref2)

            self.assertEquals(eca_expected, eca_found)

        # now get the counter
        fast_cost = self.dag1.get_lookup_count()
        print "the fast algo made: " + str(fast_cost) + " many look ups"


    def test_inv_dag_is_descendant_of_search(self):

        # every node is descendant of root
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n2'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n3'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n22'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n7'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n4'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n10'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n71'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n92'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n81'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n82'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n85'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n1', node_to_test='n87'))

        # root is descendant of no1
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n2'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n3'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n22'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n7'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n4'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n10'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n71'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n92'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n81'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n82'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n85'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n1', parent='n87'))


        # a couple others
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n4', node_to_test='n71'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n4', node_to_test='n10'))
        self.assertTrue(gu.inv_dag_is_descendant_of(dag=self.invdag1, parent='n4', node_to_test='n85'))

        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n3', parent='n10'))
        self.assertFalse(gu.inv_dag_is_descendant_of(dag=self.invdag1, node_to_test='n22', parent='n4'))


if __name__ == '__main__':

    unittest.main()