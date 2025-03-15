import unittest
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestSuite')

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_navigation_dashboardpage import *
from test_interaction_dashboardpage import *
from test_navigation_lipage import *
from test_navigation_divpage import *
from test_navigation_spanpage import *

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    loader = unittest.TestLoader()
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationDashboardPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestInteractionDashboardPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationLiPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationDivPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationSpanPage))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
