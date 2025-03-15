from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PageObjects')

class BasePage:
    '''Base class for all page objects with enhanced error handling and logging'''
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
    
    def navigate_to(self, url):
        '''Navigate to a specific URL'''
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    def find_element(self, by, value, timeout=10):
        '''Find element with explicit wait and error handling'''
        try:
            logger.debug(f"Finding element: {by}={value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"Error finding element {by}={value}: {e}")
            # Take screenshot for debugging
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"error_screenshot_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            raise
    
    def find_by_id(self, id_value, timeout=10):
        return self.find_element(By.ID, id_value, timeout)
        
    def find_by_class(self, class_name, timeout=10):
        return self.find_element(By.CLASS_NAME, class_name, timeout)
    
    def find_by_name(self, name, timeout=10):
        return self.find_element(By.NAME, name, timeout)
    
    def find_by_xpath(self, xpath, timeout=10):
        return self.find_element(By.XPATH, xpath, timeout)
    
    def find_by_css(self, css, timeout=10):
        return self.find_element(By.CSS_SELECTOR, css, timeout)
    
    def find_by_tag(self, tag, timeout=10):
        return self.find_element(By.TAG_NAME, tag, timeout)
    
    def find_by_link_text(self, text, timeout=10):
        return self.find_element(By.LINK_TEXT, text, timeout)
    
    def find_by_partial_link_text(self, text, timeout=10):
        return self.find_element(By.PARTIAL_LINK_TEXT, text, timeout)
    
    def click_element(self, element):
        '''Click element with enhanced error handling and fallbacks'''
        try:
            # Wait for element to be clickable
            self.wait_for_element_clickable(element)
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)  # Wait for scroll
            
            # Try standard click
            element.click()
            logger.info(f"Clicked element: {element}")
        except Exception as e:
            logger.warning(f"Standard click failed, trying JavaScript click: {e}")
            try:
                # Try JavaScript click as fallback
                self.driver.execute_script("arguments[0].click();", element)
                logger.info("JavaScript click successful")
            except Exception as e2:
                logger.error(f"Failed to click element: {e2}")
                raise
    
    def input_text(self, element, text):
        '''Send text to element with enhanced error handling'''
        try:
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)  # Wait for scroll
            
            # Click to focus
            self.click_element(element)
            
            # Try to clear with multiple methods
            try:
                # Standard clear
                element.clear()
            except:
                # Fallback to select all + delete
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
                time.sleep(0.3)
            
            # Send keys
            element.send_keys(text)
            logger.info(f"Input text: '{text}' into element")
        except Exception as e:
            logger.warning(f"Standard input failed, trying JavaScript: {e}")
            try:
                # Try JavaScript as fallback
                self.driver.execute_script(f"arguments[0].value = '{text.replace("'", "\'")}';", element)
                logger.info("JavaScript input successful")
            except Exception as e2:
                logger.error(f"Failed to input text: {e2}")
                raise
    
    def select_option(self, select_element, option_text):
        '''Select option from dropdown by visible text'''
        try:
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)
            select.select_by_visible_text(option_text)
            logger.info(f"Selected option: '{option_text}'")
        except Exception as e:
            logger.error(f"Failed to select option '{option_text}': {e}")
            raise
    
    def get_text(self, element):
        '''Get element text with fallbacks'''
        try:
            text = element.text
            if text:
                return text
            
            # Try value attribute for inputs
            value = element.get_attribute("value")
            if value:
                return value
                
            # Fallback to JavaScript
            return self.driver.execute_script("return arguments[0].textContent;", element)
        except Exception as e:
            logger.error(f"Failed to get text: {e}")
            return ""
    
    def wait_for_element_visible(self, locator, timeout=10):
        '''Wait for element to be visible with logging'''
        logger.debug(f"Waiting for element to be visible: {locator}")
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
        
    def wait_for_element_clickable(self, element, timeout=10):
        '''Wait for element to be clickable with logging'''
        logger.debug(f"Waiting for element to be clickable")
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(element)
        )
    
    def wait_for_page_load(self, timeout=30):
        '''Wait for page to finish loading'''
        logger.debug("Waiting for page to load")
        return WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    
    def is_element_present(self, by, value, timeout=5):
        '''Check if element is present with timeout'''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except:
            return False
    
    def is_element_visible(self, by, value, timeout=5):
        '''Check if element is visible with timeout'''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except:
            return False
            
    def hover_over_element(self, element):
        '''Hover over an element'''
        try:
            ActionChains(self.driver).move_to_element(element).perform()
            logger.info("Hovered over element")
        except Exception as e:
            logger.error(f"Failed to hover over element: {e}")
            raise


class DashboardPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_dashboard_ul_(self):
        """Get the dashboard_ul_ element"""
        try:
            return self.find_by_xpath("//ul[contains(text(), 'Home\nAnalytics\nSettings\nUsers\nReports')]")
        except Exception as e:
            logger.error(f"Error finding dashboard_ul_: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_ul_(self):
        return self._get_dashboard_ul_()

    def _get_dashboard_input_(self):
        """Get the dashboard_input_ element"""
        try:
            return self.find_by_xpath('//div[2]/div[1]/div[2]/input')
        except Exception as e:
            logger.error(f"Error finding dashboard_input_: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_input_(self):
        return self._get_dashboard_input_()

    def set_dashboard_input_(self, text):
        """Set text in the dashboard_input_"""
        element = self._get_dashboard_input_()
        self.input_text(element, text)
        return self

    def _get_dashboard_div_dashboard_card(self):
        """Get the dashboard_div_dashboard_card element"""
        try:
            return self.find_by_class('dashboard-card')
        except Exception as e:
            logger.error(f"Error finding dashboard_div_dashboard_card: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_div_dashboard_card(self):
        return self._get_dashboard_div_dashboard_card()

    def get_dashboard_div_dashboard_card_text(self):
        """Get text from dashboard_div_dashboard_card"""
        element = self._get_dashboard_div_dashboard_card()
        return self.get_text(element)

    def _get_dashboard_div_dashboard_card_1(self):
        """Get the dashboard_div_dashboard_card_1 element"""
        try:
            return self.find_by_class('dashboard-card')
        except Exception as e:
            logger.error(f"Error finding dashboard_div_dashboard_card_1: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_div_dashboard_card_1(self):
        return self._get_dashboard_div_dashboard_card_1()

    def get_dashboard_div_dashboard_card_1_text(self):
        """Get text from dashboard_div_dashboard_card_1"""
        element = self._get_dashboard_div_dashboard_card_1()
        return self.get_text(element)

    def _get_dashboard_div_dashboard_card_2(self):
        """Get the dashboard_div_dashboard_card_2 element"""
        try:
            return self.find_by_class('dashboard-card')
        except Exception as e:
            logger.error(f"Error finding dashboard_div_dashboard_card_2: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_div_dashboard_card_2(self):
        return self._get_dashboard_div_dashboard_card_2()

    def get_dashboard_div_dashboard_card_2_text(self):
        """Get text from dashboard_div_dashboard_card_2"""
        element = self._get_dashboard_div_dashboard_card_2()
        return self.get_text(element)

    def verify_page_loaded(self):
        """Verify that the DashboardPage is loaded correctly"""
        return self.is_element_visible(By.CSS_SELECTOR, '.dashboard-card')


class LiPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the LiPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class DivPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the DivPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class SpanPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_span__(self):
        """Get the span__ element"""
        try:
            return self.find_by_xpath("//span[contains(text(), '🔔')]")
        except Exception as e:
            logger.error(f"Error finding span__: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def span__(self):
        return self._get_span__()

    def get_span___text(self):
        """Get text from span__"""
        element = self._get_span__()
        return self.get_text(element)

    def _get_span___1(self):
        """Get the span___1 element"""
        try:
            return self.find_by_xpath("//span[contains(text(), '⚙️')]")
        except Exception as e:
            logger.error(f"Error finding span___1: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def span___1(self):
        return self._get_span___1()

    def get_span___1_text(self):
        """Get text from span___1"""
        element = self._get_span___1()
        return self.get_text(element)

    def verify_page_loaded(self):
        """Verify that the SpanPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None
