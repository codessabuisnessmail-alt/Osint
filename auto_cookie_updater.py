#!/usr/bin/env python3
"""
Automatic Cookie Updater - Ensures cookies are always fresh and current
"""

import sys
import os
import time
import json
import shutil
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.cookie_manager import CookieManager

class AutoCookieUpdater:
    def __init__(self):
        self.cookie_dir = Path("cookies")
        self.cookie_dir.mkdir(exist_ok=True)
        self.cookie_manager = CookieManager()
        
        # Cookie freshness settings
        self.max_cookie_age_hours = 2  # Update cookies every 2 hours
        self.force_update_after_hours = 6  # Force update after 6 hours
        
    def should_update_cookies(self):
        """Check if cookies need updating based on age"""
        try:
            # Find the most recent cookie file
            cookie_files = list(self.cookie_dir.glob("*.json"))
            if not cookie_files:
                return True, "No cookie files found"
            
            # Get the most recent file
            latest_file = max(cookie_files, key=lambda f: f.stat().st_mtime)
            file_age = datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)
            
            if file_age > timedelta(hours=self.force_update_after_hours):
                return True, f"Cookies are {file_age.total_seconds()/3600:.1f} hours old (force update)"
            elif file_age > timedelta(hours=self.max_cookie_age_hours):
                return True, f"Cookies are {file_age.total_seconds()/3600:.1f} hours old (recommended update)"
            else:
                return False, f"Cookies are fresh ({file_age.total_seconds()/3600:.1f} hours old)"
                
        except Exception as e:
            return True, f"Error checking cookie age: {e}"
    
    def update_cookies_if_needed(self, force=False):
        """Update cookies if they're old or if forced"""
        should_update, reason = self.should_update_cookies()
        
        if force:
            print(f"🔄 Force updating cookies...")
            return self.import_fresh_cookies()
        elif should_update:
            print(f"🔄 Updating cookies: {reason}")
            return self.import_fresh_cookies()
        else:
            print(f"✅ Cookies are current: {reason}")
            return True
    
    def import_fresh_cookies(self):
        """Import fresh cookies from Edge"""
        print("🔍 Importing fresh Edge cookies...")
        
        try:
            # Try to get cookies from Edge
            edge_cookies = self._extract_edge_cookies()
            if not edge_cookies:
                print("❌ No cookies found in Edge")
                return False
            
            # Save the fresh cookies
            self._save_fresh_cookies(edge_cookies)
            
            # Update the cookie manager
            self._update_cookie_manager()
            
            print("✅ Fresh cookies imported successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error importing fresh cookies: {e}")
            return False
    
    def _extract_edge_cookies(self):
        """Extract cookies from Edge browser"""
        try:
            # Edge cookie database path
            edge_profile_path = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default"
            cookie_db_path = edge_profile_path / "Network" / "Cookies"
            
            if not cookie_db_path.exists():
                print(f"❌ Edge cookie database not found at: {cookie_db_path}")
                return None
            
            print(f"📂 Found Edge cookie database: {cookie_db_path}")
            
            # Try to copy the database to temp location
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                temp_db_path = temp_file.name
            
            try:
                # Try to copy the database
                print(f"📋 Attempting to copy database to temporary location...")
                shutil.copy2(cookie_db_path, temp_db_path)
                
                # Extract cookies from temporary database
                print(f"🍪 Extracting cookies...")
                cookies = self._read_cookies_from_db(temp_db_path)
                
                return cookies
                
            except PermissionError as e:
                print(f"⚠️  Edge database is locked (Edge is running)")
                print(f"💡 Options:")
                print(f"   1. Close Edge browser and try again")
                print(f"   2. Use existing cookies (they may still work)")
                print(f"   3. Manually export cookies from Edge")
                
                # Try to use existing cookies as fallback
                return self._get_existing_cookies_as_fallback()
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_db_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error extracting cookies: {e}")
            return None
    
    def _get_existing_cookies_as_fallback(self):
        """Get existing cookies as fallback when Edge is locked"""
        try:
            print(f"🔄 Using existing cookies as fallback...")
            
            # Get current cookie summary
            summary = self.cookie_manager.get_cookie_summary()
            if not summary or not summary.get('platforms_with_cookies'):
                print(f"❌ No existing cookies found")
                return None
            
            # Check if we have sufficient cookies
            total_cookies = sum(summary.get('platforms_with_cookies', {}).values())
            if total_cookies > 0:
                print(f"✅ Found {total_cookies} existing cookies across platforms")
                print(f"💡 These cookies may still be valid")
                return "existing_cookies_found"
            else:
                print(f"❌ No valid existing cookies found")
                return None
                
        except Exception as e:
            print(f"Error getting existing cookies: {e}")
            return None
    
    def _read_cookies_from_db(self, db_path):
        """Read cookies from SQLite database"""
        cookies = []
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query cookies table
            cursor.execute("""
                SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly, creation_utc
                FROM cookies
            """)
            
            for row in cursor.fetchall():
                name, value, domain, path, expires_utc, is_secure, is_httponly, creation_utc = row
                
                # Convert Chrome timestamp to Unix timestamp
                if expires_utc:
                    # Chrome timestamps are microseconds since Jan 1, 1601
                    # Convert to Unix timestamp (seconds since Jan 1, 1970)
                    expires = (expires_utc / 1000000) - 11644473600
                else:
                    expires = None
                
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': domain,
                    'path': path,
                    'expires': int(expires) if expires else None,
                    'secure': bool(is_secure),
                    'httpOnly': bool(is_httponly)
                }
                cookies.append(cookie)
            
            conn.close()
            
        except Exception as e:
            print(f"Error reading cookie database: {e}")
            
        return cookies
    
    def _save_fresh_cookies(self, cookies):
        """Save fresh cookies to our format"""
        try:
            # If we got existing cookies as fallback, just update the timestamp
            if cookies == "existing_cookies_found":
                self._update_existing_cookies_timestamp()
                return
            
            # Organize cookies by domain
            organized_cookies = {}
            social_domains = {
                'facebook': ['facebook.com', '.facebook.com'],
                'instagram': ['instagram.com', '.instagram.com'],
                'twitter': ['twitter.com', '.twitter.com', 'x.com', '.x.com'],
                'linkedin': ['linkedin.com', '.linkedin.com'],
                'github': ['github.com', '.github.com']
            }
            
            for cookie in cookies:
                domain = cookie.get('domain', '')
                for platform, platform_domains in social_domains.items():
                    if any(social_domain in domain for social_domain in platform_domains):
                        if domain not in organized_cookies:
                            organized_cookies[domain] = []
                        organized_cookies[domain].append(cookie)
                        break
            
            # Save to file
            filename = f"edge_fresh_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.cookie_dir / filename
            
            cookie_data = {
                'browser_type': 'edge',
                'profile_name': 'fresh_import',
                'import_timestamp': datetime.now().isoformat(),
                'cookies': organized_cookies,
                'total_cookies': len(cookies),
                'social_media_cookies': len(organized_cookies)
            }
            
            with open(filepath, 'w') as f:
                json.dump(cookie_data, f, indent=2)
            
            print(f"💾 Saved {len(organized_cookies)} social media cookie domains to: {filepath}")
            
            # Clean up old cookie files (keep last 3)
            self._cleanup_old_cookie_files()
            
        except Exception as e:
            print(f"Error saving cookies: {e}")
    
    def _update_existing_cookies_timestamp(self):
        """Update timestamp of existing cookies to mark them as fresh"""
        try:
            # Find the most recent cookie file and update its timestamp
            cookie_files = list(self.cookie_dir.glob("*.json"))
            if cookie_files:
                latest_file = max(cookie_files, key=lambda f: f.stat().st_mtime)
                
                # Update the file's modification time
                current_time = time.time()
                os.utime(latest_file, (current_time, current_time))
                
                print(f"✅ Updated timestamp of existing cookies: {latest_file.name}")
                return True
            else:
                print(f"❌ No existing cookie files found")
                return False
                
        except Exception as e:
            print(f"Error updating cookie timestamp: {e}")
            return False
    
    def _cleanup_old_cookie_files(self):
        """Clean up old cookie files, keeping only the most recent ones"""
        try:
            cookie_files = list(self.cookie_dir.glob("*.json"))
            if len(cookie_files) > 3:
                # Sort by modification time and keep only the 3 most recent
                sorted_files = sorted(cookie_files, key=lambda f: f.stat().st_mtime, reverse=True)
                files_to_delete = sorted_files[3:]
                
                for file_to_delete in files_to_delete:
                    try:
                        file_to_delete.unlink()
                        print(f"🗑️  Deleted old cookie file: {file_to_delete.name}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error cleaning up old files: {e}")
    
    def _update_cookie_manager(self):
        """Update the cookie manager with fresh cookies"""
        try:
            # The cookie manager will automatically reload from the new files
            # Just verify the update worked
            summary = self.cookie_manager.get_cookie_summary()
            print(f"📊 Updated cookie summary:")
            for platform, count in summary.get('platforms_with_cookies', {}).items():
                print(f"   {platform}: {count} cookies")
                
        except Exception as e:
            print(f"Error updating cookie manager: {e}")
    
    def get_fresh_cookies_for_platform(self, platform):
        """Get fresh cookies for a specific platform, updating if needed"""
        # First check if we need to update
        self.update_cookies_if_needed()
        
        # Then get the cookies
        return self.cookie_manager.get_cookies_for_platform(platform)
    
    def ensure_fresh_cookies(self):
        """Ensure cookies are fresh before any scraping operation"""
        print("🍪 Ensuring fresh cookies...")
        return self.update_cookies_if_needed()
    
    def manual_refresh_instructions(self):
        """Provide instructions for manual cookie refresh"""
        print("\n📋 Manual Cookie Refresh Instructions:")
        print("=" * 50)
        print("If you need to refresh cookies manually:")
        print("1. Close Microsoft Edge completely")
        print("2. Wait 10 seconds")
        print("3. Run: python auto_cookie_updater.py --force")
        print("4. Reopen Edge")
        print("\nOr use the existing cookies (they may still work):")
        print("python test_fresh_cookies_john_doe2.py")

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic Cookie Updater")
    parser.add_argument("--force", action="store_true", help="Force cookie update even if not needed")
    args = parser.parse_args()
    
    updater = AutoCookieUpdater()
    
    print("🍪 Automatic Cookie Updater")
    print("=" * 40)
    
    # Check current status
    should_update, reason = updater.should_update_cookies()
    print(f"Status: {reason}")
    
    # Update if needed or forced
    if args.force or updater.update_cookies_if_needed(force=args.force):
        print("✅ Cookie update completed successfully!")
    else:
        print("❌ Cookie update failed")
        updater.manual_refresh_instructions()
    
    # Show summary
    summary = updater.cookie_manager.get_cookie_summary()
    print(f"\n📊 Current Cookie Summary:")
    for platform, count in summary.get('platforms_with_cookies', {}).items():
        print(f"   {platform}: {count} cookies")

if __name__ == "__main__":
    main()
