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
    ".lnav-box{display:inline-block;background:#0a66c2;color:#fff;border-radius:4px;padding:0 4px;margin-left:2px;font-size:.9em;line-height:1.3;}",
    ".lnav-chip{font-size:10px;color:#666;background:#f4f2ee;border:1px solid #e0dfdc;border-radius:999px;padding:2px 7px;flex-shrink:1;min-width:0;overflow:hidden;text-overflow:ellipsis;}",
    ".lnav-links{display:flex;align-items:stretch;gap:2px;margin-left:auto;height:100%;}",
    ".lnav-link{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:56px;padding:0 8px;text-decoration:none;color:#666;font-size:12px;border-bottom:2px solid transparent;border-radius:4px 4px 0 0;transition:color .15s,background .15s;}",
    ".lnav-link:hover{color:#000;background:#f3f2ef;}",
    ".lnav-link:focus-visible{outline:2px solid #0a66c2;outline-offset:-2px;}",
    ".lnav-ico{font-size:18px;line-height:1.1;}",
    ".lnav-link[aria-current=page]{color:#000;border-bottom-color:#000;font-weight:600;}",
    "@media (max-width:480px){.lnav-in{padding:4px 8px;gap:6px;height:48px}.lnav-brand{font-size:17px}.lnav-chip{font-size:9px;padding:2px 5px}.lnav-link{min-width:44px;padding:0 4px;font-size:10px}.lnav-ico{font-size:16px}}",
    "@media (max-width:360px){.lnav-txt{display:none}.lnav-chip-long{display:none}}",
    "@media (prefers-reduced-motion:reduce){.lnav-link{transition:none}}"
  ].join("\n");

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

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

  var brand = el("a", "lnav-brand", "Larped");
  brand.href = "/";
  brand.setAttribute("aria-label", "LarpedIn home");
  brand.appendChild(el("span", "lnav-box", "in"));
  inner.appendChild(brand);

  var chip = el("span", "lnav-chip", "parody");
  chip.appendChild(el("span", "lnav-chip-long", " · not affiliated"));
  chip.title = "Parody site. Not affiliated with any real professional network.";
  inner.appendChild(chip);

  var links = el("div", "lnav-links");
  [
    ["/", "📝", "Post"],
    ["/profile.html", "👤", "Profile"],
    ["/battle.html", "⚔️", "Battle"],
    ["/gallery.html", "🏆", "Hall of Larp"]
  ].forEach(function (l) {
    var a = el("a", "lnav-link");
    a.href = l[0];
    a.setAttribute("aria-label", l[2]);
    var ico = el("span", "lnav-ico", l[1]);
    ico.setAttribute("aria-hidden", "true");
    a.appendChild(ico);
    a.appendChild(el("span", "lnav-txt", l[2]));
    if (l[0] === current) a.setAttribute("aria-current", "page");
    links.appendChild(a);
  });
  inner.appendChild(links);
  nav.appendChild(inner);

  document.body.insertBefore(nav, document.body.firstChild);
  }
})();
