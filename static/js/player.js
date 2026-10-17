// Lesson player: one slide at a time, chapters, a completion screen, and the reader's place
// kept in this browser only. Without JavaScript the slides simply stack down the page.
(function () {
  "use strict";
  var KEY = "appliedai.lessons";

  function load() {
    try { return JSON.parse(window.localStorage.getItem(KEY)) || { seen: {}, last: null }; }
    catch (error) { return { seen: {}, last: null }; }
  }
  function save(state) {
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (error) { /* storage blocked */ }
  }
  function validSlug(value) { return typeof value === "string" && /^[a-z0-9-]+$/.test(value); }
  function all(root, selector) { return Array.prototype.slice.call(root.querySelectorAll(selector)); }

  function initPlayer(player) {
    var slug = player.getAttribute("data-slug");
    var slides = all(player, ".slide");
    if (!slides.length) { return; }
    var chapters = all(player, ".chapter");
    var complete = player.querySelector("[data-complete]");
    var indexLabel = player.querySelector("[data-index]");
    var sectionLabel = player.querySelector("[data-section-label]");
    var prev = player.querySelector("[data-prev]");
    var next = player.querySelector("[data-next]");
    var full = player.querySelector("[data-fullscreen]");
    var code = document.querySelector(".lesson-meta .card-code");
    var title = (code ? code.textContent.trim() + " " : "") + document.querySelector("h1").textContent.trim();
    var current = 0;
    var finished = false;

    player.classList.add("is-player");
    player.querySelector("[data-controls]").hidden = false;
    var chapterList = player.querySelector("[data-chapters]");
    if (chapterList) { chapterList.hidden = false; }
    if (!document.fullscreenEnabled && full) { full.hidden = true; }

    function record(slide) {
      var state = load();
      state.seen[slug] = Math.max(state.seen[slug] || 0, slide);
      state.last = { slug: slug, slide: Math.min(slide, slides.length), total: slides.length, title: title };
      save(state);
    }

    function show(i) {
      finished = false;
      player.classList.remove("is-complete");
      if (complete) { complete.hidden = true; }
      current = Math.max(0, Math.min(slides.length - 1, i));
      slides.forEach(function (s, n) { s.classList.toggle("is-active", n === current); });
      chapters.forEach(function (ch) {
        var start = parseInt(ch.getAttribute("data-start"), 10) - 1;
        var count = parseInt(ch.getAttribute("data-count"), 10);
        var inside = current >= start && current < start + count;
        var fill = current >= start + count ? 1 : inside ? (current - start + 1) / count : 0;
        ch.classList.toggle("is-active", inside);
        ch.style.setProperty("--fill", fill);
      });
      indexLabel.textContent = String(current + 1);
      sectionLabel.textContent = slides[current].getAttribute("data-section") || "";
      prev.disabled = current === 0;
      next.textContent = current === slides.length - 1 ? "Finish ✓" : "Next →";
      history.replaceState(null, "", "#slide-" + (current + 1));
      record(current + 1);
    }

    function finish() {
      if (!complete) { return; }
      finished = true;
      slides.forEach(function (s) { s.classList.remove("is-active"); });
      complete.hidden = false;
      player.classList.add("is-complete");
      chapters.forEach(function (ch) { ch.style.setProperty("--fill", 1); ch.classList.remove("is-active"); });
      next.textContent = "Done";
      sectionLabel.textContent = "Complete";
      record(slides.length);
      var cta = complete.querySelector("a, button");
      if (cta) { cta.focus({ preventScroll: true }); }
    }

    function forward() {
      if (finished) { return; }
      if (current === slides.length - 1) { finish(); } else { show(current + 1); }
    }
    function back() { show(finished ? slides.length - 1 : current - 1); }

    prev.addEventListener("click", back);
    next.addEventListener("click", forward);
    chapters.forEach(function (ch) {
      ch.addEventListener("click", function () { show(parseInt(ch.getAttribute("data-go"), 10) - 1); });
    });
    var restart = player.querySelector("[data-restart]");
    if (restart) { restart.addEventListener("click", function () { show(0); }); }
    player.querySelector(".stage").addEventListener("click", function (event) {
      if (event.target.tagName === "IMG") { forward(); }
    });
    if (full) {
      full.addEventListener("click", function () {
        if (document.fullscreenElement) { document.exitFullscreen(); } else { player.requestFullscreen(); }
      });
    }
    document.addEventListener("keydown", function (event) {
      if (event.target.closest("input, textarea, select")) { return; }
      if (event.key === "ArrowRight" || event.key === " ") { event.preventDefault(); forward(); }
      if (event.key === "ArrowLeft") { back(); }
    });

    var match = /^#slide-(\d+)$/.exec(window.location.hash);
    var start = match ? parseInt(match[1], 10) - 1 : 0;
    if (!match) {
      var state = load();
      if (state.last && state.last.slug === slug && state.last.slide < slides.length) { start = state.last.slide - 1; }
    }
    show(start);
  }

  function initProgress() {
    var state = load();
    all(document, "[data-lesson]").forEach(function (item) {
      var seen = state.seen[item.getAttribute("data-lesson")] || 0;
      var total = parseInt(item.getAttribute("data-total"), 10) || 1;
      if (!seen) { return; }
      var bar = item.querySelector(".card-progress span");
      if (bar) { bar.style.width = Math.round((Math.min(seen, total) / total) * 100) + "%"; }
      var label = item.querySelector("[data-state]");
      if (label) { label.textContent = seen >= total ? "Finished" : "In progress"; }
      item.classList.add(seen >= total ? "is-done" : "is-started");
    });
    var resume = document.querySelector("[data-resume]");
    var last = state.last;
    if (resume && last && validSlug(last.slug)) {
      resume.querySelector("a").href = "/episodes/" + last.slug + "/#slide-" + Number(last.slide);
      resume.querySelector("[data-resume-title]").textContent = last.title;
      resume.querySelector("[data-resume-pos]").textContent = "slide " + Number(last.slide) + " of " + Number(last.total);
      resume.hidden = false;
    }
  }

  all(document, "[data-player]").forEach(initPlayer);
  initProgress();
})();
