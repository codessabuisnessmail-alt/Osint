#!/usr/bin/env python3
"""
🔍 OSINT Social Media Profile Finder - High Performance Version
============================================================

A powerful and user-friendly tool to find social media profiles using real names.
Optimized for maximum speed with concurrent processing and intelligent caching.

USAGE EXAMPLES:
    # Find profiles for a person by name
    python osint_cli_simple.py search "John Doe"
    
    # Quick demo with sample data
    python osint_cli_simple.py demo "John Doe"
    
    # Check specific username
    python osint_cli_simple.py check-username "johndoe123"
    
    # Get system status and configuration
    python osint_cli_simple.py status
    
    # Show detailed help
    python osint_cli_simple.py --help
    python osint_cli_simple.py search --help
"""

import argparse
import sys
import os
import json
import asyncio
import concurrent.futures
import threading
from datetime import datetime
from pathlib import Path
from functools import lru_cache
import time
import random

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from username_generator import UsernameGenerator
from detection.bot_detector import BotDetector
from browser.selenium_stealth import SeleniumStealthBrowser
from scraper.cookie_manager import CookieManager
from config import Config

class FastOSINTScraper:
    """High-performance OSINT scraper with concurrent processing"""
    
    def __init__(self, max_workers=4):
        self.config = Config()
        self.bot_detector = BotDetector()
        self.cookie_manager = CookieManager()
        self.max_workers = max_workers
        self.browser_pool = []
        self.browser_lock = threading.Lock()
        
        # Import cookies from user's browser profiles for logged-in sessions
        self._import_user_cookies()
        
        # Initialize browser pool for concurrent processing
        self._init_browser_pool()
    
    def _import_user_cookies(self):
        """Import cookies from user's browser profiles"""
        try:
            print("🍪 Importing cookies from user's browser profiles...")
            
            # Try to import from Edge first (most common for Windows)
            edge_cookies = self.cookie_manager.import_cookies_from_browser('edge', 'default')
            if edge_cookies:
                total_cookies = sum(len(cookies) for cookies in edge_cookies.values())
                print(f"✅ Imported {total_cookies} cookies from Edge")
            
            # Try Chrome as fallback
            chrome_cookies = self.cookie_manager.import_cookies_from_browser('chrome', 'default')
            if chrome_cookies:
                total_cookies = sum(len(cookies) for cookies in chrome_cookies.values())
                print(f"✅ Imported {total_cookies} cookies from Chrome")
            
            # Show cookie summary
            summary = self.cookie_manager.get_cookie_summary()
            if summary:
                print("📊 Cookie Summary:")
                for platform, count in summary.items():
                    print(f"   • {platform}: {count} cookies")
            
        except Exception as e:
            print(f"⚠️  Error importing cookies: {e}")
    
    def _init_browser_pool(self):
        """Initialize a pool of browser instances for concurrent processing"""
        try:
            print(f"🌐 Initializing browser pool with {self.max_workers} workers...")
            for i in range(self.max_workers):
                browser = SeleniumStealthBrowser(
                    headless=self.config.HEADLESS,
                    viewport_width=self.config.VIEWPORT_WIDTH,
                    viewport_height=self.config.VIEWPORT_HEIGHT
                )
                self.browser_pool.append(browser)
            print(f"✅ Browser pool initialized with {len(self.browser_pool)} instances")
        except Exception as e:
            print(f"❌ Error initializing browser pool: {e}")
    
    def _get_browser(self):
        """Get a browser from the pool"""
        with self.browser_lock:
            if self.browser_pool:
                return self.browser_pool.pop()
            else:
                # Create new browser if pool is empty
                return SeleniumStealthBrowser(
                    headless=self.config.HEADLESS,
                    viewport_width=self.config.VIEWPORT_WIDTH,
                    viewport_height=self.config.VIEWPORT_HEIGHT
                )
    
    def _return_browser(self, browser):
        """Return a browser to the pool"""
        with self.browser_lock:
            if len(self.browser_pool) < self.max_workers:
                self.browser_pool.append(browser)
            else:
                browser.quit()
    
    def _inject_cookies_for_platform(self, browser, platform):
        """Inject cookies for the specific platform to maintain logged-in session"""
        try:
            if platform and platform in ['facebook', 'instagram', 'twitter', 'linkedin', 'github']:
                success = self.cookie_manager.inject_cookies_to_selenium(browser, platform)
                if success:
                    return True
                else:
                    return False
        except Exception as e:
            return False
    
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
    
    def scrape_profile_fast(self, url, platform=None, username=None):
        """Fast profile scraping with optimized timing"""
        try:
            # Determine platform if not provided
            if not platform:
                platform = self._detect_platform(url)
            
            # Extract username if not provided
            if not username:
                username = self._extract_username(url, platform)
            
            # Get browser from pool
            browser = self._get_browser()
            
            try:
                # Inject cookies for logged-in session
                self._inject_cookies_for_platform(browser, platform)
                
                # Navigate to profile with timeout
                if not browser.navigate_to(url, timeout=10):
                    return self._create_error_result(url, platform, username, "Navigation failed")
                
                # Optimized wait times - reduced for speed
                time.sleep(random.uniform(0.5, 1.5))  # Reduced from 2-4 seconds
                
                # Quick scroll for dynamic content
                browser.scroll_page(quick=True)
                
                # Get page source
                html_content = browser.get_page_source()
                if not html_content:
                    return self._create_error_result(url, platform, username, "Failed to get page source")
                
                # Get current URL (check for redirects)
                current_url = browser.get_page_url()
                page_title = browser.get_page_title()
                
                # Analyze page for bot detection
                analysis_result = self.bot_detector.analyze_page(
                    html_content, current_url, 200, platform
                )
                
                # Create result
                result = {
                    'url': current_url,
                    'platform': platform,
                    'username': username,
                    'profile_data': {'text_content': html_content[:1000]},  # Simplified
                    'confidence_score': analysis_result['confidence_score'],
                    'status_code': 200,
                    'error_message': None,
                    'is_bot_detected': analysis_result['is_bot_detected'],
                    'detection_method': analysis_result['detection_method'],
                    'page_title': page_title,
                    'analysis_details': analysis_result
                }
                
                return result
                
            finally:
                # Return browser to pool
                self._return_browser(browser)
                
        except Exception as e:
            return self._create_error_result(url, platform, username, str(e))
    
    def scrape_profiles_concurrent(self, urls_and_platforms, max_workers=None):
        """Scrape multiple profiles concurrently for maximum speed"""
        if max_workers is None:
            max_workers = min(self.max_workers, len(urls_and_platforms))
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_url = {
                executor.submit(self.scrape_profile_fast, url, platform, username): (url, platform, username)
                for url, platform, username in urls_and_platforms
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url, platform, username = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_result = self._create_error_result(url, platform, username, str(e))
                    results.append(error_result)
        
        return results
    
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
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if platform == 'facebook':
                if path_parts and path_parts[0] and not path_parts[0].startswith('profile.php'):
                    return path_parts[0]
                elif 'id=' in parsed.query:
                    return f"id_{parsed.query.split('id=')[1].split('&')[0]}"
                else:
                    return "unknown"
                    
            elif platform == 'instagram':
                if path_parts and path_parts[0]:
                    return path_parts[0]
                else:
                    return "unknown"
                    
            elif platform == 'twitter':
                if path_parts and path_parts[0]:
                    return path_parts[0]
                else:
                    return "unknown"
                    
            elif platform == 'linkedin':
                if len(path_parts) >= 2 and path_parts[0] == 'in':
                    return path_parts[1]
                else:
                    return "unknown"
                    
            elif platform == 'github':
                if path_parts and path_parts[0]:
                    return path_parts[0]
                else:
                    return "unknown"
                    
            else:
                return "unknown"
                
        except Exception as e:
            return "unknown"
    
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
            'page_title': None,
            'analysis_details': None
        }
    
    def cleanup(self):
        """Clean up browser pool"""
        with self.browser_lock:
            for browser in self.browser_pool:
                try:
                    browser.quit()
                except:
                    pass
            self.browser_pool.clear()

