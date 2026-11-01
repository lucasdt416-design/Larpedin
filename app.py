import html
import itertools
import json
import os
import random
import threading

import io
import textwrap

import requests
from flask import Flask, jsonify, request, send_file, send_from_directory
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder="static", static_url_path="")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Each model has its own free rate limit (~8K tokens/min, ~200K/day), so if one fails try the next.
# llama-3.3-70b shut down 2026-08-16; check console.groq.com/docs/deprecations before changing.
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

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
STATS = {"posts": 0, "profiles": 0, "battles": 0, "delarps": 0, "tokens": 0, "by_model": {}}


def count(kind):
    with LOCK:
        STATS[kind] += 1


def groq(messages, temperature, schema=None):
    body = {"temperature": temperature, "messages": messages}
    if schema:
        body["response_format"] = {"type": "json_schema", "json_schema": schema}
    for i, model in enumerate(MODELS):
        extra = {"reasoning_effort": "low"} if model.startswith("openai/gpt-oss") else {}
        try:
            r = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                json={**body, **extra, "model": model},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"].strip()
            if schema:
                json.loads(content)  # bad JSON from this model: try the next one
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            if i + 1 == len(MODELS):
                raise
            app.logger.warning("%s failed (%s), trying %s", model, e, MODELS[i + 1])
            continue
        with LOCK:
            STATS["tokens"] += data.get("usage", {}).get("total_tokens", 0)
            STATS["by_model"][model] = STATS["by_model"].get(model, 0) + 1
        return content


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
        STATS["posts"] += 1
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
    count("delarps")
    return jsonify(truth=truth)


@app.get("/api/stats")
def stats():
    with LOCK:
        return jsonify(STATS)


@app.get("/api/gallery")
def gallery():
    keys = ["id", "text", "tone", "level", "post", "headline", "comments", "score", "badge", "votes"]
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


PROFILE_PROMPT = (
    "You build parody LinkedIn profiles. The user tells you their name and what their life is actually like. "
    "Inflate everything into an absurd, self-important LinkedIn profile, cringe level {level}/10: {intensity}. "
    "Every job must be a ridiculous reframing of something ordinary from their real life "
    "(for example, being the family dishwasher becomes 'Head of Ceramic Hygiene Operations'). "
    "Write 3 or 4 experience entries, newest first, each with 2 or 3 bullet points full of fake metrics. "
    "Write 1 or 2 education entries, 6 skills with endorsement counts, and 2 recommendations from fake people. "
    "Plain text only, no markdown. Keep the about section under 80 words."
)


def strict(props):
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


STR, INT = {"type": "string"}, {"type": "integer"}


def array_of(item):
    return {"type": "array", "items": item}


PROFILE_SCHEMA = {
    "name": "larp_profile",
    "strict": True,
    "schema": strict({
        "headline": STR,
        "location": STR,
        "about": STR,
        "open_to": STR,
        "followers": INT,
        "experience": array_of(strict({
            "title": STR, "company": STR, "dates": STR, "location": STR, "bullets": array_of(STR),
        })),
        "education": array_of(strict({"school": STR, "degree": STR, "dates": STR})),
        "skills": array_of(strict({"name": STR, "endorsements": INT})),
        "recommendations": array_of(strict({"name": STR, "title": STR, "relation": STR, "text": STR})),
    }),
}

FALLBACK_PROFILE = {
    "headline": "Visionary | Professional Larper | Open to Synergy",
    "location": "Greater Hustle Area",
    "about": "I turn ordinary days into extraordinary narratives. Passionate about growth, grit and posting about both.",
    "open_to": "Board seats, podcasts, and being called a thought leader",
    "followers": 50000,
    "experience": [{
        "title": "Founder & Chief Vibes Officer", "company": "Self-Employed (Spiritually)",
        "dates": "2024 - Present", "location": "Remote (My Room)",
        "bullets": ["Scaled personal brand 400% by posting daily", "Disrupted the concept of a normal Tuesday"],
    }],
    "education": [{"school": "University of Life", "degree": "MBA in Grindset", "dates": "2020 - 2024"}],
    "skills": [{"name": "Synergy", "endorsements": 99}, {"name": "Thought Leadership", "endorsements": 87}],
    "recommendations": [{
        "name": "Chad Synergy", "title": "VP of Vibes", "relation": "Managed them directly (in a dream)",
        "text": "One of the most visionary people I have ever pretended to know.",
    }],
}


