#!/usr/bin/env python3
"""
Quick Demo with HTML Report Generation
=====================================

This script demonstrates the OSINT tool with automatic HTML report generation.
Generates HTML reports for OSINT search results.
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from html_report_generator import generate_html_report
from username_generator import UsernameGenerator
from detection.bot_detector import BotDetector
from browser.selenium_stealth import SeleniumStealthBrowser
from scraper.cookie_manager import CookieManager
from config import Config


def quick_demo_with_html(name="John Doe", platforms=None, max_usernames=8):
    """
    Run a quick demo and generate an HTML report.
    
    Args:
        name: Name to search for
        platforms: List of platforms to check
        max_usernames: Maximum number of usernames to check
    """
    if platforms is None:
        platforms = ['facebook', 'twitter', 'instagram', 'github', 'linkedin']
    
    print(f"🚀 Quick Demo for: {name}")
    print(f"📱 Platforms: {', '.join(platforms)}")
    print(f"🔢 Max Usernames: {max_usernames}")
    print("=" * 50)
    
    try:
        # Initialize components
        config = Config()
        bot_detector = BotDetector()
        cookie_manager = CookieManager()
        username_generator = UsernameGenerator()
        
        # Import cookies
        print("🍪 Importing cookies...")
        edge_cookies = cookie_manager.import_cookies_from_browser('edge', 'default')
        if edge_cookies:
            total_cookies = sum(len(cookies) for cookies in edge_cookies.values())
            print(f"✅ Imported {total_cookies} cookies from Edge")
        
        # Generate usernames
        print("🔄 Generating usernames...")
        # Split name into first and last
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name, last_name = name_parts[0], name_parts[1]
        else:
            first_name, last_name = name, ""
        
        usernames = username_generator.generate(first_name, last_name)
        if max_usernames > 0:
            usernames = usernames[:max_usernames]
        print(f"✅ Generated {len(usernames)} usernames")
        
        # Initialize browser
        print("🌐 Initializing browser...")
        browser = SeleniumStealthBrowser(
            headless=config.HEADLESS,
            viewport_width=config.VIEWPORT_WIDTH,
            viewport_height=config.VIEWPORT_HEIGHT
        )
        browser.start()  # Start the browser session
        
        # Inject cookies
        if edge_cookies:
            print("🍪 Injecting cookies...")
            browser.inject_cookies(edge_cookies)
        
        results = []
        
        # Check each username on each platform
        total_checks = len(usernames) * len(platforms)
        current_check = 0
        
        for username in usernames:
            for platform in platforms:
                current_check += 1
                print(f"🔍 [{current_check}/{total_checks}] Checking {username} on {platform}...")
                
                try:
                    # Build URL
                    if platform == 'facebook':
                        url = f"https://www.facebook.com/{username}"
                    elif platform == 'twitter':
                        url = f"https://twitter.com/{username}"
                    elif platform == 'instagram':
                        url = f"https://www.instagram.com/{username}"
                    elif platform == 'github':
                        url = f"https://github.com/{username}"
                    elif platform == 'linkedin':
                        url = f"https://www.linkedin.com/in/{username}"
                    else:
                        continue
                    
                    # Navigate to URL
                    browser.navigate_to(url)
                    
                    # Wait for page to load
                    browser.wait_for_dom_stable(platform)
                    
                    # Force JavaScript rendering
                    browser.force_js_rendering(platform)
                    
                    # Get page content
                    html_content = browser.get_page_source()
                    current_url = browser.get_page_url()
                    page_title = browser.get_page_title()
                    
                    # Analyze page
                    analysis_result = bot_detector.analyze_page(
                        html_content, current_url, 200, platform
                    )
                    
                    # Create result
                    result = {
                        'username': username,
                        'platform': platform,
                        'url': url,
                        'current_url': current_url,
                        'page_title': page_title,
                        'is_bot_detected': analysis_result.get('is_bot_detected', True),
                        'confidence_score': analysis_result.get('confidence_score', 0),
                        'analysis_details': analysis_result
                    }
                    
                    results.append(result)
                    
                    # Show result
                    status = "✅ REAL" if not result['is_bot_detected'] else "❌ BROKEN"
                    confidence = result['confidence_score'] * 100
                    print(f"   {status} ({confidence:.1f}% confidence)")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    results.append({
                        'username': username,
                        'platform': platform,
                        'url': url,
                        'is_bot_detected': True,
                        'confidence_score': 0,
                        'error': str(e)
                    })
        
        # Clean up browser
        browser.close()
        
        # Generate HTML report
        print("\n📄 Generating HTML report...")
        try:
            html_path = generate_html_report(results, usernames, name)
            print(f"✅ HTML report generated: {html_path}")
        except Exception as e:
            print(f"❌ Error generating HTML report: {e}")
            # Fallback to simple report
            try:
                from html_report_generator import generate_simple_html_report
                html_path = generate_simple_html_report(results, name)
                print(f"✅ Simple HTML report generated: {html_path}")
            except Exception as e2:
                print(f"❌ Error generating simple HTML report: {e2}")
        
        # Display summary
        print(f"\n📊 SUMMARY FOR: {name}")
        print("=" * 50)
        
        real_profiles = [r for r in results if not r.get('is_bot_detected', True)]
        broken_profiles = [r for r in results if r.get('is_bot_detected', True)]
        
        print(f"✅ Real Profiles: {len(real_profiles)}")
        print(f"❌ Broken Profiles: {len(broken_profiles)}")
        print(f"📈 Success Rate: {len(real_profiles)/len(results)*100:.1f}%")
        
        # Platform breakdown
        platforms_stats = {}
        for result in results:
            platform = result.get('platform', 'unknown')
            if platform not in platforms_stats:
                platforms_stats[platform] = {'real': 0, 'broken': 0}
            if not result.get('is_bot_detected', True):
                platforms_stats[platform]['real'] += 1
            else:
                platforms_stats[platform]['broken'] += 1
        
        print(f"\n📱 PLATFORM BREAKDOWN:")
        for platform, stats in platforms_stats.items():
            total = stats['real'] + stats['broken']
            real_rate = stats['real'] / total * 100 if total > 0 else 0
            print(f"   • {platform.title()}: {stats['real']} real, {stats['broken']} broken ({real_rate:.1f}% real)")
        
        return results
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        return []


if __name__ == "__main__":
    # Run demo with default settings
    results = quick_demo_with_html("John Doe", max_usernames=8)
    
    if results:
        print(f"\n✨ Demo completed! Found {len([r for r in results if not r.get('is_bot_detected', True)])} real profiles.")
        print("Check the generated HTML file for detailed results.")
