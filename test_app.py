"""Run: .venv/bin/python test_app.py  (no Groq key needed, Groq is faked)"""
import json

import app

FAKE = {
    "post": "I touched grass.", "headline": "Visionary",
    "comments": [{"name": "A", "title": "B", "text": "C"}] * 5,
    "score": {"buzzwords": 150, "emojis": -3, "humblebrag": 90, "overall": 90},
}
app.groq = lambda messages, temperature, schema=None: json.dumps(FAKE) if schema else "I got laid off."
c = app.app.test_client()

assert c.get("/api/health").json == {"ok": True}
assert c.post("/api/generate", json={"text": " "}).status_code == 400

r = c.post("/api/generate", json={"text": "touched grass", "tone": "recruiter", "level": 99}).json
assert r["fallback"] is False and len(r["comments"]) == 3
assert r["score"] == {"buzzwords": 100, "emojis": 0, "humblebrag": 90, "overall": 90}
assert r["badge"] == "Certified Lunatic"

assert c.post("/api/delarp", json={"text": "Thrilled to announce"}).json == {"truth": "I got laid off."}

assert c.post(f"/api/gallery/{r['id']}/vote").json == {"votes": 1}
assert c.post("/api/gallery/9999/vote").status_code == 404
g = c.get("/api/gallery").json
assert g[0]["id"] == r["id"] and g[0]["level"] == 10 and g[0]["tone"] == "recruiter"

def boom(*a, **k):
    raise RuntimeError("groq down")
app.groq = boom
r2 = c.post("/api/generate", json={"text": "made toast"}).json
assert r2["fallback"] is True and "made toast" in r2["post"]
assert c.post("/api/delarp", json={"text": "x"}).json["truth"]

for _ in range(60):
    c.post("/api/generate", json={"text": "spam"})
assert len(c.get("/api/gallery").json) == 50

print("all good")
