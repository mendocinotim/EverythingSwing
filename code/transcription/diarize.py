#!/usr/bin/env python3
import os
import sys
import json
import time
import torch
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import redis

# NeMo imports
from nemo.collections.asr.models import SortformerEncLabelModel
from omegaconf import OmegaConf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('diarization_service')

class SortformerDiarizer:
    """Wrapper class for Sortformer diarization model"""
    
    def __init__(self, model_path: str = None):
        """Initialize the diarizer with a Sortformer model"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Load the model
        if model_path and os.path.exists(model_path):
            logger.info(f"Loading Sortformer model from {model_path}")
            self.model = SortformerEncLabelModel.restore_from(
                restore_path=model_path,
                map_location=self.device,
                strict=False
            )
        else:
            logger.info("Downloading Sortformer model from HuggingFace")
            self.model = SortformerEncLabelModel.from_pretrained(
                "nvidia/diar_sortformer_4spk-v1", 
                map_location=self.device
            )
        
        self.model.eval()
        logger.info("Sortformer model loaded successfully")
    
    def process_audio(self, audio_path: str) -> Dict:
        """Process audio file and return diarization results"""
        logger.info(f"Processing audio file: {audio_path}")
        
        try:
            # Run diarization
            diar_output = self.model.diarize(audio_path)
            
            # Format results
            result = {
                "success": True,
                "file": audio_path,
                "segments": []
            }
            
            # Convert timestamps from Sortformer format to segment list
            for segment in diar_output:
                result["segments"].append({
                    "speaker": f"speaker_{segment['speaker']}",
                    "start_time": float(segment["start"]),
                    "end_time": float(segment["end"]),
                    "text": segment.get("text", "")
                })
            
            logger.info(f"Diarization complete for {audio_path}. Identified {len(result['segments'])} segments.")
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio file: {str(e)}")
            return {"success": False, "file": audio_path, "error": str(e)}

class DiarizationService:
    """Service to handle diarization of audio files via Redis"""
    
    def __init__(self, redis_host: str = 'redis', redis_port: int = 6379):
        """Initialize the service with Redis connection"""
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.pubsub = self.redis_client.pubsub()
        
        # Initialize diarizer
        model_path = os.environ.get('SORTFORMER_MODEL_PATH')
        self.diarizer = SortformerDiarizer(model_path)
        
        # Subscribe to channels
        self.pubsub.subscribe('asr_completed')
        logger.info("Diarization service initialized and subscribed to channels")
    
    def run(self):
        """Run the service loop to process incoming diarization requests"""
        logger.info("Starting diarization service loop")
        
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'].decode('utf-8'))
                    logger.info(f"Received message: {data}")
                    
                    if 'audio_path' in data:
                        audio_path = data['audio_path']
                        output_path = data.get('output_path', 
                                           os.path.join('/app/transcribed', 
                                                       os.path.basename(audio_path).replace('.wav', '_diarized.json')))
                        
                        # Process the audio
                        result = self.diarizer.process_audio(audio_path)
                        
                        # Save the results
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, 'w') as f:
                            json.dump(result, f, indent=2)
                        
                        # Publish completion
                        self.redis_client.publish('diarization_completed', json.dumps({
                            'audio_path': audio_path,
                            'diarization_path': output_path,
                            'status': 'completed' if result['success'] else 'failed'
                        }))
                        
                        logger.info(f"Diarization completed for {audio_path}, saved to {output_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Sortformer Diarization Service")
    parser.add_argument('--redis-host', type=str, default='redis', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    args = parser.parse_args()
    
    service = DiarizationService(redis_host=args.redis_host, redis_port=args.redis_port)
    service.run()

if __name__ == "__main__":
    main()
