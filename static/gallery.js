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

function loadVoted() {
  try {
    return new Set(JSON.parse(localStorage.getItem(VOTED_KEY)) || []);
  } catch {
    return new Set();
  }
}

const voted = loadVoted();

function saveVoted() {
  try {
    localStorage.setItem(VOTED_KEY, JSON.stringify([...voted]));
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

  const name = FAKE_NAMES[p.id % FAKE_NAMES.length];
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

async function poll() {
  try {
    const res = await fetch("/api/gallery", { cache: "no-store", signal: AbortSignal.timeout(10000) });
    if (!res.ok) throw new Error(`Gallery error (${res.status})`);
    render(await res.json());
    showError("");
  } catch {
    showError("Can't reach the server. Retrying...");
  } finally {
    setTimeout(poll, POLL_MS);
  }
}

poll();
