"""Run: .venv/bin/python test_app.py  (no Groq key needed, Groq is faked)"""
import json

import os

import app

# groq(): a 429 on the first model falls through to the next model.
class Resp:
    def __init__(self, code, content=""):
        self.status_code = code
        self._content = content
    def raise_for_status(self):
        if self.status_code >= 400:
            raise app.requests.HTTPError(str(self.status_code))
    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}

os.environ.setdefault("GROQ_API_KEY", "test")
calls = []
def fake_post(url, headers, json, timeout):
    calls.append(json["model"])
    return Resp(429) if len(calls) == 1 else Resp(200, " ok ")
real_post, app.requests.post = app.requests.post, fake_post
assert app.groq([], 0.5) == "ok" and calls == app.MODELS[:2]
calls.clear()
app.requests.post = lambda *a, **k: Resp(429)
try:
    app.groq([], 0.5)
    raise AssertionError("expected HTTPError when every model is rate limited")
except app.requests.HTTPError:
    pass
# bad JSON from one model with a schema also falls through
calls.clear()
def bad_then_good(url, headers, json, timeout):
    calls.append(json["model"])
    return Resp(200, "not json" if len(calls) == 1 else '{"a": 1}')
app.requests.post = bad_then_good
assert app.groq([], 0.5, schema={"name": "x"}) == '{"a": 1}' and len(calls) == 2
app.requests.post = real_post

FAKE = {
    "post": "I touched grass.", "headline": "Visionary",
    "comments": [{"name": "A", "title": "B", "text": "C"}] * 5,
    "score": {"buzzwords": 150, "emojis": -3, "humblebrag": 90, "overall": 90},
}
FAKE_PROFILE = {
    "headline": "H", "location": "L", "about": "A", "open_to": "O", "followers": 5,
    "experience": [{"title": "t", "company": "c", "dates": "d", "location": "l", "bullets": ["b"]}] * 6,
    "education": [{"school": "s", "degree": "d", "dates": "d"}],
    "skills": [{"name": "n", "endorsements": 1}], "recommendations": [],
}
SEEN = []
def fake_groq(messages, temperature, schema=None):
    SEEN.append(messages[-1]["content"])
    if not schema:
        return "I got laid off."
    if schema["name"] == "larp_jobs":
        job = {"title": "t", "company": "c", "location": "l", "salary": "s", "applicants": -5,
               "requirements": ["r"] * 9, "perks": "p", "outcome": "offer", "letter": "yay"}
        return json.dumps({"jobs": [job] * 6})
    if schema["name"] == "larp_battle":
        return json.dumps({"a": {"post": "p", "headline": "h", "score": 140}, "b": {"post": "q", "headline": "i", "score": 20},
                           "winner": "a", "verdict": "v"})
    return json.dumps(FAKE_PROFILE if schema["name"] == "larp_profile" else FAKE)
app.groq = fake_groq
c = app.app.test_client()

assert c.get("/api/health").json == {"ok": True}
assert c.post("/api/generate", json={"text": " "}).status_code == 400

r = c.post("/api/generate", json={"text": "touched grass", "tone": "recruiter", "level": 99}).json
assert r["fallback"] is False and len(r["comments"]) == 3
assert r["score"] == {"buzzwords": 100, "emojis": 0, "humblebrag": 90, "overall": 90}
assert r["badge"] == "Certified Lunatic"
c.post("/api/generate", json={"text": "touched grass", "previous": "OLD POST"})
assert "OLD POST" in SEEN[-1] and "even more delusional" in SEEN[-1]

assert c.post("/api/delarp", json={"text": "Thrilled to announce"}).json == {"truth": "I got laid off."}

assert c.post(f"/api/gallery/{r['id']}/vote").json == {"votes": 1}
assert c.post("/api/gallery/9999/vote").status_code == 404
g = c.get("/api/gallery").json
assert g[0]["id"] == r["id"] and g[0]["level"] == 10 and g[0]["tone"] == "recruiter"

p = c.post("/api/profile", json={"name": "Mo", "text": "I wash dishes"}).json
assert p["name"] == "Mo" and len(p["experience"]) == 4 and p["fallback"] is False
assert c.post("/api/profile", json={"name": "Mo"}).status_code == 400
assert c.get(f"/api/profile/{p['id']}").json["name"] == "Mo"
assert c.get("/api/profile/999").status_code == 404
for url in (f"/u/{p['id']}", "/u/999", "/profile.html"):
    assert "{{" not in c.get(url).get_data(as_text=True), url
assert "Mo | H" in c.get(f"/u/{p['id']}").get_data(as_text=True)
assert c.get(f"/og/u/{p['id']}.png").mimetype == "image/png" and c.get("/og/u/999.png").mimetype == "image/png"
assert c.get(f"/api/post/{r['id']}").json["comments"]
assert c.get("/api/post/99999").status_code == 404
page = c.get(f"/p/{r['id']}").get_data(as_text=True)
assert "{{" not in page and f"/og/{r['id']}.png" in page and "Visionary on LarpedIn" in page
assert c.get(f"/og/{r['id']}.png").mimetype == "image/png"

b = c.post("/api/battle", json={"a": {"name": "Mo", "text": "ate"}, "b": {"text": "slept"}}).json
assert b["winner"] == "a" and b["a"]["score"] == 100 and b["a"]["name"] == "Mo" and b["b"]["name"] == "Contestant B"
assert c.post("/api/battle", json={"a": {"text": "ate"}}).status_code == 400

j = c.post("/api/jobs", json={"text": "student"}).json
assert len(j["jobs"]) == 4 and j["jobs"][0]["applicants"] == 0 and len(j["jobs"][0]["requirements"]) == 4 and not j["fallback"]
assert c.post("/api/jobs", json={}).status_code == 400

def boom(*a, **k):
    raise RuntimeError("groq down")
app.groq = boom
r2 = c.post("/api/generate", json={"text": "made toast"}).json
assert r2["fallback"] is True and "made toast" in r2["post"]
assert c.post("/api/delarp", json={"text": "x"}).json["truth"]
assert c.post("/api/profile", json={"text": "x"}).json["fallback"] is True
assert c.post("/api/battle", json={"a": {"text": "x"}, "b": {"text": "y"}}).json["fallback"] is True
assert c.post("/api/jobs", json={"text": "x"}).json["fallback"] is True

for _ in range(60):
    c.post("/api/generate", json={"text": "spam"})
assert len(c.get("/api/gallery").json) == 50

st = c.get("/api/stats").json
assert st["posts"] >= 60 and st["profiles"] == 2 and st["battles"] == 2 and st["delarps"] == 2 and st["jobs"] == 2, st
print("all good")
