# Demo script (2 minutes)

One wow moment: TEDx. Everything else stays short.

## Before the demo (15 minutes before)

1. **Restart the server.** In the Render dashboard, open the `larpedin` service and click Manual Deploy → Restart service. The gallery lives in memory, so this clears test posts and leaves only the 12 seed posts. The leaderboard then shows only posts from the room.
2. **Wake it up.** Open https://larpedin-p1fd.onrender.com on the demo laptop. The free server can take about 50 seconds on the first load.
3. **Tab 1, Post:** the home page, empty text box, cringe slider at 5.
4. **Tab 2, TEDx:** write one post (for example "I made my bed", level 8), click **Share link**, paste it into a new tab, and leave that tab open. Check that the "Present at TEDx" button is on screen.
5. **Tab 3, Hall:** open `/gallery.html?present` and click "Presenter mode" once for fullscreen. Press Esc to leave it. Check that the QR code and URL are fully visible on the projector.
6. **Sound:** send the laptop audio to the room speakers. TEDx talks.
7. Close other tabs and turn on Do Not Disturb.

If the wifi fails, use the screenshots in the backup folder. If the AI fails, the app returns a canned post, so the demo never shows an error.

## Script

**0:00 to 0:15, the hook** (Tab 1, point at the blue masthead "Big news. I did laundry.")
"Everyone on LinkedIn is larping. Someone does laundry and announces it like a promotion. So we built LarpedIn: tell it the most boring thing you did, and it makes you sound like a leader."

**0:15 to 1:00, a judge's real day**
- Ask one judge: "What did you do this morning?" Type their answer.
- Drag the cringe slider to 8. Click **Write my post**.
- While it types itself out, point at three things: the headline, the fake comments and the cringe report.
- Click **Escalate to 9**. "And if that wasn't enough..." The same post gets grander in place.

**1:00 to 1:15, Delarp** (15 seconds)
- Click the **Delarp a post** tab, then the **Layoff post** sample, then **Translate post**.
- Read the one-line truth out loud. "It also works the other way: it's a BS detector."

**1:15 to 1:40, the wow moment: TEDx** (Tab 2)
- "Every thought leader needs a TED talk." Click **Present at TEDx**.
- Let it run for about 15 seconds, then press Esc.

**1:40 to 2:00, the room** (Tab 3)
- "Scan this and post your own. It's live." Point at the QR code. New posts pop up with a banner, and the best ones climb the leaderboard.
- Close: "LarpedIn: fake it till you make it, professionally."

## Rehearse 3 times with a timer

Say it out loud with a phone stopwatch running. Write down where you are at each checkpoint.

| Checkpoint | Target | Run 1 | Run 2 | Run 3 |
|---|---|---|---|---|
| Slider at 8, "Write my post" clicked | 0:30 | | | |
| "Escalate to 9" clicked | 0:50 | | | |
| Delarp truth read out | 1:15 | | | |
| TEDx stopped (Esc) | 1:40 | | | |
| Closing line said | 2:00 | | | |

If you run long, cut in this order:
1. Skip Escalate.
2. Use a sample chip instead of asking a judge.
3. Shorten TEDx to 10 seconds.

Do not cut the QR code: it's the moment the room joins in.

## Answers to likely judge questions

- **What else does it do?** One sentence each:
  - Larp Battle: two people's days go head to head, and an AI judge picks the bigger larp.
  - Larp your whole profile: a full fake LinkedIn profile from your real life.
  - LarpedIn Jobs: absurd listings with Easy Apply rejection letters.
  - A Delarp Chrome extension: right-click any post on any site.
- **How much does it cost?** $0. Free Groq and free Render.
- **What happens when the AI fails?** Each request tries several models. If all fail, the user gets a canned post, not an error.
- **Can it handle a whole room?** We sent 12 requests at the same time and all 12 returned real posts in 3 to 5 seconds.
- **How does the AI return a whole card?** One call with a JSON schema returns the post, headline, comments and scores together. The model first writes down what really happened and the "spin", then writes the post from that spin. That keeps it about your real event, with no invented people or statistics.
- **Where is the data stored?** In memory. A restart clears it. No accounts and no database.
- **Is it real LinkedIn?** No. It's a parody with no LinkedIn logo, and every page says so. It never posts for you, and it never connects to your LinkedIn account. "Copy + open LinkedIn" copies the text and opens LinkedIn's own composer, and you decide whether to post. The Like and Repost buttons on the fake card are part of the gag and never touch real LinkedIn.
