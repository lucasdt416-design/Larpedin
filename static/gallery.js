const $ = (id) => document.getElementById(id);

const PUBLIC_URL = "https://larpedin-p1fd.onrender.com";
const POLL_MS = 5000;
const VOTED_KEY = "larpedin.voted";

const TONE_EMOJI = {
  "thought leader": "🧠",
  "humble brag": "😇",
  "hustle bro": "💪",
  "agree?": "🤔",
  "laid off but grateful": "🙏",
  "AI influencer": "🤖",
  "founder who failed 3 startups": "🚀",
  "recruiter": "🎯",
  "Gen Z intern": "💅",
};

// The gallery API has no author names, so each post gets a stable fake one.
const FAKE_NAMES = [
  "Chad Synergy", "Karen Pivot", "Brayden Disrupt", "Ashleigh Leverage", "Tyler Bandwidth",
  "Madison Runway", "Kyle Ecosystem", "Jordan Blockchain", "Taylor Thoughtleader", "Morgan Hustle",
  "Derek Paradigm", "Skyler Scale", "Brittany Bootstrap", "Logan Learnings", "Avery Alignment",
];

// ---------- QR code ----------

// Point at whatever URL this page is served from, except when running locally.
const isLocal = ["localhost", "127.0.0.1", ""].includes(location.hostname);
const appUrl = isLocal ? PUBLIC_URL : location.origin;
$("qr-url").textContent = appUrl.replace(/^https?:\/\//, "");
if (window.QRCode) {
  new QRCode($("qr"), { text: appUrl, width: 220, height: 220, correctLevel: QRCode.CorrectLevel.M });
} else {
  $("qr").textContent = "QR code unavailable";
}

// ---------- Votes (one per post per browser) ----------

// Stored as {boot, ids}. Post ids restart at 1 when the server restarts, so the
// saved votes only count while /api/health reports the same boot id.
function loadVoted() {
  try {
    const saved = JSON.parse(localStorage.getItem(VOTED_KEY)) || {};
    return { boot: saved.boot ?? null, ids: new Set(saved.ids || []) };
  } catch {
    return { boot: null, ids: new Set() };
  }
}

const votes = loadVoted();
const voted = votes.ids;

function saveVoted() {
  try {
    localStorage.setItem(VOTED_KEY, JSON.stringify({ boot: votes.boot, ids: [...voted] }));
  } catch {
    // Storage blocked; votes still count on the server.
  }
}

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

async function vote(id, card) {
  const btn = card.querySelector(".vote-btn");
  if (voted.has(id)) return;
  btn.disabled = true;
  try {
    const res = await fetch(`/api/gallery/${id}/vote`, { method: "POST", signal: AbortSignal.timeout(10000) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Vote failed (${res.status}).`);
    voted.add(id);
    saveVoted();
    setVotes(card, id, data.votes);
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
  }
}

function setVotes(card, id, votes) {
  const btn = card.querySelector(".vote-btn");
  const mine = voted.has(id);
  card.querySelector(".vote-count").textContent = votes;
  btn.classList.toggle("is-active", mine);
  btn.setAttribute("aria-pressed", String(mine));
  btn.setAttribute("aria-label", `${mine ? "Upvoted" : "Upvote"}, ${votes} vote${votes === 1 ? "" : "s"}`);
}

// ---------- Feed ----------

const cards = new Map(); // id -> <li>
let firstLoad = true;

function buildCard(p) {
  const card = $("gallery-card-template").content.firstElementChild.cloneNode(true);
  const q = (sel) => card.querySelector(sel);

  const name = p.name || FAKE_NAMES[p.id % FAKE_NAMES.length];
  q(".avatar").textContent = TONE_EMOJI[p.tone] || "💼";
  q(".post-author").textContent = name;
  q(".post-headline").textContent = p.headline || "Anonymous Larper";
  q(".gallery-tone").textContent = `${p.tone} · level ${p.level}`;
  q(".gallery-original").textContent = `What they actually did: ${p.text}`;
  q(".post-body").textContent = p.post;
  q(".badge").textContent = p.badge || "";
  q(".gallery-score").textContent = p.score ? `Cringe ${p.score.overall}/100` : "";

  const body = q(".post-body");
  const seeMore = q(".see-more");
  seeMore.addEventListener("click", () => {
    const expanded = body.classList.toggle("is-expanded");
    seeMore.setAttribute("aria-expanded", String(expanded));
    seeMore.textContent = expanded ? "see less" : "...see more";
  });
  q(".vote-btn").addEventListener("click", () => vote(p.id, card));
  return card;
}

function render(posts) {
  const feed = $("feed");
  const seen = new Set();

  posts.forEach((p, i) => {
    seen.add(p.id);
    let card = cards.get(p.id);
    if (!card) {
      card = buildCard(p);
      card.id = `post-${p.id}`;
      cards.set(p.id, card);
      if (!firstLoad) {
        card.classList.add("is-new");
        setTimeout(() => card.classList.remove("is-new"), 4000);
        announce(p);
      }
    }
    setVotes(card, p.id, p.votes);
    // Only move nodes that are out of place, so focus and scroll stay put.
    if (feed.children[i] !== card) feed.insertBefore(card, feed.children[i] || null);
    const seeMore = card.querySelector(".see-more");
    const body = card.querySelector(".post-body");
    if (!body.classList.contains("is-expanded")) {
      seeMore.hidden = body.scrollHeight <= body.clientHeight + 1;
    }
  });

  for (const [id, card] of cards) {
    if (!seen.has(id)) {
      card.remove();
      cards.delete(id);
    }
  }

  $("empty").hidden = posts.length > 0;
  if (firstLoad) focusLinkedPost();
  firstLoad = false;
}

// Arriving from "See it in the Hall of Larp" (#post-12): scroll to it and flash it.
function focusLinkedPost() {
  const card = location.hash.startsWith("#post-") && document.getElementById(location.hash.slice(1));
  if (!card) return;
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.add("is-new");
  setTimeout(() => card.classList.remove("is-new"), 4000);
}

// ---------- Leaderboard ----------

const MEDALS = ["🥇", "🥈", "🥉"];

function renderLeaderboard(posts) {
  const top = posts
    .filter((p) => p.score)
    .sort((a, b) => b.score.overall - a.score.overall || b.votes - a.votes)
    .slice(0, 3);
  $("leaderboard").hidden = top.length === 0;
  $("leaderboard-list").replaceChildren(...top.map((p, i) => {
    const row = document.createElement("li");
    row.className = "leaderboard-row";
    row.dataset.rank = String(i + 1);
    const cell = (cls, text) => {
      const el = document.createElement("span");
      el.className = cls;
      el.textContent = text;
      return el;
    };
    row.append(
      cell("leaderboard-rank", MEDALS[i]),
      cell("leaderboard-name", p.name || FAKE_NAMES[p.id % FAKE_NAMES.length]),
      cell("leaderboard-text", p.text),
      cell("leaderboard-score", `${p.score.overall}/100`),
    );
    return row;
  }));
  const link = $("battle-link");
  link.hidden = top.length < 2;
  if (top.length >= 2) link.href = `/battle.html?a=${top[0].id}&b=${top[1].id}`;
}

// ---------- Presenter mode ----------

function setPresenting(on) {
  document.body.classList.toggle("is-presenting", on);
  $("present").setAttribute("aria-pressed", String(on));
  $("present").textContent = on ? "✕ Exit presenter mode" : "📽️ Presenter mode";
}

$("present").addEventListener("click", async () => {
  const on = !document.body.classList.contains("is-presenting");
  setPresenting(on);
  try {
    if (on && !document.fullscreenElement) await document.documentElement.requestFullscreen();
    if (!on && document.fullscreenElement) await document.exitFullscreen();
  } catch {
    // Fullscreen refused (iframe, iOS); presenter layout still works.
  }
});

// Leaving fullscreen with Esc also leaves presenter mode.
document.addEventListener("fullscreenchange", () => {
  if (!document.fullscreenElement) setPresenting(false);
});

if (new URLSearchParams(location.search).has("present")) setPresenting(true);

let flashTimer;
function announce(p) {
  if (!document.body.classList.contains("is-presenting")) return;
  $("flash").textContent = `🎉 New larp just dropped: "${p.text}"`;
  $("flash").hidden = false;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => ($("flash").hidden = true), 5000);
}

// ---------- Stats ----------

async function loadStats() {
  try {
    const res = await fetch("/api/stats", { cache: "no-store", signal: AbortSignal.timeout(10000) });
    if (!res.ok) return;
    const s = await res.json();
    const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
    // Seed posts don't count, so hide "0 larps" until the room has posted something.
    const parts = s.posts ? [`🔥 ${plural(s.posts, "larp")} posted`] : [];
    if (s.delarps) parts.push(plural(s.delarps, "delarp"));
    if (s.battles) parts.push(plural(s.battles, "battle"));
    $("stats").textContent = parts.join(" · ");
  } catch {
    // Stats are a nice-to-have; keep the last value.
  }
}

// After a server restart, ids are reused for different posts: drop stale votes and cards.
async function checkBoot() {
  try {
    const res = await fetch("/api/health", { cache: "no-store", signal: AbortSignal.timeout(10000) });
    const { boot } = await res.json();
    if (boot == null || boot === votes.boot) return;
    if (votes.boot !== null) {
      for (const card of cards.values()) card.remove();
      cards.clear();
      firstLoad = true; // don't announce the whole reloaded wall as "new"
    }
    votes.boot = boot;
    voted.clear();
    saveVoted();
  } catch {
    // Health check failed; the gallery poll will show the error.
  }
}

async function poll() {
  await checkBoot();
  try {
    const res = await fetch("/api/gallery", { cache: "no-store", signal: AbortSignal.timeout(10000) });
    if (!res.ok) throw new Error(`Gallery error (${res.status})`);
    const posts = await res.json();
    render(posts);
    renderLeaderboard(posts);
    showError("");
    loadStats();
  } catch {
    showError("Can't reach the server. Retrying...");
  } finally {
    setTimeout(poll, POLL_MS);
  }
}

poll();
