from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import asyncio
from loguru import logger

import tweepy
from ..database.db import Database

class PostScheduler:
    def __init__(self, posting_config: dict, twitter_config: dict, db: Database):
        self.config = posting_config
        self.db = db
        self.testing = twitter_config.get("testing", {})
        self.is_test_mode = self.testing.get("enabled", False)
        self.log_posts = self.testing.get("log_posts", True)
        
        if not self.is_test_mode:
            # Initialize Twitter client with credentials from config
            self.client = tweepy.Client(
                consumer_key=twitter_config["consumer_key"],
                consumer_secret=twitter_config["consumer_secret"],
                access_token=twitter_config["access_token"],
                access_token_secret=twitter_config["access_token_secret"]
            )
            logger.info("Twitter client initialized")
        else:
            logger.info("Running in TEST MODE - no posts will be made to X")
            self.client = None
        
        # Parse posting windows
        self.posting_windows = [
            (
                datetime.strptime(window["start"], "%H:%M").time(),
                datetime.strptime(window["end"], "%H:%M").time()
            )
            for window in posting_config["time_windows"]
        ]

    def _in_posting_window(self) -> bool:
        """Check if current time is in a posting window."""
        now = datetime.utcnow().time()
        return any(
            start <= now <= end
            for start, end in self.posting_windows
        )

    async def _get_next_post(self) -> Optional[Tuple[List[dict], datetime]]:
        """Get next scheduled post or thread."""
        try:
            # Get posts scheduled for next window
            now = datetime.utcnow()
            window_end = now + timedelta(hours=4)
            
            posts = await self.db.get_posts_in_timeframe(now, window_end)
            if not posts:
                return None
                
            # Group into threads if needed
            if posts[0].is_thread:
                thread_posts = [p for p in posts if p.thread_position is not None]
                thread_posts.sort(key=lambda p: p.thread_position)
                return thread_posts, thread_posts[0].scheduled_time
            else:
                return [posts[0]], posts[0].scheduled_time
                
        except Exception as e:
            logger.error(f"Error getting next post: {e}")
            return None

    def _validate_post_length(self, content: str) -> bool:
        """Check if post content is within X's character limit."""
        return len(content) <= 280

    def _truncate_if_needed(self, content: str) -> str:
        """Truncate post content if it exceeds the limit."""
        if len(content) <= 280:
            return content
            
        # Try to find a good breaking point
        truncated = content[:277] + "..."
        
        # If we cut in the middle of a parenthetical explanation,
        # try to find the last complete explanation
        if truncated.count("(") != truncated.count(")"):
            last_open = truncated.rfind("(")
            last_close = truncated.rfind(")")
            if last_open > last_close:
                # Cut before the incomplete explanation
                truncated = content[:last_open].strip()
                if len(truncated) > 277:
                    truncated = truncated[:277] + "..."
                    
        return truncated

    async def _post_thread(self, posts: List[dict]) -> bool:
        """Post a thread to Twitter."""
        try:
            if self.is_test_mode:
                # Log instead of posting
                logger.info("TEST MODE - Would have posted thread:")
                for i, post in enumerate(posts, 1):
                    logger.info(f"Post {i}: {post.content}")
                return True

            previous_id = None
            
            for post in posts:
                try:
                    content = self._truncate_if_needed(post.content)
                    
                    if previous_id:
                        response = self.client.create_tweet(
                            text=content,
                            in_reply_to_tweet_id=previous_id
                        )
                    else:
                        response = self.client.create_tweet(
                            text=content
                        )
                        
                    previous_id = response.data['id']
                    await self.db.mark_post_posted(post.id, str(previous_id))
                    
                    # Rate limit compliance
                    await asyncio.sleep(1)
                    
                except tweepy.TweepError as e:
                    logger.error(f"Error posting to Twitter: {e}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error in thread posting: {e}")
            return False

    async def run(self):
        """Main scheduling loop."""
        while True:
            try:
                # Check if we're in a posting window
                if not self._in_posting_window():
                    await asyncio.sleep(300)  # Check every 5 minutes
                    continue
                
                # Get next scheduled post
                next_posts = await self._get_next_post()
                if not next_posts:
                    await asyncio.sleep(300)
                    continue
                
                posts, scheduled_time = next_posts
                
                # Wait until scheduled time
                now = datetime.utcnow()
                if scheduled_time > now:
                    delay = (scheduled_time - now).total_seconds()
                    await asyncio.sleep(delay)
                
                # Post the content
                success = await self._post_thread(posts)
                if not success:
                    logger.error("Failed to post content")
                
                # Wait before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error 