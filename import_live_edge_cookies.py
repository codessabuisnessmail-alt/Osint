#!/usr/bin/env python3
"""
Import cookies from Edge while it's running by copying the database first
"""

import sys
import os
import shutil
import tempfile
import sqlite3
import json
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.cookie_manager import CookieManager

def import_live_edge_cookies():
    print("🔍 Importing Live Edge Cookies")
    print("=" * 40)
    
    try:
        # Edge cookie database path (newer versions store in Network subfolder)
        edge_profile_path = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default"
        cookie_db_path = edge_profile_path / "Network" / "Cookies"
        
        if not cookie_db_path.exists():
            print(f"❌ Edge cookie database not found at: {cookie_db_path}")
            return False
        
        print(f"📂 Found Edge cookie database: {cookie_db_path}")
        
        # Create temporary copy of the database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_db_path = temp_file.name
        
        try:
            # Copy the database to temp location
            print(f"📋 Copying database to temporary location...")
            shutil.copy2(cookie_db_path, temp_db_path)
            
            # Extract cookies from temporary database
            print(f"🍪 Extracting cookies...")
            cookies = extract_cookies_from_db(temp_db_path)
            
            if not cookies:
                print(f"❌ No cookies found in database")
                return False
            
            print(f"✅ Found {len(cookies)} cookies")
            
            # Filter for social media platforms
            social_domains = [
                'facebook.com', '.facebook.com',
                'instagram.com', '.instagram.com', 
                'twitter.com', '.twitter.com',
                'linkedin.com', '.linkedin.com',
                'github.com', '.github.com'
            ]
            
            social_cookies = {}
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if any(social_domain in domain for social_domain in social_domains):
                    platform = get_platform_from_domain(domain)
                    if platform:
                        if platform not in social_cookies:
                            social_cookies[platform] = []
                        social_cookies[platform].append(cookie)
            
            print(f"\n📊 Social Media Cookies Found:")
            for platform, platform_cookies in social_cookies.items():
                print(f"   {platform}: {len(platform_cookies)} cookies")
            
            # Save cookies to our cookie manager
            if social_cookies:
                save_extracted_cookies(social_cookies)
                print(f"\n✅ Successfully imported live Edge cookies!")
                return True
            else:
                print(f"❌ No social media cookies found")
                return False
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_db_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error importing cookies: {e}")
        return False

def extract_cookies_from_db(db_path):
    """Extract cookies from Chrome/Edge SQLite database"""
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

def get_platform_from_domain(domain):
    """Get platform name from domain"""
    domain = domain.lower().lstrip('.')
    if 'facebook' in domain:
        return 'facebook'
    elif 'instagram' in domain:
        return 'instagram'
    elif 'twitter' in domain or 'x.com' in domain:
        return 'twitter'
    elif 'linkedin' in domain:
        return 'linkedin'
    elif 'github' in domain:
        return 'github'
    return None

def save_extracted_cookies(social_cookies):
    """Save extracted cookies to our cookie manager format"""
    try:
        cookie_dir = Path("cookies")
        cookie_dir.mkdir(exist_ok=True)
        
        filename = f"edge_live_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = cookie_dir / filename
        
        # Organize cookies by domain for cookie manager format
        organized_cookies = {}
        for platform, platform_cookies in social_cookies.items():
            for cookie in platform_cookies:
                domain = cookie['domain']
                if domain not in organized_cookies:
                    organized_cookies[domain] = []
                organized_cookies[domain].append(cookie)
        
        cookie_data = {
            'browser_type': 'edge',
            'profile_name': 'live_import',
            'import_timestamp': datetime.now().isoformat(),
            'cookies': organized_cookies
        }
        
        with open(filepath, 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        print(f"💾 Saved cookies to: {filepath}")
        
    except Exception as e:
        print(f"Error saving cookies: {e}")

if __name__ == "__main__":
    import_live_edge_cookies()
