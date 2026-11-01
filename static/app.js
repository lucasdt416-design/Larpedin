const $ = (id) => document.getElementById(id);

const PLACEHOLDERS = {
  larp: ["I touched grass", "I microwaved leftovers", "I lost 3 games of Valorant"],
  delarp: [
    "Thrilled to announce I'm starting a new chapter...",
    "After 147 rejections, I'm humbled to share...",
    "I don't usually post, but...",
  ],
};

const MODES = {
  larp: { label: "What did you do today?", button: "Generate post", empty: "Tell us what you did first.", maxLength: 500 },
  delarp: { label: "Paste a LinkedIn post", button: "Delarp it", empty: "Paste a LinkedIn post first.", maxLength: 3000 },
};

let tone = "thought leader";
let mode = "larp";

// ---------- Composer ----------

// Rotate placeholder examples while the textarea is empty.
let placeholderIndex = 0;
setInterval(() => {
  if ($("text").value) return;
  placeholderIndex = (placeholderIndex + 1) % PLACEHOLDERS[mode].length;
  $("text").placeholder = PLACEHOLDERS[mode][placeholderIndex];
}, 3000);

document.querySelectorAll(".mode-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (mode === btn.dataset.mode || $("generate").classList.contains("is-loading")) return;
    mode = btn.dataset.mode;
    document.querySelectorAll(".mode-btn").forEach((b) => {
      const active = b === btn;
      b.classList.toggle("is-active", active);
      b.setAttribute("aria-pressed", String(active));
    });
    const m = MODES[mode];
    $("composer").classList.toggle("is-delarp", mode === "delarp");
    $("larp-options").hidden = mode === "delarp";
    $("try-all").hidden = mode === "delarp";
    $("text-label").textContent = m.label;
    $("text").maxLength = m.maxLength;
    $("text").rows = mode === "delarp" ? 6 : 3;
    placeholderIndex = 0;
    $("text").placeholder = PLACEHOLDERS[mode][0];
    if (!$("generate").disabled) $("generate").textContent = m.button;
    clearError();
  });
});

document.querySelectorAll(".vibe-pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    tone = pill.dataset.tone;
    document.querySelectorAll(".vibe-pill").forEach((p) => {
      const active = p === pill;
      p.classList.toggle("is-active", active);
      p.setAttribute("aria-pressed", String(active));
    });
  });
});

const LEVEL_NAMES = [
  "Almost normal", "Self-important", "Smug", "Full LinkedIn", "Dramatic",
  "Wildly inflated", "Delusional", "Unhinged", "Deranged", "Maximum lunacy",
];

function updateLevel() {
  const level = Number($("level").value);
  const label = `Level ${level}: ${LEVEL_NAMES[level - 1]}`;
  $("level-value").textContent = label;
  $("level").setAttribute("aria-valuetext", label);
}

$("level").addEventListener("input", updateLevel);
updateLevel();

if (/Mac|iPhone|iPad/.test(navigator.platform)) {
  $("shortcut-hint").textContent = "⌘ + Enter";
}

$("text").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    $("composer").requestSubmit();
  }
});

// ---------- Voice input ----------

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

function stopListening() {
  if (recognition) recognition.stop();
}

if (SpeechRecognition) {
  const mic = $("mic");
  mic.hidden = false;

  mic.addEventListener("click", () => {
    if (recognition) {
      stopListening();
      return;
    }
    clearError();
    const before = $("text").value.trim();
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;

    recognition.onresult = (e) => {
      const spoken = Array.from(e.results, (r) => r[0].transcript).join("");
      $("text").value = (before ? before + " " : "") + spoken.trim();
    };
    recognition.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        showError("Microphone access was blocked. Allow it in your browser to talk.");
      } else if (e.error !== "no-speech" && e.error !== "aborted") {
        showError(`Voice input failed (${e.error}). Try typing instead.`);
      }
    };
    recognition.onend = () => {
      recognition = null;
      mic.classList.remove("is-listening");
      mic.setAttribute("aria-pressed", "false");
      mic.setAttribute("aria-label", "Speak instead of typing");
    };

    try {
      recognition.start();
      mic.classList.add("is-listening");
      mic.setAttribute("aria-pressed", "true");
      mic.setAttribute("aria-label", "Stop listening");
    } catch (err) {
      recognition = null;
      showError("Couldn't start voice input. Try typing instead.");
    }
  });
}

// ---------- Warm-up ----------

