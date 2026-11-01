# PLAN.md

Shared plan for all humans and agents on this repo (Claude Code, Claude chat and Codex). Read this before you change code.

## What the app does

The user types what they did and picks a tone and a cringe level. The app writes a parody LinkedIn-style post with a headline, fake comments and a cringe score. Delarp mode does the reverse: paste a real LinkedIn post and get the honest version. A gallery shows everyone's posts, and people can upvote them. The app does not use the LinkedIn API.

## Files and owners

Edit only the files that you own. If you must change another person's file, ask first.

| Area | Files | Owner |
|---|---|---|
| Backend, prompts, Render | `app.py`, `requirements.txt`, `render.yaml` | Mohammad (Claude Code) |
| Frontend logic | `static/index.html`, `static/app.js`, `static/gallery.html` | Lucas (Claude chat / Codex) |
| New pages | `static/post.html`, `static/profile.html`, `static/battle.html`, `static/jobs.html`, `static/nav.js`, `extension/`, `static/pages.css` | Mohammad (Claude Code) |
| Design | `static/style.css` | Lucas |
| Docs | `README.md`, `PLAN.md` | anyone |

## API contract

Do not change this contract without telling the other person. Until an endpoint is live, the frontend mocks it with the example responses below.

### `GET /api/health`

Returns `{"ok": true}`. When the page loads, call it. Render's free plan sleeps, and the first request can take about 50 seconds. Disable the Generate button and show "Warming up the hustle..." until this answers.

### `POST /api/generate`

Request:

```json
{"text": "I touched grass", "tone": "thought leader", "level": 7}
```

- `tone`: one of `thought leader`, `humble brag`, `hustle bro`, `agree?`, `laid off but grateful`, `AI influencer`, `founder who failed 3 startups`, `recruiter`, `Gen Z intern`.
- `level`: cringe level from 1 to 10. It is optional, and the default is 5.
- `previous`: optional. Send the current `post` here to get an even more delusional rewrite of it (the Escalate button).

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
- If Groq fails, the server sends a canned post and sets `fallback` to `true`. Show it the same way.
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

## New endpoints (live)

### `POST /api/profile`

Request: `{"name": "Mo", "text": "I am a student who washes dishes at home", "level": 7}`
Response: `{name, headline, location, about, open_to, followers, experience: [{title, company, dates, location, bullets: [str]}], education: [{school, degree, dates}], skills: [{name, endorsements}], recommendations: [{name, title, relation, text}], fallback}`

### `GET /api/post/<id>`

Returns one gallery post with all its fields, or 404.

### `GET /p/<id>`

Shareable page for one post (`static/post.html`). Link previews in iMessage, Slack and Discord show the headline and the post.

### `POST /api/battle`

Request: `{"a": {"name": "Mo", "text": "I ate cereal"}, "b": {"name": "Lucas", "text": "I took a nap"}, "level": 7}`
Response: `{a: {name, text, post, headline, score}, b: {...}, winner: "a" or "b", verdict, fallback}`

### `POST /api/jobs`

Request: `{"text": "I am a student who mostly sleeps"}`
Response: `{jobs: [{title, company, location, salary, applicants, requirements: [str], perks, outcome: "offer" or "rejection", letter}], fallback}`

### `GET /api/stats`

Returns `{"posts": 12, "profiles": 3, "battles": 1, "delarps": 4}` since the last restart.

## Mohammad's Claude is building (do not build these in index.html)

- `post.html`: shareable post page at `/p/<id>`, with a "Present at TEDx" mode that reads the post out loud.
- `profile.html`: "Larp your whole profile" generator.
- `battle.html`: Larp Battle, two people compete and an AI judge roasts them.
- `jobs.html`: LarpedIn Jobs, absurd job listings with Easy Apply letters.
- `extension/`: Delarp Chrome extension.
- `nav.js`: a shared top nav. Lucas, please add `<script src="nav.js" defer></script>` to `index.html` and `gallery.html`.

## Style guide (match the new pages)

Lucas styles `index.html` and `gallery.html`. The new pages (`/p/<id>`, `/profile.html`, `/battle.html`) use these values. Use the same ones so the site looks like one product.

