const API_BASE = "https://larpedin-p1fd.onrender.com";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "delarp", title: "Delarp this", contexts: ["selection"] });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "delarp" || !tab?.id) return;
  const text = (info.selectionText || "").slice(0, 3000);
  const show = (state, msg) =>
    chrome.scripting.executeScript({ target: { tabId: tab.id }, func: showCard, args: [state, msg, API_BASE] });

  try {
    await show("loading", "");
  } catch {
    return; // chrome:// pages, the Web Store, etc. cannot be scripted
  }

  let truth;
  try {
    const r = await fetch(`${API_BASE}/api/delarp`, {
      signal: AbortSignal.timeout(25000), // the worker can be stopped after ~30 s; show the error card first
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!r.ok) throw new Error(r.status);
    truth = (await r.json()).truth;
    if (!truth) throw new Error("empty");
  } catch {
    return show("error", "The truth is temporarily unavailable");
  }
  show("done", truth);
});

// Runs inside the page (isolated world). Creates the card once, then updates it.
// Globals persist between executeScript calls, so the shadow root is kept on window.
function showCard(state, msg, siteUrl) {
  let c = window.__delarpCard;
  if (!c || !c.host.isConnected) {
    const host = document.createElement("div");
    host.style.cssText = "all:initial;position:fixed;top:16px;right:16px;z-index:2147483647;";
    const root = host.attachShadow({ mode: "closed" });
    // No innerHTML: pages with Trusted Types would block it. Only static strings below.
    const h = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt) e.textContent = txt; return e; };
    const style = h("style", "", `
        .card { width: 340px; background: #fff; color: #1d2226; border-radius: 12px;
          box-shadow: 0 12px 40px rgba(0,0,0,.28), 0 2px 8px rgba(0,0,0,.12);
          font: 14px/1.4 system-ui, -apple-system, "Segoe UI", sans-serif; padding: 14px 16px 12px;
          transform: translateX(120%); transition: transform .3s ease; box-sizing: border-box; }
        .card.in { transform: translateX(0); }
        .top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
        .brand { font-weight: 700; color: #0a66c2; }
        .chip { font-size: 11px; font-weight: 600; color: #0a66c2; border: 1px solid #0a66c2;
          border-radius: 999px; padding: 1px 8px; }
        .x { margin-left: auto; background: none; border: 0; font-size: 20px; line-height: 1;
          cursor: pointer; color: #666; padding: 0 4px; }
        .label { font-size: 12px; color: #666; margin-bottom: 4px; }
        .truth { font-size: 20px; font-weight: 700; line-height: 1.3; margin-bottom: 12px; word-wrap: break-word; }
        .row { display: flex; align-items: center; justify-content: space-between; }
        .copy { background: #0a66c2; color: #fff; border: 0; border-radius: 999px; padding: 6px 16px;
          font: 600 13px system-ui, sans-serif; cursor: pointer; }
        .copy:hover { background: #004182; }
        a { color: #0a66c2; font-size: 12px; text-decoration: none; }
        a:hover { text-decoration: underline; }`);
    const card = h("div", "card"); card.setAttribute("role", "dialog"); card.setAttribute("aria-label", "Delarp");
    const top = h("div", "top"); const x = h("button", "x", "×"); x.setAttribute("aria-label", "Close");
    top.append(h("span", "brand", "Delarp"), h("span", "chip", "parody"), x);
    const row = h("div", "row"); const link = h("a", "", "Made with LarpedIn");
    link.target = "_blank"; link.rel = "noopener";
    row.append(h("button", "copy", "Copy"), link);
    card.append(top, h("div", "label"), h("div", "truth"), row);
    root.append(style, card);
    const $ = (s) => root.querySelector(s);
    c = { host, card: $(".card"), label: $(".label"), truth: $(".truth"), copy: $(".copy"), timer: 0 };
    $("a").href = siteUrl;
    const close = () => { clearTimeout(c.timer); c.card.classList.remove("in"); setTimeout(() => host.remove(), 300); };
    c.arm = () => { clearTimeout(c.timer); c.timer = setTimeout(close, 20000); };
    $(".x").onclick = close;
    c.card.onmouseenter = () => clearTimeout(c.timer);
    c.card.onmouseleave = () => { if (c.done) c.arm(); };
    c.copy.onclick = () =>
      navigator.clipboard.writeText(c.truth.textContent).then(
        () => (c.copy.textContent = "Copied!"),
        () => (c.copy.textContent = "Copy failed"));
    document.documentElement.appendChild(host);
    window.__delarpCard = c;
    requestAnimationFrame(() => requestAnimationFrame(() => c.card.classList.add("in")));
  }

  c.done = state !== "loading";
  c.copy.textContent = "Copy";
  c.copy.style.display = state === "done" ? "" : "none";
  c.label.textContent = state === "loading" ? "" : "What they actually meant:";
  c.truth.textContent = state === "loading" ? "Translating corporate…" : msg;
  if (c.done) c.arm(); else clearTimeout(c.timer);
}
