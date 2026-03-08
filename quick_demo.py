#!/usr/bin/env python3
"""
Quick demo of the name lookup system - uses actual system with fewer usernames
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from username_generator import UsernameGenerator
from detection.bot_detector import BotDetector
from scraper.osint_scraper import OSINTScraper
import json

def quick_demo():
    print("🚀 Quick OSINT Name Lookup Demo - Abigail Baugh")
    print("=" * 50)
    print("📋 Enhanced 404 Detection: Heavy penalties for broken profiles ✅")
    
    # Test username generation
    print("\n1. Username Generation:")
    generator = UsernameGenerator()
    usernames = generator.generate("Abigail", "Baugh")
    print(f"   Generated {len(usernames)} usernames for 'Abigail Baugh':")
    
    # Take only first 5 usernames for quick demo
    demo_usernames = usernames[:5]
    for i, username in enumerate(demo_usernames, 1):
        print(f"   {i}. {username}")
    
    # Test bot detection with sample HTML
    print("\n2. Account Validation (Sample HTML):")
    detector = BotDetector()
    
    # Real account HTML
    real_html = """
    <html><head><title>Abigail Baugh - GitHub</title></head>
    <body><h1>Abigail Baugh</h1><div>repositories</div><div>followers</div><div>bio</div></body>
    </html>
    """
    
    # Broken account HTML  
    broken_html = """
    <html><head><title>Sorry, this page isn't available</title></head>
    <body><h1>User not found</h1><div>page not found</div></body>
    </html>
    """
    
    real_result = detector.analyze_page(real_html, "https://github.com/abigailbaugh", 200, "github")
    broken_result = detector.analyze_page(broken_html, "https://github.com/nonexistent", 404, "github")
    
    print(f"   Real account: {real_result['confidence_score']:.3f} confidence ({'✅ REAL' if not real_result['is_bot_detected'] else '❌ BROKEN'})")
    print(f"   Broken account: {broken_result['confidence_score']:.3f} confidence ({'✅ REAL' if not broken_result['is_bot_detected'] else '❌ BROKEN'})")
    
    # Run actual system with demo usernames
    print("\n3. Running Actual System (First 5 usernames):")
    try:
        scraper = OSINTScraper()
        results = []
        
        for username in demo_usernames:
            print(f"   Checking: {username}")
            for platform in ['twitter', 'github', 'instagram', 'linkedin']:
                try:
                    url = scraper._build_url(username, platform)
                    result = scraper.scrape_profile(url, platform, username)
                    if result:
                        results.append(result)
                        status = "✅ REAL" if not result.get('is_bot_detected', True) else "❌ BROKEN"
                        confidence = result.get('confidence_score', 0)
                        print(f"     {platform.title()}: {confidence:.1%} confidence ({status})")
                        # Always show URL for both real and broken accounts
                        print(f"         🔗 {result.get('url', '')}")
                except Exception as e:
                    print(f"     {platform.title()}: Error - {str(e)[:50]}...")
        
        # Show summary
        real_count = len([r for r in results if not r.get('is_bot_detected', True)])
        total_checks = len(results)
        print(f"\n📊 Summary: {real_count} real profiles out of {total_checks} checks")
        
    except Exception as e:
        print(f"   ❌ System error: {e}")
        print("   (This is expected if browser setup isn't configured)")
    
    print("\n4. Why it's slow:")
    print("   • Browser startup: ~10-15 seconds")
    print("   • Network requests: ~5-10 seconds per platform")
    print("   • Anti-detection measures: ~2-5 seconds")
    print("   • Total per search: ~30-60 seconds")
    
    print("\n5. Speed improvements possible:")
    print("   • Use headless mode")
    print("   • Parallel platform searches")
    print("   • Cache results")
    print("   • Use API endpoints where available")
    
    print("\n6. Try the CLI tools with explicit platform selection:")
    print("   python osint_cli.py search \"Abigail Baugh\" --platforms twitter github instagram linkedin")
    print("   python name_lookup_cli.py --name \"Abigail\" \"Baugh\" --platforms twitter,github,instagram")

if __name__ == "__main__":
    quick_demo()
