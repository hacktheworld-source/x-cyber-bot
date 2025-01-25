import os
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, and_

from .models import Base, CVE, Post

class Database:
    def __init__(self, database_path: str):
        # Ensure directory exists
        db_dir = os.path.dirname(database_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # Create async engine
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{database_path}",
            echo=False
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_recent_posts(self, limit: int = 100) -> List[Post]:
        async with self.async_session() as session:
            result = await session.execute(
                select(Post)
                .order_by(Post.timestamp.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_unprocessed_cves(self) -> List[CVE]:
        async with self.async_session() as session:
            result = await session.execute(
                select(CVE)
                .where(CVE.processed == False)
                .order_by(CVE.published_date.desc())
            )
            return list(result.scalars().all())

    async def add_cve(self, cve_data: dict) -> CVE:
        async with self.async_session() as session:
            cve = CVE(**cve_data)
            session.add(cve)
            await session.commit()
            return cve

    async def add_post(self, post_data: dict) -> Post:
        async with self.async_session() as session:
            post = Post(**post_data)
            session.add(post)
            await session.commit()
            return post

    async def get_posts_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Post]:
        async with self.async_session() as session:
            result = await session.execute(
                select(Post)
                .where(
                    and_(
                        Post.timestamp >= start_time,
                        Post.timestamp <= end_time
                    )
                )
            )
            return list(result.scalars().all())

    async def mark_cve_processed(self, cve_id: str):
        async with self.async_session() as session:
            cve = await session.get(CVE, cve_id)
            if cve:
                cve.processed = True
                await session.commit()

    async def mark_post_posted(self, post_id: int, x_post_id: str):
        async with self.async_session() as session:
            post = await session.get(Post, post_id)
            if post:
                post.posted = True
                post.post_id = x_post_id
                await session.commit()

    async def get_concept_frequency(self, days: int = 30) -> dict:
        """Get frequency of concepts discussed in recent posts."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with self.async_session() as session:
            result = await session.execute(
                select(Post)
                .where(Post.timestamp >= cutoff)
            )
            posts = result.scalars().all()
            
            concept_count = {}
            for post in posts:
                for concept in post.key_concepts:
                    concept_count[concept] = concept_count.get(concept, 0) + 1
            
            return concept_count

async def init_db(config: dict) -> Database:
    """Initialize database from config."""
    db = Database(config["path"])
    await db.init_db()
    return db 