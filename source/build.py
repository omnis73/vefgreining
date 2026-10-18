#!/usr/bin/env python3
"""Build the static vefgreining.com site from content/.

Usage:  python3 build.py OUTDIR [--preview] [--articles]

Production (default): writes two sites, OUTDIR/vefgreining.is/ (Icelandic, served
at www.vefgreining.is) and OUTDIR/vefgreining.com/ (English, served at
www.vefgreining.com). Links between the languages are absolute; links inside a
site are relative. Old addresses redirect to the right domain.

--preview writes one combined site (Icelandic at the root, English under /en/)
with links ending in index.html, so it can be clicked through from disk or in a
preview. Internally every page keeps this combined path ("en/..." for English).
"""
import json, os, re, shutil, sys, html, random, math
from urllib.parse import quote
from datetime import date
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
OUT = sys.argv[1]
PREVIEW = "--preview" in sys.argv
# Each language has its own domain. SITE is the Icelandic one (feed, combined preview).
BASE = {"is": "https://www.vefgreining.is", "en": "https://www.vefgreining.com"}
DOMAIN = {"is": "vefgreining.is", "en": "vefgreining.com"}
SITE = BASE["is"]
SPLIT = not PREVIEW
NEUTRAL = ("assets/", "wp-content/", "favicon")  # files present on both domains
CFG = json.load(open(os.path.join(CONTENT, "site.json"), encoding="utf-8"))
if PREVIEW: CFG["config"]["gtmId"] = CFG["config"]["ga4Id"] = ""  # keep preview visits out of real analytics
EN = CFG["en"]
# Articles (Fróðleikur) are switched off on the live site but kept in content/posts.json.
# Set "articles": true in site.json, or pass --articles, to bring them back.
ARTICLES = CFG["config"].get("articles", True) or "--articles" in sys.argv

ROOT = {"is": "", "en": "en/"}
NEWS = {"is": "news/", "en": "en/news/"}
LEGAL = {"is": "lagalegur-fyrirvari/", "en": "en/legal/"}
CV = {"is": "ferill/", "en": "en/cv/"}
EMAIL = CFG["config"]["email"]
PHONE = {"is": "825 8417", "en": "+354 825 8417"}

UI = {
 "is": {
  "skip": "Fara beint í efni", "menu": "Valmynd", "nav_label": "Aðalvalmynd", "services": "Þjónusta", "news": "Fróðleikur",
  "contact": "Hafa samband", "legal": "Lagalegur fyrirvari og vefkökur", "cookie_settings": "Stillingar vefkaka",
  "consent": "Má ég nota vefkökur frá Google Analytics til að sjá hvernig vefurinn er notaður? Engar slíkar kökur eru settar nema þú leyfir það.",
  "consent_more": "Nánar", "allow": "Leyfa mælingar", "decline": "Hafna", "consent_label": "Vefkökur",
  "other_lang": "English", "other_lang_short": "EN", "other_lang_label": "English version",
  "ua_nav": "War in Ukraine", "about": "Um mig", "theme_label": "Litaþema", "theme_blue": "Blátt", "theme_light": "Ljóst", "theme_dark": "Dökkt",
  "all_posts": "Allar greinar", "read_more": "Nánar", "read_more_about": "Nánar um", "service_crumb": "Þjónusta",
  "cta_h": "Viltu ræða verkefni?", "cta_call": "Hringdu í", "cta_or": "eða sendu póst á", "get_in_touch": "Hafðu samband",
  "other_services": "Önnur þjónusta", "in_other_lang": "", "dashboard": "Mælaborð",
  "mail_h": "Sendu mér línu", "mail_p": "Segðu mér í stuttu máli frá verkefninu og ég hef samband.",
  "mail_btn": "Senda tölvupóst", "mail_note": "Hnappurinn opnar póstforritið þitt með nýjum pósti til mín. Ef ekkert gerist geturðu sent beint á",
  "mail_subject": "Fyrirspurn af vefgreining.is",
 },
 "en": {
  "skip": "Skip to content", "menu": "Menu", "nav_label": "Main menu", "services": "Services", "news": "Articles",
  "contact": "Contact", "legal": "Legal notice and cookies", "cookie_settings": "Cookie settings",
  "consent": "May I use Google Analytics cookies to see how the site is used? No such cookies are set unless you allow it.",
  "consent_more": "Read more", "allow": "Allow analytics", "decline": "Decline", "consent_label": "Cookies",
  "other_lang": "Íslenska", "other_lang_short": "IS", "other_lang_label": "Íslensk útgáfa",
  "ua_nav": "Ukraine war dashboard", "about": "About", "theme_label": "Colour theme", "theme_blue": "Blue", "theme_light": "Light", "theme_dark": "Dark",
  "all_posts": "All articles", "read_more": "Read more", "read_more_about": "Read more about", "service_crumb": "Services",
  "cta_h": "Want to discuss a project?", "cta_call": "Call", "cta_or": "or email", "get_in_touch": "Get in touch",
  "other_services": "Other services", "in_other_lang": "In Icelandic", "dashboard": "Dashboard",
  "mail_h": "Send me a message", "mail_p": "Tell me briefly what it is about and I will get back to you.",
  "mail_btn": "Send an email", "mail_note": "The button opens your email program with a new message to me. If nothing happens, you can write directly to",
  "mail_subject": "Enquiry from vefgreining.com",
 },
}
# Messages the browser script shows (contact form, theme button)
JS_TEXT = {
 "is": {"invalid": "Fylltu út nafn og gilt netfang.", "mailto": "Póstforritið þitt opnast með skilaboðunum.", "sending": "Sendi…",
        "sent": "Skilaboðin eru send. Ég svara eins fljótt og ég get.",
        "failed": f"Skilaboðin fóru ekki. Sendu póst á {EMAIL} eða hringdu í 825 8417.", "subject": "Fyrirspurn af vefgreining.is"},
 "en": {"invalid": "Enter your name and a valid email address.", "mailto": "Your email program will open with the message.", "sending": "Sending…",
        "sent": "Message sent. I'll reply as soon as I can.",
        "failed": f"The message wasn't sent. Email {EMAIL} or call +354 825 8417.", "subject": "Enquiry from vefgreining.com"},
}
MONTHS = {"is": ["janúar","febrúar","mars","apríl","maí","júní","júlí","ágúst","september","október","nóvember","desember"],
          "en": ["January","February","March","April","May","June","July","August","September","October","November","December"]}