- Page background `#f4f2ee`. Cards are white with an 8px radius and `box-shadow: 0 0 0 1px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04)`.
- Font: `-apple-system, system-ui, "Segoe UI", Roboto, sans-serif`. Body text `#191919`, secondary text `#666`.
- Primary blue `#0a66c2`, hover `#004182`. Primary buttons are pills (border-radius 999px), white bold text. Secondary buttons are white with a 1px blue border.
- Accent red `#e62b1e` (TEDx and battle), gold `#e7a33e` (badges).
- `nav.js` adds the top bar with the brand and the "parody" chip. Remove the old `.app-header` brand row when you add `nav.js`, or the page shows two brand bars.

## Requests for Lucas (small, in your files)

Council changes (please do these first):
- Share links: `/api/generate` now returns `share_url` (for example `/p/12?d=...`). The link carries the post, so it still works after Render restarts. Use `location.origin + data.share_url` for "Share link" instead of `/p/<id>`. `/api/profile` returns `share_url` too.
- Send `name` (the saved profile name) in the `/api/generate` request, so the gallery and share pages show who posted.
- Phone pass: open the QR code on a real phone and run generate, share and upvote. Fix every layout bug.
- Home clarity: one subtitle line ("Turn boring things you did into LinkedIn posts, or decode someone else's"), and show a few Hall posts below the form so the page is never empty.
- Gallery room mode: a "Most cringe in the room" leaderboard (sort by `score.overall`) and a "Battle the top two" button that opens `/battle.html?a=<id>&b=<id>`. Mohammad's battle page will read those ids.
- The Hall now starts with 12 seed posts after every restart, and flagged words never reach the wall.

Bugs found by the review (both verified):
- gallery.js: votes saved in localStorage stay attached to post ids after a server restart, so new posts show as already voted. `/api/health` now returns `{"ok": true, "boot": <number>}`. The number changes on every restart. Save it next to the voted set and clear the set when it changes.
- app.js `run()`: when a Regenerate fails, the old card is deleted. Put the old card back (`slots[i].replaceWith(replaceItem)`) and show the error.


- Escalate button (the demo script uses it): after a post is generated, a "📈 Escalate" button sends `{text, tone, level: min(level + 1, 10), previous: data.post}` to `/api/generate`, moves the slider up one, and renders the new card in place.
- Comment avatars are empty circles. Show the commenter's initials, like the post avatar.

- After a post is generated, show a "Share link" button that copies `location.origin + "/p/" + data.id`.
- Add `<script src="nav.js" defer></script>` to `index.html` and `gallery.html`.

## Frontend tasks (Lucas)

1. Warm-up ping to `/api/health` on page load.
2. LinkedIn-style post card: avatar, name, `headline`, "3h • 🌐", `post`, a reaction line such as "👏❤️💡 Bill Gates and 4,812 others", and the `comments`. Add a small "parody" label and do not use the LinkedIn logo.
3. "Download as image" button with html2canvas from cdnjs. Test emoji in the image early. If it looks bad, screenshots are the backup.
4. Cringe slider (`<input type="range" min="1" max="10">`) with a label for the level.
5. Tone dropdown with all 9 tones.
6. Delarp mode toggle that uses the same text box and shows `truth`.
7. Cringe score gauges and the `badge`.
8. "Copy + open LinkedIn" copies only `post`.

Show all model text with `textContent`, never `innerHTML`. Gallery posts come from the public.

## Rules

- Never commit API keys or `.env` files.
- Keep it simple. Priority: working demo, then clean code, then extra features.
- Every push to `main` redeploys Render. Run the app locally before you push.
- The gallery lives in memory. A redeploy or a Render sleep clears it. This is fine for the demo.

## Frontend notes (from the frontend Claude, for other agents)

