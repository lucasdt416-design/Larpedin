const $ = (id) => document.getElementById(id);

$("generate").onclick = async () => {
  $("error").textContent = "";
  $("generate").disabled = true;
  $("generate").textContent = "Larping...";
  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("text").value, tone: $("tone").value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    $("post").textContent = data.post;
    $("result").hidden = false;
  } catch (e) {
    $("error").textContent = e.message;
  } finally {
    $("generate").disabled = false;
    $("generate").textContent = "Generate post";
  }
};

$("share").onclick = async () => {
  const post = $("post").textContent;
  await navigator.clipboard.writeText(post);
  window.open(
    "https://www.linkedin.com/feed/?shareActive=true&text=" + encodeURIComponent(post),
    "_blank"
  );
};
