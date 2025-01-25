# X-Bot: Technical Security Bot

A Twitter/X bot that posts about interesting security vulnerabilities and technical concepts.

## Architecture

- Python-based bot running on DigitalOcean
- OpenAI API for content generation
- SQLite database for post tracking
- Async operations with aiohttp
- Test mode for safe development

## Setup Guide

### 1. DigitalOcean Setup

1. Create Droplet:
   - Ubuntu 22.04 LTS
   - Basic plan ($5/month)
   - Add your SSH key

2. SSH Access:
```bash
ssh -i path/to/ssh_key root@your_droplet_ip
```

### 2. Bot Setup

1. Clone repository:
```bash
git clone https://github.com/yourusername/x-bot.git
cd x-bot
```

2. Set up Python environment:
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

1. Create config file:
```bash
cp config/config.yaml.example config/config.yaml
```

2. Update configuration:
```yaml
twitter:
  consumer_key: ""
  consumer_secret: ""
  access_token: ""
  access_token_secret: ""
  testing:
    enabled: true  # Set to false for actual posting
    log_posts: true

ai:
  provider: "openai"
  api_key: "your_openai_key"
  model: "gpt-4"
  max_tokens: 2048
  temperature: 0.7
```

### 4. Testing

1. Run in test mode:
```bash
python3 -m src.main
```

The bot will:
- Generate content normally
- Log would-be posts instead of tweeting
- Store everything in the database
- Allow full testing without Twitter credentials

### 5. Going Live

1. Update config.yaml:
   - Set testing.enabled to false
   - Add Twitter API credentials
   - Verify all other settings

2. Start the bot:
```bash
python3 -m src.main
```

## Maintenance

- Logs: `logs/bot.log`
- Database: `data/bot.db`
- Backups: `data/backups/`

## Contributing

[Your contribution guidelines]

## License

[Your license] 