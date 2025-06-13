#!/usr/bin/env python3

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv
import re
import time

load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URL')

def setup_spotify_client():
    """Set up and return an authenticated Spotify client."""
    scope = 'playlist-modify-public playlist-modify-private'
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope
    ))

def parse_song_line(line: str) -> Tuple[str, str]:
    """Parse a line into title and artist(s)."""
    if ' by ' not in line:
        return line, ''
    
    title, artists = line.split(' by ', 1)
    return title.strip(), artists.strip()

def is_track_number(title: str) -> bool:
    """Check if the title is just 'Track' or 'Track + number'."""
    # Convert to lowercase and remove special characters
    clean_title = re.sub(r'[^\w\s]', ' ', title.lower())
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    
    # Check if it matches "track" or "track number"
    return bool(re.match(r'^track(?:\s+\d+)?$', clean_title))

def clean_for_search(text: str) -> str:
    """Clean text for search by removing common variations and special characters."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove common variations
    text = re.sub(r'\b(feat|featuring|ft|feat\.|featuring\.)\b.*$', '', text)
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def generate_search_queries(title: str, artists: str) -> List[str]:
    """Generate different search query variations to try."""
    queries = []
    
    # Clean the inputs
    clean_title = clean_for_search(title)
    clean_artists = clean_for_search(artists)
    
    # Basic queries
    queries.append(f"{clean_title} {clean_artists}")
    queries.append(f"{clean_title}")
    
    # Try with just the first artist if there are multiple
    if ' _ ' in clean_artists:
        first_artist = clean_artists.split(' _ ')[0]
        queries.append(f"{clean_title} {first_artist}")
    
    # Try without common words in title
    title_words = clean_title.split()
    if len(title_words) > 2:
        # Remove common words like "the", "a", "an"
        filtered_words = [w for w in title_words if w not in {'the', 'a', 'an'}]
        if filtered_words:
            queries.append(f"{' '.join(filtered_words)} {clean_artists}")
    
    return queries

def search_track(sp: spotipy.Spotify, query: str) -> Optional[str]:
    """Search for a track and return its ID if found."""
    try:
        results = sp.search(query, limit=1, type='track')
        if results['tracks']['items']:
            return results['tracks']['items'][0]['id']
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
    return None

def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, track_ids: List[str]):
    """Add tracks to the playlist."""
    # Spotify API allows adding up to 100 tracks at a time
    chunk_size = 100
    for i in range(0, len(track_ids), chunk_size):
        chunk = track_ids[i:i + chunk_size]
        sp.playlist_add_items(playlist_id, chunk)
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Add unmatched songs to a Spotify playlist.')
    parser.add_argument('playlist_id', help='Spotify playlist ID')
    parser.add_argument('text_file', help='Path to the text file containing unmatched songs')
    args = parser.parse_args()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        exit(1)
    
    try:
        # Set up Spotify client
        sp = setup_spotify_client()
        
        # Read and process the text file
        found_tracks = []
        not_found_tracks = []
        
        with open(args.text_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                title, artists = parse_song_line(line)
                
                # Skip if the title is just "Track" or "Track + number"
                if is_track_number(title):
                    print(f"Skipping track number: {line}")
                    continue
                
                queries = generate_search_queries(title, artists)
                
                track_id = None
                for query in queries:
                    track_id = search_track(sp, query)
                    if track_id:
                        break
                
                if track_id:
                    found_tracks.append(track_id)
                    print(f"Found: {line}")
                else:
                    not_found_tracks.append(line)
                    print(f"Not found: {line}")
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
        
        # Add found tracks to playlist
        if found_tracks:
            print(f"\nAdding {len(found_tracks)} tracks to playlist...")
            add_tracks_to_playlist(sp, args.playlist_id, found_tracks)
            print("Successfully added tracks to playlist!")
        
        # Write not found tracks back to file
        if not_found_tracks:
            with open(args.text_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(not_found_tracks))
                if not_found_tracks:  # Add a newline at the end if there were any lines
                    f.write('\n')
            print(f"\n{len(not_found_tracks)} tracks could not be found and were written back to the file.")
        else:
            # If all tracks were found, create an empty file
            open(args.text_file, 'w').close()
            print("\nAll tracks were found and added to the playlist. The text file is now empty.")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main() 