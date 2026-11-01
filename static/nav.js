// LarpedIn top nav. Include with <script src="nav.js" defer></script>.
(function () {
  // Works even if included without defer (document.body may not exist yet).
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }

  function build() {
  if (document.querySelector(".lnav")) return;

  var css = [
    ".lnav{position:sticky;top:0;z-index:1000;box-sizing:border-box;width:100%;align-self:stretch;background:#fff;border-bottom:1px solid #e0dfdc;box-shadow:0 1px 3px rgba(0,0,0,.06);font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;}",
    ".lnav *{box-sizing:border-box;}",
    ".lnav-in{display:flex;align-items:center;gap:8px;max-width:1000px;margin:0 auto;padding:6px 12px;height:52px;white-space:nowrap;}",
    ".lnav-brand{display:flex;align-items:center;gap:1px;text-decoration:none;color:#0a66c2;font-weight:800;font-size:20px;letter-spacing:-.5px;flex-shrink:0;}",
    ".lnav-chip{font-size:10px;color:#666;background:#f4f2ee;border:1px solid #e0dfdc;border-radius:999px;padding:2px 7px;flex-shrink:1;min-width:0;overflow:hidden;text-overflow:ellipsis;}",
    ".lnav-links{display:flex;align-items:stretch;gap:2px;margin-left:auto;height:100%;}",
    ".lnav-link{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:56px;padding:0 8px;text-decoration:none;color:#666;font-size:12px;border-bottom:2px solid transparent;border-radius:4px 4px 0 0;transition:color .15s,background .15s;}",
    "button.lnav-link{font:inherit;background:none;border:0;border-bottom:2px solid transparent;cursor:pointer;-webkit-appearance:none;appearance:none;}",
    ".lnav-link:hover{color:#000;background:#f3f2ef;}",
    ".lnav-link:focus-visible{outline:2px solid #0a66c2;outline-offset:-2px;}",
    ".lnav-ico{font-size:18px;line-height:1.1;}",
    ".lnav-link[aria-current=page]{color:#000;border-bottom-color:#000;font-weight:600;}",
    "@media (max-width:480px){.lnav-in{padding:4px 8px;gap:6px;height:48px}.lnav-brand{font-size:17px}.lnav-chip{font-size:9px;padding:2px 5px}.lnav-link{min-width:44px;padding:0 4px;font-size:10px}.lnav-ico{font-size:16px}}",
    "@media (max-width:360px){.lnav-txt{display:none}.lnav-chip-long{display:none}}",
    "@media (max-width:340px){.lnav-chip{display:none}}",
    "@media (prefers-reduced-motion:reduce){.lnav-link{transition:none}}",
    ".lnav-toast{position:fixed;left:16px;bottom:16px;z-index:1500;max-width:min(360px,calc(100vw - 32px));display:flex;gap:10px;align-items:flex-start;background:#fff;color:#191919;border-radius:8px;padding:12px 14px;box-shadow:0 0 0 1px rgba(0,0,0,.08),0 8px 24px rgba(0,0,0,.18);font:14px/1.35 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;animation:lnav-in .35s ease-out;}",
    ".lnav-toast b{display:block;font-size:12px;color:#666;font-weight:600;margin-bottom:2px;}",
    ".lnav-toast button{font:inherit;cursor:pointer;border:0;background:none;}",
    ".lnav-x{color:#666;font-size:18px;line-height:1;padding:0 2px;margin-left:auto;}",
    ".lnav-cta{display:inline-block;margin-top:6px;background:#e7a33e !important;color:#3b2500;font-weight:700 !important;border-radius:999px;padding:4px 12px;}",
    "@keyframes lnav-in{from{transform:translateY(20px);opacity:0}to{transform:none;opacity:1}}",
    ".lnav-modal{position:fixed;inset:0;z-index:1600;background:rgba(0,0,0,.55);display:grid;place-items:center;padding:16px;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;}",
    ".lnav-card{background:#fff;border-radius:12px;max-width:420px;width:100%;padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.35);text-align:center;color:#191919;}",
    ".lnav-card h2{margin:6px 0 4px;font-size:22px;}",
    ".lnav-card ul{text-align:left;padding-left:20px;margin:14px 0;line-height:1.6;}",
    ".lnav-card .lnav-price{font-size:28px;font-weight:800;margin:8px 0;}",
    ".lnav-card .lnav-price s{font-size:16px;color:#999;font-weight:400;margin-right:6px;}",
    ".lnav-card button{font:inherit;font-weight:700;cursor:pointer;border-radius:999px;padding:10px 20px;border:0;margin:4px;}",
    ".lnav-gold{background:#e7a33e;color:#3b2500;}",
    ".lnav-plain{background:#fff;color:#0a66c2;box-shadow:inset 0 0 0 1px #0a66c2;}",
    ".lnav-prem{font-size:10px;font-weight:800;color:#3b2500;background:#e7a33e;border-radius:999px;padding:2px 7px;flex-shrink:0;}",
    "@media (max-width:400px){.lnav-prem{font-size:0;padding:2px 4px}.lnav-prem::before{content:'P';font-size:12px}}",
    "@media (prefers-reduced-motion:reduce){.lnav-toast{animation:none}}"
  ].join("\n");

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // Installable app (Add to Home Screen): added here so every page gets it, including pages we don't own.
  [["link", { rel: "manifest", href: "/manifest.webmanifest" }],
   ["link", { rel: "apple-touch-icon", href: "/icons/apple-touch-icon.png" }],
   ["meta", { name: "apple-mobile-web-app-capable", content: "yes" }],
   ["meta", { name: "mobile-web-app-capable", content: "yes" }],
   ["meta", { name: "apple-mobile-web-app-title", content: "LarpedIn" }],
   ["meta", { name: "theme-color", content: "#0a66c2" }]
  ].forEach(function (t) {
    var sel = t[0] + (t[1].rel ? '[rel="' + t[1].rel + '"]' : '[name="' + t[1].name + '"]');
    if (document.head.querySelector(sel)) return;
    var e = document.createElement(t[0]);
    Object.keys(t[1]).forEach(function (k) { e.setAttribute(k, t[1][k]); });
    document.head.appendChild(e);
  });

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  var path = location.pathname.replace(/\/+$/, "") || "/";
  var current = path === "/" || path === "/index.html" ? "/" : path;

  var nav = el("nav", "lnav");
  nav.setAttribute("aria-label", "Main");
  var inner = el("div", "lnav-in");

  var brand = el("a", "lnav-brand");
  var logo = el("img");
  logo.src = "/icons/wordmark.png";
  logo.alt = "LarpedIn";
  brand.appendChild(logo);
  brand.href = "/";
  brand.setAttribute("aria-label", "LarpedIn home");
  inner.appendChild(brand);

  var chip = el("span", "lnav-chip", "Parody network");

  chip.title = "Parody site. Not affiliated with any real professional network.";
  inner.appendChild(chip);

  var links = el("div", "lnav-links");
  [
    ["/", "Post"],
    ["/profile.html", "Profile"],
    ["/battle.html", "Battle"],
    ["/jobs.html", "Jobs"],
    ["/gallery.html", "Hall"]
  ].forEach(function (l) {
    var a = el("a", "lnav-link");
    a.href = l[0];
    a.setAttribute("aria-label", l[1]);
    a.appendChild(el("span", "lnav-txt", l[1]));
    if (l[0] === current) a.setAttribute("aria-current", "page");
    links.appendChild(a);
  });
  inner.appendChild(links);
  nav.appendChild(inner);

  document.body.insertBefore(nav, document.body.firstChild);

  // Storage can throw in private / blocked-storage browsers; the gags must never break the nav.
  function getFlag(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function setFlag(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // ---- Premium gag ----
  function markPremium() {
    if (getFlag("lnavPremium") && !nav.querySelector(".lnav-prem")) {
      brand.after(el("span", "lnav-prem", "PREMIUM"));
    }
  }
  markPremium();

  function premiumModal() {
    var modal = el("div", "lnav-modal");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    var card = el("div", "lnav-card");

    card.appendChild(el("h2", "", "LarpedIn Premium"));
    card.appendChild(el("p", "", "Be seen as the visionary you pretend to be."));
    var ul = el("ul");
    ["See who pretended not to view your profile", "Unlimited humblebrags (fair use: 900/day)",
     "Priority access to the word \"synergy\"", "A gold badge that means nothing"].forEach(function (t) {
      ul.appendChild(el("li", "", t));
    });
    card.appendChild(ul);
    var price = el("div", "lnav-price");
    price.appendChild(el("s", "", "$39.99/mo"));
    price.appendChild(document.createTextNode("$0 forever"));
    card.appendChild(price);
    var yes = el("button", "lnav-gold", "Start free trial");
    var no = el("button", "lnav-plain", "Stay irrelevant");
    yes.type = no.type = "button";
    card.appendChild(yes);
    card.appendChild(no);
    modal.appendChild(card);
    function close() { modal.remove(); document.removeEventListener("keydown", onKey); }
    function onKey(e) { if (e.key === "Escape") close(); }
    document.addEventListener("keydown", onKey);
    modal.addEventListener("click", function (e) { if (e.target === modal) close(); });
    no.addEventListener("click", close);
    yes.addEventListener("click", function () {
      setFlag("lnavPremium", "1");
      markPremium();
      while (card.firstChild) card.removeChild(card.firstChild);

      card.appendChild(el("h2", "", "Welcome to Premium"));
      card.appendChild(el("p", "", "You now appear 400% more visionary. Your card will be charged $0.00 in exposure."));
      var ok = el("button", "lnav-gold", "I deserve this");
      ok.type = "button";
      ok.addEventListener("click", close);
      card.appendChild(ok);
      ok.focus();
    });
    document.body.appendChild(modal);
    yes.focus();
  }

  // ---- Fake notifications ----
  var NOTES = [
    ["A recruiter at Hooli viewed your profile"],
    ["Your post is trending in Greater Couch Area"],
    ["Elon's cousin's dentist wants to connect"],
    ["You appeared in 47 searches this week"],
    ["Congratulate Chad on 0 years at Unemployed"],
    ["New InMail: \"Quick question about synergy\""],
    ["You've been selected for LarpedIn Premium", true]
  ];
  var shown = 0;
  var order = NOTES.slice().sort(function () { return Math.random() - 0.5; });
  function toast() {
    if (document.hidden) return;
    var n = order[shown++ % order.length];
    var t = el("div", "lnav-toast");
    t.setAttribute("role", "status");

    var body = el("div");
    body.appendChild(el("b", "", "LarpedIn notification"));
    body.appendChild(document.createTextNode(n[0]));
    if (n[1] && !getFlag("lnavPremium")) {
      body.appendChild(document.createElement("br"));
      var cta = el("button", "lnav-cta", "See offer");
      cta.type = "button";
      cta.addEventListener("click", function () { t.remove(); premiumModal(); });
      body.appendChild(cta);
    }
    t.appendChild(body);
    var x = el("button", "lnav-x", "×");
    x.type = "button";
    x.setAttribute("aria-label", "Dismiss");
    x.addEventListener("click", function () { t.remove(); });
    t.appendChild(x);
    document.querySelectorAll(".lnav-toast").forEach(function (o) { o.remove(); });
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, n[1] ? 9000 : 6000);
  }
  var notices = el("button", "lnav-link", "Inbox");
  notices.type = "button";
  notices.addEventListener("click", function () { shown %= order.length; toast(); });
  links.appendChild(notices);
  }
})();
