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
app.secret_key = os.urandom(24)
CORS(app, origins=["http://localhost:3000", "https://personify-nu.vercel.app"])

# Spotify credentials from .env file
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://personify-nu.vercel.app/callback")

# Spotify Authentication URL
@app.route('/login')
def login():
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

            # Redirect to results immediately
            return redirect("http://personify-nu.vercel.app/results")

    return jsonify({"error": "Failed to retrieve access token or top tracks"}), 500

def generate_track_critique(tracks):
    # Initialize OpenAI (or DeepSeek) client with the correct API key and endpoint
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1")

    # Create a message to send to the model, you could use track names or further track details
    track_names = [f"{track['name']} - {track['artist']}" for track in tracks]
    user_message = f"Guess my MBTI and critique my top tracks from Spotify, be very mean, make fun of me. Here are the songs: {', '.join(track_names)}. don't roast the tracks one by one. use ** for bold and * for italic. limit your response to 200 words and list and enumerate the first 10 tracks (song name and artist) as '**Your top 10 tracks:**' after your description. in bold,  write a short but very niche degrading sentence about my music taste as the last sentence, on a seperate line similar to this: 'Your music taste is music-to-stalk-boys-to-jazz-snob-nobody-puts-baby-in-a-corner bad' but dont copy it. don't mention pinterest and don't assume gender. do not use any other symbol characters except for - and . in the last sentence."

    # Call OpenAI (or DeepSeek) to generate a critique message
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat:free",  # Or any other model you're using
        messages=[
            {"role": "system", "content": "You are a very sarcastic gen-z niche music critic who thinks everyone is beneath them and that has a deep obsession with myers-briggs."},
            {"role": "user", "content": user_message},
        ]
    )

    # Return the response from the AI (the critique)
    return response.choices[0].message.content

@app.route('/get-critique')
def get_critique():
    tracks = session.get('tracks')
    print(tracks)
    if not tracks:
        return jsonify({"critique": "No tracks available."})

    # Call AI now
    critique = generate_track_critique(tracks)
    session['critique'] = critique
    return jsonify({"critique": critique})

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
    app.run(debug=True)