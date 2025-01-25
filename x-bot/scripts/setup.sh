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

# Create bot user
echo "Creating bot user..."
sudo useradd -r -s /bin/false x-bot || true

# Create project structure
echo "Creating project structure..."
sudo mkdir -p /opt/x-bot
sudo mkdir -p /var/log/x-bot
sudo mkdir -p /opt/x-bot/data/backups
sudo mkdir -p /opt/x-bot/logs

# Set permissions
sudo chown -R x-bot:x-bot /opt/x-bot
sudo chown -R x-bot:x-bot /var/log/x-bot

# Copy files
echo "Copying project files..."
sudo cp -r . /opt/x-bot/
sudo chown -R x-bot:x-bot /opt/x-bot

# Set up Python environment
echo "Setting up Python environment..."
cd /opt/x-bot
sudo -u x-bot python3 -m venv env
sudo -u x-bot env/bin/pip install --upgrade pip
sudo -u x-bot env/bin/pip install -r requirements.txt

# Create config if it doesn't exist
if [ ! -f "/opt/x-bot/config/config.yaml" ]; then
    echo "Creating default config..."
    sudo -u x-bot cp config/config.yaml.example config/config.yaml
fi

# Set up systemd service
echo "Setting up systemd service..."
sudo cp scripts/x-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable x-bot

# Set up backup cron job
echo "Setting up backup cron job..."
(crontab -l 2>/dev/null; echo "0 0 * * * /opt/x-bot/env/bin/python /opt/x-bot/scripts/backup.py") | crontab -

echo "Setup complete! Please:"
echo "1. Edit /opt/x-bot/config/config.yaml with your API credentials"
echo "2. Start the service with: sudo systemctl start x-bot"
echo "3. Check status with: sudo systemctl status x-bot"
echo "4. View logs with: tail -f /var/log/x-bot/bot.log" 