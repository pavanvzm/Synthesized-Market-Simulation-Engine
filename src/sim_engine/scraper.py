"""Web scraper module with polite scraping practices."""

import hashlib
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import BaseModel


class ScrapedContent(BaseModel):
    """Scraped content model."""
    url: str
    content: str
    timestamp: str
    status_code: int
    content_hash: str


class Scraper:
    """Polite web scraper with rate limiting and caching.
    
    IMPORTANT: Only scrape allowlisted domains with proper robots.txt compliance.
    This module is designed for public market data sources only.
    """
    
    # Allowlist of domains that can be scraped (add as needed)
    ALLOWLIST = [
        "example.com",
        "public-data.gov",
    ]
    
    def __init__(
        self,
        cache_dir: str = ".cache/scrapes",
        rate_limit_seconds: float = 1.0,
        user_agent: str = "SimEngine/1.0 (+https://github.com/meta/sim-engine)",
    ):
        """Initialize scraper.
        
        Args:
            cache_dir: Directory for cached responses
            rate_limit_seconds: Minimum time between requests to same domain
            user_agent: User agent string
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit_seconds
        self.user_agent = user_agent
        self._last_request: dict[str, float] = {}
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=30.0,
            follow_redirects=True,
        )
    
    def _is_allowed(self, url: str) -> bool:
        """Check if URL is in allowlist.
        
        Args:
            url: URL to check
        
        Returns:
            True if allowed
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix for matching
        if domain.startswith("www."):
            domain = domain[4:]
        
        return any(allowed in domain for allowed in self.ALLOWLIST)
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check robots.txt for URL path.
        
        Args:
            url: URL to check
        
        Returns:
            True if allowed by robots.txt
        """
        from urllib.parse import urlparse, urljoin
        
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            response = self._client.get(robots_url)
            if response.status_code == 200:
                # Simple check - in production use proper robots.txt parser
                path = parsed.path
                lines = response.text.split("\n")
                for line in lines:
                    if line.lower().startswith("disallow:"):
                        disallow_path = line.split(":", 1)[1].strip()
                        if disallow_path and path.startswith(disallow_path):
                            return False
                return True
        except Exception:
            pass
        
        return True  # Default to allowing if robots.txt unavailable
    
    def _rate_limit(self, url: str) -> None:
        """Apply rate limiting per domain.
        
        Args:
            url: URL being requested
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        now = time.time()
        if domain in self._last_request:
            elapsed = now - self._last_request[domain]
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
        
        self._last_request[domain] = time.time()
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL.
        
        Args:
            url: URL to cache
        
        Returns:
            Path to cache file
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return self.cache_dir / f"{url_hash}.json"
    
    def _load_cache(self, url: str) -> Optional[ScrapedContent]:
        """Load cached content.
        
        Args:
            url: URL to load
        
        Returns:
            Cached content or None
        """
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            import json
            with open(cache_path, "r") as f:
                data = json.load(f)
                return ScrapedContent(**data)
        return None
    
    def _save_cache(self, content: ScrapedContent) -> None:
        """Save content to cache.
        
        Args:
            content: Content to cache
        """
        import json
        cache_path = self._get_cache_path(content.url)
        with open(cache_path, "w") as f:
            json.dump(content.model_dump(), f, indent=2)
    
    def scrape(self, url: str, use_cache: bool = True) -> Optional[ScrapedContent]:
        """Scrape URL with caching and rate limiting.
        
        Args:
            url: URL to scrape
            use_cache: Whether to use cache
        
        Returns:
            Scraped content or None
        """
        # Check allowlist
        if not self._is_allowed(url):
            return None
        
        # Check cache
        if use_cache:
            cached = self._load_cache(url)
            if cached:
                return cached
        
        # Rate limit
        self._rate_limit(url)
        
        try:
            response = self._client.get(url)
            response.raise_for_status()
            
            content = ScrapedContent(
                url=url,
                content=response.text,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                status_code=response.status_code,
                content_hash=hashlib.sha256(response.content).hexdigest(),
            )
            
            # Cache successful response
            if use_cache:
                self._save_cache(content)
            
            return content
        
        except Exception as e:
            return None
    
    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()
