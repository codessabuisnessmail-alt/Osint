import time
import random
from scraper.cookie_manager import CookieManager
from browser.selenium_stealth import SeleniumStealthBrowser
from detection.bot_detector import BotDetector
from config import Config
from username_generator import UsernameGenerator


def check_usernames(name: str, count: int = 71):
    cfg = Config()
    cookies = CookieManager()
    detector = BotDetector()
    generator = UsernameGenerator()
    
    # Generate usernames (now generates 71)
    first_name, last_name = name.split(' ', 1)
    usernames = generator.generate(first_name, last_name)
    
    # Platforms to check
    platforms = ['instagram', 'twitter', 'github', 'linkedin']
    
    results = []
    
    # Use all 71 usernames instead of limiting to count
    for i, username in enumerate(usernames):
        print(f"\nChecking {i+1}/{count}: {username}")
        
        for platform in platforms:
            url = f"https://www.{platform}.com/{username}"
            
            try:
                with SeleniumStealthBrowser(headless=cfg.HEADLESS,
                                            viewport_width=cfg.VIEWPORT_WIDTH,
                                            viewport_height=cfg.VIEWPORT_HEIGHT) as browser:
                    
                    # Inject cookies for logged-in session
                    cookies.inject_cookies_to_selenium(browser, platform)
                    
                    if browser.navigate_to(url):
                        html = browser.get_page_source()
                        current_url = browser.current_url
                        result = detector.analyze_page(html, current_url, 200, platform)
                        
                        status = 'REAL' if result['confidence_score'] >= cfg.MEDIUM_CONFIDENCE else 'BROKEN'
                        
                        results.append({
                            'username': username,
                            'platform': platform,
                            'url': current_url,
                            'confidence': result['confidence_score'],
                            'status': status,
                            'method': result['detection_method']
                        })
                        
                        print(f"  {platform}: {status} ({result['confidence_score']:.1%})")
                        
                        # Random delay between requests
                        time.sleep(random.uniform(1, 3))
                    else:
                        print(f"  {platform}: Navigation failed")
                        
            except Exception as e:
                print(f"  {platform}: Error - {e}")
    
    return results


def generate_html_report(results, name: str):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Username Check Results - {name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .results {{ margin-top: 20px; }}
            .result {{ 
                border: 1px solid #ddd; 
                margin: 10px 0; 
                padding: 15px; 
                border-radius: 5px;
                background: white;
            }}
            .real {{ border-left: 5px solid #4CAF50; }}
            .broken {{ border-left: 5px solid #f44336; }}
            .username {{ font-weight: bold; font-size: 18px; }}
            .platform {{ color: #666; }}
            .confidence {{ font-size: 14px; }}
            .status {{ font-weight: bold; }}
            .status.real {{ color: #4CAF50; }}
            .status.broken {{ color: #f44336; }}
            a {{ color: #2196F3; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Username Check Results</h1>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Total Results:</strong> {len(results)}</p>
        </div>
        
        <div class="results">
    """
    
    for result in results:
        status_class = result['status'].lower()
        html += f"""
            <div class="result {status_class}">
                <div class="username">{result['username']}</div>
                <div class="platform">{result['platform'].title()}</div>
                <div class="confidence">Confidence: {result['confidence']:.1%}</div>
                <div class="status {status_class}">Status: {result['status']}</div>
                <div>Method: {result['method']}</div>
                <a href="{result['url']}" target="_blank">Visit Profile →</a>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    # Save to file
    filename = f"username_check_results_{name.replace(' ', '_').lower()}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filename


if __name__ == "__main__":
    name = "Abigail Baugh"
    print(f"Checking 71 usernames for: {name}")
    
    results = check_usernames(name, 71)
    
    if results:
        filename = generate_html_report(results, name)
        print(f"\n✅ Results saved to: {filename}")
        print(f"📊 Found {len([r for r in results if r['status'] == 'REAL'])} real profiles")
    else:
        print("❌ No results to report")
