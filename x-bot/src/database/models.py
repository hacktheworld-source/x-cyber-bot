from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class CVE(Base):
    __tablename__ = "cves"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)  # CVE-YYYY-NNNNN
    published_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    references: Mapped[List[str]] = mapped_column(JSON)  # List of reference URLs
    cvss_score: Mapped[float] = mapped_column(Integer, nullable=True)
    technical_writeups: Mapped[List[str]] = mapped_column(JSON)  # List of writeup URLs
    interesting_factors: Mapped[List[str]] = mapped_column(JSON)  # Why we found it interesting
    processed: Mapped[bool] = mapped_column(default=False)  # Whether we've posted about it
    
    posts = relationship("Post", back_populates="cve")

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    post_id: Mapped[str] = mapped_column(String, nullable=True)  # X/Twitter post ID
    is_thread: Mapped[bool] = mapped_column(default=False)
    thread_position: Mapped[int] = mapped_column(Integer, nullable=True)  # Position in thread if part of one
    technical_depth: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 scale
    
    # Relationships
    cve_id: Mapped[str] = mapped_column(ForeignKey("cves.id"), nullable=True)
    cve = relationship("CVE", back_populates="posts")
    
    # Metadata for tracking
    key_concepts: Mapped[List[str]] = mapped_column(JSON)  # Technical concepts covered
    prerequisites_explained: Mapped[List[str]] = mapped_column(JSON)  # Concepts we explained
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    posted: Mapped[bool] = mapped_column(default=False)
    
    def __repr__(self):
        return f"<Post(id={self.id}, timestamp={self.timestamp}, is_thread={self.is_thread})>" 