CATS_EN = {"Fróðleikur": "Insights", "Greining": "Analysis", "Lausnir": "Solutions", "COVID-19": "COVID-19", "Ukraine War": "Ukraine War"}

def fdate(d, lang):
    y, m, dd = map(int, d.split("-"))
    return f"{dd}. {MONTHS['is'][m-1]} {y}" if lang == "is" else f"{dd} {MONTHS['en'][m-1]} {y}"

def esc(s): return html.escape(s, quote=True)

def side(path):
    """Which language/domain a combined path belongs to."""
    return "en" if path == "en" or path.startswith("en/") else "is"

def local(path):
    """Path on its own domain: English pages drop the en/ prefix when the sites are split."""
    return path[3:] if SPLIT and side(path) == "en" else path

def absurl(path, lang=None):
    """Full public URL of a combined path (a file under assets/ or wp-content/ on the domain of `lang`)."""
    s = lang if (lang and path.startswith(NEUTRAL)) else side(path)
    return BASE[s] + "/" + (path[3:] if s == "en" and side(path) == "en" else path)

def rel(from_dir, to):
    """Link from a page living in from_dir ('' = root) to a combined site path.
    `to` is a folder path ending in '/' (a page) or a file path. Pages in the
    other language are on the other domain, so they get a full URL."""
    if SPLIT:
        if not to.startswith(NEUTRAL) and side(to) != side(from_dir):
            return absurl(to)
        if not to.startswith(NEUTRAL): to = local(to)
        from_dir = local(from_dir)
    depth = len([p for p in from_dir.split("/") if p])
    up = "../" * depth
    if to.endswith("/") or to == "":
        target = to
        if PREVIEW: target = to + "index.html"
        elif target == "": target = "./" if depth == 0 else ""
        return (up + target) or "./"
    return up + to

# ---------- shared chrome ----------
THEME_ICONS = {
    "blue": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect class="swatch" x="4" y="4" width="16" height="16" rx="4"/></svg>',
    "light": ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/>'
              '<path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>'),
    "dark": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6Z"/></svg>',
}

def theme_picker(lang):
    t = UI[lang]
    btns = "".join(f'<button type="button" data-set-theme="{k}" aria-pressed="{"true" if k == "blue" else "false"}" title="{t["theme_" + k]}">'
                   f'{THEME_ICONS[k]}<span class="theme-name">{t["theme_" + k]}</span></button>'
                   for k in ("blue", "light", "dark"))
    return f'<div class="themes" role="group" aria-label="{t["theme_label"]}">{btns}</div>'

def head(page_dir, title, desc, canonical, lang, og_image=None, alt=None):
    css = rel(page_dir, "assets/site.css")
    og = f'<meta property="og:image" content="{absurl(og_image, lang)}">' if og_image else ""
    canon = BASE[lang] + "/404.html" if canonical == "/404.html" else absurl(canonical.lstrip("/"), lang)
    alts = ""
    if alt:
        other = "en" if lang == "is" else "is"
        alts = (f'<link rel="alternate" hreflang="{lang}" href="{canon}">\n'
                f'<link rel="alternate" hreflang="{other}" href="{absurl(alt)}">\n')
    cfg = dict(CFG["config"], text=JS_TEXT[lang], lang=lang, domains=list(DOMAIN.values()))
    rss = f'<link rel="alternate" type="application/rss+xml" title="Vefgreining — fróðleikur" href="{SITE}/feed.xml">' if ARTICLES else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
{alts}<meta property="og:type" content="website">
<meta property="og:site_name" content="Vefgreining">
<meta property="og:locale" content="{'is_IS' if lang == 'is' else 'en_GB'}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
{og}
<meta name="theme-color" content="#0B3B7A">
<link rel="icon" href="{rel(page_dir, 'assets/favicon-32.png')}" sizes="32x32" type="image/png">
<link rel="icon" href="{rel(page_dir, 'assets/favicon-192.png')}" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{rel(page_dir, 'assets/favicon-180.png')}">
{rss}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,400..800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400&display=swap">
<link rel="stylesheet" href="{css}">
<script>(function(d){{d.classList.add("js");var t=null,q=/[?&]theme=(blue|light|dark)\\b/.exec(location.search);if(q){{t=q[1];try{{localStorage.setItem("vg-theme",t)}}catch(e){{}}}}else{{try{{t=localStorage.getItem("vg-theme")}}catch(e){{}}}}if(!t){{var m=/(?:^|;)vg-theme=(\\w+)/.exec(window.name||"");if(m)t=m[1]}}if(t!=="dark"&&t!=="light")t="blue";d.setAttribute("data-theme",t)}})(document.documentElement);window.VG_CONFIG={json.dumps(cfg, ensure_ascii=False)};</script>
</head>
<body>
<a class="skip" href="#content">{UI[lang]['skip']}</a>
"""

# Drawn flag: the emoji shows as the letters "UA" on Windows
FLAG_UA = ('<svg class="flag-ua" viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="1" fill="#0057B7"/>'
           '<rect y="1" width="3" height="1" fill="#FFD700"/></svg>')

def nav_links(page_dir, lang, home, cur):
    t = UI[lang]
    ua = f'<a class="nav-ua" href="https://ukraine.vefgreining.com" lang="en" data-track="dashboard_click">{FLAG_UA}{t["ua_nav"]}</a>'
    if lang == "en":
        # English visitors come for the dashboard: it leads, the consulting site stays in the background
        return "\n      ".join([ua, f'<a href="{home}#about">{t["about"]}</a>', f'<a href="{home}#contact">{t["contact"]}</a>'])
    return "\n      ".join([f'<a href="{home}#features">{t["services"]}</a>',
                             *([f'<a href="{rel(page_dir, NEWS[lang])}"{cur("news")}>{t["news"]}</a>'] if ARTICLES else []),
                             f'<a href="{home}#contact">{t["contact"]}</a>', ua])

def header(page_dir, lang, current=None, alt=None):
    t = UI[lang]
    home = rel(page_dir, ROOT[lang])
    other = "en" if lang == "is" else "is"
    alt_href = rel(page_dir, alt if alt is not None else ROOT[other])
    def cur(k): return ' aria-current="page"' if current == k else ""
    return f"""<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{home}"><img class="logo logo-light" src="{rel(page_dir, 'assets/logo.png')}" alt="Vefgreining – Web Analytics" width="199" height="48"><img class="logo logo-dark" src="{rel(page_dir, 'assets/logo-dark.png')}" alt="Vefgreining – Web Analytics" width="199" height="48"></a>
    <nav class="nav" id="nav" aria-label="{t['nav_label']}">
      {nav_links(page_dir, lang, home, cur)}
      {theme_picker(lang)}
    </nav>
    <div class="tools">
      <a class="lang-switch" href="{alt_href}" hreflang="{other}" lang="{other}" aria-label="{t['other_lang_label']}"><span class="long">{t['other_lang']}</span><span class="short" aria-hidden="true">{t['other_lang_short']}</span></a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav">{t['menu']}</button>
    </div>
  </div>
