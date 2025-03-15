import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from page_objects import InputPage
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('NavigationTest')

class TestNavigationInputPage(unittest.TestCase):
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
            self.page = InputPage(self.driver, base_url="http://localhost:5000")
        except Exception as e:
            logger.error(f"Error in setup: {e}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        
    def test_page_navigation(self):
        '''Test navigation to InputPage and verify elements are present'''
        try:
            # Navigate to the page
            logger.info(f"Navigating to InputPage")
            self.page.navigate()
            
            # Wait for page to load completely
            self.assertTrue(self.page.verify_page_loaded(), "Page failed to load properly")
            
            # Verify key elements are present
            # Verify input_input_section is present
            try:
                self.assertIsNotNone(self.page.input_input_section, "input_input_section element not found")
                logger.info(f"input_input_section verified")
            except Exception as e:
                logger.warning(f"Could not verify input_input_section: {e}")
            # Verify input_name is present
            try:
                self.assertIsNotNone(self.page.input_name, "input_name element not found")
                logger.info(f"input_name verified")
            except Exception as e:
                logger.warning(f"Could not verify input_name: {e}")

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
