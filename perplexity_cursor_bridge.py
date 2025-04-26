# COMPLETE REPLACEMENT FOR perplexity_cursor_bridge.py
import os
import json
import time
from dotenv import load_dotenv
from perplexipy import PerplexityClient
from pathlib import Path

# Load environment variables
load_dotenv()
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Directories
LOG_DIR = Path('./logs')
CURSOR_LOG = LOG_DIR / 'cursor_actions.log'
RECOMMENDATIONS_LOG = LOG_DIR / 'perplexity_recommendations.log'

# Ensure directories exist
LOG_DIR.mkdir(exist_ok=True)

# Initialize Perplexity client
# Changed 'api_key' to 'key' to match the expected parameter name
client = PerplexityClient(key=PERPLEXITY_API_KEY)

def get_cursor_actions():
    """Read the latest cursor actions from log file"""
    try:
        if CURSOR_LOG.exists():
            with open(CURSOR_LOG, 'r') as f:
                return f.read()
        return "No cursor actions logged yet."
    except Exception as e:
        return f"Error reading cursor logs: {str(e)}"

def analyze_with_perplexity():
    """Use Perplexity to analyze cursor actions and provide recommendations"""
    cursor_actions = get_cursor_actions()
    
    query = f"""
    As an AI project manager for the EverythingSwing project, analyze these recent 
    Cursor agent actions and recommend next steps:
    
    {cursor_actions}
    
    Focus on architectural guidance, best practices, and potential issues to watch for.
    """
    
    print("Sending to Perplexity for analysis...")
    result = client.query(query)
    
    # Save recommendation to log file
    with open(RECOMMENDATIONS_LOG, 'a') as f:
        f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(result)
        f.write("\n\n")
    
    print("\nPerplexity Recommendation saved to logs/perplexity_recommendations.log")
    print("Summary:", result[:200], "...\n")

if __name__ == "__main__":
    print("Perplexity-Cursor Bridge")
    print("========================")
    
    if not PERPLEXITY_API_KEY:
        print("ERROR: PERPLEXITY_API_KEY not found in .env file")
        print("Please add your API key to .env file as: PERPLEXITY_API_KEY=your_key_here")
        exit(1)
        
    try:
        analyze_with_perplexity()
    except Exception as e:
        print(f"Error: {str(e)}")
