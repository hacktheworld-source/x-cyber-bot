#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import argparse
import yaml
from loguru import logger
from datetime import datetime, timedelta

from src.database.db import init_db
from src.sources.collector import CVECollector
from src.llm.model import LLMGenerator
from src.content.generator import ContentGenerator
from src.content.scheduler import PostScheduler

async def load_config() -> dict:
    """Load configuration from yaml file."""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
        
    with open(config_path) as f:
        return yaml.safe_load(f)

async def test_cve_collection(config: dict):
    """Test CVE collection and processing."""
    db = await init_db(config["database"])
    collector = CVECollector(config["nvd"], db)
    
    print("Testing CVE collection...")
    cves = await collector.collect_recent_cves()
    print(f"Collected {len(cves)} CVEs")
    
    if cves:
        print("\nExample CVE:")
        cve = cves[0]
        # Handle both dict and CVE model objects
        if hasattr(cve, 'id'):
            # It's a CVE model object
            print(f"ID: {cve.id}")
            print(f"Description: {cve.description}")
            print(f"CVSS Score: {cve.cvss_score}")
            print(f"Interesting Factors: {', '.join(cve.interesting_factors)}")
        else:
            # It's a dictionary
            print(f"ID: {cve['id']}")
            print(f"Description: {cve['description']}")
            print(f"CVSS Score: {cve['cvss_score']}")
            print(f"Interesting Factors: {', '.join(cve['interesting_factors'])}")
    
    await collector.close()

async def test_content_generation(config: dict):
    """Test content generation without posting."""
    db = await init_db(config["database"])
    collector = CVECollector(config["nvd"], db)
    llm = LLMGenerator(config["ai"])
    generator = ContentGenerator(config["content"], db, collector, llm)
    
    print("Testing content generation...")
    success = await generator.generate_content()
    
    if success:
        print("\nRecent generated posts:")
        posts = await db.get_recent_posts(5)
        for post in posts:
            print(f"\nPost {post.id}:")
            print(f"Content: {post.content}")
            print(f"Technical Depth: {post.technical_depth}")
            print(f"Is Thread: {post.is_thread}")
            if post.is_thread:
                print(f"Thread Position: {post.thread_position}")
    
    await generator.close()

async def test_scheduler(config: dict):
    """Test post scheduling without actual posting."""
    db = await init_db(config["database"])
    scheduler = PostScheduler(config["posting"], config["twitter"], db)
    
    print("Testing scheduler...")
    print("Will log would-be posts instead of posting to X")
    
    try:
        # Run scheduler for 30 seconds
        print("Running scheduler for 30 seconds...")
        scheduler_task = asyncio.create_task(scheduler.run())
        await asyncio.sleep(30)
        scheduler_task.cancel()
        
    except asyncio.CancelledError:
        print("Scheduler test complete")

async def test_single_post(config: dict):
    """Test generating a single technical post."""
    db = await init_db(config["database"])
    collector = CVECollector(config["nvd"], db)
    llm = LLMGenerator(config["ai"])
    generator = ContentGenerator(config["content"], db, collector, llm)
    
    print("Testing single post generation...")
    success = await generator._generate_single_post()
    
    if success:
        posts = await db.get_recent_posts(1)
        if posts:
            post = posts[0]
            print("\nGenerated Post:")
            print(f"Content: {post.content}")
            print(f"Character Count: {len(post.content)}")
            print(f"Technical Depth: {post.technical_depth}")
            print(f"Key Concepts: {', '.join(post.key_concepts)}")
            print(f"Prerequisites: {', '.join(post.prerequisites_explained)}")
    
    await generator.close()

async def test_character_limits(config: dict):
    """Test character limit validation and truncation."""
    db = await init_db(config["database"])
    scheduler = PostScheduler(config["posting"], config["twitter"], db)
    
    test_posts = [
        "Short post that should be fine.",
        "x" * 280,  # Exactly 280 chars
        "x" * 300,  # Over limit
        "this is a post with an explanation (which is quite long and should be handled carefully) that might get truncated",
        "multiple (explanations) in (one post) to test (truncation logic) properly"
    ]
    
    print("Testing character limit handling...")
    for post in test_posts:
        print(f"\nOriginal ({len(post)} chars):")
        print(post)
        
        truncated = scheduler._truncate_if_needed(post)
        print(f"After truncation ({len(truncated)} chars):")
        print(truncated)
        print(f"Valid: {scheduler._validate_post_length(truncated)}")

async def test_database(config: dict):
    """Test database operations."""
    db = await init_db(config["database"])
    
    print("Testing database operations...")
    
    # Test post retrieval
    posts = await db.get_recent_posts(5)
    print(f"\nFound {len(posts)} recent posts")
    
    # Test CVE retrieval
    cves = await db.get_unprocessed_cves()
    print(f"Found {len(cves)} unprocessed CVEs")
    
    # Test time window queries
    now = datetime.utcnow()
    window_posts = await db.get_posts_in_timeframe(
        now - timedelta(hours=24),
        now
    )
    print(f"Found {len(window_posts)} posts in last 24 hours")

async def main():
    parser = argparse.ArgumentParser(description="Test X-Bot functionality")
    parser.add_argument("command", 
                       choices=["cves", "content", "scheduler", 
                               "single", "limits", "database"],
                       help="Which component to test")
    args = parser.parse_args()
    
    config = await load_config()
    
    # Ensure we're in test mode
    if not config["twitter"]["testing"]["enabled"]:
        print("WARNING: Test mode not enabled in config!")
        return
    
    if args.command == "cves":
        await test_cve_collection(config)
    elif args.command == "content":
        await test_content_generation(config)
    elif args.command == "scheduler":
        await test_scheduler(config)
    elif args.command == "single":
        await test_single_post(config)
    elif args.command == "limits":
        await test_character_limits(config)
    elif args.command == "database":
        await test_database(config)

if __name__ == "__main__":
    asyncio.run(main()) 