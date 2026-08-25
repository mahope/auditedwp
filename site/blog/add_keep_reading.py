#!/usr/bin/env python3
"""Add a Keep Reading block to blog posts that lack it."""
import re, os

BLOG = os.path.dirname(os.path.abspath(__file__))

# slug -> (title, description)
POSTS = {
    "abmahnung-risk-ecommerce": ("Abmahnung Risk for E-commerce: Why German Competitors Send Cease-and-Desist Letters", "How German Abmahnung law works, what triggers a cease-and-desist against online stores, and how to check your site before someone else does it for you."),
    "best-free-gdpr-compliance-checkers-2026": ("Best Free GDPR Compliance Checkers in 2026 (Tested)", "We tested the most popular free GDPR compliance checkers on real websites. What they find, what they miss, and which one to use."),
    "nis2-compliance-checklist-2026": ("NIS2 Compliance Checklist 2026: The Essentials", "The core NIS2 requirements in one practical checklist: who is covered, what to implement, and how to document it."),
}

def get_title(html):
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    return re.sub(r"<.*?>", "", m.group(1)).strip() if m else ""

for slug, (title, desc) in POSTS.items():
    path = os.path.join(BLOG, slug, "index.html")
    if not os.path.exists(path):
        print(f"SKIP missing {slug}")
        continue
    with open(path) as f:
        html = f.read()
    if "keep-reading" in html:
        print(f"SKIP already has keep-reading: {slug}")
        continue
    others = [s for s in POSTS if s != slug]
    links = "\n".join(
        f'<li><a href="/blog/{s}/">{POSTS[s][0]}</a></li>' for s in others
    )
    block = f'''
<div class="keep-reading">
<h2>Keep reading</h2>
<ul>
{links}
</ul>
</div>
'''
    # insert before closing body tag
    html = html.replace("</body>", block + "</body>", 1)
    # add CSS once if missing
    if ".keep-reading" not in html.split("keep-reading")[0]:
        pass  # style added below via replace of </style>
    css = '''
.keep-reading{margin-top:48px;padding-top:24px;border-top:1px solid var(--line)}
.keep-reading h2{font-size:20px;margin-bottom:12px;border:none;padding:0}
.keep-reading ul{list-style:none;padding:0;margin:0;display:grid;gap:8px}
.keep-reading a{color:var(--accent);text-decoration:none}
.keep-reading a:hover{text-decoration:underline}
</style>'''
    html = html.replace("</style>", css, 1)
    with open(path, "w") as f:
        f.write(html)
    print(f"OK {slug}")
