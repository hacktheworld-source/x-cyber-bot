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

Use lowercase and minimal formatting. Explain technical terms briefly in parentheses when needed.

Your goal is to teach advanced concepts while keeping posts interesting and never annoying."""

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

Keep each post under 280 characters. Use lowercase. Explain technical terms briefly in parentheses when needed."""

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
- Stay under 280 characters

Use lowercase and explain technical terms briefly in parentheses when needed."""

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
5. Appropriate length

Respond with either:
VALID if the thread is good
or
INVALID: [reason] if there are issues"""

    @staticmethod
    def get_post_validation_prompt(post_content: str) -> str:
        return f"""Validate this post for technical accuracy and style:

{post_content}

Check for:
1. Technical accuracy
2. Clear explanation
3. Engaging style
4. Length (under 280 chars)

Respond with either:
VALID if the post is good
or
INVALID: [reason] if there are issues""" 