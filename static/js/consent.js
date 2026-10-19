// Analytics consent. Google Analytics loads only after a visitor accepts; until then nothing is
// requested from Google and no analytics cookies are set. The choice is kept in this browser and
// can be changed from "Cookie settings" in the footer. Withdrawing consent removes GA's cookies.
(function () {
  "use strict";
  var KEY = "appliedai.consent";
  var banner = document.querySelector("[data-consent]");
  if (!banner) { return; }
  var gaId = banner.getAttribute("data-ga-id");
  if (!/^G-[A-Z0-9]{4,20}$/.test(gaId || "")) { return; }
  var loaded = false;

  function read() {
    try { return window.localStorage.getItem(KEY); } catch (error) { return null; }
  }
  function write(value) {
    try { window.localStorage.setItem(KEY, value); } catch (error) { /* storage blocked: ask again next visit */ }
  }

  function loadAnalytics() {
    if (loaded) { return; }
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    // Analytics only: no advertising storage, ad personalisation, or ad user data.
    window.gtag("consent", "default", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
    window.gtag("js", new Date());
    window.gtag("config", gaId, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
    });
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(gaId);
    document.head.appendChild(script);
  }

  // GA's cookies are _ga and _ga_<id>, set on the site's domain and its parent domain.
  function removeAnalyticsCookies() {
    var host = window.location.hostname;
    var domains = ["", host, "." + host.split(".").slice(-2).join(".")];
    document.cookie.split(";").forEach(function (part) {
      var name = part.split("=")[0].trim();
      if (name !== "_ga" && name.indexOf("_ga_") !== 0) { return; }
      domains.forEach(function (domain) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" +
          (domain ? "; domain=" + domain : "");
      });
    });
  }

  function show() { banner.hidden = false; }
  function hide() { banner.hidden = true; }

  banner.querySelector("[data-consent-accept]").addEventListener("click", function () {
    write("granted");
    hide();
    loadAnalytics();
  });
  banner.querySelector("[data-consent-decline]").addEventListener("click", function () {
    var wasGranted = read() === "granted";
    write("denied");
    hide();
    removeAnalyticsCookies();
    // A script already running cannot be unloaded; a reload makes sure it stops.
    if (wasGranted && loaded) { window.location.reload(); }
  });
  document.querySelectorAll("[data-consent-open]").forEach(function (button) {
    button.hidden = false;
    button.addEventListener("click", show);
  });

  var choice = read();
  if (choice === "granted") { loadAnalytics(); } else if (choice !== "denied") { show(); }
})();
