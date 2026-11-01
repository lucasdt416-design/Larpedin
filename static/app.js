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

if (/Mac|iPhone|iPad/.test(navigator.platform)) {
  $("shortcut-hint").textContent = "⌘ + Enter";
}

$("text").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    $("composer").requestSubmit();
  }
});

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

async function generate(text, tone) {
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, tone }),
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
  return data.post;
}

$("composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("generate");
  if (btn.disabled) return;
  clearError();
  btn.disabled = true;
  btn.classList.add("is-loading");
  btn.textContent = "Larping...";
  try {
    $("post").textContent = await generate($("text").value, tone);
    $("result").hidden = false;
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.classList.remove("is-loading");
    btn.textContent = "Generate post";
  }
});

$("share").onclick = async () => {
  const post = $("post").textContent;
  await navigator.clipboard.writeText(post);
  window.open(
    "https://www.linkedin.com/feed/?shareActive=true&text=" + encodeURIComponent(post),
    "_blank"
  );
};
