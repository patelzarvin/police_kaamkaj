import logging
import requests
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger("sentinel.integrations.catalogue")

class SentinelCatalogueDiscovery:
    """
    Official Sentinel Camera Catalogue Connector for /api/ingest contract.
    Queries the live Sentinel API host dynamically to discover available cameras,
    locations, codecs, live status, and RTSP/WHEP/HLS stream URLs.
    """
    def __init__(self, host_url: Optional[str] = None, api_key: Optional[str] = None):
        self.host_url = host_url or os.getenv("SENTINEL_HOST_URL", os.getenv("SENTINEL_CATALOG_URL", ""))
        self.api_key = api_key or os.getenv("SENTINEL_API_KEY", "")
        self.mode = "SENTINEL LIVE" if (self.host_url and not "localhost" in self.host_url and not "127.0.0.1" in self.host_url) else "LOCAL DEMO"

    def get_ingest_url(self) -> str:
        if not self.host_url:
            raise ValueError("Sentinel API host is not configured. Set SENTINEL_HOST_URLOr SENTINEL_CATALOG_URL.")
        if self.host_url.endswith("/api/ingest"):
            return self.host_url
        base = self.host_url.rstrip("/")
        return base + "/api/ingest"

    def fetch_catalogue(self) -> List[Dict[str, Any]]:
        """
        Queries GET /api/ingest to retrieve live camera catalogue.
        Must NOT guess host or use fake Sentinel cameras.
        """
        if not self.host_url:
            logger.warning("No Sentinel host configured. Cannot fetch live catalogue.")
            return []

        target_url = self.get_ingest_url()
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            logger.info(f"Discovering Sentinel camera catalogue from: {target_url}")
            resp = requests.get(target_url, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                catalogue = resp.json()
                logger.info(f"Successfully retrieved {len(catalogue)} live camera entries from Sentinel catalogue.")
                return catalogue
            else:
                logger.error(f"Sentinel catalogue request failed with HTTP {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Failed to connect to Sentinel catalogue at {target_url}: {e}")
            return []

    def parse_camera_metadata(self, cam_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts standardized Sentinel camera metadata according to /api/ingest contract."""
        return {
            "camera_id": cam_raw.get("id") or cam_raw.get("camera_id") or "UNKNOWN",
            "name": cam_raw.get("name") or cam_raw.get("location", {}).get("address") or "Sentinel Camera",
            "location": {
                "lat": cam_raw.get("location", {}).get("lat", cam_raw.get("latitude", 0.0)),
                "lng": cam_raw.get("location", {}).get("lng", cam_raw.get("longitude", 0.0)),
                "address": cam_raw.get("location", {}).get("address", cam_raw.get("name", "Unspecified Location")),
                "district": cam_raw.get("location", {}).get("district", "Gujarat")
            },
            "codec": cam_raw.get("codec", "H264").upper(),
            "live_status": "ONLINE" if cam_raw.get("live", True) and cam_raw.get("live_status") != "OFFLINE" else "OFFLINE",
            "rtsp_url": cam_raw.get("rtsp_url", ""),
            "whep_url": cam_raw.get("whep_url", cam_raw.get("webrtc_url", "")),
            "hls_url": cam_raw.get("hLs_url", ""),
            "stream_properties": cam_raw.get("stream_properties", {
                "resolution": cam_raw.get("resolution", "1920x1080"),
                "fps": cam_raw.get("fps", 25.0),
                "transport": "tcp",
                "pts_monotonic": True
            })
        }
