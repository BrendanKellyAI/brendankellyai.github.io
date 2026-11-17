// Google Analytics in Consent Mode. The GA tag loads on every page for every visitor. Until a
// visitor accepts analytics cookies, analytics_storage is denied: GA sets and reads no cookies and
// sends cookieless pings, which Google uses to estimate visits. This runs before the tag so the
// defaults are in place first; consent.js updates them when the visitor chooses.
(function () {
  "use strict";
  var script = document.currentScript;
  var gaId = script && script.getAttribute("data-ga-id");
  if (!/^G-[A-Z0-9]{4,20}$/.test(gaId || "")) { return; }

  var granted = false;
  try {
    granted = window.localStorage.getItem("appliedai.consent") === "granted";
  } catch (error) { /* storage blocked: treat as no choice, so cookies stay off */ }

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  // Analytics only: no advertising storage, ad personalisation, or ad user data, ever.
  window.gtag("consent", "default", {
    analytics_storage: granted ? "granted" : "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
  });
  window.gtag("js", new Date());
  window.gtag("config", gaId, {
    allow_google_signals: false,
    allow_ad_personalization_signals: false,
  });
})();
