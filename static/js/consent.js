// Analytics cookie consent. Google Analytics itself always runs (see analytics.js), in Consent
// Mode: without consent it counts visits with no cookies. Accepting lets GA use its cookies;
// declining keeps them off and removes any already set. The choice is kept in this browser and
// can be changed from "Cookie settings" in the footer.
(function () {
  "use strict";
  var KEY = "appliedai.consent";
  var banner = document.querySelector("[data-consent]");
  if (!banner) { return; }

  function read() {
    try { return window.localStorage.getItem(KEY); } catch (error) { return null; }
  }
  function write(value) {
    try { window.localStorage.setItem(KEY, value); } catch (error) { /* storage blocked: ask again next visit */ }
  }
  function setAnalyticsStorage(value) {
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", { analytics_storage: value });
    }
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
    setAnalyticsStorage("granted");
  });
  banner.querySelector("[data-consent-decline]").addEventListener("click", function () {
    write("denied");
    hide();
    setAnalyticsStorage("denied");
    removeAnalyticsCookies();
  });
  document.querySelectorAll("[data-consent-open]").forEach(function (button) {
    button.hidden = false;
    button.addEventListener("click", show);
  });

  var choice = read();
  if (choice !== "granted" && choice !== "denied") { show(); }
})();
