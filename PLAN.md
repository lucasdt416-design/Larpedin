# PLAN.md

Shared plan for all humans and agents on this repo (Claude Code, Claude chat and Codex). Read this before you change code.

## What the app does

The user types what they did, picks a tone and a cringe level, and gets a parody LinkedIn-style post with a headline, fake comments and a cringe score. Delarp mode does the reverse: paste a real LinkedIn post and get the honest version. A gallery shows everyone's posts, and people can upvote them. The app does not use the LinkedIn API.

## Files and owners

Edit only the files that you own. If you must change another person's file, ask first.

| Area | Files | Owner |
|---|---|---|
| Backend, prompts, Render | `app.py`, `requirements.txt`, `render.yaml` | Mohammad (Claude Code) |
| Frontend logic | `static/index.html`, `static/app.js`, `static/gallery.html` | Lucas (Claude chat / Codex) |
| Design | `static/style.css` | Lucas |
| Docs | `README.md`, `PLAN.md` | anyone |

## API contract

Do not change this contract without telling the other person. Until an endpoint is live, the frontend mocks it with the example responses below.

### `GET /api/health`

Returns `{"ok": true}`. Call it when the page loads. Render's free plan sleeps, and the first request can take about 50 seconds. Disable the Generate button and show "Warming up the hustle..." until this answers.

### `POST /api/generate`

Request:

```json
{"text": "I touched grass", "tone": "thought leader", "level": 7}
```

- `tone`: one of `thought leader`, `humble brag`, `hustle bro`, `agree?`, `laid off but grateful`, `AI influencer`, `founder who failed 3 startups`, `recruiter`, `Gen Z intern`.
- `level`: cringe level from 1 to 10. It is optional, and the default is 5.

Response, status 200:

```json
{
  "id": 12,
  "post": "I stepped outside and touched grass...",
  "headline": "Visionary | Grass Toucher | Ex-Unemployed",
  "comments": [
    {"name": "Chad Synergy", "title": "VP of Vibes at Disruptr", "text": "Congrats on this journey! 🙌"}
  ],
  "score": {"buzzwords": 87, "emojis": 64, "humblebrag": 92, "overall": 81},
  "badge": "Certified Lunatic",
  "fallback": false
}
```

- `comments` has 0 to 3 items. It can be empty.
- All `score` values are whole numbers from 0 to 100.
- `fallback` is `true` when Groq failed and the server sent a canned post. Show it the same way.
- `id` is the post's id in the gallery.

### `POST /api/delarp`

Request: `{"text": "Thrilled to announce I'm starting a new chapter..."}`
Response: `{"truth": "I got laid off."}`

### `GET /api/gallery`

Returns a list of up to 50 posts, most votes first, then newest:

```json
[{"id": 12, "text": "I touched grass", "tone": "thought leader", "level": 7, "post": "...", "headline": "...", "score": {...}, "badge": "...", "votes": 3}]
```

### `POST /api/gallery/<id>/vote`

Returns `{"votes": 4}`. Unknown id returns 404 `{"error": "..."}`.

### Errors

Status 400 `{"error": "message"}` for empty or missing input. Show `error` to the user. Groq problems do not return errors from `/api/generate`, they return a fallback post.

## Frontend tasks (Lucas)

1. Warm-up ping to `/api/health` on page load.
2. LinkedIn-style post card: avatar, name, `headline`, "3h • 🌐", `post`, a reaction line such as "👏❤️💡 Bill Gates and 4,812 others", and the `comments`. Add a small "parody" label and do not use the LinkedIn logo.
3. "Download as image" button with html2canvas from cdnjs. Test emoji in the image early. If it looks bad, screenshots are the backup.
4. Cringe slider (`<input type="range" min="1" max="10">`) with a label for the level.
5. Tone dropdown with all 9 tones.
6. Delarp mode toggle that uses the same text box and shows `truth`.
7. Cringe score gauges and the `badge`.
8. `gallery.html`: polls `/api/gallery` every 5 seconds, upvote buttons, and a QR code that points to https://larpedin.onrender.com.
9. "Copy + open LinkedIn" copies only `post`.

Show all model text with `textContent`, never `innerHTML`. Gallery posts come from the public.

## Rules

- Never commit API keys or `.env` files.
- Keep it simple. Priority: working demo, then clean code, then extra features.
- Every push to `main` redeploys Render. Run the app locally before you push.
- The gallery lives in memory. A redeploy or a Render sleep clears it. This is fine for the demo.
