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

## Hosting (pick one)

**Cloudflare Pages or Netlify (recommended, free).** Drag the `site/` folder into a new project, then point vefgreining.com and www.vefgreining.com at it in the DNS settings. The `_redirects` file is picked up automatically and sends old WordPress addresses (categories, feed, demo pages) to the right place.

**Your current host (Apache/cPanel).** Delete the WordPress files and upload the contents of `site/`. The `.htaccess` file handles the 404 page and the old-address redirects.

All article and page addresses are the same as on the WordPress site, so links from Google, social media and other sites keep working.

## Settings to check in `content/site.json`

- `config.ga4Id` — your GA4 Measurement ID (`G-ETDRLBN0KH`, the "vefgreining.com - GA4" property). GA4 loads directly, and only after a visitor accepts cookies, with Google Consent Mode v2. Events sent: `dashboard_click`, `email_click`, `language_switch`, `theme_change`.
- `config.gtmId` — your Google Tag Manager container (`GTM-584FJFB`), loaded after consent alongside GA4. It currently holds only Universal Analytics tags, which Google switched off in 2024. If you add a GA4 tag inside Tag Manager later, empty `ga4Id` so visits aren't counted twice.

## Password-protected client pages

The WordPress site has six password-protected pages that were not migrated, because their content can't be read without the passwords and a static site can't protect pages on its own:

`/domstolar/`, `/ger/`, `/hafnarfjordur/`, `/idan/`, `/kringlan/`, `/s3x/`

If clients still use these, the simplest replacement is sharing the Looker Studio reports directly with their Google accounts. Alternatively, Cloudflare Access (free for up to 50 users) can put a login in front of chosen pages on Cloudflare Pages.
