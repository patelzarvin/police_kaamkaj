import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("sentinel.catalog_client")

class SentinelCatalogClient:
    """
    Client for interacting with official Gujarat Police Sentinel Catalogue API Contract (/api/ingest).
    Discovers camera IDs, stream protocols, codecs, resolutions, and properties dynamically.
    """
    def __init__(self, catalog_url: str = "http://localhost:8000/api/ingest", api_key: Optional[str] = None):
        self.catalog_url = catalog_url
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def fetch_catalog(self) -> List[Dict[str, Any]]:
        """Fetch latest camera assets catalog contract."""
        try:
            logger.info(f"Querying Sentinel Camera Catalogue: {self.catalog_url}")
            response = requests.get(self.catalog_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                catalog = response.json()
                logger.info(f"Successfully retrieved {len(catalog)} camera entries from Sentinel catalog.")
                return catalog
            else:
                logger.warning(f"Catalog query returned HTTP {response.status_code}. Using fallback catalog.")
                return self._get_fallback_catalog()
        except Exception as e:
            logger.error(f"Failed to query Sentinel catalog endpoint ({e}). Using local fallback catalog.")
            return self._get_fallback_catalog()

    def _get_fallback_catalog(self) -> List[Dict[str, Any]]:
        """Fallback local camera catalog matching Sentinel structure."""
        return [
            {
                "id": "CAM-01",
                "name": "Ahmedabad SG Highway - ISCON Cross Road",
                "department": "Home Department",
                "latitude": 23.0276,
                "longitude": 72.5074,
                "codec": "H264",
                "resolution": "1920x1080",
                "fps": 25.0,
                "live_status": "ONLINE",
                "rtsp_url": "rtsp://localhost:8554/stream/1",
                "hls_url": "http://localhost:8888/stream/1/index.m3u8",
                "webrtc_url": "http://localhost:8889/stream/1",
                "properties": {"transport": "tcp", "pts_timestamp_support": True}
            },
            {
                "id": "CAM-07",
                "name": "Ahmedabad SG Highway - Vaishno Devi Circle",
                "department": "Home Department",
                "latitude": 23.1184,
                "longitude": 72.5401,
                "codec": "H264",
                "resolution": "1920x1080",
                "fps": 25.0,
                "live_status": "ONLINE",
                "rtsp_url": "rtsp://localhost:8554/stream/7",
                "hls_url": "http://localhost:8888/stream/7/index.m3u8",
                "webrtc_url": "http://localhost:8889/stream/7",
                "properties": {"transport": "tcp", "pts_timestamp_support": True}
            },
            {
                "id": "CAM-19",
                "name": "Gandhinagar - CH-0 Circle Police Post",
                "department": "Home Department",
                "latitude": 23.2156,
                "longitude": 72.6369,
                "codec": "H265",
                "resolution": "1920x1080",
                "fps": 30.0,
                "live_status": "ONLINE",
                "rtsp_url": "rtsp://localhost:8554/stream/19",
                "hls_url": "http://localhost:8888/stream/19/index.m3u8",
                "webrtc_url": "http://localhost:8889/stream/19",
                "properties": {"transport": "tcp", "pts_timestamp_support": True}
            },
            {
                "id": "CAM-31",
                "name": "Gandhinagar - GIFT City Expressway Toll Gate",
                "department": "Transport Department (RTO)",
                "latitude": 23.1610,
                "longitude": 72.6845,
                "codec": "H264",
                "resolution": "3840x2160",
                "fps": 30.0,
                "live_status": "ONLINE",
                "rtsp_url": "rtsp://localhost:8554/stream/31",
                "hls_url": "http://localhost:8888/stream/31/index.m3u8",
                "webrtc_url": "http://localhost:8889/stream/31",
                "properties": {"transport": "tcp", "pts_timestamp_support": True}
            }
        ]
