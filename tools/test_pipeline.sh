#!/bin/bash

# Test script for EverythingSwing processing pipeline
# This script tests the basic workflow with a sample audio file

# Set up variables
BASE_DIR="/Volumes/AI_ETS_2TB/EverythingSwing"
SAMPLE_FILE="$1"

if [ -z "$SAMPLE_FILE" ]; then
  echo "Usage: $0 path/to/sample_audio_file"
  exit 1
fi

if [ ! -f "$SAMPLE_FILE" ]; then
  echo "Error: Sample file not found: $SAMPLE_FILE"
  exit 1
fi

# Create a timestamp for this test run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_DIR="$BASE_DIR/tests/test_$TIMESTAMP"
mkdir -p "$TEST_DIR"

echo "=== EverythingSwing Pipeline Test ==="
echo "Sample file: $SAMPLE_FILE"
echo "Test directory: $TEST_DIR"
echo "Timestamp: $TIMESTAMP"
echo "==================================="

# Step 1: Copy sample file to test directory
echo "Step 1: Importing sample file..."
cp "$SAMPLE_FILE" "$TEST_DIR/"
FILENAME=$(basename "$SAMPLE_FILE")
echo "File imported: $FILENAME"

# Step 2: Simulate transcription (in real usage, you would call MacWhisper here)
echo "Step 2: Simulating transcription..."
echo "This is a simulated transcription of the audio file." > "$TEST_DIR/${FILENAME%.*}.txt"
echo "It would normally contain the full text from MacWhisper." >> "$TEST_DIR/${FILENAME%.*}.txt"
echo "Transcription created: ${FILENAME%.*}.txt"

# Step 3: Apply text filter to clean transcription
echo "Step 3: Cleaning transcription..."
if [ -f "$HOME/Library/Application Support/BBEdit/Text Filters/CleanTranscription.sh" ]; then
  cat "$TEST_DIR/${FILENAME%.*}.txt" | "$HOME/Library/Application Support/BBEdit/Text Filters/CleanTranscription.sh" > "$TEST_DIR/${FILENAME%.*}_cleaned.txt"
  echo "Cleaned transcription: ${FILENAME%.*}_cleaned.txt"
else
  echo "Warning: CleanTranscription.sh not found. Skipping cleaning step."
fi

echo "=== Test Complete ==="
echo "All test files are in: $TEST_DIR"
