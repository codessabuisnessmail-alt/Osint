import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus
from pathlib import Path

from username_generator import UsernameGenerator
from browser.selenium_stealth import SeleniumStealthBrowser
from scraper.cookie_manager import CookieManager
from config import Config
from database.models import OSINTResult, get_session
import re

logger = logging.getLogger(__name__)

class RealNameLookup:
    """
    Real Name Lookup System for OSINT Operations
    
    Searches across multiple platforms and databases to find real names
    associated with usernames, email addresses, phone numbers, etc.
    """
    
    def __init__(self, config: Config = None):
        """Initialize the Real Name Lookup system"""
        self.config = config or Config()
        self.username_generator = UsernameGenerator()
        self.cookie_manager = CookieManager()
        self.session = None
        
        # Import cookies from user's browser profiles
        self._import_user_cookies()
        
        # Define lookup sources
        self.lookup_sources = {
            'social_media': ['facebook', 'instagram', 'twitter', 'linkedin', 'github', 'tiktok'],
            'professional': ['linkedin', 'github'],
            'all': ['facebook', 'instagram', 'twitter', 'linkedin', 'github', 'tiktok']
        }
        
        logger.info("RealNameLookup system initialized with cookie management")
    
    def _import_user_cookies(self):
        """Import cookies from user's browser profiles"""
        try:
            logger.info("Importing cookies from user's browser profiles...")
            
            # Try to import from Edge first (since we're using Edge)
            edge_cookies = self.cookie_manager.import_cookies_from_browser('edge', 'default')
            if edge_cookies:
                logger.info(f"✅ Imported {sum(len(cookies) for cookies in edge_cookies.values())} cookies from Edge")
            
            # Also try Chrome as backup
            chrome_cookies = self.cookie_manager.import_cookies_from_browser('chrome', 'default')
            if chrome_cookies:
                logger.info(f"✅ Imported {sum(len(cookies) for cookies in chrome_cookies.values())} cookies from Chrome")
            
            # Show cookie summary
            summary = self.cookie_manager.get_cookie_summary()
            if summary:
                logger.info("📊 Cookie Summary:")
                for platform, count in summary.items():
                    if count > 0:
                        logger.info(f"   • {platform}: {count} cookies")
            
        except Exception as e:
            logger.warning(f"Could not import cookies: {e}")
            logger.info("System will continue without cookies (may encounter login popups)")
    
    def lookup_by_username(self, username: str, platforms: List[str] = None) -> Dict:
        """
        Look up real name by username across multiple platforms
        
        Args:
            username (str): Username to search for
            platforms (List[str]): Specific platforms to search (default: all)
            
        Returns:
            Dict: Lookup results with confidence scores
        """
        if not platforms:
            platforms = self.lookup_sources['social_media']
        
        results = {
            'username': username,
            'search_timestamp': datetime.utcnow().isoformat(),
            'platforms_searched': platforms,
            'potential_names': [],
            'confidence_score': 0.0,
            'sources': [],
            'errors': []
        }
        
        logger.info(f"Starting real name lookup for username: {username}")
        
        # Search each platform
        for platform in platforms:
            try:
                platform_result = self._search_platform(username, platform)
                if platform_result:
                    results['potential_names'].extend(platform_result['names'])
                    results['sources'].append({
                        'platform': platform,
                        'names_found': len(platform_result['names']),
                        'confidence': platform_result['confidence']
                    })
            except Exception as e:
                error_msg = f"Error searching {platform}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Calculate overall confidence score
        results['confidence_score'] = self._calculate_confidence(results['potential_names'])
        
        # Remove duplicates and sort by confidence
        results['potential_names'] = self._deduplicate_names(results['potential_names'])
        
        return results
    
    def lookup_by_name(self, first_name: str, last_name: str, birth_year: int = None, platforms: List[str] = None) -> Dict:
        """
        Look up profiles by generating potential usernames from a real name
        
        Args:
            first_name (str): First name
            last_name (str): Last name
            birth_year (int): Birth year for additional username variations
            platforms (List[str]): Specific platforms to search
            
        Returns:
            Dict: Lookup results with found profiles and usernames
        """
        if not platforms:
            platforms = self.lookup_sources['social_media']
        elif 'all' in platforms:
            # Replace 'all' with the actual platform list
            platforms = [p for p in self.lookup_sources['social_media'] if p != 'all']
        
        results = {
            'search_name': f"{first_name} {last_name}",
            'first_name': first_name,
            'last_name': last_name,
            'birth_year': birth_year,
            'search_timestamp': datetime.utcnow().isoformat(),
            'platforms_searched': platforms,
            'generated_usernames': [],
            'found_profiles': [],
            'confidence_score': 0.0,
            'sources': [],
            'errors': []
        }
        
        logger.info(f"Starting name-based lookup for: {first_name} {last_name}")
        
        # Generate potential usernames
        generated_usernames = self.username_generator.generate(first_name, last_name, birth_year)
        results['generated_usernames'] = generated_usernames
        
        # Search for each generated username across platforms
        for username in generated_usernames:
            try:
                username_results = self._search_username_across_platforms(username, platforms)
                if username_results:
                    results['found_profiles'].extend(username_results)
                    results['sources'].append({
                        'username': username,
                        'profiles_found': len(username_results),
                        'platforms': list(set([p['platform'] for p in username_results]))
                    })
            except Exception as e:
                error_msg = f"Error searching username {username}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Calculate overall confidence score
        results['confidence_score'] = self._calculate_name_lookup_confidence(results['found_profiles'])
        
        return results
    
    def reverse_lookup_by_name(self, name: str, platforms: List[str] = None) -> Dict:
        """
        Perform reverse lookup - find usernames associated with a given name
        
        Args:
            name (str): Full name or partial name to search for
            platforms (List[str]): Specific platforms to search
            
        Returns:
            Dict: Reverse lookup results with found usernames
        """
        if not platforms:
            platforms = self.lookup_sources['social_media']
        
        results = {
            'search_name': name,
            'search_timestamp': datetime.utcnow().isoformat(),
            'platforms_searched': platforms,
            'found_usernames': [],
            'confidence_score': 0.0,
            'sources': [],
            'errors': []
        }
        
        logger.info(f"Starting reverse lookup for name: {name}")
        
        # Search each platform for the name
        for platform in platforms:
            try:
                platform_results = self._search_by_name(name, platform)
                if platform_results and platform_results.get('matches'):
                    results['found_usernames'].extend(platform_results['matches'])
                    results['sources'].append({
                        'platform': platform,
                        'usernames_found': len(platform_results['matches']),
                        'confidence': platform_results.get('confidence', 0.5)
                    })
            except Exception as e:
                error_msg = f"Error searching {platform} for {name}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Calculate confidence score
        results['confidence_score'] = self._calculate_reverse_lookup_confidence(results['found_usernames'])
        
        return results
    
    def lookup_by_email(self, email: str) -> Dict:
        """
        Look up real name by email address
        
        Args:
            email (str): Email address to search
            
        Returns:
            Dict: Lookup results
        """
        results = {
            'email': email,
            'search_timestamp': datetime.utcnow().isoformat(),
            'potential_names': [],
            'confidence_score': 0.0,
            'sources': [],
            'errors': []
        }
        
        # Extract username from email
        username = email.split('@')[0]
        
        # Search social media platforms
        social_results = self.lookup_by_username(username, ['facebook', 'instagram', 'twitter'])
        results['potential_names'].extend(social_results['potential_names'])
        results['sources'].extend(social_results['sources'])
        
        # Search professional platforms
        professional_results = self.lookup_by_username(username, ['linkedin', 'github'])
        results['potential_names'].extend(professional_results['potential_names'])
        results['sources'].extend(professional_results['sources'])
        
        # Calculate confidence
        results['confidence_score'] = self._calculate_confidence(results['potential_names'])
        results['potential_names'] = self._deduplicate_names(results['potential_names'])
        
        return results
    
    def lookup_by_phone(self, phone: str) -> Dict:
        """
        Look up real name by phone number
        
        Args:
            phone (str): Phone number to search
            
        Returns:
            Dict: Lookup results
        """
        results = {
            'phone': phone,
            'search_timestamp': datetime.utcnow().isoformat(),
            'potential_names': [],
            'confidence_score': 0.0,
            'sources': [],
            'errors': []
        }
        
        # Search public record databases
        try:
            public_results = self._search_public_records(phone)
            if public_results:
                results['potential_names'].extend(public_results['names'])
                results['sources'].append({
                    'platform': 'public_records',
                    'names_found': len(public_results['names']),
                    'confidence': public_results['confidence']
                })
        except Exception as e:
            error_msg = f"Error searching public records: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        # Calculate confidence
        results['confidence_score'] = self._calculate_confidence(results['potential_names'])
        results['potential_names'] = self._deduplicate_names(results['potential_names'])
        
        return results
    
    def cross_reference_names(self, names: List[str]) -> Dict:
        """
        Cross-reference names across multiple platforms to validate identity
        
        Args:
            names (List[str]): List of potential names to cross-reference
            
        Returns:
            Dict: Cross-reference results with validation scores
        """
        results = {
            'names': names,
            'cross_reference_results': [],
            'validation_score': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for name in names:
            name_result = {
                'name': name,
                'platforms_found': [],
                'consistency_score': 0.0,
                'details': []
            }
            
            # Search for this name across all platforms
            for platform in self.lookup_sources['social_media']:
                try:
                    platform_result = self._search_by_name(name, platform)
                    if platform_result:
                        name_result['platforms_found'].append(platform)
                        name_result['details'].append(platform_result)
                except Exception as e:
                    logger.error(f"Error cross-referencing {name} on {platform}: {e}")
            
            # Calculate consistency score
            name_result['consistency_score'] = len(name_result['platforms_found']) / len(self.lookup_sources['social_media'])
            results['cross_reference_results'].append(name_result)
        
        # Calculate overall validation score
        if results['cross_reference_results']:
            results['validation_score'] = sum(r['consistency_score'] for r in results['cross_reference_results']) / len(results['cross_reference_results'])
        
        return results
    
    def _search_username_across_platforms(self, username: str, platforms: List[str]) -> List[Dict]:
        """Search for a username across multiple platforms"""
        found_profiles = []
        
        for platform in platforms:
            try:
                platform_result = self._search_platform(username, platform)
                if platform_result and platform_result.get('names'):
                    for name_data in platform_result['names']:
                        profile = {
                            'username': username,
                            'platform': platform,
                            'name': name_data.get('name', ''),
                            'confidence': name_data.get('confidence', 0.0),
                            'profile_url': self._get_profile_url(username, platform),
                            'extracted_data': platform_result
                        }
                        found_profiles.append(profile)
            except Exception as e:
                logger.error(f"Error searching {platform} for {username}: {e}")
        
        return found_profiles
    
    def _get_profile_url(self, username: str, platform: str) -> str:
        """Get profile URL for a username on a specific platform"""
        if platform == 'facebook':
            return f"https://www.facebook.com/{username}"
        elif platform == 'instagram':
            return f"https://www.instagram.com/{username}/"
        elif platform == 'twitter':
            return f"https://twitter.com/{username}"
        elif platform == 'linkedin':
            return f"https://www.linkedin.com/in/{username}/"
        elif platform == 'github':
            return f"https://github.com/{username}"
        else:
            return ""
    
    def _search_platform(self, username: str, platform: str) -> Optional[Dict]:
        """Search a specific platform for username"""
        try:
            with SeleniumStealthBrowser(
                headless=self.config.HEADLESS,
                viewport_width=self.config.VIEWPORT_WIDTH,
                viewport_height=self.config.VIEWPORT_HEIGHT
            ) as browser:
                
                # Inject cookies for this platform before searching
                logger.info(f"Injecting cookies for {platform} before username search...")
                cookie_success = self.cookie_manager.inject_cookies_to_selenium(browser, platform)
                if cookie_success:
                    logger.info(f"✅ Cookies injected for {platform}")
                else:
                    logger.warning(f"⚠️  No cookies available for {platform} - may encounter login popups")
                
                # Platform-specific search URLs
                search_urls = self._get_platform_search_urls(username, platform)
                
                for url in search_urls:
                    if browser.navigate_to(url):
                        time.sleep(random.uniform(2, 4))
                        
                        # Extract profile information
                        profile_data = self._extract_profile_info(browser, platform)
                        if profile_data and profile_data.get('names'):
                            return {
                                'names': profile_data['names'],
                                'confidence': profile_data.get('confidence', 0.5)
                            }
                
                return None
                
        except Exception as e:
            logger.error(f"Error searching {platform} for {username}: {e}")
            return None
    
    def _get_platform_search_urls(self, username: str, platform: str) -> List[str]:
        """Get search URLs for different platforms"""
        urls = []
        
        if platform == 'facebook':
            urls = [
                f"https://www.facebook.com/{username}",
                f"https://www.facebook.com/search/people/?q={quote_plus(username)}"
            ]
        elif platform == 'instagram':
            urls = [
                f"https://www.instagram.com/{username}/",
                f"https://www.instagram.com/explore/tags/{username}/"
            ]
        elif platform == 'twitter':
            urls = [
                f"https://twitter.com/{username}",
                f"https://twitter.com/search?q={quote_plus(username)}&src=typed_query"
            ]
        elif platform == 'linkedin':
            urls = [
                f"https://www.linkedin.com/in/{username}/",
                f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(username)}"
            ]
        elif platform == 'github':
            urls = [
                f"https://github.com/{username}",
                f"https://github.com/search?q={quote_plus(username)}&type=users"
            ]
        
        return urls
    
    def _extract_profile_info(self, browser: SeleniumStealthBrowser, platform: str) -> Optional[Dict]:
        """Extract profile information from browser"""
        try:
            html_content = browser.get_page_source()
            if not html_content:
                return None
            
            # Platform-specific extraction
            if platform == 'facebook':
                return self._extract_facebook_profile(html_content)
            elif platform == 'instagram':
                return self._extract_instagram_profile(html_content)
            elif platform == 'twitter':
                return self._extract_twitter_profile(html_content)
            elif platform == 'linkedin':
                return self._extract_linkedin_profile(html_content)
            elif platform == 'github':
                return self._extract_github_profile(html_content)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting profile info from {platform}: {e}")
            return None
    
    def _extract_facebook_profile(self, html_content: str) -> Dict:
        """Extract Facebook profile information with enhanced validation"""
        names = []
        confidence = 0.0
        
        try:
            # Enhanced name patterns for Facebook
            name_patterns = [
                r'<h1[^>]*class="[^"]*profile[^"]*"[^>]*>([^<]+)</h1>',
                r'<h2[^>]*class="[^"]*profile[^"]*"[^>]*>([^<]+)</h2>',
                r'<span[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</span>',
                r'<div[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</div>',
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
                r'<title[^>]*>([^<]+)</title>',
                r'<span[^>]*class="[^"]*full[^"]*"[^>]*>([^<]+)</span>'
            ]
            
            # Check for error indicators first
            error_indicators = [
                'sorry, this page isn\'t available',
                'this content isn\'t available right now',
                'page not found',
                'user not found',
                'account not found',
                'this page is not available'
            ]
            
            html_lower = html_content.lower()
            for error in error_indicators:
                if error in html_lower:
                    logger.info(f"Facebook profile error detected: {error}")
                    return {
                        'names': [],
                        'confidence': 0.0,
                        'status': 'error',
                        'error_type': 'page_not_available'
                    }
            
            # Check for login redirects
            if '/login' in html_lower or '/checkpoint' in html_lower:
                logger.info("Facebook login redirect detected")
                return {
                    'names': [],
                    'confidence': 0.0,
                    'status': 'login_required',
                    'error_type': 'login_redirect'
                }
            
            # Extract names using patterns
            for pattern in name_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    if name and len(name) > 2 and not name.isdigit():
                        names.append(name)
            
            # Check for profile indicators to boost confidence
            profile_indicators = [
                'profile photo', 'cover photo', 'posts', 'friends', 'about',
                'timeline', 'photos', 'videos', 'check-ins'
            ]
            
            found_indicators = sum(1 for indicator in profile_indicators if indicator in html_lower)
            if found_indicators >= 3:
                confidence = 0.9
            elif found_indicators >= 1:
                confidence = 0.7
            elif names:
                confidence = 0.5
            
            # Remove duplicates and clean names
            unique_names = list(set([name for name in names if name and len(name.strip()) > 2]))
            
            return {
                'names': unique_names,
                'confidence': confidence,
                'status': 'success' if confidence > 0.0 else 'no_data',
                'profile_indicators_found': found_indicators
            }
            
        except Exception as e:
            logger.error(f"Error extracting Facebook profile: {e}")
            return {
                'names': [],
                'confidence': 0.0,
                'status': 'error',
                'error_type': 'extraction_error'
            }
    
    def _extract_instagram_profile(self, html_content: str) -> Dict:
        """Extract Instagram profile information with enhanced validation"""
        names = []
        confidence = 0.0
        
        try:
            # Enhanced name patterns for Instagram
            name_patterns = [
                r'<h1[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</h1>',
                r'<h2[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</h2>',
                r'<span[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</span>',
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
                r'<title[^>]*>([^<]+)</title>',
                r'<span[^>]*class="[^"]*full[^"]*"[^>]*>([^<]+)</span>'
            ]
            
            # Check for error indicators
            error_indicators = [
                'sorry, this page isn\'t available',
                'user not found',
                'this account is private',
                'page not found',
                'account not found'
            ]
            
            html_lower = html_content.lower()
            for error in error_indicators:
                if error in html_lower:
                    logger.info(f"Instagram profile error detected: {error}")
                    return {
                        'names': [],
                        'confidence': 0.0,
                        'status': 'error',
                        'error_type': 'page_not_available'
                    }
            
            # Check for login redirects
            if '/accounts/login' in html_lower or '/login' in html_lower:
                logger.info("Instagram login redirect detected")
                return {
                    'names': [],
                    'confidence': 0.0,
                    'status': 'login_required',
                    'error_type': 'login_redirect'
                }
            
            # Extract names using patterns
            for pattern in name_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    if name and len(name) > 2 and not name.isdigit():
                        names.append(name)
            
            # Check for profile indicators
            profile_indicators = [
                'posts', 'followers', 'following', 'bio', 'profile picture',
                'stories', 'highlights', 'igtv'
            ]
            
            found_indicators = sum(1 for indicator in profile_indicators if indicator in html_lower)
            if found_indicators >= 3:
                confidence = 0.8
            elif found_indicators >= 1:
                confidence = 0.6
            elif names:
                confidence = 0.4
            
            # Remove duplicates and clean names
            unique_names = list(set([name for name in names if name and len(name.strip()) > 2]))
            
            return {
                'names': unique_names,
                'confidence': confidence,
                'status': 'success' if confidence > 0.0 else 'no_data',
                'profile_indicators_found': found_indicators
            }
            
        except Exception as e:
            logger.error(f"Error extracting Instagram profile: {e}")
            return {
                'names': [],
                'confidence': 0.0,
                'status': 'error',
                'error_type': 'extraction_error'
            }
    
    def _extract_twitter_profile(self, html_content: str) -> Dict:
        """Extract Twitter profile information with enhanced validation"""
        names = []
        confidence = 0.0
        
        try:
            # Enhanced name patterns for Twitter
            name_patterns = [
                r'<h1[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</h1>',
                r'<h2[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</h2>',
                r'<span[^>]*class="[^"]*display[^"]*"[^>]*>([^<]+)</span>',
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
                r'<title[^>]*>([^<]+)</title>',
                r'<span[^>]*class="[^"]*full[^"]*"[^>]*>([^<]+)</span>'
            ]
            
            # Check for error indicators
            error_indicators = [
                'this account doesn\'t exist',
                'account suspended',
                'user not found',
                'page not found',
                'account not found'
            ]
            
            html_lower = html_content.lower()
            for error in error_indicators:
                if error in html_lower:
                    logger.info(f"Twitter profile error detected: {error}")
                    return {
                        'names': [],
                        'confidence': 0.0,
                        'status': 'error',
                        'error_type': 'page_not_available'
                    }
            
            # Check for login redirects
            if '/login' in html_lower or '/i/flow/login' in html_lower:
                logger.info("Twitter login redirect detected")
                return {
                    'names': [],
                    'confidence': 0.0,
                    'status': 'login_required',
                    'error_type': 'login_redirect'
                }
            
            # Extract names using patterns
            for pattern in name_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    if name and len(name) > 2 and not name.isdigit():
                        names.append(name)
            
            # Check for profile indicators
            profile_indicators = [
                'tweets', 'following', 'followers', 'bio', 'location',
                'website', 'joined', 'verified'
            ]
            
            found_indicators = sum(1 for indicator in profile_indicators if indicator in html_lower)
            if found_indicators >= 3:
                confidence = 0.8
            elif found_indicators >= 1:
                confidence = 0.6
            elif names:
                confidence = 0.4
            
            # Remove duplicates and clean names
            unique_names = list(set([name for name in names if name and len(name.strip()) > 2]))
            
            return {
                'names': unique_names,
                'confidence': confidence,
                'status': 'success' if confidence > 0.0 else 'no_data',
                'profile_indicators_found': found_indicators
            }
            
        except Exception as e:
            logger.error(f"Error extracting Twitter profile: {e}")
            return {
                'names': [],
                'confidence': 0.0,
                'status': 'error',
                'error_type': 'extraction_error'
            }
    
    def _extract_linkedin_profile(self, html_content: str) -> Dict:
        """Extract LinkedIn profile information with enhanced validation"""
        names = []
        confidence = 0.0
        
        try:
            # Enhanced name patterns for LinkedIn
            name_patterns = [
                r'<h1[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</h1>',
                r'<h2[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</h2>',
                r'<span[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</span>',
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
                r'<title[^>]*>([^<]+)</title>',
                r'<span[^>]*class="[^"]*full[^"]*"[^>]*>([^<]+)</span>'
            ]
            
            # Check for error indicators
            error_indicators = [
                'page not found',
                'profile not found',
                'this profile doesn\'t exist',
                'page unavailable',
                'profile unavailable'
            ]
            
            html_lower = html_content.lower()
            for error in error_indicators:
                if error in html_lower:
                    logger.info(f"LinkedIn profile error detected: {error}")
                    return {
                        'names': [],
                        'confidence': 0.0,
                        'status': 'error',
                        'error_type': 'page_not_available'
                    }
            
            # Check for login redirects
            if '/login' in html_lower or '/uas/login' in html_lower:
                logger.info("LinkedIn login redirect detected")
                return {
                    'names': [],
                    'confidence': 0.0,
                    'status': 'login_required',
                    'error_type': 'login_redirect'
                }
            
            # Extract names using patterns
            for pattern in name_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    if name and len(name) > 2 and not name.isdigit():
                        names.append(name)
            
            # Check for profile indicators
            profile_indicators = [
                'experience', 'education', 'connections', 'about', 'contact info',
                'skills', 'endorsements', 'recommendations', 'publications'
            ]
            
            found_indicators = sum(1 for indicator in profile_indicators if indicator in html_lower)
            if found_indicators >= 3:
                confidence = 0.9  # LinkedIn is most reliable
            elif found_indicators >= 1:
                confidence = 0.7
            elif names:
                confidence = 0.5
            
            # Remove duplicates and clean names
            unique_names = list(set([name for name in names if name and len(name.strip()) > 2]))
            
            return {
                'names': unique_names,
                'confidence': confidence,
                'status': 'success' if confidence > 0.0 else 'no_data',
                'profile_indicators_found': found_indicators
            }
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn profile: {e}")
            return {
                'names': [],
                'confidence': 0.0,
                'status': 'error',
                'error_type': 'extraction_error'
            }
    
    def _extract_github_profile(self, html_content: str) -> Dict:
        """Extract GitHub profile information with enhanced validation"""
        names = []
        confidence = 0.0
        
        try:
            # Enhanced name patterns for GitHub
            name_patterns = [
                r'<span[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</span>',
                r'<h1[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</h1>',
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
                r'<title[^>]*>([^<]+)</title>',
                r'<span[^>]*class="[^"]*full[^"]*"[^>]*>([^<]+)</span>'
            ]
            
            # Check for error indicators
            error_indicators = [
                '404',
                'user not found',
                'page not found',
                'profile not found'
            ]
            
            html_lower = html_content.lower()
            for error in error_indicators:
                if error in html_lower:
                    logger.info(f"GitHub profile error detected: {error}")
                    return {
                        'names': [],
                        'confidence': 0.0,
                        'status': 'error',
                        'error_type': 'page_not_available'
                    }
            
            # Extract names using patterns
            for pattern in name_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    if name and len(name) > 2 and not name.isdigit():
                        names.append(name)
            
            # Check for profile indicators
            profile_indicators = [
                'repositories', 'followers', 'following', 'bio', 'location',
                'company', 'blog', 'pinned', 'contributions'
            ]
            
            found_indicators = sum(1 for indicator in profile_indicators if indicator in html_lower)
            if found_indicators >= 3:
                confidence = 0.8
            elif found_indicators >= 1:
                confidence = 0.6
            elif names:
                confidence = 0.4
            
            # Remove duplicates and clean names
            unique_names = list(set([name for name in names if name and len(name.strip()) > 2]))
            
            return {
                'names': unique_names,
                'confidence': confidence,
                'status': 'success' if confidence > 0.0 else 'no_data',
                'profile_indicators_found': found_indicators
            }
            
        except Exception as e:
            logger.error(f"Error extracting GitHub profile: {e}")
            return {
                'names': [],
                'confidence': 0.0,
                'status': 'error',
                'error_type': 'extraction_error'
            }
    
    def _search_public_records(self, phone: str) -> Optional[Dict]:
        """Search public record databases (placeholder for now)"""
        # This would integrate with actual public record APIs
        # For now, return placeholder data
        return {
            'names': [],
            'confidence': 0.0
        }
    
    def _search_by_name(self, name: str, platform: str) -> Optional[Dict]:
        """Search for a name on a specific platform"""
        try:
            with SeleniumStealthBrowser(
                headless=self.config.HEADLESS,
                viewport_width=self.config.VIEWPORT_WIDTH,
                viewport_height=self.config.VIEWPORT_HEIGHT
            ) as browser:
                
                # Inject cookies for this platform before searching (logged-in session)
                logger.info(f"Injecting cookies for {platform} before search...")
                cookie_success = self.cookie_manager.inject_cookies_to_selenium(browser, platform)
                if cookie_success:
                    logger.info(f"✅ Cookies injected for {platform}")
                else:
                    logger.warning(f"⚠️  No cookies available for {platform} - may encounter login popups")
                
                # Search by name on platform
                search_url = self._get_name_search_url(name, platform)
                if browser.navigate_to(search_url):
                    time.sleep(random.uniform(2, 4))
                    
                    # Extract search results
                    results = self._extract_search_results(browser, platform, name)
                    return results
                
                return None
                
        except Exception as e:
            logger.error(f"Error searching for name {name} on {platform}: {e}")
            return None
    
    def _get_name_search_url(self, name: str, platform: str) -> str:
        """Get search URL for searching by name"""
        if platform == 'facebook':
            return f"https://www.facebook.com/search/people/?q={quote_plus(name)}"
        elif platform == 'linkedin':
            return f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(name)}"
        elif platform == 'twitter':
            return f"https://twitter.com/search?q={quote_plus(name)}&src=typed_query&f=user"
        elif platform == 'instagram':
            # Instagram doesn't have a public name search, so we'll search for usernames
            # that might contain the name
            return f"https://www.instagram.com/explore/tags/{quote_plus(name.replace(' ', ''))}/"
        elif platform == 'github':
            return f"https://github.com/search?q={quote_plus(name)}&type=users"
        elif platform == 'tiktok':
            return f"https://www.tiktok.com/search?q={quote_plus(name)}"
        else:
            return ""
    
    def _extract_search_results(self, browser: SeleniumStealthBrowser, platform: str, search_name: str) -> Dict:
        """Extract search results from browser"""
        try:
            results = {
                'results_count': 0,
                'matches': [],
                'platform': platform,
                'search_name': search_name
            }
            
            # Get page source for analysis
            page_source = browser.get_page_source()
            
            if platform == 'facebook':
                results = self._extract_facebook_results(page_source, search_name)
            elif platform == 'linkedin':
                results = self._extract_linkedin_results(page_source, search_name)
            elif platform == 'twitter':
                results = self._extract_twitter_results(page_source, search_name)
            elif platform == 'instagram':
                results = self._extract_instagram_results(page_source, search_name)
            elif platform == 'github':
                results = self._extract_github_results(page_source, search_name)
            elif platform == 'tiktok':
                results = self._extract_tiktok_results(page_source, search_name)
            
            return results
            
        except Exception as e:
            logger.error(f"Error extracting results from {platform}: {e}")
            return {
                'results_count': 0,
                'matches': [],
                'platform': platform,
                'search_name': search_name,
                'error': str(e)
            }
    
    def _extract_facebook_results(self, page_source: str, search_name: str) -> Dict:
        """Extract Facebook search results"""
        results = {
            'results_count': 0,
            'matches': [],
            'platform': 'facebook',
            'search_name': search_name
        }
        
        # Look for profile links in the page source
        import re
        
        # Facebook profile pattern
        profile_pattern = r'href="(/[^"]*?/profile\.php\?id=\d+)"[^>]*>([^<]+)</a>'
        matches = re.findall(profile_pattern, page_source)
        
        for profile_url, profile_name in matches:
            if search_name.lower() in profile_name.lower():
                results['matches'].append({
                    'name': profile_name.strip(),
                    'profile_url': f"https://www.facebook.com{profile_url}",
                    'platform': 'facebook',
                    'confidence': 0.8
                })
        
        results['results_count'] = len(results['matches'])
        return results
    
    def _extract_linkedin_results(self, page_source: str, search_name: str) -> Dict:
        """Extract LinkedIn search results"""
        results = {
            'results_count': 0,
            'matches': [],
            'platform': 'linkedin',
            'search_name': search_name
        }
        
        import re
        
        # LinkedIn profile pattern
        profile_pattern = r'href="(/in/[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(profile_pattern, page_source)
        
        for profile_url, profile_name in matches:
            if search_name.lower() in profile_name.lower():
                results['matches'].append({
                    'name': profile_name.strip(),
                    'profile_url': f"https://www.linkedin.com{profile_url}",
                    'platform': 'linkedin',
                    'confidence': 0.9
                })
        
        results['results_count'] = len(results['matches'])
        return results
    
    def _extract_twitter_results(self, page_source: str, search_name: str) -> Dict:
        """Extract Twitter search results"""
        results = {
            'results_count': 0,
            'matches': [],
            'platform': 'twitter',
            'search_name': search_name
        }
        
        import re
        
        # Twitter profile pattern
        profile_pattern = r'href="(/([^"]+))"[^>]*>@([^<]+)</a>'
        matches = re.findall(profile_pattern, page_source)
        
        for profile_url, username, display_name in matches:
            if search_name.lower() in display_name.lower() or search_name.lower() in username.lower():
                results['matches'].append({
                    'name': display_name.strip(),
                    'username': username.strip(),
                    'profile_url': f"https://twitter.com{profile_url}",
                    'platform': 'twitter',
                    'confidence': 0.8
                })
        
        results['results_count'] = len(results['matches'])
        return results
    
    def _extract_github_results(self, page_source: str, search_name: str) -> Dict:
        """Extract GitHub search results"""
        results = {
            'results_count': 0,
            'matches': [],
            'platform': 'github',
            'search_name': search_name
        }
        
        import re
        
        # GitHub profile pattern
        profile_pattern = r'href="(/([^"]+))"[^>]*>([^<]+)</a>'
        matches = re.findall(profile_pattern, page_source)
        
        for profile_url, username, display_name in matches:
            if search_name.lower() in display_name.lower() or search_name.lower() in username.lower():
                results['matches'].append({
                    'name': display_name.strip(),
                    'username': username.strip(),
                    'profile_url': f"https://github.com{profile_url}",
                    'platform': 'github',
                    'confidence': 0.9
                })
        
        results['results_count'] = len(results['matches'])
        return results
    
    def _extract_instagram_results(self, page_source: str, search_name: str) -> Dict:
        """Extract Instagram search results"""
        results = {
            'results_count': 0,
            'matches': [],
            'platform': 'instagram',
            'search_name': search_name
        }
        
        import re
        
        # Instagram profile pattern - look for actual profile links
        profile_pattern = r'href="(/([^"]+))"[^>]*>([^<]+)</a>'
        matches = re.findall(profile_pattern, page_source)
        
        # Also check for "User not found" or similar error messages
        if 'User not found' in page_source or 'Sorry, this page isn\'t available' in page_source:
            logger.info(f"Instagram account not found for search: {search_name}")
            return results
        
        # Look for actual profile matches
        for profile_url, username, display_name in matches:
            # Filter for actual profile links (not hashtags or other content)
            if len(username) > 3 and not username.startswith('#'):
                if search_name.lower() in display_name.lower() or search_name.lower() in username.lower():
                    results['matches'].append({
                        'name': display_name.strip(),
                        'username': username.strip(),
                        'profile_url': f"https://www.instagram.com{profile_url}",
                        'platform': 'instagram',
                        'confidence': 0.7
                    })
        
        results['results_count'] = len(results['matches'])
        
        # Log the results
        if results['results_count'] > 0:
            logger.info(f"Found {results['results_count']} Instagram profiles for '{search_name}'")
        else:
            logger.info(f"No Instagram profiles found for '{search_name}'")
        
        return results
    
    def _extract_tiktok_results(self, page_source: str, search_name: str) -> Dict:
        """Extract TikTok search results"""
        results = {
            'results_count': 0,
            'matches': [],
            'platform': 'tiktok',
            'search_name': search_name
        }
        
        import re
        
        # TikTok profile pattern
        profile_pattern = r'href="(/([^"]+))"[^>]*>([^<]+)</a>'
        matches = re.findall(profile_pattern, page_source)
        
        for profile_url, username, display_name in matches:
            if search_name.lower() in display_name.lower() or search_name.lower() in username.lower():
                results['matches'].append({
                    'name': display_name.strip(),
                    'username': username.strip(),
                    'profile_url': f"https://www.tiktok.com{profile_url}",
                    'platform': 'tiktok',
                    'confidence': 0.7
                })
        
        results['results_count'] = len(results['matches'])
        return results
    
    def _calculate_confidence(self, names: List[Dict]) -> float:
        """Calculate overall confidence score for lookup results"""
        if not names:
            return 0.0
        
        total_confidence = 0.0
        for name_data in names:
            total_confidence += name_data.get('confidence', 0.0)
        
        return min(1.0, total_confidence / len(names))
    
    def _calculate_name_lookup_confidence(self, profiles: List[Dict]) -> float:
        """Calculate confidence score for name-based lookups"""
        if not profiles:
            return 0.0
        
        total_confidence = 0.0
        for profile in profiles:
            total_confidence += profile.get('confidence', 0.0)
        
        return min(1.0, total_confidence / len(profiles))
    
    def _calculate_reverse_lookup_confidence(self, usernames: List[Dict]) -> float:
        """Calculate confidence score for reverse lookups"""
        if not usernames:
            return 0.0
        
        # Higher confidence for more platforms found
        platform_counts = {}
        for username_data in usernames:
            platform = username_data.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # More platforms = higher confidence
        confidence = min(1.0, len(platform_counts) / len(self.lookup_sources['social_media']))
        return confidence
    
    def _deduplicate_names(self, names: List[Dict]) -> List[Dict]:
        """Remove duplicate names and sort by confidence"""
        # Create a dictionary to track unique names with highest confidence
        unique_names = {}
        
        for name_data in names:
            name = name_data.get('name', '').lower().strip()
            if name:
                if name not in unique_names or name_data.get('confidence', 0) > unique_names[name].get('confidence', 0):
                    unique_names[name] = name_data
        
        # Sort by confidence (highest first)
        sorted_names = sorted(unique_names.values(), key=lambda x: x.get('confidence', 0), reverse=True)
        
        return sorted_names
    
    def save_lookup_result(self, result: Dict) -> int:
        """Save lookup result to database"""
        try:
            # Create a new OSINT result for the lookup
            osint_result = OSINTResult(
                url=f"name_lookup_{result.get('username', 'unknown')}",
                platform='name_lookup',
                username=result.get('username', 'unknown'),
                profile_data=result,
                confidence_score=result.get('confidence_score', 0.0),
                status_code=200,
                error_message=None,
                is_bot_detected=False,
                detection_method='name_lookup',
                html_hash=None,
                screenshot_hash=None
            )
            
            self.session.add(osint_result)
            self.session.commit()
            
            logger.info(f"Saved name lookup result to database with ID: {osint_result.id}")
            return osint_result.id
            
        except Exception as e:
            logger.error(f"Error saving lookup result to database: {e}")
            self.session.rollback()
            return None
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
