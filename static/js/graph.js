// Course map: a small force-directed graph of seasons, lessons, and the ideas that link them.
// No libraries and no network requests. Progress comes from this browser's localStorage only.
(function () {
  "use strict";
  var SVG = "http://www.w3.org/2000/svg";
  var host = document.querySelector("[data-graph]");
  var source = document.getElementById("course-graph");
  if (!host || !source) { return; }

  var data;
  try { data = JSON.parse(source.textContent); } catch (error) { return; }
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var seen = {};
  try { seen = (JSON.parse(window.localStorage.getItem("appliedai.lessons")) || {}).seen || {}; }
  catch (error) { seen = {}; }

  var byId = {};
  var nodes = data.nodes.map(function (n, i) {
    var node = Object.assign({}, n, { x: 0, y: 0, vx: 0, vy: 0, index: i, near: [] });
    byId[node.id] = node;
    return node;
  });
  var links = data.links
    .filter(function (pair) { return byId[pair[0]] && byId[pair[1]]; })
    .map(function (pair) { return { a: byId[pair[0]], b: byId[pair[1]] }; });
  links.forEach(function (l) { l.a.near.push(l.b); l.b.near.push(l.a); });

  // Deterministic start: seasons on a spiral, everything else beside its first neighbour.
  var seasons = nodes.filter(function (n) { return n.kind === "season"; });
  seasons.forEach(function (n, i) {
    var angle = i * 0.9;
    var radius = 60 + i * 22;
    n.x = Math.cos(angle) * radius;
    n.y = Math.sin(angle) * radius;
  });
  nodes.forEach(function (n, i) {
    if (n.kind === "season") { return; }
    var anchor = n.near[0] || { x: 0, y: 0 };
    n.x = anchor.x + Math.cos(i * 2.4) * 30;
    n.y = anchor.y + Math.sin(i * 2.4) * 30;
  });

  function radius(n) {
    if (n.kind === "season") { return n.current ? 13 : 9; }
    if (n.kind === "lesson") { return n.live ? 8 : 5; }
    return 4;
  }
  function restLength(l) {
    if (l.a.kind === "season" && l.b.kind === "season") { return 95; }
    if (l.a.kind === "concept" || l.b.kind === "concept") { return 70; }
    return 42;
  }

  function tick(alpha) {
    var i, j, a, b, dx, dy, d2, d, f;
    for (i = 0; i < nodes.length; i++) {
      a = nodes[i];
      for (j = i + 1; j < nodes.length; j++) {
        b = nodes[j];
        dx = b.x - a.x; dy = b.y - a.y;
        d2 = dx * dx + dy * dy + 0.01;
        f = (300 * alpha) / d2;
        a.vx -= dx * f; a.vy -= dy * f;
        b.vx += dx * f; b.vy += dy * f;
      }
    }
    links.forEach(function (l) {
      dx = l.b.x - l.a.x; dy = l.b.y - l.a.y;
      d = Math.sqrt(dx * dx + dy * dy) || 1;
      f = ((d - restLength(l)) / d) * 0.3 * alpha;
      l.a.vx += dx * f; l.a.vy += dy * f;
      l.b.vx -= dx * f; l.b.vy -= dy * f;
    });
    nodes.forEach(function (n) {
      n.vx -= n.x * 0.01 * alpha;
      n.vy -= n.y * 0.013 * alpha;
      if (n.fixed) { n.vx = 0; n.vy = 0; return; }
      n.vx *= 0.6; n.vy *= 0.6;
      n.x += n.vx; n.y += n.vy;
    });
  }

  for (var t = 0; t < 420; t++) { tick(1 - t / 600); }

  // Build the SVG.
  var svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("class", "graph-svg");
  svg.setAttribute("role", "group");
  svg.setAttribute("aria-label", "Course map. Each season, its lessons, and the ideas that connect them.");
  var linkLayer = document.createElementNS(SVG, "g");
  var nodeLayer = document.createElementNS(SVG, "g");
  svg.appendChild(linkLayer);
  svg.appendChild(nodeLayer);

  links.forEach(function (l) {
    l.el = document.createElementNS(SVG, "line");
    l.el.setAttribute("class", "edge" + (l.a.kind === "concept" || l.b.kind === "concept" ? " edge-concept" : ""));
    linkLayer.appendChild(l.el);
  });

  nodes.forEach(function (n) {
    var group;
    if (n.href) {
      group = document.createElementNS(SVG, "a");
      group.setAttribute("href", n.href);
      group.setAttribute("aria-label", n.code + ", " + (n.title || n.label) + (n.kind === "lesson" ? ", lesson" : ", season"));
    } else {
      group = document.createElementNS(SVG, "g");
      group.setAttribute("aria-hidden", "true");
    }
    var classes = ["node", "node-" + n.kind];
    if (n.kind === "lesson") { classes.push(n.live ? "is-live" : "is-planned"); }
    if (n.kind === "season") { classes.push("is-" + n.type); if (n.current) { classes.push("is-current"); } }
    if (n.slug && seen[n.slug]) { classes.push("is-seen"); }
    group.setAttribute("class", classes.join(" "));

    n.circle = document.createElementNS(SVG, "circle");
    group.appendChild(n.circle);

    // Seasons show their code only; the full title appears on hover, which keeps the map calm.
    n.text = document.createElementNS(SVG, "text");
    n.text.textContent = n.kind === "season" ? n.code : n.label;
    group.appendChild(n.text);

    n.el = group;
    nodeLayer.appendChild(group);

    group.addEventListener("pointerenter", function () { focus(n); });
    group.addEventListener("pointerleave", function () { if (!dragging) { blur(); } });
    group.addEventListener("focus", function () { focus(n); });
    group.addEventListener("blur", blur);
    group.addEventListener("pointerdown", function (event) { startDrag(n, event); });
  });

  host.appendChild(svg);

  var card = host.querySelector("[data-graph-card]");

  function render() {
    links.forEach(function (l) {
      l.el.setAttribute("x1", l.a.x.toFixed(1)); l.el.setAttribute("y1", l.a.y.toFixed(1));
      l.el.setAttribute("x2", l.b.x.toFixed(1)); l.el.setAttribute("y2", l.b.y.toFixed(1));
    });
    nodes.forEach(function (n) { n.el.setAttribute("transform", "translate(" + n.x.toFixed(1) + " " + n.y.toFixed(1) + ")"); });
  }

  function fit() {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(function (n) {
      minX = Math.min(minX, n.x); minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x); maxY = Math.max(maxY, n.y);
    });
    var pad = 70;
    var box = [minX - pad, minY - pad, maxX - minX + pad * 2, maxY - minY + pad * 2];
    svg.setAttribute("viewBox", box.join(" "));
    // Keep dots and labels a constant size on screen, however far the map is zoomed to fit.
    var k = Math.max(box[2] / (host.clientWidth || 1), box[3] / (host.clientHeight || 1));
    svg.style.setProperty("--fs", (12 * k).toFixed(2) + "px");
    svg.style.setProperty("--halo", (4 * k).toFixed(2) + "px");
    nodes.forEach(function (n) {
      n.circle.setAttribute("r", (radius(n) * k).toFixed(2));
      n.text.setAttribute("dy", (-(radius(n) + 7) * k).toFixed(2));
    });
  }

  var resizeTimer;
  window.addEventListener("resize", function () {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(fit, 150);
  });

  function focus(n) {
    svg.classList.add("is-focusing");
    nodes.forEach(function (m) { m.el.classList.remove("is-near", "is-hot"); });
    links.forEach(function (l) { l.el.classList.toggle("is-near", l.a === n || l.b === n); });
    n.el.classList.add("is-hot");
    n.near.forEach(function (m) { m.el.classList.add("is-near"); });
    showCard(n);
  }
  function blur() {
    svg.classList.remove("is-focusing");
    nodes.forEach(function (m) { m.el.classList.remove("is-near", "is-hot"); });
    links.forEach(function (l) { l.el.classList.remove("is-near"); });
    if (card) { card.hidden = true; }
  }

  function showCard(n) {
    if (!card) { return; }
    var kind = n.kind === "concept" ? "Idea" : n.kind === "season" ? (n.type === "leadership" ? "Leadership season" : "Technical season") : (n.live ? "Lesson" : "Lesson, coming soon");
    var connected = n.near.filter(function (m) { return m.kind === "lesson"; }).map(function (m) { return m.code; });
    card.querySelector("[data-card-kind]").textContent = kind + (n.code ? " · " + n.code : "");
    card.querySelector("[data-card-title]").textContent = n.title || n.label;
    var body = n.summary || (n.kind === "concept" && connected.length ? "Comes up in " + connected.join(", ") + "." : "");
    if (n.kind === "season" && n.progress && n.progress[1]) { body += " " + n.progress[0] + " of " + n.progress[1] + " lessons published."; }
    card.querySelector("[data-card-body]").textContent = body;
    card.querySelector("[data-card-cta]").hidden = !n.href;
    card.hidden = false;
  }

  // Dragging, with a short re-settle afterwards.
  var dragging = null;
  var moved = false;
  function toGraph(event) {
    var point = svg.createSVGPoint();
    point.x = event.clientX; point.y = event.clientY;
    return point.matrixTransform(svg.getScreenCTM().inverse());
  }
  function startDrag(n, event) {
    if (event.button !== 0) { return; }
    dragging = n; moved = false; n.fixed = true;
    svg.setPointerCapture && svg.setPointerCapture(event.pointerId);
  }
  svg.addEventListener("pointermove", function (event) {
    if (!dragging) { return; }
    var p = toGraph(event);
    moved = moved || Math.abs(p.x - dragging.x) + Math.abs(p.y - dragging.y) > 2;
    dragging.x = p.x; dragging.y = p.y;
    heat = Math.max(heat, 0.35);
    if (!running) { loop(); }
  });
  svg.addEventListener("pointerup", function () {
    if (dragging) { dragging.fixed = false; }
    dragging = null;
  });
  svg.addEventListener("click", function (event) { if (moved) { event.preventDefault(); moved = false; } }, true);

  var heat = 0;
  var running = false;
  function loop() {
    running = true;
    tick(heat);
    render();
    heat *= 0.97;
    if (heat > 0.02 || dragging) { window.requestAnimationFrame(loop); } else { running = false; }
  }

  render();
  fit();
  host.classList.add("is-ready");
  if (!reduceMotion) {
    // A gentle settle on load, like opening a graph view.
    nodes.forEach(function (n, i) { n.x += Math.cos(i) * 18; n.y += Math.sin(i) * 18; });
    heat = 0.5;
    loop();
  }
})();
