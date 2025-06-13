# Music Manager

A Python tool for managing music files and Spotify playlists. This tool provides functionality to:
- Create Spotify playlists from local music files
- Remove duplicate songs from text files
- Compare and remove duplicates between Spotify playlists and text files

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Spotify API credentials:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URL=your_redirect_url
```

## Usage

The tool provides several commands:

### Create a playlist from local music files
```bash
python music_manager.py create-playlist /path/to/music/directory "My Playlist Name"
```

### Remove duplicates from a text file
```bash
python music_manager.py remove-duplicates input.txt [-o output.txt]
```

### Compare and remove duplicates between a playlist and text file
```bash
python music_manager.py compare-playlist playlist_id text_file.txt
```

## Features

- Automatically matches local music files with Spotify tracks
- Handles various music file formats (mp3, m4a, wav, flac)
- Preserves order when removing duplicates
- Normalizes song titles for better matching
- Creates a list of unmatched songs for manual review
- Supports both iTunes Music and regular directory structures
