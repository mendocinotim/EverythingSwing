#!/bin/bash
# COMPLETE REPLACEMENT FOR core/audio/convert.sh
INPUT_DIR="raw_audio"
OUTPUT_DIR="processed"

mkdir -p "$OUTPUT_DIR"

for file in "$INPUT_DIR"/*.mp3; do
    base=$(basename "$file" .mp3)
    ffmpeg -i "$file" \
        -acodec pcm_s16le \
        -ac 1 \
        -ar 16000 \
        "$OUTPUT_DIR/${base}.wav"
done
