#!/usr/bin/env python3
"""
Fingerprint Manager module for processing audio files and storing fingerprints in a database.
"""

import os
import argparse
import traceback
from pathlib import Path
import essentia.standard as es

# Import required modules
from .fingerprint_generator import convert_audio_fingerprint
from ..utils.db_manager import DatabaseManager

def main():
    parser = argparse.ArgumentParser(
        description="Generate audio fingerprints from WAV files and save them to the database"
    )
    parser.add_argument("--name", required=True, help="Name for the fingerprint collection")
    parser.add_argument("--genre", required=True, help="Genre of worldcup")
    parser.add_argument("--series", help="Series numbering", default=1)
    parser.add_argument("--dir", help="Directory containing audio files", default="audio")
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create worldcup record
    worldcup_data = {'title': args.name, 'genre': args.genre, 'series_number': args.series}
    worldcup_id = db_manager.insert_worldcup(worldcup_data)
    
    # Process audio files
    # Check if directory exist
    audio_dir = Path(args.dir)
    if not audio_dir.is_dir():
        raise Exception(f"Cannot find audio directory: {audio_dir}")
    
    # get list of audio file path
    audio_paths = [str(f) for f in audio_dir.glob("*.wav")]
    if not audio_paths:
        raise Exception(f"Empty directory. No audio data: {audio_dir}")
    print(f"Whole audio count: {len(audio_paths)}")

    processed_count = 0
    for audio_path in audio_paths:
        print(f"Processing {audio_path}...")
        audio_loader = es.MonoLoader(filename=audio_path)
        audio_file = audio_loader()

        fingerprint = convert_audio_fingerprint(audio_file)
        name = Path(audio_path).stem

        print(f"Saving database {audio_path}...")
        record = {
            'name': name,
            "artist": None,
            'worldcup_id': worldcup_id,
            **fingerprint
        }
        db_manager.insert_changpop(record)
    
        processed_count += 1
        print(f"Successfully processed: {audio_path}")
    
    print(f"Successfully processed {processed_count} out of {len(audio_paths)} files.")

if __name__ == "__main__":
    main()