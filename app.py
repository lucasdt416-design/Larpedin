import html
import itertools
import json
import os
import random
import secrets
import time
import re
import threading
import zlib
import base64

import io
import textwrap

import requests
from flask import Flask, jsonify, redirect, request, send_file, send_from_directory
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # every endpoint truncates long text anyway

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
FEATHERLESS_URL = "https://api.featherless.ai/v1/chat/completions"
# Featherless (paid, better writers) goes first. Its $25 plan runs ONE big-model request at a time and
# answers 429 to the rest, so a busy room spills over to Groq's free models instead of failing.
FEATHERLESS_MODELS = [m for m in os.environ.get("FEATHERLESS_MODELS", "moonshotai/Kimi-K2-Instruct-0905").split(",") if m]
# Each Groq model has its own free rate limit (~8K tokens/min, ~200K/day), so if one fails try the next.
# llama-3.3-70b shut down 2026-08-16; check console.groq.com/docs/deprecations before changing.
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

TONES = {
    "thought leader": "a thought leader. Open with a contrarian hook (for example 'Unpopular opinion:', 'Nobody talks about this, but', 'Hot take:' or 'Here is what 99% of people get wrong:'; pick one at random). Turn the event into a principle and preach it to the reader.",
    "humble brag": "a humble-bragger. Open with fake reluctance such as 'I don't usually post about myself, but' and slip in prestige while pretending it is no big deal.",
    "hustle bro": "a hustle bro. Open with a time stamp only if they mentioned a time; otherwise open with a short punchy fragment ('While you were scrolling, I executed.'). Punchy sentences. Everything is discipline, grind and closing.",
    "agree?": "an engagement farmer. Open with a bold claim built from the event, and make the takeaway line exactly 'Agree?'.",
    "laid off but grateful": "someone recently laid off and aggressively grateful. Open with 'Some personal news.' Frame the event as proof that the layoff was a gift. Mention being #OpenToWork.",
    "AI influencer": "an AI influencer. Explain how the event is basically what AI does, warn that people who don't get it will be left behind, and offer a 'framework' in numbered steps.",
    "founder who failed 3 startups": "a founder whose three startups failed. Open by mentioning the three failures, then present the event as the lesson none of them taught. Investors are 'welcome to reach out'.",
    "recruiter": "an over-excited recruiter. Treat the event as a hiring signal, end with 'We're hiring!' or 'My DMs are open', and use phrases like 'rockstar' and 'culture fit'.",
    "Gen Z intern": "a Gen Z intern. Write in lowercase with Gen Z slang ('lowkey', 'no cap', 'it's giving', 'ate', 'main character energy'), still bragging like a LinkedIn post. Up to 2 emojis allowed.",
}

# Cringe = how grandly you present YOUR OWN event and what it proves about you. Never surreal,
# never a different invented event.
LEVELS = [
    "modest and sincere; 40-60 words; it could pass as a real post",
    "proud, one small humblebrag; 50-70 words",
    "a proud milestone that claims a couple of real-sounding skills; 60-90 words",
    "full LinkedIn voice: grand framing, skills, gratitude; 80-110 words",
    "confident: proof you are ready for big things; 90-120 words",
    "a major career milestone with impressive-sounding skills; 100-130 words",
    "grandiose: a defining moment of your leadership journey; 110-140 words",
    "thought-leader mode: you now have advice for everyone; 120-150 words",
    "visionary: clearly the start of something historic for you; 130-160 words",
    "maximum larp: legend-in-the-making energy, still completely straight-faced; 140-170 words",
]

# Blind A/B (3 judges, 12 inputs): this vibe-first prompt won 34 of 36 judgments over the template prompt.
# About half of posts get a couple of emojis, like real LinkedIn; kept out of the skills and hashtag lines
# so post_shape_ok() still sees "1." and "#" at the start of those lines.
EMOJI_RULES = [
    "none in this post.",
    "use 1 or 2 emojis a real LinkedIn poster would use (for example 🚀 ✅ 💡 🙌 📈 👇), only in the opening "
    "paragraph or the takeaway line, never at the start of a line, never in the numbered skills or the hashtag line.",
]

