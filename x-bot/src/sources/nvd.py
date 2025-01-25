import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
from loguru import logger

class NVDClient:
    def __init__(self, config: dict):
        self.base_url = config["base_url"]
        self.request_delay = config["request_delay"]
        self.last_request_time = datetime.min
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed NVD's rate limits."""
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        self.last_request_time = datetime.now()

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _process_cve_data(self, raw_cve: dict) -> dict:
        """Extract relevant information from NVD's CVE format."""
        try:
            cve_data = {
                "id": raw_cve["cve"]["id"],
                "published_date": datetime.fromisoformat(raw_cve["cve"]["published"].replace("Z", "+00:00")),
                "description": raw_cve["cve"]["descriptions"][0]["value"],
                "references": [ref["url"] for ref in raw_cve["cve"].get("references", [])],
                "cvss_score": None,
                "technical_writeups": [],
                "interesting_factors": []
            }

            # Extract CVSS score if available
            metrics = raw_cve["cve"].get("metrics", {})
            if "cvssMetricV31" in metrics:
                cve_data["cvss_score"] = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV30" in metrics:
                cve_data["cvss_score"] = metrics["cvssMetricV30"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV2" in metrics:
                cve_data["cvss_score"] = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]

            # Initial assessment of interesting factors
            interesting_factors = []
            
            # Check for potentially interesting patterns in description
            desc_lower = cve_data["description"].lower()
            interesting_patterns = [
                ("race condition", "Potential race condition vulnerability"),
                ("buffer overflow", "Memory corruption via buffer overflow"),
                ("use after free", "Use-after-free vulnerability"),
                ("privilege escalation", "Privilege escalation potential"),
                ("remote code execution", "Remote code execution possibility"),
                ("zero-day", "Zero-day vulnerability"),
                ("sandbox escape", "Sandbox escape mechanism"),
                ("authentication bypass", "Authentication bypass technique")
            ]
            
            for pattern, factor in interesting_patterns:
                if pattern in desc_lower:
                    interesting_factors.append(factor)

            # Check reference URLs for technical writeups
            technical_writeups = []
            writeup_domains = [
                "github.com",
                "hackerone.com",
                "bugzilla",
                "exploit-db.com",
                "research.",
                "blog.",
                "advisory"
            ]
            
            for ref in cve_data["references"]:
                if any(domain in ref.lower() for domain in writeup_domains):
                    technical_writeups.append(ref)

            cve_data["technical_writeups"] = technical_writeups
            cve_data["interesting_factors"] = interesting_factors

            return cve_data
            
        except KeyError as e:
            logger.error(f"Error processing CVE data: {e}")
            logger.debug(f"Raw CVE data: {raw_cve}")
            raise ValueError(f"Invalid CVE data format: {e}")

    async def get_recent_cves(self, hours: int = 48) -> List[dict]:
        """Fetch CVEs from the last specified hours."""
        await self._wait_for_rate_limit()
        
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        params = {
            "pubStartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
        }
        
        try:
            session = await self._get_session()
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"NVD API error: {response.status}")
                    return []
                
                data = await response.json()
                
                if "vulnerabilities" not in data:
                    logger.error("No vulnerabilities field in NVD response")
                    return []
                
                processed_cves = []
                for vuln in data["vulnerabilities"]:
                    try:
                        processed = self._process_cve_data(vuln)
                        processed_cves.append(processed)
                    except ValueError as e:
                        logger.error(f"Error processing vulnerability: {e}")
                        continue
                
                return processed_cves
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching CVEs: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching CVEs: {e}")
            return []

    async def get_cve_details(self, cve_id: str) -> Optional[dict]:
        """Fetch details for a specific CVE."""
        await self._wait_for_rate_limit()
        
        params = {"cveId": cve_id}
        
        try:
            session = await self._get_session()
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"NVD API error: {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("vulnerabilities"):
                    logger.error(f"No data found for CVE {cve_id}")
                    return None
                
                return self._process_cve_data(data["vulnerabilities"][0])
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching CVE {cve_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching CVE {cve_id}: {e}")
            return None 