</header>
"""

def footer(page_dir, lang):
    t = UI[lang]
    return f"""<footer class="site-foot">
  <div class="wrap">
    <span>© {date.today().year} Vefgreining · Ragnar Bjartur Guðmundsson</span>
    <span class="foot-links">
      <a href="{rel(page_dir, LEGAL[lang])}">{t['legal']}</a>
      <button type="button" class="linklike" data-open-consent>{t['cookie_settings']}</button>
    </span>
  </div>
</footer>
<div class="consent" id="consent" role="dialog" aria-label="{t['consent_label']}" hidden>
  <p>{t['consent']} <a href="{rel(page_dir, LEGAL[lang])}">{t['consent_more']}</a></p>
  <div class="btns">
    <button type="button" class="btn" data-consent="granted">{t['allow']}</button>
    <button type="button" class="btn btn-ghost" data-consent="denied">{t['decline']}</button>
  </div>
</div>
<script src="{rel(page_dir, 'assets/site.js')}" defer></script>
</body>
</html>
"""

def page(page_dir, lang, title, desc, canonical, body, current=None, og_image=None, alt=None):
    return head(page_dir, title, desc, canonical, lang, og_image, alt) + header(page_dir, lang, current, alt) + \
        f'<main id="content">\n{body}\n</main>\n' + footer(page_dir, lang)

def write(path, text, lang=None):
    """Write a page by its combined path, or (with lang) a file at the root of that language's site."""
    if SPLIT:
        full = os.path.join(OUT, DOMAIN[lang], path) if lang else os.path.join(OUT, DOMAIN[side(path)], local(path))
    else:
        full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)

def img_url(page_dir, path):
    return rel(page_dir, quote(path))

# ---------- language-specific content ----------
def L(lang):
    """Front-page content for a language: Icelandic is the top level of site.json, English overrides it."""
    if lang == "is":
        return {k: CFG[k] for k in ("hero", "process", "services", "figures", "case", "home")} | {"clients": CFG["clients"]}
    clients = [dict(c, name=EN["client_names"].get(c["name"], c["name"])) for c in CFG["clients"]]
    return {k: EN[k] for k in ("hero", "process", "services", "figures", "case", "home")} | {"clients": clients}

# ---------- hero chart ----------
def hero_chart(lang):
    c = L(lang)
    W, H = 1200, 380
    top, bot = 70, H - 40
    rnd = random.Random(7)
    n = 60
    pts = []
    for i in range(n):
        t = i / (n - 1)
        base = 0.12 + 0.03 * math.sin(i * 0.9)
        if t > 0.22: base += 0.66 * ((t - 0.22) / 0.78) ** 1.7
        v = base + rnd.uniform(-0.035, 0.035) + (0.03 * math.sin(i * 2.3))
        pts.append((round(30 + t * (W - 60), 1), round(bot - v * (bot - top), 1)))
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    area = d + f" L{pts[-1][0]},{bot} L{pts[0][0]},{bot} Z"
    grid = "".join(f'<line class="gridline" x1="30" x2="{W-30}" y1="{round(top + k*(bot-top)/3)}" y2="{round(top + k*(bot-top)/3)}"/>' for k in range(4))
    idx = [12, 24, 38, 54]
    flags = []
    for k, (i, st) in enumerate(zip(idx, c["process"])):
        x, y = pts[i]
        anchor = "end" if k == 3 else "start"
        span = range(i - 9, i + 1) if anchor == "end" else range(i, min(n, i + 12))
        ly = max(22, min(pts[j][1] for j in span) - 34)
        tx = x + 10 if anchor == "start" else x - 10
        flags.append(f'<g class="flag" style="--d:{0.6 + k*0.5:.2f}s"><line class="lead" x1="{x}" x2="{x}" y1="{ly + 6}" y2="{y - 6}"/>'
                     f'<circle cx="{x}" cy="{y}" r="6"/>'
                     f'<text class="label" x="{tx}" y="{ly}" text-anchor="{anchor}"><tspan class="n">{k+1}. </tspan>{esc(st)}</text>'
                     f'<text class="num" x="{x}" y="{y - 22}" text-anchor="middle">{k+1}</text></g>')
    steps = "".join(f"<li>{esc(st)}</li>" for st in c["process"])
    h = c["hero"]
    return f"""<figure class="chart" role="img" aria-label="{esc(h['chart_label'])}">
<svg viewBox="0 0 {W} {H}" aria-hidden="true">
{grid}<path class="area" d="{area}"/><path class="trend" d="{d}"/>{''.join(flags)}
<text class="axis" x="30" y="{H-12}">{esc(h['before'])}</text><text class="axis" x="{W-30}" y="{H-12}" text-anchor="end">{esc(h['now'])}</text></svg>
<ol class="chart-steps">{steps}</ol>
<figcaption class="chart-caption">{esc(h['caption'])}</figcaption>
</figure>"""

