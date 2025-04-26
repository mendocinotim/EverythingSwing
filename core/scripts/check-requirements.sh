# COMPLETE REPLACEMENT FOR core/scripts/check-requirements.sh
#!/bin/bash
if [ -f "requirements.txt" ]; then
    echo "requirements.txt exists at: $(pwd)/requirements.txt"
else
    echo "Creating new requirements.txt"
    echo "# Project dependencies" > requirements.txt
    echo "perplexity-client==2.3.0" >> requirements.txt
    echo "python-dotenv==1.0.0" >> requirements.txt
fi
