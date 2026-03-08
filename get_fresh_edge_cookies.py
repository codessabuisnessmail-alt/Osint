#!/usr/bin/env python3
"""
Get fresh Edge cookies by temporarily closing Edge
"""

import sys
import os
import subprocess
import time
import psutil
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_fresh_edge_cookies():
    print("🔍 Getting Fresh Edge Cookies")
    print("=" * 40)
    
    # Check if Edge is running
    edge_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'msedge' in proc.info['name'].lower():
                edge_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if edge_processes:
        print(f"🌐 Found {len(edge_processes)} Edge processes running")
        print("⚠️  To import fresh cookies, we need to temporarily close Edge")
        print("   This is because Edge locks the cookie database while running")
        
        response = input("\n❓ Do you want to close Edge temporarily to import fresh cookies? (y/n): ")
        
        if response.lower() not in ['y', 'yes']:
            print("❌ Skipping cookie import")
            return False
        
        print("🔄 Closing Edge processes...")
        for proc in edge_processes:
            try:
                proc.terminate()
            except:
                pass
        
        # Wait for processes to close
        time.sleep(3)
        
        # Force kill any remaining processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'msedge' in proc.info['name'].lower():
                    proc.kill()
            except:
                pass
        
        time.sleep(2)
        print("✅ Edge processes closed")
    
    # Now import cookies
    try:
        from import_live_edge_cookies import import_live_edge_cookies
        success = import_live_edge_cookies()
        
        if success:
            print("\n✅ Successfully imported fresh Edge cookies!")
            
            # Restart Edge
            print("🔄 Restarting Edge...")
            edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            if not os.path.exists(edge_path):
                edge_path = "msedge"  # Try system PATH
            
            try:
                subprocess.Popen([edge_path])
                print("✅ Edge restarted")
            except:
                print("⚠️  Please manually restart Edge")
            
            return True
        else:
            print("❌ Failed to import cookies")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def alternative_cookie_method():
    """Alternative method: Use our existing cookies but test them better"""
    print("\n🔍 Alternative: Testing Existing Cookies")
    print("=" * 40)
    
    from scraper.cookie_manager import CookieManager
    
    cm = CookieManager()
    facebook_cookies = cm.get_cookies_for_platform('facebook')
    
    if not facebook_cookies:
        print("❌ No Facebook cookies found")
        return False
    
    print(f"✅ Found {len(facebook_cookies)} Facebook cookies")
    
    # Check cookie details
    auth_cookies = []
    for cookie in facebook_cookies:
        name = cookie.get('name', '')
        if any(auth_name in name.lower() for auth_name in ['c_user', 'xs', 'datr', 'sb']):
            auth_cookies.append(cookie)
    
    print(f"🔑 Found {len(auth_cookies)} authentication cookies")
    
    if len(auth_cookies) >= 2:
        print("✅ We have sufficient authentication cookies")
        print("💡 The issue might be in how we're using them")
        return True
    else:
        print("⚠️  We may not have sufficient authentication cookies")
        return False

if __name__ == "__main__":
    print("🍪 Edge Cookie Management")
    print("=" * 50)
    
    # Try alternative first (less disruptive)
    if alternative_cookie_method():
        print("\n💡 Recommendation: Try using existing cookies with improved injection")
    else:
        print("\n💡 Recommendation: Get fresh cookies")
        get_fresh_edge_cookies()