# Service icons. Parts carry classes the stylesheet animates: draw (line drawing),
# grow-y / grow-x (bars growing), pop (dots appearing), ring (pulsing accent).
SERVICE_GLYPHS = [
    '<svg class="glyph" viewBox="0 0 144 40" aria-hidden="true"><path class="soft" d="M2 38H142"/>'
    '<path class="draw" pathLength="1" d="M2 32 18 30 32 33 46 26 60 28 74 20 88 22 102 14 116 16 130 9"/>'
    '<circle class="ring" cx="130" cy="9" r="4"/><circle class="dot pop" style="--i:9" cx="130" cy="9" r="4"/></svg>',
    '<svg class="glyph" viewBox="0 0 144 40" aria-hidden="true"><path class="soft" d="M2 38H142"/>'
    + "".join(f'<rect class="bar grow-y" style="--i:{k}" x="{6+k*20}" y="{38-h}" width="9" height="{h}" rx="1.5"/>' for k, h in enumerate([8, 16, 28, 34, 24, 13, 6]))
    + '</svg>',
    '<svg class="glyph" viewBox="0 0 144 40" aria-hidden="true"><path class="soft" d="M2 38H142"/>'
    + "".join(f'<rect class="bar grow-x" style="--i:{k}" x="2" y="{4+k*11}" width="{w}" height="7" rx="1.5"/>' for k, w in enumerate([88, 118, 58]))
    + '<circle class="ring" cx="128" cy="18.5" r="4"/><circle class="dot pop" style="--i:4" cx="128" cy="18.5" r="4"/></svg>',
    '<svg class="glyph" viewBox="0 0 144 40" aria-hidden="true">'
    '<path class="draw" pathLength="1" d="M10 30 46 12 82 28 118 10"/><path class="soft draw" pathLength="1" style="--i:6" d="M118 10 136 34"/>'
    '<circle class="node pop" style="--i:0" cx="10" cy="30" r="5"/><circle class="node pop" style="--i:2" cx="46" cy="12" r="5"/>'
    '<circle class="node pop" style="--i:4" cx="82" cy="28" r="5"/><circle class="ring" cx="118" cy="10" r="5"/><circle class="dot pop" style="--i:6" cx="118" cy="10" r="5"/></svg>',
]

# ---------- posts ----------
POSTS = json.load(open(os.path.join(CONTENT, "posts.json"), encoding="utf-8"))
POSTS.sort(key=lambda p: p["date"], reverse=True)

def clean_body(raw, page_dir, lang="is"):
    s = BeautifulSoup(raw, "html.parser")
    root = s.find(class_="entry-content") or s
    for t in root.find_all(True):
        cls = t.get("class") or []
        keep = [c for c in cls if c in ("alignleft", "alignright", "aligncenter")]
        for a in ("class", "style", "srcset", "sizes", "decoding", "fetchpriority", "id"):
            if a in t.attrs and not (a == "style" and t.name == "iframe"): del t[a]
        if keep: t["class"] = keep
        if t.name == "img":
            src = t.get("src", "")
            m = re.search(r"vefgreining\.com/(wp-content/.*)$", src)
            if m:
                p = m.group(1)
                if not os.path.exists(os.path.join(HERE, "media", p)):
                    print("MISSING IMAGE", p, file=sys.stderr)
                t["src"] = img_url(page_dir, p)
            t["loading"] = "lazy"
        if t.name == "a" and t.get("href"):
            h = t["href"]
            m = re.match(r"https?://(www\.)?vefgreining\.com/(.*)$", h)
            if m and m.group(2).startswith("wp-content"):
                t["href"] = rel(page_dir, quote(m.group(2)))
            elif m:
                pth, _, frag = m.group(2).partition("#")
                if pth and not pth.endswith("/"): pth += "/"
                t["href"] = rel(page_dir, pth) + ("#" + frag if frag else "")
            if t.get("target") == "_blank": t["rel"] = "noopener"
    for f in root.find_all("iframe"):
        src = f.get("src", "").replace("datastudio.google.com", "lookerstudio.google.com")
        h = f.get("height", "1200")
        wrap = s.new_tag("div", attrs={"class": "embed"})
        nf = s.new_tag("iframe", attrs={"src": src, "height": h, "loading": "lazy", "allowfullscreen": "",
                                       "title": UI[lang]["dashboard"], "sandbox": "allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"})
        wrap.append(nf)
        f.replace_with(wrap)
    for p in root.find_all("p"):
        if not p.get_text(strip=True).replace("\xa0", "") and not p.find(["img", "iframe", "a"]):
            p.decompose()
    return root.decode_contents().strip()

def post_list(page_dir, posts, lang):
    items = []
    for p in posts:
        thumb = f'<img class="thumb" src="{img_url(page_dir, p["thumb"])}" alt="" loading="lazy" width="300" height="150">' if p.get("thumb") else '<span class="thumb"></span>'
        plang = p.get("lang", "is")
        if lang == "en":
            title = p.get("en_title", p["title"]); excerpt = p.get("en_excerpt", p["excerpt"])
            cats = [CATS_EN.get(c, c) for c in p["cats"]]
            note = f'<span class="lang-note">{UI["en"]["in_other_lang"]}</span>' if plang == "is" else ""
            hreflang = ' hreflang="is"' if plang == "is" else ""
        else:
            title, excerpt, cats, note, hreflang = p["title"], p["excerpt"], p["cats"], "", ""
        la = f' lang="{plang}"' if plang != lang and lang == "is" else ""
        href = rel(page_dir, p["path"])
        items.append(f"""<li class="post-item"{la}>
  <a href="{href}" tabindex="-1" aria-hidden="true">{thumb}</a>
  <div>
    <div class="meta"><time datetime="{p['date']}">{fdate(p['date'], lang)}</time><span class="cats">{esc(', '.join(cats))}</span>{note}</div>
    <h3><a href="{href}"{hreflang}>{esc(title)}</a></h3>
    <p>{esc(excerpt)}</p>
  </div>
</li>""")
    return '<ul class="posts">\n' + "\n".join(items) + "\n</ul>"