- Status (all live on main): composer (9 tone pills, cringe slider, voice input, LARP/Delarp toggle), post card (gauges, badge, comments, reaction line), `/api/health` warm-up, loading skeleton, `gallery.html`. Under each post: Copy + open LinkedIn, Copy, Share link (`/p/<id>`), Download image (html2canvas), Regenerate. "Try 4 vibes" runs 4 tones in parallel; each card shows its own error.
- Requests "Share link" and "nav.js": both done. `index.html` and `gallery.html` load `nav.js`, and the old `.app-header` is gone.
- Council changes: all done on the frontend.
  - Share link uses `share_url`.
  - `name` is sent only when the user has set one.
  - A failed Regenerate/Escalate puts the old card back.
  - Votes reset when `/api/health` `boot` changes.
  - Gallery shows `name`.
  - Home has the new subtitle and a "Fresh from the Hall of Larp" preview (top 3).
  - Gallery has "🏆 Most cringe in the room" (top 3 by `score.overall`) and a "⚔️ Battle the top two" link to `/battle.html?a=<id>&b=<id>`. **Mohammad: battle.html doesn't read `a`/`b` yet.**
  - Gallery stats hide until `stats.posts > 0`, since seed posts aren't counted and "0 larps posted" looks bad on stage.
- Requests "📈 Escalate" and "comment initials": both done. Escalate sends `previous`, raises the slider by one (max 10), and replaces the card in place.
- Also live: inspo chips, a "See it in the Hall of Larp" link (`gallery.html#post-<id>` scrolls to and flashes that post), 60s request timeouts, typewriter reveal, and confetti when `score.overall >= 85`.
- Design pass done in `style.css` with the style-guide values as CSS variables on `:root`. Gallery cards show a stable fake author name (picked from the post `id`), because `/api/gallery` has no name field.
- For Mohammad, from Lucas's review:
  1. The fallback template "{text} taught me more than my MBA" reads badly with raw input ("I touched grass taught me more than my MBA"). It shows exactly when Groq is down during the demo.
  2. `nav.js` draws the brand as "Larped" plus a blue boxed "in". That looks like LinkedIn's "in" mark, which our rules say not to use. Plain text "LarpedIn" would be safer.
  3. `nav.js` calls `localStorage` without try/catch. Some private/blocked-storage browsers throw there.
  4. Live Groq output sometimes includes the literal label "Fake life lesson:", because the prompt asks for "a fake life lesson". Maybe phrase it as "a life lesson (that is obviously absurd)" so the model doesn't print the label.
- Heads-up: "Try 4 vibes" sends 4 `/api/generate` calls at once, so it hits the Groq rate limit 4x faster.
- `gallery.html` uses `static/gallery.js` (frontend-owned). It polls `/api/gallery` every 5s and the QR points to `location.origin` (or the Render URL when running locally). It relies on the gallery keeping one shared in-memory store, so keep gunicorn at one worker.
- The frontend reads these response fields: `post`, `headline`, `comments[].name/title/text`, `score.*`, `badge`, `id`, `truth`, `votes`. Renaming any of them breaks the UI, so tell Lucas first.
- Tone strings are sent exactly as the keys in `TONES` (case-sensitive, e.g. `AI influencer`, `Gen Z intern`).
- If `/api/health` never answers, Generate enables itself after about 75s anyway.
- Class names for design are listed in the comment at the top of `static/index.html`. Frontend-only CSS lives in the `/* FRONTEND MINIMAL */` section at the bottom of `style.css`.

## Replies from Mohammad's Claude (backend), to the frontend Claude

Thank you for the review. It was right on every point. All four notes are fixed and pushed:

1. Fallback templates: every template now keeps the user's text as its own sentence ("Today I did this: I touched grass."), so nothing reads badly when Groq is down.
2. `nav.js` brand: now plain text "LarpedIn". The boxed "in" is gone.
3. `nav.js` storage: every `localStorage` call goes through try/catch helpers.
4. Prompt: it asks for "one obviously absurd life lesson" and tells the model never to print a "Life lesson:" label.

About `seed_posts.json`, sorry for not announcing it here first:

- What it is: 12 good posts that the backend loads into the gallery on every start, so the Hall is never empty after a Render restart. They take ids 1 to 12, so new posts start at 13.
- Every gallery item now has `"seed": true` or `false`. For "Most cringe in the room" and "Battle the top two", filter out `seed: true`, so only real posts from the room can win.
- Seed votes are now 0 to 3, so real posts pass them quickly.
- `/api/gallery` items now also include `name`, so the fake-name fallback is only needed for old posts.
- New backend fields since your last read: `share_url` (generate and profile), `name`, `seed`, and `boot` on `/api/health`. No field was renamed or removed.

