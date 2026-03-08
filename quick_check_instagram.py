import time
from scraper.cookie_manager import CookieManager
from browser.selenium_stealth import SeleniumStealthBrowser
from detection.bot_detector import BotDetector
from config import Config


def check_url(url: str, platform: str = "instagram"):
    cfg = Config()
    cookies = CookieManager()
    detector = BotDetector()

    with SeleniumStealthBrowser(headless=cfg.HEADLESS,
                                viewport_width=cfg.VIEWPORT_WIDTH,
                                viewport_height=cfg.VIEWPORT_HEIGHT) as browser:
        # Inject cookies for logged-in session
        cookies.inject_cookies_to_selenium(browser, platform)

        if not browser.navigate_to(url):
            print("Navigation failed")
            return

        html = browser.get_page_source()
        current_url = browser.current_url
        result = detector.analyze_page(html, current_url, 200, platform)

        print(f"URL: {current_url}")
        print(f"Confidence: {result['confidence_score']:.1%}")
        print(f"Detected: {'REAL' if result['confidence_score'] >= cfg.MEDIUM_CONFIDENCE else 'BROKEN/OTHER'}")
        print(f"Method: {result['detection_method']}")


if __name__ == "__main__":
    check_url("https://www.instagram.com/abigail.baugh", "instagram")
