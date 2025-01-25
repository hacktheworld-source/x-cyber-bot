from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from loguru import logger

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

    async def _store_thread(self, posts: List[str], cve_id: Optional[str] = None) -> bool:
        """Store thread posts in database."""
        try:
            thread_time = datetime.utcnow()
            
            for i, content in enumerate(posts):
                technical_depth = await self._estimate_technical_depth(content)
                
                post_data = {
                    "content": content,
                    "timestamp": thread_time,
                    "is_thread": True,
                    "thread_position": i + 1,
                    "technical_depth": technical_depth,
                    "cve_id": cve_id,
                    "key_concepts": [],  # To be implemented
                    "prerequisites_explained": []  # To be implemented
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
            
            logger.info("No suitable content generated")
            return False
            
        except Exception as e:
            logger.error(f"Error in content generation: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        await self.collector.close()
        self.llm.close() 