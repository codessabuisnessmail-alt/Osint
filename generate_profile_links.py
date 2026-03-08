#!/usr/bin/env python3
"""
Generate an HTML file with clickable known real profile links for quick verification.

Usage:
  python generate_profile_links.py --out clickable_test_links.html
"""

import os
import argparse
from datetime import datetime

KNOWN_PROFILES = [
	# Twitter (official account)
	{"name": "Example", "platform": "twitter", "username": "twitter", "url": "https://twitter.com/twitter"},
	# GitHub (org account)
	{"name": "Example", "platform": "github", "username": "github", "url": "https://github.com/github"},
	# LinkedIn (company page)
	{"name": "Example", "platform": "linkedin", "username": "linkedin", "url": "https://www.linkedin.com/company/linkedin"},
]


def build_html(profiles, output_path):
	html = [
		"<!DOCTYPE html>",
		"<html>",
		"<head>",
		"<meta charset='utf-8'>",
		"<meta name='viewport' content='width=device-width, initial-scale=1'>",
		"<title>Clickable Test Links</title>",
		"<style>body{font-family:sans-serif;margin:24px;line-height:1.6} a{color:#0a66c2;text-decoration:none} a:hover{text-decoration:underline} .item{margin:10px 0}</style>",
		"</head>",
		"<body>",
		"<h1>Clickable Test Links</h1>",
		f"<p>Generated: {datetime.utcnow().isoformat()}Z</p>",
		"<ul>",
	]
	for p in profiles:
		label = f"{p['name']} — {p['platform'].title()} (@{p['username']})"
		html.append(f"<li class='item'><a href='{p['url']}' target='_blank' rel='noopener noreferrer'>{label}</a></li>")
	html += ["</ul>", "</body>", "</html>"]
	with open(output_path, 'w', encoding='utf-8') as f:
		f.write("\n".join(html))
	return output_path


def parse_args():
	parser = argparse.ArgumentParser(description="Generate clickable known profile links")
	parser.add_argument('--out', default='clickable_test_links.html', help='Output HTML path')
	return parser.parse_args()


def main():
	args = parse_args()
	out_path = os.path.abspath(args.out)
	build_html(KNOWN_PROFILES, out_path)
	print(out_path)


if __name__ == '__main__':
	main()
