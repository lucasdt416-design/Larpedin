// Each tab gets all three headlines in order, one per page load.
(() => {
  const lead = document.getElementById("banner-lead");
  const reveal = document.getElementById("banner-reveal");
  const headlines = [
    [lead.textContent, reveal.textContent],
    ["New role.", "I fed the cat."],
    ["Just shipped.", "I made toast."],
  ];
  const key = "larpedin.nextBanner";
  let index = 0;
  try {
    const next = Number(sessionStorage.getItem(key));
    if (Number.isInteger(next) && next >= 0 && next < headlines.length) index = next;
    sessionStorage.setItem(key, String((index + 1) % headlines.length));
  } catch {
    // A browser that disables storage can still show a headline.
    index = Math.floor(Math.random() * headlines.length);
  }
  [lead.textContent, reveal.textContent] = headlines[index];
})();
