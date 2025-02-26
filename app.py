import eventlet
eventlet.monkey_patch()  # Eventlet for gunicorn


import os
import requests
from flask import Flask, redirect, request, jsonify, send_from_directory, session, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import textwrap
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
    PERMANENT_SESSION_LIFETIME=1200  # 20 mins 
)

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "https://personify-ai.onrender.com/callback")

# Spotify auth URL
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

# Callback route to handle Spotify auth and fetch top tracks
@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code received from Spotify"}), 400

    token_url = "https://accounts.spotify.com/api/token" #S potify auth 
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

        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=10" # Fetch top tracks
        headers = {"Authorization": f"Bearer {access_token}"}
        top_tracks_response = requests.get(top_tracks_url, headers=headers)

        if top_tracks_response.status_code == 200:
            top_tracks = top_tracks_response.json()['items']
            tracks = [
                {"name": track['name'], "artist": track['artists'][0]['name']}
                for track in top_tracks
            ]

            # Store tracks in session
            session['tracks'] = tracks  
            session.modified = True  # Force session save

            # Redirect to results page
            return redirect("https://personify-ai.onrender.com/results")

    return jsonify({"error": "Failed to retrieve access token or top tracks"}), 500


# Function to generate track critique using DeepSeek model
def generate_track_critique(tracks, max_retries=3, retry_delay=2):
    print("asking chatgpt")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1", timeout=600)

    # AI prompt
    track_names = [f"{track['name']} - {track['artist']}" for track in tracks]
    user_message = f"Guess my MBTI and critique my top tracks from Spotify, be very mean, make fun of me. Here are the songs: {', '.join(track_names)}. don't roast the tracks one by one. use ** for bold and * for italic. limit your response to 200 words and list and enumerate the first 10 tracks (song name and artist) as '**Your top 10 tracks:**' after your description. in bold,  write a short but very niche degrading sentence about my music taste as the last sentence, on a seperate line similar to this: 'Your music taste is music-to-stalk-boys-to-jazz-snob-nobody-puts-baby-in-a-corner bad' but dont copy it. don't mention pinterest and don't assume gender. do not use any other symbol characters except for - and . in the last sentence."

    # Retry loop
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat:free",
                messages=[
                    {"role": "system", "content": "You are a very sarcastic Gen-Z niche music critic who thinks everyone is beneath them and has a deep obsession with Myers-Briggs."},
                    {"role": "user", "content": user_message},
                ]
            )

            # Debug: Print full API response
            print("Full API response:", response)

            # Extract critique from response
            if response and response.choices and response.choices[0].message and response.choices[0].message.content:
                critique = response.choices[0].message.content.strip()
            else:
                critique = ""  # Set empty string if response is invalid

            # Check if critique is long enough (sometimes it generates very short responses)
            if len(critique.split()) >= 100:
                print("Received critique:", critique)
                return critique
            else:
                print(f"Retry {attempt} failed. Critique too short ({len(critique.split())} words). Retrying...")

        except Exception as e:
            print(f"Error calling AI: {e}")

        time.sleep(retry_delay + random.uniform(1, 2)) 

    print("All retries failed. Returning fallback message.")
    return "Your music taste broke the AI. Please reload the page or go back to home."

# Route to get critique
@app.route('/get-critique')
def get_critique():
    tracks = session.get('tracks')
    if not tracks:
        return jsonify({"critique": "No tracks available."}), 400  # Return error if no tracks

    # Call to generate critique
    try:
        critique = generate_track_critique(tracks)
        session['critique'] = critique
        session.modified = True  # Save session
        print(f"Stored critique in session: {critique}")
        return jsonify({"critique": critique}), 200
    except Exception as e:
        return jsonify({"error": f"Error generating critique: {str(e)}"}), 500

@app.route('/get-image')
def get_image():
    critique = session.get('critique')
    formatted_critique = critique.replace("*", "").split("\n") # Remove * and split by new line
    end_critique = formatted_critique[-1] # Get last element
    tracks = session.get('tracks')
    
    # Append tracks to list
    i = 1
    formatted_tracks = []
    for track in tracks:
        if i <= 11:
            formatted_tracks.append(f"{i}. {track['name']} - {track['artist']}")
            i += 1
        else:
            break

    # Create image
    j = 100 # Height offset
    img = Image.new("RGB", (1080, 1920), color="black")
    draw = ImageDraw.Draw(img)
    end_critique = textwrap.fill(str(end_critique), width = 40)
    
    # Load font
    font_path = os.path.join(os.getcwd(), 'build', 'fonts', 'PPNeueMontreal', 'PPNeueMontrealMono-Medium.otf')
    font = ImageFont.truetype(font_path, 70)
    fontSub = ImageFont.truetype(font_path, 40)
    
    # Draw text onto image
    draw.text((50, 50 + j), text="Personify AI", fill="white", font=font)
    draw.text((50, 200 + j), end_critique, fill="#0070f3", font=fontSub)
    
    lines = end_critique.split("\n")
    _, _, _, line_height = draw.textbbox((0, 0), "a", font=fontSub)  # Calculate height of a single line of text
    
    line_height *= len(lines) # Total height of all lines
    draw.text((50, 350 + int(line_height) + j), text="Your top tracks:", fill="white", font=font)
    
    x = 550 + j  # Starting y-position
    z = 0    # Tracks total height offset
    
    _, _, _, line_height = draw.textbbox((0, 0), "a", font=font)  
    
    for track in formatted_tracks:
        formatted_track = textwrap.fill(str(track), width=45)
        track_lines = formatted_track.split("\n")  # Split into multiple lines
    
        draw.text((50, x + z + int(line_height) + j), text=formatted_track, fill="#0070f3", font=fontSub)  
    
        # Update total height offset
        z += line_height * len(track_lines) + 10
    
    temp_image_path = os.path.join("/tmp", "critique.png") # Save image to temp folder
    img.save(temp_image_path, "PNG")
    return send_file(temp_image_path, as_attachment=True, download_name="critique.png") # Send image as attachment

# Serve the React app
@app.route('/')
@app.route('/results')
def index():
    return send_from_directory('build', 'index.html')

@app.route('/logo192.png')
def logo192():
    return send_from_directory('build', 'logo192.png', mimetype='image/x-icon')

@app.route('/logo512.png')
def logo512():
    return send_from_directory('build', 'logo512.png', mimetype='image/x-icon')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('build', 'favicon.ico', mimetype='image/x-icon')

if __name__ == '__main__':
    app.run()