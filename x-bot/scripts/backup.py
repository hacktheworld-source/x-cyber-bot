#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
import yaml
from pathlib import Path
import logging

def load_config() -> dict:
    """Load configuration from yaml file."""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
        
    with open(config_path) as f:
        return yaml.safe_load(f)

def backup_database(config: dict):
    """Create a backup of the SQLite database."""
    db_path = Path(config["database"]["path"])
    backup_dir = Path(config["database"]["backup_dir"])
    
    # Ensure backup directory exists
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"bot_db_backup_{timestamp}.db"
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        logging.info(f"Database backed up to {backup_path}")
        
        # Clean up old backups (keep last 7 days)
        cleanup_old_backups(backup_dir)
        
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        raise

def cleanup_old_backups(backup_dir: Path, keep_days: int = 7):
    """Remove backups older than specified days."""
    now = datetime.utcnow()
    
    for backup_file in backup_dir.glob("bot_db_backup_*.db"):
        try:
            # Get file creation time
            file_time = datetime.fromtimestamp(os.path.getctime(backup_file))
            
            # Remove if older than keep_days
            if (now - file_time).days > keep_days:
                backup_file.unlink()
                logging.info(f"Removed old backup: {backup_file}")
                
        except Exception as e:
            logging.warning(f"Error processing backup file {backup_file}: {e}")

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        config = load_config()
        backup_database(config)
        logging.info("Backup completed successfully")
        
    except Exception as e:
        logging.error(f"Backup script failed: {e}")
        exit(1)

if __name__ == "__main__":
    main() 