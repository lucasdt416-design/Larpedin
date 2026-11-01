# Devpost submission draft: LarpedIn

Copy each section into the matching Devpost field. Fill in the items marked **TODO** before submitting.

## Required links

- **Demo (live site):** https://larpedin-p1fd.onrender.com
- **Repo:** https://github.com/lucasdt416-design/LarpHacks
- **Demo video:** **TODO** (Devpost usually asks for one. A 2-minute screen recording of the DEMO.md script works.)

## Tagline

Do nothing. Post like a visionary. A parody professional network that turns the most ordinary thing you did into a LinkedIn-worthy accomplishment.

## Inspiration

The theme was "a product to help you LARP as someone you are not." Nowhere is the larp stronger than on LinkedIn: someone does laundry and announces it like a promotion. We wanted to build the tool every one of those posts was secretly written with.

## What it does

- **Larp a post:** type something ordinary ("I graduated", "I got a B- on a quiz"), pick one of 9 posting voices and a cringe level from 1 to 10. LarpedIn writes a believable LinkedIn post about that exact event, told as grandly as possible: an achievement hook, the lessons it "taught" you, gratitude, hashtags. It renders as a full feed card with an inflated headline, fake comments, a reaction count and a cringe report.
- **Escalate:** one click rewrites the same post one level grander, in place.
- **Delarp:** paste a real LinkedIn post and get the honest one-line truth. "Thrilled to announce a new chapter" becomes "I got laid off."
- **Present at TEDx:** any post can be performed on a dark stage, read aloud while each word lights up.
- **Hall of Larp:** a live gallery with upvotes, a "Most cringe in the room" leaderboard and a presenter mode with a giant QR code, so the whole room can post from their phones and watch it land on the projector.
- **Also:** Larp Battle (two people's days go head to head, judged by an AI), Larp your whole profile, LarpedIn Jobs, a Delarp Chrome extension, share links with link-preview images, image download, voice input, and an iOS app wrapper.
- **Copy + open LinkedIn:** copies your post and opens LinkedIn's own composer. LarpedIn never connects to your account or posts for you.

## How we built it

- **Backend:** one Flask file (`app.py`) on gunicorn, deployed on Render's free plan. Link-preview images are drawn with Pillow.
- **AI:** Groq (`gpt-oss-120b`, with fallbacks to `gpt-oss-20b` and `qwen3.8-27b`). The code can also route to Kimi K2 on Featherless. Each post is one call with a JSON schema that returns the post, headline, comments and cringe scores together. The model first writes down what really happened and the "spin" it will claim, then writes the post from that spin. That keeps posts about your real event, with no invented people or statistics. If every model fails, users get a canned post instead of an error.
- **Frontend:** plain HTML, CSS and JavaScript with no build step. It uses html2canvas for image export, qrcodejs for the room QR code and the Web Speech API for voice input.
- **Reliability for a live room:** share links carry the post inside the URL, so they survive server restarts. The gallery is seeded with 12 posts on every start, a GitHub Actions job keeps the free server awake, and a word filter keeps slurs off the projector.
- **Team workflow:** we built with AI coding agents working in parallel (Claude Code for frontend and backend, plus a ChatGPT agent for the visual redesign). They coordinated through a shared `PLAN.md` with file ownership, an API contract, and requests and replies between agents.

## Challenges we ran into

- **Getting the AI to actually larp.** Early versions wrote surreal nonsense ("negotiate a merger with a cactus") or invented a different, bigger event (a "company-wide talent program" for a graduation). We rewrote the prompt so the model commits to the real event and a "spin" first, bans cosmic metaphors, and never invents people or statistics. We checked each version against real live outputs.
- **Keeping real actions separate from gags.** Posting to LinkedIn is a real, public action, and everything else is a joke. We made sure no fake button (the card's Like or Repost) can lead to a real post, and settled on copy-and-paste only.
- **A free server in front of a live room.** Sleeping instances, in-memory data and restarts shaped the design: warm-up handling, request timeouts, restart-proof share links, seeded posts, and a presenter mode that sorts by New, so audience posts are visible right away.
- **Three agents in one repo:** we avoided collisions with file ownership and written handoffs in `PLAN.md`.

## Accomplishments that we're proud of

- A room can join in seconds by scanning a QR code, and their posts appear on the projector live.
- The posts read like real LinkedIn posts at first glance, which is where the joke lands.
- It runs on free tiers and degrades gracefully: there's always a post, never an error page.

## What we learned

- With LLMs, structure beats adjectives. Making the model decide "what really happened" and "the spin" before writing fixed more than any amount of "be funny".
- A parody still needs real care where it touches the real world: posting, links and other people's names.

## What's next for LarpedIn

- Real job openings with a larped "why you're perfect for this" pitch, clearly labelled.
- A stronger difference between cringe levels.
- Optional accounts, so your Hall of Larp history survives restarts.

## Built with

python, flask, gunicorn, render, groq, featherless, pillow, javascript, html5, css3, html2canvas, qrcodejs, web-speech-api, chrome-extension, swiftui, github-actions

## Team roles

- **Lucas:** product direction, frontend and design. Built the home page (composer, post card, Escalate, Delarp mode, loading states, voice input, image export, the More menu), the Hall of Larp gallery with presenter mode and leaderboard, and the live demo script. Owned Render deployment.
- **Mohammad:** backend and AI. Built the Flask API and model routing with fallbacks, prompts, share pages with link previews, Larp Battle, TEDx mode, Larp your whole profile, LarpedIn Jobs, the Chrome extension and the iOS app.
- **AI agents:** Claude Code on both sides of the stack, and a ChatGPT agent for the visual redesign, coordinated through `PLAN.md`. **TODO:** check that this matches how you want to credit AI tools under the hackathon's rules.