@app.post("/api/profile")
def profile():
    data, text = text_from_request(800)
    name = str(data.get("name", "")).strip()[:60] or "Anonymous Visionary"
    if not text:
        return jsonify(error="Tell us what your life is actually like first."), 400
    try:
        level = max(1, min(10, int(data.get("level", 7))))
    except (TypeError, ValueError):
        level = 7
    system = PROFILE_PROMPT.format(level=level, intensity=LEVELS[level - 1])
    try:
        out = json.loads(groq(
            [{"role": "system", "content": system}, {"role": "user", "content": f"Name: {name}\nMy real life: {text}"}],
            temperature=0.5 + 0.06 * level,
            schema=PROFILE_SCHEMA,
        ))
        out["experience"] = out["experience"][:4]
        out["education"] = out["education"][:2]
        out["skills"] = out["skills"][:8]
        out["recommendations"] = out["recommendations"][:3]
        out["fallback"] = False
    except Exception:
        app.logger.exception("Groq profile failed, sending fallback")
        out = {**FALLBACK_PROFILE, "fallback": True}
    out["name"] = name
    count("profiles")
    return jsonify(out)


BATTLE_PROMPT = (
    "You host Larp Battle, a parody LinkedIn competition. Two people tell you something ordinary they did. "
    "For each one, write a short LinkedIn post (under 120 words, plain text, no markdown, a few emojis and hashtags) "
    "and an absurd headline, at cringe level {level}/10: {intensity}. "
    "Then act as a dramatic judge: score each post 0 to 100 for how delusional and self-important it is, "
    "pick the winner, and write a 2-sentence verdict that roasts both contestants by name."
)

BATTLE_SCHEMA = {
    "name": "larp_battle",
    "strict": True,
    "schema": strict({
        "a": strict({"post": STR, "headline": STR, "score": INT}),
        "b": strict({"post": STR, "headline": STR, "score": INT}),
        "winner": {"type": "string", "enum": ["a", "b"]},
        "verdict": STR,
    }),
}


@app.post("/api/battle")
def battle():
    data = request.get_json(silent=True) or {}
    sides = {}
    for k in ("a", "b"):
        side = data.get(k) if isinstance(data.get(k), dict) else {}
        sides[k] = {
            "name": str(side.get("name", "")).strip()[:40] or f"Contestant {k.upper()}",
            "text": str(side.get("text", "")).strip()[:300],
        }
        if not sides[k]["text"]:
            return jsonify(error=f"{sides[k]['name']} has not said what they did yet."), 400
    try:
        level = max(1, min(10, int(data.get("level", 7))))
    except (TypeError, ValueError):
        level = 7
    user = "\n".join(f"Contestant {k.upper()}: {v['name']} - {v['text']}" for k, v in sides.items())
    try:
        out = json.loads(groq(
            [{"role": "system", "content": BATTLE_PROMPT.format(level=level, intensity=LEVELS[level - 1])},
             {"role": "user", "content": user}],
            temperature=0.5 + 0.06 * level,
            schema=BATTLE_SCHEMA,
        ))
        for k in ("a", "b"):
            out[k]["score"] = clamp_score(out[k]["score"])
        if out["winner"] not in ("a", "b"):
            out["winner"] = "a" if out["a"]["score"] >= out["b"]["score"] else "b"
        out["fallback"] = False
    except Exception:
        app.logger.exception("Groq battle failed, sending fallback")
        winner = random.choice("ab")
        out = {
            k: {"post": random.choice(FALLBACK_POSTS).format(text=v["text"]),
                "headline": "Visionary | Professional Larper", "score": 80 if k == winner else 70}
            for k, v in sides.items()
        }
        out.update(winner=winner, verdict="Both of you are deeply delusional. One of you is slightly more delusional.", fallback=True)
    for k in ("a", "b"):
        out[k]["name"] = sides[k]["name"]
        out[k]["text"] = sides[k]["text"]
    count("battles")
    return jsonify(out)


