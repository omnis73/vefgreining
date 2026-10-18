# vefgreining.is / vefgreining.com — static site

Plain HTML, CSS and a little JavaScript. No WordPress, no database, no plugins to update.

## What's in the package

- `public/vefgreining.is/` — the finished Icelandic site, served at www.vefgreining.is.
- `public/vefgreining.com/` — the finished English site, served at www.vefgreining.com.
- `source/` — what the site is generated from, for when you want to change something:
  - `content/site.json` — front-page text in Icelandic (top level) and English (the `en` block): services, clients, figures, social links, analytics and form settings
  - `content/posts.json` — the ten articles (title, date, categories, excerpt, body)
  - `content/*.html` — the other Icelandic pages (legal, Hafnarfjörður dashboard, the four service pages, CV)
  - `content/en/*.html` — the English versions of those pages
  - `media/assets/` — logo (light and dark versions) and favicons
  - `site.css`, `site.js` — design and behaviour
  - `media/wp-content/` — every image and the CV PDF, at the same paths as before
  - `build.py` — regenerates `public/` (both sites)

## Rebuilding after a change

```
pip install beautifulsoup4
python3 source/build.py public
```

This writes both sites. Pages link to their counterpart on the other domain (the language switch, hreflang), and old addresses redirect to the right domain: Icelandic pages that used to be on vefgreining.com go to the same address on vefgreining.is, and the English pages that used to be under vefgreining.com/en/ are now at the root of vefgreining.com.

To click through the site from your computer, build the combined preview instead (`python3 source/build.py preview --preview`) and open `preview/index.html`. It has both languages in one folder (English under `en/`), and the links work without a web server.

### The articles (Fróðleikur)

The ten old articles are switched off on the live site, but nothing is deleted:

- Their text, dates and translations are in `content/posts.json`, and their images in `media/wp-content/`.
- `archive/` in this package is a readable copy of the site with the articles switched on. Open `archive/news/index.html` in a browser to read them; no web server needed.
- Old article addresses redirect: the Ukraine dashboard article goes to ukraine.vefgreining.com, the rest to the home page.

To bring them back, set `"articles": true` in `config` in `content/site.json` and rebuild. The menu item, the home-page section, the article list and the RSS feed all return, and the redirects are dropped. To add a new article, add an entry to `content/posts.json` (copy an existing one, set `path` like `2026/10/18/my-slug/`); `en_title` and `en_excerpt` show it in English on the English article list.

In the content files the English pages still have paths starting with `en/` (for example `en/web-analytics/`); the build drops that prefix for vefgreining.com. Each page has an `alt` field pointing to its counterpart in the other language, which the language switch in the header uses.

## How it is hosted

- **Two Cloudflare Pages projects** in the ragnarbjartur@gmail.com Cloudflare account, both connected to the GitHub repository `omnis73/vefgreining` (branch `main`), with no build step on Cloudflare:
  - `vefgreining-is` serves `public/vefgreining.is` at www.vefgreining.is and vefgreining.is.
  - `vefgreining` serves `public/vefgreining.com` at www.vefgreining.com and vefgreining.com.
- **Updating the site:** rebuild with `build.py`, commit and push to `main`. Both projects publish the new version within a minute. Each deployment also gets a preview address under vefgreining-is.pages.dev and vefgreining.pages.dev.
- **Addresses:** the www addresses are the main ones. A Cloudflare redirect rule in each domain sends the bare domain to www, keeping the path and query string.
- **Changing language** moves the visitor to the other domain. The chosen colour theme travels along in the address (`?theme=dark`), and GA4 cross-domain linking keeps the visit together. Cookie consent is asked separately on each domain, because browsers keep each domain's storage apart.
- **DNS:** both domains are managed in Cloudflare with nameservers melnicoff.ns.cloudflare.com and vida.ns.cloudflare.com. vefgreining.com's nameservers are set at Bluehost (its registrar) and vefgreining.is's at ISNIC (its registrar).
- **Email** for both domains runs on Bluehost: vefgreining.is's MX record points to mail.vefgreining.com. The mail records are "DNS only" in Cloudflare and must stay that way; the Cloudflare proxy only handles web traffic.
- **ukraine.vefgreining.com** is a "DNS only" CNAME to omnis73.github.io (GitHub Pages).
- **Going back to WordPress** would mean restoring ns1/ns2.bluehost.com at Bluehost and forwarding00/forwarding01.isnic.is at ISNIC (whose DNS pointed vefgreining.is to 69.195.124.215). The WordPress site is still there, untouched.

The `_redirects` and `_headers` files in each site folder are read by Cloudflare Pages: old WordPress addresses redirect to their new places, and pages get basic security and caching headers.

All page addresses are the same as on the WordPress site, so links from Google, social media and other sites keep working.

## Settings to check in `content/site.json`

- `config.ga4Id` — your GA4 Measurement ID (`G-ETDRLBN0KH`, the "vefgreining.com - GA4" property). GA4 loads directly, and only after a visitor accepts cookies, with Google Consent Mode v2. Events sent: `dashboard_click`, `email_click`, `language_switch`, `theme_change`.
- `config.gtmId` — your Google Tag Manager container (`GTM-584FJFB`), loaded after consent alongside GA4. It currently holds only Universal Analytics tags, which Google switched off in 2024. If you add a GA4 tag inside Tag Manager later, empty `ga4Id` so visits aren't counted twice.

## Password-protected client pages

The WordPress site has six password-protected pages that were not migrated, because their content can't be read without the passwords and a static site can't protect pages on its own:

`/domstolar/`, `/ger/`, `/hafnarfjordur/`, `/idan/`, `/kringlan/`, `/s3x/`

If clients still use these, the simplest replacement is sharing the Looker Studio reports directly with their Google accounts. Alternatively, Cloudflare Access (free for up to 50 users) can put a login in front of chosen pages on Cloudflare Pages.
