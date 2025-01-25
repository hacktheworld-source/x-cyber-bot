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
        
        # Set up Twitter client
        auth = tweepy.OAuthHandler(
            twitter_config["consumer_key"],
            twitter_config["consumer_secret"]
        )
        auth.set_access_token(
            twitter_config["access_token"],
            twitter_config["access_token_secret"]
        )
        self.twitter = tweepy.API(auth)
        
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

    async def _post_thread(self, posts: List[dict]) -> bool:
        """Post a thread to Twitter."""
        try:
            previous_id = None
            
            for post in posts:
                try:
                    if previous_id:
                        response = self.twitter.update_status(
                            status=post.content,
                            in_reply_to_status_id=previous_id
                        )
                    else:
                        response = self.twitter.update_status(
                            status=post.content
                        )
                        
                    previous_id = response.id
                    await self.db.mark_post_posted(post.id, str(response.id))
                    
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