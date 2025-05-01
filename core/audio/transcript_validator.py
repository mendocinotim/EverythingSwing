from perplexipy import PerplexityClient
import json
from pathlib import Path

class TranscriptValidator:
    def __init__(self, api_key: str):
        self.client = PerplexityClient(key=api_key)
        self.context = self._load_project_context()
    
    def validate_chunk(self, transcript_chunk: dict) -> dict:
        """Validate transcript against project requirements"""
        prompt = f"""
        Validate transcript chunk for EverythingSwing project:
        
        PROJECT CONTEXT:
        {json.dumps(self.context, indent=2)}
        
        TRANSCRIPT CHUNK:
        {json.dumps(transcript_chunk, indent=2)}
        
        Required Checks:
        1. Verify speaker labels match known voices (Fred Hall/Guest)
        2. Validate Big Band terminology accuracy
        3. Identify missing musical references
        4. Check timestamp alignment
        5. Flag potential transcription errors
        """
        
        return {
            "validation": self.client.query(prompt),
            "original_chunk": transcript_chunk
        }
    
    def _load_project_context(self) -> dict:
        """Load EverythingSwing knowledge base"""
        return {
            "known_speakers": ["Fred Hall", "Guest"],
            "music_terms": [
                "Big Band", "Swing", "Arrangement",
                "Brass Section", "Rhythm Section"
            ],
            "target_artists": ["Glenn Miller", "Count Basie", "Duke Ellington"],
            "validation_rules": {
                "min_speaker_confidence": 0.85,
                "max_speaker_gap": 1.5
            }
        }