GENERATE_PROMPT = (
    "You ghostwrite LinkedIn posts for someone who is LARPING: making something ordinary they did sound "
    "impressive WITHOUT lying. Write in the first person as {voice}\n"
    "Grandness level {level}/10: {intensity}. Follow that word range.\n"
    "THE TRUTH CONTRACT (never break it):\n"
    "- Every sentence must be literally true of what they told you.\n"
    "- Never invent titles, employers, teams, clients, people, results, numbers or outcomes they did not state "
    "(no 'flawless', 'first try', 'promoted', 'my team', 'mentors'). Numbers only if they follow from what they said.\n"
    "THE LARP:\n"
    "- Never name the ordinary object or activity. Describe it only through true but impressive-sounding "
    "abstractions, so a reader assumes it was something big. 'flipped a pancake' -> 'executed a time-critical "
    "maneuver in a high-heat environment'. 'took a nap' -> 'blocked a deliberate offline window to reset'.\n"
    "- Never admit it was ordinary: no 'it may sound small', no 'technically it was', no plain-truth confession.\n"
    "- Pick the details that sound impressive and leave out the rest. Let the reader infer the importance.\n"
    "- Prestige that is actually true may be named (a well-known university, a city).\n"
    "- Never add circumstances they did not state: no time of day, no 'alone' or 'without help', no audience or "
    "anyone's reaction, no network. Never describe how good the result was (no perfect, flawless, golden, impressed).\n"
    "- Also avoid the obvious related words that would give it away (for a pancake: no kitchen, batter, flip, pan).\n"
    "- At levels 9-10 go all the way on what it means (legacy, 'they will teach this one day', a keynote you are "
    "'considering'), still about the same disguised event and still true.\n"
    "- No surreal or cosmic metaphors, no talking objects, no section labels, no markdown.\n"
    "- Emojis: {emoji}\n"
    "STRUCTURE (always exactly these four parts, in this order, separated by exactly one blank line, with no other "
    "blank lines anywhere):\n"
    "1. An opening paragraph of 2 to 4 sentences, written as flowing prose on one line (not one sentence per line). "
    "The voice's hook goes at the start of it.\n"
    "2. One short line introducing the skills (for example 'What it sharpened:'), followed directly by 3 numbered "
    "lines, each a real career skill and how the moment showed it.\n"
    "3. One takeaway sentence. If the voice has a signature ending ('Agree?', 'We're hiring!'), it goes here.\n"
    "4. 2 to 4 hashtags on one line.\n"
    "Before the post, fill real_event (the plain truth), true_details (the facts you may use) and disguise "
    "(how you will describe it without naming it). After the post, fill claims_check: list any sentence in the "
    "post that claims something not supported by true_details. It must be an empty string.\n"
    "Two examples of the style and structure (different topics; never reuse their wording):\n"
    "What they did: 'I made coffee'. Post:\n"
    "Some personal news. Today I owned an end-to-end process from sourcing to delivery, with every variable on me: "
    "precise measurement, heat and timing. And I delivered.\n\n"
    "What it sharpened:\n"
    "1. Ownership: no handoffs, no excuses.\n"
    "2. Precision: small measurements decide the outcome.\n"
    "3. Execution: a plan only matters once it ships.\n\n"
    "Most people never see the work that happens before the result.\n\n"
    "#Ownership #Execution #Precision\n"
    "What they did: 'I returned a library book'. Post:\n"
    "I don't usually post about this, but today I closed out a long-running commitment. It had a hard deadline, "
    "and I met it with no extensions and no excuses.\n\n"
    "What it reinforced:\n"
    "1. Accountability: a deadline is a promise.\n"
    "2. Follow-through: finishing is a skill.\n"
    "3. Integrity: doing what you said you'd do, even when nobody is checking.\n\n"
    "Reliability isn't glamorous, but people remember who delivered.\n\n"
    "#Accountability #Integrity #FollowThrough\n"
    "Also write the author's LinkedIn headline: 2 or 3 impressive descriptors separated by pipes, or a short "
    "mission statement, that are true of them given the event (descriptors, never job titles they don't hold). "
    "No company names; do not start with 'Visionary' or 'Chief'; never use 'Whisperer'.\n"
    "Also write 3 comments from fake connections with realistic, varied names and job titles (never Alex Rivera, "
    "Alex Chen, Priya Sharma, Maya Patel or Jordan, and never the author's own name; commenters never address themselves). "
    "Mix the reactions: always one humblebrag that one-ups the author, plus two of these at random: sincere "
    "congratulations, 'This.', someone tagging a friend, a recruiter or coach pitching something, someone asking "
    "for the template. Never label a comment with its type (no 'Humblebrag:' or 'Recruiter:').\n"
    "Finally, rate the post for buzzwords, emojis, humblebrag and overall cringe. "
    "Each rating is a percentage from 0 to 100, not a count: 0 means none at all, 100 means maximum. "
    "A level {level}/10 post should usually rate around {pct} overall."
)


DELARP_PROMPT = (
    "You translate LinkedIn posts into the brutally honest, funny truth, in the first person, as the author. "
    "Expose the real motive or the boring reality behind the corporate language. Be specific and petty, not generic. "
    "Reply with one or two short deadpan sentences, under 25 words total. Plain text, no quotes, no emojis.\n"
    "Examples:\n"
    "'Thrilled to announce I am starting a new chapter!' -> I got laid off and I am scared.\n"
    "'Humbled to accept a position at a Big 4 firm' -> I will now work 80 hours a week to make spreadsheets slightly bluer.\n"
    "'I rejected a candidate who did not send a thank you email. Agree?' -> I have a tiny bit of power and I need you to know.\n"
    "'We just closed our pre-seed round from friends and family!' -> My parents gave me money and I called it a funding round.\n"
    "'Taking time to reflect and recharge before my next adventure' -> I have been applying to jobs for four months."
)

SCORE_KEYS = ["buzzwords", "emojis", "humblebrag", "overall"]

