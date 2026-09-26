/* ==========================================================================
   Awesome Tips — site behaviour
   Theme, drawer nav, offline search, lightbox, reading progress, gallery filter
   ========================================================================== */
(function () {
  "use strict";

  var ROOT = window.__ROOT__ || "";
  var LANG = window.__LANG__ || "en";
  var UI = window.__UI__ || {};
  var INDEX = window.__SEARCH__ || [];

  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  /* ------------------------------------------------------------- theme */
  var THEME_KEY = "awesome-tips-theme";
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

  function applyTheme(theme) {
    if (theme) {
      document.documentElement.setAttribute("data-theme", theme);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    syncThemeGlyph(theme);
  }

  function currentTheme() {
    var set = document.documentElement.getAttribute("data-theme");
    if (set) return set;
    return prefersDark.matches ? "dark" : "light";
  }

  /* the glyph shows what a click will switch TO, and every button carries a
     tooltip so it never reads as decoration */
  function syncThemeGlyph() {
    var dark = currentTheme() === "dark";
    $$(".theme-glyph").forEach(function (g) { g.textContent = dark ? "☀" : "☾"; });
  }

  var stored = null;
  try { stored = localStorage.getItem(THEME_KEY); } catch (e) {}
  applyTheme(stored);

  $$("[data-theme-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    });
  });
  var onSchemeChange = function () { syncThemeGlyph(); };
  if (prefersDark.addEventListener) prefersDark.addEventListener("change", onSchemeChange);
  else if (prefersDark.addListener) prefersDark.addListener(onSchemeChange);

  /* -------------------------------------------------------- drawer nav */
  $$(".nav-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.body.classList.toggle("nav-open");
    });
  });
  document.addEventListener("click", function (e) {
    if (!document.body.classList.contains("nav-open")) return;
    if (e.target.closest(".sidebar") || e.target.closest(".nav-toggle")) return;
    document.body.classList.remove("nav-open");
  });

  /* ------------------------------------------------- reading progress */
  var bar = $("#progress");
  if (bar) {
    var update = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var pct = h > 0 ? Math.min(100, Math.max(0, (window.scrollY / h) * 100)) : 0;
      bar.style.width = pct + "%";
      bar.style.opacity = pct > 1 ? "1" : "0";
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
  }

  /* ----------------------------------------------------------- lightbox */
  var box = $("#lightbox");
  if (box) {
    var boxImg = $("img", box);
    var caption = null;

    function openBox(src, cap) {
      boxImg.src = src;
      boxImg.alt = cap || "";
      box.hidden = false;
      document.body.style.overflow = "hidden";
    }
    function closeBox() {
      box.hidden = true;
      boxImg.removeAttribute("src");
      document.body.style.overflow = "";
      caption = null;
    }
    document.addEventListener("click", function (e) {
      var link = e.target.closest("a.zoom, .gallery-item");
      if (!link) return;
      e.preventDefault();
      openBox(link.getAttribute("href"), link.getAttribute("data-caption") ||
        (link.querySelector("img") ? link.querySelector("img").alt : ""));
    });
    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.closest("[data-lightbox-close]")) closeBox();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !box.hidden) closeBox();
    });
    caption = null;
  }

  /* ------------------------------------------------------------- search */
  var overlay = $("#search-overlay");
  var input = $("#search-input");
  var results = $("#search-results");
  var active = -1;
  var current = [];

  function isCJK(s) { return /[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]/.test(s); }

  function terms(query) {
    var raw = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var out = [];
    raw.forEach(function (t) {
      if (isCJK(t) && t.length > 2) {
        for (var i = 0; i < t.length - 1; i++) out.push(t.slice(i, i + 2));
      } else if (isCJK(t) && t.length === 1) {
        out.push(t);
      } else {
        out.push(t);
      }
    });
    return out.filter(function (t, i, a) { return a.indexOf(t) === i; });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function highlight(text, list) {
    var out = esc(text);
    list.forEach(function (t) {
      if (!t) return;
      var safe = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      try {
        out = out.replace(new RegExp("(" + safe + ")", "gi"), "<mark>$1</mark>");
      } catch (e) {}
    });
    return out;
  }

  function snippet(text, list) {
    var lower = text.toLowerCase();
    var at = -1;
    for (var i = 0; i < list.length; i++) {
      var pos = lower.indexOf(list[i]);
      if (pos >= 0 && (at < 0 || pos < at)) at = pos;
    }
    if (at < 0) at = 0;
    var start = Math.max(0, at - 60);
    var slice = text.slice(start, start + 200);
    return (start > 0 ? "…" : "") + slice + (start + 200 < text.length ? "…" : "");
  }

  function runSearch(query) {
    var list = terms(query);
    if (!list.length) return [];
    var hits = [];
    for (var i = 0; i < INDEX.length; i++) {
      var e = INDEX[i];
      var title = (e.t || "").toLowerCase();
      var text = (e.x || "").toLowerCase();
      var hay = title + " " + text + " " + (e.c || "").toLowerCase();
      var ok = true;
      for (var j = 0; j < list.length; j++) {
        if (hay.indexOf(list[j]) < 0) { ok = false; break; }
      }
      if (!ok) continue;
      var score = 0;
      for (var k = 0; k < list.length; k++) {
        var t = list[k];
        var ti = title.indexOf(t);
        if (ti >= 0) score += 40 - Math.min(ti, 20);
        var n = text.split(t).length - 1;
        score += Math.min(n, 8) * 3;
      }
      if (e.l === LANG) score += 22;
      hits.push({ e: e, score: score });
    }
    hits.sort(function (a, b) { return b.score - a.score; });
    return hits.slice(0, 40).map(function (h) { return h.e; });
  }

  function render(list, query) {
    current = list;
    active = -1;
    if (!list.length) {
      results.innerHTML = '<div class="search-empty">' + esc(UI.no_results || "No results") + "</div>";
      return;
    }
    var list_terms = terms(query);
    results.innerHTML = list.map(function (e, i) {
      var kind = e.k === "article" ? "📄" : e.k === "slide" ? "🖼️" : e.k === "bsky" ? "☁️" : "🧵";
      var lang = e.l === "zh" ? "中文" : "EN";
      return '<a class="sr" data-i="' + i + '" href="' + ROOT + e.u + '">' +
        '<div class="sr-title">' + kind + " " + highlight(e.t, list_terms) + "</div>" +
        '<div class="sr-meta">' + esc(lang) + (e.c ? " · " + esc(e.c) : "") + (e.d ? " · " + esc(e.d) : "") + "</div>" +
        '<div class="sr-snip">' + highlight(snippet(e.x || "", list_terms), list_terms) + "</div></a>";
    }).join("");
    results.scrollTop = 0;
  }

  function openSearch() {
    if (!overlay) return;
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    input.value = "";
    input.focus();
    results.innerHTML = "";
    active = -1;
  }
  function closeSearch() {
    if (!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = "";
  }
  function move(delta) {
    var items = $$(".sr", results);
    if (!items.length) return;
    active = (active + delta + items.length) % items.length;
    items.forEach(function (el, i) { el.classList.toggle("active", i === active); });
    var cur = items[active];
    if (cur) cur.scrollIntoView({ block: "nearest" });
  }

  $$("[data-search-open]").forEach(function (btn) {
    btn.addEventListener("click", openSearch);
  });
  $$("[data-search-close]").forEach(function (btn) {
    btn.addEventListener("click", closeSearch);
  });
  if (overlay) {
    overlay.addEventListener("click", function (e) { if (e.target === overlay) closeSearch(); });
    var timer = null;
    input.addEventListener("input", function () {
      var q = input.value;
      clearTimeout(timer);
      timer = setTimeout(function () { render(runSearch(q), q); }, 90);
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        var items = $$(".sr", results);
        var target = items[active >= 0 ? active : 0];
        if (target) { window.location.href = target.getAttribute("href"); }
      } else if (e.key === "Escape") { closeSearch(); }
    });
  }
  document.addEventListener("keydown", function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName || "")) || e.target.isContentEditable;
    if (typing) return;
    if (e.key === "/" || (e.key === "k" && (e.metaKey || e.ctrlKey))) {
      e.preventDefault();
      openSearch();
    } else if (e.key === "Escape" && document.body.classList.contains("nav-open")) {
      document.body.classList.remove("nav-open");
    }
  });

  /* ----------------------------------------------------- gallery filter */
  var filter = $("#gallery-filter");
  if (filter) {
    filter.addEventListener("input", function () {
      var q = filter.value.toLowerCase().trim();
      $$(".gallery-thread").forEach(function (section) {
        var title = (section.querySelector("h3") || {}).textContent || "";
        var visible = 0;
        $$(".gallery-item", section).forEach(function (item) {
          var hay = (title + " " + (item.getAttribute("data-caption") || "")).toLowerCase();
          var show = !q || hay.indexOf(q) >= 0;
          item.classList.toggle("hidden", !show);
          if (show) visible++;
        });
        section.classList.toggle("hidden", visible === 0);
      });
      $$(".gallery-cat").forEach(function (section) {
        var any = $$(".gallery-thread", section).some(function (s) { return !s.classList.contains("hidden"); });
        section.classList.toggle("hidden", !any);
      });
    });
  }

  /* ------------------------------------- autoplay (viewport-triggered) */
  /* GIF-style clips play automatically once they scroll into view and pause
     again when they leave. Autoplay policy requires them to be muted, so they
     ship as muted + loop + playsinline. Everything else here exists to avoid
     the classic pitfalls: a clip that can never reach a visibility ratio, a
     play() interrupted by a competing pause(), and mistaking our own pause()
     for the reader pausing a clip on purpose. */
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var autoplay = !reduceMotion.matches;          // honour the OS "reduce motion" setting

  var allVideos = $$("video");

  function wanted(v) {
    return autoplay && !document.hidden && v.__inView === true && v.dataset.userPaused !== "1";
  }

  function attempt(v) {
    if (!wanted(v) || !v.paused) return;
    var tries = (parseInt(v.dataset.retries || "0", 10) || 0) + 1;
    v.dataset.retries = String(tries);
    var p = v.play();
    if (!p || !p.catch) return;                  // very old Safari: no promise
    p.then(function () {
      v.dataset.retries = "0";
    }).catch(function () {
      // usually AbortError: a competing pause() won the race. Retry while the
      // clip is still supposed to be playing.
      if (tries <= 4 && wanted(v)) {
        setTimeout(function () { attempt(v); }, 250 * tries);
      } else {
        v.dataset.retries = "0";
      }
    });
  }

  function release(v) {
    if (!v.paused) v.pause();
  }

  function sync(v) { if (wanted(v)) attempt(v); else release(v); }
  function syncAll() { allVideos.forEach(sync); }

  /* Only a real interaction with the player counts as "the reader paused this".
     We cannot use the pause event alone, because media events fire
     asynchronously -- our own pause() would look identical. */
  ["pointerdown", "touchstart", "keydown"].forEach(function (evt) {
    document.addEventListener(evt, function (e) {
      var t = e.target;
      var v = t && (t.tagName === "VIDEO" ? t : (t.closest ? t.closest("video") : null));
      if (v) v.dataset.touchedAt = String(Date.now());
    }, true);
  });
  function touchedRecently(v) {
    var t = parseInt(v.dataset.touchedAt || "0", 10) || 0;
    return Date.now() - t < 2500;
  }
  document.addEventListener("pause", function (e) {
    var v = e.target;
    if (v && v.tagName === "VIDEO" && touchedRecently(v)) v.dataset.userPaused = "1";
  }, true);
  document.addEventListener("play", function (e) {
    var v = e.target;
    if (v && v.tagName === "VIDEO" && touchedRecently(v)) v.dataset.userPaused = "0";
  }, true);

  if (allVideos.length && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        entry.target.__inView = entry.isIntersecting;
        sync(entry.target);
      });
    }, { threshold: 0, rootMargin: "200px 0px" });
    allVideos.forEach(function (v) {
      v.__inView = false;
      observer.observe(v);
      // if the first play() landed before the data was ready, try again
      ["loadeddata", "canplay"].forEach(function (evt) {
        v.addEventListener(evt, function () { if (wanted(v) && v.paused) attempt(v); });
      });
    });
  } else {
    allVideos.forEach(function (v) { v.__inView = true; attempt(v); });
  }

  document.addEventListener("visibilitychange", function () { syncAll(); });

  /* clips always autoplay; the only thing that turns them off is the OS
     "reduce motion" accessibility setting */
  var onReduceChange = function () {
    autoplay = !reduceMotion.matches;
    syncAll();
  };
  if (reduceMotion.addEventListener) reduceMotion.addEventListener("change", onReduceChange);
  else if (reduceMotion.addListener) reduceMotion.addListener(onReduceChange);
})();
