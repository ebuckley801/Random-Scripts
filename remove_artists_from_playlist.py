#!/usr/bin/env python3

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from typing import List, Set
from dotenv import load_dotenv
import re

load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8888/callback'

def setup_spotify_client():
    """Set up and return an authenticated Spotify client."""
    scope = 'playlist-modify-public playlist-modify-private'
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope
    ))

def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[dict]:
    """Get all tracks from a playlist."""
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    return tracks

def get_tracks_to_remove(tracks: List[dict]) -> List[str]:
    """Get track IDs for songs that match the pattern 'Track' followed by a number."""
    tracks_to_remove = []
    pattern = re.compile(r'Track\s+\d+', re.IGNORECASE)
    
    for track in tracks:
        if not track['track']:  # Skip if track is None
            continue
            
        # Get track name
        track_name = track['track']['name']
        
        # Check if the track name matches the pattern
        if pattern.search(track_name):
            tracks_to_remove.append(track['track']['id'])
            print(f"Found track to remove: {track_name}")
    
    return tracks_to_remove

def remove_tracks_from_playlist(sp: spotipy.Spotify, playlist_id: str, track_ids: List[str]):
    """Remove tracks from the playlist."""
    # Spotify API allows removing up to 100 tracks at a time
    chunk_size = 100
    for i in range(0, len(track_ids), chunk_size):
        chunk = track_ids[i:i + chunk_size]
        sp.playlist_remove_all_occurrences_of_items(playlist_id, chunk)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove tracks with "Track" followed by a number from a Spotify playlist.')
    parser.add_argument('playlist_id', help='Spotify playlist ID')
    args = parser.parse_args()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        exit(1)
    
    try:
        # Set up Spotify client
        sp = setup_spotify_client()
        
        # Get playlist tracks
        print("Fetching playlist tracks...")
        tracks = get_playlist_tracks(sp, args.playlist_id)
        
        # Get tracks to remove
        print("Identifying tracks to remove...")
        tracks_to_remove = get_tracks_to_remove(tracks)
        
        if not tracks_to_remove:
            print("No tracks found matching the pattern 'Track' followed by a number.")
            return
        
        # Remove tracks
        print(f"Removing {len(tracks_to_remove)} tracks...")
        remove_tracks_from_playlist(sp, args.playlist_id, tracks_to_remove)
        
        print("Successfully removed tracks from the playlist!")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main() 