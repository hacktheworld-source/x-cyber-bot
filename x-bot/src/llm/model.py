import os
from typing import List, Optional, Tuple
from pathlib import Path
from loguru import logger
from openai import AsyncOpenAI
import logging

from .prompts import Prompts

logger = logging.getLogger(__name__)

class LLMGenerator:
    def __init__(self, config: dict):
        self.client = AsyncOpenAI(api_key=config["api_key"])
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        self.prompts = Prompts()

    async def _generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text with the OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return ""

    async def generate_cve_thread(
        self,
        cve_data: dict,
        recent_posts: List[dict]
    ) -> Tuple[bool, List[str]]:
        """Generate a thread about a CVE."""
        # Get the full prompt
        system_prompt = self.prompts.get_system_prompt()
        thread_prompt = self.prompts.get_cve_thread_prompt(cve_data, recent_posts)
        full_prompt = f"{system_prompt}\n\n{thread_prompt}"
        
        # Generate the thread
        response = await self._generate(full_prompt, max_tokens=1000)
        if not response:
            return False, []
            
        # Split into individual posts
        try:
            posts = []
            for line in response.split("\n"):
                if line.strip() and "/" in line:
                    # Extract post content after the number/
                    post_content = line.split("/", 1)[1].strip()
                    if post_content:
                        posts.append(post_content)
            
            # Validate the thread
            is_valid = await self.validate_thread(posts)
            return is_valid, posts
            
        except Exception as e:
            logger.error(f"Error processing thread: {e}")
            return False, []

    async def generate_technical_post(
        self,
        concept: str,
        recent_posts: List[dict]
    ) -> Tuple[bool, str]:
        """Generate a single technical post."""
        system_prompt = self.prompts.get_system_prompt()
        post_prompt = self.prompts.get_technical_post_prompt(concept, recent_posts)
        full_prompt = f"{system_prompt}\n\n{post_prompt}"
        
        response = await self._generate(full_prompt, max_tokens=300)
        if not response:
            return False, ""
            
        # Validate the post
        is_valid = await self.validate_post(response)
        return is_valid, response

    async def validate_thread(self, posts: List[str]) -> bool:
        """Validate a thread for technical accuracy and style."""
        validation_prompt = self.prompts.get_thread_validation_prompt(posts)
        response = await self._generate(validation_prompt, max_tokens=100)
        
        return response.strip().startswith("VALID")

    async def validate_post(self, post_content: str) -> bool:
        """Validate a single post."""
        validation_prompt = self.prompts.get_post_validation_prompt(post_content)
        response = await self._generate(validation_prompt, max_tokens=100)
        
        return response.strip().startswith("VALID")

    def close(self):
        """Clean up resources."""
        del self.client 