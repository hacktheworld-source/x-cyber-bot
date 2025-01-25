#!/bin/bash

# Exit on any error
set -e

echo "Setting up X-Bot environment..."

# Update system
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
sudo apt install -y python3-pip python3-venv git wget

# Create project structure
echo "Creating project structure..."
mkdir -p data/backups logs models
chmod 755 data data/backups logs models

# Set up Python environment
echo "Setting up Python environment..."
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create config if it doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo "Creating default config..."
    cp config/config.yaml.example config/config.yaml
fi

echo "Setup complete! Please:"
echo "1. Edit config/config.yaml with your Twitter API credentials"
echo "2. Verify the model path in config.yaml"
echo "3. Run the test scripts in README.md"
echo "4. Start the bot with: python3 -m src.main" 