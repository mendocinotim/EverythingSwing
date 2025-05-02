#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from datetime import datetime

# Configuration
LOGS_DIR = "/Volumes/AI_ETS_2TB/EverythingSwing/logs"
TASKS_DIR = "/Volumes/AI_ETS_2TB/EverythingSwing/tasks"
CONFIG_FILE = os.path.join(LOGS_DIR, ".logit_config")
API_ENDPOINT = "https://api.perplexity.ai/chat/completions"

def load_config():
    """Load configuration from file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file not found. Please run 'logit -c' to configure.")
        sys.exit(1)
    
    config = {}
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')
    
    if 'PERPLEXITY_API_KEY' not in config:
        print("API key not found in configuration. Please run 'logit -c'.")
        sys.exit(1)
    
    return config

def analyze_cursor_actions():
    """Send recent actions to Perplexity for analysis."""
    config = load_config()
    log_file = os.path.join(LOGS_DIR, "cursor_actions.log")
    
    if not os.path.exists(log_file):
        print(f"No action log found at {log_file}")
        return
    
    # Read most recent actions (last 30 lines)
    with open(log_file, 'r') as f:
        actions = f.readlines()[-30:]
    
    # Format actions for Perplexity
    actions_text = "".join(actions)
    
    # Build query for Perplexity
    query = f"""
    Analyze these Cursor actions for the EverythingSwing project:
    
    {actions_text}
    
    Based on your understanding of the EverythingSwing project:
    1. Identify the key changes or operations being performed
    2. Suggest any potential improvements or corrections
    3. Recommend specific next steps for implementation
    
    Format your response as a clear, actionable report with numbered recommendations.
    """
    
    # Send to Perplexity API
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {config['PERPLEXITY_API_KEY']}"
    }
    
    data = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI project manager analyzing Cursor actions for the EverythingSwing project."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }
    
    try:
        print("Sending actions to Perplexity for analysis...")
        response = requests.post(API_ENDPOINT, 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        
        result = response.json()
        analysis = result["choices"][0]["message"]["content"]
        
        # Save analysis to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(LOGS_DIR, f"recommendation_{timestamp}.md")
        
        with open(output_file, 'w') as f:
            f.write(f"# Logit Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(analysis)
        
        print(f"Analysis complete. Recommendations saved to: {output_file}")
        print("\nRecommendations Summary:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
    except Exception as e:
        print(f"Error communicating with Perplexity API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.content}")

def approve_recommendation(recommendation_num):
    """Approve and implement a recommendation."""
    config = load_config()
    
    # Find most recent recommendation file
    recommendation_files = [f for f in os.listdir(LOGS_DIR) 
                           if f.startswith("recommendation_") and f.endswith(".md")]
    
    if not recommendation_files:
        print("No recommendations found")
        return
    
    recommendation_files.sort(reverse=True)
    recommendation_file = os.path.join(LOGS_DIR, recommendation_files[0])
    
    # Extract the recommendation
    with open(recommendation_file, 'r') as f:
        content = f.read()
    
    # Find the recommendation by number
    import re
    pattern = rf"{recommendation_num}\.\s+(.*?)(?=\n\d+\.|\n*$)"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"Recommendation #{recommendation_num} not found")
        return
    
    recommendation_text = match.group(1).strip()
    
    # Send approval to Perplexity
    query = f"""
    I'm approving recommendation #{recommendation_num} from your analysis:
    
    "{recommendation_text}"
    
    Please generate the implementation steps for this recommendation for the EverythingSwing project.
    Provide complete code if appropriate. Be specific and actionable.
    """
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {config['PERPLEXITY_API_KEY']}"
    }
    
    data = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI project manager implementing recommendations for the EverythingSwing project."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }
    
    try:
        print(f"Sending approval for recommendation #{recommendation_num}...")
        response = requests.post(API_ENDPOINT, 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        
        result = response.json()
        implementation = result["choices"][0]["message"]["content"]
        
        # Save implementation to tasks folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_file = os.path.join(TASKS_DIR, f"task_{timestamp}.md")
        
        with open(task_file, 'w') as f:
            f.write(f"# Implementation Task - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Original Recommendation\n{recommendation_text}\n\n")
            f.write("## Implementation Steps\n")
            f.write(implementation)
        
        print(f"Implementation plan saved to: {task_file}")
        
    except Exception as e:
        print(f"Error communicating with Perplexity API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.content}")

def request_revision(recommendation_num):
    """Request revision for a recommendation."""
    config = load_config()
    
    # Find most recent recommendation file
    recommendation_files = [f for f in os.listdir(LOGS_DIR) 
                           if f.startswith("recommendation_") and f.endswith(".md")]
    
    if not recommendation_files:
        print("No recommendations found")
        return
    
    recommendation_files.sort(reverse=True)
    recommendation_file = os.path.join(LOGS_DIR, recommendation_files[0])
    
    # Extract the recommendation
    with open(recommendation_file, 'r') as f:
        content = f.read()
    
    # Find the recommendation by number
    import re
    pattern = rf"{recommendation_num}\.\s+(.*?)(?=\n\d+\.|\n*$)"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"Recommendation #{recommendation_num} not found")
        return
    
    recommendation_text = match.group(1).strip()
    
    # Get revision request from user
    print(f"Original recommendation #{recommendation_num}:")
    print(f'"{recommendation_text}"\n')
    revision_request = input("Enter your revision request: ")
    
    # Send revision request to Perplexity
    query = f"""
    I need revision for recommendation #{recommendation_num}:
    
    Original: "{recommendation_text}"
    
    Revision request: {revision_request}
    
    Please provide a revised recommendation based on this feedback.
    """
    
    headers = {
        "Authorization": f"Bearer {config['PERPLEXITY_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar-medium-chat",
        "messages": [{"role": "user", "content": query}]
    }
    
    try:
        print("Sending revision request...")
        response = requests.post(f"{API_ENDPOINT}/chat/completions", 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        
        result = response.json()
        revised = result["choices"][0]["message"]["content"]
        
        # Save revised recommendation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        revised_file = os.path.join(LOGS_DIR, f"revised_{timestamp}.md")
        
        with open(revised_file, 'w') as f:
            f.write(f"# Revised Recommendation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Original Recommendation\n{recommendation_text}\n\n")
            f.write(f"## Revision Request\n{revision_request}\n\n")
            f.write("## Revised Recommendation\n")
            f.write(revised)
        
        print(f"Revised recommendation saved to: {revised_file}")
        
    except Exception as e:
        print(f"Error communicating with Perplexity API: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  perplexity_analyzer.py analyze")
        print("  perplexity_analyzer.py approve [recommendation_num]")
        print("  perplexity_analyzer.py revise [recommendation_num]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        analyze_cursor_actions()
    elif command == "approve" and len(sys.argv) > 2:
        approve_recommendation(int(sys.argv[2]))
    elif command == "revise" and len(sys.argv) > 2:
        request_revision(int(sys.argv[2]))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
