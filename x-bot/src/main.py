import asyncio
import yaml
from pathlib import Path
from loguru import logger

from database.db import init_db
from sources.collector import CVECollector
from llm.model import LLMGenerator
from content.generator import ContentGenerator
from content.scheduler import PostScheduler
from utils.health import HealthMonitor

async def load_config() -> dict:
    """Load configuration from yaml file."""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
        
    with open(config_path) as f:
        return yaml.safe_load(f)

async def setup_logging(config: dict):
    """Configure logging."""
    log_config = config["logging"]
    logger.add(
        log_config["file"],
        level=log_config["level"],
        rotation=log_config["max_size"],
        retention=log_config["backup_count"]
    )

class Bot:
    def __init__(self, config: dict):
        self.config = config
        self.db = None
        self.collector = None
        self.llm = None
        self.content_generator = None
        self.scheduler = None
        self.health_monitor = HealthMonitor()

    async def setup(self):
        """Initialize all components."""
        try:
            # Initialize database
            self.db = await init_db(self.config["database"])
            logger.info("Database initialized")
            
            # Initialize CVE collector
            self.collector = CVECollector(self.config["nvd"], self.db)
            logger.info("CVE collector initialized")
            
            # Initialize LLM
            self.llm = LLMGenerator(self.config["llm"])
            logger.info("LLM initialized")
            
            # Initialize content generator
            self.content_generator = ContentGenerator(
                self.config["content"],
                self.db,
                self.collector,
                self.llm
            )
            logger.info("Content generator initialized")
            
            # Initialize scheduler
            self.scheduler = PostScheduler(
                self.config["posting"],
                self.config["twitter"],
                self.db
            )
            logger.info("Post scheduler initialized")
            
            # Start health monitoring
            asyncio.create_task(self.health_monitor.monitor_loop())
            logger.info("Health monitoring started")
            
        except Exception as e:
            logger.error(f"Error during setup: {e}")
            self.health_monitor.record_error()
            raise

    async def run(self):
        """Run the main bot loops."""
        try:
            # Start content generation loop
            asyncio.create_task(self._content_generation_loop())
            
            # Start post scheduler
            await self.scheduler.run()
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.health_monitor.record_error()
            raise
        finally:
            await self.cleanup()

    async def _content_generation_loop(self):
        """Periodically generate new content."""
        while True:
            try:
                # Record CVE check attempt
                self.health_monitor.record_cve_check()
                
                success = await self.content_generator.generate_content()
                
                # Record post attempt
                self.health_monitor.record_post_attempt(success)
                
                await asyncio.sleep(self.config["content"]["generation_interval"])
            except Exception as e:
                logger.error(f"Error in content generation: {e}")
                self.health_monitor.record_error()
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def cleanup(self):
        """Clean up resources."""
        if self.content_generator:
            await self.content_generator.close()
        if self.collector:
            await self.collector.close()
        if self.llm:
            self.llm.close()

async def main():
    try:
        # Load configuration
        config = await load_config()
        await setup_logging(config)
        
        logger.info("Starting X-Bot")
        
        # Initialize and run bot
        bot = Bot(config)
        await bot.setup()
        await bot.run()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 