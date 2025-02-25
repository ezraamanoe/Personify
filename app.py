import eventlet
eventlet.monkey_patch()  # This must be the first import


import os
import requests
from flask import Flask, redirect, request, jsonify, send_from_directory, session, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import time
import random

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

# Handle Spotify Callback and Fetch Top Tracks
@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code received from Spotify"}), 400

    token_url = "https://accounts.spotify.com/api/token" #Spotify auth 
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=token_data)

    if response.status_code == 200:
        access_token = response.json()['access_token']

        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=10" #Fetch top tracks
        headers = {"Authorization": f"Bearer {access_token}"}
        top_tracks_response = requests.get(top_tracks_url, headers=headers)

        if top_tracks_response.status_code == 200:
            top_tracks = top_tracks_response.json()['items']
            tracks = [
                {"name": track['name'], "artist": track['artists'][0]['name']}
                for track in top_tracks
            ]

            # Store tracks in session instead of calling OpenAI now
            session['tracks'] = tracks  
            session.modified = True  # Force session save

            # Redirect to results immediately
            return redirect("https://personify-ai.onrender.com/results")

    return jsonify({"error": "Failed to retrieve access token or top tracks"}), 500


def generate_track_critique(tracks, max_retries=3, retry_delay=2):
    print("asking chatgpt")
    # Initialize OpenAI (or DeepSeek) client with the correct API key and endpoint
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1", timeout=600)

    # Create a message to send to the model, you could use track names or further track details
    track_names = [f"{track['name']} - {track['artist']}" for track in tracks]
    user_message = f"Guess my MBTI and critique my top tracks from Spotify, be very mean, make fun of me. Here are the songs: {', '.join(track_names)}. don't roast the tracks one by one. use ** for bold and * for italic. limit your response to 200 words and list and enumerate the first 10 tracks (song name and artist) as '**Your top 10 tracks:**' after your description. in bold,  write a short but very niche degrading sentence about my music taste as the last sentence, on a seperate line similar to this: 'Your music taste is music-to-stalk-boys-to-jazz-snob-nobody-puts-baby-in-a-corner bad' but dont copy it. don't mention pinterest and don't assume gender. do not use any other symbol characters except for - and . in the last sentence."

    # Retry loop
    for attempt in range(max_retries):
        # Call OpenAI (or DeepSeek) to generate a critique message
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat:free",  # Or any other model you're using
            messages=[
                {"role": "system", "content": "You are a very sarcastic gen-z niche music critic who thinks everyone is beneath them and that has a deep obsession with myers-briggs."},
                {"role": "user", "content": user_message},
            ]
        )

        # Check if response has valid critique content
        if response.choices and response.choices[0].message.content.strip():
            print(response.choices[0].message.content)
            return response.choices[0].message.content
        else:
            # If no valid critique, print a warning and wait before retrying
            print(f"Retry {attempt + 1} failed. No valid critique returned. Waiting before retrying...")
            time.sleep(retry_delay + random.uniform(0, 2))  # Add random delay to avoid hitting rate limits

    # After max retries, return a fallback message
    print("All retries failed. Returning fallback message.")
    return "Your music taste broke the AI. Please reload the page or go back to home."

@app.route('/get-critique')
def get_critique():
    tracks = session.get('tracks')
    if not tracks:
        return jsonify({"critique": "No tracks available."}), 400  # Return error if no tracks

    # Call AI to generate critique
    try:
        critique = generate_track_critique(tracks)
        session['critique'] = critique
        session.modified = True  # Ensure session is updated
        print(f"Stored critique in session: {critique}")
        return jsonify({"critique": critique}), 200
    except Exception as e:
        return jsonify({"error": f"Error generating critique: {str(e)}"}), 500

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
    font_path = os.path.join(os.getcwd(), 'build', 'fonts', 'PPNeueMontreal', 'PPNeueMontrealMono-Medium.otf')
    font = ImageFont.truetype(font_path, 70)
    fontSub = ImageFont.truetype(font_path, 40)
    
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
    
    temp_image_path = os.path.join("/tmp", "critique.png")
    img.save(temp_image_path, "PNG")
    return send_file(temp_image_path, as_attachment=True, download_name="critique.png")

# Serve the React app
@app.route('/')
@app.route('/results')
def index():
    return send_from_directory('build', 'index.html')

if __name__ == '__main__':
    app.run()