import os
import time
from pathlib import Path
from perplexipy import PerplexityClient

class LogitMonitor:
    def __init__(self):
        self.client = PerplexityClient(key=os.getenv("PERPLEXITY_API_KEY"))
        self.log_dir = Path("/app/logs")
        self.log_dir.mkdir(exist_ok=True)
        
    def monitor_actions(self):
        while True:
            # Simulated Cursor action monitoring
            action = f"Action at {time.ctime()}"
            log_entry = f"[{time.ctime()}] {action}"
            
            # Save to log file
            with open(self.log_dir/"cursor_actions.log", "a") as f:
                f.write(log_entry + "\n")
            
            # Send to Perplexity
            self.client.query(
                f"Analyze Cursor action: {log_entry}",
                system_prompt="You are the EverythingSwing project supervisor"
            )
            
            time.sleep(5)

if __name__ == "__main__":
    LogitMonitor().monitor_actions()