# ---------- pages ----------
def ukraine_feature(d):
    u = EN["ukraine"]
    bsky = next(s["url"] for s in CFG["social"] if s["name"] == "Bluesky")
    topics = "".join(f"<li>{esc(t)}</li>" for t in u["topics"])
    return f"""<section class="ua" aria-labelledby="ua-h">
  <div class="wrap ua-inner">
    <div class="ua-text">
      <p class="ua-status"><span class="live-dot" aria-hidden="true"></span>{esc(u['status'])}</p>
      <h1 id="ua-h">{esc(u['title'])}</h1>
      <p class="ua-lede">{esc(u['lede'])}</p>
      <ul class="ua-topics">{topics}</ul>
      <div class="ua-actions">
        <a class="btn btn-ua" href="{u['url']}" data-track="dashboard_click">{esc(u['open'])}</a>
        <a class="ua-link" href="{bsky}" rel="me">{esc(u['follow'])}</a>
      </div>
      <p class="ua-meta">{esc(u['languages'])} {esc(u['users'])}</p>
    </div>
    <a class="ua-map" href="{u['url']}" tabindex="-1" aria-hidden="true" data-track="dashboard_click"><img src="{rel(d, 'assets/ukraine-map.jpg')}" alt="" width="570" height="390"></a>
  </div>
</section>"""

