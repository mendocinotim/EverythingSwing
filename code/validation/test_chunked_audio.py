#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import argparse
import requests
import numpy as np
import soundfile as sf
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('chunked_audio_test')

def split_audio(audio_path, output_dir, chunk_duration_sec=30, overlap_sec=5):
    """Split audio file into overlapping chunks"""
    logger.info(f"Splitting audio file: {audio_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read audio file
    audio_data, sample_rate = sf.read(audio_path)
    
    # Calculate chunk size and overlap size in samples
    chunk_size = int(chunk_duration_sec * sample_rate)
    overlap_size = int(overlap_sec * sample_rate)
    stride = chunk_size - overlap_size
    
    # Split audio into chunks
    chunks = []
    chunk_paths = []
    start = 0
    chunk_index = 0
    
    while start < len(audio_data):
        end = min(start + chunk_size, len(audio_data))
        chunk = audio_data[start:end]
        
        # Create output path
        base_name = os.path.basename(audio_path)
        chunk_name = f"{os.path.splitext(base_name)[0]}_chunk_{chunk_index:03d}.wav"
        chunk_path = os.path.join(output_dir, chunk_name)
        
        # Save chunk
        sf.write(chunk_path, chunk, sample_rate)
        
        chunks.append(chunk)
        chunk_paths.append(chunk_path)
        
        start += stride
        chunk_index += 1
    
    logger.info(f"Split audio into {len(chunks)} chunks")
    return chunk_paths

def submit_to_asr(chunk_paths, asr_url="http://asr-service:5000/transcribe"):
    """Submit audio chunks to ASR service"""
    logger.info(f"Submitting {len(chunk_paths)} chunks to ASR service")
    
    transcriptions = []
    
    for chunk_path in tqdm(chunk_paths, desc="Processing chunks"):
        files = {'audio': open(chunk_path, 'rb')}
        data = {'format': 'wav'}
        
        try:
            response = requests.post(asr_url, files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                transcriptions.append(result)
                logger.info(f"Successfully transcribed {chunk_path}")
            else:
                logger.error(f"Failed to transcribe {chunk_path}: {response.status_code}, {response.text}")
                transcriptions.append({"error": f"Failed with status {response.status_code}"})
        except Exception as e:
            logger.error(f"Error transcribing {chunk_path}: {str(e)}")
            transcriptions.append({"error": str(e)})
        
        # Close file
        files['audio'].close()
    
    return transcriptions

def merge_transcriptions(transcriptions, output_path):
    """Merge chunked transcriptions"""
    logger.info(f"Merging {len(transcriptions)} transcriptions")
    
    merged = {
        "text": "",
        "segments": []
    }
    
    time_offset = 0.0
    
    for i, trans in enumerate(transcriptions):
        if "error" in trans:
            logger.warning(f"Skipping chunk {i} due to error: {trans['error']}")
            continue
        
        # Add segments with adjusted timing
        if "segments" in trans:
            for segment in trans["segments"]:
                segment["start"] += time_offset
                segment["end"] += time_offset
                merged["segments"].append(segment)
        
        # Update text
        if "text" in trans:
            if merged["text"]:
                merged["text"] += " " + trans["text"]
            else:
                merged["text"] = trans["text"]
        
        # Update time offset (30 seconds minus 5 seconds overlap)
        time_offset += 25.0  # 30s chunk - 5s overlap
    
    # Save merged transcription
    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=2)
    
    logger.info(f"Merged transcription saved to {output_path}")
    return merged

def main():
    parser = argparse.ArgumentParser(description="Test Chunked Audio Processing")
    parser.add_argument('--audio', type=str, required=True, help='Path to audio file')
    parser.add_argument('--output-dir', type=str, default='./processed_chunks', help='Output directory for chunks')
    parser.add_argument('--chunk-duration', type=int, default=30, help='Chunk duration in seconds')
    parser.add_argument('--overlap', type=int, default=5, help='Overlap between chunks in seconds')
    parser.add_argument('--asr-url', type=str, default='http://asr-service:5000/transcribe', help='ASR service URL')
    args = parser.parse_args()
    
    # Split audio into chunks
    chunk_paths = split_audio(
        args.audio, 
        args.output_dir,
        chunk_duration_sec=args.chunk_duration,
        overlap_sec=args.overlap
    )
    
    # Submit to ASR
    transcriptions = submit_to_asr(chunk_paths, asr_url=args.asr_url)
    
    # Merge transcriptions
    output_path = os.path.join(args.output_dir, f"{os.path.splitext(os.path.basename(args.audio))[0]}_merged.json")
    merged = merge_transcriptions(transcriptions, output_path)
    
    logger.info("Chunked audio processing test completed successfully!")

if __name__ == "__main__":
    main()