GENERATE_SCHEMA = {
    "name": "larp_post",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["real_event", "true_details", "disguise", "post", "claims_check", "headline", "comments", "score"],
        "properties": {
            # Planned before the post (truth, usable facts, disguise), audited right after it.
            "real_event": {"type": "string"},
            "true_details": {"type": "string"},
            "disguise": {"type": "string"},
            "post": {"type": "string"},
            "claims_check": {"type": "string"},
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
    "Unpopular opinion:\n\nToday I did this: {text}.\n\nIt taught me more than my MBA.\n\nI will not be taking questions.\n\nAgree?\n\n#Mindset #Hustle #Journey",
    "5:00 AM. Cold shower. Then I did this:\n\n{text}.\n\nWhile you were sleeping, I was compounding.\n\nThe grind does not care about your feelings.\n\n#Grindset #5AMClub #NoDaysOff",
    "I almost didn't share this.\n\nBut vulnerability is leadership.\n\nToday, {text}.\n\nI cried. My team cried. The intern is still crying.\n\nGrateful for this journey.\n\n#Authenticity #Grateful #Leadership",
    "Everyone asks me how I stay so productive.\n\nHere is my secret. Today: {text}.\n\nThat's it. That's the post.\n\n(DM me for my $499 course on it.)\n\n#Productivity #Founder #Mindset",
    "My 4-year-old asked me: 'Why do you work so hard?'\n\nI didn't answer. I just showed her: {text}.\n\nShe understood. Now she is a VP.\n\n#Parenting #Leadership #Legacy",
    "Hot take\n\nWhat I did today: {text}.\n\nThat is the new MBA.\n\nI said what I said.\n\nRepost if you agree.\n\n#Disruption #FutureOfWork #Agree",
    "Today: {text}.\n\nTurns out that is basically B2B sales.\n\nYou show up. You add value. You follow up.\n\nHumbled. Honored. Hiring.\n\n#Sales #Growth #Hiring",
]

FALLBACK_HEADLINES = [
    "Founder, CEO, and only employee of Vibes Inc.",
    "Helping 0 people find their purpose | Keynote speaker (at home)",
    "Chief Synergy Officer @ My Bedroom | Forbes 30 Under 30 (pending)",
    "Thought Leader | Podcast host (2 episodes) | Open to board seats",
]

FALLBACK_COMMENTS = [
    {"name": "Chad Synergy", "title": "VP of Vibes at Disruptr", "text": "Congrats on this journey! "},
    {"name": "Brenda Bandwidth", "title": "Chief Alignment Officer", "text": "This. So much this."},
    {"name": "Kyle Kpi", "title": "Growth Hacker | Ex-Intern", "text": "Love this! Let's circle back offline. "},
    {"name": "Recruiter Rita", "title": "Talent Ninja at Hooli", "text": "Hi! Are you open to a role that pays in exposure?"},
]

# ponytail: tiny blocklist so slurs and sexual content never reach the projector wall; a real moderation API if this grows.
BLOCKED = re.compile(
    r"\b(n[i1]gg\w*|f[a@]gg?ots?|retards?|tr[a@]nn(y|ies)|k[i1]kes?|sp[i1]cs?|ch[i1]nks?|wetbacks?|c[u*]nts?|"
    r"wh[o0]res?|sl[u*]ts?|rap(e|ed|es|ist|ing)|porn\w*|nudes?|dicks?|cocks?|pussy|tits|cum|nazis?|hitler|kys|"
    r"kill (yo)?ur ?self)\b", re.I)


def is_clean(*texts):
    return not any(BLOCKED.search(t or "") for t in texts)

# ponytail: in-memory gallery, cleared on redeploy/sleep; needs one gunicorn worker so all requests share it.
GALLERY = {}
NEXT_ID = itertools.count(1)
PROFILES = {}
NEXT_PROFILE_ID = itertools.count(1)
LOCK = threading.Lock()
def load_seeds():
    # Fill the Hall with good posts on every start, so the wall is never empty after a Render restart.
    path = os.path.join(os.path.dirname(__file__), "seed_posts.json")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for i, p in enumerate(json.load(f)):
            pid = next(NEXT_ID)
            GALLERY[pid] = {**clean_post(p), "id": pid, "votes": p.get("votes", 0), "fallback": False, "seed": True}


STATS = {"posts": 0, "profiles": 0, "battles": 0, "delarps": 0, "jobs": 0, "tokens": 0, "by_model": {}}


def count(kind):
    with LOCK:
        STATS[kind] += 1


def routes(fast=False):
    # (url, api key env var, model, supports strict json_schema); providers without a key are skipped.
    # fast=True skips Featherless: Kimi needs ~65-90 s for the long profile/jobs JSON, too slow on stage.
    out = [] if fast else [(FEATHERLESS_URL, "FEATHERLESS_API_KEY", m, False) for m in FEATHERLESS_MODELS]
    out += [(GROQ_URL, "GROQ_API_KEY", m, True) for m in MODELS]
    return [r for r in out if os.environ.get(r[1])]


def parse_json(text, schema):
    # Featherless has no strict JSON mode: accept code fences or chatter around one JSON object,
    # and insist on the schema's required keys so a half answer moves on to the next model.
    text = text.strip()
    obj = json.loads(text[text.index("{"):text.rindex("}") + 1])
    missing = [k for k in schema["schema"]["required"] if k not in obj]
    if missing:
        raise ValueError(f"missing keys {missing}")
    return obj


def llm(messages, temperature, schema=None, fast=False):
    todo = routes(fast)
    if not todo:
        raise RuntimeError("no LLM API key configured")
    for i, (url, key_env, model, strict) in enumerate(todo):
        body = {"model": model, "temperature": temperature, "messages": messages}
        if schema and strict:
            body["response_format"] = {"type": "json_schema", "json_schema": schema}
        elif schema:
            body["messages"] = messages + [{"role": "system", "content":
                "Reply with ONE JSON object only: no prose, no markdown fences. "
                "It must match this JSON Schema exactly: " + json.dumps(schema["schema"])}]
            body["max_tokens"] = 1800
        if model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {os.environ[key_env]}"}, json=body,
                              timeout=30 if url == GROQ_URL else 60)
            r.raise_for_status()
            data = r.json()
            content = (data["choices"][0]["message"].get("content") or "").strip()
            if not content:
                raise ValueError("empty content")
            if schema:
                content = json.dumps(parse_json(content, schema))
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            if i + 1 == len(todo):
                raise
            app.logger.warning("%s failed (%s), trying %s", model, str(e)[:200], todo[i + 1][2])
            continue
        with LOCK:
            STATS["tokens"] += (data.get("usage") or {}).get("total_tokens", 0)
            STATS["by_model"][model] = STATS["by_model"].get(model, 0) + 1
        return content


