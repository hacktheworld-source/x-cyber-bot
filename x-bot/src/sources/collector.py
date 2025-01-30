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

    def _is_interesting_cve(self, cve_data: dict) -> tuple[bool, list[str]]:
        """
        Simple check if a CVE is interesting enough to post about.
        Returns (is_interesting, reasons_why)
        """
        reasons = []
        desc = cve_data.get("description", "").lower()
        
        # 1. High Impact / Damage Potential
        high_impact = [
            "remote code execution",
            "privilege escalation",
            "arbitrary code",
            "root access",
            "system takeover",
            "full access",
            "critical",
            "wormable",
            "code execution",
            "escalation of privileges",
            "host binary",  # For container escapes
            "host device",  # For container escapes
            "host's network",  # For container escapes
            "data tampering"
        ]
        
        # 2. Clever/Novel Methods
        clever_methods = [
            "chain",
            "race condition",
            "side channel",
            "type confusion",
            "novel technique",
            "zero-day",
            "sandbox escape",
            "container escape",
            "improper isolation",
            "creative",
            "specially crafted",
            "bypass"
        ]
        
        # 3. Groundbreaking/Notable
        notable = [
            "first time",
            "previously unknown",
            "breakthrough",
            "major vulnerability",
            "widespread impact",
            "affects all",
            "multiple vendors",
            "nondefault way"  # Interesting misconfigurations
        ]

        # Check each category
        if any(impact in desc for impact in high_impact):
            reasons.append("high impact")
            
        if any(method in desc for method in clever_methods):
            reasons.append("clever method")
            
        if any(note in desc for note in notable):
            reasons.append("notable discovery")
            
        # Also consider CVSS if available
        try:
            cvss_score = float(cve_data.get("cvss_score", 0))
            if cvss_score >= 9.0:
                reasons.append("critical severity")
            elif cvss_score >= 7.5:
                reasons.append("high severity")
        except (TypeError, ValueError):
            # If CVSS score is invalid, just ignore it
            pass

        return len(reasons) > 0, reasons

    async def collect_recent_cves(self) -> List[dict]:
        """Collect and filter recent CVEs."""
        logger.info("Starting CVE collection")
        
        # Get recent CVEs from NVD
        cves = await self.nvd_client.get_recent_cves()
        logger.info(f"Retrieved {len(cves)} CVEs from NVD")
        
        # Debug: Print sample of raw CVEs
        for i, cve in enumerate(cves[:3]):
            logger.debug(f"\nRaw CVE {i + 1}:")
            logger.debug(f"ID: {cve.get('id', 'N/A')}")
            logger.debug(f"Description: {cve.get('description', 'N/A')}")
            logger.debug(f"CVSS: {cve.get('cvss_score', 'N/A')}")
            logger.debug(f"References: {cve.get('references', [])}")
            logger.debug(f"Technical Writeups: {cve.get('technical_writeups', [])}")
        
        # Filter for interesting ones
        interesting_cves = []
        for cve in cves:
            is_interesting, reasons = self._is_interesting_cve(cve)
            if is_interesting:
                logger.info(f"Found interesting CVE {cve['id']}: {', '.join(reasons)}")
                interesting_cves.append(cve)
            else:
                logger.debug(f"Skipping CVE {cve['id']}: No interesting factors found")
                
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