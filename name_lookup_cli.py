#!/usr/bin/env python3
"""
Command Line Interface for Real Name Lookup System

Usage examples:
    python name_lookup_cli.py --name "John Doe" --birth-year 1990
    python name_lookup_cli.py --username "johndoe"
    python name_lookup_cli.py --email "johndoe@gmail.com"
    python name_lookup_cli.py --reverse "John Doe"
"""

import argparse
import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.name_lookup import RealNameLookup

def print_banner():
    """Print application banner"""
    print("🔍 Real Name Lookup System - OSINT Tool")
    print("=" * 50)
    print("Search across social media platforms to find real names")
    print("and associated profiles using advanced username generation")
    print("=" * 50)

def print_result(result, search_type):
    """Print formatted search results"""
    print(f"\n🎯 {search_type.upper()} SEARCH RESULTS")
    print("-" * 40)
    
    if not result:
        print("❌ No results found")
        return
    
    # Print basic info
    if 'search_timestamp' in result:
        timestamp = datetime.fromisoformat(result['search_timestamp'].replace('Z', '+00:00'))
        print(f"📅 Search Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    if 'confidence_score' in result:
        confidence = result['confidence_score']
        confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
        print(f"🎯 Confidence: {confidence:.2f} {confidence_bar}")
    
    # Print platform info
    if 'platforms_searched' in result:
        print(f"🔍 Platforms Searched: {', '.join(result['platforms_searched'])}")
    
    # Print errors if any
    if result.get('errors'):
        print(f"\n⚠️  Errors encountered:")
        for error in result['errors']:
            print(f"   • {error}")
    
    # Print specific results based on search type
    if search_type == 'name_lookup':
        print_name_lookup_results(result)
    elif search_type == 'username_lookup':
        print_username_lookup_results(result)
    elif search_type == 'reverse_lookup':
        print_reverse_lookup_results(result)
    elif search_type == 'email_lookup':
        print_email_lookup_results(result)

def print_name_lookup_results(result):
    """Print results for name-based lookup"""
    if result.get('generated_usernames'):
        print(f"\n🔑 Generated Usernames ({len(result['generated_usernames'])}):")
        print("=" * 60)
        
        # Group profiles by username
        username_profiles = {}
        for profile in result.get('found_profiles', []):
            username = profile.get('username', '')
            if username not in username_profiles:
                username_profiles[username] = []
            username_profiles[username].append(profile)
        
        # Display each username with its profiles
        for i, username in enumerate(result['generated_usernames'], 1):
            print(f"{i:3d}. {username}")
            
            # Show matching profiles for this username
            if username in username_profiles:
                profiles = username_profiles[username]
                for profile in profiles:
                    platform = profile.get('platform', 'Unknown').upper()
                    name = profile.get('name', 'Unknown Name')
                    profile_url = profile.get('profile_url', '')
                    confidence = profile.get('confidence', 0.0)
                    
                    print(f"     📱 {platform}: {name}")
                    print(f"        🔗 {profile_url}")
                    print(f"        🎯 Confidence: {confidence:.2f}")
                    print()
            else:
                print("     ❌ No profiles found")
                print()
    
    if result.get('found_profiles'):
        total_profiles = len(result['found_profiles'])
        print(f"\n📊 Summary: Found {total_profiles} profiles across all usernames")
        
        # Show platform breakdown
        platform_counts = {}
        for profile in result['found_profiles']:
            platform = profile.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        if platform_counts:
            print("\n🌐 Platform Breakdown:")
            for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {platform.upper()}: {count} profiles")
    
    if result.get('errors'):
        print(f"\n⚠️  Errors encountered:")
        for error in result['errors']:
            print(f"   • {error}")

def print_username_lookup_results(result):
    """Print results for username-based lookup"""
    if result.get('potential_names'):
        print(f"\n👤 Potential Names Found ({len(result['potential_names'])}):")
        for name_data in result['potential_names']:
            print(f"   • {name_data.get('name', 'Unknown')} (Confidence: {name_data.get('confidence', 0):.2f})")
    
    if result.get('found_profiles'):
        print(f"\n📱 Profiles Found ({len(result['found_profiles'])}):")
        print("=" * 50)
        
        for profile in result['found_profiles']:
            platform = profile.get('platform', 'Unknown').upper()
            name = profile.get('name', 'Unknown Name')
            username = profile.get('username', 'Unknown')
            profile_url = profile.get('profile_url', '')
            confidence = profile.get('confidence', 0.0)
            
            print(f"🌐 {platform}")
            print(f"   👤 Name: {name}")
            print(f"   🔑 Username: {username}")
            print(f"   🔗 Profile: {profile_url}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            print()
    
    if result.get('sources'):
        print(f"\n📊 Sources:")
        for source in result['sources']:
            print(f"   • {source['platform']}: {source['names_found']} names, Confidence: {source['confidence']:.2f}")

def print_reverse_lookup_results(result):
    """Print results for reverse lookup"""
    if result.get('found_usernames'):
        print(f"\n🔑 Usernames Found ({len(result['found_usernames'])}):")
        for username_data in result['found_usernames']:
            print(f"   • {username_data.get('username', 'Unknown')}")
            print(f"      Platform: {username_data.get('platform', 'Unknown')}")
            print(f"      Confidence: {username_data.get('confidence', 0):.2f}")

def print_email_lookup_results(result):
    """Print results for email-based lookup"""
    if result.get('potential_names'):
        print(f"\n👤 Potential Names Found ({len(result['potential_names'])}):")
        for name_data in result['potential_names']:
            print(f"   • {name_data.get('name', 'Unknown')} (Confidence: {name_data.get('confidence', 0):.2f})")

def save_results(result, search_type, output_file=None):
    """Save results to file"""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"name_lookup_{search_type}_{timestamp}.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Real Name Lookup System - OSINT Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python name_lookup_cli.py --name "John Doe" --birth-year 1990 --platforms twitter,github,instagram,linkedin
  python name_lookup_cli.py --username "johndoe" --platforms facebook,instagram,twitter
  python name_lookup_cli.py --email "johndoe@gmail.com" --platforms linkedin,github
  python name_lookup_cli.py --reverse "John Doe" --platforms linkedin,github,twitter
        """
    )
    
    # Search type arguments (mutually exclusive)
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--name', nargs=2, metavar=('FIRST', 'LAST'),
                             help='Search by first and last name')
    search_group.add_argument('--username', metavar='USERNAME',
                             help='Search by username')
    search_group.add_argument('--email', metavar='EMAIL',
                             help='Search by email address')
    search_group.add_argument('--reverse', metavar='FULL_NAME',
                             help='Reverse lookup - find usernames by name')
    
    # Optional arguments
    parser.add_argument('--birth-year', type=int, metavar='YEAR',
                       help='Birth year for additional username variations')
    parser.add_argument('--platforms', metavar='PLATFORMS', required=True,
                       help='Comma-separated list of platforms to search (facebook,instagram,twitter,linkedin,github,tiktok)')
    parser.add_argument('--output', metavar='FILE',
                       help='Output file for results (default: auto-generated)')
    parser.add_argument('--save', action='store_true',
                       help='Save results to file')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Initialize lookup system
    try:
        lookup = RealNameLookup()
        print("✅ Lookup system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize lookup system: {e}")
        sys.exit(1)
    
    # Parse platforms
    platforms = [p.strip() for p in args.platforms.split(',')]
    print(f"🔍 Searching platforms: {', '.join(platforms)}")
    
    # Perform search based on arguments
    result = None
    search_type = ""
    
    try:
        if args.name:
            first_name, last_name = args.name
            print(f"\n🔍 Searching for profiles by name: {first_name} {last_name}")
            if args.birth_year:
                print(f"📅 Using birth year: {args.birth_year}")
            
            result = lookup.lookup_by_name(first_name, last_name, args.birth_year, platforms)
            search_type = "name_lookup"
            
        elif args.username:
            print(f"\n🔍 Searching for real name by username: {args.username}")
            result = lookup.lookup_by_username(args.username, platforms)
            search_type = "username_lookup"
            
        elif args.email:
            print(f"\n🔍 Searching for real name by email: {args.email}")
            result = lookup.lookup_by_email(args.email)
            search_type = "email_lookup"
            
        elif args.reverse:
            print(f"\n🔍 Performing reverse lookup for name: {args.reverse}")
            result = lookup.reverse_lookup_by_name(args.reverse, platforms)
            search_type = "reverse_lookup"
        
        # Print results
        print_result(result, search_type)
        
        # Save results if requested
        if args.save or args.output:
            save_results(result, search_type, args.output)
        
        # Save to database
        try:
            if result and result.get('confidence_score', 0) > 0:
                lookup.save_lookup_result(result)
                print("\n💾 Results saved to database")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not save to database: {e}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Search interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        sys.exit(1)
    finally:
        lookup.close()

if __name__ == "__main__":
    main()
