const $ = (id) => document.getElementById(id);

const PLACEHOLDERS = [
  "I touched grass",
  "I microwaved leftovers",
  "I lost 3 games of Valorant",
];

let tone = "thought leader";

// ---------- Composer ----------

// Rotate placeholder examples while the textarea is empty.
let placeholderIndex = 0;
setInterval(() => {
  if ($("text").value) return;
  placeholderIndex = (placeholderIndex + 1) % PLACEHOLDERS.length;
  $("text").placeholder = PLACEHOLDERS[placeholderIndex];
}, 3000);

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
      const res = await fetch("/api/health", { cache: "no-store" });
      if (res.ok) break;
    } catch {
      // Server still waking up or offline; retry below.
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  btn.classList.remove("is-warming");
  btn.disabled = false;
  btn.textContent = "Generate post";
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

// ---------- Generate ----------

async function generate(text, tone, level) {
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, tone, level }),
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    // Non-JSON response (e.g. server crashed); fall through to generic error.
  }
  if (!res.ok || !data.post) {
    throw new Error(data.error || `Something went wrong (${res.status}).`);
  }
  return data;
}

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
  btn.classList.toggle("is-loading", busy);
  btn.textContent = busy ? "Larping..." : "Generate post";
  $("result").classList.toggle("is-loading", busy);
  $("result").setAttribute("aria-busy", String(busy));
}

// One request per tone, in parallel. Each gets a skeleton that its card replaces.
async function run(text, tones, level) {
  if ($("generate").disabled) return;
  stopListening();
  clearError();
  if (!text.trim()) {
    showError("Tell us what you did first.");
    $("text").focus();
    return;
  }
  setBusy(true);
  const stopStatus = startStatusLines();
  $("results").replaceChildren();
  $("result").hidden = false;
  const slots = tones.map(() => {
    const slot = $("skeleton-template").content.firstElementChild.cloneNode(true);
    $("results").append(slot);
    return slot;
  });
  try {
    await Promise.all(tones.map(async (t, i) => {
      try {
        renderCard(await generate(text, t, level), slots[i]);
      } catch (err) {
        slots[i].remove();
        showError(err.message);
      }
    }));
  } finally {
    stopStatus();
    if (!$("results").children.length) $("result").hidden = true;
    setBusy(false);
  }
}

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  run($("text").value, [tone], Number($("level").value));
});

// ---------- Profile (name + headline, saved locally) ----------

const PROFILE_KEY = "larpedin.profile";
const DEFAULT_PROFILE = { name: "Your Name", headline: "Visionary | Ex-Nothing | Open to Work" };

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

function bindEditable(el, field) {
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      el.blur();
    }
  });
  el.addEventListener("input", () => {
    profile[field] = el.textContent.trim() || DEFAULT_PROFILE[field];
    saveProfile();
    if (field === "name") syncProfile(el);
  });
  el.addEventListener("blur", () => {
    if (!el.textContent.trim()) el.textContent = DEFAULT_PROFILE[field];
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
function renderCard(data, slot) {
  const item = $("post-card-template").content.firstElementChild.cloneNode(true);
  const q = (sel) => item.querySelector(sel);

  q(".avatar").textContent = initials(profile.name);
  q(".post-author").textContent = profile.name;
  q(".post-headline").textContent = data.headline || profile.headline;
  bindEditable(q(".post-author"), "name");
  bindEditable(q(".post-headline"), "headline");

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
