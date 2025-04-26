import os
import sys
import json
import time
import logging
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional, Union
import redis
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uvicorn

#!/0usr/bin/env python3
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('summarization_service')

# FastAPI app
app = FastAPI(title="Summarization API", description="API for audio transcript summarization using LM Studio")

# Redis client
redis_client = None

class SummarizationRequest(BaseModel):
    """Request model for summarization"""
    transcript_path: str
    output_path: Optional[str] = None
    max_length: Optional[int] = 512
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None

class SummarizationResponse(BaseModel):
    """Response model for summarization"""
    status: str
    summary: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None

class LMStudioClient:
    """Client for LM Studio API interactions"""
    
    def __init__(self, host: str = 'lm-studio', port: int = 1234):
        """Initialize with LM Studio server details"""
        self.base_url = f"http://{host}:{port}/v1"
        logger.info(f"LM Studio client initialized with base URL: {self.base_url}")
        
        # Test connection
        try:
            self.test_connection()
        except Exception as e:
            logger.warning(f"Could not connect to LM Studio: {str(e)}")
    
    def test_connection(self):
        """Test connection to LM Studio server"""
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                logger.info("Successfully connected to LM Studio")
                return True
            else:
                logger.error(f"Failed to connect to LM Studio. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to LM Studio: {str(e)}")
            raise
    
    def summarize(self, text: str, max_tokens: int = 512, 
                  temperature: float = 0.7, system_prompt: str = None) -> str:
        """Generate a summary using LM Studio"""
        if not system_prompt:
            system_prompt = (
                "You are a concise summarization assistant. Summarize the following audio "
                "transcript into a clear, factual summary that captures the key points. "
                "Be comprehensive but avoid unnecessary details."
            )
        
        try:
            data = {
                "model": "t5-summarizer-finetuned",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"[TRANSCRIPT]\n{text}\n[/TRANSCRIPT]\n\nSummary:"}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
                "repeat_penalty": 1.25,
                "top_p": 0.9,
                "top_k": 40,
                "min_p": 0.05
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", json=data)
            
            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content']
                logger.info(f"Successfully generated summary of length {len(summary)}")
                return summary
            else:
                logger.error(f"LM Studio API error: {response.status_code}, {response.text}")
                raise Exception(f"LM Studio API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            raise

def process_summarization(request: SummarizationRequest, 
                          lm_studio_host: str = 'lm-studio', 
                          lm_studio_port: int = 1234) -> SummarizationResponse:
    """Process a summarization request"""
    
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(host='redis', port=6379)
    
    try:
        # Initialize LM Studio client
        lm_client = LMStudioClient(host=lm_studio_host, port=lm_studio_port)
        
        # Read transcript
        if not os.path.exists(request.transcript_path):
            raise FileNotFoundError(f"Transcript file not found: {request.transcript_path}")
        
        with open(request.transcript_path, 'r') as f:
            transcript_data = json.load(f)
        
        # Extract full text from segments
        if 'segments' in transcript_data:
            text = " ".join([segment.get('text', '') for segment in transcript_data['segments']])
        else:
            text = transcript_data.get('text', '')
        
        if not text:
            raise ValueError("No text found in transcript")
        
        # Generate summary
        summary = lm_client.summarize(
            text=text,
            max_tokens=request.max_length,
            temperature=request.temperature,
            system_prompt=request.system_prompt
        )
        
        # Determine output path
        output_path = request.output_path
        if not output_path:
            output_path = request.transcript_path.replace('_diarized.json', '_summary.txt')
            if output_path == request.transcript_path:
                output_path = os.path.splitext(request.transcript_path)[0] + "_summary.txt"
        
        # Save summary
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(summary)
        
        # Publish to Redis
        if redis_client:
            redis_client.publish('summarization_completed', json.dumps({
                'transcript_path': request.transcript_path,
                'summary_path': output_path,
                'status': 'completed'
            }))
        
        logger.info(f"Summarization completed for {request.transcript_path}, saved to {output_path}")
        
        return SummarizationResponse(
            status="completed",
            summary=summary,
            output_path=output_path
        )
        
    except Exception as e:
        logger.error(f"Error processing summarization: {str(e)}")
        
        # Publish error to Redis
        if redis_client:
            redis_client.publish('summarization_completed', json.dumps({
                'transcript_path': request.transcript_path,
                'status': 'failed',
                'error': str(e)
            }))
        
        return SummarizationResponse(
            status="failed",
            error=str(e)
        )

@app.post("/summarize", response_model=SummarizationResponse)
async def summarize_endpoint(request: SummarizationRequest, background_tasks: BackgroundTasks):
    """API endpoint for summarization"""
    background_tasks.add_task(
        process_summarization, 
        request,
        os.environ.get('LM_STUDIO_HOST', 'lm-studio'),
        int(os.environ.get('LM_STUDIO_PORT', 1234))
    )
    
    return SummarizationResponse(
        status="processing",
        output_path=request.output_path
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

def main():
    parser = argparse.ArgumentParser(description='LM Studio API server')
    parser.add_argument('-host', type=str, default='0.0.0.0', help='Host to bind')
    parser.add_argument('-port', type=int, default=8000, help='Port to bind')
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