def build_home_en():
    d = ROOT["en"]
    u = EN["ukraine"]
    a = EN["about"]
    services = "".join(f'<li><a href="{rel(d, s["more"])}">{esc(s["title"])}</a></li>' for s in EN["services"])
    soc = "".join(f'<li><a href="{esc(s["url"])}" rel="me">{esc(s["name"])}</a></li>' for s in CFG["social"])
    body = f"""{ukraine_feature(d)}

<section class="section about-en" id="about" aria-labelledby="about-h">
  <div class="wrap about-grid">
    <img class="about-photo" src="{img_url(d, 'wp-content/uploads/2016/09/ragnar.gudmundsson-transparent.png')}" alt="Ragnar Bjartur Guðmundsson" width="144" height="144" loading="lazy">
    <div>
      <h2 id="about-h">{esc(a['title'])}</h2>
      <p class="about-lede">{esc(a['lede'])}</p>
      <p>{esc(a['work'])}</p>
      <ul class="work-links">{services}</ul>
    </div>
  </div>
</section>

<section class="section" id="contact" aria-labelledby="contact-h">
  <div class="wrap">
    <div class="section-head"><h2 id="contact-h">{esc(a['contact_h'])}</h2><p>{esc(a['contact_p'])}</p></div>
    <div class="contact">
      <div class="about">
        <ul class="reach">
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li><a href="tel:+3548258417">{PHONE['en']}</a></li>
        </ul>
        <ul class="social">{soc}</ul>
      </div>
      {contact_form('en')}
    </div>
  </div>
</section>
"""
    jsonld = {"@context": "https://schema.org", "@type": "Dataset", "name": u["title"], "description": u["lede"],
              "url": u["url"], "isAccessibleForFree": True, "inLanguage": ["en", "uk", "ru"],
              "creator": {"@type": "Person", "name": "Ragnar Bjartur Guðmundsson", "sameAs": [s["url"] for s in CFG["social"]]}}
    html_ = page(d, "en", a["page_title"], a["page_description"], "/" + d, body, og_image="assets/ukraine-dashboard.jpg", alt=ROOT["is"])
    html_ = html_.replace("</head>", f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n</head>', 1)
    write(d + "index.html", html_)

def contact_form(lang):
    """Contact box: a button that opens the visitor's own email program, with the address shown as text too."""
    t = UI[lang]
    href = f"mailto:{EMAIL}?subject={quote(t['mail_subject'])}"
    return f"""<div class="mail-box">
        <h3>{t['mail_h']}</h3>
        <p>{t['mail_p']}</p>
        <p><a class="btn" href="{href}" data-track="email_click">{t['mail_btn']}</a></p>
        <p class="mail-note">{t['mail_note']} <span class="mail-addr">{EMAIL}</span></p>
      </div>"""

def build_home(lang):
    if lang == "en": return build_home_en()
    d = ROOT[lang]
    t = UI[lang]
    c = L(lang)
    h, hm = c["hero"], c["home"]
    svc = "".join(f'<div class="service" data-animate>{g}<h3><a href="{rel(d, s["more"])}">{esc(s["title"])}</a></h3><p>{esc(s["text"])}</p>'
                  f'<p class="service-more"><a href="{rel(d, s["more"])}" aria-label="{t["read_more_about"]} {esc(s["title"])}">{t["read_more"]}</a></p></div>'
                  for g, s in zip(SERVICE_GLYPHS, c["services"]))
    clients = "".join(f'<li><a href="{esc(x["url"])}">{esc(x["name"])}</a></li>' for x in c["clients"])
    def count_attr(v):
        num = re.sub(r"[^0-9]", "", v); suffix = v[len(v.rstrip("+")):]
        return f' data-count="{num}" data-suffix="{suffix}"'
    figs = "".join(f'<tr><th scope="row">{esc(f["label"])}</th><td{count_attr(f["value"])}>{esc(f["value"])}</td></tr>' for f in c["figures"])
    case = c["case"]
    soc = "".join(f'<li><a href="{esc(s["url"])}" rel="me">{esc(s["name"])}</a></li>' for s in CFG["social"])
    news_posts = POSTS[:3]
    news_section = (f"""<section class="section" id="news" aria-labelledby="news-h">
  <div class="wrap">
    <div class="section-head"><h2 id="news-h">{esc(hm['news_h'])}</h2><p>{esc(hm['news_p'])}</p></div>
    {post_list(d, news_posts, lang)}
    <p class="more"><a href="{rel(d, NEWS[lang])}">{t['all_posts']} ({len(POSTS)})</a></p>
  </div>
</section>""") if ARTICLES else ""
    ua = ukraine_feature(d) if lang == "en" else ""
    htag = "h2" if ua else "h1"
    intro = f'<p class="hero-intro">{esc(EN["ukraine"]["intro"])}</p>' if ua else ""
    body = f"""{ua}
<section class="hero wrap{' hero-second' if ua else ''}">
  {intro}<{htag} class="hero-title">{esc(h['title'])}</{htag}>
  <p class="lede">{esc(h['lede'])}</p>
  <div class="actions"><a class="btn" href="#contact">{t['get_in_touch']}</a><a href="#features">{esc(h['see_services'])}</a></div>
  {hero_chart(lang)}
</section>

<section class="section" id="clients" aria-labelledby="clients-h">
  <div class="wrap">
    <div class="section-head"><h2 id="clients-h">{esc(hm['clients_h'])}</h2></div>
    <ul class="clients">{clients}</ul>
    <p class="clients-note">{esc(hm['clients_note'])}</p>
  </div>
</section>

<section class="section" id="features" aria-labelledby="features-h">
  <div class="wrap">
    <div class="section-head"><h2 id="features-h">{esc(hm['services_h'])}</h2></div>
    <div class="services">{svc}</div>
  </div>
</section>

<section class="section" id="work" aria-labelledby="work-h">
  <div class="wrap">
    <div class="section-head"><h2 id="work-h">{esc(hm['work_h'])}</h2>
      <p>{esc(hm['work_p'])}</p></div>
    <div class="case">
      <a href="{rel(d, case['path'])}" tabindex="-1" aria-hidden="true"><img src="{img_url(d, case['image'])}" alt="" width="578" height="433" loading="lazy"></a>
      <div>
        <h3><a href="{rel(d, case['path'])}">{esc(case['title'])}</a></h3>
        <p>{esc(case['summary'])}</p>
        <p><a href="{rel(d, case['path'])}">{esc(hm['view_dashboard'])}</a></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="figures" aria-labelledby="figures-h">
  <div class="wrap">
    <div class="section-head"><h2 id="figures-h">{esc(hm['figures_h'])}</h2></div>
    <table class="figures" data-animate data-sep="{'.' if lang == 'is' else ','}"><tbody>{figs}</tbody></table>
  </div>
</section>

{news_section}

<section class="section" id="contact" aria-labelledby="contact-h">
  <div class="wrap">
    <div class="section-head"><h2 id="contact-h">{esc(hm['contact_h'])}</h2><p>{esc(hm['contact_p'])}</p></div>
    <div class="contact">
      <div class="about">
        <img class="about-photo" src="{img_url(d, 'wp-content/uploads/2016/09/ragnar.gudmundsson-transparent.png')}" alt="Ragnar Bjartur Guðmundsson" width="144" height="144" loading="lazy">
        <h3>Ragnar Bjartur Guðmundsson</h3>
        <p class="role">{esc(hm['role'])}</p>
        <p>{esc(hm['about'])}</p>
        <ul class="reach">
          <li><a href="tel:+3548258417">{PHONE[lang]}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        </ul>
        <ul class="social">{soc}<li><a href="{rel(d, CV[lang])}">{esc(hm['cv'])}</a></li></ul>
      </div>
      {contact_form(lang)}
    </div>
  </div>
</section>
"""
    jsonld = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": "Vefgreining",
              "url": absurl(d), "email": EMAIL, "telephone": "+354 825 8417",
              "founder": {"@type": "Person", "name": "Ragnar Bjartur Guðmundsson"},
              "sameAs": [s["url"] for s in CFG["social"]]}
    other = ROOT["en" if lang == "is" else "is"]
    html_ = page(d, lang, hm["title"], hm["description"], "/" + d, body, alt=other)
    html_ = html_.replace("</head>", f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n</head>', 1)
    write(d + "index.html", html_)

def build_news(lang):
    d = NEWS[lang]
    hm = L(lang)["home"]
    intro = f'<p class="lede">{esc(hm["news_intro"])}</p>' if hm.get("news_intro") else ""
    body = f"""<div class="article wrap">
  <header><h1>{esc(hm['news_title'])}</h1>{intro}</header>
  {post_list(d, POSTS, lang)}
</div>"""
    other = NEWS["en" if lang == "is" else "is"]
    write(d + "index.html", page(d, lang, hm["news_title"] + " — Vefgreining", hm["news_description"], "/" + d, body, current="news", alt=other))

def article(d, lang, p, title, body_html, wide=False):
    t = UI[lang]
    cats = [CATS_EN.get(c, c) for c in p.get("cats", [])] if lang == "en" else p.get("cats", [])
    meta = f'<div class="meta"><time datetime="{p["date"]}">{fdate(p["date"], lang)}</time><span class="cats">{esc(", ".join(cats))}</span></div>' if p.get("date") else ""
    crumb = f'<a class="crumb" href="{rel(d, NEWS[lang])}">{t["news"]}</a>' if p.get("date") else ""
    all_link = f'<a href="{rel(d, NEWS[lang])}">{t["all_posts"]}</a>' if ARTICLES else ""
    back = f'<div class="article-foot">{all_link}<a href="{rel(d, ROOT[lang])}#contact">{t["contact"]}</a></div>'
    return f"""<article class="article wrap">
  <header>{crumb}<h1>{esc(title)}</h1>{meta}</header>
  <div class="prose{' embed-wide' if wide else ''}">{body_html}</div>
  {back}
</article>"""

def build_posts():
    for p in POSTS:
        d = p["path"]
        lang = p.get("lang", "is")
        body = clean_body(p["html"], d, lang)
        if p.get("notice"): body = f'<aside class="notice"><p>{p["notice"]}</p></aside>' + body
        alt = NEWS["en" if lang == "is" else "is"]
        html_ = page(d, lang, p["title"] + " — Vefgreining", p["excerpt"], "/" + d, article(d, lang, p, p["title"], body),
                     current="news", og_image=p.get("thumb"), alt=None)
        # Articles exist in one language only; the switch goes to the other language's article list
        html_ = html_.replace(f'class="lang-switch" href="{rel(d, ROOT["en" if lang == "is" else "is"])}"', f'class="lang-switch" href="{rel(d, alt)}"', 1)
        write(d + "index.html", html_)

def service_page(d, lang, k, body):
    t = UI[lang]
    services = L(lang)["services"]
    s = services[k]
    others = "".join(f'<li class="service" data-animate>{SERVICE_GLYPHS[j]}<h3><a href="{rel(d, o["more"])}">{esc(o["title"])}</a></h3><p>{esc(o["text"])}</p></li>'
                     for j, o in enumerate(services) if j != k)
    return f"""<article class="article wrap service-page">
  <header>
    <a class="crumb" href="{rel(d, ROOT[lang])}#features">{t['service_crumb']}</a>
    <div class="service hero-glyph" data-animate>{SERVICE_GLYPHS[k]}</div>
    <h1>{esc(s["title"])}</h1>
    <p class="lede">{esc(s["text"])}</p>
  </header>
  <div class="prose">{body}</div>
  <aside class="cta" aria-labelledby="cta-h">
    <h2 id="cta-h">{t['cta_h']}</h2>
    <p>{t['cta_call']} <a href="tel:+3548258417">{PHONE[lang]}</a> {t['cta_or']} <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    <p><a class="btn" href="{rel(d, ROOT[lang])}#contact">{t['get_in_touch']}</a></p>
  </aside>
  <section class="others" aria-labelledby="others-h">
    <h2 id="others-h">{t['other_services']}</h2>
    <ul class="services">{others}</ul>
  </section>
</article>"""

def all_pages():
    for sp in CFG["pages"]: yield sp, sp.get("lang", "is")
    for sp in EN["pages"]: yield sp, "en"

def build_static_pages():
    for sp, lang in all_pages():
        d = sp["path"]
        raw = open(os.path.join(CONTENT, sp["file"]), encoding="utf-8").read()
        body = clean_body(raw, d, lang)
        if "service" in sp:
            main = service_page(d, lang, sp["service"], body)
            title = L(lang)["services"][sp["service"]]["title"]
        else:
            main = article(d, lang, {}, sp["title"], body, wide=sp.get("wide", False))
            title = sp["title"]
        html_ = page(d, lang, title + " — Vefgreining", sp["description"], "/" + d, main, og_image=sp.get("image"), alt=sp.get("alt"))
        write(d + "index.html", html_)

def build_404():
    # The 404 page is served at any depth, so it uses root-absolute links
    def fix(h): return re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:)(\./)?', r'\1="/', h)
    en_home = BASE["en"] + "/" if SPLIT else "/en/"
    body = f"""<div class="notfound wrap"><h1>Þessi síða fannst ekki</h1>
<p>Slóðin gæti hafa breyst þegar vefurinn var endurnýjaður. Prófaðu <a href="/">forsíðuna</a>.</p>
<p lang="en">This page wasn't found. Try the <a href="{en_home}">English home page</a>.</p></div>"""
    write("404.html", fix(page("", "is", "Síða fannst ekki — Vefgreining", "Síðan fannst ekki.", "/404.html", body)), "is" if SPLIT else None)
    if SPLIT:
        body = f"""<div class="notfound wrap"><h1>Page not found</h1>
<p>The address may have changed when the site was rebuilt. Try the <a href="/">home page</a>, or the <a href="https://ukraine.vefgreining.com/" data-track="dashboard_click">Ukraine war dashboard</a>.</p>
<p lang="is">Síðan fannst ekki. Íslenski vefurinn er á <a href="{BASE['is']}/">vefgreining.is</a>.</p></div>"""
        write("404.html", fix(page("en/", "en", "Page not found — Vefgreining", "Page not found.", "/404.html", body)), "en")

