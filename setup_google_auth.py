#!/usr/bin/env python3
"""
Simple Google Sign-In Setup for OSINT Tool
==========================================

This script helps you set up Google Sign-In authentication for social media platforms.
It will guide you through the process and save your credentials securely.
"""

import sys
import os
import json
import time
from pathlib import Path
from getpass import getpass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser.selenium_stealth import SeleniumStealthBrowser
from scraper.cookie_manager import CookieManager

class GoogleAuthSetup:
    def __init__(self):
        self.auth_config_file = Path("google_auth_config.json")
        self.auth_config = self._load_config()
        self.cookie_manager = CookieManager()
    
    def _load_config(self):
        """Load existing configuration"""
        if self.auth_config_file.exists():
            try:
                with open(self.auth_config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_config(self):
        """Save configuration"""
        try:
            with open(self.auth_config_file, 'w') as f:
                json.dump(self.auth_config, f, indent=2)
            print("✅ Configuration saved to google_auth_config.json")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def setup_credentials(self):
        """Interactive setup for Google credentials"""
        print("🔐 Google Sign-In Setup for OSINT Tool")
        print("=" * 50)
        print("This will help you set up Google Sign-In for social media platforms.")
        print("Your credentials will be saved locally for future use.")
        print()
        
        # Get Google credentials
        print("📝 Enter your Google account credentials:")
        email = input("Google Email: ").strip()
        password = getpass("Google Password: ")
        
        if not email or not password:
            print("❌ Email and password are required")
            return
        
        # Save credentials
        self.auth_config['google'] = {
            'email': email,
            'password': password
        }
        
        # Ask which platforms to set up
        platforms = ['facebook', 'twitter', 'instagram', 'linkedin']
        selected_platforms = []
        
        print(f"\n📱 Select platforms to set up Google Sign-In:")
        for i, platform in enumerate(platforms, 1):
            use_google = input(f"Use Google Sign-In for {platform.title()}? (y/n): ").lower().startswith('y')
            if use_google:
                selected_platforms.append(platform)
        
        if not selected_platforms:
            print("❌ No platforms selected")
            return
        
        # Save platform preferences
        self.auth_config['platforms'] = selected_platforms
        self._save_config()
        
        print(f"\n✅ Setup complete! Selected platforms: {', '.join(selected_platforms)}")
        print("You can now run authentication tests or use the OSINT tool.")
    
    def test_facebook_google_auth(self):
        """Test Google Sign-In for Facebook"""
        print("🧪 Testing Google Sign-In for Facebook...")
        
        if 'google' not in self.auth_config:
            print("❌ No Google credentials found. Run setup first.")
            return
        
        credentials = self.auth_config['google']
        
        # Start browser
        browser = SeleniumStealthBrowser(headless=False)
        browser.start()
        
        try:
            # Navigate to Facebook login
            print("🌐 Navigating to Facebook login...")
            browser.navigate_to("https://www.facebook.com/login")
            time.sleep(3)
            
            # Look for Google Sign-In button
            print("🔍 Looking for Google Sign-In button...")
            
            # Try different selectors for Google button
            google_selectors = [
                "//button[contains(text(), 'Continue with Google')]",
                "//button[contains(text(), 'Sign in with Google')]",
                "//div[contains(@class, 'google')]//button",
                "//button[contains(@class, 'google')]"
            ]
            
            google_button = None
            for selector in google_selectors:
                try:
                    google_button = browser.driver.find_element_by_xpath(selector)
                    if google_button:
                        print(f"✅ Found Google button with selector: {selector}")
                        break
                except:
                    continue
            
            if not google_button:
                print("❌ Google Sign-In button not found")
                print("You may need to manually click 'Continue with Google'")
                input("Press Enter after clicking the Google button...")
            else:
                google_button.click()
                print("✅ Clicked Google Sign-In button")
                time.sleep(3)
            
            # Handle Google login
            print("🔐 Handling Google login...")
            success = self._handle_google_login(browser, credentials['email'], credentials['password'])
            
            if success:
                print("✅ Google Sign-In successful!")
                
                # Save cookies
                self._save_platform_cookies(browser, 'facebook')
                
                # Test profile access
                print("🧪 Testing profile access...")
                browser.navigate_to("https://www.facebook.com/zuck")
                time.sleep(3)
                
                current_url = browser.get_page_url()
                if "login" not in current_url and "checkpoint" not in current_url:
                    print("✅ Successfully accessed Facebook profile!")
                else:
                    print("❌ Still redirected to login/checkpoint")
            else:
                print("❌ Google Sign-In failed")
                
        except Exception as e:
            print(f"❌ Error during Facebook Google Sign-In: {e}")
        finally:
            browser.close()
    
    def _handle_google_login(self, browser, email, password):
        """Handle Google login process"""
        try:
            # Wait for Google login page
            print("⏳ Waiting for Google login page...")
            time.sleep(5)
            
            # Check if we're on Google login page
            current_url = browser.get_page_url()
            if "accounts.google.com" not in current_url:
                print("⚠️  Not on Google login page, may need manual intervention")
                return False
            
            # Enter email
            print("📧 Entering email...")
            try:
                email_field = browser.driver.find_element_by_name("identifier")
                email_field.clear()
                email_field.send_keys(email)
                
                # Click Next
                next_button = browser.driver.find_element_by_xpath("//button[contains(text(), 'Next')]")
                next_button.click()
                time.sleep(3)
            except Exception as e:
                print(f"❌ Error entering email: {e}")
                return False
            
            # Enter password
            print("🔑 Entering password...")
            try:
                password_field = browser.driver.find_element_by_name("password")
                password_field.clear()
                password_field.send_keys(password)
                
                # Click Next
                next_button = browser.driver.find_element_by_xpath("//button[contains(text(), 'Next') or contains(text(), 'Sign in')]")
                next_button.click()
                time.sleep(5)
            except Exception as e:
                print(f"❌ Error entering password: {e}")
                return False
            
            # Handle 2FA if needed
            if self._check_for_2fa(browser):
                print("📱 2FA detected! Please complete verification manually.")
                print("⏰ You have 60 seconds to complete...")
                
                start_time = time.time()
                while time.time() - start_time < 60:
                    current_url = browser.get_page_url()
                    if "accounts.google.com" not in current_url:
                        print("✅ 2FA completed successfully!")
                        return True
                    time.sleep(2)
                
                print("⏰ Timeout waiting for 2FA completion")
                return False
            
            # Check if login successful
            time.sleep(3)
            current_url = browser.get_page_url()
            if "accounts.google.com" not in current_url:
                print("✅ Google login successful!")
                return True
            else:
                print("❌ Still on Google login page")
                return False
                
        except Exception as e:
            print(f"❌ Error in Google login: {e}")
            return False
    
    def _check_for_2fa(self, browser):
        """Check if 2FA is required"""
        try:
            page_source = browser.get_page_source().lower()
            return any(indicator in page_source for indicator in [
                "verification code", "2-step verification", "security code",
                "enter the code", "verification", "authenticator"
            ])
        except:
            return False
    
    def _save_platform_cookies(self, browser, platform):
        """Save cookies for a platform"""
        try:
            # Get cookies from browser
            selenium_cookies = browser.driver.get_cookies()
            
            # Convert to our format
            cookies = []
            for cookie in selenium_cookies:
                cookies.append({
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie.get('path', '/'),
                    'expires': cookie.get('expiry'),
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False)
                })
            
            # Save to cookie manager
            self.cookie_manager._save_cookies('google_auth', f'{platform}_google', {platform: cookies})
            
            print(f"💾 Saved {len(cookies)} cookies for {platform}")
            
        except Exception as e:
            print(f"❌ Error saving cookies: {e}")

def main():
    """Main function"""
    setup = GoogleAuthSetup()
    
    print("🔐 Google Sign-In Setup")
    print("=" * 30)
    print("1. Setup Google credentials")
    print("2. Test Facebook Google Sign-In")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        setup.setup_credentials()
    elif choice == "2":
        setup.test_facebook_google_auth()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
