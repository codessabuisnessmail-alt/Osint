#!/usr/bin/env python3
"""
Debug Cookie Injection - Test if cookies are being properly injected
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser.selenium_stealth import SeleniumStealthBrowser
from scraper.cookie_manager import CookieManager
from auto_cookie_updater import AutoCookieUpdater

def debug_cookie_injection():
    print("🔍 DEBUGGING COOKIE INJECTION")
    print("=" * 50)
    
    # Initialize components
    cookie_manager = CookieManager()
    cookie_updater = AutoCookieUpdater()
    
    # Ensure fresh cookies
    print("🍪 Ensuring fresh cookies...")
    cookie_updater.ensure_fresh_cookies()
    
    # Get cookie summary
    print("\n📊 Cookie Summary:")
    summary = cookie_manager.get_cookie_summary()
    if summary:
        for platform, count in summary.items():
            print(f"   • {platform}: {count} cookies")
    else:
        print("   ❌ No cookies found!")
        return
    
    # Test with browser
    print("\n🌐 Testing with browser...")
    browser = SeleniumStealthBrowser(headless=False)  # Use visible browser for debugging
    
    try:
        browser.start()
        print("✅ Browser started")
        
        # Test Facebook cookies
        print("\n📘 Testing Facebook cookies...")
        facebook_cookies = cookie_manager.get_cookies_for_platform('facebook')
        print(f"   Found {len(facebook_cookies)} Facebook cookies")
        
        if facebook_cookies:
            # Navigate to Facebook first
            print("   Navigating to Facebook...")
            browser.navigate_to("https://www.facebook.com")
            
            # Inject cookies
            print("   Injecting cookies...")
            success = cookie_manager.inject_cookies_to_selenium(browser, 'facebook')
            print(f"   Cookie injection result: {success}")
            
            # Check if we're logged in
            print("   Checking login status...")
            browser.navigate_to("https://www.facebook.com")
            time.sleep(3)
            
            page_source = browser.get_page_source()
            if "login" in page_source.lower() or "sign up" in page_source.lower():
                print("   ❌ Still showing login page")
            else:
                print("   ✅ Appears to be logged in!")
            
            # Test with a known profile
            print("\n   Testing with known profile...")
            browser.navigate_to("https://www.facebook.com/zuck")
            time.sleep(3)
            
            current_url = browser.get_page_url()
            print(f"   Current URL: {current_url}")
            
            if "login" in current_url or "checkpoint" in current_url:
                print("   ❌ Redirected to login/checkpoint")
            else:
                print("   ✅ Successfully accessed profile!")
        
        # Test Twitter cookies
        print("\n🐦 Testing Twitter cookies...")
        twitter_cookies = cookie_manager.get_cookies_for_platform('twitter')
        print(f"   Found {len(twitter_cookies)} Twitter cookies")
        
        if twitter_cookies:
            # Navigate to Twitter first
            print("   Navigating to Twitter...")
            browser.navigate_to("https://twitter.com")
            
            # Inject cookies
            print("   Injecting cookies...")
            success = cookie_manager.inject_cookies_to_selenium(browser, 'twitter')
            print(f"   Cookie injection result: {success}")
            
            # Check if we're logged in
            print("   Checking login status...")
            browser.navigate_to("https://twitter.com")
            time.sleep(3)
            
            page_source = browser.get_page_source()
            if "log in" in page_source.lower() or "sign up" in page_source.lower():
                print("   ❌ Still showing login page")
            else:
                print("   ✅ Appears to be logged in!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    finally:
        browser.close()
        print("\n✅ Browser closed")

if __name__ == "__main__":
    import time
    debug_cookie_injection()
