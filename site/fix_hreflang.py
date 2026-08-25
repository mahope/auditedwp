#!/usr/bin/env python3
"""Fix hreflang clusters across the site.

Rules applied:
- Every EN page with a DE counterpart gets: hreflang=en (self), hreflang=de,
  hreflang=x-default (self). DE pages already have en+de; x-default added if missing.
- Pages with only x-default get full cluster: en + de (self) + x-default.
- de/was-ist-ein-impressum: add self-referencing hreflang=de + x-default(en).
"""
import re, os, sys

BASE = 'https://eucomplypro.com'

def url_for(path):
    path = path.removesuffix('index.html').removesuffix('/')
    if not path:
        return BASE + '/'
    return BASE + '/' + path.strip('/') + '/'

def inject_before(head_close_marker):
    pass

def fix_page(path, en_url=None, de_url=None, self_lang='en'):
    html = open(path, encoding='utf-8').read()
    head, rest = html.split('</head>', 1)
    # strip existing alternate links
    head = re.sub(r'\s*<link rel="alternate"[^>]*>\n?', '\n', head)
    u_self = url_for(path)
    tags = []
    if self_lang == 'en':
        tags.append(f'<link rel="alternate" hreflang="en" href="{u_self}">')
        if de_url:
            tags.append(f'<link rel="alternate" hreflang="de" href="{de_url}">')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{u_self}">')
    else:  # de page
        if en_url:
            tags.append(f'<link rel="alternate" hreflang="en" href="{en_url}">')
        tags.append(f'<link rel="alternate" hreflang="de" href="{u_self}">')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{en_url or u_self}">')
    block = '\n'.join(tags) + '\n'
    head = head.rstrip() + '\n' + block
    open(path, 'w', encoding='utf-8').write(head + '</head>' + rest)

def main():
    # 1. EN pages with DE counterpart -> full cluster
    en_with_de = [
        ('index.html', f'{BASE}/de/'),
        ('cookie-banner-check/index.html', f'{BASE}/de/cookie-banner-check/'),
        ('blog/gdpr-cookie-banner-fines/index.html', f'{BASE}/de/dsgvo-cookie-banner-bussgelder/'),
        ('blog/german-impressum-foreign-sellers/index.html', f'{BASE}/de/was-ist-ein-impressum/'),
    ]
    for p, de in en_with_de:
        fix_page(p, de_url=de, self_lang='en')

    # 2. DE pages -> ensure full cluster (self de + en counterpart + x-default)
    de_pages = [
        ('de/index.html', f'{BASE}/'),
        ('de/cookie-banner-check/index.html', f'{BASE}/cookie-banner-check/'),
        ('de/dsgvo-cookie-banner-bussgelder/index.html', f'{BASE}/blog/gdpr-cookie-banner-fines/'),
        ('de/was-ist-ein-impressum/index.html', f'{BASE}/blog/german-impressum-foreign-sellers/'),
    ]
    for p, en in de_pages:
        fix_page(p, en_url=en, self_lang='de')

    print("done")

if __name__ == '__main__':
    main()
