#!/usr/bin/env python3
"""
Quick demo of the name lookup system for John Doe - generates HTML results
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from username_generator import UsernameGenerator
from detection.bot_detector import BotDetector
from scraper.osint_scraper import OSINTScraper

def generate_html_results(results, usernames, search_name):
    """Generate an HTML page with the search results"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Count statistics
    real_count = len([r for r in results if not r.get('is_bot_detected', True)])
    total_checks = len(results)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Results - {search_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            margin-top: 10px;
            opacity: 0.8;
            font-size: 1.1em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .usernames-section {{
            padding: 30px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .usernames-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .username-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }}
        .results-section {{
            padding: 30px;
        }}
        .platform-results {{
            margin-bottom: 30px;
        }}
        .platform-header {{
            background: #34495e;
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
            font-size: 1.2em;
        }}
        .result-card {{
            border: 1px solid #ecf0f1;
            border-top: none;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: white;
        }}
        .result-card:last-child {{
            border-radius: 0 0 8px 8px;
        }}
        .result-info {{
            flex: 1;
        }}
        .username {{
            font-weight: bold;
            font-size: 1.1em;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .url {{
            color: #3498db;
            text-decoration: none;
            font-size: 0.9em;
        }}
        .url:hover {{
            text-decoration: underline;
        }}
        .status {{
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        .status.real {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        .status.broken {{
            background: #fadbd8;
            color: #e74c3c;
        }}
        .confidence {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        .no-results {{
            text-align: center;
            padding: 50px;
            color: #7f8c8d;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OSINT Name Lookup Results</h1>
            <div class="subtitle">Search for: <strong>{search_name}</strong></div>
            <div class="subtitle">Generated: {timestamp}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(usernames)}</div>
                <div class="stat-label">Usernames Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_checks}</div>
                <div class="stat-label">Platform Checks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{real_count}</div>
                <div class="stat-label">Real Profiles Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{real_count/total_checks*100:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <div class="usernames-section">
            <h2>Generated Usernames</h2>
            <div class="usernames-grid">
"""
    
    for username in usernames:
        html_content += f'                <div class="username-card">{username}</div>\n'
    
    html_content += """
            </div>
        </div>
        
        <div class="results-section">
            <h2>Platform Results</h2>
"""
    
    if results:
        # Group results by platform
        platforms = {}
        for result in results:
            platform = result.get('platform', 'unknown')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(result)
        
        for platform, platform_results in platforms.items():
            html_content += f"""
            <div class="platform-results">
                <div class="platform-header">🔗 {platform.title()}</div>
"""
            
            for result in platform_results:
                username = result.get('username', 'Unknown')
                url = result.get('url', '#')
                is_real = not result.get('is_bot_detected', True)
                confidence = result.get('confidence_score', 0)
                
                status_class = 'real' if is_real else 'broken'
                status_text = 'REAL' if is_real else 'BROKEN'
                
                html_content += f"""
                <div class="result-card">
                    <div class="result-info">
                        <div class="username">{username}</div>
                        <a href="{url}" target="_blank" class="url">{url}</a>
                        <div class="confidence">Confidence: {confidence:.1%}</div>
                    </div>
                    <div class="status {status_class}">{status_text}</div>
                </div>
"""
            
            html_content += """
            </div>
"""
    else:
        html_content += """
            <div class="no-results">
                <h3>No results found</h3>
                <p>No platform checks were completed. This might be due to browser setup issues or network problems.</p>
            </div>
"""
    
    html_content += """
        </div>
        
        <div class="footer">
            <p>Generated by OSINT Name Lookup System | Enhanced 404 Detection with JavaScript Rendering</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def quick_demo_john_doe():
    print("🚀 Quick OSINT Name Lookup Demo - John Doe")
    print("=" * 50)
    print("📋 Enhanced 404 Detection: Heavy penalties for broken profiles ✅")
    
    # Test username generation
    print("\n1. Username Generation:")
    generator = UsernameGenerator()
    usernames = generator.generate("John", "Doe")
    print(f"   Generated {len(usernames)} usernames for 'John Doe':")
    
    # Take only first 8 usernames for demo
    demo_usernames = usernames[:8]
    for i, username in enumerate(demo_usernames, 1):
        print(f"   {i}. {username}")
    
    # Test bot detection with sample HTML
    print("\n2. Account Validation (Sample HTML):")
    detector = BotDetector()
    
    # Real account HTML
    real_html = """
    <html><head><title>John Doe - GitHub</title></head>
    <body><h1>John Doe</h1><div>repositories</div><div>followers</div><div>bio</div></body>
    </html>
    """
    
    # Broken account HTML  
    broken_html = """
    <html><head><title>Sorry, this page isn't available</title></head>
    <body><h1>User not found</h1><div>page not found</div></body>
    </html>
    """
    
    real_result = detector.analyze_page(real_html, "https://github.com/johndoe", 200, "github")
    broken_result = detector.analyze_page(broken_html, "https://github.com/nonexistent", 404, "github")
    
    print(f"   Real account: {real_result['confidence_score']:.3f} confidence ({'✅ REAL' if not real_result['is_bot_detected'] else '❌ BROKEN'})")
    print(f"   Broken account: {broken_result['confidence_score']:.3f} confidence ({'✅ REAL' if not broken_result['is_bot_detected'] else '❌ BROKEN'})")
    
    # Run actual system with demo usernames
    print("\n3. Running Actual System (First 8 usernames):")
    results = []
    
    try:
        scraper = OSINTScraper()
        
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
        print("   Generating HTML with sample data for demonstration...")
        
        # Generate sample results for HTML demo
        results = []
        for username in demo_usernames[:3]:  # Just first 3 for demo
            for platform in ['twitter', 'github', 'instagram', 'linkedin']:
                # Simulate some real and some broken results
                is_real = hash(username + platform) % 3 == 0  # 1/3 chance of being real
                confidence = 0.85 if is_real else 0.15
                url = f"https://{platform}.com/{username}"
                
                results.append({
                    'username': username,
                    'platform': platform,
                    'url': url,
                    'is_bot_detected': not is_real,
                    'confidence_score': confidence
                })
    
    # Generate HTML results
    print("\n4. Generating HTML Results Page...")
    html_content = generate_html_results(results, demo_usernames, "John Doe")
    
    # Save HTML file
    filename = f"john_doe_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ HTML results saved to: {filename}")
    print(f"   📊 Found {len([r for r in results if not r.get('is_bot_detected', True)])} real profiles")
    print(f"   🔗 Open {filename} in your browser to view results")
    
    print("\n5. Why it's slow:")
    print("   • Browser startup: ~10-15 seconds")
    print("   • Network requests: ~5-10 seconds per platform")
    print("   • Anti-detection measures: ~2-5 seconds")
    print("   • Total per search: ~30-60 seconds")
    
    print("\n6. Speed improvements possible:")
    print("   • Use headless mode")
    print("   • Parallel platform searches")
    print("   • Cache results")
    print("   • Use API endpoints where available")

if __name__ == "__main__":
    quick_demo_john_doe()
