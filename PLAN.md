# PLAN.md

Shared plan for all humans and agents on this repo (Claude Code and Codex). Read this before you change code.

## What the app does

The user types what they did and picks a vibe. The backend asks Groq for a parody LinkedIn post. The page shows the post with a "Copy + open LinkedIn" button. The app does not use the LinkedIn API.

## API contract

Do not change this contract without telling the other person.

`POST /api/generate`

- Request: `{"text": "I touched grass", "tone": "thought leader"}`
- Tones: `thought leader`, `humble brag`, `hustle bro`, `agree?`
- Success, status 200: `{"post": "..."}`
- Failure, status 400, 500 or 502: `{"error": "message to show the user"}`

## Files and owners

Fill in the owner column. Edit only the files that you own. If you must change another person's file, ask first.

| Area | Files | Owner |
|---|---|---|
| Backend, prompt, Render | `app.py`, `requirements.txt` | |
| Frontend logic | `static/index.html`, `static/app.js` | Claude (claude.ai chat) |
| Design (from Claude Design) | `static/style.css` | |
| Docs | `README.md`, `PLAN.md` | anyone |

## Rules

- Never commit API keys or `.env` files.
- Keep it simple. Priority: working demo, then clean code, then extra features.
- Every push to `main` redeploys Render. Run the app locally before you push.

## Ideas after the demo works

- More tones.
- A "cringe level" slider that sets the temperature.
- A fake LinkedIn post card with likes and comments for screenshots.
