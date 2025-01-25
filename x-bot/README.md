# X-Bot: Technical Security Bot

A Twitter/X bot that posts about interesting security vulnerabilities and technical concepts.

## Setup Guide

### 1. Oracle Cloud Setup

1. Sign up for Oracle Cloud Free Tier:
   - Go to oracle.com/cloud/free
   - Click "Start for free"
   - Complete registration (no credit card required)

2. Create VM Instance:
   - Login to Oracle Cloud Console
   - Navigate to Compute > Instances
   - Click "Create Instance"
   - Configure as follows:
     ```
     Name: x-bot
     Image: Ubuntu 22.04 Minimal
     Shape: VM.Standard.A1.Flex
     OCPU: 4
     Memory: 24 GB
     Network: Create new VCN
     Subnet: Create new subnet
     ```
   - Save the SSH private key

3. Configure Network:
   - Navigate to Virtual Cloud Network
   - Click your VCN
   - Add Ingress Rules:
     - Allow SSH (port 22)
     - Allow HTTPS (port 443)

### 2. VM Setup

1. SSH into your instance:
```bash
ssh -i path/to/private_key ubuntu@your_instance_ip
```

2. Update system and install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

3. Clone repository:
```bash
git clone https://github.com/yourusername/x-bot.git
cd x-bot
```

4. Set up Python environment:
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 3. LLM Setup

1. Create models directory:
```bash
mkdir -p models
cd models
```

2. Download Mistral 7B (4-bit quantized):
```bash
# Using wget
wget https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf
```

3. Update config:
   - Edit `config/config.yaml`
   - Verify model_path points to downloaded model

### 4. Twitter API Setup

1. Apply for Twitter API access:
   - Go to developer.twitter.com
   - Sign up for Basic tier (free)
   - Create a new Project and App
   - Generate API keys and tokens

2. Update configuration:
   - Edit `config/config.yaml`
   - Fill in Twitter credentials:
     ```yaml
     twitter:
       consumer_key: "your_key"
       consumer_secret: "your_secret"
       access_token: "your_token"
       access_token_secret: "your_token_secret"
     ```

### 5. Directory Setup

1. Create required directories:
```bash
mkdir -p data/backups logs
```

2. Set permissions:
```bash
chmod 755 data data/backups logs
```

### 6. Testing

1. Test database setup:
```bash
python3 -c "
import asyncio
from src.database.db import init_db
from config.config import load_config

async def test():
    config = await load_config()
    db = await init_db(config['database'])
    print('Database initialized successfully')

asyncio.run(test())
"
```

2. Test NVD collection:
```bash
python3 -c "
import asyncio
from src.sources.collector import CVECollector
from src.database.db import init_db
from config.config import load_config

async def test():
    config = await load_config()
    db = await init_db(config['database'])
    collector = CVECollector(config['nvd'], db)
    cves = await collector.collect_recent_cves()
    print(f'Collected {len(cves)} CVEs')

asyncio.run(test())
"
```

3. Test LLM:
```bash
python3 -c "
from src.llm.model import LLMGenerator
from config.config import load_config
import asyncio

async def test():
    config = await load_config()
    llm = LLMGenerator(config['llm'])
    response = llm._generate('Generate a test response about security:', max_tokens=100)
    print('LLM Response:', response)

asyncio.run(test())
"
```

### 7. Running the Bot

1. Start the bot:
```bash
python3 -m src.main
```

2. Monitor logs:
```bash
tail -f logs/bot.log
```

### 8. Maintenance

- Logs are in `logs/bot.log`
- Database is in `data/bot.db`
- Backups in `data/backups`
- Model file in `models/`

## Troubleshooting

1. If LLM fails to load:
   - Check model path in config
   - Verify model downloaded correctly
   - Check system memory usage

2. If database errors:
   - Check permissions on data directory
   - Verify SQLite installation
   - Check disk space

3. If Twitter posting fails:
   - Verify API credentials
   - Check rate limits
   - Verify network connectivity

## Contributing

[Your contribution guidelines here]

## License

[Your license here] 