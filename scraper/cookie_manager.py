import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)

class CookieManager:
    """
    Cookie Manager for Social Media Platforms
    
    Imports cookies from various browser profiles and manages them
    for use in Selenium stealth browser to avoid login popups.
    """
    
    def __init__(self):
        self.cookie_sources = {
            'chrome': self._get_chrome_cookies,
            'firefox': self._get_firefox_cookies,
            'edge': self._get_edge_cookies,
            'safari': self._get_safari_cookies
        }
        
        # Social media domains and their cookie patterns
        self.social_domains = {
            'facebook': ['facebook.com', '.facebook.com'],
            'instagram': ['instagram.com', '.instagram.com'],
            'twitter': ['twitter.com', '.twitter.com', 'x.com', '.x.com'],
            'linkedin': ['linkedin.com', '.linkedin.com'],
            'github': ['github.com', '.github.com'],
            'tiktok': ['tiktok.com', '.tiktok.com']
        }
        
        # Cookie storage directory
        self.cookie_dir = Path("cookies")
        self.cookie_dir.mkdir(exist_ok=True)
    
    def import_cookies_from_browser(self, browser_type: str = 'chrome', profile_name: str = 'default') -> Dict[str, List[Dict]]:
        """
        Import cookies from a specific browser profile
        
        Args:
            browser_type (str): Browser type (chrome, firefox, edge, safari)
            profile_name (str): Profile name to import from
            
        Returns:
            Dict: Cookies organized by domain
        """
        try:
            if browser_type not in self.cookie_sources:
                raise ValueError(f"Unsupported browser type: {browser_type}")
            
            logger.info(f"Importing cookies from {browser_type} profile: {profile_name}")
            
            # Get cookies from browser
            cookies = self.cookie_sources[browser_type](profile_name)
            
            if not cookies:
                logger.warning(f"No cookies found in {browser_type} profile: {profile_name}")
                return {}
            
            # Organize cookies by domain
            organized_cookies = self._organize_cookies_by_domain(cookies)
            
            # Save imported cookies
            self._save_cookies(browser_type, profile_name, organized_cookies)
            
            logger.info(f"Successfully imported {len(cookies)} cookies from {browser_type}")
            return organized_cookies
            
        except Exception as e:
            logger.error(f"Error importing cookies from {browser_type}: {e}")
            return {}
    
    def import_all_browser_cookies(self) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Import cookies from all available browser profiles
        
        Returns:
            Dict: Cookies from all browsers organized by browser and domain
        """
        all_cookies = {}
        
        for browser_type in self.cookie_sources.keys():
            try:
                # Try to import from default profile
                try:
                    from config import Config
                    cfg = Config()
                except Exception:
                    cfg = None
                default_profile = 'default'
                if browser_type == 'edge' and cfg is not None:
                    default_profile = getattr(cfg, 'EDGE_PROFILE', 'default')
                if browser_type == 'chrome' and cfg is not None:
                    default_profile = getattr(cfg, 'CHROME_PROFILE', 'default')
                cookies = self.import_cookies_from_browser(browser_type, default_profile)
                if cookies:
                    all_cookies[browser_type] = cookies
                
                # Try to import from other common profile names
                if browser_type in ['chrome', 'edge']:
                    profile_names = ['Default', 'Profile 1', 'Profile 2', 'Profile 3']
                    for profile in profile_names:
                        try:
                            profile_cookies = self.import_cookies_from_browser(browser_type, profile)
                            if profile_cookies:
                                all_cookies[f"{browser_type}_{profile}"] = profile_cookies
                        except Exception:
                            continue
                            
            except Exception as e:
                logger.warning(f"Could not import cookies from {browser_type}: {e}")
        
        return all_cookies
    
    def inject_cookies_to_selenium(self, driver: WebDriver, platform: str, browser_type: str = None) -> bool:
        """
        Inject cookies into a Selenium WebDriver session following proper flow:
        1. Visit domain first
        2. Add cookies
        3. Refresh page
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            platform (str): Social media platform name
            browser_type (str): Specific browser to get cookies from (optional)
            
        Returns:
            bool: True if cookies were injected successfully
        """
        try:
            # Get cookies for the platform
            cookies = self.get_cookies_for_platform(platform, browser_type)
            
            if not cookies:
                logger.warning(f"No cookies found for platform: {platform}")
                return False
            
            # Get platform URL
            platform_url = self._get_platform_url(platform)
            if not platform_url:
                logger.error(f"Unknown platform: {platform}")
                return False
            
            logger.info(f"Injecting {len(cookies)} cookies for {platform}")
            
            # Step 1: Visit the domain first so Selenium allows adding cookies
            logger.info(f"Step 1: Visiting {platform_url} to establish domain context")
            try:
                if hasattr(driver, 'navigate_to'):
                    driver.navigate_to(platform_url)
                else:
                    driver.get(platform_url)
            except Exception as e:
                logger.error(f"Failed to visit {platform_url}: {e}")
                return False
            
            # Step 2: Inject cookies with proper format
            injected_count = 0
            for cookie in cookies:
                try:
                    # Ensure proper cookie format for Selenium
                    selenium_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie.get('path', '/')
                    }
                    
                    # Add optional fields if present
                    if cookie.get('expires'):
                        selenium_cookie['expiry'] = cookie['expires']
                    if cookie.get('secure') is not None:
                        selenium_cookie['secure'] = bool(cookie['secure'])
                    if cookie.get('httpOnly') is not None:
                        selenium_cookie['httpOnly'] = bool(cookie['httpOnly'])
                    if cookie.get('sameSite'):
                        selenium_cookie['sameSite'] = cookie['sameSite']
                    
                    # Add cookie to driver
                    if hasattr(driver, 'add_cookie'):
                        driver.add_cookie(selenium_cookie)
                    elif hasattr(driver, 'driver') and driver.driver:
                        driver.driver.add_cookie(selenium_cookie)
                    else:
                        logger.warning("No valid driver found for cookie injection")
                        continue
                    
                    injected_count += 1
                    logger.debug(f"Injected cookie: {cookie.get('name', 'unknown')} for domain {cookie.get('domain', 'unknown')}")
                    
                except Exception as e:
                    logger.warning(f"Failed to inject cookie {cookie.get('name', 'unknown')}: {e}")
                    continue
            
            # Step 3: Refresh page so cookies are sent in request
            logger.info("Step 3: Refreshing page to apply cookies")
            try:
                if hasattr(driver, 'refresh'):
                    driver.refresh()
                elif hasattr(driver, 'driver') and driver.driver:
                    driver.driver.refresh()
                else:
                    # Fallback: navigate again
                    if hasattr(driver, 'navigate_to'):
                        driver.navigate_to(platform_url)
                    else:
                        driver.get(platform_url)
            except Exception as e:
                logger.warning(f"Failed to refresh page: {e}")
            
            logger.info(f"Successfully injected {injected_count}/{len(cookies)} cookies for {platform}")
            return injected_count > 0
            
        except Exception as e:
            logger.error(f"Error injecting cookies to Selenium: {e}")
            return False
    
    def inject_all_platform_cookies(self, driver: WebDriver, browser_type: str = None) -> Dict[str, bool]:
        """
        Inject cookies for all platforms into a Selenium WebDriver session
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            browser_type (str): Specific browser to get cookies from (optional)
            
        Returns:
            Dict: Results for each platform
        """
        results = {}
        
        for platform in self.social_domains.keys():
            try:
                success = self.inject_cookies_to_selenium(driver, platform, browser_type)
                results[platform] = success
                
                if success:
                    logger.info(f"✅ Successfully injected cookies for {platform}")
                else:
                    logger.warning(f"⚠️  Failed to inject cookies for {platform}")
                    
            except Exception as e:
                logger.error(f"❌ Error injecting cookies for {platform}: {e}")
                results[platform] = False
        
        return results
    
    def get_cookies_for_domain(self, domain: str, browser_type: str = None) -> List[Dict]:
        """
        Get cookies for a specific domain
        
        Args:
            domain (str): Domain to get cookies for
            browser_type (str): Specific browser to get cookies from (optional)
            
        Returns:
            List: Cookies for the domain
        """
        cookies = []
        
        # Load saved cookies
        saved_cookies = self._load_all_saved_cookies()
        
        if browser_type:
            # Get cookies from specific browser
            if browser_type in saved_cookies:
                cookies.extend(self._extract_domain_cookies(saved_cookies[browser_type], domain))
        else:
            # Get cookies from all browsers
            for browser_cookies in saved_cookies.values():
                cookies.extend(self._extract_domain_cookies(browser_cookies, domain))
        
        # Remove duplicates and return
        return self._deduplicate_cookies(cookies)
    
    def get_cookies_for_platform(self, platform: str, browser_type: str = None) -> List[Dict]:
        """
        Get cookies for a specific social media platform
        
        Args:
            platform (str): Platform name (facebook, instagram, twitter, etc.)
            browser_type (str): Specific browser to get cookies from (optional)
            
        Returns:
            List: Cookies for the platform
        """
        if platform not in self.social_domains:
            logger.warning(f"Unknown platform: {platform}")
            return []
        
        cookies = []
        for domain in self.social_domains[platform]:
            domain_cookies = self.get_cookies_for_domain(domain, browser_type)
            cookies.extend(domain_cookies)
        
        return self._deduplicate_cookies(cookies)
    
    def _get_platform_url(self, platform: str) -> str:
        """Get the base URL for a platform"""
        platform_urls = {
            'facebook': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'twitter': 'https://twitter.com',
            'linkedin': 'https://www.linkedin.com',
            'github': 'https://github.com',
            'tiktok': 'https://www.tiktok.com'
        }
        return platform_urls.get(platform, '')
    
    def _get_chrome_cookies(self, profile_name: str = 'default') -> List[Dict]:
        """Get cookies from Chrome browser"""
        cookies = []
        
        try:
            # Chrome cookie paths for different OS
            if os.name == 'nt':  # Windows
                base_path = Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data'
            elif os.name == 'posix':  # macOS/Linux
                if os.path.exists('/Applications'):  # macOS
                    base_path = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'
                else:  # Linux
                    base_path = Path.home() / '.config' / 'google-chrome'
            else:
                logger.warning("Unsupported operating system for Chrome cookie extraction")
                return []
            
            # Profile path
            if profile_name == 'default':
                profile_path = base_path
            else:
                profile_path = base_path / profile_name
            
            cookie_file = profile_path / 'Default' / 'Cookies'
            
            if not cookie_file.exists():
                logger.warning(f"Chrome cookie file not found: {cookie_file}")
                return []
            
            # Extract cookies using sqlite3
            cookies = self._extract_chrome_cookies_sqlite(cookie_file)
            
        except Exception as e:
            logger.error(f"Error extracting Chrome cookies: {e}")
        
        return cookies
    
    def _extract_chrome_cookies_sqlite(self, cookie_file: Path) -> List[Dict]:
        """Extract cookies from Chrome's SQLite cookie file"""
        cookies = []
        
        try:
            # Create a copy of the cookie file (Chrome might have it locked)
            temp_cookie_file = self.cookie_dir / f"chrome_cookies_temp_{datetime.now().timestamp()}"
            
            # Copy the file
            import shutil
            shutil.copy2(cookie_file, temp_cookie_file)
            
            # Connect to the cookie database
            conn = sqlite3.connect(str(temp_cookie_file))
            cursor = conn.cursor()
            
            # Query cookies
            cursor.execute("""
                SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly
                FROM cookies
                WHERE host_key LIKE '%facebook.com%' 
                   OR host_key LIKE '%instagram.com%'
                   OR host_key LIKE '%twitter.com%'
                   OR host_key LIKE '%linkedin.com%'
                   OR host_key LIKE '%github.com%'
                   OR host_key LIKE '%tiktok.com%'
            """)
            
            for row in cursor.fetchall():
                host_key, name, value, path, expires_utc, is_secure, is_httponly = row
                
                # Convert Chrome timestamp to Unix timestamp
                if expires_utc:
                    # Chrome uses microseconds since 1601-01-01
                    chrome_epoch = datetime(1601, 1, 1)
                    expires_dt = chrome_epoch + timedelta(microseconds=expires_utc)
                    expires = int(expires_dt.timestamp())
                else:
                    expires = None
                
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': host_key,
                    'path': path or '/',
                    'expires': expires,
                    'secure': bool(is_secure),
                    'httpOnly': bool(is_httponly)
                }
                cookies.append(cookie)
            
            conn.close()
            
            # Clean up temp file
            temp_cookie_file.unlink()
            
        except Exception as e:
            logger.error(f"Error extracting cookies from SQLite: {e}")
        
        return cookies
    
    def _get_firefox_cookies(self, profile_name: str = 'default') -> List[Dict]:
        """Get cookies from Firefox browser"""
        cookies = []
        
        try:
            # Firefox profile paths
            if os.name == 'nt':  # Windows
                base_path = Path(os.environ['APPDATA']) / 'Mozilla' / 'Firefox' / 'Profiles'
            elif os.name == 'posix':  # macOS/Linux
                if os.path.exists('/Applications'):  # macOS
                    base_path = Path.home() / 'Library' / 'Application Support' / 'Firefox' / 'Profiles'
                else:  # Linux
                    base_path = Path.home() / '.mozilla' / 'firefox'
            else:
                logger.warning("Unsupported operating system for Firefox cookie extraction")
                return []
            
            if profile_name == 'default':
                # Find default profile
                profiles_file = base_path.parent / 'profiles.ini'
                if profiles_file.exists():
                    with open(profiles_file, 'r') as f:
                        content = f.read()
                        # Parse profiles.ini to find default profile
                        for line in content.split('\n'):
                            if line.startswith('Path='):
                                profile_path = base_path / line.split('=')[1]
                                break
                else:
                    profile_path = base_path
            else:
                profile_path = base_path / profile_name
            
            # Firefox stores cookies in cookies.sqlite
            cookie_file = profile_path / 'cookies.sqlite'
            
            if not cookie_file.exists():
                logger.warning(f"Firefox cookie file not found: {cookie_file}")
                return []
            
            # Extract cookies using sqlite3
            cookies = self._extract_firefox_cookies_sqlite(cookie_file)
            
        except Exception as e:
            logger.error(f"Error extracting Firefox cookies: {e}")
        
        return cookies
    
    def _extract_firefox_cookies_sqlite(self, cookie_file: Path) -> List[Dict]:
        """Extract cookies from Firefox's SQLite cookie file"""
        cookies = []
        
        try:
            # Create a copy of the cookie file
            temp_cookie_file = self.cookie_dir / f"firefox_cookies_temp_{datetime.now().timestamp()}"
            import shutil
            shutil.copy2(cookie_file, temp_cookie_file)
            
            # Connect to the cookie database
            conn = sqlite3.connect(str(temp_cookie_file))
            cursor = conn.cursor()
            
            # Query cookies
            cursor.execute("""
                SELECT host, name, value, path, expiry, isSecure, isHttpOnly
                FROM moz_cookies
                WHERE host LIKE '%facebook.com%' 
                   OR host LIKE '%instagram.com%'
                   OR host LIKE '%twitter.com%'
                   OR host LIKE '%linkedin.com%'
                   OR host LIKE '%github.com%'
                   OR host LIKE '%tiktok.com%'
            """)
            
            for row in cursor.fetchall():
                host, name, value, path, expiry, is_secure, is_httponly = row
                
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': host,
                    'path': path or '/',
                    'expires': expiry,
                    'secure': bool(is_secure),
                    'httpOnly': bool(is_httponly)
                }
                cookies.append(cookie)
            
            conn.close()
            
            # Clean up temp file
            temp_cookie_file.unlink()
            
        except Exception as e:
            logger.error(f"Error extracting Firefox cookies from SQLite: {e}")
        
        return cookies
    
    def _get_edge_cookies(self, profile_name: str = 'default') -> List[Dict]:
        """Get cookies from Edge browser (similar to Chrome)"""
        try:
            # Edge uses similar structure to Chrome
            if os.name == 'nt':  # Windows
                base_path = Path(os.environ['LOCALAPPDATA']) / 'Microsoft' / 'Edge' / 'User Data'
            else:
                logger.warning("Edge cookie extraction only supported on Windows")
                return []
            
            # Profile path
            if profile_name == 'default':
                profile_path = base_path
            else:
                profile_path = base_path / profile_name
            
            # Edge stores cookies in Network subdirectory
            cookie_file = profile_path / 'Default' / 'Network' / 'Cookies'
            
            if not cookie_file.exists():
                logger.warning(f"Edge cookie file not found: {cookie_file}")
                return []
            
            # Extract cookies using same method as Chrome
            return self._extract_chrome_cookies_sqlite(cookie_file)
            
        except Exception as e:
            logger.error(f"Error extracting Edge cookies: {e}")
            return []
    
    def _get_safari_cookies(self, profile_name: str = 'default') -> List[Dict]:
        """Get cookies from Safari browser (macOS only)"""
        cookies = []
        
        try:
            if os.name != 'posix' or not os.path.exists('/Applications'):
                logger.warning("Safari cookie extraction only supported on macOS")
                return []
            
            # Safari stores cookies in binary plist format
            cookie_file = Path.home() / 'Library' / 'Cookies' / 'Cookies.binarycookies'
            
            if not cookie_file.exists():
                logger.warning(f"Safari cookie file not found: {cookie_file}")
                return []
            
            # Safari cookies are in binary format, would need additional parsing
            # For now, return empty list
            logger.info("Safari cookie extraction not yet implemented")
            
        except Exception as e:
            logger.error(f"Error extracting Safari cookies: {e}")
        
        return cookies
    
    def _organize_cookies_by_domain(self, cookies: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize cookies by domain"""
        organized = {}
        
        for cookie in cookies:
            domain = cookie.get('domain', '')
            if domain:
                # Remove leading dot for consistency
                if domain.startswith('.'):
                    domain = domain[1:]
                
                if domain not in organized:
                    organized[domain] = []
                organized[domain].append(cookie)
        
        return organized
    
    def _extract_domain_cookies(self, browser_cookies: Dict[str, List[Dict]], target_domain: str) -> List[Dict]:
        """Extract cookies for a specific domain from browser cookies"""
        cookies = []
        
        for domain, domain_cookies in browser_cookies.items():
            if target_domain in domain or domain in target_domain:
                cookies.extend(domain_cookies)
        
        return cookies
    
    def _deduplicate_cookies(self, cookies: List[Dict]) -> List[Dict]:
        """Remove duplicate cookies based on name, domain, and path"""
        seen = set()
        unique_cookies = []
        
        for cookie in cookies:
            key = (cookie.get('name'), cookie.get('domain'), cookie.get('path'))
            if key not in seen:
                seen.add(key)
                unique_cookies.append(cookie)
        
        return unique_cookies
    
    def _save_cookies(self, browser_type: str, profile_name: str, cookies: Dict[str, List[Dict]]):
        """Save imported cookies to file"""
        try:
            filename = f"{browser_type}_{profile_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.cookie_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump({
                    'browser_type': browser_type,
                    'profile_name': profile_name,
                    'import_timestamp': datetime.now().isoformat(),
                    'cookies': cookies
                }, f, indent=2)
            
            logger.info(f"Saved cookies to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
    
    def _load_all_saved_cookies(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Load all saved cookie files"""
        all_cookies = {}
        
        try:
            for cookie_file in self.cookie_dir.glob("*.json"):
                try:
                    with open(cookie_file, 'r') as f:
                        data = json.load(f)
                        browser_key = f"{data['browser_type']}_{data['profile_name']}"
                        all_cookies[browser_key] = data['cookies']
                except Exception as e:
                    logger.warning(f"Error loading cookie file {cookie_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading saved cookies: {e}")
        
        return all_cookies
    
    def get_cookie_summary(self) -> Dict[str, Any]:
        """Get summary of available cookies"""
        summary = {
            'total_browsers': 0,
            'total_cookies': 0,
            'platforms_with_cookies': {},
            'browser_details': {}
        }
        
        saved_cookies = self._load_all_saved_cookies()
        
        for browser_key, browser_cookies in saved_cookies.items():
            summary['total_browsers'] += 1
            browser_cookie_count = sum(len(cookies) for cookies in browser_cookies.values())
            summary['total_cookies'] += browser_cookie_count
            
            summary['browser_details'][browser_key] = {
                'total_cookies': browser_cookie_count,
                'domains': list(browser_cookies.keys())
            }
            
            # Count cookies by platform
            for platform, domains in self.social_domains.items():
                platform_cookies = 0
                for domain in domains:
                    if domain in browser_cookies:
                        platform_cookies += len(browser_cookies[domain])
                
                if platform_cookies > 0:
                    if platform not in summary['platforms_with_cookies']:
                        summary['platforms_with_cookies'][platform] = 0
                    summary['platforms_with_cookies'][platform] += platform_cookies
        
        return summary
    
    def clear_old_cookies(self, days_old: int = 7):
        """Clear cookie files older than specified days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            cleared_count = 0
            
            for cookie_file in self.cookie_dir.glob("*.json"):
                try:
                    file_time = datetime.fromtimestamp(cookie_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        cookie_file.unlink()
                        cleared_count += 1
                except Exception as e:
                    logger.warning(f"Error checking cookie file {cookie_file}: {e}")
            
            logger.info(f"Cleared {cleared_count} old cookie files")
            
        except Exception as e:
            logger.error(f"Error clearing old cookies: {e}")
