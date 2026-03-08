import time
import random
import logging
from urllib.parse import urlparse
from datetime import datetime
from browser.selenium_stealth import SeleniumStealthBrowser
from detection.bot_detector import BotDetector
from storage.s3_client import StorageClient
from database.models import OSINTResult, Snapshot, get_session
from scraper.cookie_manager import CookieManager
from config import Config
import os

logger = logging.getLogger(__name__)

class OSINTScraper:
    def __init__(self):
        self.config = Config()
        self.bot_detector = BotDetector()
        # Optional storage: only initialize when remote storage is enabled
        self.storage_client = None
        try:
            if getattr(self.config, 'USE_REMOTE_STORAGE', False):
                self.storage_client = StorageClient()
            else:
                logger.info("Remote storage disabled (USE_REMOTE_STORAGE=false) - using local-only mode")
        except Exception as e:
            logger.warning(f"Storage initialization skipped due to error: {e}. Continuing without remote storage.")
        self.session = get_session()
        self.cookie_manager = CookieManager()
        
        # Initialize auto cookie updater for fresh cookies
        try:
            from auto_cookie_updater import AutoCookieUpdater
            self.cookie_updater = AutoCookieUpdater()
            logger.info("Auto cookie updater initialized")
        except Exception as e:
            logger.warning(f"Auto cookie updater not available: {e}")
            self.cookie_updater = None
        
        # Import cookies from user's browser profiles for logged-in sessions
        self._import_user_cookies()
        
    def scrape_profile(self, url, platform=None, username=None):
        """
        Scrape a social media profile for OSINT data
        
        Args:
            url (str): Profile URL to scrape
            platform (str): Platform name (facebook, instagram, twitter, linkedin)
            username (str): Username if known
            
        Returns:
            dict: Scraping results with confidence score and data
        """
        try:
            # Determine platform if not provided
            if not platform:
                platform = self._detect_platform(url)
            
            # Extract username if not provided
            if not username:
                username = self._extract_username(url, platform)
            
            logger.info(f"Starting OSINT scrape for {platform} profile: {username}")
            
            # Initialize Selenium stealth browser (Edge) with randomized UA
            with SeleniumStealthBrowser(
                headless=self.config.HEADLESS,
                viewport_width=self.config.VIEWPORT_WIDTH,
                viewport_height=self.config.VIEWPORT_HEIGHT
            ) as browser:
                
                # Step 1: Inject cookies BEFORE any navigation to ensure proper session
                logger.info(f"Step 1: Injecting cookies for {platform} before navigation")
                self._inject_cookies_for_platform(browser, platform)
                
                # Step 2: Navigate to profile URL
                logger.info(f"Step 2: Navigating to profile URL: {url}")
                if not browser.navigate_to(url):
                    return self._create_error_result(url, platform, username, "Navigation failed")
                
                # Wait for JS-rendered content with platform-specific optimizations
                browser.wait_for_dom_stable(timeout=8, min_length=300, platform=platform)
                
                # Force JavaScript rendering for the specific platform
                browser.force_js_rendering(platform=platform)
                
                # Scroll to trigger any lazy-loaded content
                browser.scroll_page(quick=True)
                
                # Take screenshot
                screenshot_filename = f"{platform}_{username}_{int(time.time())}"
                screenshot_path = browser.take_screenshot(screenshot_filename)
                
                # Get page source
                html_content = browser.get_page_source()
                if not html_content or len(html_content) < 200:
                    # Fallback to visible text if HTML too short (JS heavy pages)
                    visible_text = browser.get_visible_text()
                    html_content = f"<html><body><pre>{visible_text}</pre></body></html>"
                if not html_content:
                    return self._create_error_result(url, platform, username, "Failed to get page source")
                
                # Get current URL (check for redirects)
                current_url = browser.get_page_url()
                page_title = browser.get_page_title()
                
                # Analyze page for bot detection
                analysis_result = self.bot_detector.analyze_page(
                    html_content, current_url, 200, platform
                )
                
                # Extract profile data
                profile_data = self._extract_profile_data(html_content, platform, username)
                
                # Store snapshots (only if remote storage is enabled and available)
                html_key, html_hash = None, None
                screenshot_key, screenshot_hash = None, None
                if self.storage_client is not None:
                    try:
                        html_key, html_hash = self.storage_client.store_html_snapshot(
                            html_content, screenshot_filename
                        )
                    except Exception as e:
                        logger.warning(f"Skipping remote HTML storage: {e}")
                    
                    if screenshot_path:
                        try:
                            screenshot_key, screenshot_hash = self.storage_client.store_screenshot(
                                screenshot_path, screenshot_filename
                            )
                        except Exception as e:
                            logger.warning(f"Skipping remote screenshot storage: {e}")
                
                # Create result
                result = {
                    'url': current_url,
                    'platform': platform,
                    'username': username,
                    'profile_data': profile_data,
                    'confidence_score': analysis_result['confidence_score'],
                    'status_code': 200,
                    'error_message': None,
                    'is_bot_detected': analysis_result['is_bot_detected'],
                    'detection_method': analysis_result['detection_method'],
                    'html_hash': html_hash,
                    'screenshot_hash': screenshot_hash,
                    'page_title': page_title,
                    'analysis_details': analysis_result
                }
                
                # Save to database
                self._save_result(result, html_key, screenshot_key)
                
                logger.info(f"OSINT scrape completed for {username} on {platform}. "
                          f"Confidence: {analysis_result['confidence_score']}")
                
                return result
                
        except Exception as e:
            logger.error(f"Error scraping profile {url}: {e}")
            return self._create_error_result(url, platform, username, str(e))
    
    def _detect_platform(self, url):
        """Detect platform from URL"""
        url_lower = url.lower()
        
        if 'facebook.com' in url_lower:
            return 'facebook'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'github.com' in url_lower:
            return 'github'
        else:
            return 'unknown'
    
    def _extract_username(self, url, platform):
        """Extract username from URL"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if platform == 'facebook':
                # Facebook: facebook.com/username or facebook.com/profile.php?id=123
                if path_parts and path_parts[0] and not path_parts[0].startswith('profile.php'):
                    return path_parts[0]
                elif 'id=' in parsed.query:
                    return f"id_{parsed.query.split('id=')[1].split('&')[0]}"
                else:
                    return "unknown"
                    
            elif platform == 'instagram':
                # Instagram: instagram.com/username
                if path_parts and path_parts[0]:
                    return path_parts[0]
                else:
                    return "unknown"
                    
            elif platform == 'twitter':
                # Twitter: twitter.com/username
                if path_parts and path_parts[0]:
                    return path_parts[0]
                else:
                    return "unknown"
                    
            elif platform == 'linkedin':
                # LinkedIn: linkedin.com/in/username
                if len(path_parts) >= 2 and path_parts[0] == 'in':
                    return path_parts[1]
                else:
                    return "unknown"
                    
            elif platform == 'github':
                # GitHub: github.com/username
                if path_parts and path_parts[0]:
                    return path_parts[0]
                else:
                    return "unknown"
                    
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Error extracting username: {e}")
            return "unknown"
    
    def _extract_profile_data(self, html_content, platform, username):
        """Extract relevant profile data from HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            profile_data = {
                'username': username,
                'platform': platform,
                'extracted_at': datetime.utcnow().isoformat(),
                'text_content': soup.get_text()[:5000],  # First 5000 chars
                'links': [],
                'images': [],
                'meta_data': {}
            }
            
            # Extract links
            for link in soup.find_all('a', href=True)[:20]:  # Limit to 20 links
                profile_data['links'].append({
                    'text': link.get_text().strip()[:100],
                    'href': link['href']
                })
            
            # Extract images
            for img in soup.find_all('img', src=True)[:10]:  # Limit to 10 images
                profile_data['images'].append({
                    'alt': img.get('alt', ''),
                    'src': img['src']
                })
            
            # Extract meta data
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    profile_data['meta_data'][name] = content[:200]
            
            # Platform-specific extraction
            if platform == 'facebook':
                profile_data.update(self._extract_facebook_data(soup))
            elif platform == 'instagram':
                profile_data.update(self._extract_instagram_data(soup))
            elif platform == 'twitter':
                profile_data.update(self._extract_twitter_data(soup))
            elif platform == 'linkedin':
                profile_data.update(self._extract_linkedin_data(soup))
            elif platform == 'github':
                profile_data.update(self._extract_github_data(soup))
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return {'error': str(e)}
    
    def _extract_facebook_data(self, soup):
        """Extract Facebook-specific data"""
        data = {}
        
        try:
            # Look for profile name
            name_elements = soup.find_all(['h1', 'h2', 'h3'], class_=lambda x: x and 'profile' in x.lower())
            if name_elements:
                data['profile_name'] = name_elements[0].get_text().strip()
            
            # Look for bio/about
            bio_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'bio' in x.lower())
            if bio_elements:
                data['bio'] = bio_elements[0].get_text().strip()
            
            # Look for location
            location_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'location' in x.lower())
            if location_elements:
                data['location'] = location_elements[0].get_text().strip()
                
        except Exception as e:
            logger.error(f"Error extracting Facebook data: {e}")
        
        return data
    
    def _extract_instagram_data(self, soup):
        """Extract Instagram-specific data"""
        data = {}
        
        try:
            # Look for display name
            name_elements = soup.find_all(['h1', 'h2'], class_=lambda x: x and 'display' in x.lower())
            if name_elements:
                data['display_name'] = name_elements[0].get_text().strip()
            
            # Look for bio
            bio_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'bio' in x.lower())
            if bio_elements:
                data['bio'] = bio_elements[0].get_text().strip()
            
            # Look for post count
            post_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'post' in x.lower())
            if post_elements:
                data['post_count'] = post_elements[0].get_text().strip()
                
        except Exception as e:
            logger.error(f"Error extracting Instagram data: {e}")
        
        return data
    
    def _extract_twitter_data(self, soup):
        """Extract Twitter-specific data"""
        data = {}
        
        try:
            # Look for display name
            name_elements = soup.find_all(['h1', 'h2'], class_=lambda x: x and 'display' in x.lower())
            if name_elements:
                data['display_name'] = name_elements[0].get_text().strip()
            
            # Look for bio
            bio_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'bio' in x.lower())
            if bio_elements:
                data['bio'] = bio_elements[0].get_text().strip()
            
            # Look for tweet count
            tweet_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'tweet' in x.lower())
            if tweet_elements:
                data['tweet_count'] = tweet_elements[0].get_text().strip()
                
        except Exception as e:
            logger.error(f"Error extracting Twitter data: {e}")
        
        return data
    
    def _extract_linkedin_data(self, soup):
        """Extract LinkedIn-specific data"""
        data = {}
        
        try:
            # Look for name
            name_elements = soup.find_all(['h1', 'h2'], class_=lambda x: x and 'name' in x.lower())
            if name_elements:
                data['full_name'] = name_elements[0].get_text().strip()
            
            # Look for headline
            headline_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'headline' in x.lower())
            if headline_elements:
                data['headline'] = headline_elements[0].get_text().strip()
            
            # Look for location
            location_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'location' in x.lower())
            if location_elements:
                data['location'] = location_elements[0].get_text().strip()
                
        except Exception as e:
            logger.error(f"Error extracting LinkedIn data: {e}")
        
        return data
    
    def _extract_github_data(self, soup):
        """Extract GitHub-specific data"""
        data = {}
        
        try:
            # Look for display name
            name_elements = soup.find_all(['h1', 'h2'], class_=lambda x: x and 'name' in x.lower())
            if name_elements:
                data['display_name'] = name_elements[0].get_text().strip()
            
            # Look for bio
            bio_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'bio' in x.lower())
            if bio_elements:
                data['bio'] = bio_elements[0].get_text().strip()
            
            # Look for location
            location_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'location' in x.lower())
            if location_elements:
                data['location'] = location_elements[0].get_text().strip()
            
            # Look for company
            company_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'company' in x.lower())
            if company_elements:
                data['company'] = company_elements[0].get_text().strip()
            
            # Look for repository count
            repo_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'repo' in x.lower())
            if repo_elements:
                data['repository_count'] = repo_elements[0].get_text().strip()
                
        except Exception as e:
            logger.error(f"Error extracting GitHub data: {e}")
        
        return data
    
    def _build_url(self, username, platform):
        """Build URL for username check"""
        platform_urls = {
            'twitter': f'https://twitter.com/{username}',
            'github': f'https://github.com/{username}',
            'instagram': f'https://instagram.com/{username}',
            'linkedin': f'https://linkedin.com/in/{username}',
            'facebook': f'https://facebook.com/{username}'
        }
        return platform_urls.get(platform, f'https://{platform}.com/{username}')
    
    def _create_error_result(self, url, platform, username, error_message):
        """Create error result when scraping fails"""
        return {
            'url': url,
            'platform': platform or 'unknown',
            'username': username or 'unknown',
            'profile_data': None,
            'confidence_score': 0.0,
            'status_code': 500,
            'error_message': error_message,
            'is_bot_detected': True,
            'detection_method': 'scraping_error',
            'html_hash': None,
            'screenshot_hash': None,
            'page_title': None,
            'analysis_details': None
        }
    
    def _save_result(self, result, html_key, screenshot_key):
        """Save result to database"""
        try:
            # Create OSINT result
            osint_result = OSINTResult(
                url=result['url'],
                platform=result['platform'],
                username=result['username'],
                profile_data=result['profile_data'],
                confidence_score=result['confidence_score'],
                status_code=result['status_code'],
                error_message=result['error_message'],
                is_bot_detected=result['is_bot_detected'],
                detection_method=result['detection_method'],
                html_hash=result['html_hash'],
                screenshot_hash=result['screenshot_hash']
            )
            
            self.session.add(osint_result)
            self.session.commit()
            
            # Create snapshot
            if html_key:
                snapshot = Snapshot(
                    osint_result_id=osint_result.id,
                    html_content=result.get('profile_data', {}).get('text_content', ''),
                    screenshot_path=screenshot_key,
                    html_hash=result['html_hash'],
                    screenshot_hash=result['screenshot_hash']
                )
                self.session.add(snapshot)
                self.session.commit()
            
            logger.info(f"Saved result to database with ID: {osint_result.id}")
            
        except Exception as e:
            logger.error(f"Error saving result to database: {e}")
            self.session.rollback()
    
    def _import_user_cookies(self):
        """Import cookies from user's browser profiles"""
        try:
            logger.info("Importing cookies from user's browser profiles...")
            
            # Try to import from Edge first (most common for Windows)
            edge_cookies = self.cookie_manager.import_cookies_from_browser('edge', 'default')
            if edge_cookies:
                logger.info(f"✅ Imported {sum(len(cookies) for cookies in edge_cookies.values())} cookies from Edge")
            
            # Try Chrome as fallback
            chrome_cookies = self.cookie_manager.import_cookies_from_browser('chrome', 'default')
            if chrome_cookies:
                logger.info(f"✅ Imported {sum(len(cookies) for cookies in chrome_cookies.values())} cookies from Chrome")
            
            # Show cookie summary
            summary = self.cookie_manager.get_cookie_summary()
            if summary:
                logger.info("📊 Cookie Summary:")
                for platform, count in summary.items():
                    logger.info(f"   • {platform}: {count} cookies")
            
        except Exception as e:
            logger.error(f"Error importing cookies: {e}")
    
    def _inject_cookies_for_platform(self, browser, platform):
        """Inject cookies for the specific platform to maintain logged-in session"""
        try:
            if platform and platform in ['facebook', 'instagram', 'twitter', 'linkedin', 'github']:
                # Ensure we have fresh cookies before injection
                if self.cookie_updater:
                    logger.info(f"🍪 Ensuring fresh cookies for {platform}...")
                    self.cookie_updater.ensure_fresh_cookies()
                
                # Inject cookies following proper flow: visit domain -> add cookies -> refresh
                success = self.cookie_manager.inject_cookies_to_selenium(browser, platform)
                if success:
                    logger.info(f"✅ Successfully injected cookies for {platform} following proper flow")
                    
                    # Verify login status by checking for login indicators
                    page_source = browser.get_page_source().lower()
                    if any(indicator in page_source for indicator in ['log in', 'sign in', 'login']):
                        logger.warning(f"⚠️  Still showing login page for {platform} - cookies may not be working")
                    else:
                        logger.info(f"✅ Appears to be logged in to {platform}")
                else:
                    logger.warning(f"⚠️  No cookies found for {platform}")
        except Exception as e:
            logger.error(f"Error injecting cookies for {platform}: {e}")
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
