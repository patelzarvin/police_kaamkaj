import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from backend.config import settings

logger = logging.getLogger("sentinel.client")

class SentinelIngestClient:
    """
    Official Gujarat Police Sentinel Sandbox Ingestion Catalogue Client.
    Fetches the dynamic camera catalogue from GET /api/ingest at https://live.corp8.cloud
    """
    def __init__(self, host_url: Optional[str] = None):
        self.host_url = (host_url or settings.SENTINEL_HOST).rstrip('/')
        self.username = settings.SENTINEL_USERNAME
        self.password = settings.SENTINEL_PASSWORD
        self.auth_token = settings.SENTINEL_AUTH_TOKEN

    def get_auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def fetch_catalogue(self) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """
        Queries GET /api/ingest from the live host.
        Returns (reachable: bool, catalogue: List[Dict], error_msg: Optional[str])
        """
        endpoint = f"{self.host_url}/api/ingest"
        headers = self.get_auth_headers()
        auth = (self.username, self.password) if (self.username and self.password) else None

        try:
            resp = requests.get(endpoint, headers=headers, auth=auth, timeout=8.0, verify=True)
            if resp.status_code == 200:
                data = resp.json()
                catalogue = []
                if isinstance(data, list):
                    catalogue = data
                elif isinstance(data, dict):
                    catalogue = data.get("cameras") or data.get("data") or [data]
                
                logger.info(f"Successfully fetched Sentinel catalogue from {endpoint}: {len(catalogue)} cameras discovered.")
                return True, catalogue, None
            elif resp.status_code in (401, 403):
                msg = f"HTTP {resp.status_code} Unauthorized at {endpoint}"
                logger.warning(msg)
                return True, [], "AUTHENTICATION_REQUIRED"
            else:
                msg = f"HTTP {resp.status_code} Error from {endpoint}"
                logger.warning(msg)
                return False, [], msg
        except Exception as e:
            msg = f"Connection error reaching {endpoint}: {e}"
            logger.error(msg)
            return False, [], msg

    def build_stream_url(self, raw_url: str) -> str:
        """
        Appends authentication parameters or credentials to stream URLs if provided.
        """
        if not raw_url:
            return ""

        # Make relative HLS URLs absolute
        if raw_url.startswith("/"):
            raw_url = f"{self.host_url}{raw_url}"

        if self.auth_token and "token=" not in raw_url:
            separator = "&" if "?" in raw_url else "?"
            return f"{raw_url}{separator}token={self.auth_token}"
        
        if self.username and self.password and "rtsp://" in raw_url and "@" not in raw_url:
            proto, rest = raw_url.split("rtsp://", 1)
            return f"rtsp://{self.username}:{self.password}@{rest}"

        return raw_url
