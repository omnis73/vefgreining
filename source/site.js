/* Vefgreining — small site script: menu, theme switch, motion, cookie consent, contact form. */
(function () {
  var CFG = window.VG_CONFIG || {};
  var GTM_ID = CFG.gtmId || "";
  var GA4_ID = CFG.ga4Id || "";
  var FORM_ENDPOINT = CFG.formEndpoint || "";
  var EMAIL = CFG.email || "vefgreining@vefgreining.is";
  var TXT = CFG.text || {};

  /* Storage can throw in private windows and previews */
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  /* Opened straight from disk (file://) there is no web server to turn folder links like "kannanir/"
     into "kannanir/index.html", so add it to the links. On the live site this does nothing. */
  if (location.protocol === "file:") {
    document.querySelectorAll("a[href]").forEach(function (a) {
      var h = a.getAttribute("href");
      if (/^[a-z][a-z0-9+.-]*:/i.test(h) || h.charAt(0) === "#" || h.charAt(0) === "/") return;
      var m = h.match(/^([^#?]*)(.*)$/), path = m[1], rest = m[2];
      if (path === "" ) return;
      if (path === "." || path === "./") path = "./index.html";
      else if (/\/$/.test(path) || path === "..") path = path.replace(/\/?$/, "/") + "index.html";
      else return;
      a.setAttribute("href", path + rest);
    });
  }

  /* Mobile menu */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
    });
  }

  /* Theme picker: blue (default), light or dark. The head script applies the saved choice before paint. */
  var root = document.documentElement;
  var themeBtns = document.querySelectorAll("[data-set-theme]");
  /* Same lookup as the head script: storage first, then the tab's window.name (for frames where storage is blocked) */
  /* The other language lives on the other domain (vefgreining.is / vefgreining.com), where storage is separate,
     so the theme travels in the address (?theme=dark) and is removed from it again here. */
  var qTheme = /[?&]theme=(blue|light|dark)\b/.exec(location.search);
  var chosen = qTheme ? qTheme[1] : get("vg-theme");
  if (qTheme) {
    set("vg-theme", chosen);
    try { history.replaceState(history.state, "", location.pathname + location.search.replace(/([?&])theme=\w+&?/, "$1").replace(/[?&]$/, "") + location.hash); } catch (e) {}
  }
  if (!chosen) { var nm = /(?:^|;)vg-theme=(\w+)/.exec(window.name || ""); if (nm) chosen = nm[1]; }
  if (chosen !== "light" && chosen !== "dark") chosen = "blue";
  if (root.getAttribute("data-theme") !== chosen) root.setAttribute("data-theme", chosen);
  function current() { return chosen; }
  /* Keep the visitor's choice if something else (an embedding page, a browser extension) changes the attribute */
  if (window.MutationObserver) {
    new MutationObserver(function () {
      if (root.getAttribute("data-theme") !== chosen) { root.setAttribute("data-theme", chosen); syncThemeButtons(); }
    }).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
  }
  function syncThemeButtons() {
    var t = current();
    themeBtns.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-set-theme") === t ? "true" : "false"); });
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", t === "light" ? "#FAFBFC" : t === "dark" ? "#0F1722" : "#0B3B7A");
  }
  themeBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      var t = b.getAttribute("data-set-theme");
      chosen = t;
      root.setAttribute("data-theme", t);
      set("vg-theme", t);
      /* Also kept in the tab's window.name, which survives page loads where storage is blocked */
      try { window.name = (window.name || "").replace(/(?:^|;)vg-theme=\w+/g, "").replace(/^;/, "") + ";vg-theme=" + t; } catch (e) {}
      syncThemeButtons();
      if (typeof track === "function") track("theme_change", { theme: t });
    });
  });
  syncThemeButtons();

  /* Links to the other domain carry a non-default theme along */
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || chosen === "blue" || a.origin === location.origin) return;
    if (!/(^|\.)vefgreining\.(is|com)$/.test(a.hostname) || a.hostname.indexOf("ukraine.") === 0) return;
    try { var u = new URL(a.href); u.searchParams.set("theme", chosen); a.href = u.toString(); } catch (err) {}
  }, true);

  /* Pages opened from a link start at the top, even inside frames that keep the scroll position
     between pages (such as the preview). Back/forward still restores where the visitor was, and #anchors still work. */
  (function () {
    var nav0 = performance.getEntriesByType ? performance.getEntriesByType("navigation")[0] : null;
    if ((nav0 && nav0.type === "back_forward") || location.hash) return;
    function toTop() {
      window.scrollTo(0, 0);
      var first = document.body && document.body.firstElementChild;
      if (first && first.scrollIntoView && window.self !== window.top) { try { first.scrollIntoView({ block: "start" }); } catch (e) {} }
    }
    toTop();
    window.addEventListener("load", toTop, { once: true });
  })();

  /* Logo: on the page it links to, scroll back to the top instead of reloading */
  function samePage(a) {
    var strip = function (p) { return p.replace(/index\.html$/, ""); };
    return a.origin === location.origin && strip(a.pathname) === strip(location.pathname);
  }
  document.querySelectorAll("a.brand").forEach(function (a) {
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0 || !samePage(a)) return;
      e.preventDefault();
      var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
      if (location.hash) { try { history.replaceState(null, "", location.pathname + location.search); } catch (err) {} }
      if (nav) { nav.classList.remove("open"); if (toggle) toggle.setAttribute("aria-expanded", "false"); }
    });
  });

  /* Hero chart: measure the line so it can draw itself once */
  document.querySelectorAll(".chart .trend").forEach(function (t) {
    if (t.getTotalLength) t.style.setProperty("--len", Math.ceil(t.getTotalLength()));
  });

  /* Scroll-triggered motion: service icons draw themselves, key figures count up */
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function fmt(n, sep) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, sep); }
  function countUp(td) {
    var table = td.closest("[data-sep]"), sep = table ? table.getAttribute("data-sep") : ".";
    var target = parseInt(td.getAttribute("data-count"), 10), suffix = td.getAttribute("data-suffix") || "";
    if (!target || reduce) return;
    var dur = 1600, t0 = null;
    function step(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      td.textContent = fmt(Math.round(target * e), sep) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  function play(el) {
    if (el.classList.contains("play")) return;
    el.classList.add("play");
    el.querySelectorAll("[data-count]").forEach(countUp);
  }
  var animated = document.querySelectorAll("[data-animate]");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { play(en.target); io.unobserve(en.target); } });
    }, { threshold: 0.35 });
    animated.forEach(function (el) { io.observe(el); });
  } else {
    animated.forEach(play);
  }

  /* Analytics only after consent (Google Consent Mode v2, default denied) */
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag("consent", "default", { ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied", analytics_storage: "denied" });
  var gtmLoaded = false;
  function loadGTM() {
    if (gtmLoaded || !GTM_ID) return;
    gtmLoaded = true;
    window.dataLayer.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(GTM_ID);
    document.head.appendChild(s);
  }
  var ga4Loaded = false;
  function loadGA4() {
    if (ga4Loaded || !GA4_ID) return;
    ga4Loaded = true;
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA4_ID);
    document.head.appendChild(s);
    gtag("js", new Date());
    /* One GA4 property for both domains; the linker keeps a visit together when it crosses between them */
    gtag("config", GA4_ID, CFG.domains ? { linker: { domains: CFG.domains } } : {});
  }
  function applyConsent(choice) {
    if (choice === "granted") {
      gtag("consent", "update", { analytics_storage: "granted" });
      loadGA4();
      loadGTM();
    }
  }
  /* Events: sent to GA4 directly when it is loaded, and to the data layer for Tag Manager */
  function track(name, params) {
    params = params || {};
    if (ga4Loaded) gtag("event", name, params);
    if (gtmLoaded) window.dataLayer.push(Object.assign({ event: name }, params));
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("[data-track]") : null;
    if (a) track(a.getAttribute("data-track"), { link_url: a.href, page_language: CFG.lang || "is" });
    var l = e.target.closest ? e.target.closest(".lang-switch") : null;
    if (l) track("language_switch", { to_language: l.getAttribute("hreflang") });
  });
  var banner = document.getElementById("consent");
  var choice = get("vg-consent");
  applyConsent(choice);
  if (banner) {
    if (!choice && (GTM_ID || GA4_ID)) banner.hidden = false;
    banner.addEventListener("click", function (e) {
      var v = e.target.getAttribute("data-consent");
      if (!v) return;
      set("vg-consent", v);
      banner.hidden = true;
      applyConsent(v);
    });
  }
  document.querySelectorAll("[data-open-consent]").forEach(function (b) {
    b.addEventListener("click", function () { if (banner) banner.hidden = false; });
  });

  /* Contact form: posts to a form service if one is configured, otherwise opens email */
  var form = document.getElementById("contact-form");
  if (form) {
    var status = form.querySelector(".form-status");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.querySelector(".hp input").value) return;
      var d = new FormData(form);
      var name = (d.get("name") || "").trim(), email = (d.get("email") || "").trim();
      status.className = "form-status";
      if (!name || !email || email.indexOf("@") < 1) {
        status.textContent = TXT.invalid;
        status.classList.add("err");
        return;
      }
      if (!FORM_ENDPOINT) {
        var subj = d.get("subject") || TXT.subject;
        var body = (d.get("message") || "") + "\n\n— " + name + " (" + email + ")";
        window.location.href = "mailto:" + EMAIL + "?subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(body);
        status.textContent = TXT.mailto;
        status.classList.add("ok");
        return;
      }
      var btn = form.querySelector("button[type=submit]");
      btn.disabled = true;
      status.textContent = TXT.sending;
      fetch(FORM_ENDPOINT, { method: "POST", body: d, headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error(r.status);
          form.reset();
          status.textContent = TXT.sent;
          status.classList.add("ok");
          track("contact_form_sent", { page_language: CFG.lang || "is" });
        })
        .catch(function () {
          status.textContent = TXT.failed;
          status.classList.add("err");
        })
        .finally(function () { btn.disabled = false; });
    });
  }
})();
