from datetime import datetime
from typing import List, Optional
from loguru import logger

from .nvd import NVDClient
from ..database.db import Database

class CVECollector:
    def __init__(self, nvd_config: dict, db: Database):
        self.nvd_client = NVDClient(nvd_config)
        self.db = db

    async def close(self):
        """Clean up resources."""
        await self.nvd_client.close()

    def _is_interesting_cve(self, cve_data: dict) -> bool:
        """Determine if a CVE is interesting enough to post about."""
        
        # Must have some technical writeups
        if not cve_data["technical_writeups"]:
            return False
            
        # Should have identified interesting factors
        if not cve_data["interesting_factors"]:
            return False
            
        # If it has a CVSS score, it should be significant
        if cve_data["cvss_score"] is not None and cve_data["cvss_score"] < 7.0:
            return False
            
        # Check for indicators of boring vulnerabilities
        boring_patterns = [
            "default password",
            "default credential",
            "missing authentication",
            "cross-site scripting",
            "sql injection",
            "weak password",
            "information disclosure",
            "denial of service"
        ]
        
        desc_lower = cve_data["description"].lower()
        if any(pattern in desc_lower for pattern in boring_patterns):
            return False
            
        # Check for indicators of interesting vulnerabilities
        interesting_patterns = [
            "novel",
            "unique",
            "sophisticated",
            "chain",
            "chained",
            "complex",
            "creative",
            "unusual",
            "unexpected"
        ]
        
        # Bonus points for interesting descriptions
        if any(pattern in desc_lower for pattern in interesting_patterns):
            return True
            
        # If it has multiple interesting factors, it's probably worth posting
        if len(cve_data["interesting_factors"]) >= 2:
            return True
            
        # If it has a high CVSS score and technical writeups, might be interesting
        if cve_data["cvss_score"] is not None and cve_data["cvss_score"] >= 9.0:
            return True
            
        # Default to False if none of the above criteria are met
        return False

    async def collect_recent_cves(self) -> List[dict]:
        """Collect and filter recent CVEs."""
        logger.info("Starting CVE collection")
        
        # Get recent CVEs from NVD
        cves = await self.nvd_client.get_recent_cves()
        logger.info(f"Retrieved {len(cves)} CVEs from NVD")
        
        # Filter for interesting ones
        interesting_cves = []
        for cve in cves:
            if self._is_interesting_cve(cve):
                interesting_cves.append(cve)
                
        logger.info(f"Found {len(interesting_cves)} interesting CVEs")
        
        # Store in database
        stored_cves = []
        for cve in interesting_cves:
            try:
                stored = await self.db.add_cve(cve)
                stored_cves.append(stored)
            except Exception as e:
                logger.error(f"Error storing CVE {cve['id']}: {e}")
                continue
                
        return stored_cves

    async def get_cve_with_writeups(self, cve_id: str) -> Optional[dict]:
        """Get detailed CVE information including technical writeups."""
        try:
            # Get basic CVE details
            cve_data = await self.nvd_client.get_cve_details(cve_id)
            if not cve_data:
                return None
                
            # Could expand this to fetch and parse technical writeups
            # For now, we just return the basic data
            return cve_data
            
        except Exception as e:
            logger.error(f"Error fetching CVE {cve_id} details: {e}")
            return None

    async def process_backlog(self, limit: int = 10) -> List[dict]:
        """Process unprocessed CVEs from the database."""
        try:
            # Get unprocessed CVEs
            unprocessed = await self.db.get_unprocessed_cves()
            logger.info(f"Found {len(unprocessed)} unprocessed CVEs")
            
            # Limit the number we process at once
            unprocessed = unprocessed[:limit]
            
            processed = []
            for cve in unprocessed:
                # Get additional details if needed
                details = await self.get_cve_with_writeups(cve.id)
                if details:
                    processed.append(details)
                    await self.db.mark_cve_processed(cve.id)
                    
            return processed
            
        except Exception as e:
            logger.error(f"Error processing CVE backlog: {e}")
            return [] 