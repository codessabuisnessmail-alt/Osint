import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
import logging
from config import Config
import os

logger = logging.getLogger(__name__)

class StealthBrowser:
    def __init__(self, headless=True, viewport_width=1920, viewport_height=1080):
        self.config = Config()
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.driver = None
        self.current_user_agent = None
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize the undetected Chrome driver with stealth options"""
        try:
            options = uc.ChromeOptions()
            
            # Basic options
            if self.headless:
                options.add_argument('--headless')
            
            options.add_argument(f'--window-size={self.viewport_width},{self.viewport_height}')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            # Note: Removed problematic experimental options for Chrome compatibility
            
            # Stealth options
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Optional: disable images for faster loading
            # Note: JavaScript is enabled by default for social media compatibility
            
            # Random user agent
            self.current_user_agent = random.choice(self.config.USER_AGENTS)
            options.add_argument(f'--user-agent={self.current_user_agent}')
            
            # Random viewport size variation
            width_variation = random.randint(-100, 100)
            height_variation = random.randint(-50, 50)
            actual_width = self.viewport_width + width_variation
            actual_height = self.viewport_height + height_variation
            options.add_argument(f'--window-size={actual_width},{actual_height}')
            
            # Initialize driver
            if self.config.CHROME_DRIVER_PATH:
                self.driver = uc.Chrome(driver_executable_path=self.config.CHROME_DRIVER_PATH, options=options)
            else:
                self.driver = uc.Chrome(options=options)
            
            # Execute stealth scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            # Set random timezone
            timezones = ['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo']
            random_tz = random.choice(timezones)
            self.driver.execute_script(f"Intl.DateTimeFormat().resolvedOptions().timeZone = '{random_tz}'")
            
            logger.info(f"Initialized stealth browser with UA: {self.current_user_agent[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to initialize stealth browser: {e}")
            raise
    
    def navigate_to(self, url, wait_time=10):
        """Navigate to URL with stealth measures"""
        try:
            # Random delay before navigation
            delay = random.uniform(self.config.DELAY_MIN, self.config.DELAY_MAX)
            time.sleep(delay)
            
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional random delay after page load
            time.sleep(random.uniform(1, 3))
            
            return True
            
        except TimeoutException:
            logger.warning(f"Timeout waiting for page to load: {url}")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def scroll_page(self, scroll_pause_time=2):
        """Scroll the page to load lazy content"""
        try:
            # Get scroll height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load page
                time.sleep(scroll_pause_time)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                # Random delay between scrolls
                time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.info("Page scrolling completed")
            
        except Exception as e:
            logger.error(f"Failed to scroll page: {e}")
    
    def take_screenshot(self, filename):
        """Take a screenshot of the current page"""
        try:
            screenshot_path = f"screenshots/{filename}.png"
            os.makedirs("screenshots", exist_ok=True)
            
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def get_page_source(self):
        """Get the full page source"""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Failed to get page source: {e}")
            return None
    
    def get_page_title(self):
        """Get the page title"""
        try:
            return self.driver.title
        except Exception as e:
            logger.error(f"Failed to get page title: {e}")
            return None
    
    def get_page_url(self):
        """Get the current page URL"""
        try:
            return self.driver.current_url
        except Exception as e:
            logger.error(f"Failed to get current URL: {e}")
            return None
    
    def wait_for_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Wait for an element to be present on the page"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"Element not found within timeout: {selector}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element {selector}: {e}")
            return None
    
    def execute_script(self, script):
        """Execute JavaScript on the page"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            return None
    
    def inject_cookies(self, cookies):
        """Inject cookies into the browser session"""
        try:
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            logger.info(f"Injected {len(cookies)} cookies")
        except Exception as e:
            logger.error(f"Failed to inject cookies: {e}")
    
    def get_cookies(self):
        """Get all cookies from the current session"""
        try:
            return self.driver.get_cookies()
        except Exception as e:
            logger.error(f"Failed to get cookies: {e}")
            return []
    
    def clear_cookies(self):
        """Clear all cookies"""
        try:
            self.driver.delete_all_cookies()
            logger.info("Cleared all cookies")
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
    
    def close(self):
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Failed to close browser: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