def post_shape_ok(text):
    # The agreed layout: paragraph, intro line + exactly 3 numbered skills, takeaway, hashtag line.
    text = tidy_post(text)
    last = text.split("\n")[-1].strip()
    return len(re.findall(r"^\s*\d+[.)]", text, re.M)) == 3 and last.startswith("#") and text.count("\n\n") == 3


def tidy_post(text):
    # Some models emit a literal backslash-n or stack blank lines; keep at most one blank line between parts.
    text = str(text).replace("\\n", "\n")
    lines = [line.rstrip() for line in text.strip().split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))


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


BOOT_ID = random.randrange(1 << 30)  # changes on every restart, so clients can drop stale post ids (votes)


@app.get("/api/health")
def health():
    return jsonify(ok=True, boot=BOOT_ID)


@app.post("/api/generate")
def generate():
    data, text = text_from_request(500)
    if not text:
        return jsonify(error="Tell us what you did first."), 400
    tone = data.get("tone") if data.get("tone") in TONES else "thought leader"
    name = str(data.get("name", "")).strip()[:60]
    try:
        level = max(1, min(10, int(data.get("level", 5))))
    except (TypeError, ValueError):
        level = 5

    system = GENERATE_PROMPT.format(voice=TONES[tone], level=level, intensity=LEVELS[level - 1], pct=level * 10,
                                    emoji=random.choice(EMOJI_RULES))
    previous = str(data.get("previous", "")).strip()[:2000]
    user = text if not previous else (
        f"What I actually did: {text}\n\nMy last post about it:\n{previous}\n\n"
        "Rewrite it one level grander. Same real event, still never named, first person, straight-faced. "
        "Frame it more grandly and say more about what it means, but keep the truth contract: invent no new "
        "events, people, results, companies or statistics."
    )
    try:
        for attempt in range(3):
            out = json.loads(llm(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=min(0.85, 0.55 + 0.03 * level),
                schema=GENERATE_SCHEMA,
            ))
            flagged = str(out.get("claims_check", "")).strip().strip(".").lower()
            clean = flagged in ("", "none", "n/a", "[]", "empty", "no")
            if clean and post_shape_ok(str(out.get("post", ""))):
                break
            app.logger.info("retrying post (claims_check=%r, shape ok=%s)", flagged[:80], post_shape_ok(str(out.get("post", ""))))
        result = {
            "post": tidy_post(out["post"]),
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
            "post": random.choice(FALLBACK_POSTS).format(text=text.rstrip(".!?")),
            "headline": random.choice(FALLBACK_HEADLINES),
            "comments": random.sample(FALLBACK_COMMENTS, 3),
            "score": {k: random.randint(55, 95) for k in SCORE_KEYS},
            "fallback": True,
        }
    result["badge"] = badge(result["score"]["overall"])

    result["name"] = name
    with LOCK:
        STATS["posts"] += 1
        result["id"] = next(NEXT_ID)
        if is_clean(text, name, result["post"], result["headline"]):  # anything flagged never reaches the wall
            GALLERY[result["id"]] = {"text": text, "tone": tone, "level": level, "votes": 0, **result}
        for old in sorted(GALLERY)[:-50]:
            del GALLERY[old]
    result["share_url"] = f"/p/{result['id']}?d=" + pack(clean_post({**result, "text": text, "tone": tone, "level": level}))
    return jsonify(result)


