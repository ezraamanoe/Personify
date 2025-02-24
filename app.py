import os
import requests
from flask import Flask, redirect, request, jsonify, send_from_directory, session, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='build/static', template_folder='build')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))  # Fixed secret key
CORS(app)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1200  # 20 minute session lifetime
)

# Spotify credentials from .env file
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "https://personify-ai.onrender.com/callback")

@app.route('/login')
def login():
    session.clear()
    scope = "user-read-private user-read-email user-top-read"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code received from Spotify"}), 400

    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        access_token = response.json()['access_token']

        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=10"
        headers = {"Authorization": f"Bearer {access_token}"}
        top_tracks_response = requests.get(top_tracks_url, headers=headers)
        top_tracks_response.raise_for_status()

        tracks = [
            {"name": track['name'], "artist": track['artists'][0]['name']}
            for track in top_tracks_response.json()['items']
        ]

        # Generate critique immediately and store in session
        session['tracks'] = tracks
        session['critique'] = generate_track_critique(tracks)  # Critical fix here
        session.permanent = True  # Honor the session lifetime
        
        return redirect(f"{SPOTIFY_REDIRECT_URI}/results")

    except Exception as e:
        return jsonify({"error": f"Failed to process Spotify data: {str(e)}"}), 500

def generate_track_critique(tracks):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1")
    track_names = [f"{track['name']} - {track['artist']}" for track in tracks]
    user_message = f"Guess my MBTI and critique my top tracks from Spotify, be very mean, make fun of me. Here are the songs: {', '.join(track_names)}. don't roast the tracks one by one. use ** for bold and * for italic. limit your response to 200 words and list and enumerate the first 10 tracks (song name and artist) as '**Your top 10 tracks:**' after your description. in bold,  write a short but very niche degrading sentence about my music taste as the last sentence, on a seperate line similar to this: 'Your music taste is music-to-stalk-boys-to-jazz-snob-nobody-puts-baby-in-a-corner bad' but dont copy it. don't mention pinterest and don't assume gender. do not use any other symbol characters except for - and . in the last sentence."

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat:free",
        messages=[
            {"role": "system", "content": "You are a very sarcastic gen-z niche music critic who thinks everyone is beneath them and that has a deep obsession with myers-briggs."},
            {"role": "user", "content": user_message},
        ]
    )
    return response.choices[0].message.content

@app.route('/get-critique')
def get_critique():
    if 'critique' not in session:
        return jsonify({"error": "No critique available"}), 404
    return jsonify({"critique": session['critique']})

@app.route('/get-image')
def get_image():
    if 'critique' not in session or 'tracks' not in session:
        return jsonify({"error": "Missing session data"}), 400
        
    critique = session['critique']
    tracks = session['tracks']
    
    # Rest of your original image generation code remains unchanged
    formatted_critique = critique.replace("*", "").split("\n")
    end_critique = formatted_critique[-1]
    
    i = 1
    formatted_tracks = []
    for track in tracks:
        if i <= 11:
            formatted_tracks.append(f"{i}. {track['name']} - {track['artist']}")
            i += 1
        else:
            break

    img = Image.new("RGB", (1080, 1920), color="black")
    draw = ImageDraw.Draw(img)
    end_critique = textwrap.fill(str(end_critique), width=40)
    
    font = ImageFont.truetype("PPNeueMontrealMono-Medium.otf", 70)
    fontSub = ImageFont.truetype("PPNeueMontrealMono-Medium.otf", 40)
    
    draw.text((50, 50), text="Personify AI", fill="white", font=font)
    draw.text((50, 200), end_critique, fill="#0070f3", font=fontSub)
    
    lines = end_critique.split("\n")
    _, _, _, line_height = draw.textbbox((0, 0), "a", font=fontSub)
    line_height *= len(lines)
    
    draw.text((50, 350 + int(line_height)), text="Your top tracks:", fill="white", font=font)
    
    x = 550
    z = 0
    _, _, _, line_height = draw.textbbox((0, 0), "a", font=font)
    
    for track in formatted_tracks:
        formatted_track = textwrap.fill(str(track), width=45)
        track_lines = formatted_track.split("\n")
        draw.text((50, x + z + int(line_height)), text=formatted_track, fill="#0070f3", font=fontSub)
        z += line_height * len(track_lines) + 10
    
    image_path = os.path.join("build", "static", "images", "critique.png")
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    img.save(image_path, "PNG")
    return send_file(image_path, as_attachment=True, download_name="critique.png")

@app.route('/')
@app.route('/results')
def index():
    return send_from_directory('build', 'index.html')

if __name__ == '__main__':
    app.run()