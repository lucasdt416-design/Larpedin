import os

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b shut down 2026-08-16

TONES = {
    "thought leader": "a visionary thought leader who turns everything into a business lesson",
    "humble brag": "someone humbly bragging, pretending to be modest while flexing hard",
    "hustle bro": "a 5am-grindset hustle bro who relates everything to closing deals",
    "agree?": "an engagement-bait poster who ends with 'Agree?' and asks people to comment",
}

SYSTEM = (
    "You write parody LinkedIn posts. The user tells you something small and ordinary they did. "
    "Rewrite it as a dramatically inflated LinkedIn post in the voice of {voice}. "
    "Use short one-line paragraphs, a fake life lesson, a numbered list of 3 takeaways, "
    "a few emojis, and 3-5 hashtags at the end. Keep it under 200 words. "
    "Output only the post text, as plain text with no markdown or asterisks."
)


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()[:500]
    tone = data.get("tone", "thought leader")
    if not text:
        return jsonify(error="Tell us what you did first."), 400
    voice = TONES.get(tone, TONES["thought leader"])

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
            json={
                "model": MODEL,
                "temperature": 0.9,
                "reasoning_effort": "low",
                "messages": [
                    {"role": "system", "content": SYSTEM.format(voice=voice)},
                    {"role": "user", "content": text},
                ],
            },
            timeout=30,
        )
        if not r.ok:
            return jsonify(error=f"Groq error {r.status_code}: {r.text[:300]}"), 502
        post = r.json()["choices"][0]["message"]["content"].strip()
    except KeyError:
        return jsonify(error="Server is missing GROQ_API_KEY."), 500
    except requests.RequestException as e:
        return jsonify(error=f"Groq request failed: {e}"), 502

    return jsonify(post=post)


if __name__ == "__main__":
    app.run(debug=True)
