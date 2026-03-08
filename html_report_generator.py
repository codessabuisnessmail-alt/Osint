#!/usr/bin/env python3
"""
HTML Report Generator for OSINT Results
=======================================

Generates beautiful HTML reports for OSINT search results.
"""

import os
import json
from datetime import datetime
from pathlib import Path


def generate_html_report(results, usernames, search_name, output_path=None):
    """
    Generate a comprehensive HTML report for OSINT search results.
    
    Args:
        results: List of search results
        usernames: List of usernames that were checked
        search_name: The name that was searched
        output_path: Optional output path for the HTML file
    
    Returns:
        str: Path to the generated HTML file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"username_check_results_{search_name.lower().replace(' ', '_')}_{timestamp}.html"
    
    # Calculate statistics
    total_checks = len(results)
    real_profiles = [r for r in results if not r.get('is_bot_detected', True)]
    broken_profiles = [r for r in results if r.get('is_bot_detected', True)]
    
    # Group by platform
    platform_stats = {}
    for result in results:
        platform = result.get('platform', 'unknown')
        if platform not in platform_stats:
            platform_stats[platform] = {'real': 0, 'broken': 0, 'total': 0}
        platform_stats[platform]['total'] += 1
        if not result.get('is_bot_detected', True):
            platform_stats[platform]['real'] += 1
        else:
            platform_stats[platform]['broken'] += 1
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Results: {search_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
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
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
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
            border-left: 4px solid #3498db;
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .success-rate {{
            border-left-color: #27ae60;
        }}
        
        .broken-rate {{
            border-left-color: #e74c3c;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }}
        
        .platform-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .platform-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
        }}
        
        .platform-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            text-transform: capitalize;
        }}
        
        .platform-stats {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }}
        
        .platform-stat {{
            text-align: center;
        }}
        
        .platform-stat-number {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .platform-stat-label {{
            font-size: 0.8em;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        .results-table th {{
            background: #34495e;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 500;
        }}
        
        .results-table td {{
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .results-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .status-real {{
            background: #d5f4e6;
            color: #27ae60;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .status-broken {{
            background: #fadbd8;
            color: #e74c3c;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .confidence-bar {{
            background: #ecf0f1;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-top: 5px;
        }}
        
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60);
            transition: width 0.3s ease;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        .link {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .link:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .platform-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OSINT Search Results</h1>
            <div class="subtitle">
                Search for: <strong>{search_name}</strong><br>
                Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_checks}</div>
                <div class="stat-label">Total Checks</div>
            </div>
            <div class="stat-card success-rate">
                <div class="stat-number">{len(real_profiles)}</div>
                <div class="stat-label">Real Profiles</div>
            </div>
            <div class="stat-card broken-rate">
                <div class="stat-number">{len(broken_profiles)}</div>
                <div class="stat-label">Broken Profiles</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(real_profiles)/total_checks*100:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <div class="content">
    

            
            <div class="section">
                <h2>🎯 Detailed Results</h2>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Platform</th>
                            <th>Status</th>
                            <th>Confidence</th>
                            <th>URL</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Add detailed results
    for result in results:
        username = result.get('username', 'Unknown')
        platform = result.get('platform', 'Unknown').title()
        is_real = not result.get('is_bot_detected', True)
        confidence = result.get('confidence_score', 0) * 100
        url = result.get('url', '#')
        
        status_class = 'status-real' if is_real else 'status-broken'
        status_text = '✅ REAL' if is_real else '❌ BROKEN'
        
        html_content += f"""
                        <tr>
                            <td><strong>{username}</strong></td>
                            <td>{platform}</td>
                            <td><span class="{status_class}">{status_text}</span></td>
                            <td>
                                {confidence:.1f}%
                                <div class="confidence-bar">
                                    <div class="confidence-fill" style="width: {confidence}%"></div>
                                </div>
                            </td>
                            <td><a href="{url}" target="_blank" class="link">View Profile</a></td>
                        </tr>
"""
    
    html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>📝 Search Details</h2>
                <p><strong>Search Name:</strong> {search_name}</p>
                <p><strong>Usernames Checked:</strong> {len(usernames)}</p>
                <p><strong>Total Profile Checks:</strong> {total_checks}</p>
                <p><strong>Search Date:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")}</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by OSINT Social Media Profile Finder</p>
            <p>🔍 Find social media profiles using real names with high accuracy</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML report generated: {output_path}")
    return output_path


def generate_simple_html_report(results, search_name, output_path=None):
    """
    Generate a simple HTML report for quick viewing.
    
    Args:
        results: List of search results
        search_name: The name that was searched
        output_path: Optional output path for the HTML file
    
    Returns:
        str: Path to the generated HTML file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"simple_results_{search_name.lower().replace(' ', '_')}_{timestamp}.html"
    
    # Calculate basic stats
    total = len(results)
    real = len([r for r in results if not r.get('is_bot_detected', True)])
    broken = total - real
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OSINT Results: {search_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            flex: 1;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .result {{
            margin: 10px 0;
            padding: 10px;
            border-left: 4px solid #ddd;
            background: #f9f9f9;
        }}
        .real {{
            border-left-color: #28a745;
            background: #d4edda;
        }}
        .broken {{
            border-left-color: #dc3545;
            background: #f8d7da;
        }}
        .platform {{
            font-weight: bold;
            color: #666;
        }}
        .confidence {{
            color: #007bff;
            font-weight: bold;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 OSINT Results: {search_name}</h1>
        <p>Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{total}</div>
                <div>Total</div>
            </div>
            <div class="stat">
                <div class="stat-number">{real}</div>
                <div>Real</div>
            </div>
            <div class="stat">
                <div class="stat-number">{broken}</div>
                <div>Broken</div>
            </div>
        </div>
        
        <h2>Results:</h2>
"""
    
    for result in results:
        username = result.get('username', 'Unknown')
        platform = result.get('platform', 'Unknown').title()
        is_real = not result.get('is_bot_detected', True)
        confidence = result.get('confidence_score', 0) * 100
        url = result.get('url', '#')
        
        status_class = 'real' if is_real else 'broken'
        status_text = '✅ REAL' if is_real else '❌ BROKEN'
        
        html_content += f"""
        <div class="result {status_class}">
            <div><strong>{username}</strong> on <span class="platform">{platform}</span></div>
            <div>Status: {status_text} | Confidence: <span class="confidence">{confidence:.1f}%</span></div>
            <div><a href="{url}" target="_blank">View Profile</a></div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Simple HTML report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage
    sample_results = [
        {
            'username': 'johndoe',
            'platform': 'facebook',
            'is_bot_detected': False,
            'confidence_score': 0.85,
            'url': 'https://facebook.com/johndoe'
        },
        {
            'username': 'johndoe123',
            'platform': 'twitter',
            'is_bot_detected': True,
            'confidence_score': 0.15,
            'url': 'https://twitter.com/johndoe123'
        }
    ]
    
    generate_html_report(sample_results, ['johndoe', 'johndoe123'], 'John Doe')