def build_meta_combined():
    urls = ["/", "/en/"] + ["/" + sp["path"] for sp, _ in all_pages()]
    if ARTICLES: urls += ["/news/", "/en/news/"] + ["/" + p["path"] for p in POSTS]
    sm = "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    # Cloudflare Pages / Netlify response headers: basic security headers and caching
    write("_headers", """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/assets/*
  Cache-Control: public, max-age=86400

/wp-content/*
  Cache-Control: public, max-age=2592000
""")
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE}/{p['path']}</link><guid>{SITE}/{p['path']}</guid>"
                    f"<pubDate>{date.fromisoformat(p['date']).strftime('%a, %d %b %Y')} 12:00:00 +0000</pubDate><description>{esc(p['excerpt'])}</description></item>" for p in POSTS)
    if ARTICLES: write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Vefgreining</title><link>{SITE}/</link><description>Fróðleikur og tilkynningar</description><language>is</language>{items}</channel></rss>\n')
    # Redirects for old WordPress addresses (Netlify / Cloudflare Pages format, plus Apache .htaccess)
    news = "/news/" if ARTICLES else "/"
    rules = [("/category/*", news), ("/feed/*", "/feed.xml" if ARTICLES else "/"), ("/feed", "/feed.xml" if ARTICLES else "/"), ("/news/page/*", news),
             ("/wp-admin/*", "/"), ("/wp-login.php", "/"), ("/greinar/*", news), ("/blog/*", news)] + \
            [(f"/{x}/*", "/") for x in ("sample-page","home","contact-us","our-history","our-achievements","our-vision","service-title-2","service-title-3","service-title-4","shop","cart","checkout","my-account")]
    if not ARTICLES:
        # Old article addresses: the dashboard article goes to the dashboard, the rest to the home page
        ua = next(p["path"] for p in POSTS if "ukraine" in p["path"])
        rules = [(f"/{ua}*", "https://ukraine.vefgreining.com/"), (f"/{ua.rstrip('/')}", "https://ukraine.vefgreining.com/")] + rules
        rules += [("/news/*", "/"), ("/news", "/"), ("/en/news/*", "/en/"), ("/en/news", "/en/")]
        rules += [(f"/{y}/*", "/") for y in sorted({p["path"][:4] for p in POSTS})]
    write("_redirects", "".join(f"{a} {b} 301\n" for a, b in rules))
    n = "/news/" if ARTICLES else "/"
    ht = ["ErrorDocument 404 /404.html", "RewriteEngine On",
          "RewriteCond %{HTTP_HOST} ^vefgreining\\.com$ [NC]", "RewriteRule ^(.*)$ https://www.vefgreining.com/$1 [R=301,L]"]
    if not ARTICLES:
        ua = next(p["path"] for p in POSTS if "ukraine" in p["path"])
        years = "|".join(sorted({p["path"][:4] for p in POSTS}))
        ht += [f"RewriteRule ^{ua.rstrip('/')}/?$ https://ukraine.vefgreining.com/ [R=301,L]",
               "RewriteRule ^en/news(/.*)?$ /en/ [R=301,L]", "RewriteRule ^news(/.*)?$ / [R=301,L]",
               f"RewriteRule ^({years})/ / [R=301,L]"]
    ht += [f"RewriteRule ^category/ {n} [R=301,L]", f"RewriteRule ^feed/?$ {'/feed.xml' if ARTICLES else '/'} [R=301,L]",
           f"RewriteRule ^news/page/ {n} [R=301,L]", "RewriteRule ^(wp-admin|wp-login\\.php) / [R=301,L]",
           f"RewriteRule ^(greinar|blog)/?$ {n} [R=301,L]",
           "RewriteRule ^(sample-page|home|contact-us|our-history|our-achievements|our-vision|service-title-[234]|shop|cart|checkout|my-account)/?$ / [R=301,L]"]
    write(".htaccess", "\n".join(ht) + "\n")