// Render's free plan sleeps; the first request can take ~50s. Keep Generate
// disabled until /api/health answers, but give up after ~75s so it never sticks.
async function warmUp() {
  const btn = $("generate");
  const deadline = Date.now() + 75000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch("/api/health", { cache: "no-store", signal: AbortSignal.timeout(60000) });
      if (res.ok) break;
    } catch {
      // Server still waking up or offline; retry below.
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  btn.classList.remove("is-warming");
  btn.disabled = false;
  btn.textContent = MODES[mode].button;
  $("try-all").disabled = false;
}

warmUp();

// ---------- Errors ----------

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
}

function clearError() {
  $("error").textContent = "";
  $("error").hidden = true;
}

let toastTimer;
function showToast(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => ($("toast").hidden = true), 2000);
}

async function copyText(text, message) {
  try {
    await navigator.clipboard.writeText(text);
    showToast(message);
  } catch {
    showError("Couldn't copy. Select the text and copy it by hand.");
  }
}

// ---------- Generate ----------

const REQUEST_TIMEOUT_MS = 60000;

// POST JSON and return the parsed body. Throws with the backend's error message,
// or a friendly one on timeout / network failure, so the UI never hangs.
async function postJSON(url, body, requiredField) {
  let res;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    if (err.name === "TimeoutError") throw new Error("The thought leaders took too long. Try again.");
    throw new Error("Can't reach the server. Check your connection and try again.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data[requiredField]) {
    throw new Error(data.error || `Something went wrong (${res.status}).`);
  }
  return data;
}

const generate = (text, tone, level) => postJSON("/api/generate", { text, tone, level }, "post");

const STATUS_LINES = [
  "Synergizing...",
  "Leveraging your journey...",
  "Consulting a thought leader...",
  "Circling back...",
  "Adding a humble brag...",
  "Disrupting the narrative...",
  "Crying in the Uber...",
  "Aligning stakeholders...",
];

function startStatusLines() {
  let i = 0;
  $("status").textContent = STATUS_LINES[0];
  const timer = setInterval(() => {
    i = (i + 1) % STATUS_LINES.length;
    $("status").textContent = STATUS_LINES[i];
  }, 1500);
  return () => {
    clearInterval(timer);
    $("status").textContent = "";
  };
}

function setBusy(busy) {
  const btn = $("generate");
  btn.disabled = busy;
  $("try-all").disabled = busy;
  document.querySelectorAll(".regen-btn").forEach((b) => (b.disabled = busy));
  btn.classList.toggle("is-loading", busy);
  btn.textContent = busy ? (mode === "delarp" ? "Delarping..." : "Larping...") : MODES[mode].button;
  $("result").classList.toggle("is-loading", busy);
  $("result").setAttribute("aria-busy", String(busy));
}

const delarp = async (text) => (await postJSON("/api/delarp", { text }, "truth")).truth;

function renderTruth(truth, slot) {
  const item = $("truth-card-template").content.firstElementChild.cloneNode(true);
  item.querySelector(".truth-text").textContent = truth;
  slot.replaceWith(item);
}

const newSkeleton = () => $("skeleton-template").content.firstElementChild.cloneNode(true);

// Runs tasks in parallel. Each task gets a skeleton slot that it replaces with its card.
// With `replaceItem`, that one card is swapped out instead of clearing the results.
async function run(text, tasks, replaceItem = null) {
  if ($("generate").disabled) return;
  stopListening();
  clearError();
  if (!text.trim()) {
    showError(MODES[mode].empty);
    $("text").focus();
    return;
  }
  setBusy(true);
  const stopStatus = startStatusLines();
  let slots;
  if (replaceItem) {
    slots = [newSkeleton()];
    replaceItem.replaceWith(slots[0]);
  } else {
    $("results").replaceChildren();
    slots = tasks.map(() => $("results").appendChild(newSkeleton()));
  }
  $("result").hidden = false;
  const multi = $("results").children.length > 1;
  try {
    await Promise.all(tasks.map(async (task, i) => {
      try {
        await task(slots[i]);
      } catch (err) {
        if (multi) {
          // Other cards are still useful; show the error in this card's place.
          const errItem = $("card-error-template").content.firstElementChild.cloneNode(true);
          errItem.querySelector(".post-vibe").textContent = task.label || "";
          errItem.querySelector(".card-error-text").textContent = err.message;
          slots[i].replaceWith(errItem);
        } else {
          slots[i].remove();
          showError(err.message);
        }
      }
    }));
  } finally {
    stopStatus();
    if (!$("results").children.length) $("result").hidden = true;
    setBusy(false);
  }
}

