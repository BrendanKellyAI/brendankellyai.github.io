// Lesson player: one slide at a time, chapters, a completion screen, swipe between slides,
// zoom in full screen, and the reader's place kept in this browser only. Without JavaScript
// the slides simply stack down the page.
(function () {
  "use strict";
  var KEY = "appliedai.lessons";
  var SWIPE_MIN_PX = 50;
  var SWIPE_MAX_MS = 800;
  var DOUBLE_TAP_MS = 300;
  var TAP_SLOP_PX = 10;
  var ZOOM_MAX = 4;
  var ZOOM_STEP = 1.5;
  var DOUBLE_TAP_ZOOM = 2.5;

  function load() {
    try { return JSON.parse(window.localStorage.getItem(KEY)) || { seen: {}, last: null }; }
    catch (error) { return { seen: {}, last: null }; }
  }
  function save(state) {
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (error) { /* storage blocked */ }
  }
  function validSlug(value) { return typeof value === "string" && /^[a-z0-9-]+$/.test(value); }
  function all(root, selector) { return Array.prototype.slice.call(root.querySelectorAll(selector)); }
  function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }

  // Zoom and pan for one image at a time, as a transform with its origin at the top left.
  // A point on screen maps to the image as: screen = base + translate + scale * local.
  function createZoom() {
    var image = null;
    var scale = 1;
    var x = 0;
    var y = 0;

    function apply(animate) {
      if (!image) { return; }
      image.style.transition = animate ? "transform 0.2s ease-out" : "none";
      image.style.transform = scale === 1 && x === 0 && y === 0
        ? "" : "translate(" + x + "px, " + y + "px) scale(" + scale + ")";
    }

    // Untransformed size and position of the image on screen. Read it before changing the
    // state: the box on screen reflects the transform last applied, not the one being set.
    function bounds() {
      var box = image.getBoundingClientRect();
      return { left: box.left - x, top: box.top - y, width: box.width / scale, height: box.height / scale };
    }

    // Keep the zoomed image covering its own unzoomed box, so it can never be dragged away.
    function clampPan(b) {
      x = clamp(x, b.width - b.width * scale, 0);
      y = clamp(y, b.height - b.height * scale, 0);
    }

    // Scale to `next`, keeping the image point under (screenX, screenY) where it is.
    function zoomAt(next, screenX, screenY, animate) {
      if (!image) { return; }
      var b = bounds();
      var focusX = screenX === undefined ? b.left + b.width / 2 : screenX;
      var focusY = screenY === undefined ? b.top + b.height / 2 : screenY;
      var localX = (focusX - b.left - x) / scale;
      var localY = (focusY - b.top - y) / scale;
      scale = clamp(next, 1, ZOOM_MAX);
      x = focusX - b.left - scale * localX;
      y = focusY - b.top - scale * localY;
      clampPan(b);
      apply(animate);
    }

    return {
      attach: function (next) { if (image !== next) { this.reset(); image = next; } },
      reset: function () { scale = 1; x = 0; y = 0; apply(false); },
      zoomAt: zoomAt,
      zoomBy: function (factor) { zoomAt(scale * factor, undefined, undefined, true); },
      toggleAt: function (screenX, screenY) {
        zoomAt(scale > 1 ? 1 : DOUBLE_TAP_ZOOM, screenX, screenY, true);
      },
      panBy: function (dx, dy) {
        if (!image) { return; }
        var b = bounds();
        x += dx;
        y += dy;
        clampPan(b);
        apply(false);
      },
      scale: function () { return scale; },
      isZoomed: function () { return scale > 1.01; },
    };
  }

  // Pointer gestures on the stage: swipe to change slide, and in full screen, pinch,
  // double-tap, drag, and wheel to zoom and pan.
  function attachGestures(stage, options) {
    var pointers = {};
    var start = null;
    var pinch = null;
    var lastTap = { time: 0, x: 0, y: 0 };
    var swiped = false;

    function count() { return Object.keys(pointers).length; }
    function points() { return Object.keys(pointers).map(function (id) { return pointers[id]; }); }

    stage.addEventListener("pointerdown", function (event) {
      if (event.target.closest("a, button") || !options.activeImage()) { return; }
      pointers[event.pointerId] = { x: event.clientX, y: event.clientY };
      if (count() === 1) {
        start = { x: event.clientX, y: event.clientY, time: Date.now(), lastX: event.clientX, lastY: event.clientY };
        swiped = false;
      } else if (count() === 2 && options.canZoom()) {
        var p = points();
        pinch = { distance: Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y), scale: options.zoom.scale() };
        options.followFinger(0);
      } else {
        // Two fingers outside full screen: the browser's own page zoom, never a swipe.
        start = null;
        options.followFinger(0, true);
      }
      if (stage.setPointerCapture) { stage.setPointerCapture(event.pointerId); }
    });

    stage.addEventListener("pointermove", function (event) {
      if (!pointers[event.pointerId]) { return; }
      pointers[event.pointerId] = { x: event.clientX, y: event.clientY };
      if (pinch && count() === 2) {
        var p = points();
        var distance = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
        options.zoom.zoomAt(pinch.scale * (distance / pinch.distance), (p[0].x + p[1].x) / 2, (p[0].y + p[1].y) / 2);
        return;
      }
      if (!start || count() !== 1) { return; }
      if (options.canZoom() && options.zoom.isZoomed()) {
        options.zoom.panBy(event.clientX - start.lastX, event.clientY - start.lastY);
      } else {
        var dx = event.clientX - start.x;
        var dy = event.clientY - start.y;
        if (Math.abs(dx) > Math.abs(dy)) { options.followFinger(dx); }
      }
      start.lastX = event.clientX;
      start.lastY = event.clientY;
    });

    function end(event) {
      if (!pointers[event.pointerId]) { return; }
      delete pointers[event.pointerId];
      if (pinch) {
        if (count() < 2) { pinch = null; start = null; }
        return;
      }
      if (count() > 0) { start = null; return; }
      if (!start || event.type === "pointercancel") { options.followFinger(0, true); start = null; return; }
      var dx = event.clientX - start.x;
      var dy = event.clientY - start.y;
      var quick = Date.now() - start.time < SWIPE_MAX_MS;
      var zoomed = options.canZoom() && options.zoom.isZoomed();
      if (!zoomed && quick && Math.abs(dx) > SWIPE_MIN_PX && Math.abs(dx) > Math.abs(dy) * 1.5) {
        swiped = true;
        options.followFinger(0);
        if (dx < 0) { options.next(); } else { options.previous(); }
      } else {
        options.followFinger(0, true);
        var isTap = Math.abs(dx) < TAP_SLOP_PX && Math.abs(dy) < TAP_SLOP_PX;
        if (isTap && options.canZoom() && event.pointerType !== "mouse") {
          var now = Date.now();
          var near = Math.abs(event.clientX - lastTap.x) < 30 && Math.abs(event.clientY - lastTap.y) < 30;
          if (now - lastTap.time < DOUBLE_TAP_MS && near) {
            options.zoom.toggleAt(event.clientX, event.clientY);
            lastTap.time = 0;
          } else {
            lastTap = { time: now, x: event.clientX, y: event.clientY };
          }
        }
      }
      start = null;
    }
    stage.addEventListener("pointerup", end);
    stage.addEventListener("pointercancel", end);

    stage.addEventListener("dblclick", function (event) {
      if (options.canZoom() && event.target.tagName === "IMG") { options.zoom.toggleAt(event.clientX, event.clientY); }
    });
    stage.addEventListener("wheel", function (event) {
      if (!options.canZoom() || !options.activeImage()) { return; }
      event.preventDefault();
      var factor = Math.exp(-event.deltaY * 0.0015);
      options.zoom.zoomAt(options.zoom.scale() * factor, event.clientX, event.clientY);
    }, { passive: false });

    return { swipedJustNow: function () { var was = swiped; swiped = false; return was; } };
  }

  function initPlayer(player) {
    var slug = player.getAttribute("data-slug");
    var slides = all(player, ".slide");
    if (!slides.length) { return; }
    var stage = player.querySelector(".stage");
    var chapters = all(player, ".chapter");
    var complete = player.querySelector("[data-complete]");
    var indexLabel = player.querySelector("[data-index]");
    var sectionLabel = player.querySelector("[data-section-label]");
    var prev = player.querySelector("[data-prev]");
    var next = player.querySelector("[data-next]");
    var full = player.querySelector("[data-fullscreen]");
    var code = document.querySelector(".lesson-meta .card-code");
    var title = (code ? code.textContent.trim() + " " : "") + document.querySelector("h1").textContent.trim();
    var nativeFullscreen = !!(document.fullscreenEnabled && player.requestFullscreen);
    var zoom = createZoom();
    var current = 0;
    var finished = false;

    player.classList.add("is-player");
    player.querySelector("[data-controls]").hidden = false;
    var chapterList = player.querySelector("[data-chapters]");
    if (chapterList) { chapterList.hidden = false; }

    function activeImage() { return finished ? null : slides[current].querySelector("img"); }
    function isFull() { return player.classList.contains("is-fullscreen"); }

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
      zoom.attach(activeImage());
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
      zoom.reset();
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

    // While a swipe is under way, the slide follows the finger; it snaps back if not taken.
    function followFinger(dx, animate) {
      var image = activeImage();
      if (!image || zoom.isZoomed()) { return; }
      image.style.transition = animate ? "transform 0.2s ease-out" : "none";
      image.style.transform = dx ? "translateX(" + dx * 0.6 + "px)" : "";
    }

    // Full screen: the browser's own where it is supported (not on iPhone), otherwise a
    // full-window view. Both get the same class, so styling and zoom work the same way.
    function setFull(on) {
      player.classList.toggle("is-fullscreen", on);
      // Lock page scrolling behind the full-window view (the browser does it in real full screen).
      document.documentElement.classList.toggle("player-open", on && document.fullscreenElement !== player);
      if (full) {
        full.setAttribute("aria-pressed", on ? "true" : "false");
        full.setAttribute("aria-label", on ? "Exit full screen" : "Full screen");
      }
      zoom.reset();
    }
    function toggleFull() {
      if (isFull() && !document.fullscreenElement) { setFull(false); return; }
      if (nativeFullscreen) {
        if (document.fullscreenElement) {
          document.exitFullscreen();
        } else {
          // Some browsers and embedded views refuse; fall back to the full-window view.
          Promise.resolve(player.requestFullscreen()).catch(function () { setFull(true); });
        }
      } else {
        setFull(!isFull());
      }
    }
    document.addEventListener("fullscreenchange", function () {
      setFull(document.fullscreenElement === player);
    });

    var gestures = attachGestures(stage, {
      zoom: zoom,
      activeImage: activeImage,
      canZoom: isFull,
      next: forward,
      previous: back,
      followFinger: followFinger,
    });

    prev.addEventListener("click", back);
    next.addEventListener("click", forward);
    chapters.forEach(function (ch) {
      ch.addEventListener("click", function () { show(parseInt(ch.getAttribute("data-go"), 10) - 1); });
    });
    var restart = player.querySelector("[data-restart]");
    if (restart) { restart.addEventListener("click", function () { show(0); }); }
    // A click on the slide advances it, except in full screen, where taps zoom instead.
    stage.addEventListener("click", function (event) {
      if (gestures.swipedJustNow() || isFull()) { return; }
      if (event.target.tagName === "IMG") { forward(); }
    });
    if (full) { full.addEventListener("click", toggleFull); }
    var zoomIn = player.querySelector("[data-zoom-in]");
    var zoomOut = player.querySelector("[data-zoom-out]");
    var zoomReset = player.querySelector("[data-zoom-reset]");
    if (zoomIn) { zoomIn.addEventListener("click", function () { zoom.zoomBy(ZOOM_STEP); }); }
    if (zoomOut) { zoomOut.addEventListener("click", function () { zoom.zoomBy(1 / ZOOM_STEP); }); }
    if (zoomReset) { zoomReset.addEventListener("click", function () { zoom.reset(); }); }

    document.addEventListener("keydown", function (event) {
      if (event.target.closest && event.target.closest("input, textarea, select")) { return; }
      if (event.key === "ArrowRight" || event.key === " ") { event.preventDefault(); forward(); }
      if (event.key === "ArrowLeft") { back(); }
      if (event.key === "Escape" && isFull() && !document.fullscreenElement) { setFull(false); }
      if (isFull() && (event.key === "+" || event.key === "=")) { zoom.zoomBy(ZOOM_STEP); }
      if (isFull() && event.key === "-") { zoom.zoomBy(1 / ZOOM_STEP); }
      if (isFull() && event.key === "0") { zoom.reset(); }
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
