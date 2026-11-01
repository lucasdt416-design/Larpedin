import itertools
import json
import os
import random
import threading

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b shut down 2026-08-16

TONES = {
    "thought leader": "a visionary thought leader who turns everything into a business lesson",
    "humble brag": "someone humbly bragging, pretending to be modest while flexing hard",
    "hustle bro": "a 5am-grindset hustle bro who relates everything to closing deals",
    "agree?": "an engagement-bait poster who ends with 'Agree?' and begs people to comment",
    "laid off but grateful": "someone who just got laid off and insists it is the best thing that ever happened",
    "AI influencer": "an AI influencer who says this changes everything and you are falling behind",
    "founder who failed 3 startups": "a founder whose 3 startups failed and who sees each failure as a masterclass",
    "recruiter": "an overly excited recruiter who turns everything into a hiring pitch",
    "Gen Z intern": "a Gen Z intern who writes in slang and is way too confident",
}

LEVELS = [
    "mildly corporate, almost normal",
    "a little self-important",
    "noticeably smug",
    "full LinkedIn voice",
    "very dramatic, every sentence is a lesson",
    "wildly inflated, compares yourself to famous CEOs",
    "delusional, this small thing changed your whole career",
    "unhinged, you are now a visionary changing the industry",
    "completely deranged, the universe sent you a sign about B2B sales",
    "maximum lunacy: you cried in the Uber thinking about synergy",
]

GENERATE_PROMPT = (
    "You write parody LinkedIn posts. The user tells you something small and ordinary they did. "
    "Rewrite it as a LinkedIn post in the voice of {voice}. Cringe level {level}/10: {intensity}. "
    "Use short one-line paragraphs, a fake life lesson, a numbered list of 3 takeaways, "
    "a few emojis, and 3-5 hashtags at the end. Keep it under 200 words. "
    "The post is plain text with no markdown or asterisks. "
    "Also write an absurd LinkedIn headline for the author, like 'Visionary | Grass Toucher | Ex-Unemployed', "
    "and 2 or 3 comments from fake connections with silly names and job titles. "
    "Finally, rate the post for buzzwords, emojis, humblebrag and overall cringe. "
    "Each rating is a percentage from 0 to 100, not a count: 0 means none at all, 100 means maximum. "
    "A cringe level {level}/10 post should usually rate around {pct} overall."
)

DELARP_PROMPT = (
    "You translate LinkedIn posts into the brutally honest truth. "
    "Read the post and reply with one short, deadpan sentence that says what actually happened. "
    "Example: 'Thrilled to announce I am starting a new chapter' becomes 'I got laid off.' "
    "Output only that sentence, plain text."
)

SCORE_KEYS = ["buzzwords", "emojis", "humblebrag", "overall"]

GENERATE_SCHEMA = {
    "name": "larp_post",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["post", "headline", "comments", "score"],
        "properties": {
            "post": {"type": "string"},
            "headline": {"type": "string"},
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "title", "text"],
                    "properties": {k: {"type": "string"} for k in ["name", "title", "text"]},
                },
            },
            "score": {
                "type": "object",
                "additionalProperties": False,
                "required": SCORE_KEYS,
                "properties": {k: {"type": "integer"} for k in SCORE_KEYS},
            },
        },
    },
}

FALLBACK_POSTS = [
    "I did something today.\n\n{text}.\n\nMost people would call it ordinary.\n\nI call it a masterclass in leadership.\n\n3 takeaways:\n1. Show up.\n2. Stay humble.\n3. Post about it.\n\n#Growth #Leadership #Grateful",
    "Unpopular opinion:\n\n{text} taught me more than my MBA.\n\nI will not be taking questions. 🙏\n\nAgree?\n\n#Mindset #Hustle #Journey",
]

# ponytail: in-memory gallery, cleared on redeploy/sleep; needs one gunicorn worker so all requests share it.
GALLERY = {}
NEXT_ID = itertools.count(1)
LOCK = threading.Lock()


