from typing import List, Dict

class Prompts:
    @staticmethod
    def get_system_prompt() -> str:
        return """You are a highly technical X/Twitter bot that posts about hacking, security vulnerabilities, and advanced technical concepts.

Your posts should be:
- Technical but accessible
- Educational without being condescending
- Focused on interesting/novel aspects
- Written in a casual, engaging style
- Free of emojis or "hacker aesthetic"
- STRICTLY under 280 characters per post

Use lowercase and minimal formatting. Explain technical terms briefly in parentheses when needed.

Your goal is to teach advanced concepts while keeping posts interesting and never annoying.

IMPORTANT: Each post MUST be under 280 characters. This is a hard limit that cannot be exceeded."""

    @staticmethod
    def get_cve_thread_prompt(cve_data: dict, recent_posts: List[dict]) -> str:
        # Format recent posts for context
        post_history = "\n".join([
            f"- {post['content']}" for post in recent_posts[:5]
        ])
        
        # Format technical writeups
        writeups = "\n".join([
            f"- {url}" for url in cve_data["technical_writeups"]
        ])
        
        return f"""Generate a thread about this vulnerability:

CVE ID: {cve_data['id']}
Description: {cve_data['description']}
Technical Writeups:
{writeups}
Interesting Factors: {', '.join(cve_data['interesting_factors'])}

Recent post history for context:
{post_history}

Create a thread that:
1. Starts with an engaging hook about what makes this interesting
2. Explains the vulnerability in simple terms
3. Dives into the technical details
4. Shows why it's clever or significant
5. Teaches the underlying concepts

Format as:
1/ [first post]
2/ [second post]
etc.

CRITICAL RULES:
- Each post MUST be under 280 characters
- Use lowercase throughout
- Explain technical terms briefly in parentheses
- No emojis or special formatting
- Keep explanations concise but clear
- If you can't fit an explanation in 280 chars, split it across posts

Example format and length:
1/ found a clever way to break out of docker containers by abusing mount propagation (how containers share folders with the host)
2/ normally containers are isolated (think secure boxes running on your computer). but when you tell docker to share a folder...

Remember: 280 characters is a HARD LIMIT per post. The bot will reject any post longer than this."""

    @staticmethod
    def get_technical_post_prompt(concept: str, recent_posts: List[dict]) -> str:
        post_history = "\n".join([
            f"- {post['content']}" for post in recent_posts[:5]
        ])
        
        return f"""Generate a single technical post about: {concept}

Recent post history for context:
{post_history}

The post should:
- Be technical but accessible
- Explain a non-obvious aspect
- Teach something interesting
- Use simple language for complex ideas
- MUST be under 280 characters total

Example format and length:
"turns out you can bypass most corporate network monitoring by running dns over https. they watch your dns queries to see what sites you visit, but if you encrypt them and send them to cloudflare (1.1.1.1), it just looks like normal https traffic"

Remember:
- 280 characters is a HARD LIMIT
- Use lowercase
- Explain technical terms briefly in parentheses
- No emojis or special formatting
- One complete thought per post"""

    @staticmethod
    def get_thread_validation_prompt(thread_content: List[str]) -> str:
        thread = "\n".join([
            f"{i+1}/ {post}" for i, post in enumerate(thread_content)
        ])
        
        return f"""Validate this thread for technical accuracy and style:

{thread}

Check for:
1. Technical accuracy
2. Proper progression of concepts
3. Clear explanations
4. Engaging style
5. Character limit (MUST be under 280 per post)

Respond with either:
VALID if the thread is good
or
INVALID: [reason] if there are issues

If ANY post is over 280 characters, respond with:
INVALID: Post [number] exceeds character limit"""

    @staticmethod
    def get_post_validation_prompt(post_content: str) -> str:
        return f"""Validate this post for technical accuracy and style:

{post_content}

Check for:
1. Technical accuracy
2. Clear explanation
3. Engaging style
4. Character limit (MUST be under 280)

Respond with either:
VALID if the post is good
or
INVALID: [reason] if there are issues

If the post is over 280 characters, respond with:
INVALID: Exceeds character limit""" 