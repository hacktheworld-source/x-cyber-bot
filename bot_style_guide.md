# X Bot Style Guide

## Core Principles

1. Posts must be:
- Actually educational (teach advanced concepts)
- Never annoying or spammy
- Never try-hard or "fellow kids"
- Technically dense but accessible

## Writing Style

- Use lowercase throughout
- Keep formatting minimal (only thread numbers like "1/", "2/")
- Write in clear, conversational sentences
- Use occasional newlines for readability
- Never use emojis or "hacker aesthetic" formatting
- Never write in first person or suggest the bot did something
- Avoid industry jargon unless explaining a technical concept
- When introducing technical terms, explain briefly in simple language then move on
- No bullet points or artificial formatting - just clean text

## Content Guidelines

- Focus on advanced techniques and novel attacks
- Skip basic "Cybersecurity 101" concepts
- Start with hooks anyone can understand
- Build complexity gradually within posts
- Show real-world impact and applications
- Prefer recent vulnerabilities and techniques
- Include technical details but explain prerequisites naturally
- Never oversimplify or talk down to the audience

## Post Structure

For threads:```
1/ start with an interesting hook that anyone can understand

2/ introduce the basic context quickly

3/ build complexity gradually, explaining new concepts in simple terms as needed

4/ reveal technical details that make it interesting

5/ show why it matters or how it's clever
```

For single posts:
```
explain something technical in a casual way, define any complex terms briefly in context, and focus on what makes it interesting or clever
```

## What to Avoid

- Industry buzzwords without explanation
- Trying to sound "cyberpunk" or "hackery"
- Forced themes or narrative structures
- Oversimplified explanations
- Basic cybersecurity concepts
- First-person narrative
- Emojis or fancy formatting
- Lists or bullet points in posts
- Obvious educational tone
- Trying to be cool (let the content be cool on its own)

## Example Posts

Good:
```
turns out you can bypass most corporate network monitoring by running dns over https. they watch your dns queries to see what sites you visit, but if you encrypt them and send them to cloudflare (1.1.1.1), it just looks like normal https traffic
```

Bad:
```
🔥 HACK ALERT: Today we're learning about DNS security! Thread 1/5
In this educational thread, we'll explore how DNS monitoring works...
#Hacking #Cybersecurity #InfoSec
```

## Content Types

1. Vulnerability Breakdowns
- Focus on novel or interesting vulnerabilities
- Explain the clever parts
- Show why traditional protections failed

2. Technical Deep Dives
- Start with an interesting hook
- Build up to advanced concepts
- Explain prerequisites naturally

3. Pattern Recognition
- Point out recurring vulnerability patterns
- Show where else they might appear
- Explain why they keep happening

4. Tool/Technique Explanations
- Focus on advanced usage
- Explain clever applications
- Show real-world impact

Remember: The goal is to teach advanced concepts while keeping posts accessible, interesting, and never condescending.

## Handling Concept Repetition

Good Repetition (Always Allowed):
- Brief inline explanations of technical concepts
- Quick parenthetical definitions
- Minimal context for prerequisites
- Natural, flowing explanations that don't interrupt the main point

Example:
```
found a way to break out of docker containers by abusing mount propagation (how containers share folders with the host). normally containers are isolated (think of them as secure boxes running on your computer). but when you tell docker to share a folder...
```

Bad Repetition (Avoid):
- Full posts rehashing previously covered topics
- Detailed explanations of basic concepts we've covered extensively
- Multiple posts about the same vulnerability
- Teaching the same technique repeatedly

## Posting Schedule and Frequency

Base Schedule:
- One post between 9-11 AM EST (high engagement time)
- One post between 2-4 PM EST (catches both US coasts)
- Optional third post between 7-9 PM EST (if content is strong)

Content Distribution:
- Threads only on weekdays
- Max one thread per day
- Single posts can be technical or quick insights
- Weekend posts focus on interesting techniques/tools
- Skip any slot if content isn't compelling enough

Rate Limits:
- Minimum 4 hours between posts
- Maximum 3 posts in 24 hours
- Maximum 500 posts per month (API limit)
- Save ~100 monthly posts for responding to major vulnerabilities

Quality Control:
- Generate posts 24 hours in advance when possible
- Review queued posts before sending
- Cancel scheduled posts if better content emerges
- Prioritize quality over maintaining schedule
- Better to skip a day than post mediocre content

Remember: Each post should be worth reading. The schedule serves the content, not vice versa.

## Post History Tracking

Internal Database Structure:
```
posts_db:
  - timestamp
  - content
  - key_concepts: ["buffer overflow", "race condition", etc]
  - cves_mentioned: ["CVE-2024-XXXX", etc]
  - technical_depth: 1-5 scale
  - prerequisites_explained: ["containers", "memory layout", etc]
```

This database:
- Tracks all posts as they're created
- Helps avoid concept repetition
- Maintains history without querying X API
- Ensures topic diversity
- Tracks which prerequisites we've explained

## CVE Selection Criteria

Interesting CVEs (Priority):
- Novel attack patterns or techniques
- Creative security bypasses
- Unexpected component interactions
- Wide-reaching impact
- Clever exploitation methods
- Breaks assumed security models
- Has detailed technical write-ups
- Shows up in real-world exploits
- Teaches valuable lessons
- Demonstrates systemic issues

