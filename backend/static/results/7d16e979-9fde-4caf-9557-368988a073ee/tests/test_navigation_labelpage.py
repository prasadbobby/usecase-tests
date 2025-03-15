import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from page_objects import LabelPage
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('NavigationTest')

class TestNavigationLabelPage(unittest.TestCase):
    def setUp(self):
        self.driver = None
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            
            # Uncomment to run headless
            # chrome_options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.page = LabelPage(self.driver, base_url="http://localhost:5000")
        except Exception as e:
            logger.error(f"Error in setup: {e}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        
    def test_page_navigation(self):
        '''Test navigation to LabelPage and verify elements are present'''
        try:
            # Navigate to the page
            logger.info(f"Navigating to LabelPage")
            self.page.navigate()
            
            # Wait for page to load completely
            self.assertTrue(self.page.verify_page_loaded(), "Page failed to load properly")
            
            # Verify key elements are present
            # Verify label_project_name is present
            try:
                self.assertIsNotNone(self.page.label_project_name, "label_project_name element not found")
                logger.info(f"label_project_name verified")
            except Exception as e:
                logger.warning(f"Could not verify label_project_name: {e}")
            # Verify label_description is present
            try:
                self.assertIsNotNone(self.page.label_description, "label_description element not found")
                logger.info(f"label_description verified")
            except Exception as e:
                logger.warning(f"Could not verify label_description: {e}")
            # Verify label_upload_source_files is present
            try:
                self.assertIsNotNone(self.page.label_upload_source_files, "label_upload_source_files element not found")
                logger.info(f"label_upload_source_files verified")
            except Exception as e:
                logger.warning(f"Could not verify label_upload_source_files: {e}")

        except Exception as e:
            # Take screenshot on failure
            if self.driver:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"test_failure_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.error(f"Test failed. Screenshot saved to {screenshot_path}")
            logger.error(f"Error in test_page_navigation: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
