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
from test_navigation_indexpage import *
from test_interaction_indexpage import *
from test_navigation_apage import *
from test_interaction_apage import *
from test_navigation_buttonpage import *
from test_interaction_buttonpage import *
from test_navigation_formpage import *
from test_navigation_inputpage import *
from test_interaction_inputpage import *
from test_navigation_trpage import *
from test_navigation_tdpage import *
from test_navigation_labelpage import *
from test_navigation_textareapage import *
from test_interaction_textareapage import *

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
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationIndexPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestInteractionIndexPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationAPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestInteractionAPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationButtonPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestInteractionButtonPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationFormPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationInputPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestInteractionInputPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationTrPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationTdPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationLabelPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNavigationTextareaPage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestInteractionTextareaPage))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
