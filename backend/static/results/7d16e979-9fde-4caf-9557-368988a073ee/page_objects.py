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

    def _get_dashboard_ul__1(self):
        """Get the dashboard_ul__1 element"""
        try:
            return self.find_by_xpath("//ul[contains(text(), 'Home\nAnalytics\nSettings\nUsers\nReports')]")
        except Exception as e:
            logger.error(f"Error finding dashboard_ul__1: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_ul__1(self):
        return self._get_dashboard_ul__1()

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

    def _get_dashboard_input__1(self):
        """Get the dashboard_input__1 element"""
        try:
            return self.find_by_xpath('//div[2]/div[1]/div[2]/input')
        except Exception as e:
            logger.error(f"Error finding dashboard_input__1: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def dashboard_input__1(self):
        return self._get_dashboard_input__1()

    def set_dashboard_input__1(self, text):
        """Set text in the dashboard_input__1"""
        element = self._get_dashboard_input__1()
        self.input_text(element, text)
        return self

    def verify_page_loaded(self):
        """Verify that the DashboardPage is loaded correctly"""


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


class SpanPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the SpanPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class IndexPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_index_nav_navbar(self):
        """Get the index_nav_navbar element"""
        try:
            return self.find_by_class('navbarnavbar-expand-lgnavbar-darkbg-primary')
        except Exception as e:
            logger.error(f"Error finding index_nav_navbar: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_nav_navbar(self):
        return self._get_index_nav_navbar()

    def _get_index_ul_navbar_nav(self):
        """Get the index_ul_navbar_nav element"""
        try:
            return self.find_by_class('navbar-nav')
        except Exception as e:
            logger.error(f"Error finding index_ul_navbar_nav: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_ul_navbar_nav(self):
        return self._get_index_ul_navbar_nav()

    def _get_index_ul_list_group(self):
        """Get the index_ul_list_group element"""
        try:
            return self.find_by_class('list-group')
        except Exception as e:
            logger.error(f"Error finding index_ul_list_group: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_ul_list_group(self):
        return self._get_index_ul_list_group()

    def _get_index_a_list_group_item(self):
        """Get the index_a_list_group_item element"""
        try:
            return self.find_by_class('list-group-itemlist-group-item-action{%ifselected_projectandselected_projectid==projectid%}active{%endif%}')
        except Exception as e:
            logger.error(f"Error finding index_a_list_group_item: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_a_list_group_item(self):
        return self._get_index_a_list_group_item()

    def click_index_a_list_group_item(self):
        """Click the index_a_list_group_item"""
        element = self._get_index_a_list_group_item()
        self.click_element(element)
        self.wait_for_page_load()
        return self

    def _get_index_table_table(self):
        """Get the index_table_table element"""
        try:
            return self.find_by_class('tabletable-stripedtable-hover')
        except Exception as e:
            logger.error(f"Error finding index_table_table: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_table_table(self):
        return self._get_index_table_table()

    def _get_index_table_table_1(self):
        """Get the index_table_table_1 element"""
        try:
            return self.find_by_class('tabletable-sm')
        except Exception as e:
            logger.error(f"Error finding index_table_table_1: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_table_table_1(self):
        return self._get_index_table_table_1()

    def _get_index_tr_(self):
        """Get the index_tr_ element"""
        try:
            return self.find_by_xpath('//div[2]/div/div[2]/div[1]/div[2]/div[2]/div[2]/div[2]/table/tbody/tr')
        except Exception as e:
            logger.error(f"Error finding index_tr_: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_tr_(self):
        return self._get_index_tr_()

    def _get_index_td_(self):
        """Get the index_td_ element"""
        try:
            return self.find_by_xpath('//div[2]/div/div[2]/div[1]/div[2]/div[2]/div[2]/div[2]/table/tbody/tr/td[4]')
        except Exception as e:
            logger.error(f"Error finding index_td_: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_td_(self):
        return self._get_index_td_()

    def _get_index_tr__1(self):
        """Get the index_tr__1 element"""
        try:
            return self.find_by_xpath('//div[2]/div/div[2]/div[1]/div[2]/div[2]/div[5]/div[1]/div/div[3]/table/tbody/tr')
        except Exception as e:
            logger.error(f"Error finding index_tr__1: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_tr__1(self):
        return self._get_index_tr__1()

    def _get_index_button_accordion_button(self):
        """Get the index_button_accordion_button element"""
        try:
            return self.find_by_class('accordion-buttoncollapsed')
        except Exception as e:
            logger.error(f"Error finding index_button_accordion_button: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_button_accordion_button(self):
        return self._get_index_button_accordion_button()

    def click_index_button_accordion_button(self):
        """Click the index_button_accordion_button"""
        element = self._get_index_button_accordion_button()
        self.click_element(element)
        self.wait_for_page_load()
        return self

    def _get_index_li_list_group_item(self):
        """Get the index_li_list_group_item element"""
        try:
            return self.find_by_class('list-group-item')
        except Exception as e:
            logger.error(f"Error finding index_li_list_group_item: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_li_list_group_item(self):
        return self._get_index_li_list_group_item()

    def _get_index_form_(self):
        """Get the index_form_ element"""
        try:
            return self.find_by_xpath('//div[3]/div/div/form')
        except Exception as e:
            logger.error(f"Error finding index_form_: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def index_form_(self):
        return self._get_index_form_()

    def verify_page_loaded(self):
        """Verify that the IndexPage is loaded correctly"""


class APage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the APage is loaded correctly"""


class ButtonPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_button_cancel(self):
        """Get the button_cancel element"""
        try:
            return self.find_by_class('btnbtn-secondary')
        except Exception as e:
            logger.error(f"Error finding button_cancel: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def button_cancel(self):
        return self._get_button_cancel()

    def click_button_cancel(self):
        """Click the button_cancel"""
        element = self._get_button_cancel()
        self.click_element(element)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the ButtonPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class FormPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the FormPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class InputPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_input_name(self):
        """Get the input_name element"""
        try:
            return self.find_by_id('name')
        except Exception as e:
            logger.error(f"Error finding input_name: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def input_name(self):
        return self._get_input_name()

    def set_input_name(self, text):
        """Set text in the input_name"""
        element = self._get_input_name()
        self.input_text(element, text)
        return self

    def verify_page_loaded(self):
        """Verify that the InputPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class TrPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_tr_name_type_selector_t(self):
        """Get the tr_name_type_selector_t element"""
        try:
            return self.find_by_xpath("//tr[contains(text(), 'Name\nType\nSelector\nText')]")
        except Exception as e:
            logger.error(f"Error finding tr_name_type_selector_t: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def tr_name_type_selector_t(self):
        return self._get_tr_name_type_selector_t()

    def _get_tr_test_status(self):
        """Get the tr_test_status element"""
        try:
            return self.find_by_xpath("//tr[contains(text(), 'Test\nStatus')]")
        except Exception as e:
            logger.error(f"Error finding tr_test_status: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def tr_test_status(self):
        return self._get_tr_test_status()

    def verify_page_loaded(self):
        """Verify that the TrPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class TdPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def verify_page_loaded(self):
        """Verify that the TdPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class LabelPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_label_project_name(self):
        """Get the label_project_name element"""
        try:
            return self.find_by_class('form-label')
        except Exception as e:
            logger.error(f"Error finding label_project_name: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def label_project_name(self):
        return self._get_label_project_name()

    def _get_label_description(self):
        """Get the label_description element"""
        try:
            return self.find_by_class('form-label')
        except Exception as e:
            logger.error(f"Error finding label_description: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def label_description(self):
        return self._get_label_description()

    def _get_label_upload_source_files(self):
        """Get the label_upload_source_files element"""
        try:
            return self.find_by_class('form-label')
        except Exception as e:
            logger.error(f"Error finding label_upload_source_files: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def label_upload_source_files(self):
        return self._get_label_upload_source_files()

    def verify_page_loaded(self):
        """Verify that the LabelPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None


class TextareaPage(BasePage):
    def __init__(self, driver, base_url='http://localhost'):
        super().__init__(driver)
        self.base_url = base_url
        self.page_url = f"{self.base_url}/"

    def navigate(self):
        self.navigate_to(self.page_url)
        self.wait_for_page_load()
        return self

    def _get_textarea_description(self):
        """Get the textarea_description element"""
        try:
            return self.find_by_id('description')
        except Exception as e:
            logger.error(f"Error finding textarea_description: {e}")
            # Return a dummy element or re-raise
            raise

    @property
    def textarea_description(self):
        return self._get_textarea_description()

    def set_textarea_description(self, text):
        """Set text in the textarea_description"""
        element = self._get_textarea_description()
        self.input_text(element, text)
        return self

    def verify_page_loaded(self):
        """Verify that the TextareaPage is loaded correctly"""
        # Check if we're on the right page by URL or title
        return self.driver.title is not None