function vibeLabel(t) {
  const pill = document.querySelector(`.vibe-pill[data-tone="${CSS.escape(t)}"]`);
  return pill ? pill.textContent.trim() : t;
}

// req: {text, tone, level, showVibe}
function generateTask(req) {
  const task = async (slot) => renderCard(await generate(req.text, req.tone, req.level), slot, req);
  task.label = vibeLabel(req.tone);
  return task;
}

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("text").value;
  if (mode === "delarp") {
    run(text, [async (slot) => renderTruth(await delarp(text), slot)]);
  } else {
    run(text, [generateTask({ text, tone, level: Number($("level").value) })]);
  }
});

// Current vibe plus 3 random others, all in parallel.
$("try-all").addEventListener("click", () => {
  const text = $("text").value;
  const level = Number($("level").value);
  const others = [...document.querySelectorAll(".vibe-pill")]
    .map((p) => p.dataset.tone)
    .filter((t) => t !== tone)
    .sort(() => Math.random() - 0.5)
    .slice(0, 3);
  run(text, [tone, ...others].map((t) => generateTask({ text, tone: t, level, showVibe: true })));
});

// ---------- Profile (name + headline, saved locally) ----------

const PROFILE_KEY = "larpedin.profile";
const DEFAULT_PROFILE = { name: "Your Name" };
const DEFAULT_HEADLINE = "Visionary | Ex-Nothing | Open to Work";

function loadProfile() {
  try {
    return { ...DEFAULT_PROFILE, ...JSON.parse(localStorage.getItem(PROFILE_KEY)) };
  } catch {
    return { ...DEFAULT_PROFILE };
  }
}

function saveProfile() {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch {
    // Storage blocked (private mode etc.); edits just won't persist.
  }
}

let profile = loadProfile();

function initials(name) {
  const letters = name.trim().split(/\s+/).map((w) => w[0]).join("");
  return (letters.slice(0, 2) || "?").toUpperCase();
}

// Keep every card's name/avatar in sync after an edit.
function syncProfile(source) {
  document.querySelectorAll(".post-card").forEach((card) => {
    const name = card.querySelector(".post-author");
    if (name !== source) name.textContent = profile.name;
    card.querySelector(".avatar").textContent = initials(profile.name);
  });
}

// Only the name is saved; a headline edit stays on that one card.
function bindEditable(el, field, fallback) {
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      el.blur();
    }
  });
  el.addEventListener("blur", () => {
    if (!el.textContent.trim()) el.textContent = fallback;
  });
  if (field !== "name") return;
  el.addEventListener("input", () => {
    profile[field] = el.textContent.trim() || DEFAULT_PROFILE[field];
    saveProfile();
    syncProfile(el);
  });
}

// ---------- Post card ----------

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const randInt = (min, max) => Math.floor(min + Math.random() * (max - min + 1));
const fmt = (n) => n.toLocaleString("en-US");

