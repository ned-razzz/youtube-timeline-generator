#!/usr/bin/env python3
"""
Fingerprint Manager module for processing audio files and storing fingerprints in a database.
"""

import os
import argparse
import traceback
from typing import Optional
import glob
from pathlib import Path

# Import required modules
from .fingerprint_generator import convert_audio_fingerprint
from ..db_manager import DatabaseManager, WorldCupData

def process_audio_files(
    directory: str = 'audio', 
    worldcup_data: Optional[WorldCupData] = None
) -> None:
    """
    Process all WAV audio files in the specified directory, generate fingerprints,
    and save them to the database.
    
    Args:
        directory (str): Directory containing WAV audio files
        worldcup_data (Optional[Worldcup]): Worldcups data to link fingerprints to
    """

    audio_path = Path(directory).resolve()

    # Ensure directory exists
    if not os.path.exists(audio_path):
        print(f"Directory not found: {audio_path}")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create worldcup record if worldcups data is provided
    worldcup_id = None
    if worldcup_data:
        worldcup_id = db_manager.insert_worldcup(worldcup_data)
    
    # Get all WAV files in the directory
    wav_files = [str(file) for file in audio_path.glob("*.wav")]

    if not wav_files:
        print(f"No WAV files found in {directory}")
        return
    
    print(f"Found {len(wav_files)} WAV files. Processing...")
    
    # Process each WAV file
    processed_count = 0
    for wav_file in wav_files:
        # Get filename without extension to use as name
        filename = os.path.basename(wav_file)
        audio_name = os.path.splitext(filename)[0]
        
        print(f"Processing {filename}...")
        
        try:
            # Generate fingerprint
            fingerprint, metadata = convert_audio_fingerprint(wav_file)
            if fingerprint is not None:
                print(f"생성된 지문 정보:")
                print(f"- 오디오 길이: {metadata['duration']:.2f}초")
                print(f"- 지문 형태: {fingerprint.shape}")
                print(f"- 메타데이터: {metadata}")
                print(f"작업이 완료되었습니다.")

            # Save to database with file name as name and None as artist
            db_manager.insert_changpop({
                'name': audio_name,
                "artist": None,
                'fingerprint': fingerprint,
                'metadata': metadata,
                'worldcup_id': worldcup_id,
            })

            processed_count += 1
            print(f"Successfully processed: {filename}")
        except Exception as e:
            traceback.print_exc()
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"Successfully processed {processed_count} out of {len(wav_files)} files.")

def main():
    """Main function to handle command line arguments and process audio files."""
    parser = argparse.ArgumentParser(
        description="Generate audio fingerprints from WAV files and save them to the database"
    )
    
    parser.add_argument(
        "--name", 
        required=True, 
        help="Name for the fingerprint collection"
    )
    
    parser.add_argument(
        "--genre", 
        help="Description for the fingerprint collection",
        default=None
    )
    
    parser.add_argument(
        "--series", 
        help="JSON string with worldcups data", 
        default=None
    )
    
    parser.add_argument(
        "--directory", 
        help="Directory containing WAV files", 
        default="audio"
    )
    
    args = parser.parse_args()
    
    # Parse worldcups data if provided
    worldcups_data = {'title': args.name, 'genre': args.genre, 'series_number': args.series}
    
    # Process audio files
    process_audio_files(
        directory=args.directory,
        worldcup_data=worldcups_data
    )

if __name__ == "__main__":
    main()