import hashlib
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
from config import Config
import json
import time

logger = logging.getLogger(__name__)

class BotDetector:
    def __init__(self):
        self.config = Config()
        
        # Enhanced bot detection patterns
        self.bot_detection_patterns = [
            r'bot.*detected',
            r'access.*denied',
            r'blocked.*request',
            r'suspicious.*activity',
            r'rate.*limit.*exceeded',
            r'too.*many.*requests',
            r'captcha',
            r'verify.*human',
            r'security.*check',
            r'blocked.*ip',
            r'cloudflare',
            r'ddos.*protection',
            r'checking.*browser',
            r'please.*wait',
            r'challenge.*page'
        ]
        
        # Enhanced error page indicators with heavy 404 focus
        self.error_indicators = [
            # 404-specific indicators (highest priority)
            '404',
            'page not found',
            'not found',
            'page not available',
            'sorry, this page isn\'t available',
            'sorry, this page is not available',
            'this page is not available',
            'page may have been removed',
            'link you followed may be broken',
            'page removed',
            'content not available',
            'this content isn\'t available right now',
            'content isn\'t available right now',
            'user not found',
            'account not found',
            'profile not found',
            'page doesn\'t exist',
            'page does not exist',
            'no such page',
            'page unavailable',
            'page not accessible',
            'page not available',
            # Other error indicators (more specific to avoid username conflicts)
            'access denied',
            'forbidden',
            'unauthorized',
            'account suspended',
            'account deleted',
            'maintenance',
            'temporarily unavailable',
            'private account',
            'authwall'  # LinkedIn authentication wall indicates profile likely doesn't exist
        ]
        
        # Login wall indicators - more specific to avoid false positives
        self.login_wall_indicators = [
            'you must log in to continue',
            'log into facebook',
            'log in to facebook',
            'please log in',
            'sign in to continue',
            'login required',
            'authentication required'
        ]
        
        # Enhanced platform-specific detection patterns
        self.platform_patterns = {
            'facebook': {
                'login_redirects': ['/login', '/checkpoint', '/login.php', '/login/', '/recover', '/help'],
                'blocked_indicators': ['checkpoint', 'blocked', 'suspended', 'security check', 'community standards', 'content removed'],
                'profile_indicators': ['profile.php', 'profile', 'timeline', 'posts', 'photos'],
                'error_patterns': [
                    r'sorry.*page.*not.*available',
                    r'this.*content.*not.*available',
                    r'this.*content.*isn\'t.*available.*right.*now',
                    r'content.*isn\'t.*available.*right.*now',
                    r'page.*not.*found',
                    r'user.*not.*found',
                    r'checkpoint.*required',
                    r'security.*check',
                    r'community.*standards',
                    r'content.*unavailable',
                    r'owner.*only.*shared.*with.*small.*group',
                    r'changed.*who.*can.*see',
                    r'been.*deleted'
                ],
                'success_patterns': [
                    r'profile.*photo',
                    r'cover.*photo',
                    r'posts',
                    r'friends',
                    r'about'
                ]
            },
            'instagram': {
                'login_redirects': ['/accounts/login', '/login', '/accounts/login/'],
                'blocked_indicators': ['blocked', 'suspended', 'checkpoint', 'challenge'],
                'profile_indicators': ['/p/', '/reel/', '/stories/', 'posts', 'followers'],
                'error_patterns': [
                    r'sorry.*page.*not.*available',
                    r'sorry.*page.*isn\'t.*available',
                    r'link.*followed.*may.*be.*broken',
                    r'page.*may.*have.*been.*removed',
                    r'user.*not.*found',
                    r'account.*not.*found',
                    r'profile.*not.*found'
                    # Removed 'account.*private' and 'this.*account.*is.*private' - these are valid accounts
                ],
                'success_patterns': [
                    r'posts',
                    r'followers', 
                    r'following',
                    r'bio',
                    r'profile.*picture',
                    r'instagram',
                    r'story',
                    r'stories',
                    r'tagged',
                    r'reels',
                    r'highlights',
                    r'verified',
                    r'follow.*button',
                    r'message.*button',
                    r'profile.*photo',
                    r'edit.*profile'
                ]
            },
            'twitter': {
                'login_redirects': ['/login', '/i/flow/login', '/login/'],
                'blocked_indicators': ['suspended', 'blocked', 'unavailable', 'restricted'],
                'profile_indicators': ['/status/', '/photo/', '/video/', 'tweets', 'following'],
                'error_patterns': [
                    r'this.*account.*doesn.*exist',
                    r'account.*suspended',
                    r'user.*not.*found',
                    r'page.*not.*found',
                    r'404',
                    r'doesn.*exist',
                    r'try.*searching.*for.*another',
                    r'account.*not.*found'
                ],
                'success_patterns': [
                    r'tweets',
                    r'following',
                    r'followers',
                    r'bio',
                    r'location'
                ]
            },
            'linkedin': {
                'login_redirects': ['/login', '/uas/login', '/login/', '/authwall'],
                'blocked_indicators': ['blocked', 'restricted', 'unavailable', 'access denied', 'authwall'],
                'profile_indicators': ['/in/', '/company/', '/school/', 'experience', 'education'],
                'error_patterns': [
                    r'404',
                    r'page.*not.*found',
                    r'profile.*not.*found',
                    r'this.*profile.*doesn.*exist',
                    r'page.*unavailable',
                    r'page.*not.*available',
                    r'profile.*not.*available',
                    r'user.*not.*found',
                    r'account.*not.*found',
                    r'page.*doesn.*exist',
                    r'page.*does.*not.*exist',
                    r'no.*such.*page',
                    r'page.*removed',
                    r'page.*deleted',
                    r'authwall'  # LinkedIn authentication wall
                ],
                'success_patterns': [
                    r'experience',
                    r'education',
                    r'connections',
                    r'about',
                    r'contact.*info'
                ]
            },
            'github': {
                'login_redirects': ['/login', '/signup', '/join'],
                'blocked_indicators': ['blocked', 'suspended', 'unavailable', 'restricted'],
                'profile_indicators': ['/repositories', '/stars', '/followers', '/following'],
                'error_patterns': [
                    r'404',
                    r'page.*not.*found',
                    r'user.*not.*found',
                    r'this.*user.*doesn.*exist',
                    r'page.*unavailable',
                    r'user.*unavailable',
                    r'account.*not.*found',
                    r'page.*doesn.*exist',
                    r'page.*does.*not.*exist',
                    r'no.*such.*user',
                    r'user.*removed',
                    r'user.*deleted'
                ],
                'success_patterns': [
                    r'repositories',
                    r'followers',
                    r'following',
                    r'stars',
                    r'bio',
                    r'location',
                    r'company',
                    r'blog',
                    r'pinned',
                    r'contributions',
                    r'overview',
                    r'projects',
                    r'packages',
                    r'follow',
                    r'block',
                    r'report',
                    r'avatar',
                    r'profile'
                ]
            }
        }
        
        # Account validation patterns
        self.account_validation_patterns = {
            'real_account_indicators': [
                'profile', 'posts', 'followers', 'following', 'bio', 'about',
                'experience', 'education', 'connections', 'tweets', 'photos',
                'videos', 'stories', 'timeline', 'feed', 'activity', 'verified',
                'join', 'joined', 'member', 'follow', 'message', 'contact',
                'website', 'link', 'location', 'works at', 'lives in',
                'highlights', 'reels', 'tagged', 'mentions', 'likes',
                'comments', 'shares', 'views', 'profile photo', 'cover photo'
            ],
            'fake_account_indicators': [
                'bot', 'spam', 'fake', 'account suspended', 'account deleted', 'account blocked',
                'not found', 'unavailable', 'restricted', 'removed', 'violated'
                # Removed 'private' - private accounts are still real accounts
            ]
        }
    
    def analyze_page(self, html_content, url, status_code, platform=None):
        """
        Enhanced page analysis with improved accuracy
        
        Returns:
            dict: Analysis results with confidence score and detection details
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Step 1: Enhanced page structure analysis
            structure_score = self._analyze_page_structure_enhanced(soup, url, platform)
            
            # Step 2: Enhanced error analysis
            error_score = self._analyze_error_indicators_enhanced(soup, status_code, url, platform)
            
            # Step 3: Enhanced bot detection analysis
            bot_detection_score = self._analyze_bot_detection_enhanced(soup, html_content, platform)
            
            # Step 4: Enhanced platform-specific analysis
            platform_score = self._analyze_platform_specific_enhanced(soup, url, platform)
            
            # Step 5: Account validation analysis
            account_validation_score = self._analyze_account_validation(soup, html_content, platform)
            
            # Step 6: URL and redirect analysis
            url_analysis_score = self._analyze_url_patterns(url, platform)
            
            # Calculate overall confidence score with enhanced weighting
            confidence_score = self._calculate_enhanced_confidence(
                structure_score, error_score, bot_detection_score, 
                platform_score, account_validation_score, url_analysis_score
            )
            
            # Determine if bot is detected with improved thresholds
            is_bot_detected = confidence_score < self.config.LOW_CONFIDENCE
            
            # Determine detection method
            detection_method = self._determine_enhanced_detection_method(
                structure_score, error_score, bot_detection_score, 
                platform_score, account_validation_score, url_analysis_score
            )
            
            # Additional validation checks
            validation_details = self._get_validation_details(
                soup, html_content, url, platform, confidence_score
            )
            
            return {
                'confidence_score': confidence_score,
                'is_bot_detected': is_bot_detected,
                'detection_method': detection_method,
                'structure_score': structure_score,
                'error_score': error_score,
                'bot_detection_score': bot_detection_score,
                'platform_score': platform_score,
                'account_validation_score': account_validation_score,
                'url_analysis_score': url_analysis_score,
                'html_hash': hashlib.sha256(html_content.encode()).hexdigest(),
                'validation_details': validation_details,
                'platform': platform,
                'url': url,
                'status_code': status_code
            }
            
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            return {
                'confidence_score': 0.0,
                'is_bot_detected': True,
                'detection_method': 'analysis_error',
                'error': str(e)
            }
    
    def _analyze_page_structure_enhanced(self, soup, url, platform):
        """Enhanced page structure analysis"""
        score = 0.5  # Base score
        
        try:
            # Check for basic HTML structure
            if soup.find('html') and soup.find('body'):
                score += 0.1
            
            # Check for meaningful content length
            text_content = soup.get_text()
            if len(text_content) > 200:
                score += 0.1
            elif len(text_content) > 1000:
                score += 0.2
            
            # Enhanced social media elements check
            social_elements = [
                'profile', 'post', 'tweet', 'photo', 'video', 'story',
                'follower', 'following', 'like', 'comment', 'share',
                'bio', 'about', 'experience', 'education', 'connections'
            ]
            
            found_elements = sum(1 for elem in social_elements if elem.lower() in text_content.lower())
            if found_elements >= 3:
                score += 0.2
            elif found_elements >= 1:
                score += 0.1
            
            # Check for navigation elements
            nav_elements = soup.find_all(['nav', 'header', 'footer', 'menu'])
            if nav_elements:
                score += 0.1
            
            # Check for images or media
            media_elements = soup.find_all(['img', 'video', 'audio'])
            if media_elements:
                score += 0.1
            
            # Check for interactive elements
            interactive_elements = soup.find_all(['button', 'input', 'form', 'a'])
            if len(interactive_elements) > 10:
                score += 0.1
            
            # Check for platform-specific content
            if platform and platform in self.platform_patterns:
                platform_config = self.platform_patterns[platform]
                success_patterns = platform_config.get('success_patterns', [])
                found_success = sum(1 for pattern in success_patterns if re.search(pattern, text_content, re.IGNORECASE))
                if found_success > 0:
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing page structure: {e}")
            return 0.3
    
    def _analyze_error_indicators_enhanced(self, soup, status_code, url, platform):
        """Enhanced error analysis with 90% 404 penalties"""
        score = 1.0  # Start with perfect score
        
        try:
            # IMMEDIATE 90% PENALTY for 404 URLs - check this FIRST
            url_lower = url.lower()
            if '404' in url_lower or 'notfound' in url_lower:
                return 0.1  # Return 10% immediately for 404 URLs (90% penalty)
            
            # 90% PENALTY for 404 status codes
            if status_code == 404:
                score -= 0.9  # 90% penalty for 404
            elif status_code >= 400:
                score -= 0.6  # Strong penalty for other 4xx errors
            
            # Check for error text in content
            text_content = soup.get_text().lower()
            
            # 90% PENALTY for 404 error indicators in content
            if '404' in text_content or 'page not found' in text_content:
                score -= 0.9  # 90% penalty for 404 content
            
            # Enhanced error pattern matching with stronger penalties (but avoid matching usernames)
            for error_indicator in self.error_indicators:
                if error_indicator in text_content:
                    # Avoid matching usernames that contain error words
                    if f"@{error_indicator}" in text_content or f"@{error_indicator.upper()}" in text_content:
                        continue  # Skip if it's clearly a username
                    # Check if it's in a sentence context (more likely to be an error message)
                    if f" {error_indicator} " in text_content or f" {error_indicator}." in text_content:
                        score -= 0.9  # Much stronger penalty for error indicators
                        break
            
            # Special check for Twitter's JavaScript-rendered error pages
            if platform == 'twitter':
                # Check for Twitter's error page indicators
                twitter_error_indicators = [
                    '404', 'doesn\'t exist', 'try searching', 'account doesn\'t exist'
                ]
                for indicator in twitter_error_indicators:
                    if indicator in text_content:
                        score -= 0.9  # 90% penalty for Twitter error indicators
                        break
            
            # Platform-specific error patterns with stronger penalties
            if platform and platform in self.platform_patterns:
                platform_config = self.platform_patterns[platform]
                error_patterns = platform_config.get('error_patterns', [])
                for pattern in error_patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        score -= 0.9  # 90% penalty for platform-specific errors
                        break
            
            # 90% PENALTY for error page titles
            title = soup.find('title')
            if title:
                title_text = title.get_text().lower()
                if '404' in title_text or 'page not found' in title_text:
                    score -= 0.9  # 90% penalty for 404 in title
                elif any(error in title_text for error in self.error_indicators):
                    score -= 0.6  # Strong penalty for other errors in title
            
            # Check for other error URLs (already checked 404 above)
            if any(error in url_lower for error in ['error', 'blocked', 'suspended']):
                score -= 0.6  # Strong penalty for other errors in URL
            
            # Check for empty or minimal content
            if len(text_content.strip()) < 50:
                score -= 0.4  # Increased penalty for minimal content
            
            # Check for login walls - but only if we don't have real profile content
            has_real_content = False
            if platform and platform in self.platform_patterns:
                platform_config = self.platform_patterns[platform]
                success_patterns = platform_config.get('success_patterns', [])
                found_success = sum(1 for pattern in success_patterns if re.search(pattern, text_content, re.IGNORECASE))
                if found_success > 0:
                    has_real_content = True
            
            # Only apply login wall penalty if we don't have real profile content
            if not has_real_content:
                for login_indicator in self.login_wall_indicators:
                    if login_indicator in text_content:
                        score -= 0.7  # Strong penalty for login walls, but not as harsh as 404
                        break
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Error analyzing error indicators: {e}")
            return 0.5
    
    def _analyze_bot_detection_enhanced(self, soup, html_content, platform):
        """Enhanced bot detection analysis"""
        score = 1.0  # Start with perfect score
        
        try:
            text_content = html_content.lower()
            
            # Enhanced bot detection patterns with stronger penalties
            for pattern in self.bot_detection_patterns:
                if re.search(pattern, text_content, re.IGNORECASE):
                    score -= 0.6  # Increased penalty
                    break
            
            # Check for CAPTCHA elements with stronger penalties
            captcha_indicators = ['captcha', 'recaptcha', 'hcaptcha', 'verify', 'challenge']
            if any(indicator in text_content for indicator in captcha_indicators):
                score -= 0.5  # Increased penalty
            
            # Check for security check pages with stronger penalties
            security_indicators = ['security check', 'verify identity', 'confirm human', 'checking browser']
            if any(indicator in text_content for indicator in security_indicators):
                score -= 0.5  # Increased penalty
            
            # Check for rate limiting with stronger penalties
            rate_limit_indicators = ['rate limit', 'too many requests', 'try again later', 'please wait']
            if any(indicator in text_content for indicator in rate_limit_indicators):
                score -= 0.4  # Increased penalty
            
            # Check for Cloudflare or DDoS protection with stronger penalties
            protection_indicators = ['cloudflare', 'ddos protection', 'checking your browser']
            if any(indicator in text_content for indicator in protection_indicators):
                score -= 0.4  # Increased penalty
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Error analyzing bot detection: {e}")
            return 0.5
    
    def _analyze_platform_specific_enhanced(self, soup, url, platform):
        """Enhanced platform-specific analysis"""
        if not platform or platform not in self.platform_patterns:
            return 0.5
        
        score = 0.5  # Base score
        platform_config = self.platform_patterns[platform]
        
        try:
            url_lower = url.lower()
            text_content = soup.get_text().lower()
            
            # Check for login redirects with stronger penalties
            if any(redirect in url_lower for redirect in platform_config['login_redirects']):
                score -= 0.5  # Increased penalty
            
            # Check for blocked indicators with stronger penalties (but avoid matching usernames)
            blocked_indicators = platform_config['blocked_indicators']
            for indicator in blocked_indicators:
                # Avoid matching usernames that contain error words
                if indicator in text_content:
                    # Check if it's likely part of a username (preceded by @ or in specific contexts)
                    if f"@{indicator}" in text_content or f"@{indicator.upper()}" in text_content:
                        continue  # Skip if it's clearly a username
                    # Check if it's in a sentence context (more likely to be an error message)
                    if f" {indicator} " in text_content or f" {indicator}." in text_content:
                        score -= 0.6  # Increased penalty
                        break
            
            # Check for profile indicators in page content (not URL)
            if any(indicator in text_content for indicator in platform_config['profile_indicators']):
                score += 0.2
            
            # Enhanced platform-specific content checks
            success_patterns = platform_config.get('success_patterns', [])
            found_success = sum(1 for pattern in success_patterns if re.search(pattern, text_content, re.IGNORECASE))
            if found_success >= 4:
                score += 0.4  # Very strong real account signal
            elif found_success >= 3:
                score += 0.3  # Strong real account signal
            elif found_success >= 2:
                score += 0.2  # Good real account signal
            elif found_success >= 1:
                score += 0.1  # Basic real account signal
            
            # Platform-specific validation
            if platform == 'facebook':
                if 'timeline' in text_content or 'profile' in text_content or 'posts' in text_content:
                    score += 0.1
            elif platform == 'instagram':
                # Enhanced Instagram real account detection
                instagram_indicators = ['post', 'story', 'bio', 'followers', 'following', 'highlights', 
                                      'reels', 'tagged', 'verified', 'instagram', 'profile photo']
                found_indicators = sum(1 for indicator in instagram_indicators if indicator in text_content)
                if found_indicators >= 3:
                    score += 0.3  # Strong Instagram account signal
                elif found_indicators >= 2:
                    score += 0.2  # Good Instagram account signal  
                elif found_indicators >= 1:
                    score += 0.1  # Basic Instagram account signal
            elif platform == 'twitter':
                if 'tweet' in text_content or 'follow' in text_content or 'bio' in text_content:
                    score += 0.1
            elif platform == 'linkedin':
                if 'connection' in text_content or 'experience' in text_content or 'education' in text_content:
                    score += 0.1
            elif platform == 'github':
                if 'follow' in text_content or 'overview' in text_content or 'repositories' in text_content or 'profile' in text_content:
                    score += 0.1
            
            return max(min(score, 1.0), 0.0)
            
        except Exception as e:
            logger.error(f"Error analyzing platform-specific indicators: {e}")
            return 0.5
    
    def _analyze_account_validation(self, soup, html_content, platform):
        """Analyze account validation patterns (page content only, not URLs)"""
        score = 0.5  # Base score
        
        try:
            # Extract only visible text content from the page, not the URL
            if soup:
                visible_text = soup.get_text(separator=' ', strip=True).lower()
            else:
                visible_text = html_content.lower()
            
            # Check for real account indicators (in page content only)
            real_indicators = self.account_validation_patterns['real_account_indicators']
            found_real = sum(1 for indicator in real_indicators if indicator in visible_text)
            if found_real >= 3:
                score += 0.3
            elif found_real >= 1:
                score += 0.1
            
            # Check for fake account indicators (in page content only)
            fake_indicators = self.account_validation_patterns['fake_account_indicators']
            found_fake = 0
            for indicator in fake_indicators:
                if indicator in visible_text:
                    # Avoid matching usernames that contain error words
                    if f"@{indicator}" in visible_text or f"@{indicator.upper()}" in visible_text:
                        continue  # Skip if it's clearly a username
                    # Check if it's in a sentence context (more likely to be an error message)
                    if f" {indicator} " in visible_text or f" {indicator}." in visible_text:
                        found_fake += 1
            
            if found_fake >= 2:
                score -= 0.4
            elif found_fake >= 1:
                score -= 0.2
            
            return max(min(score, 1.0), 0.0)
            
        except Exception as e:
            logger.error(f"Error analyzing account validation: {e}")
            return 0.5
    
    def _analyze_url_patterns(self, url, platform):
        """Analyze URL patterns for validity with 90% 404 penalties"""
        score = 0.5  # Base score
        
        try:
            url_lower = url.lower()
            
            # 90% PENALTY for 404 URLs - check this FIRST
            if '404' in url_lower or 'notfound' in url_lower:
                return 0.1  # Return 10% immediately for 404 URLs (90% penalty)
            
            # Check for valid platform URLs
            if platform == 'facebook' and 'facebook.com' in url_lower:
                score += 0.2
            elif platform == 'instagram' and 'instagram.com' in url_lower:
                score += 0.2
            elif platform == 'twitter' and ('twitter.com' in url_lower or 'x.com' in url_lower):
                score += 0.2
            elif platform == 'linkedin' and 'linkedin.com' in url_lower:
                score += 0.2
            elif platform == 'github' and 'github.com' in url_lower:
                score += 0.2
            
            # Check for other error URLs (but avoid penalizing usernames)
            error_words = ['error', 'blocked', 'suspended']
            for error_word in error_words:
                if error_word in url_lower:
                    # Check if it's part of a username path (like /suspendeduser)
                    if f"/{error_word}" in url_lower and not any(f"/{error_word}/" in url_lower for e in ['error/', 'blocked/', 'suspended/']):
                        continue  # Skip if it's likely a username
                    # Check if it's in error context
                    if any(f"/{error_word}/" in url_lower for e in ['error/', 'blocked/', 'suspended/']):
                        score -= 0.6  # Strong penalty for other errors
                        break
            
            # Check for login redirects and authentication walls
            if any(redirect in url_lower for redirect in ['login', 'signin', 'auth']):
                score -= 0.3  # Increased penalty
            
            # HEAVY PENALTY for LinkedIn authwall - this indicates profile doesn't exist or requires login
            if platform == 'linkedin' and 'authwall' in url_lower:
                return 0.1  # Very low score for authwall redirects
            
            return max(min(score, 1.0), 0.0)
            
        except Exception as e:
            logger.error(f"Error analyzing URL patterns: {e}")
            return 0.5
    
    def _calculate_enhanced_confidence(self, structure_score, error_score, bot_detection_score, 
                                     platform_score, account_validation_score, url_analysis_score):
        """Calculate balanced confidence score with reasonable error detection and strong real account signals"""
        # Rebalanced weights for better accuracy with real accounts
        weights = {
            'structure': 0.20,           # Increased - important for real account detection
            'error': 0.40,               # Reduced from 90% - still important but not overwhelming
            'bot_detection': 0.15,       # Increased - bot detection is important
            'platform': 0.15,            # Increased - platform-specific indicators matter
            'account_validation': 0.08,  # Significantly increased - real account patterns matter
            'url_analysis': 0.02         # Minimal weight for URL patterns
        }
        
        confidence = (
            structure_score * weights['structure'] +
            error_score * weights['error'] +
            bot_detection_score * weights['bot_detection'] +
            platform_score * weights['platform'] +
            account_validation_score * weights['account_validation'] +
            url_analysis_score * weights['url_analysis']
        )
        
        return round(confidence, 3)
    
    def _determine_enhanced_detection_method(self, structure_score, error_score, bot_detection_score, 
                                           platform_score, account_validation_score, url_analysis_score):
        """Determine the primary detection method used"""
        if bot_detection_score < 0.5:
            return 'bot_detection_patterns'
        elif error_score < 0.5:
            return 'error_indicators'
        elif structure_score < 0.5:
            return 'page_structure_analysis'
        elif platform_score < 0.5:
            return 'platform_specific_indicators'
        elif account_validation_score < 0.5:
            return 'account_validation'
        elif url_analysis_score < 0.5:
            return 'url_pattern_analysis'
        else:
            return 'combined_enhanced_analysis'
    
    def _get_validation_details(self, soup, html_content, url, platform, confidence_score):
        """Get detailed validation information"""
        try:
            details = {
                'content_length': len(html_content),
                'text_length': len(soup.get_text()),
                'has_images': len(soup.find_all('img')) > 0,
                'has_links': len(soup.find_all('a')) > 0,
                'has_forms': len(soup.find_all('form')) > 0,
                'platform_detected': platform,
                'url_analysis': self._analyze_url_details(url),
                'content_analysis': self._analyze_content_details(soup, html_content, platform)
            }
            
            # Add confidence level
            details['confidence_level'] = self.get_confidence_level(confidence_score)
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting validation details: {e}")
            return {'error': str(e)}
    
    def _analyze_url_details(self, url):
        """Analyze URL details"""
        try:
            parsed = urlparse(url)
            return {
                'domain': parsed.netloc,
                'path': parsed.path,
                'query': parsed.query,
                'fragment': parsed.fragment,
                'is_secure': parsed.scheme == 'https'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_content_details(self, soup, html_content, platform):
        """Analyze content details"""
        try:
            text_content = soup.get_text()
            
            details = {
                'word_count': len(text_content.split()),
                'has_title': soup.find('title') is not None,
                'has_meta_description': soup.find('meta', attrs={'name': 'description'}) is not None,
                'social_elements_found': []
            }
            
            # Check for social media elements
            social_elements = ['profile', 'post', 'tweet', 'photo', 'video', 'story', 'bio', 'about']
            for element in social_elements:
                if element in text_content.lower():
                    details['social_elements_found'].append(element)
            
            return details
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_confidence_level(self, confidence_score):
        """Get confidence level description"""
        if confidence_score >= self.config.HIGH_CONFIDENCE:
            return 'HIGH'
        elif confidence_score >= self.config.MEDIUM_CONFIDENCE:
            return 'MEDIUM'
        elif confidence_score >= self.config.LOW_CONFIDENCE:
            return 'LOW'
        else:
            return 'VERY_LOW'