@app.post("/api/delarp")
def delarp():
    _, text = text_from_request(3000)
    if not text:
        return jsonify(error="Paste a LinkedIn post first."), 400
    try:
        truth = llm(
            [{"role": "system", "content": DELARP_PROMPT}, {"role": "user", "content": text}],
            temperature=0.9,
        )
    except Exception:
        app.logger.exception("Groq delarp failed, sending fallback")
        truth = "I did something completely normal and wanted attention."
    count("delarps")
    return jsonify(truth=truth)


TTS_URL = "https://api.groq.com/openai/v1/audio/speech"
TTS_VOICES = {"troy", "hannah", "austin"}


@app.post("/api/tts")
def tts():
    # Orpheus takes at most 200 characters per request, so the page sends one sentence at a time.
    data, text = text_from_request(200)
    if not text:
        return jsonify(error="Nothing to say."), 400
    voice = data.get("voice") if data.get("voice") in TTS_VOICES else "troy"
    try:
        r = requests.post(
            TTS_URL,
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
            json={"model": "canopylabs/orpheus-v1-english", "input": text, "voice": voice, "response_format": "wav"},
            timeout=30,
        )
        r.raise_for_status()
    except (requests.RequestException, KeyError) as e:
        detail = getattr(getattr(e, "response", None), "text", "")[:300]
        app.logger.warning("TTS failed: %s %s", e, detail)
        return jsonify(error="Voice unavailable, use the browser voice."), 502
    return app.response_class(r.content, mimetype="audio/wav")


@app.get("/api/stats")
def stats():
    with LOCK:
        return jsonify(STATS)


