import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
import re

# Spotify API credentials
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8888/callback"

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private"
))

def clean_filename(filename):
    """Remove file extension and clean up the filename for better matching."""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    # Remove common patterns like (Official Video), [HD], etc.
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\[[^\]]*\]', '', name)
    return name.strip()

def find_track_on_spotify(track_name, artist_name):
    """Search for a track on Spotify and return its URI if found."""
    query = f"track:{track_name} artist:{artist_name}"
    results = sp.search(q=query, type="track", limit=1)
    
    if results['tracks']['items']:
        return results['tracks']['items'][0]['uri']
    return None

def process_music_file(file_path, artist_name):
    """Process a single music file and return its Spotify URI if found."""
    if file_path.lower().endswith(('.mp3', '.m4a', '.wav', '.flac')):
        track_name = clean_filename(os.path.basename(file_path))
        track_uri = find_track_on_spotify(track_name, artist_name)
        if track_uri:
            print(f"Found match: {track_name} by {artist_name}")
            return track_uri
        else:
            print(f"No match found for: {track_name} by {artist_name}")
    return None

def create_playlist_from_directory(directory_path, playlist_name):
    """Create a Spotify playlist from music files in the given directory."""
    # Create a new playlist
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user_id, playlist_name)
    playlist_id = playlist['id']
    
    # Track URIs to add to playlist
    track_uris = []
    
    # Walk through the directory
    for root, dirs, files in os.walk(directory_path):
        # Get the relative path from the root directory
        rel_path = os.path.relpath(root, directory_path)
        path_parts = rel_path.split(os.sep)
        
        # If we're in the root directory, skip (no artist name)
        if rel_path == '.':
            continue
            
        # The first directory level is the artist name
        artist_name = path_parts[0]
        
        # Process files in current directory
        for file in files:
            file_path = os.path.join(root, file)
            track_uri = process_music_file(file_path, artist_name)
            if track_uri:
                track_uris.append(track_uri)
    
    # Add tracks to playlist in chunks of 100 (Spotify API limit)
    for i in range(0, len(track_uris), 100):
        chunk = track_uris[i:i + 100]
        sp.playlist_add_items(playlist_id, chunk)
    
    print(f"\nCreated playlist '{playlist_name}' with {len(track_uris)} tracks")
    return playlist_id

if __name__ == "__main__":
    # Replace with your music directory path
    music_directory = "path/to/your/music/directory"
    playlist_name = "My Local Music Collection"
    
    create_playlist_from_directory(music_directory, playlist_name)
