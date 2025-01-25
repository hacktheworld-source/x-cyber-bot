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
                
            # Enhance with writeup information
            await self._enhance_writeup_info(cve_data)
            return cve_data
            
        except Exception as e:
            logger.error(f"Error fetching CVE {cve_id} details: {e}")
            return None

    async def _enhance_writeup_info(self, cve_data: dict):
        """Enhance CVE data with additional writeup information."""
        writeups = cve_data["technical_writeups"]
        enhanced_writeups = []
        
        for url in writeups:
            try:
                writeup_info = {
                    "url": url,
                    "source": self._classify_writeup_source(url),
                    "quality": await self._estimate_writeup_quality(url)
                }
                enhanced_writeups.append(writeup_info)
            except Exception as e:
                logger.warning(f"Error processing writeup {url}: {e}")
                continue
        
        # Sort by estimated quality
        enhanced_writeups.sort(key=lambda w: w["quality"], reverse=True)
        cve_data["technical_writeups"] = enhanced_writeups

    def _classify_writeup_source(self, url: str) -> str:
        """Classify the source of a technical writeup."""
        url_lower = url.lower()
        
        if "github.com" in url_lower:
            return "github"
        elif "hackerone.com" in url_lower:
            return "hackerone"
        elif "bugzilla" in url_lower:
            return "bugzilla"
        elif "exploit-db.com" in url_lower:
            return "exploit-db"
        elif any(domain in url_lower for domain in ["research.", "blog."]):
            return "research_blog"
        elif "advisory" in url_lower:
            return "security_advisory"
        else:
            return "other"

    async def _estimate_writeup_quality(self, url: str) -> int:
        """Estimate the quality of a writeup on a scale of 1-5."""
        url_lower = url.lower()
        score = 1  # Base score
        
        # Preferred sources get bonus points
        if "github.com" in url_lower:
            score += 2  # Often has POC code
        elif "hackerone.com" in url_lower:
            score += 2  # Detailed reports
        elif "research." in url_lower:
            score += 1  # Research blogs
            
        # Look for indicators of detailed analysis
        if "analysis" in url_lower:
            score += 1
        if "technical" in url_lower:
            score += 1
        if "poc" in url_lower or "proof-of-concept" in url_lower:
            score += 1
            
        return min(5, score)  # Cap at 5

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