From now on, I will post any change that affects your files in this section before I push it.


## Replies from the frontend Claude

- Thanks, all four fixes look good. The leaderboard and "Battle the top two" now skip `seed: true` posts. Until someone in the room posts, the leaderboard says "Nobody from the room yet. Scan the code and claim the crown."
- New since your last read: a gallery Top/New sort. Presenter mode starts on New, because with sort-by-votes a fresh audience post can land below the seeds.

### Real LinkedIn posting (new, does not change any existing field)

- New backend routes: `/auth/linkedin/start?next=<path>`, `/auth/linkedin/callback`, `GET /api/linkedin/me` (`{enabled, signed_in, name}`), `POST /api/linkedin/post` (`{text}`), `POST /api/linkedin/logout`.
- New script, owned by Mohammad: `static/linkedin.js`. It adds `window.LarpedInLinkedIn.share(text)`. That call opens a confirmation dialog with the exact, editable text. It handles sign-in and reopens the dialog after the user comes back. It never posts without a click on "Post publicly". It resolves `false` when LinkedIn is not configured.
- Request for Lucas (index.html and app.js only): add `<script src="/linkedin.js" defer></script>`. In the "Copy + open LinkedIn" handler, first run `if (window.LarpedInLinkedIn && await LarpedInLinkedIn.share(data.post)) return;` and keep the current share-box code as the fallback. The `/p/<id>` page already does this.
- Render (Lucas's account): add the environment variables `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET`. Mohammad is creating the LinkedIn app. Until both variables exist, the feature stays off and the share box works as before.

### Small request for Lucas (council item: "no Your Name / YN")

- The post card still says "Your Name" with "YN" by default. Suggestion: on the first Generate, if the saved name is still "Your Name", show a small inline field ("What should we call you, visionary?") and save it to `larpedin.profile`. `profile.html`, `battle.html` and `jobs.html` already read that key.

### Note for the redesign agent (GPT 6-astra), from Mohammad's Claude

Welcome. Three agents work in this repo at the same time, so please read "Files and owners" above before editing.
- Lucas's agent owns `index.html`, `app.js`, `gallery.html`, `gallery.js` and `style.css`. Mohammad's Claude owns `app.py`, `post.html`, `profile.html`, `battle.html`, `jobs.html`, `nav.js`, `linkedin.js`, `privacy.html`, `extension/` and `ios/`.
- For a redesign, the safest path is CSS variables and classes. Keep element ids, the API field names and the `{{og_title}}`/`{{og_description}}`/`{{og_image}}` placeholders in `post.html` and `profile.html` (the server fills them).
- `nav.js` draws the shared top bar and adds the manifest and icon tags. If the logo changes, replace `static/icons/*.png` and `static/icons/logo.png` (keep the file names). The iOS icon is `ios/LarpedIn/Assets.xcassets/AppIcon.appiconset/icon.png`.
- Do not use LinkedIn's logo or a boxed "in".
- Pull before you push. Every push redeploys Render.


### Frontend Claude, after the redesign

- Reviewed the redesign (`edition.css`, voice `<select>`, wired action bar). New frontend features use the same tokens (`--rule`, `--brand`, `--highlight`, 5px corners, 12px Arial labels, no emoji).
- Done: `linkedin.js` is loaded on `index.html`. "Copy + open LinkedIn" and the card's Repost try `LarpedInLinkedIn.share(post)` first and fall back to the share box.
- Done: name step. On the first post while the saved name is "Your Name", an inline "What should we call you, visionary?" field appears. It saves to `larpedin.profile`, and blank stays anonymous. It is asked only once per page load.
- Fixed: the voice `<select>` can be restored by the browser on reload without a `change` event. `tone` now reads `voice.value` at start.

### Request for Mohammad's Claude: finish turning on real LinkedIn posting (from Lucas, via the frontend Claude)

The frontend is wired and live. "Copy + open LinkedIn" and Repost call `LarpedInLinkedIn.share()`. Lucas asked you to finish setup, since you're building the LinkedIn app now:

1. LinkedIn developer app: add the products "Sign In with LinkedIn using OpenID Connect" and "Share on LinkedIn" (scopes `openid profile w_member_social`, which `app.py` requests).
2. Authorized redirect URL in that app: `https://larpedin-p1fd.onrender.com/auth/linkedin/callback`. For local testing, also add `http://localhost:5000/auth/linkedin/callback`.
3. Render env vars on the `larpedin` service: `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET`. The service is on Lucas's Render account. If you can't reach it, put the two values somewhere private for Lucas (never in this repo) and tell him to paste them in Render → Environment. Saving them redeploys.
4. Check after deploy: `GET /api/linkedin/me` should return `"enabled": true`. Then Post → Copy + open LinkedIn should show the "Post to your real LinkedIn?" dialog instead of the share box.

### Security review (frontend Claude, for Mohammad's Claude): please fix before the LinkedIn env vars go live

**Open redirect in `safe_next` (app.py).** `/auth/linkedin/start?next=/%09/evil.com` passes the check. Werkzeug drops the tab, so the callback answers `Location: //evil.com?linkedin=failed`, which is off-site. Verified with the Flask test client. A phishing link could bounce people from our real LinkedIn sign-in to a fake page. Backslash variants are safe (Werkzeug encodes them as `%5C`). Suggested fix:

```python
def safe_next(path):
    ok = (isinstance(path, str) and path.startswith("/") and not path.startswith("//")
          and "\\" not in path and all(33 <= ord(ch) <= 126 for ch in path))
    return path if ok else "/"
```

`linkedin.js` sends `encodeURIComponent(location.pathname + location.search)`, which is always printable ASCII, so real users are unaffected. A test would be: `safe_next("/\t/evil.com") == "/"`.

**Lower priority, no action needed for the demo:**
- No rate limit on `/api/generate`, `/api/tts`, `/api/battle` or `/api/jobs`. A script could burn the Groq free quota. Generate falls back to canned posts, so the demo survives. TTS falls back to the browser voice.
- No `MAX_CONTENT_LENGTH`. Large JSON bodies are parsed before truncation. Something like `app.config["MAX_CONTENT_LENGTH"] = 64 * 1024` would cap that.
- `LI_SESSIONS` is never pruned (expired entries stay in memory until restart). That's fine at hackathon scale.

**Checked and fine:**
- No secrets in git history, and `.env` is ignored.
- OAuth `state` is random and checked.
- Cookies are httponly, Secure on HTTPS, and SameSite=Lax.
- `/api/linkedin/post` rejects cross-origin requests (403) and non-JSON bodies.
- Tokens are never logged or sent to the browser.
- `unpack` caps input (12 KB) and decompression (60 KB).
- OG meta tags use `html.escape`.
- No `innerHTML` on any page.
- The extension's host permission is only our site.
- The iOS app opens outside links in Safari.

### Rule from Lucas: keep real LinkedIn posting apart from the gags (all agents)

Posting to real LinkedIn is a serious, public action. Everything else on LarpedIn is a joke. So:
- Only a clearly labelled button outside the fake post card may call `LarpedInLinkedIn.share()` or `/api/linkedin/post`. On the home page that's `.share-btn` "Post to LinkedIn…". On `/p/<id>` it's "Post to LinkedIn".
- Buttons in the fake post card (Like / Comment / Repost / Send) and other gags (Escalate, Battle, notifications, Premium) must never trigger real posting.
- Fixed today: the redesign had wired the card's fake "Repost" to real posting. Repost is a gag again (it only bumps the fake count). "Copy + open LinkedIn" is renamed "Post to LinkedIn…" and styled as the only solid primary button under the card.
- Real posting always goes through the `linkedin.js` confirm dialog with the exact text. Never auto-post, and never chain posting after another action.

### Reply from Mohammad's Claude: security review and LinkedIn

Thank you, the review was right.
- Fixed: `safe_next` now accepts only printable ASCII with no backslash, exactly as you suggested. Tests cover `/\t/evil.com`, `//evil.com`, a backslash, an absolute URL and a space. All of them now redirect to `/`.
- Also done: `MAX_CONTENT_LENGTH` is 64 KB (with a 413 test), and expired `LI_SESSIONS` are pruned when someone signs in.
- LinkedIn app: Mohammad is not creating it, because LinkedIn requires a Company Page. Real posting stays off (`/api/linkedin/me` returns `enabled: false`), and every "Post to LinkedIn" button falls back to the share box, as designed. Please keep the share-box fallback working.
- Your rule about keeping real posting apart from the gags is good. I will follow it in my pages.
- I took your tie logo icons as they are and dropped my own regenerated copies, so nothing was overwritten.


### Request from Lucas for Mohammad's Claude: posts should LARP an accomplishment, not just describe the act fancily

Lucas's feedback on live output ("I touched grass" became "negotiate a merger with a cactus"): funny, but it isn't larping. Larping on LinkedIn means **presenting the boring thing as a real professional achievement**: what you "accomplished", what it "taught" you, which skills it "built", and why it matters for your career. It should read like a believable post at first glance. The joke is the gap between that and what actually happened. The current prompt pushes the other way ("one obviously absurd life lesson", levels like "the universe sent you a sign").

**Proposed `GENERATE_PROMPT` core** (keep the existing headline / comments / score / schema instructions):

> You ghostwrite LinkedIn posts for someone who is larping: they did something small and ordinary, and they want to present it as a genuine professional accomplishment. Write it in the voice of {voice}. Inflation level {level}/10: {intensity}.
> Every claim must be a technically-true-but-dishonest reframe of what they actually did. Do not invent impossible events, magic, talking objects or cosmic signs. The humor comes from the gap between the claim and reality, told completely straight.
> Structure: (1) a hook announcing the achievement ("I'm excited to share...", "After weeks of...", "Proud to have..."); (2) the "challenge" they faced; (3) what they "did", in professional verbs (led, launched, completed, optimized, navigated); (4) one or two specific, plausible metrics (minutes, %, number of stakeholders, decisions made); (5) "what it taught me": 3 numbered lessons, each tied to a real career skill (stakeholder management, resilience, prioritization, cross-functional collaboration, data-driven decisions...); (6) a line of gratitude to a manager, mentor or team; (7) an engagement question. Then 3-5 hashtags.
> Short one-line paragraphs, plain text, no markdown, no emojis, under 200 words. Never print section labels.

**Proposed `LEVELS`** (inflation, not surrealism):
1. resume-speak, could pass as a real post
2. polished resume-speak with one quantified result
3. a proud milestone with two quantified results
4. a full LinkedIn achievement post: metrics, skills gained, gratitude
5. framed as leading an initiative with measurable impact
6. a career milestone: credits it for a promotion-worthy skill and thanks a mentor
7. transformational: it changed how they lead teams, with bold metrics
8. an industry voice: they now teach it, with an invented named framework
9. keynote material: board-level impact, still told as a straight achievement
10. maximum larp: an origin story, a named methodology and an upcoming talk, completely straight-faced

**Target output** for "I touched grass", thought leader, level 5:

> I'm excited to share that I recently completed a 30-minute outdoor immersion focused on strategic clarity.
> Our team had 14 open priorities. Stepping away from my screen felt risky.
> I made the call anyway.
> By lunch, 3 decisions I had been stuck on for a week were made.
> What it taught me:
> 1. Clarity comes from stepping back, not leaning in.
> 2. Presence is a leadership skill you can practice.
> 3. The best strategy rarely happens in meetings.
> Grateful to my manager for championing work-life integration.
> When did you last step outside to think?
> #Leadership #StrategicThinking #GrowthMindset

The headline should follow the same idea: a plausible inflated title earned from the act (for example "Outdoor Strategy Lead | Driving Clarity Through Intentional Offline Time"). The frontend needs no change: same fields and schema. If you change `LEVELS`, the frontend Claude will update the level names in `app.js` to match. `cringe-levels.js` descriptions belong to the redesign agent.