def groq(messages, temperature, schema=None):
    body = {"model": MODEL, "temperature": temperature, "reasoning_effort": "low", "messages": messages}
    if schema:
        body["response_format"] = {"type": "json_schema", "json_schema": schema}
    r = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json=body,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def badge(overall):
    if overall >= 85:
        return "Certified Lunatic"
    if overall >= 60:
        return "Thought Leader in Training"
    if overall >= 30:
        return "Mildly Corporate"
    return "Suspiciously Normal"


def clamp_score(v):
    try:
        return max(0, min(100, int(v)))
    except (TypeError, ValueError):
        return 50


def text_from_request(limit):
    data = request.get_json(silent=True) or {}
    return data, str(data.get("text", "")).strip()[:limit]


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/health")
def health():
    return jsonify(ok=True)


@app.post("/api/generate")
def generate():
    data, text = text_from_request(500)
    if not text:
        return jsonify(error="Tell us what you did first."), 400
    tone = data.get("tone") if data.get("tone") in TONES else "thought leader"
    try:
        level = max(1, min(10, int(data.get("level", 5))))
    except (TypeError, ValueError):
        level = 5

    system = GENERATE_PROMPT.format(voice=TONES[tone], level=level, intensity=LEVELS[level - 1], pct=level * 10)
    try:
        out = json.loads(groq(
            [{"role": "system", "content": system}, {"role": "user", "content": text}],
            temperature=0.5 + 0.06 * level,
            schema=GENERATE_SCHEMA,
        ))
        result = {
            "post": str(out["post"]).strip(),
            "headline": str(out["headline"]).strip(),
            "comments": [
                {k: str(c.get(k, "")) for k in ["name", "title", "text"]}
                for c in out.get("comments", [])[:3] if isinstance(c, dict)
            ],
            "score": {k: clamp_score(out.get("score", {}).get(k)) for k in SCORE_KEYS},
            "fallback": False,
        }
    except Exception:
        app.logger.exception("Groq generate failed, sending fallback")
        result = {
            "post": random.choice(FALLBACK_POSTS).format(text=text),
            "headline": "Visionary | Professional Larper | Open to Synergy",
            "comments": [{"name": "Chad Synergy", "title": "VP of Vibes", "text": "Congrats on this journey! 🙌"}],
            "score": {"buzzwords": 70, "emojis": 40, "humblebrag": 80, "overall": 75},
            "fallback": True,
        }
    result["badge"] = badge(result["score"]["overall"])

    with LOCK:
        result["id"] = next(NEXT_ID)
        GALLERY[result["id"]] = {"text": text, "tone": tone, "level": level, "votes": 0, **result}
        for old in sorted(GALLERY)[:-50]:
            del GALLERY[old]
    return jsonify(result)


@app.post("/api/delarp")
def delarp():
    _, text = text_from_request(3000)
    if not text:
        return jsonify(error="Paste a LinkedIn post first."), 400
    try:
        truth = groq(
            [{"role": "system", "content": DELARP_PROMPT}, {"role": "user", "content": text}],
            temperature=0.7,
        )
    except Exception:
        app.logger.exception("Groq delarp failed, sending fallback")
        truth = "I did something completely normal and wanted attention."
    return jsonify(truth=truth)


@app.get("/api/gallery")
def gallery():
    keys = ["id", "text", "tone", "level", "post", "headline", "score", "badge", "votes"]
    with LOCK:
        posts = sorted(GALLERY.values(), key=lambda p: (p["votes"], p["id"]), reverse=True)
        return jsonify([{k: p[k] for k in keys} for p in posts])


@app.post("/api/gallery/<int:post_id>/vote")
def vote(post_id):
    with LOCK:
        post = GALLERY.get(post_id)
        if not post:
            return jsonify(error="That post is gone."), 404
        post["votes"] += 1
        return jsonify(votes=post["votes"])


if __name__ == "__main__":
    app.run(debug=True)
