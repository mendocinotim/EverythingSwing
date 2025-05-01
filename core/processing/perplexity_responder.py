# COMPLETE REPLACEMENT FOR perplexity_responder.py
import os
import time
from perplexipy import PerplexityClient

class ResponseHandler:
    def __init__(self):
        self.client = PerplexityClient(key=os.getenv("PERPLEXITY_API_KEY"))
        self.log_file = "/Volumes/AI_ETS_2TB/EverythingSwing/logs/cursor_actions.log"
        
    def analyze_actions(self):
        while True:
            if os.path.exists(self.log_file):
                with open(self.log_file) as f:
                    new_actions = f.read()
                
                if new_actions:
                    response = self.client.query(
                        f"Analyze these Cursor actions for EverythingSwing:\n{new_actions}",
                        system_prompt="You are the EverythingSwing project supervisor. Review code changes and suggest next steps."
                    )
                    print(f"Perplexity Recommendation:\n{response}")
                    
                time.sleep(30)
            else:
                time.sleep(5)

if __name__ == "__main__":
    handler = ResponseHandler()
    handler.analyze_actions()
