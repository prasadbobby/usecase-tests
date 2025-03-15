import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from page_objects import TextareaPage
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('InteractionTest')

class TestInteractionTextareaPage(unittest.TestCase):
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
            self.page = TextareaPage(self.driver, base_url="http://localhost:5000")
            
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

    def test_input_textarea_description(self):
        '''Test inputting text into the textarea_description field'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.textarea_description, "textarea_description not found")
            
            # Input text
            test_text = "Test input text"
            logger.info(f"Setting text in textarea_description: {test_text}")
            self.page.set_textarea_description(test_text)
            
            # Wait after input to see results
            time.sleep(1)
            
            # Add assertions to verify the input was successful
            # For example, check if value attribute matches input
            # element_value = self.page.textarea_description.get_attribute("value")
            # self.assertEqual(element_value, test_text, "Input text verification failed")
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"input_textarea_description_failure_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {screenshot_path}")
            logger.error(f"Error in test_input_textarea_description: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
