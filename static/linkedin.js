// Real LinkedIn posting. Usage: `if (!(await LarpedInLinkedIn.share(text))) openShareBox(text);`
// share() resolves false when LinkedIn posting is not configured, so the caller keeps the old share box.
// Nothing is ever posted without the user confirming the exact text in the dialog.
(function () {
  var PENDING = "larpedin.liPending";
  var css = [
    ".li-modal{position:fixed;inset:0;z-index:1700;background:rgba(0,0,0,.55);display:grid;place-items:center;padding:16px;font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;}",
    ".li-card{background:#fff;color:#191919;border-radius:12px;max-width:520px;width:100%;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.35);}",
    ".li-card h2{margin:0 0 4px;font-size:20px;}",
    ".li-card p{margin:0 0 12px;color:#666;font-size:14px;}",
    ".li-card textarea{width:100%;box-sizing:border-box;min-height:200px;font:15px/1.4 inherit;font-family:inherit;padding:10px;border:1px solid #ccc;border-radius:8px;}",
    ".li-row{display:flex;gap:8px;justify-content:flex-end;margin-top:12px;flex-wrap:wrap;}",
    ".li-card button{font:inherit;font-weight:700;cursor:pointer;border-radius:999px;padding:10px 18px;border:0;}",
    ".li-go{background:#0a66c2;color:#fff;}.li-go:disabled{opacity:.6;cursor:wait;}",
    ".li-no{background:#fff;color:#0a66c2;box-shadow:inset 0 0 0 1px #0a66c2;}",
    ".li-msg{margin-top:10px;font-size:14px;}.li-msg a{color:#0a66c2;font-weight:700;}",
    ".li-err{color:#b00020;}"
  ].join("\n");

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function status() {
    return fetch("/api/linkedin/me", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .catch(function () { return { enabled: false }; });
  }

  function dialog(text, me) {
    if (!document.getElementById("li-style")) {
      var st = el("style");
      st.id = "li-style";
      st.textContent = css;
      document.head.appendChild(st);
    }
    var opener = document.activeElement;
    var modal = el("div", "li-modal");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    var card = el("div", "li-card");
    card.appendChild(el("h2", "", "Post to your real LinkedIn?"));
    card.appendChild(el("p", "", me.signed_in
      ? "This posts publicly as " + (me.name || "you") + ". Edit it first if you like. There is no undo here."
      : "Sign in with LinkedIn first. Then you will see this text again and can still cancel."));
    var box = el("textarea");
    box.value = text;
    box.setAttribute("aria-label", "Post text");
    box.maxLength = 2900;
    card.appendChild(box);
    var msg = el("div", "li-msg");
    msg.setAttribute("role", "status");
    var row = el("div", "li-row");
    var no = el("button", "li-no", "Cancel");
    var go = el("button", "li-go", me.signed_in ? "Post publicly" : "Sign in with LinkedIn");
    no.type = go.type = "button";
    row.appendChild(no);
    row.appendChild(go);
    card.appendChild(row);
    card.appendChild(msg);
    modal.appendChild(card);

    function close() {
      modal.remove();
      document.removeEventListener("keydown", onKey);
      if (opener && opener.focus) opener.focus();
    }
    function onKey(e) { if (e.key === "Escape") close(); }
    document.addEventListener("keydown", onKey);
    modal.addEventListener("click", function (e) { if (e.target === modal) close(); });
    no.addEventListener("click", close);

    go.addEventListener("click", function () {
      if (!me.signed_in) {
        try { sessionStorage.setItem(PENDING, box.value); } catch (e) {}
        location.href = "/auth/linkedin/start?next=" + encodeURIComponent(location.pathname + location.search);
        return;
      }
      go.disabled = true;
      go.textContent = "Posting…";
      fetch("/api/linkedin/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: box.value })
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error(res.d.error || "LinkedIn did not accept the post.");
          while (row.firstChild) row.removeChild(row.firstChild);
          box.disabled = true;
          msg.textContent = "Posted. Your network has been blessed. ";
          var a = el("a", "", "View it on LinkedIn");
          a.href = res.d.url;
          a.target = "_blank";
          a.rel = "noopener";
          msg.appendChild(a);
          var done = el("button", "li-no", "Close");
          done.type = "button";
          done.addEventListener("click", close);
          row.appendChild(done);
          done.focus();
        })
        .catch(function (err) {
          msg.className = "li-msg li-err";
          msg.textContent = err.message;
          go.disabled = false;
          go.textContent = "Try again";
        });
    });

    document.body.appendChild(modal);
    box.focus();
  }

  function share(text) {
    return status().then(function (me) {
      if (!me.enabled) return false;
      dialog(text, me);
      return true;
    });
  }

  window.LarpedInLinkedIn = { share: share, status: status };

  // Back from LinkedIn sign-in: reopen the dialog with the saved text. Never posts on its own.
  var flag = new URLSearchParams(location.search).get("linkedin");
  if (flag) {
    var clean = new URL(location.href);
    clean.searchParams.delete("linkedin");
    history.replaceState(null, "", clean.pathname + clean.search + clean.hash);
    var pending = null;
    try { pending = sessionStorage.getItem(PENDING); sessionStorage.removeItem(PENDING); } catch (e) {}
    if (flag === "ok" && pending) {
      status().then(function (me) { if (me.signed_in) dialog(pending, me); });
    } else if (flag === "failed") {
      status().then(function () { dialog(pending || "", { signed_in: false }); });
    }
  }
})();