function animateCount(el, target) {
  if (reduceMotion) {
    el.textContent = fmt(target);
    return;
  }
  const start = performance.now();
  const duration = 1200;
  const tick = (now) => {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = fmt(Math.round(target * eased));
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

const FAMOUS_LIKERS = [
  "Bill Gates", "Oprah Winfrey", "Satya Nadella", "Gordon Ramsay", "Your Mom",
  "Mark Cuban", "Taylor Swift", "Your Ex", "Richard Branson", "Gary Vee",
];

// data: response from /api/generate. The new card replaces `slot` (a skeleton).
// req is the request that made it, reused by Regenerate.
function renderCard(data, slot, req) {
  const item = $("post-card-template").content.firstElementChild.cloneNode(true);
  const q = (sel) => item.querySelector(sel);

  q(".avatar").textContent = initials(profile.name);
  q(".post-author").textContent = profile.name;
  const headline = data.headline || DEFAULT_HEADLINE;
  q(".post-headline").textContent = headline;
  bindEditable(q(".post-author"), "name", DEFAULT_PROFILE.name);
  bindEditable(q(".post-headline"), "headline", headline);

  if (req.showVibe) {
    q(".post-vibe").textContent = vibeLabel(req.tone);
    q(".post-vibe").hidden = false;
  }

  q(".reaction-name").textContent = FAMOUS_LIKERS[randInt(0, FAMOUS_LIKERS.length - 1)];

  const body = q(".post-body");
  const seeMore = q(".see-more");
  body.textContent = data.post;
  seeMore.addEventListener("click", () => {
    const expanded = body.classList.toggle("is-expanded");
    seeMore.setAttribute("aria-expanded", String(expanded));
    seeMore.textContent = expanded ? "see less" : "...see more";
  });

  if (data.score) {
    q(".badge").textContent = data.badge || "";
    q(".badge").hidden = !data.badge;
    item.querySelectorAll(".gauge").forEach((gauge) => {
      const value = Math.max(0, Math.min(100, Number(data.score[gauge.dataset.key]) || 0));
      gauge.setAttribute("aria-valuenow", String(value));
      gauge.querySelector(".gauge-value").dataset.target = value;
    });
    q(".cringe-report").hidden = false;
  }

  const comments = Array.isArray(data.comments) ? data.comments : [];
  const counts = {
    like: randInt(1200, 9800),
    comment: comments.length + randInt(40, 400),
    repost: randInt(10, 300),
  };
  const showCounts = () => {
    q(".comment-count").textContent = `${fmt(counts.comment)} comments`;
    q(".repost-count").textContent = `${fmt(counts.repost)} reposts`;
  };
  showCounts();

  if (comments.length) {
    const list = q(".post-comments");
    for (const c of comments) {
      const li = document.createElement("li");
      li.className = "comment";
      for (const [cls, text] of [["comment-author", c.name], ["comment-title", c.title], ["comment-text", c.text]]) {
        const span = document.createElement("span");
        span.className = cls;
        span.textContent = text || "";
        li.append(span);
      }
      list.append(li);
    }
    list.hidden = false;
  }

  item.querySelectorAll(".action-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const on = btn.classList.toggle("is-active");
      btn.setAttribute("aria-pressed", String(on));
      const action = btn.dataset.action;
      if (action === "like") {
        counts.like += on ? 1 : -1;
        q(".reaction-count").textContent = fmt(counts.like);
      } else if (action in counts) {
        counts[action] += on ? 1 : -1;
        showCounts();
      }
    });
  });

  q(".share-btn").addEventListener("click", () => shareToLinkedIn(data.post));
  q(".copy-btn").addEventListener("click", () => copyText(data.post, "Copied!"));
  if (data.id != null) {
    q(".link-btn").hidden = false;
    q(".link-btn").addEventListener("click", () => copyText(`${location.origin}/p/${data.id}`, "Link copied!"));
  }
  q(".download-btn").addEventListener("click", (e) => downloadCard(q(".post-card"), e.currentTarget));
  q(".regen-btn").addEventListener("click", () => run(req.text, [generateTask(req)], item));

  slot.replaceWith(item);

  // Only offer "see more" if the clamped text actually overflows.
  seeMore.hidden = body.scrollHeight <= body.clientHeight + 1;
  animateCount(q(".reaction-count"), counts.like);
  item.querySelectorAll(".gauge").forEach((gauge) => {
    const value = Number(gauge.querySelector(".gauge-value").dataset.target || 0);
    animateCount(gauge.querySelector(".gauge-value"), value);
    // Set after insertion so a CSS transition on the fill width can play.
    requestAnimationFrame(() => gauge.style.setProperty("--pct", value));
  });
  return item;
}

async function downloadCard(card, btn) {
  if (!window.html2canvas) {
    showError("Image export didn't load. Take a screenshot instead.");
    return;
  }
  btn.disabled = true;
  try {
    const canvas = await html2canvas(card, {
      scale: 2,
      backgroundColor: "#ffffff",
      logging: false,
      // Export the full post, not the clamped preview.
      onclone: (doc, clone) => {
        clone.querySelector(".post-body").classList.add("is-expanded");
        clone.querySelector(".see-more").hidden = true;
      },
    });
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    if (!blob) throw new Error("empty image");
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "larpedin-post.png";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast("Image saved!");
  } catch {
    showError("Couldn't make the image. Take a screenshot instead.");
  } finally {
    btn.disabled = false;
  }
}

async function shareToLinkedIn(post) {
  try {
    await navigator.clipboard.writeText(post);
  } catch {
    // Clipboard can be blocked; still open the share page with the text prefilled.
  }
  window.open(
    "https://www.linkedin.com/feed/?shareActive=true&text=" + encodeURIComponent(post),
    "_blank"
  );
}