class OSINTCLI:
    def __init__(self):
        self.setup_parser()
    
    def setup_parser(self):
        """Setup command line argument parser with comprehensive help"""
        self.parser = argparse.ArgumentParser(
            prog='osint_cli_simple.py',
            description='🔍 OSINT Social Media Profile Finder - High Performance Version',
            epilog='''
EXAMPLES:
  python osint_cli_simple.py search "John Doe" --platforms twitter github instagram linkedin
  python osint_cli_simple.py demo "John Doe" --platforms twitter github instagram
  python osint_cli_simple.py check-username "johndoe123" --platforms linkedin twitter
  python osint_cli_simple.py status

PLATFORMS SUPPORTED:
  • Twitter/X (twitter.com)
  • GitHub (github.com) 
  • Instagram (instagram.com)
  • LinkedIn (linkedin.com)
  • Facebook (facebook.com)

FEATURES:
  • Advanced username generation algorithms
  • Real-time profile validation with confidence scoring
  • Anti-bot detection bypass with logged-in sessions
  • Cookie management from browser profiles
  • High-performance concurrent processing
  • Browser connection pooling for maximum speed
            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Create subparsers for different commands
        subparsers = self.parser.add_subparsers(
            dest='command',
            help='Available commands (use --help for detailed info)',
            metavar='COMMAND'
        )
        
        # SEARCH command
        search_parser = subparsers.add_parser(
            'search',
            help='Search for social media profiles using a real name',
            description='Search across all platforms to find profiles matching the given name'
        )
        search_parser.add_argument(
            'name',
            help='Full name to search for (e.g., "John Doe")'
        )
        search_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to search (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        search_parser.add_argument(
            '--max-usernames',
            type=int,
            default=20,
            help='Maximum number of usernames to generate and check (default: 20)'
        )
        search_parser.add_argument(
            '--max-workers',
            type=int,
            default=4,
            help='Maximum concurrent workers (default: 4)'
        )
        search_parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )
        
        # DEMO command
        demo_parser = subparsers.add_parser(
            'demo',
            help='Run a quick demo with sample data',
            description='Demonstrate the system capabilities with a sample name'
        )
        demo_parser.add_argument(
            'name',
            help='Name to use for demo (e.g., "John Doe")'
        )
        demo_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to search (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        demo_parser.add_argument(
            '--max-usernames',
            type=int,
            default=5,
            help='Maximum number of usernames to check (default: 5 for demo)'
        )
        demo_parser.add_argument(
            '--max-workers',
            type=int,
            default=4,
            help='Maximum concurrent workers (default: 4)'
        )
        demo_parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )
        
        # CHECK-USERNAME command
        check_parser = subparsers.add_parser(
            'check-username',
            help='Check if a specific username exists on platforms',
            description='Check a single username across all platforms'
        )
        check_parser.add_argument(
            'username',
            help='Username to check (e.g., "johndoe123")'
        )
        check_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to check (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        check_parser.add_argument(
            '--max-workers',
            type=int,
            default=4,
            help='Maximum concurrent workers (default: 4)'
        )
        
        # STATUS command
        status_parser = subparsers.add_parser(
            'status',
            help='Show system status and configuration',
            description='Display system information, configuration, and health status'
        )
        
        # GENERATE command
        generate_parser = subparsers.add_parser(
            'generate',
            help='Generate usernames from a real name',
            description='Show what usernames would be generated for a given name'
        )
        generate_parser.add_argument(
            'name',
            help='Full name to generate usernames for (e.g., "John Doe")'
        )
        generate_parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of usernames to generate (default: 20)'
        )
        generate_parser.add_argument(
            '--show-all',
            action='store_true',
            help='Show all generated usernames (not just first 10)'
        )
    
    def print_banner(self):
        """Print beautiful application banner"""
        print("🔍 OSINT Social Media Profile Finder - High Performance")
        print("=" * 60)
        print("Find social media profiles using real names")
        print("Powered by advanced username generation and AI detection")
        print("With logged-in session support and concurrent processing")
        print("=" * 60)
    
    def print_status(self):
        """Show system status and configuration"""
        print("📊 SYSTEM STATUS")
        print("=" * 50)
        
        # Check core components
        print("🔧 Core Components:")
        try:
            from username_generator import UsernameGenerator
            print("   ✅ Username Generator - Ready")
        except ImportError as e:
            print(f"   ❌ Username Generator - Error: {e}")
        
        try:
            from detection.bot_detector import BotDetector
            print("   ✅ Bot Detector - Ready")
        except ImportError as e:
            print(f"   ❌ Bot Detector - Error: {e}")
        
        try:
            from browser.selenium_stealth import SeleniumStealthBrowser
            print("   ✅ Selenium Stealth Browser - Ready")
        except ImportError as e:
            print(f"   ❌ Selenium Stealth Browser - Error: {e}")
        
        try:
            from scraper.cookie_manager import CookieManager
            print("   ✅ Cookie Manager - Ready")
        except ImportError as e:
            print(f"   ❌ Cookie Manager - Error: {e}")
        
        # Check browser setup
        print("\n🌐 Browser Setup:")
        try:
            from config import Config
            config = Config()
            print(f"   • Headless Mode: {config.HEADLESS}")
            print(f"   • Viewport: {config.VIEWPORT_WIDTH}x{config.VIEWPORT_HEIGHT}")
        except Exception as e:
            print(f"   ❌ Configuration Error: {e}")
        
        # Test cookie import
        print("\n🍪 Cookie Management:")
        try:
            cookie_manager = CookieManager()
            summary = cookie_manager.get_cookie_summary()
            if summary:
                print("   ✅ Cookies available:")
                for platform, count in summary.items():
                    print(f"     • {platform}: {count} cookies")
            else:
                print("   ⚠️  No cookies found - will run without logged-in sessions")
        except Exception as e:
            print(f"   ❌ Cookie Manager Error: {e}")
        
        print("\n⚡ Performance Features:")
        print("   • Concurrent processing with ThreadPoolExecutor")
        print("   • Browser connection pooling")
        print("   • Optimized wait times")
        print("   • Intelligent caching")
        
        print("\n📈 Ready for high-speed searching!")
    
    @lru_cache(maxsize=128)
    def generate_usernames_cached(self, name):
        """Generate usernames with caching for repeated requests"""
        generator = UsernameGenerator()
        first_name, last_name = name.split()[0], name.split()[1] if len(name.split()) > 1 else ""
        return generator.generate(first_name, last_name)
    
    def generate_usernames(self, name, count=20, show_all=False):
        """Generate and display usernames for a given name"""
        print(f"🔑 GENERATING USERNAMES FOR: {name}")
        print("=" * 50)
        
        try:
            usernames = self.generate_usernames_cached(name)
            
            print(f"📊 Generated {len(usernames)} total usernames")
            print(f"📋 Showing first {count} usernames:")
            print()
            
            display_count = len(usernames) if show_all else min(count, len(usernames))
            for i, username in enumerate(usernames[:display_count], 1):
                print(f"{i:3d}. {username}")
            
            if not show_all and len(usernames) > count:
                print(f"\n... and {len(usernames) - count} more usernames")
                print("Use --show-all to see all generated usernames")
            
            return usernames
            
        except Exception as e:
            print(f"❌ Error generating usernames: {e}")
            return []
    
    def run_search(self, name, platforms, max_usernames, max_workers=4, verbose=False):
        """Run a high-speed search for profiles using concurrent processing"""
        start_time = time.time()
        
        print(f"🔍 HIGH-SPEED SEARCH FOR: {name}")
        print(f"📱 Platforms: {', '.join(platforms)}")
        print(f"🔢 Max Usernames: {max_usernames}")
        print(f"⚡ Max Workers: {max_workers}")
        print("=" * 50)
        
        try:
            # Generate usernames
            if verbose:
                print("🔄 Generating usernames...")
            
            usernames = self.generate_usernames_cached(name)
            
            # Limit to requested number of usernames
            if max_usernames > 0:
                usernames = usernames[:max_usernames]
            
            if verbose:
                print(f"✅ Generated {len(usernames)} usernames")
            
            # Initialize high-performance scraper
            if verbose:
                print("🔄 Initializing high-performance scraper...")
            
            scraper = FastOSINTScraper(max_workers=max_workers)
            
            try:
                # Prepare all URLs for concurrent processing
                urls_and_platforms = []
                for username in usernames:
                    for platform in platforms:
                        url = scraper._build_url(username, platform)
                        urls_and_platforms.append((url, platform, username))
                
                if verbose:
                    print(f"🔄 Starting concurrent processing of {len(urls_and_platforms)} checks...")
                
                # Use concurrent processing for maximum speed
                results = scraper.scrape_profiles_concurrent(urls_and_platforms, max_workers)
                
                        # Generate HTML report
        print("\n📄 Generating HTML report...")
        try:
            from html_report_generator import generate_html_report
            html_path = generate_html_report(results, usernames, name)
            print(f"✅ HTML report generated: {html_path}")
        except Exception as e:
            print(f"❌ Error generating HTML report: {e}")
        
        # Display summary
        self._display_search_summary(results, name, start_time)
        
        return results
                
            finally:
                # Clean up scraper
                scraper.cleanup()
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def _display_search_summary(self, results, name, start_time):
        """Display search results summary with timing"""
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 SEARCH SUMMARY FOR: {name}")
        print("=" * 50)
        print(f"⏱️  Total Time: {duration:.2f} seconds")
        print(f"⚡ Average Speed: {len(results)/duration:.1f} checks/second")
        
        if not results:
            print("❌ No profiles found")
            return
        
        # Count real vs broken profiles
        real_profiles = [r for r in results if not r.get('is_bot_detected', True)]
        broken_profiles = [r for r in results if r.get('is_bot_detected', True)]
        
        print(f"✅ Real Profiles: {len(real_profiles)}")
        print(f"❌ Broken Profiles: {len(broken_profiles)}")
        print(f"📈 Success Rate: {len(real_profiles)/len(results)*100:.1f}%")
        
        # Show real profiles
        if real_profiles:
            print(f"\n🎯 REAL PROFILES FOUND:")
            for profile in real_profiles:
                username = profile.get('username', 'Unknown')
                platform = profile.get('platform', 'Unknown').title()
                confidence = profile.get('confidence_score', 0)
                url = profile.get('url', '')
                print(f"   • {username} on {platform} ({confidence:.1%} confidence)")
                print(f"     🔗 {url}")
        
        # Platform breakdown
        platforms = {}
        for result in results:
            platform = result.get('platform', 'unknown')
            if platform not in platforms:
                platforms[platform] = {'real': 0, 'broken': 0}
            if not result.get('is_bot_detected', True):
                platforms[platform]['real'] += 1
            else:
                platforms[platform]['broken'] += 1
        
        print(f"\n📱 PLATFORM BREAKDOWN:")
        for platform, counts in platforms.items():
            total = counts['real'] + counts['broken']
            real_rate = counts['real'] / total * 100 if total > 0 else 0
            print(f"   • {platform.title()}: {counts['real']} real, {counts['broken']} broken ({real_rate:.1f}% real)")
    
    def run_demo(self, name, platforms, max_usernames=5, max_workers=4, verbose=False):
        """Run a quick high-speed demo"""
        print(f"🚀 HIGH-SPEED DEMO FOR: {name}")
        print("=" * 50)
        print("This is a demonstration of the OSINT system capabilities.")
        print(f"Running with {max_usernames} usernames and {max_workers} workers for maximum speed...")
        print()
        
        # Run search with specified parameters
        results = self.run_search(name, platforms, max_usernames=max_usernames, max_workers=max_workers, verbose=verbose)
        
        # Generate HTML report for demo
        if results:
            print("\n📄 Generating demo HTML report...")
            try:
                from html_report_generator import generate_html_report
                from username_generator import UsernameGenerator
                
                # Generate usernames for the report
                generator = UsernameGenerator()
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_name, last_name = name_parts[0], name_parts[1]
                else:
                    first_name, last_name = name, ""
                
                usernames = generator.generate(first_name, last_name)
                if max_usernames > 0:
                    usernames = usernames[:max_usernames]
                
                html_path = generate_html_report(results, usernames, name)
                print(f"✅ Demo HTML report generated: {html_path}")
            except Exception as e:
                print(f"❌ Error generating demo HTML report: {e}")
        
        print(f"\n✨ Demo completed! Found {len([r for r in results if not r.get('is_bot_detected', True)])} real profiles.")
        print("Use 'search' command for full comprehensive search.")
    
    def check_username(self, username, platforms, max_workers=4):
        """Check a specific username across platforms with concurrent processing"""
        start_time = time.time()
        
        print(f"🔍 HIGH-SPEED CHECK FOR: {username}")
        print(f"📱 Platforms: {', '.join(platforms)}")
        print(f"⚡ Max Workers: {max_workers}")
        print("=" * 50)
        
        try:
            scraper = FastOSINTScraper(max_workers=max_workers)
            
            try:
                # Prepare URLs for concurrent processing
                urls_and_platforms = []
                for platform in platforms:
                    url = scraper._build_url(username, platform)
                    urls_and_platforms.append((url, platform, username))
                
                # Use concurrent processing
                results = scraper.scrape_profiles_concurrent(urls_and_platforms, max_workers)
                
                # Display results
                for result in results:
                    platform = result.get('platform', 'Unknown').title()
                    confidence = result.get('confidence_score', 0)
                    status = "✅ REAL" if not result.get('is_bot_detected', True) else "❌ BROKEN"
                    print(f"   {platform}: {confidence:.1%} confidence ({status})")
                    # Always show URL for both real and broken accounts
                    print(f"       🔗 {result.get('url', '')}")
                
                # Generate HTML report for username check
                if results:
                    print("\n📄 Generating username check HTML report...")
                    try:
                        from html_report_generator import generate_html_report
                        html_path = generate_html_report(results, [username], f"Username Check: {username}")
                        print(f"✅ Username check HTML report generated: {html_path}")
                    except Exception as e:
                        print(f"❌ Error generating username check HTML report: {e}")
                
                # Summary with timing
                end_time = time.time()
                duration = end_time - start_time
                real_count = len([r for r in results if not r.get('is_bot_detected', True)])
                print(f"\n📊 Summary: {real_count} real profiles out of {len(results)} checks")
                print(f"⏱️  Time: {duration:.2f} seconds")
                
                return results
                
            finally:
                scraper.cleanup()
            
        except Exception as e:
            print(f"❌ Error checking username: {e}")
            return []
    
    def run(self):
        """Main CLI runner"""
        args = self.parser.parse_args()
        
        if not args.command:
            self.print_banner()
            self.parser.print_help()
            return
        
        # Run appropriate command
        if args.command == 'status':
            self.print_status()
        
        elif args.command == 'generate':
            self.generate_usernames(args.name, args.count, args.show_all)
        
        elif args.command == 'search':
            self.run_search(args.name, args.platforms, args.max_usernames, args.max_workers, args.verbose)
        
        elif args.command == 'demo':
            self.run_demo(args.name, args.platforms, args.max_usernames, args.max_workers, args.verbose)
        
        elif args.command == 'check-username':
            self.check_username(args.username, args.platforms, args.max_workers)

def main():
    """Main entry point"""
    cli = OSINTCLI()
    cli.run()

if __name__ == "__main__":
    main()
