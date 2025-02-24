import os
import requests
from flask import Flask, redirect, request, jsonify, send_from_directory, session, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='build/static', template_folder='build')
app.secret_key = os.environ["FLASK_SECRET_KEY"]  # Must be set in Render
CORS(app, 
    supports_credentials=True, 
    origins=["https://personify-ai.onrender.com"], 
    methods=["GET", "POST"]
)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESIZE='Lax',
    PERMANENT_SESSION_LIFETIME=1800
)

# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "https://personify-ai.onrender.com/callback")

@app.route('/login')
def login():
    session.clear()
    scope = "user-read-private user-read-email user-top-read"
    auth_url = f"https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={scope}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code received from Spotify"}), 400

    try:
        # Get access token
        token_response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            timeout=10
        )
        token_response.raise_for_status()

        # Get top tracks
        tracks_response = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=10",
            headers={"Authorization": f"Bearer {token_response.json()['access_token']}"},
            timeout=10
        )
        tracks_response.raise_for_status()

        # Process tracks
        tracks = [{"name": t['name'], "artist": t['artists'][0]['name']} 
                for t in tracks_response.json()['items']]

        # Generate and store immediately
        critique = generate_track_critique(tracks)
        
        session.update({
            "tracks": tracks,
            "critique": critique
        })
        
        return redirect(f"{SPOTIFY_REDIRECT_URI}/results")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_track_critique(tracks):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        timeout=30
    )

    track_names = [f"{t['name']} - {t['artist']}" for t in tracks]
    user_message = f"Guess my MBTI and critique my top tracks from Spotify, be very mean. Tracks: {', '.join(track_names)}. Use **bold** and *italics*. 200 words max. End with unique roast line."

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat:free",
        messages=[
            {"role": "system", "content": "Sarcastic music critic obsessed with MBTI."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

@app.route('/get-critique')
def get_critique():
    if "critique" not in session:
        return jsonify({"error": "No critique available"}), 404
    return jsonify({"critique": session["critique"]})
@app.route('/get-image')
def get_image():
    critique = session.get('critique')
    formatted_critique = critique.replace("*", "").split("\n")
    end_critique = formatted_critique[-1] # Get last element
    tracks = session.get('tracks')
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
    end_critique = textwrap.fill(str(end_critique), width = 40)
    
    # Load font
    font = ImageFont.truetype("PPNeueMontrealMono-Medium.otf", 70)  # Use a font available on your system
    fontSub = ImageFont.truetype("PPNeueMontrealMono-Medium.otf", 40)
    
    # Draw text onto image
    draw.text((50, 50), text="Personify AI", fill="white", font=font)
    draw.text((50, 200), end_critique, fill="#0070f3", font=fontSub)
    
    lines = end_critique.split("\n")
    _, _, _, line_height = draw.textbbox((0, 0), "a", font=fontSub)  # Calculate height of Critique
    
    line_height *= len(lines)
    draw.text((50, 350 + int(line_height)), text="Your top tracks:", fill="white", font=font)
    
    x = 550  # Starting y-position
    z = 0    # Tracks total height offset
    
    # Get height of a single line of text
    _, _, _, line_height = draw.textbbox((0, 0), "a", font=font)  
    
    for track in formatted_tracks:
        formatted_track = textwrap.fill(str(track), width=45)
        track_lines = formatted_track.split("\n")  # Split into multiple lines
    
        draw.text((50, x + z + int(line_height)), text=formatted_track, fill="#0070f3", font=fontSub)  
    
        # Update total height offset
        z += line_height * len(track_lines) + 10

    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

# Serve the React app
@app.route('/')
@app.route('/results')
def index():
    return send_from_directory('build', 'index.html')

if __name__ == '__main__':
    app.run()