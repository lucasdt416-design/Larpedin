const API_BASE = "https://larpedin-p1fd.onrender.com";

const $ = (id) => document.getElementById(id);
$("site").href = API_BASE;

$("go").onclick = async () => {
  const text = $("text").value.trim().slice(0, 3000);
  if (!text) return;
  $("go").disabled = true;
  $("label").textContent = "";
  $("out").textContent = "Translating corporate…";
  try {
    const r = await fetch(`${API_BASE}/api/delarp`, {
      signal: AbortSignal.timeout(60000),
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!r.ok) throw new Error(r.status);
    const { truth } = await r.json();
    if (!truth) throw new Error("empty");
    $("label").textContent = "What they actually meant:";
    $("out").textContent = truth;
  } catch {
    $("out").textContent = "The truth is temporarily unavailable";
  }
  $("go").disabled = false;
};