@app.get("/api/post/<int:post_id>")
def get_post(post_id):
    with LOCK:
        post = GALLERY.get(post_id)
        if not post:
            return jsonify(error="That post is gone. Posts reset when the server restarts."), 404
        return jsonify(dict(post))


def no_emoji(text):
    # The default font has no emoji glyphs; drop them instead of drawing boxes. Keycaps "1️⃣" become "1.".
    def drawable(o):
        return o < 0x2000 or 0x2010 <= o <= 0x206F or 0x20A0 <= o <= 0x20CF or 0x2E80 <= o < 0xFE00 or 0xFE10 <= o < 0x1F000
    text = text.replace("\ufe0f\u20e3", ".").replace("\u20e3", ".")
    return "".join(ch for ch in text if drawable(ord(ch))).strip()


@app.get("/og/<int:post_id>.png")
def og_image(post_id):
    with LOCK:
        post = dict(GALLERY.get(post_id) or {})
    font = ImageFont.load_default
    img = Image.new("RGB", (1200, 630), "#f4f2ee")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, 1160, 590), radius=16, fill="white", outline="#dcdad6", width=2)
    d.ellipse((80, 80, 170, 170), fill="#0a66c2")
    d.text((125, 125), "LV", font=font(size=38), fill="white", anchor="mm")
    d.text((195, 88), "A LarpedIn Visionary", font=font(size=34), fill="#191919")
    headline = no_emoji(post.get("headline", "Visionary | Professional Larper"))
    d.text((195, 134), textwrap.shorten(headline, 60), font=font(size=24), fill="#666666")
    body = no_emoji(post.get("post", "This post went back to being a normal day."))
    lines = []
    for para in body.splitlines():
        lines += textwrap.wrap(para, 58) if para.strip() else []
    y = 205
    for line in lines[:8]:
        d.text((80, y), line, font=font(size=30), fill="#191919")
        y += 40
    if len(lines) > 8:
        d.text((80, y), "...see more", font=font(size=28), fill="#666666")
    if post:
        tag = f"{post['badge']}  |  Cringe {post['score']['overall']}/100"
        d.rounded_rectangle((80, 520, 100 + font(size=26).getlength(tag) + 20, 566), radius=23, fill="#0a66c2")
        d.text((110, 543), tag, font=font(size=26), fill="white", anchor="lm")
    d.text((1120, 543), "LarpedIn (parody)", font=font(size=24), fill="#999999", anchor="rm")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", max_age=300)


@app.get("/p/<int:post_id>")
def permalink(post_id):
    # Fill link-preview meta tags server-side so iMessage/Slack/Discord previews show the post.
    with LOCK:
        post = GALLERY.get(post_id)
    with open(os.path.join(app.static_folder, "post.html"), encoding="utf-8") as f:
        page = f.read()
    title = f"{post['headline']} on LarpedIn" if post else "LarpedIn"
    desc = post["post"][:200] if post else "Turn your ordinary day into a LinkedIn masterpiece."
    image = f"{request.host_url}og/{post_id}.png"
    return (page.replace("{{og_title}}", html.escape(title))
            .replace("{{og_description}}", html.escape(desc))
            .replace("{{og_image}}", html.escape(image)))


if __name__ == "__main__":
    app.run(debug=True)
