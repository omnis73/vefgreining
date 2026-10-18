# vefgreining.com — static site

Plain HTML, CSS and a little JavaScript. No WordPress, no database, no plugins to update.

## What's in the package

- `site/` — the finished website. Upload the contents of this folder to any web host. You can also open `site/index.html` straight from your computer to click through it; links work there too, though the fonts and the embedded dashboard need an internet connection.
- `source/` — what the site is generated from, for when you want to change something:
  - `content/site.json` — front-page text in Icelandic (top level) and English (the `en` block): services, clients, figures, social links, analytics and form settings
  - `content/posts.json` — the ten articles (title, date, categories, excerpt, body)
  - `content/*.html` — the other Icelandic pages (legal, Hafnarfjörður dashboard, the four service pages, CV)
  - `content/en/*.html` — the English versions of those pages
  - `media/assets/` — logo (light and dark versions) and favicons
  - `site.css`, `site.js` — design and behaviour
  - `media/wp-content/` — every image and the CV PDF, at the same paths as before
  - `build.py` — regenerates `site/`

## Rebuilding after a change

```
pip install beautifulsoup4
python3 build.py ../site
```

### The articles (Fróðleikur)

The ten old articles are switched off on the live site, but nothing is deleted:

- Their text, dates and translations are in `content/posts.json`, and their images in `media/wp-content/`.
- `archive/` in this package is a readable copy of the site with the articles switched on. Open `archive/news/index.html` in a browser to read them; no web server needed.
- Old article addresses redirect: the Ukraine dashboard article goes to ukraine.vefgreining.com, the rest to the home page.

To bring them back, set `"articles": true` in `config` in `content/site.json` and rebuild. The menu item, the home-page section, the article list and the RSS feed all return, and the redirects are dropped. To add a new article, add an entry to `content/posts.json` (copy an existing one, set `path` like `2026/10/18/my-slug/`); `en_title` and `en_excerpt` show it in English on the English article list.

The English site is under `/en/`. Each page has an `alt` field pointing to its counterpart in the other language, which the language switch in the header uses.

## How it is hosted

- **Cloudflare Pages**, project `vefgreining` in the ragnarbjartur@gmail.com Cloudflare account, connected to the GitHub repository `omnis73/vefgreining` (branch `main`). It serves the `site/` folder as is; there is no build step on Cloudflare.
- **Updating the site:** rebuild `site/` with `build.py`, commit and push to `main`. Cloudflare publishes the new version within a minute. Each deployment also gets its own preview address under vefgreining.pages.dev.
- **Addresses:** www.vefgreining.com is the main address. A Cloudflare redirect rule sends vefgreining.com to www, keeping the path and query string.
- **DNS** for vefgreining.com is managed in Cloudflare (nameservers melnicoff.ns.cloudflare.com and vida.ns.cloudflare.com, set at Bluehost, which is still the registrar).
- **Email** for vefgreining.com still runs on Bluehost. The mail records (MX, mail, imap, pop, smtp, autodiscover, SPF, DKIM) are "DNS only" in Cloudflare and must stay that way; the Cloudflare proxy only handles web traffic.
- **ukraine.vefgreining.com** is a "DNS only" CNAME to omnis73.github.io (GitHub Pages).
- **Going back to WordPress** would mean restoring ns1/ns2.bluehost.com at Bluehost. The WordPress site is still there, untouched.

The `_redirects` and `_headers` files in `site/` are read by Cloudflare Pages: old WordPress addresses redirect to their new places, and pages get basic security and caching headers. `.htaccess` is only for an Apache host and is ignored on Cloudflare.

All page addresses are the same as on the WordPress site, so links from Google, social media and other sites keep working.

## Settings to check in `content/site.json`

- `config.ga4Id` — your GA4 Measurement ID (`G-ETDRLBN0KH`, the "vefgreining.com - GA4" property). GA4 loads directly, and only after a visitor accepts cookies, with Google Consent Mode v2. Events sent: `dashboard_click`, `email_click`, `language_switch`, `theme_change`.
- `config.gtmId` — your Google Tag Manager container (`GTM-584FJFB`), loaded after consent alongside GA4. It currently holds only Universal Analytics tags, which Google switched off in 2024. If you add a GA4 tag inside Tag Manager later, empty `ga4Id` so visits aren't counted twice.

## Password-protected client pages

The WordPress site has six password-protected pages that were not migrated, because their content can't be read without the passwords and a static site can't protect pages on its own:

`/domstolar/`, `/ger/`, `/hafnarfjordur/`, `/idan/`, `/kringlan/`, `/s3x/`

If clients still use these, the simplest replacement is sharing the Looker Studio reports directly with their Google accounts. Alternatively, Cloudflare Access (free for up to 50 users) can put a login in front of chosen pages on Cloudflare Pages.
