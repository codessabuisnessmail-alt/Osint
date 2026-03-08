#!/usr/bin/env python3
"""
Run reverse lookup by name and output an HTML file with clickable links.

Usage:
  python run_reverse_lookup_links.py --name "John Doe" --platforms github
  python run_reverse_lookup_links.py --name "John Doe" --platforms twitter github
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.name_lookup import RealNameLookup


def build_html_report(name: str, results: dict, output_path: str) -> str:
	"""Create a simple HTML report with clickable links."""
	report = [
		"<!DOCTYPE html>",
		"<html>",
		"<head>",
		f"<meta charset='utf-8'><title>Reverse Lookup Results for {name}</title>",
		"<style>body{font-family:sans-serif;line-height:1.5;margin:24px} .plat{margin-top:16px} a{color:#0a66c2;text-decoration:none} a:hover{text-decoration:underline} .err{color:#b00020}</style>",
		"</head>",
		"<body>",
		f"<h1>Reverse Lookup Results for: {name}</h1>",
		f"<p>Generated at: {datetime.utcnow().isoformat()} UTC</p>",
	]

	found = results.get('found_usernames', []) or []
	if not found:
		report.append("<p>No usernames found.</p>")
	else:
		report.append("<h2>Matches</h2>")
		# Group by platform
		by_platform = {}
		for m in found:
			plat = m.get('platform', 'unknown')
			by_platform.setdefault(plat, []).append(m)
		for plat, items in by_platform.items():
			report.append(f"<div class='plat'><h3>{plat.title()}</h3><ul>")
			for item in items:
				name_txt = item.get('name') or item.get('username') or '(no name)'
				url = item.get('profile_url') or '#'
				conf = item.get('confidence', 0)
				report.append(f"<li><a href='{url}' target='_blank' rel='noopener noreferrer'>{name_txt}</a> <small>(confidence {conf:.2f})</small></li>")
			report.append("</ul></div>")

	errors = results.get('errors', []) or []
	if errors:
		report.append("<h2>Errors</h2><ul>")
		for e in errors:
			report.append(f"<li class='err'>{e}</li>")
		report.append("</ul>")

	report.extend(["</body>", "</html>"])

	with open(output_path, 'w', encoding='utf-8') as f:
		f.write("\n".join(report))
	return output_path


def parse_args():
	parser = argparse.ArgumentParser(description="Reverse lookup by name to clickable links HTML report")
	parser.add_argument('--name', required=True, help='Full name to search (e.g., "John Doe")')
	parser.add_argument('--platforms', nargs='+', required=True, help='Platforms to search (choose one or more: facebook,instagram,twitter,linkedin,github,tiktok)')
	parser.add_argument('--out', default='reverse_lookup_links.html', help='Output HTML file')
	return parser.parse_args()


def main():
	args = parse_args()
	lookup = RealNameLookup()
	results = lookup.reverse_lookup_by_name(args.name, args.platforms)
	out_path = os.path.abspath(args.out)
	build_html_report(args.name, results, out_path)
	print(json.dumps({
		"name": args.name,
		"platforms": args.platforms,
		"output": out_path,
		"results_count": len(results.get('found_usernames', []) or []),
	}, indent=2))
	print(f"\nOpen this file in a browser: {out_path}")


if __name__ == '__main__':
	main()