HEADERS = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/assets/*
  Cache-Control: public, max-age=86400

/wp-content/*
  Cache-Control: public, max-age=2592000
"""

def build_meta_split():
    """Sitemaps, robots, headers and redirects for the two domains."""
    is_pages = [sp["path"] for sp, l in all_pages() if side(sp["path"]) == "is"]
    en_pages = [local(sp["path"]) for sp, l in all_pages() if side(sp["path"]) == "en"]
    clash = set(is_pages) & set(en_pages)
    assert not clash, f"Same address on both domains: {clash}"
    for lang, pages in (("is", is_pages), ("en", en_pages)):
        urls = [BASE[lang] + "/"] + [BASE[lang] + "/" + x for x in pages]
        if ARTICLES and lang == "is": urls += [SITE + "/news/"] + [SITE + "/" + p["path"] for p in POSTS]
        write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n", lang)
        write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE[lang]}/sitemap.xml\n", lang)
        write("_headers", HEADERS, lang)
    if ARTICLES:
        items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE}/{p['path']}</link><guid>{SITE}/{p['path']}</guid>"
                        f"<pubDate>{date.fromisoformat(p['date']).strftime('%a, %d %b %Y')} 12:00:00 +0000</pubDate><description>{esc(p['excerpt'])}</description></item>" for p in POSTS)
        write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Vefgreining</title><link>{SITE}/</link><description>Fróðleikur og tilkynningar</description><language>is</language>{items}</channel></rss>\n', "is")

    # Old WordPress addresses. These were all on the Icelandic site, so on vefgreining.com they go to vefgreining.is.
    news = "/news/" if ARTICLES else "/"
    feed = "/feed.xml" if ARTICLES else "/"
    old = [("/category/*", news), ("/feed/*", feed), ("/feed", feed), ("/news/page/*", news),
           ("/wp-admin/*", "/"), ("/wp-login.php", "/"), ("/greinar/*", news), ("/blog/*", news)] + \
          [(f"/{x}/*", "/") for x in ("sample-page","home","contact-us","our-history","our-achievements","our-vision","service-title-2","service-title-3","service-title-4","shop","cart","checkout","my-account")]
    ua_dash = "https://ukraine.vefgreining.com/"
    first = []
    if not ARTICLES:
        # Old article addresses: the dashboard article goes to the dashboard, the rest to the home page
        ua = next(p["path"] for p in POSTS if "ukraine" in p["path"])
        first = [(f"/{ua}*", ua_dash), (f"/{ua.rstrip('/')}", ua_dash)]
        old += [("/news/*", "/"), ("/news", "/")] + [(f"/{y}/*", "/") for y in sorted({p["path"][:4] for p in POSTS})]
    en = BASE["en"]; is_ = BASE["is"]

    # vefgreining.is: the English pages used to be under /en/
    rules_is = first + [("/en/*", en + "/:splat"), ("/en", en + "/")] + old
    # vefgreining.com: English moved from /en/ to the root; every Icelandic address moves to vefgreining.is
    rules_en = first + [("/en/news/*", "/"), ("/en/news", "/"), ("/en/*", "/:splat"), ("/en", "/")]
    for x in is_pages:
        rules_en += [(f"/{x}*", f"{is_}/{x}:splat"), (f"/{x.rstrip('/')}", f"{is_}/{x}")]
    if ARTICLES:
        rules_en += [("/news/*", is_ + "/news/:splat"), ("/news", is_ + "/news/")] + \
                    [(f"/{y}/*", f"{is_}/{y}/:splat") for y in sorted({p["path"][:4] for p in POSTS})]
    rules_en += [(a, is_ + b if b.startswith("/") else b) for a, b in old]
    for lang, rules in (("is", rules_is), ("en", rules_en)):
        write("_redirects", "".join(f"{a} {b} 301\n" for a, b in rules), lang)

def copy_assets():
    if SPLIT:
        for lang in ("is", "en"): copy_assets_to(os.path.join(OUT, DOMAIN[lang]))
    else:
        copy_assets_to(OUT)

def copy_assets_to(OUT):
    shutil.copytree(os.path.join(HERE, "media", "wp-content"), os.path.join(OUT, "wp-content"), dirs_exist_ok=True)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for f in ("site.css", "site.js"): shutil.copy(os.path.join(HERE, f), os.path.join(OUT, "assets", f))
    for f in os.listdir(os.path.join(HERE, "media", "assets")):
        shutil.copy(os.path.join(HERE, "media", "assets", f), os.path.join(OUT, "assets", f))
    shutil.copy(os.path.join(HERE, "media", "assets", "favicon.ico"), os.path.join(OUT, "favicon.ico"))

if __name__ == "__main__":
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    copy_assets()
    for lang in ("is", "en"):
        build_home(lang)
        if ARTICLES: build_news(lang)
    if ARTICLES: build_posts()
    build_static_pages(); build_404()
    build_meta_split() if SPLIT else build_meta_combined()
    print("built", OUT, "preview (combined)" if PREVIEW else "production: " + " + ".join(DOMAIN.values()))