@app.get("/api/gallery")
def gallery():
    keys = ["id", "name", "text", "tone", "level", "post", "headline", "comments", "score", "badge", "votes", "seed"]
    with LOCK:
        posts = sorted(GALLERY.values(), key=lambda p: (p["votes"], p["id"]), reverse=True)
        return jsonify([{k: p.get(k, False) if k == "seed" else p[k] for k in keys} for p in posts])


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
        out = json.loads(llm(
            [{"role": "system", "content": system}, {"role": "user", "content": f"Name: {name}\nMy real life: {text}"}],
            temperature=0.5 + 0.06 * level,
            schema=PROFILE_SCHEMA,
            fast=True,
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
    with LOCK:
        out["id"] = next(NEXT_PROFILE_ID)
        PROFILES[out["id"]] = out
        for old in sorted(PROFILES)[:-50]:
            del PROFILES[old]
    out = {**out, "share_url": f"/u/{out['id']}?d=" + pack(clean_profile(out))}
    return jsonify(out)


BATTLE_PROMPT = (
    "You host Larp Battle, a parody LinkedIn competition. Two people tell you something ordinary they did. "
    "For each one, write a short LinkedIn post (under 120 words, plain text, no markdown, no emojis, a few hashtags) "
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
        out = json.loads(llm(
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


JOBS_PROMPT = (
    "You write parody job listings for LarpedIn, a LinkedIn parody. The user describes who they really are. "
    "Write 4 absurd job listings that 'match' them, from fake companies with silly names. "
    "Each has a corporate title, a location like 'Remote (mandatory office 5 days)', a funny salary line, "
    "an applicant count, 3 ridiculous requirements (for example '15 years of experience in a 3 year old framework'), "
    "and a perks line. For each job, also write the letter the applicant receives right after clicking Easy Apply: "
    "pick 'offer' for exactly one job and 'rejection' for the rest. Letters are under 70 words, signed by a fake recruiter, "
    "overly enthusiastic, and the rejections thank them for their 'journey'. Plain text, no markdown."
)

JOBS_SCHEMA = {
    "name": "larp_jobs",
    "strict": True,
    "schema": strict({
        "jobs": array_of(strict({
            "title": STR, "company": STR, "location": STR, "salary": STR, "applicants": INT,
            "requirements": array_of(STR), "perks": STR,
            "outcome": {"type": "string", "enum": ["offer", "rejection"]}, "letter": STR,
        })),
    }),
}

FALLBACK_JOBS = [{
    "title": "Chief Synergy Evangelist", "company": "Disruptr.ai", "location": "Remote (office 5 days a week)",
    "salary": "Competitive (with minimum wage)", "applicants": 4012,
    "requirements": ["10 years of experience in AI tools released last week", "Must love family (we are a family)",
                     "Comfortable with ambiguity, especially about pay"],
    "perks": "Unlimited PTO (never approved), free pizza on Fridays (one slice)",
    "outcome": "rejection",
    "letter": "Thank you for sharing your journey with us! After careful consideration of 0 seconds, we have decided to "
              "move forward with candidates who already work here. We will keep your resume on file forever. - Chad, Talent Ninja",
}]


@app.post("/api/jobs")
def jobs():
    _, text = text_from_request(500)
    if not text:
        return jsonify(error="Tell us who you are first."), 400
    try:
        out = json.loads(llm(
            [{"role": "system", "content": JOBS_PROMPT}, {"role": "user", "content": text}],
            temperature=0.9,
            schema=JOBS_SCHEMA,
            fast=True,
        ))
        listings = out["jobs"][:4]
        for j in listings:
            j["requirements"] = j["requirements"][:4]
            j["applicants"] = max(0, int(j["applicants"]))
        if not listings:
            raise ValueError("no jobs")
        fallback = False
    except Exception:
        app.logger.exception("Groq jobs failed, sending fallback")
        listings, fallback = FALLBACK_JOBS, True
    count("jobs")
    return jsonify(jobs=listings, fallback=fallback)


# Share links carry the data itself (zlib + base64url in ?d=), so they still work after Render
# restarts and wipes the in-memory GALLERY/PROFILES.
def pack(obj):
    raw = zlib.compress(json.dumps(obj, separators=(",", ":")).encode(), 9)
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def unpack(token):
    try:
        if not token or len(token) > 12000:
            return None
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        d = zlib.decompressobj()
        data = json.loads(d.decompress(raw, 60000))
        return data if isinstance(data, dict) else None
    except (ValueError, zlib.error, TypeError):
        return None


def s_(v, limit):
    return str(v if v is not None else "")[:limit]


def clean_post(d):
    score = d.get("score") if isinstance(d.get("score"), dict) else {}
    out = {
        "post": s_(d.get("post"), 4000), "headline": s_(d.get("headline"), 300),
        "name": s_(d.get("name"), 60), "text": s_(d.get("text"), 500), "tone": s_(d.get("tone"), 60),
        "comments": [{k: s_(c.get(k), 600) for k in ("name", "title", "text")}
                     for c in (d.get("comments") if isinstance(d.get("comments"), list) else [])[:3] if isinstance(c, dict)],
        "score": {k: clamp_score(score.get(k)) for k in SCORE_KEYS},
    }
    try:
        out["level"] = max(1, min(10, int(d.get("level", 5))))
    except (TypeError, ValueError):
        out["level"] = 5
    out["badge"] = s_(d.get("badge"), 60) or badge(out["score"]["overall"])
    return out


def clean_profile(d):
    def items(key, fields, n):
        lst = d.get(key) if isinstance(d.get(key), list) else []
        return [{f: (x.get(f) if f in ("endorsements",) else s_(x.get(f), 600)) for f in fields}
                for x in lst[:n] if isinstance(x, dict)]
    out = {k: s_(d.get(k), 1200) for k in ("name", "headline", "location", "about", "open_to")}
    try:
        out["followers"] = max(0, int(d.get("followers", 0)))
    except (TypeError, ValueError):
        out["followers"] = 0
    out["experience"] = [{**x, "bullets": [s_(b, 400) for b in (src.get("bullets") if isinstance(src.get("bullets"), list) else [])[:4]]}
                         for x, src in zip(items("experience", ("title", "company", "dates", "location"), 4),
                                           [e for e in (d.get("experience") or [])[:4] if isinstance(e, dict)])]
    out["education"] = items("education", ("school", "degree", "dates"), 2)
    out["skills"] = [{**x, "endorsements": max(0, int(x["endorsements"])) if isinstance(x["endorsements"], int) else 0}
                     for x in items("skills", ("name", "endorsements"), 8)]
    out["recommendations"] = items("recommendations", ("name", "title", "relation", "text"), 3)
    return out


def load_post(post_id):
    with LOCK:
        post = GALLERY.get(post_id)
        if post:
            return dict(post)
    data = unpack(request.args.get("d"))
    return {**clean_post(data), "id": post_id, "votes": 0, "expired": True} if data else None


def load_profile(profile_id):
    with LOCK:
        prof = PROFILES.get(profile_id)
        if prof:
            return dict(prof)
    data = unpack(request.args.get("d"))
    return {**clean_profile(data), "id": profile_id, "fallback": False} if data else None


def with_d(url):
    d = request.args.get("d")
    return f"{url}?d={d}" if d else url


@app.get("/api/post/<int:post_id>")
def get_post(post_id):
    post = load_post(post_id)
    if not post:
        return jsonify(error="That post is gone. Posts reset when the server restarts."), 404
    return jsonify(post)


PUNCT = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u00a0": " ", "\u202f": " ", "\u2009": " ",
                       "\u2014": " - ", "\u2013": "-", "\u2022": "-", "\u2192": "->", "\u2713": ""})  # no glyph in the image font


def plain_punct(text):
    # The model likes non-breaking hyphens/spaces; the image font draws them as boxes.
    return text.translate(PUNCT)


def no_emoji(text):
    # The default font has no emoji glyphs; drop them instead of drawing boxes. Keycaps "1️⃣" become "1.".
    def drawable(o):
        return o < 0x2000 or 0x2010 <= o <= 0x206F or 0x20A0 <= o <= 0x20CF or 0x2E80 <= o < 0xFE00 or 0xFE10 <= o < 0x1F000
    text = plain_punct(text).replace("\ufe0f\u20e3", ".").replace("\u20e3", ".")
    return "".join(ch for ch in text if drawable(ord(ch))).strip()


def card_png(name, headline, body, tag):
    font = ImageFont.load_default
    img = Image.new("RGB", (1200, 630), "#f4f2ee")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, 1160, 590), radius=16, fill="white", outline="#dcdad6", width=2)
    d.ellipse((80, 80, 170, 170), fill="#0a66c2")
    initials = "".join(w[0] for w in no_emoji(name).split()[:2]).upper() or "LV"
    d.text((125, 125), initials, font=font(size=38), fill="white", anchor="mm")
    d.text((195, 88), textwrap.shorten(no_emoji(name), 45), font=font(size=34), fill="#191919")
    d.text((195, 134), textwrap.shorten(no_emoji(headline), 60), font=font(size=24), fill="#666666")
    lines = []
    for para in no_emoji(body).splitlines():
        lines += textwrap.wrap(para, 58) if para.strip() else []
    y = 205
    for line in lines[:8]:
        d.text((80, y), line, font=font(size=30), fill="#191919")
        y += 40
    if len(lines) > 8:
        d.text((80, y), "...see more", font=font(size=28), fill="#666666")
    if tag:
        d.rounded_rectangle((80, 520, 120 + font(size=26).getlength(tag), 566), radius=23, fill="#0a66c2")
        d.text((100, 543), tag, font=font(size=26), fill="white", anchor="lm")
    with Image.open(os.path.join(app.static_folder, "icons", "wordmark.png")) as logo:
        logo.thumbnail((180, 40), Image.Resampling.LANCZOS)
        img.paste(logo, (1120 - logo.width, 543 - logo.height // 2), logo)
    d.text((1120, 573), "PARODY", font=font(size=12), fill="#666666", anchor="rm")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", max_age=300)


@app.get("/og/<int:post_id>.png")
def og_image(post_id):
    post = load_post(post_id)
    if not post:
        return card_png("A LarpedIn Visionary", "Visionary | Professional Larper", "This post went back to being a normal day.", "")
    return card_png(post.get("name") or "A LarpedIn Visionary", post["headline"], post["post"],
                    f"{post['badge']}  |  Cringe {post['score']['overall']}/100")


@app.get("/og/u/<int:profile_id>.png")
def og_profile_image(profile_id):
    prof = load_profile(profile_id)
    if not prof:
        return card_png("A LarpedIn Visionary", "Visionary | Professional Larper", "This profile went back to being a normal person.", "")
    jobs = "\n".join(f"{x['title']} at {x['company']}" for x in prof["experience"][:4])
    return card_png(prof["name"], prof["headline"], f"{prof['about']}\n\n{jobs}", f"{prof['followers']:,} followers")


def page_with_meta(filename, title, desc, image):
    # Fill link-preview meta tags server-side so iMessage/Slack/Discord previews show the content.
    with open(os.path.join(app.static_folder, filename), encoding="utf-8") as f:
        page = f.read()
    return (page.replace("{{og_title}}", html.escape(title))
            .replace("{{og_description}}", html.escape(desc))
            .replace("{{og_image}}", html.escape(image)))


@app.get("/p/<int:post_id>")
def permalink(post_id):
    post = load_post(post_id)
    title = f"{post['headline']} on LarpedIn" if post else "LarpedIn"
    desc = post["post"][:200] if post else "Turn your ordinary day into a LinkedIn masterpiece."
    return page_with_meta("post.html", title, desc, with_d(f"{request.host_url}og/{post_id}.png"))


@app.get("/profile.html")
def profile_page():
    return page_with_meta("profile.html", "Larp your whole profile | LarpedIn",
                          "Tell us your real life. We will make recruiters weep.", f"{request.host_url}og/u/0.png")


@app.get("/u/<int:profile_id>")
def profile_link(profile_id):
    prof = load_profile(profile_id)
    title = f"{prof['name']} | {prof['headline']}" if prof else "LarpedIn profile"
    desc = prof["about"][:200] if prof else "Tell us your real life. We will make recruiters weep."
    return page_with_meta("profile.html", title, desc, with_d(f"{request.host_url}og/u/{profile_id}.png"))


@app.get("/api/profile/<int:profile_id>")
def get_profile(profile_id):
    prof = load_profile(profile_id)
    if not prof:
        return jsonify(error="That profile is gone. Profiles reset when the server restarts."), 404
    return jsonify(prof)


# ---- Real LinkedIn posting (Sign In with LinkedIn + Share on LinkedIn) ----
# Off unless LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET are set in Render; the site then keeps the share box.
LI_AUTH = "https://www.linkedin.com/oauth/v2/authorization"
LI_TOKEN = "https://www.linkedin.com/oauth/v2/accessToken"
LI_USERINFO = "https://api.linkedin.com/v2/userinfo"
LI_POSTS = "https://api.linkedin.com/v2/ugcPosts"
LI_SESSIONS = {}  # ponytail: in-memory sessions, a restart signs everyone out; fine without a database


def li_enabled():
    return bool(os.environ.get("LINKEDIN_CLIENT_ID") and os.environ.get("LINKEDIN_CLIENT_SECRET"))


def base_url():
    # Render terminates TLS at its proxy, so force https everywhere except local dev.
    url = request.host_url.rstrip("/")
    local = request.host.split(":")[0] in ("localhost", "127.0.0.1")
    return url if local else url.replace("http://", "https://", 1)


def li_redirect_uri():
    return base_url() + "/auth/linkedin/callback"


def li_session():
    sess = LI_SESSIONS.get(request.cookies.get("li_sid", ""))
    return sess if sess and sess["exp"] > time.time() else None


def safe_next(path):
    # Printable ASCII only: Werkzeug drops tabs, so "/\t/evil.com" would become "//evil.com" (frontend review).
    ok = (isinstance(path, str) and path.startswith("/") and not path.startswith("//")
          and "\\" not in path and all(33 <= ord(ch) <= 126 for ch in path))
    return path if ok else "/"


@app.get("/auth/linkedin/start")
def li_start():
    if not li_enabled():
        return redirect("/")
    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code", "client_id": os.environ["LINKEDIN_CLIENT_ID"], "redirect_uri": li_redirect_uri(),
        "state": state, "scope": "openid profile w_member_social",
    }
    resp = redirect(LI_AUTH + "?" + requests.compat.urlencode(params))
    resp.set_cookie("li_state", state + "|" + safe_next(request.args.get("next")), max_age=600,
                    httponly=True, secure=base_url().startswith("https"), samesite="Lax")
    return resp


@app.get("/auth/linkedin/callback")
def li_callback():
    state, _, nxt = request.cookies.get("li_state", "").partition("|")
    nxt = safe_next(nxt)
    sep = "&" if "?" in nxt else "?"
    if not li_enabled() or not state or request.args.get("state") != state or not request.args.get("code"):
        return redirect(nxt + sep + "linkedin=failed")
    try:
        tok = requests.post(LI_TOKEN, data={
            "grant_type": "authorization_code", "code": request.args["code"], "redirect_uri": li_redirect_uri(),
            "client_id": os.environ["LINKEDIN_CLIENT_ID"], "client_secret": os.environ["LINKEDIN_CLIENT_SECRET"],
        }, timeout=15)
        tok.raise_for_status()
        token = tok.json()["access_token"]
        me = requests.get(LI_USERINFO, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        me.raise_for_status()
        me = me.json()
    except (requests.RequestException, KeyError, ValueError) as e:
        app.logger.warning("LinkedIn sign-in failed: %s", e)
        return redirect(nxt + sep + "linkedin=failed")
    sid = secrets.token_urlsafe(32)
    with LOCK:
        for old in [k for k, v in LI_SESSIONS.items() if v["exp"] < time.time()]:
            del LI_SESSIONS[old]
        LI_SESSIONS[sid] = {"token": token, "sub": me["sub"], "name": me.get("name", ""),
                            "exp": time.time() + min(int(tok.json().get("expires_in", 3600)), 86400)}  # privacy page: 24 h max
    resp = redirect(nxt + sep + "linkedin=ok")
    resp.set_cookie("li_sid", sid, max_age=86400, httponly=True,
                    secure=base_url().startswith("https"), samesite="Lax")
    resp.delete_cookie("li_state")
    return resp


@app.get("/api/linkedin/me")
def li_me():
    sess = li_session()
    return jsonify(enabled=li_enabled(), signed_in=bool(sess), name=sess["name"] if sess else "")


@app.post("/api/linkedin/post")
def li_post():
    # Same-origin JSON only (SameSite=Lax cookie + Origin check), so other sites cannot post as the user.
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") not in (base_url(), request.host_url.rstrip("/")):
        return jsonify(error="Cross-site request blocked."), 403
    sess = li_session()
    if not sess:
        return jsonify(error="Sign in with LinkedIn first.", signed_in=False), 401
    _, text = text_from_request(2900)
    if not text:
        return jsonify(error="Nothing to post."), 400
    body = {
        "author": f"urn:li:person:{sess['sub']}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    try:
        r = requests.post(LI_POSTS, json=body, timeout=20, headers={
            "Authorization": f"Bearer {sess['token']}", "X-Restli-Protocol-Version": "2.0.0"})
        r.raise_for_status()
    except requests.RequestException as e:
        app.logger.warning("LinkedIn post failed: %s %s", e, getattr(getattr(e, "response", None), "text", "")[:300])
        return jsonify(error="LinkedIn did not accept the post. Try the share box instead."), 502
    post_id = r.headers.get("X-RestLi-Id", "")
    return jsonify(ok=True, url=f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else "https://www.linkedin.com/feed/")


@app.post("/api/linkedin/logout")
def li_logout():
    with LOCK:
        LI_SESSIONS.pop(request.cookies.get("li_sid", ""), None)
    resp = jsonify(ok=True)
    resp.delete_cookie("li_sid")
    return resp


load_seeds()

if __name__ == "__main__":
    app.run(debug=True)
