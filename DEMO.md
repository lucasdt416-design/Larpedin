# Demo script

## Before the demo (10 minutes before)

1. Open https://larpedin-p1fd.onrender.com on the demo laptop. The free server sleeps after about 15 minutes with no traffic, and the first load can take about 50 seconds.
2. Generate one post. Then open its share link (`/p/<id>`) in a second tab, so that the TEDx step is ready.
3. Make sure that the laptop sound goes to the room speakers. TEDx mode and the battle judge talk.
4. Open `/gallery.html?present` in a third tab. That is presenter mode: a giant QR code, live post counts, and a banner each time someone in the room posts. Click "Presenter mode" once to go fullscreen, and press Esc to leave.
5. If you show the Chrome extension, load it first (see `extension/README.md`) and keep a tab open with a cringe LinkedIn post to select.
6. Close other tabs and turn on Do Not Disturb.

If the wifi fails, use the screenshots in a backup folder. If Groq fails, the app still returns canned posts, so the demo does not show an error.

## Script (3 minutes)

0:00 to 0:20, the hook.
"Everyone on LinkedIn is larping. Someone eats a sandwich and posts what it taught them about B2B sales. The theme today is helping people larp, so we built LarpedIn. You tell it the most boring thing you did, and it makes you a thought leader."

0:20 to 1:00, the core loop.
Ask a judge what they did this morning. Type it, pick "Hustle bro", and drag the cringe slider to 8. Click Generate post. Point at the absurd headline, the reaction count, the fake comments and the cringe report. Click "📈 Escalate" once: the slider jumps up a level and the post gets even worse in place. If there is time, click "Try 4 vibes".

1:00 to 1:20, delarp.
Switch to "Delarp a post". Paste "After 4 incredible years, today was my last day. Taking time to reflect and recharge." Show the honest translation.

1:20 to 2:00, Larp Battle.
Open Battle. Put two judges' names in the corners and ask each one what they did today. Click FIGHT. Let the scores count up, the winner get the crown, and the judge read the verdict out loud.

2:00 to 2:30, TEDx.
Open the share link tab. "Every thought leader needs a TED talk." Click "Present at TEDx" and let it run for about 15 seconds. Press Esc.

2:30 to 2:50, the rest.
Switch to the Hall of Larp presenter tab and invite the room to scan the QR code and post. Each new post pops up with a banner, and "See it in the Hall of Larp" on their phone jumps to it. Mention, in one sentence each: Larp your whole profile, LarpedIn Jobs with Easy Apply rejection letters, and the Delarp Chrome extension that works on any website.

2:50 to 3:00, the close.
"It is one Flask file and plain JavaScript, on free Groq and free Render, so it costs $0 to run. If a model fails, it moves to the next of three. LarpedIn: fake it till you make it, professionally."

## Answers to likely judge questions

- **How much does it cost?** $0. Groq free plan and Render free plan.
- **What happens when the AI fails?** Each request tries three models. If all three fail, the user gets a canned post, not an error.
- **Can it handle a whole room?** We sent 12 requests at the same time and all 12 returned real posts in 3 to 5 seconds.
- **How does the AI return a whole card?** One call with a strict JSON schema returns the post, headline, comments and scores together.
- **Where is the data stored?** In memory. A restart clears it. No accounts and no database.
- **Is it real LinkedIn?** No. It is a parody with no LinkedIn logo, and every page says so. It never posts for you. "Copy + open LinkedIn" only fills the share box, and you decide whether to post.
