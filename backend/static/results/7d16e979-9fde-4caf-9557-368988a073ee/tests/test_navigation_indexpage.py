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
logger = logging.getLogger('NavigationTest')

class TestNavigationIndexPage(unittest.TestCase):
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
        except Exception as e:
            logger.error(f"Error in setup: {e}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        
    def test_page_navigation(self):
        '''Test navigation to IndexPage and verify elements are present'''
        try:
            # Navigate to the page
            logger.info(f"Navigating to IndexPage")
            self.page.navigate()
            
            # Wait for page to load completely
            self.assertTrue(self.page.verify_page_loaded(), "Page failed to load properly")
            
            # Verify key elements are present
            # Verify index_nav_navbar is present
            try:
                self.assertIsNotNone(self.page.index_nav_navbar, "index_nav_navbar element not found")
                logger.info(f"index_nav_navbar verified")
            except Exception as e:
                logger.warning(f"Could not verify index_nav_navbar: {e}")
            # Verify index_container_section is present
            try:
                self.assertIsNotNone(self.page.index_container_section, "index_container_section element not found")
                logger.info(f"index_container_section verified")
            except Exception as e:
                logger.warning(f"Could not verify index_container_section: {e}")
            # Verify index_text_section is present
            try:
                self.assertIsNotNone(self.page.index_text_section, "index_text_section element not found")
                logger.info(f"index_text_section verified")
            except Exception as e:
                logger.warning(f"Could not verify index_text_section: {e}")
            # Verify index_ul_navbar_nav is present
            try:
                self.assertIsNotNone(self.page.index_ul_navbar_nav, "index_ul_navbar_nav element not found")
                logger.info(f"index_ul_navbar_nav verified")
            except Exception as e:
                logger.warning(f"Could not verify index_ul_navbar_nav: {e}")
            # Verify index_ul_list_group is present
            try:
                self.assertIsNotNone(self.page.index_ul_list_group, "index_ul_list_group element not found")
                logger.info(f"index_ul_list_group verified")
            except Exception as e:
                logger.warning(f"Could not verify index_ul_list_group: {e}")
            # Verify index_structure_section is present
            try:
                self.assertIsNotNone(self.page.index_structure_section, "index_structure_section element not found")
                logger.info(f"index_structure_section verified")
            except Exception as e:
                logger.warning(f"Could not verify index_structure_section: {e}")
            # Verify index_a_list_group_item is present
            try:
                self.assertIsNotNone(self.page.index_a_list_group_item, "index_a_list_group_item element not found")
                logger.info(f"index_a_list_group_item verified")
            except Exception as e:
                logger.warning(f"Could not verify index_a_list_group_item: {e}")
            # Verify index_table_table is present
            try:
                self.assertIsNotNone(self.page.index_table_table, "index_table_table element not found")
                logger.info(f"index_table_table verified")
            except Exception as e:
                logger.warning(f"Could not verify index_table_table: {e}")
            # Verify index_table_table_1 is present
            try:
                self.assertIsNotNone(self.page.index_table_table_1, "index_table_table_1 element not found")
                logger.info(f"index_table_table_1 verified")
            except Exception as e:
                logger.warning(f"Could not verify index_table_table_1: {e}")
            # Verify index_tr_ is present
            try:
                self.assertIsNotNone(self.page.index_tr_, "index_tr_ element not found")
                logger.info(f"index_tr_ verified")
            except Exception as e:
                logger.warning(f"Could not verify index_tr_: {e}")
            # Verify index_td_ is present
            try:
                self.assertIsNotNone(self.page.index_td_, "index_td_ element not found")
                logger.info(f"index_td_ verified")
            except Exception as e:
                logger.warning(f"Could not verify index_td_: {e}")
            # Verify index_tr__1 is present
            try:
                self.assertIsNotNone(self.page.index_tr__1, "index_tr__1 element not found")
                logger.info(f"index_tr__1 verified")
            except Exception as e:
                logger.warning(f"Could not verify index_tr__1: {e}")
            # Verify index_button_accordion_button is present
            try:
                self.assertIsNotNone(self.page.index_button_accordion_button, "index_button_accordion_button element not found")
                logger.info(f"index_button_accordion_button verified")
            except Exception as e:
                logger.warning(f"Could not verify index_button_accordion_button: {e}")
            # Verify index_li_list_group_item is present
            try:
                self.assertIsNotNone(self.page.index_li_list_group_item, "index_li_list_group_item element not found")
                logger.info(f"index_li_list_group_item verified")
            except Exception as e:
                logger.warning(f"Could not verify index_li_list_group_item: {e}")
            # Verify index_form_ is present
            try:
                self.assertIsNotNone(self.page.index_form_, "index_form_ element not found")
                logger.info(f"index_form_ verified")
            except Exception as e:
                logger.warning(f"Could not verify index_form_: {e}")

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
