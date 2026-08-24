#!/usr/bin/env python3
"""Inject JSON-LD structured data into pages that lack it.

- store/*/index.html -> Product + Offer (price scraped from page)
- blog/*, vs/*, pro/vs-* , devnotify/guides|vs -> Article
Idempotent: skips files that already contain ld+json.
"""
import os, re, json, html

ROOT = os.path.join(os.path.dirname(__file__), '..', 'site')
BASE = 'https://auditedwp.pages.dev'

def meta(t, prop):
    m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)' % re.escape(prop), t)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % re.escape(prop), t)
    return html.unescape(m.group(1)) if m else ''

def title_of(t):
    m = re.search(r'<title>([^<]*)</title>', t)
    return html.unescape(m.group(1)).strip() if m else ''

def desc_of(t):
    return meta(t, 'og:description') or meta(t, 'description')

def price_of(t):
    m = re.search(r'\$([0-9]+)', t)
    return m.group(1) if m else None

def breadcrumb(url):
    parts = url.strip('/').split('/') if url.strip('/') else []
    items, path = [], ''
    for i, p in enumerate(parts):
        path += '/' + p
        items.append({'@type': 'ListItem', 'position': i + 1,
                      'name': p.replace('-', ' ').title(), 'item': BASE + path + '/'})
    return items

org = {'@type': 'Organization', 'name': 'ComplianceDocs'}

def article_ld(url, t):
    d = {'@context': 'https://schema.org', '@type': 'Article',
         'headline': title_of(t)[:110], 'description': desc_of(t)[:300],
         'mainEntityOfPage': BASE + url, 'author': org, 'publisher': org}
    m = re.search(r'date[Pp]ublished["\']?[:=]\s*["\'](\d{4}-\d{2}-\d{2})', t)
    if m:
        d['datePublished'] = d['dateModified'] = m.group(1)
    return d

def product_ld(url, t):
    name = title_of(t).split('—')[0].strip()
    price = price_of(t)
    d = {'@context': 'https://schema.org', '@type': 'Product',
         'name': name, 'description': desc_of(t)[:300],
         'brand': {'@type': 'Brand', 'name': 'ComplianceDocs'}}
    if price:
        d['offers'] = {'@type': 'Offer', 'price': price, 'priceCurrency': 'USD',
                       'availability': 'https://schema.org/PreOrder',
                       'url': BASE + url.rstrip('/') + '/'}
    return d

SKIP = ('privacy/', 'terms/', 'thank-you', 'dashboard', '/sample/', 'tools/',
        'pro/sample-report', 'badge/', 'template/', 'update.json')

for dp, _, fs in os.walk(ROOT):
    for f in fs:
        if f != 'index.html':
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT)
        url = '/' + rel.replace(os.sep, '/')
        t = open(p, encoding='utf-8', errors='ignore').read()
        if 'ld+json' in t:
            continue
        blocks = []
        if rel.startswith('store/') and price_of(t):
            blocks.append(product_ld(url, t))
            bc = breadcrumb('/store')
            if bc:
                blocks.append({'@context': 'https://schema.org',
                               '@type': 'BreadcrumbList', 'itemListElement': bc})
        elif any(rel.startswith(s.strip('/')) or s in rel for s in
                 ('blog/', 'vs/', 'devnotify/guides/', 'devnotify/vs/', 'devnotify/slack')) \
                and not any(s in rel for s in SKIP):
            blocks.append(article_ld(url, t))
        if not blocks:
            continue
        snippet = '\n'.join(
            '<script type="application/ld+json">%s</script>' % json.dumps(b, ensure_ascii=False)
            for b in blocks)
        idx = t.find('</head>')
        assert idx > 0, rel
        open(p, 'w', encoding='utf-8').write(t[:idx] + snippet + '\n' + t[idx:])
        print('patched', rel)
