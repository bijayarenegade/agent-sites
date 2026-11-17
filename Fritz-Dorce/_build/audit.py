"""Pre-launch audit for the v2 site. Run from the site folder."""
import json, os, re, sys
from html.parser import HTMLParser

issues, notes = [], []
PAGES = ["index.html", "about.html", "services.html", "contact.html", "404.html"]
CLEAN = {"./": "index.html", "about": "about.html", "services": "services.html", "contact": "contact.html",
         "/": "index.html", "/about": "about.html", "/services": "services.html", "/contact": "contact.html"}


def walk_ids(o, defined, refs):
    if isinstance(o, dict):
        if "@id" in o:
            (defined if len(o) > 1 else refs).add(o["@id"])
        for v in o.values():
            walk_ids(v, defined, refs)
    elif isinstance(o, list):
        for v in o:
            walk_ids(v, defined, refs)


for f in PAGES:
    h = open(f, encoding="utf-8").read()
    title = re.search(r"<title>(.*?)</title>", h).group(1).replace("&amp;", "&")
    desc = re.search(r'<meta name="description" content="([^"]*)"', h).group(1).replace("&amp;", "&")
    notes.append(f"{f}: title {len(title)}ch, description {len(desc)}ch")
    if len(title) > 65: issues.append((f, "title > 65 chars", title))
    if not 70 <= len(desc) <= 165: issues.append((f, "description length", len(desc)))
    if f != "404.html":
        if '<link rel="canonical"' not in h: issues.append((f, "no canonical"))
        if 'og:image' not in h: issues.append((f, "no og:image"))
    elif "noindex" not in h:
        issues.append((f, "404 should be noindex"))
    n1 = len(re.findall(r"<h1[ >]", h))
    if n1 != 1: issues.append((f, "h1 count", n1))
    prev = 0
    for lvl in map(int, re.findall(r"<h([1-6])[ >]", re.sub(r"<noscript>.*?</noscript>", "", h, flags=re.S))):
        if prev and lvl > prev + 1:
            issues.append((f, "heading skip", f"h{prev}->h{lvl}")); break
        prev = lvl
    for tag in re.findall(r"<img [^>]*>", h):
        if 'alt="' not in tag: issues.append((f, "img no alt", tag[:70]))
        if "width=" not in tag: issues.append((f, "img no width/height", tag[:70]))
        src = re.search(r'src="([^"]+)"', tag).group(1)
        if not src.startswith("http") and not os.path.exists(src): issues.append((f, "img missing", src))
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            data = json.loads(blk)
        except Exception as e:
            issues.append((f, "jsonld parse", str(e))); continue
        defined, refs = set(), set()
        walk_ids(data, defined, refs)
        for r in refs - defined:
            issues.append((f, "jsonld dangling @id", r))
        types = [n.get("@type") for n in data.get("@graph", [data])]
        notes.append(f"{f}: schema {types}")
    for href in re.findall(r'href="([^"]*)"', h):
        if re.match(r"(https?:|mailto:|tel:|#)", href): continue
        base = href.split("#")[0]
        target = CLEAN.get(base, base)
        if target and not os.path.exists(target): issues.append((f, "broken link", href))
        if base.endswith(".html") and f != "404.html": issues.append((f, "non-clean internal link", href))
    for m in re.finditer(r'<a [^>]*target="_blank"[^>]*>', h):
        if "noopener" not in m.group(0): issues.append((f, "target=_blank without noopener", m.group(0)[:80]))
    for bad in ["Doran", "Grohs", "Chris Young", "Bakersfield", "cta-image-s", "(305)", "healthliving", "lorem"]:
        if bad.lower() in h.lower(): issues.append((f, "leftover text", bad))
    ids = re.findall(r'\sid="([^"]+)"', h)
    d = {i for i in ids if ids.count(i) > 1}
    if d: issues.append((f, "duplicate id", d))

for f in ["robots.txt", "sitemap.xml", "vercel.json", "og-image.jpg", "favicon-32.png", "apple-touch-icon.png", "favicon.svg"]:
    if not os.path.exists(f): issues.append((f, "missing"))
json.load(open("vercel.json"))
for js in ["config.js", "app.js"]:
    t = open(js, encoding="utf-8").read()
    for bad in ["Doran", "Chris Young", "(305)", "healthliving"]:
        if bad in t: issues.append((js, "leftover text", bad))

print("\n".join(notes))
print("\nISSUES:" if issues else "\nno issues")
for i in issues: print(" ", i)
