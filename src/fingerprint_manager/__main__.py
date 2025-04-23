#!/usr/bin/env python3
"""
Fingerprint Manager module for processing audio files and storing fingerprints in a database.
"""

import argparse
import json
from pathlib import Path
import essentia.standard as es

# Import required modules
from .fingerprint_generator import FingerprintGenerator
from src.utils.db_manager import ChangPopData, DatabaseManager, WorldcupData

def main():
    parser = argparse.ArgumentParser(
        description="Generate audio fingerprints from WAV files and save them to the database"
    )
    parser.add_argument("-n", "--name", required=True, help="Name for the fingerprint collection")
    parser.add_argument("-g","--genre", required=True, help="Genre of worldcup")
    parser.add_argument("-s","--series", help="Series numbering", default=1)
    parser.add_argument("-d","--dir", help="Directory containing audio files", default="audio")
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create worldcup record
    worldcup_data = WorldcupData(title=args.name, 
                                 genre=args.genre, 
                                 series_number=args.series) 
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

    fg = FingerprintGenerator()
    processed_count = 0
    for audio_path in audio_paths:
        print(f"Processing {audio_path}...")
        audio_file = es.MonoLoader(filename=audio_path)()
        sample_rate = es.MetadataReader(filename=str(audio_path))()[-2]
        fingerprint = fg.get_spectrogram_fingerprint(audio_file, sample_rate)

        print(f"Saving database {audio_path}...")
        record = ChangPopData(
            name=Path(audio_path).stem,
            fingerprint=fingerprint,
            artist=None,
            worldcup_id=worldcup_id
        )
        db_manager.insert_changpop(record)
    
        processed_count += 1
        print(f"Successfully processed: {audio_path}")
    
    print(f"Successfully processed {processed_count} out of {len(audio_paths)} files.")

if __name__ == "__main__":
    main()