from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from loguru import logger
import random

from ..database.db import Database
from ..sources.collector import CVECollector
from ..llm.model import LLMGenerator

class ContentGenerator:
    def __init__(self, content_config: dict, db: Database, collector: CVECollector, llm: LLMGenerator):
        self.config = content_config
        self.db = db
        self.collector = collector
        self.llm = llm
        
        # Track content mix
        self.last_thread_time = datetime.min
        self.daily_posts = 0
        self.daily_threads = 0

    async def _can_post_thread(self) -> bool:
        """Check if we can post a thread based on our rules."""
        now = datetime.utcnow()
        
        # Only one thread per day
        if self.daily_threads >= 1:
            return False
            
        # Must be weekday for threads
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        # At least 4 hours since last thread
        hours_since_last = (now - self.last_thread_time).total_seconds() / 3600
        if hours_since_last < 4:
            return False
            
        return True

    async def _get_post_history(self, limit: int = 100) -> List[Dict]:
        """Get recent posts for context."""
        posts = await self.db.get_recent_posts(limit)
        return [
            {
                "content": post.content,
                "timestamp": post.timestamp,
                "key_concepts": post.key_concepts
            }
            for post in posts
        ]

    async def _create_cve_thread(self, cve_data: dict) -> Optional[List[str]]:
        """Generate a thread about a CVE."""
        try:
            # Get post history for context
            history = await self._get_post_history()
            
            # Generate thread
            is_valid, posts = await self.llm.generate_cve_thread(cve_data, history)
            
            if not is_valid:
                logger.warning(f"Generated thread for {cve_data['id']} was invalid")
                return None
                
            if not posts:
                logger.warning(f"No posts generated for {cve_data['id']}")
                return None
                
            if len(posts) > self.config["max_thread_length"]:
                logger.warning(f"Thread too long for {cve_data['id']}")
                return None
                
            return posts
            
        except Exception as e:
            logger.error(f"Error creating thread for {cve_data['id']}: {e}")
            return None

    async def _estimate_technical_depth(self, content: str) -> int:
        """Estimate technical depth on 1-5 scale."""
        # Simple heuristic based on technical terms
        technical_terms = [
            "buffer overflow", "race condition", "heap", "stack",
            "kernel", "syscall", "memory corruption", "exploit",
            "vulnerability", "payload", "shellcode", "rop chain",
            "sandbox escape", "privilege escalation"
        ]
        
        content_lower = content.lower()
        term_count = sum(1 for term in technical_terms if term in content_lower)
        
        # Scale from 1-5 based on term density
        depth = min(5, max(1, 1 + (term_count // 2)))
        return depth

    async def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key technical concepts from post content."""
        technical_concepts = [
            "buffer overflow", "race condition", "heap", "stack",
            "kernel", "syscall", "memory corruption", "exploit",
            "vulnerability", "payload", "shellcode", "rop chain",
            "sandbox escape", "privilege escalation", "zero day",
            "authentication bypass", "remote code execution", "container escape",
            "side channel", "timing attack", "type confusion", "use after free"
        ]
        
        content_lower = content.lower()
        found_concepts = []
        
        # Extract direct mentions
        for concept in technical_concepts:
            if concept in content_lower:
                found_concepts.append(concept)
        
        return found_concepts

    async def _extract_prerequisites(self, content: str) -> List[str]:
        """Extract explained prerequisite concepts from parenthetical explanations."""
        # Look for explanations in parentheses
        import re
        explanations = re.findall(r'\((.*?)\)', content.lower())
        
        # Filter out non-explanations (like asides)
        prerequisites = []
        for exp in explanations:
            # Only include if it looks like a definition
            if any(word in exp for word in ["is", "are", "means", "when", "how"]):
                prerequisites.append(exp.strip())
        
        return prerequisites

    async def _store_thread(self, posts: List[str], cve_id: Optional[str] = None) -> bool:
        """Store thread posts in database."""
        try:
            thread_time = datetime.utcnow()
            
            for i, content in enumerate(posts):
                technical_depth = await self._estimate_technical_depth(content)
                key_concepts = await self._extract_key_concepts(content)
                prerequisites = await self._extract_prerequisites(content)
                
                post_data = {
                    "content": content,
                    "timestamp": thread_time,
                    "is_thread": True,
                    "thread_position": i + 1,
                    "technical_depth": technical_depth,
                    "cve_id": cve_id,
                    "key_concepts": key_concepts,
                    "prerequisites_explained": prerequisites
                }
                
                await self.db.add_post(post_data)
                
            self.last_thread_time = thread_time
            self.daily_threads += 1
            self.daily_posts += len(posts)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing thread: {e}")
            return False

    async def generate_content(self) -> bool:
        """Main content generation loop."""
        try:
            # Reset daily counters if needed
            now = datetime.utcnow()
            if now.date() > self.last_thread_time.date():
                self.daily_posts = 0
                self.daily_threads = 0
            
            # Check if we can post more today
            if self.daily_posts >= self.config["max_daily_posts"]:
                logger.info("Daily post limit reached")
                return False

            # Decide content type based on current state
            if now.weekday() < 5 and self.daily_threads == 0:  # Weekday and no thread yet
                # 70% chance of CVE thread if available
                if random.random() < 0.7:
                    return await self._generate_cve_thread()
            
            # If we didn't create a thread, try a single post
            return await self._generate_single_post()
            
        except Exception as e:
            logger.error(f"Error in content generation: {e}")
            return False

    async def _generate_single_post(self) -> bool:
        """Generate a single technical post."""
        try:
            # Choose topic from our concept pool
            concept = await self._choose_topic()
            
            # Generate the post
            history = await self._get_post_history()
            is_valid, content = await self.llm.generate_technical_post(concept, history)
            
            if not is_valid or not content:
                return False
            
            # Store the post
            post_data = {
                "content": content,
                "timestamp": datetime.utcnow(),
                "is_thread": False,
                "technical_depth": await self._estimate_technical_depth(content),
                "key_concepts": await self._extract_key_concepts(content),
                "prerequisites_explained": await self._extract_prerequisites(content)
            }
            
            await self.db.add_post(post_data)
            self.daily_posts += 1
            return True
            
        except Exception as e:
            logger.error(f"Error generating single post: {e}")
            return False

    async def _choose_topic(self) -> str:
        """Choose a topic for a single post."""
        topics = [
            "kernel exploitation",
            "reverse engineering",
            "fuzzing techniques",
            "binary analysis",
            "web security",
            "network protocols",
            "cryptography",
            "cloud security",
            "container security",
            "hardware security"
        ]
        
        # Get recent post concepts to avoid repetition
        recent_posts = await self._get_post_history(limit=20)
        recent_concepts = set()
        for post in recent_posts:
            recent_concepts.update(post.get("key_concepts", []))
        
        # Filter out recently covered topics
        available_topics = [t for t in topics if t not in recent_concepts]
        if not available_topics:
            available_topics = topics  # Reset if all topics used
            
        return random.choice(available_topics)

    async def _generate_cve_thread(self) -> bool:
        """Generate a CVE-based thread."""
        # Get unprocessed CVEs
        cves = await self.collector.process_backlog(limit=5)
        
        for cve in cves:
            # Check if we can post a thread
            if not await self._can_post_thread():
                logger.info("Cannot post thread now")
                continue
            
            # Generate thread
            posts = await self._create_cve_thread(cve)
            if not posts:
                continue
            
            # Store thread
            if await self._store_thread(posts, cve["id"]):
                logger.info(f"Successfully created thread for {cve['id']}")
                return True
        
        return False

    async def close(self):
        """Clean up resources."""
        await self.collector.close()
        self.llm.close()