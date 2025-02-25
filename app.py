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
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CORS(app, 
     supports_credentials=True, 
     origins=["https://personify-ai.onrender.com"], 
     methods=["GET", "POST"]
)

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

# Spotify Authentication URL
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

def generate_track_critique(tracks):
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            timeout=30
        )

        track_names = [f"{track['name']} - {track['artist']}" for track in tracks]
        if not track_names:
            return "No tracks to critique. Your music taste is nonexistent."

        user_message = f"Guess my MBTI and critique my top tracks from Spotify, be very mean... [truncated for brevity]"

        response = client.chat.completions.create(
            model="deepseek/deepseek-chat:free",
            messages=[
                {"role": "system", "content": "You are a sarcastic..."},
                {"role": "user", "content": user_message},
            ]
        )
        critique = response.choices[0].message.content.strip()
        if not critique:
            raise ValueError("Empty critique generated")
        
        return critique
    except Exception as e:
        return "Failed to generate critique. Your music taste broke the AI."

@app.route('/callback')
def callback():
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Authorization code missing"}), 400

        # Token exchange
        token_response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            }
        )
        token_response.raise_for_status()  # Raises HTTPError for bad responses

        access_token = token_response.json()['access_token']

        # Fetch top tracks
        top_tracks_response = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        top_tracks_response.raise_for_status()

        top_tracks = top_tracks_response.json().get('items', [])
        if not top_tracks:
            raise ValueError("No top tracks found")

        tracks = [
            {"name": track['name'], "artist": track['artists'][0]['name']}
            for track in top_tracks
        ]

        critique = generate_track_critique(tracks)
        
        # Ensure session is properly updated
        session.update({
            "tracks": tracks,
            "critique": critique,
            "_fresh": True,
            "_permanent": True
        })
        session.modified = True  # Force session save

        return redirect("https://personify-ai.onrender.com/results")

    except requests.HTTPError as e:
        return jsonify({"error": "Failed to communicate with Spotify"}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/get-critique')
def get_critique():
    try:
        # Ensure session is loaded
        critique = session.get("critique", "Critique not available")
        return jsonify({"critique": critique})
    except Exception as e:
        return jsonify({"critique": "Error loading critique"})

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
    
    image_path = os.path.join("build", "static", "images", "critique.png")
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    img.save(image_path, "PNG")
    return send_file(image_path, as_attachment=True, download_name="critique.png")

# Serve the React app
@app.route('/')
@app.route('/results')
def index():
    return send_from_directory('build', 'index.html')

if __name__ == '__main__':
    app.run()