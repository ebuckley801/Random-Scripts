#!/usr/bin/env python3

import os
import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
from typing import List, Set, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URL = os.getenv("SPOTIFY_REDIRECT_URL")

class MusicManager:
    def __init__(self):
        """Initialize the MusicManager with Spotify authentication."""
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URL,
            scope="playlist-modify-public playlist-modify-private playlist-read-private"
        ))

    def clean_filename(self, filename: str) -> str:
        """Remove file extension and clean up the filename for better matching."""
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Remove hidden file prefix
        name = name.replace('._', '')
        
        # Remove track numbers and their separators
        name = re.sub(r'^\d+[-.]?\d*\s*', '', name)
        
        # Remove common patterns like (Official Video), [HD], etc.
        name = re.sub(r'\([^)]*\)', '', name)
        name = re.sub(r'\[[^\]]*\]', '', name)
        
        # Remove special characters and normalize spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()

    def normalize_title(self, title: str) -> str:
        """Normalize a title for comparison."""
        # Convert to lowercase
        title = title.lower()
        
        # Remove special characters and normalize spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common variations
        title = re.sub(r'\b(feat|featuring|ft|feat\.|featuring\.)\b.*$', '', title)
        
        return title

    def find_track_on_spotify(self, track_name: str, artist_name: str) -> Optional[str]:
        """Search for a track on Spotify and return its URI if found."""
        query = f"track:{track_name} artist:{artist_name}"
        results = self.sp.search(q=query, type="track", limit=1)
        
        if results['tracks']['items']:
            return results['tracks']['items'][0]['uri']
        return None

    def get_playlist_tracks(self, playlist_id: str) -> List[dict]:
        """Get all tracks from a playlist."""
        results = self.sp.playlist_tracks(playlist_id)
        tracks = results['items']
        
        while results['next']:
            results = self.sp.next(results)
            tracks.extend(results['items'])
        
        return tracks

    def get_playlist_titles(self, playlist_id: str) -> Set[str]:
        """Get normalized titles from a Spotify playlist."""
        tracks = self.get_playlist_tracks(playlist_id)
        titles = set()
        
        for track in tracks:
            if not track['track']:
                continue
            
            title = track['track']['name']
            artists = [artist['name'] for artist in track['track']['artists']]
            full_title = f"{title} by {' _ '.join(artists)}"
            titles.add(self.normalize_title(full_title))
        
        return titles

    def create_playlist_from_directory(self, directory_path: str, playlist_name: str) -> str:
        """Create a Spotify playlist from music files in the given directory."""
        user_id = self.sp.current_user()['id']
        playlist = self.sp.user_playlist_create(user_id, playlist_name)
        playlist_id = playlist['id']
        
        track_uris = []
        unmatched_songs = []
        
        for root, dirs, files in os.walk(directory_path):
            if os.path.basename(root).lower() == 'itunes' and 'itunes music' not in root.lower():
                continue
                
            rel_path = os.path.relpath(root, directory_path)
            path_parts = rel_path.split(os.sep)
            
            if rel_path == '.':
                continue
                
            if 'itunes music' in root.lower():
                artist_name = os.path.basename(root)
            else:
                artist_name = path_parts[0]
            
            for file in files:
                file_path = os.path.join(root, file)
                if file_path.lower().endswith(('.mp3', '.m4a', '.wav', '.flac')):
                    track_name = self.clean_filename(os.path.basename(file_path))
                    track_uri = self.find_track_on_spotify(track_name, artist_name)
                    if track_uri:
                        print(f"Found match: {track_name} by {artist_name}")
                        track_uris.append(track_uri)
                    else:
                        print(f"No match found for: {track_name} by {artist_name}")
                        unmatched_songs.append(f"{track_name} by {artist_name}")
        
        # Add tracks to playlist in chunks of 100
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i + 100]
            self.sp.playlist_add_items(playlist_id, chunk)
        
        if unmatched_songs:
            with open("unmatched_songs.txt", 'w', encoding='utf-8') as f:
                f.write("Songs that couldn't be matched on Spotify:\n\n")
                for song in unmatched_songs:
                    f.write(f"{song}\n")
            print(f"\nWrote {len(unmatched_songs)} unmatched songs to unmatched_songs.txt")
        
        print(f"\nCreated playlist '{playlist_name}' with {len(track_uris)} tracks")
        return playlist_id

    def remove_duplicates_from_file(self, input_file: str, output_file: Optional[str] = None) -> None:
        """Remove duplicate lines from a text file while preserving order."""
        if output_file is None:
            output_file = input_file
        
        seen = set()
        unique_lines = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                normalized_line = self.normalize_title(line)
                if normalized_line not in seen:
                    seen.add(normalized_line)
                    unique_lines.append(line)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_lines))
            if unique_lines:
                f.write('\n')

    def compare_and_remove_duplicates(self, playlist_id: str, text_file: str) -> None:
        """Compare song titles between a Spotify playlist and a text file."""
        playlist_titles = self.get_playlist_titles(playlist_id)
        kept_lines = []
        removed_count = 0
        
        with open(text_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                normalized_line = self.normalize_title(line)
                if normalized_line not in playlist_titles:
                    kept_lines.append(line)
                else:
                    removed_count += 1
                    print(f"Removing: {line}")
        
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(kept_lines))
            if kept_lines:
                f.write('\n')
        
        print(f"\nRemoved {removed_count} duplicate songs from the text file.")
        print(f"Kept {len(kept_lines)} unique songs.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Music Manager - Handle Spotify playlists and local music files')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create playlist from directory command
    create_parser = subparsers.add_parser('create-playlist', help='Create a playlist from local music files')
    create_parser.add_argument('directory', help='Directory containing music files')
    create_parser.add_argument('playlist_name', help='Name for the new playlist')
    
    # Remove duplicates from file command
    remove_parser = subparsers.add_parser('remove-duplicates', help='Remove duplicate lines from a text file')
    remove_parser.add_argument('input_file', help='Input text file path')
    remove_parser.add_argument('-o', '--output', help='Output file path (optional)')
    
    # Compare and remove duplicates command
    compare_parser = subparsers.add_parser('compare-playlist', help='Compare and remove duplicates between playlist and text file')
    compare_parser.add_argument('playlist_id', help='Spotify playlist ID')
    compare_parser.add_argument('text_file', help='Path to the text file containing song titles')
    
    args = parser.parse_args()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        exit(1)
    
    try:
        manager = MusicManager()
        
        if args.command == 'create-playlist':
            manager.create_playlist_from_directory(args.directory, args.playlist_name)
        elif args.command == 'remove-duplicates':
            manager.remove_duplicates_from_file(args.input_file, args.output)
        elif args.command == 'compare-playlist':
            manager.compare_and_remove_duplicates(args.playlist_id, args.text_file)
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main() 