#!/usr/bin/env python3
"""
🔍 OSINT Social Media Profile Finder
====================================

A powerful and user-friendly tool to find social media profiles using real names.
Searches across Twitter, GitHub, Instagram, LinkedIn, and Facebook.

USAGE EXAMPLES:
    # Find profiles for a person by name
    python osint_cli.py search "John Doe"
    
    # Quick demo with sample data
    python osint_cli.py demo "Abigail Baugh"
    
    # Generate HTML report
    python osint_cli.py report "John Doe" --output john_doe_results.html
    
    # Check specific username
    python osint_cli.py check-username "johndoe123"
    
    # Get system status and configuration
    python osint_cli.py status
    
    # Show detailed help
    python osint_cli.py --help
    python osint_cli.py search --help
"""

import argparse
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from username_generator import UsernameGenerator
from detection.bot_detector import BotDetector
from scraper.osint_scraper import OSINTScraper

class OSINTCLI:
    def __init__(self):
        self.setup_parser()
    
    def setup_parser(self):
        """Setup command line argument parser with comprehensive help"""
        self.parser = argparse.ArgumentParser(
            prog='osint_cli.py',
            description='🔍 OSINT Social Media Profile Finder - Find social media profiles using real names',
            epilog='''
EXAMPLES:
  python osint_cli.py search "John Doe" --platforms twitter github instagram linkedin
  python osint_cli.py demo "Abigail Baugh" --platforms twitter github instagram
  python osint_cli.py check-username "johndoe123" --platforms linkedin twitter
  python osint_cli.py report "John Doe" --platforms twitter github instagram linkedin facebook
  python osint_cli.py status

PLATFORMS SUPPORTED:
  • Twitter/X (twitter.com)
  • GitHub (github.com) 
  • Instagram (instagram.com)
  • LinkedIn (linkedin.com)
  • Facebook (facebook.com)

FEATURES:
  • Advanced username generation algorithms
  • Real-time profile validation with confidence scoring
  • Anti-bot detection bypass
  • Beautiful HTML reports
  • Fast and accurate results
            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Create subparsers for different commands
        subparsers = self.parser.add_subparsers(
            dest='command',
            help='Available commands (use --help for detailed info)',
            metavar='COMMAND'
        )
        
        # SEARCH command
        search_parser = subparsers.add_parser(
            'search',
            help='Search for social media profiles using a real name',
            description='Search across all platforms to find profiles matching the given name'
        )
        search_parser.add_argument(
            'name',
            help='Full name to search for (e.g., "John Doe")'
        )
        search_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to search (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        search_parser.add_argument(
            '--max-usernames',
            type=int,
            default=20,
            help='Maximum number of usernames to generate and check (default: 20)'
        )
        search_parser.add_argument(
            '--output',
            help='Save results to JSON file'
        )
        search_parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )
        
        # DEMO command
        demo_parser = subparsers.add_parser(
            'demo',
            help='Run a quick demo with sample data',
            description='Demonstrate the system capabilities with a sample name'
        )
        demo_parser.add_argument(
            'name',
            help='Name to use for demo (e.g., "Abigail Baugh")'
        )
        demo_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to search (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        demo_parser.add_argument(
            '--max-usernames',
            type=int,
            default=5,
            help='Maximum number of usernames to check (default: 5 for demo)'
        )
        demo_parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )
        
        # CHECK-USERNAME command
        check_parser = subparsers.add_parser(
            'check-username',
            help='Check if a specific username exists on platforms',
            description='Check a single username across all platforms'
        )
        check_parser.add_argument(
            'username',
            help='Username to check (e.g., "johndoe123")'
        )
        check_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to check (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        
        # REPORT command
        report_parser = subparsers.add_parser(
            'report',
            help='Generate a beautiful HTML report',
            description='Create an HTML report with search results'
        )
        report_parser.add_argument(
            'name',
            help='Name used for the search'
        )
        report_parser.add_argument(
            '--input',
            help='JSON file with search results (if not provided, will run search)'
        )
        report_parser.add_argument(
            '--output',
            default=None,
            help='Output HTML file (default: username_check_results_NAME.html)'
        )
        report_parser.add_argument(
            '--platforms',
            nargs='+',
            choices=['twitter', 'github', 'instagram', 'linkedin', 'facebook'],
            required=True,
            help='Platforms to search (choose one or more: twitter, github, instagram, linkedin, facebook)'
        )
        
        # STATUS command
        status_parser = subparsers.add_parser(
            'status',
            help='Show system status and configuration',
            description='Display system information, configuration, and health status'
        )
        
        # GENERATE command
        generate_parser = subparsers.add_parser(
            'generate',
            help='Generate usernames from a real name',
            description='Show what usernames would be generated for a given name'
        )
        generate_parser.add_argument(
            'name',
            help='Full name to generate usernames for (e.g., "John Doe")'
        )
        generate_parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of usernames to generate (default: 20)'
        )
        generate_parser.add_argument(
            '--show-all',
            action='store_true',
            help='Show all generated usernames (not just first 10)'
        )
    
    def print_banner(self):
        """Print beautiful application banner"""
        print("🔍 OSINT Social Media Profile Finder")
        print("=" * 50)
        print("Find social media profiles using real names")
        print("Powered by advanced username generation and AI detection")
        print("=" * 50)
    
    def print_status(self):
        """Show system status and configuration"""
        print("📊 SYSTEM STATUS")
        print("=" * 50)
        
        # Check core components
        print("🔧 Core Components:")
        try:
            from username_generator import UsernameGenerator
            print("   ✅ Username Generator - Ready")
        except ImportError as e:
            print(f"   ❌ Username Generator - Error: {e}")
        
        try:
            from detection.bot_detector import BotDetector
            print("   ✅ Bot Detector - Ready")
        except ImportError as e:
            print(f"   ❌ Bot Detector - Error: {e}")
        
        try:
            from scraper.osint_scraper import OSINTScraper
            print("   ✅ OSINT Scraper - Ready")
        except ImportError as e:
            print(f"   ❌ OSINT Scraper - Error: {e}")
        
        # Check browser setup
        print("\n🌐 Browser Setup:")
        try:
            from browser.selenium_stealth import SeleniumStealthBrowser
            print("   ✅ Selenium Stealth Browser - Available")
        except ImportError as e:
            print(f"   ❌ Selenium Stealth Browser - Error: {e}")
        
        # Show configuration
        print("\n⚙️  Configuration:")
        try:
            from config import Config
            config = Config()
            print(f"   • Headless Mode: {config.HEADLESS}")
            print(f"   • Viewport: {config.VIEWPORT_WIDTH}x{config.VIEWPORT_HEIGHT}")
            print(f"   • Platforms: {list(config.PLATFORMS.keys())}")
        except Exception as e:
            print(f"   ❌ Configuration Error: {e}")
        
        print("\n📈 Ready to search!")
    
    def generate_usernames(self, name, count=20, show_all=False):
        """Generate and display usernames for a given name"""
        print(f"🔑 GENERATING USERNAMES FOR: {name}")
        print("=" * 50)
        
        try:
            generator = UsernameGenerator()
            usernames = generator.generate(name.split()[0], name.split()[1] if len(name.split()) > 1 else "")
            
            print(f"📊 Generated {len(usernames)} total usernames")
            print(f"📋 Showing first {count} usernames:")
            print()
            
            display_count = len(usernames) if show_all else min(count, len(usernames))
            for i, username in enumerate(usernames[:display_count], 1):
                print(f"{i:3d}. {username}")
            
            if not show_all and len(usernames) > count:
                print(f"\n... and {len(usernames) - count} more usernames")
                print("Use --show-all to see all generated usernames")
            
            return usernames
            
        except Exception as e:
            print(f"❌ Error generating usernames: {e}")
            return []
    
    def run_search(self, name, platforms, max_usernames, output=None, verbose=False):
        """Run a full search for profiles using selenium-based system"""
        print(f"🔍 SEARCHING FOR: {name}")
        print(f"📱 Platforms: {', '.join(platforms)}")
        print(f"🔢 Max Usernames: {max_usernames}")
        print("=" * 50)
        
        try:
            # Generate usernames
            if verbose:
                print("🔄 Generating usernames...")
            
            generator = UsernameGenerator()
            usernames = generator.generate(name.split()[0], name.split()[1] if len(name.split()) > 1 else "")
            
            # Limit to requested number of usernames
            if max_usernames > 0:
                usernames = usernames[:max_usernames]
            
            if verbose:
                print(f"✅ Generated {len(usernames)} usernames")
            
            # Initialize selenium-based scraper
            if verbose:
                print("🔄 Initializing selenium-based scraper...")
            
            scraper = OSINTScraper()
            
            # Ensure fresh cookies are available
            try:
                from auto_cookie_updater import AutoCookieUpdater
                cookie_updater = AutoCookieUpdater()
                cookie_updater.ensure_fresh_cookies()
                if verbose:
                    print("✅ Fresh cookies ensured")
            except Exception as e:
                if verbose:
                    print(f"⚠️  Cookie updater not available: {e}")
            results = []
            
            # Search each username on each platform
            total_checks = len(usernames) * len(platforms)
            current_check = 0
            
            for username in usernames:
                if verbose:
                    print(f"\n🔍 Checking username: {username}")
                
                for platform in platforms:
                    current_check += 1
                    if verbose:
                        print(f"   [{current_check}/{total_checks}] {platform.title()}: ", end="", flush=True)
                    
                    try:
                        # Build URL using scraper's method
                        url = scraper._build_url(username, platform)
                        
                        # Use selenium-based scraping
                        result = scraper.scrape_profile(url, platform, username)
                        
                        if result:
                            results.append(result)
                            confidence = result.get('confidence_score', 0)
                            status = "✅ REAL" if not result.get('is_bot_detected', True) else "❌ BROKEN"
                            
                            if verbose:
                                print(f"{confidence:.1%} confidence ({status})")
                                # Always show URL for both real and broken accounts
                                print(f"      🔗 {result.get('url', '')}")
                            else:
                                print(f"   {platform.title()}: {confidence:.1%} confidence ({status})")
                                # Always show URL for both real and broken accounts
                                print(f"       🔗 {result.get('url', '')}")
                        else:
                            if verbose:
                                print("No result")
                    
                    except Exception as e:
                        if verbose:
                            print(f"Error: {str(e)[:30]}...")
                        else:
                            print(f"   {platform.title()}: Error")
            
            # Display summary
            self._display_search_summary(results, name)
            
            # Save results if requested
            if output:
                self._save_results(results, output)
            
            # Generate HTML report
            print("\n📄 Generating HTML report...")
            try:
                from html_report_generator import generate_html_report
                html_path = generate_html_report(results, usernames, name)
                print(f"✅ HTML report generated: {html_path}")
            except Exception as e:
                print(f"❌ Error generating HTML report: {e}")

            # Clean up scraper
            try:
                scraper.close()
            except:
                pass
            
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def _build_url(self, username, platform):
        """Build URL for username check"""
        platform_urls = {
            'twitter': f'https://twitter.com/{username}',
            'github': f'https://github.com/{username}',
            'instagram': f'https://instagram.com/{username}',
            'linkedin': f'https://linkedin.com/in/{username}',
            'facebook': f'https://facebook.com/{username}'
        }
        return platform_urls.get(platform, f'https://{platform}.com/{username}')
    
    def _display_search_summary(self, results, name):
        """Display search results summary"""
        print(f"\n📊 SEARCH SUMMARY FOR: {name}")
        print("=" * 50)
        
        if not results:
            print("❌ No profiles found")
            return
        
        # Count real vs broken profiles
        real_profiles = [r for r in results if not r.get('is_bot_detected', True)]
        broken_profiles = [r for r in results if r.get('is_bot_detected', True)]
        
        print(f"✅ Real Profiles: {len(real_profiles)}")
        print(f"❌ Broken Profiles: {len(broken_profiles)}")
        print(f"📈 Success Rate: {len(real_profiles)/len(results)*100:.1f}%")
        
        # Show real profiles
        if real_profiles:
            print(f"\n🎯 REAL PROFILES FOUND:")
            for profile in real_profiles:
                username = profile.get('username', 'Unknown')
                platform = profile.get('platform', 'Unknown').title()
                confidence = profile.get('confidence_score', 0)
                url = profile.get('url', '')
                print(f"   • {username} on {platform} ({confidence:.1%} confidence)")
                print(f"     🔗 {url}")
        
        # Platform breakdown
        platforms = {}
        for result in results:
            platform = result.get('platform', 'unknown')
            if platform not in platforms:
                platforms[platform] = {'real': 0, 'broken': 0}
            if not result.get('is_bot_detected', True):
                platforms[platform]['real'] += 1
            else:
                platforms[platform]['broken'] += 1
        
        print(f"\n📱 PLATFORM BREAKDOWN:")
        for platform, counts in platforms.items():
            total = counts['real'] + counts['broken']
            real_rate = counts['real'] / total * 100 if total > 0 else 0
            print(f"   • {platform.title()}: {counts['real']} real, {counts['broken']} broken ({real_rate:.1f}% real)")
    
    def _save_results(self, results, output_file):
        """Save results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def run_demo(self, name, platforms, max_usernames=5, verbose=False):
        """Run a quick demo"""
        print(f"🚀 QUICK DEMO FOR: {name}")
        print("=" * 50)
        print("This is a demonstration of the OSINT system capabilities.")
        print(f"Running with {max_usernames} usernames for speed...")
        print()
        
        # Run search with specified number of usernames
        results = self.run_search(name, platforms, max_usernames=max_usernames, verbose=verbose)
        
        # Generate HTML report for demo
        if results:
            print("\n📄 Generating demo HTML report...")
            try:
                from html_report_generator import generate_html_report
                from username_generator import UsernameGenerator
                
                # Generate usernames for the report
                generator = UsernameGenerator()
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_name, last_name = name_parts[0], name_parts[1]
                else:
                    first_name, last_name = name, ""
                
                usernames = generator.generate(first_name, last_name)
                if max_usernames > 0:
                    usernames = usernames[:max_usernames]
                
                html_path = generate_html_report(results, usernames, name)
                print(f"✅ Demo HTML report generated: {html_path}")
            except Exception as e:
                print(f"❌ Error generating demo HTML report: {e}")
        
        print(f"\n✨ Demo completed! Found {len([r for r in results if not r.get('is_bot_detected', True)])} real profiles.")
        print("Use 'search' command for full comprehensive search.")
    
    def check_username(self, username, platforms):
        """Check a specific username across platforms"""
        print(f"🔍 CHECKING USERNAME: {username}")
        print(f"📱 Platforms: {', '.join(platforms)}")
        print("=" * 50)
        
        try:
            scraper = OSINTScraper()
            results = []
            
            for platform in platforms:
                print(f"🔍 {platform.title()}: ", end="", flush=True)
                
                try:
                    url = self._build_url(username, platform)
                    result = scraper.scrape_profile(url, platform, username)
                    
                    if result:
                        results.append(result)
                        confidence = result.get('confidence_score', 0)
                        status = "✅ REAL" if not result.get('is_bot_detected', True) else "❌ BROKEN"
                        print(f"{confidence:.1%} confidence ({status})")
                    else:
                        print("No result")
                
                except Exception as e:
                    print(f"Error: {str(e)[:30]}...")
            
            # Generate HTML report for username check
            if results:
                print("\n📄 Generating username check HTML report...")
                try:
                    from html_report_generator import generate_html_report
                    html_path = generate_html_report(results, [username], f"Username Check: {username}")
                    print(f"✅ Username check HTML report generated: {html_path}")
                except Exception as e:
                    print(f"❌ Error generating username check HTML report: {e}")
            
            # Summary
            real_count = len([r for r in results if not r.get('is_bot_detected', True)])
            print(f"\n📊 Summary: {real_count} real profiles out of {len(results)} checks")
            
            return results
            
        except Exception as e:
            print(f"❌ Error checking username: {e}")
            return []
    
    def generate_report(self, name, input_file=None, output=None, platforms=None):
        """Generate HTML report"""
        print(f"📄 GENERATING HTML REPORT FOR: {name}")
        print("=" * 50)
        
        try:
            # Get results
            if input_file:
                print(f"📂 Loading results from: {input_file}")
                with open(input_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            else:
                print("🔍 Running search to get results...")
                results = self.run_search(name, platforms or ['twitter', 'github', 'instagram', 'linkedin'], 20)
            
            if not results:
                print("❌ No results to generate report from")
                return
            
            # Generate HTML using the new HTML report generator
            print("\n📄 Generating HTML report...")
            try:
                from html_report_generator import generate_html_report
                from username_generator import UsernameGenerator
                
                # Generate usernames for the report
                generator = UsernameGenerator()
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_name, last_name = name_parts[0], name_parts[1]
                else:
                    first_name, last_name = name, ""
                
                usernames = generator.generate(first_name, last_name)
                
                # Use provided output path or generate default
                if not output:
                    output = f"username_check_results_{name.replace(' ', '_').lower()}.html"
                
                html_path = generate_html_report(results, usernames, name, output)
                print(f"✅ HTML report generated: {html_path}")
                
            except Exception as e:
                print(f"❌ Error generating HTML report: {e}")
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    

    
    def run(self):
        """Main CLI runner"""
        args = self.parser.parse_args()
        
        if not args.command:
            self.print_banner()
            self.parser.print_help()
            return
        
        # Run appropriate command
        if args.command == 'status':
            self.print_status()
        
        elif args.command == 'generate':
            self.generate_usernames(args.name, args.count, args.show_all)
        
        elif args.command == 'search':
            self.run_search(args.name, args.platforms, args.max_usernames, args.output, args.verbose)
        
        elif args.command == 'demo':
            self.run_demo(args.name, args.platforms)
        
        elif args.command == 'check-username':
            self.check_username(args.username, args.platforms)
        
        elif args.command == 'report':
            self.generate_report(args.name, args.input, args.output, args.platforms)

def main():
    """Main entry point"""
    cli = OSINTCLI()
    cli.run()

if __name__ == "__main__":
    main()
