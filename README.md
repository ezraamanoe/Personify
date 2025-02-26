# Personify

<html>
  <p>
    A web app that connects to your Spotify account and uses AI to humorously critique your music taste andd guess your MBTI, heavily inspired by <a         href="https://pudding.cool/2021/10/judge-my-music/">pudding.cool</a>. Built with React for the frontend and Flask for the backend, leveraging the DeepSeek API for AI-generated insights.
  </p>
</html>

## Features
<html>
  <dl>
    <dt>Spotify Integration:</dt>
    <dd>- Log in and fetch top 10 tracks</dd>
    <dt>A.I. Integration:</dt>
    <dd>- Uses DeepSeek API via OpenRouter to judge music taste</dd>
    <dt>Custom Image Generation:</dt>
    <dd>- Generates a downloadable image with AI generated message and top tracks</dd>
  </dl>
</html>

## Running the App Locally
<html>
  <dl>
    <dt>Prerequisites:</dt>
    <dd>
      - <a href="https://www.python.org">Python 3.9+</a>
      <br/>
      - <a href="https://docs.npmjs.com/downloading-and-installing-node-js-and-npm">Node.js and npm</a>
      <br/>
      - <a href="https://developer.spotify.com">Spotify Developer Account</a> (for API credentials)
      <br/>
      - <a href="https://openrouter.ai">OpenRouter API key</a> (for AI model)
    </dd>
  </dl>
</html>

Clone the git repository by running:

```
$ git clone 
$ cd Personify
```

Set up the flask backend by creating a virual environment and installing requirements:

```
$ python -m venv venv
$ source venv/bin/activate  # (Windows: venv\Scripts\activate)
$ pip install -r requirements.txt
```
In your Spotify for Developers dashboard, register <a>http://127.0.0.1:5000/callback</a> as your redirect URI. Create a `.env ` file in the root directory and add your API keys and credentials.:

```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI="http://127.0.0.1:5000/callback"
OPENAI_API_KEY=your_openai_api_key
```

Before running app locally, change all occurences of `https://personify-ai.onrender.com` to `http://127.0.0.1:5000` in Results.js, Home.js, and app.py.

For example, `https://personify-ai.onrender.com/login` becomes `http://127.0.0.1:5000/login`.

Install dependencies and create a build for React:

```
$ npm install
$ npm run build
```

Run using flask development server:
```
flask run # (development server)
```

Then open http://127.0.0.1/5000 on your browser.




