import time
import random
import logging
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config import Config
from pathlib import Path

logger = logging.getLogger(__name__)

class SeleniumStealthBrowser:
    """
    Selenium Stealth Browser for OSINT Operations
    
    Uses Edge with advanced stealth options to avoid bot detection while maintaining
    full browser functionality for social media scraping.
    """
    
    def __init__(self, headless: bool = True, viewport_width: int = 1920, viewport_height: int = 1080):
        self.config = Config()
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.driver = None
        self.wait = None
        self.current_user_agent = None
        
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def start(self):
        """Start the browser session"""
        try:
            # Setup Edge options
            edge_options = Options()
            
            if self.headless:
                edge_options.add_argument("--headless")
            
            # Advanced stealth options for Edge
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            
            # Additional stealth options
            edge_options.add_argument("--disable-extensions")
            edge_options.add_argument("--disable-plugins")
            edge_options.add_argument("--disable-images")  # Optional: disable images for faster loading
            # Keep JavaScript enabled for social sites
            
            # Performance options
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--disable-software-rasterizer")
            
            # Edge-specific stealth options
            edge_options.add_argument("--disable-web-security")
            edge_options.add_argument("--allow-running-insecure-content")
            edge_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Viewport settings with slight randomization
            width_variation = random.randint(-80, 80)
            height_variation = random.randint(-40, 40)
            actual_width = max(1024, self.viewport_width + width_variation)
            actual_height = max(700, self.viewport_height + height_variation)
            edge_options.add_argument(f"--window-size={actual_width},{actual_height}")
            
            # Randomized user agent
            try:
                self.current_user_agent = random.choice(self.config.USER_AGENTS)
            except Exception:
                self.current_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            edge_options.add_argument(f"--user-agent={self.current_user_agent}")
            
            # Try to create driver with system Edge first
            try:
                # Try using system Edge driver
                self.driver = webdriver.Edge(options=edge_options)
                logger.info("Using system Edge driver")
            except Exception as e:
                logger.info(f"System Edge driver failed: {e}")
                logger.info("Trying webdriver-manager...")
                
                # Fall back to webdriver-manager
                service = Service(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=edge_options)
                logger.info("Using webdriver-manager Edge driver")
            
            # Apply Edge-specific stealth JavaScript
            self._apply_edge_stealth(edge_options)
            
            # Set window size
            self.driver.set_window_size(self.viewport_width, self.viewport_height)
            
            # Setup wait
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Selenium stealth browser (Edge) started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    def _apply_edge_stealth(self, options):
        """Apply Edge-specific stealth options"""
        # Disable GPU acceleration to avoid virtualization errors
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-gpu-sandbox')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Disable virtualization features that cause errors
        options.add_argument('--disable-accelerated-2d-canvas')
        options.add_argument('--disable-accelerated-jpeg-decoding')
        options.add_argument('--disable-accelerated-mjpeg-decode')
        options.add_argument('--disable-accelerated-video-decode')
        options.add_argument('--disable-accelerated-video-encode')
        
        # Memory and performance optimizations
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Additional stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        if hasattr(self, 'current_user_agent') and self.current_user_agent:
            options.add_argument(f"--user-agent={self.current_user_agent}")
        
        return options
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def navigate_to(self, url: str, timeout: int = 10) -> bool:
        """
        Navigate to a URL with optimized timing
        
        Args:
            url (str): URL to navigate to
            timeout (int): Navigation timeout in seconds
            
        Returns:
            bool: True if navigation successful
        """
        try:
            if not self.driver:
                logger.error("Browser not started")
                return False
            
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Optimized wait - reduced for speed
            time.sleep(random.uniform(0.5, 1.5))
            
            # Check if page loaded successfully
            if "chrome://" in self.driver.current_url:
                logger.error("Navigation failed - chrome:// URL detected")
                return False
            
            logger.info(f"Successfully navigated to: {self.driver.current_url}")
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def get_page_source(self) -> str:
        """Get the current page source"""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error getting page source: {e}")
            return ""
    
    @property
    def current_url(self) -> str:
        """Get the current URL"""
        try:
            return self.driver.current_url
        except Exception as e:
            logger.error(f"Error getting current URL: {e}")
            return ""

    def get_page_url(self) -> str:
        """Compatibility helper to get the current page URL"""
        try:
            return self.current_url
        except Exception:
            try:
                return self.driver.current_url if self.driver else ""
            except Exception:
                return ""
    
    def get_page_title(self) -> Optional[str]:
        """Get the current page title"""
        try:
            if not self.driver:
                return None
            
            return self.driver.title
            
        except Exception as e:
            logger.error(f"Failed to get page title: {e}")
            return None
    
    def get_visible_text(self) -> str:
        """Return visible text from the current page (post-JS)."""
        try:
            if not self.driver:
                return ""
            
            # Execute JavaScript to get fully rendered content
            js_script = """
            return (function() {
                // Wait for any pending animations/transitions
                if (document.readyState !== 'complete') {
                    return 'Page still loading...';
                }
                
                // Get all visible text content
                let text = '';
                
                // Get body text
                if (document.body) {
                    text += document.body.innerText || '';
                }
                
                // Also check for dynamic content in common containers
                const containers = document.querySelectorAll('[data-testid], [role="main"], .main, #main, .content, #content');
                containers.forEach(container => {
                    if (container.innerText) {
                        text += ' ' + container.innerText;
                    }
                });
                
                return text.trim();
            })();
            """
            
            result = self.driver.execute_script(js_script) or ""
            return result
            
        except Exception as e:
            logger.error(f"Failed to get visible text: {e}")
            # Fallback to basic method
            try:
                return self.driver.execute_script("return document.body ? document.body.innerText || '' : '';") or ""
            except:
                return ""

    def wait_for_dom_stable(self, timeout: int = 8, min_length: int = 300, platform: str = None) -> bool:
        """
        Wait until the DOM appears stable by checking visible text length.
        This helps ensure JS-rendered content has appeared.
        
        Args:
            timeout (int): Maximum time to wait
            min_length (int): Minimum text length to consider page loaded
            platform (str): Platform name for platform-specific optimizations
        """
        try:
            if not self.driver:
                return False
            
            # Platform-specific optimizations
            if platform == 'facebook':
                # Facebook needs extra time for React rendering
                timeout = max(timeout, 12)
                min_length = max(min_length, 500)
            elif platform == 'instagram':
                # Instagram has heavy JS content
                timeout = max(timeout, 10)
                min_length = max(min_length, 400)
            elif platform == 'twitter':
                # Twitter loads content dynamically
                timeout = max(timeout, 10)
                min_length = max(min_length, 400)
            elif platform == 'linkedin':
                # LinkedIn has complex JS rendering
                timeout = max(timeout, 15)
                min_length = max(min_length, 600)
            
            end_time = time.time() + timeout
            last_len = 0
            stable_count = 0
            
            # Wait for initial page load
            time.sleep(1.0)
            
            while time.time() < end_time:
                # Get visible text (post-JS rendering)
                text = self.get_visible_text()
                curr_len = len(text)
                
                # Check for platform-specific content indicators
                if platform and self._check_platform_content_loaded(text, platform):
                    logger.info(f"Platform-specific content detected for {platform}")
                    return True
                
                # Check for stability
                if curr_len >= min_length and abs(curr_len - last_len) < 50:
                    stable_count += 1
                else:
                    stable_count = 0
                
                last_len = curr_len
                
                if stable_count >= 2:
                    logger.info(f"DOM stable after {stable_count} checks, length: {curr_len}")
                    return True
                
                time.sleep(0.5)
            
            logger.warning(f"DOM stability timeout after {timeout}s, final length: {last_len}")
            return last_len >= min_length
            
        except Exception as e:
            logger.error(f"Error waiting for DOM stability: {e}")
            return False
    
    def _check_platform_content_loaded(self, text: str, platform: str) -> bool:
        """Check if platform-specific content has loaded"""
        text_lower = text.lower()
        
        if platform == 'facebook':
            # Check for Facebook-specific content
            indicators = ['timeline', 'posts', 'friends', 'about', 'profile photo', 'cover photo']
            return any(indicator in text_lower for indicator in indicators)
        
        elif platform == 'instagram':
            # Check for Instagram-specific content
            indicators = ['posts', 'followers', 'following', 'bio', 'instagram', 'story', 'reels']
            return any(indicator in text_lower for indicator in indicators)
        
        elif platform == 'twitter':
            # Check for Twitter-specific content
            indicators = ['tweets', 'following', 'followers', 'bio', 'location', 'join']
            return any(indicator in text_lower for indicator in indicators)
        
        elif platform == 'linkedin':
            # Check for LinkedIn-specific content
            indicators = ['experience', 'education', 'connections', 'about', 'contact info']
            return any(indicator in text_lower for indicator in indicators)
        
        elif platform == 'github':
            # Check for GitHub-specific content
            indicators = ['repositories', 'followers', 'following', 'stars', 'overview', 'profile']
            return any(indicator in text_lower for indicator in indicators)
        
        return False

    def force_js_rendering(self, platform: str = None) -> bool:
        """
        Force JavaScript rendering for platforms that need it
        
        Args:
            platform (str): Platform name for specific optimizations
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.driver:
                return False
            
            logger.info(f"Forcing JS rendering for {platform or 'general'}")
            
            # Platform-specific JavaScript execution
            if platform == 'facebook':
                # Facebook-specific JS to trigger React rendering
                js_script = """
                // Trigger Facebook's React rendering
                if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                    // Force React to re-render
                    const event = new Event('scroll');
                    window.dispatchEvent(event);
                }
                
                // Wait for any pending state updates
                return new Promise(resolve => {
                    setTimeout(() => {
                        resolve('Facebook rendering triggered');
                    }, 1000);
                });
                """
                
            elif platform == 'instagram':
                # Instagram-specific JS
                js_script = """
                // Trigger Instagram's dynamic content loading
                const observer = new MutationObserver(() => {});
                observer.observe(document.body, { childList: true, subtree: true });
                
                // Scroll to trigger lazy loading
                window.scrollTo(0, document.body.scrollHeight / 2);
                return 'Instagram rendering triggered';
                """
                
            elif platform == 'twitter':
                # Twitter-specific JS
                js_script = """
                // Trigger Twitter's dynamic content
                if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                    window.dispatchEvent(new Event('resize'));
                }
                return 'Twitter rendering triggered';
                """
                
            elif platform == 'linkedin':
                # LinkedIn-specific JS
                js_script = """
                // Trigger LinkedIn's content loading
                const containers = document.querySelectorAll('[data-test-id]');
                containers.forEach(container => {
                    if (container.style.display === 'none') {
                        container.style.display = 'block';
                    }
                });
                return 'LinkedIn rendering triggered';
                """
                
            else:
                # General JavaScript rendering trigger
                js_script = """
                // General JS rendering trigger
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
                
                // Wait for any pending animations
                return new Promise(resolve => {
                    setTimeout(() => {
                        resolve('General rendering triggered');
                    }, 500);
                });
                """
            
            # Execute the JavaScript
            result = self.driver.execute_script(js_script)
            logger.info(f"JS rendering result: {result}")
            
            # Wait a bit for rendering to complete
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error forcing JS rendering: {e}")
            return False

    def scroll_page(self, scroll_pause: float = 1.0, max_scrolls: int = 5, quick: bool = False):
        """
        Scroll the page to load lazy content
        
        Args:
            scroll_pause (float): Pause between scrolls
            max_scrolls (int): Maximum number of scrolls
            quick (bool): Use quick scroll for faster processing
        """
        try:
            if not self.driver:
                return
            
            if quick:
                # Quick scroll for speed optimization
                logger.info("Quick scrolling page")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(random.uniform(0.2, 0.5))
                self.driver.execute_script("window.scrollTo(0, 0);")
                return
            
            logger.info("Scrolling page to load content")
            
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            scroll_count = 0
            while scroll_count < max_scrolls:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for content to load
                time.sleep(scroll_pause)
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # If height is the same, we've reached the bottom
                if new_height == last_height:
                    break
                
                last_height = new_height
                scroll_count += 1
                
                # Random pause between scrolls
                time.sleep(random.uniform(0.5, 1.5))
            
            logger.info(f"Page scrolling completed after {scroll_count} scrolls")
            
        except Exception as e:
            logger.error(f"Error scrolling page: {e}")
    
    def take_screenshot(self, filename: str) -> Optional[str]:
        """
        Take a screenshot of the current page
        
        Args:
            filename (str): Base filename for screenshot
            
        Returns:
            str: Path to screenshot file if successful
        """
        try:
            if not self.driver:
                return None
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            
            # Generate full filename
            timestamp = int(time.time())
            full_filename = f"{filename}_{timestamp}.png"
            filepath = screenshots_dir / full_filename
            
            # Take screenshot
            self.driver.save_screenshot(str(filepath))
            
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """
        Wait for an element to be present on the page
        
        Args:
            by (By): Locator strategy
            value (str): Locator value
            timeout (int): Timeout in seconds
            
        Returns:
            WebElement: Found element or None
        """
        try:
            if not self.wait:
                return None
            
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
            
        except TimeoutException:
            logger.warning(f"Element not found within {timeout}s: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element: {e}")
            return None
    
    def find_elements(self, by: By, value: str) -> List[Any]:
        """
        Find elements on the page
        
        Args:
            by (By): Locator strategy
            value (str): Locator value
            
        Returns:
            List: List of found elements
        """
        try:
            if not self.driver:
                return []
            
            elements = self.driver.find_elements(by, value)
            return elements
            
        except Exception as e:
            logger.error(f"Error finding elements: {e}")
            return []
    
    def click_element(self, element: Any) -> bool:
        """
        Click on an element
        
        Args:
            element: WebElement to click
            
        Returns:
            bool: True if click successful
        """
        try:
            if not element:
                return False
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Click element
            element.click()
            time.sleep(random.uniform(1, 2))
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    def type_text(self, element: Any, text: str, clear_first: bool = True) -> bool:
        """
        Type text into an element
        
        Args:
            element: WebElement to type into
            text (str): Text to type
            clear_first (bool): Whether to clear existing text first
            
        Returns:
            bool: True if typing successful
        """
        try:
            if not element:
                return False
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Clear existing text if requested
            if clear_first:
                element.clear()
            
            # Type text with random delays to simulate human typing
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            return True
            
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript code
        
        Args:
            script (str): JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Any: Result of script execution
        """
        try:
            if not self.driver:
                return None
            
            return self.driver.execute_script(script, *args)
            
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None
    
    def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies from the current session"""
        try:
            if not self.driver:
                return []
            
            return self.driver.get_cookies()
            
        except Exception as e:
            logger.error(f"Error getting cookies: {e}")
            return []
    
    def add_cookie(self, cookie: Dict[str, Any]) -> bool:
        """
        Add a cookie to the current session
        
        Args:
            cookie (Dict): Cookie data
            
        Returns:
            bool: True if cookie added successfully
        """
        try:
            if not self.driver:
                return False
            
            self.driver.add_cookie(cookie)
            return True
            
        except Exception as e:
            logger.error(f"Error adding cookie: {e}")
            return False
    
    def delete_cookie(self, name: str) -> bool:
        """
        Delete a cookie by name
        
        Args:
            name (str): Name of cookie to delete
            
        Returns:
            bool: True if cookie deleted successfully
        """
        try:
            if not self.driver:
                return False
            
            self.driver.delete_cookie(name)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cookie: {e}")
            return False
    
    def clear_cookies(self) -> bool:
        """Clear all cookies from the current session"""
        try:
            if not self.driver:
                return False
            
            self.driver.delete_all_cookies()
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cookies: {e}")
            return False
    
    def refresh_page(self) -> bool:
        """Refresh the current page"""
        try:
            if not self.driver:
                return False
            
            self.driver.refresh()
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing page: {e}")
            return False
    
    def go_back(self) -> bool:
        """Go back to the previous page"""
        try:
            if not self.driver:
                return False
            
            self.driver.back()
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            logger.error(f"Error going back: {e}")
            return False
    
    def go_forward(self) -> bool:
        """Go forward to the next page"""
        try:
            if not self.driver:
                return False
            
            self.driver.forward()
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            logger.error(f"Error going forward: {e}")
            return False
    
    def is_page_loaded(self) -> bool:
        """Check if the page is fully loaded"""
        try:
            if not self.driver:
                return False
            
            # Check if document is ready
            ready_state = self.driver.execute_script("return document.readyState")
            return ready_state == "complete"
            
        except Exception as e:
            logger.error(f"Error checking page load status: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        Wait for page to fully load
        
        Args:
            timeout (int): Timeout in seconds
            
        Returns:
            bool: True if page loaded within timeout
        """
        try:
            if not self.driver:
                return False
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_page_loaded():
                    return True
                time.sleep(0.5)
            
            logger.warning(f"Page load timeout after {timeout}s")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for page load: {e}")
            return False
