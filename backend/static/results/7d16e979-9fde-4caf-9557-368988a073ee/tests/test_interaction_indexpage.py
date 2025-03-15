import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from page_objects import IndexPage
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('InteractionTest')

class TestInteractionIndexPage(unittest.TestCase):
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
            self.page = IndexPage(self.driver, base_url="http://localhost:5000")
            
            # Navigate to the page
            self.page.navigate()
            
            # Wait for page to load
            self.assertTrue(self.page.verify_page_loaded(), "Page failed to load properly")
        except Exception as e:
            logger.error(f"Error in setup: {e}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()

    def test_click_index_a_list_group_item(self):
        '''Test clicking the index_a_list_group_item element'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.index_a_list_group_item, "index_a_list_group_item not found")
            
            # Click the element
            logger.info(f"Clicking index_a_list_group_item")
            self.page.click_index_a_list_group_item()
            
            # Wait after click to see results
            time.sleep(1)
            
            # Add assertions for expected behavior after click
            # For example, check if URL changed, new elements appeared, etc.
            pass
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"click_index_a_list_group_item_failure_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {screenshot_path}")
            logger.error(f"Error in test_click_index_a_list_group_item: {e}")
            raise

    def test_click_index_button_accordion_button(self):
        '''Test clicking the index_button_accordion_button element'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.index_button_accordion_button, "index_button_accordion_button not found")
            
            # Click the element
            logger.info(f"Clicking index_button_accordion_button")
            self.page.click_index_button_accordion_button()
            
            # Wait after click to see results
            time.sleep(1)
            
            # Add assertions for expected behavior after click
            # For example, check if URL changed, new elements appeared, etc.
            pass
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"click_index_button_accordion_button_failure_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {screenshot_path}")
            logger.error(f"Error in test_click_index_button_accordion_button: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
