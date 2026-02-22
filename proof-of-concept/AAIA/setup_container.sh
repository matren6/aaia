#!/bin/bash
# setup_container.sh

# Update and install basics
apt-get update
apt-get install -y python3 python3-pip git curl

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
pip3 install requests

# Create directory structure
mkdir -p /opt/aaia/{data,tools}
cd /opt/aaia

# Clone your code (or copy it)
# git clone <your-repo> .
# Or copy files manually

# Pull Ollama models
ollama pull llama2
ollama pull mistral
ollama pull codellama

# Initialize database
python3 scribe.py

echo "aaia setup complete"
echo "Run with: python3 main.py"