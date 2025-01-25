import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.content.generator import ContentGenerator
from src.database.models import CVE, Post

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.get_recent_posts = AsyncMock(return_value=[])
    return db

@pytest.fixture
def mock_collector():
    collector = MagicMock()
    collector.process_backlog = AsyncMock(return_value=[{
        "id": "CVE-2024-0001",
        "description": "Test vulnerability",
        "cvss_score": 8.5,
        "interesting_factors": ["Novel technique"],
        "technical_writeups": ["https://example.com/writeup"],
        "published_date": datetime.utcnow()
    }])
    return collector

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate_cve_thread = AsyncMock(return_value=(True, [
        "test thread post 1",
        "test thread post 2"
    ]))
    return llm

@pytest.mark.asyncio
async def test_content_generation(mock_db, mock_collector, mock_llm):
    """Test that content generation works correctly."""
    config = {
        "max_thread_length": 7,
        "technical_depth_range": [1, 5],
        "history_context_size": 100
    }
    
    generator = ContentGenerator(config, mock_db, mock_collector, mock_llm)
    success = await generator.generate_content()
    
    assert success is True
    mock_collector.process_backlog.assert_called_once()
    mock_llm.generate_cve_thread.assert_called_once()
    assert mock_db.add_post.call_count == 2  # Two posts in the thread

@pytest.mark.asyncio
async def test_content_generation_no_cves(mock_db, mock_collector, mock_llm):
    """Test handling when no CVEs are available."""
    mock_collector.process_backlog = AsyncMock(return_value=[])
    
    config = {
        "max_thread_length": 7,
        "technical_depth_range": [1, 5],
        "history_context_size": 100
    }
    
    generator = ContentGenerator(config, mock_db, mock_collector, mock_llm)
    success = await generator.generate_content()
    
    assert success is False
    mock_collector.process_backlog.assert_called_once()
    mock_llm.generate_cve_thread.assert_not_called()
    mock_db.add_post.assert_not_called() 