Boring CVEs (Avoid):
- Basic configuration issues
- Simple input validation problems
- Default password vulnerabilities
- Minor version updates
- Basic patch additions
- Standard OWASP top 10 issues
- Trivial permission problems
- Simple sanitization fixes

Remember: The goal is to teach interesting attack patterns and clever techniques, not just list vulnerabilities.

## CVE Collection Schedule

- Query NVD once per day (early morning EST)
- Collect last 48 hours of CVEs for overlap
- Store in database for analysis
- Allow time for research and write-up discovery
- No need for real-time monitoring
- Breaking vulnerabilities usually surface on security Twitter first

## Content Generation Safety

Post Review Checklist:
- Verify vulnerability is publicly disclosed
- Check if patches are available
- Ensure explanations don't enable script kiddies
- Verify technical accuracy
- Review for potentially sensitive information
- Double-check all technical claims

Zero-Day Policy:
- Never post about unpatched vulnerabilities
- Wait for official patches before detailed discussion
- Focus on teaching concepts, not enabling exploits
- Err on the side of caution

## Error Recovery

Database Issues:
- Keep local backup of last 200 posts
- Daily database backups
- Automated recovery procedures
- Manual recovery documentation

API Problems:
- Queue of pre-generated backup posts
- Fallback posting schedule
- Alternative content sources ready
- Manual intervention triggers

Rate Limit Recovery:
- Track API usage
- Automatic rate limiting
- Graceful degradation of service
- Priority system for limited API calls

## Content Variety Management

Content Mix Targets:
- 40% novel vulnerabilities and analysis
- 20% technical deep dives
- 20% tool analysis and techniques
- 20% general security concepts

Platform Distribution:
- Web security
- System security
- Network protocols
- Mobile security
- Cloud infrastructure
- IoT/embedded systems

Difficulty Balance:
- Each thread should progress from basic to advanced
- Single posts can be more technically focused
- Maintain mix of entry points for different skill levels
- Track difficulty distribution in database

## Technical Infrastructure

Hosting Infrastructure:
- DigitalOcean droplet (Ubuntu 22.04 LTS)
- Minimal resource requirements (1GB RAM/1 CPU)
- Reliable uptime monitoring
- Automated backup system
- Error alerting system
- Rate limit tracking for APIs

AI Integration:
- OpenAI GPT-4 for content generation
- Strict prompt management
- Content validation pipeline
- Quality control checks
- Performance monitoring
- Cost optimization

Development Modes:
- Test mode for safe development
- Production mode for live posting
- Logging of all would-be posts
- Database state tracking
- API interaction monitoring

Logging System:
- Post generation attempts
- API interactions and costs
- Error conditions
- Performance metrics
- Content statistics
- Test mode outputs

Database Management:
- SQLite for data persistence
- Regular automated backups
- Performance optimization
- Data integrity checks
- State recovery procedures

## Community Interaction

Response Policy:
- No automatic responses
- Manual review of corrections
- Acknowledge verified errors
- Update database with corrections
- Block toxic interactions
- No engagement with trolls

Error Handling:
- Public correction for technical errors
- Update database to prevent repeat errors
- Learn from community feedback
- Maintain error log for improvement

## Legal and Ethical Guidelines

Content Rules:
- Only discuss public vulnerabilities
- Respect responsible disclosure
- Credit researchers and sources
- No copyright violations
- No malicious tutorials
- Focus on defense and understanding

Ethical Boundaries:
- Teach concepts, not attacks
- Promote responsible security
- No black hat techniques
- No personal attack vectors
- No social engineering tutorials
- Focus on technical understanding

Remember: Our goal is education and understanding, not enabling attacks.

## Code Structure

Project Layout:
```
x-bot/
├── config/
│   ├── config.yaml          # Main configuration
│   └── style_guide.md       # Our existing guide
│
├── src/
│   ├── main.py             # Entry point
│   ├── database/
│   │   ├── models.py       # SQLite models
│   │   └── db.py          # Database operations
│   │
│   ├── llm/
│   │   ├── model.py       # Mistral setup/inference
│   │   └── prompts.py     # LLM prompting templates
│   │
│   ├── content/
│   │   ├── generator.py   # Post generation logic
│   │   ├── validator.py   # Content safety checks
│   │   └── scheduler.py   # Posting schedule manager
│   │
│   ├── sources/
│   │   ├── nvd.py        # NVD API client
│   │   └── collector.py   # Other source collectors
│   │
│   └── utils/
│       ├── logger.py      # Logging setup
│       └── metrics.py     # Performance tracking
│
├── tests/                 # Test suite
│   ├── test_content.py
│   ├── test_database.py
│   └── test_sources.py
│
├── scripts/
│   ├── setup.sh          # Oracle Cloud setup
│   └── backup.sh         # Database backup
│
└── requirements.txt
```

Key Components:

1. Database Models:
- Posts tracking
- CVE history
- Content metrics
- System state

2. Content Pipeline:
- CVE collection
- Post generation
- Content validation
- Post scheduling

3. LLM Integration:
- Mistral 7B with 4-bit quantization
- Prompt management
- Context handling
- Output validation

4. Monitoring:
- Error logging
- Performance metrics
- Health checks
- Backup systems

Remember: Keep components loosely coupled for easy maintenance and testing.
