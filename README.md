# LarpedIn

You type something ordinary that you did, for example "I touched grass". The app rewrites it as a dramatic LinkedIn post. One button copies the post and opens the LinkedIn share page.

The app uses Flask and the free Groq API (model `llama-3.3-70b-versatile`). It runs on Render.

## Run locally

1. Get a free API key at https://console.groq.com/keys.
2. Install the packages:

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3. Start the app:

```
GROQ_API_KEY=your_key flask --app app run
```

4. Open http://localhost:5000.

Do not commit the key. If you put it in a `.env` file, git ignores that file.

## Deploy on Render

The app is a free Render web service connected to this repo. Each push to `main` redeploys it.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variable: `GROQ_API_KEY`

The free service sleeps after about 15 minutes with no traffic. Open the site a few minutes before a demo.
