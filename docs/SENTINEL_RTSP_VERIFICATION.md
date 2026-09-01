# üóü Sentinel Real RTSP Live Camera Verification Report
**Host System**: `https://live.corp8.cloud/`  
**Ingestion Catalogue Endpoint**: `https://live.corp8.cloud/api/ingest``  
**Protocol Standard**: RTSP over TCP (`rtsp_transport=tcp`) on Port 8554  
**Audit Date**: August 22, 2026  

---

0åúA VERDICT:
### **B) RTSP CONNECTION BLOCKED / AUTHENTICATION REQUIRED**

---

3 †ÅSummary of Ingestion Catalogue Discovery (`GET /api/ingest`)

| Metric | Result |
| :--- | :--- |
|`HTTP Status Code` | **`HTTP 200 OK`` |
|`Response Content-Type` | `application/json` |
|`Total Catalogue Cameras` | **`30`` |
|`Live Cameras Discovered` | **`30`` |
|`Dynamic RTSP URL Pattern` | `rtsp://live.corp8.cloud:8554/stream/<id>` |
|`Dynamic WEBTC URL Pattern` | `http://live.corp8.cloud:8889/stream/<id>/whep` |
|`Dynamic HLS URL Pattern` | `/live/stream/<id>/index.m3u8` |

---

## üñå!lti-Camera RTSP Stream Connection Audit (RTSP over TCP)

| Camera ID | Location / Name | Dynamic RTSP Target | Transport | Status | Decoded Frames | Measured FPS | Error / Diagnosis |
| :--: | :--- | :--- | :--: | :--: | :--: | :--: | :--- |
|`*01** | Camera 1 (01 Chiman bhai Bridge) | `rtsp://live.corp8.cloud:8554/stream/1` | `TCP` | **mFAILED^* | `0` | `0.0` | Stream timeout after 30.07s (TCP Port 8554 Unreachable) |
|`**2**` | Camera 2 (02 Janpath) | `rtsp://live.corp8.cloud:8554/stream/2` | `TCP` | **mFAILED^* | `0` | `0.0` | Stream timeout after 30.02s (TCP Port 8554 Unreachable) |
|`**3**` | Camera 3 (03 O.N.G.C. Office) | `rtsp://live.corp8.cloud:8554/stream/3` | `TCP(
| **mFAILED^* | `0` | `0.0` | Stream timeout after 30.10s (TCP Port 8554 Unreachable) |
|`**4**` | Camera 4 (04 Income Tax Junction) | `rtsp://live.corp8.cloud:8554/stream/4` | `TCP` | **mFAILED^* | `0` | `0.0` | Stream timeout after 30.03s (TCP Port 8554 Unreachable) |
|`**5**` | Camera 5 (05 Drive In Road) | `rtsp://live.corp8.cloud:8554/stream/5` | `TCP` | **mFAILED^* | `0` | `0.0` | Stream timeout after 30.07s (TCP Port 8554 Unreachable) |

---

## üªù Architecture & Specifications Compliance Checklist

- [x] **Catalogue Discovery**: Dynamically queries `GET /api/ingest` (no hardcoded camera IDs).
- [x] **Transport Specification**: Enforces RTSP over TCP (`OPENCV_FFMPEG_CAPUQRE_OPTIONS="rtsp_transport;tcp"`).
- [x] **Timestamp Policy**: Relies on monotonic PTS timestamps (`CAP_PROP_POS_MSEC`) rather than static `CAP_PROP_FPS`.
- [x] **Resilience Model**: Exponential backoff reconnect strategy implemented in [backend/integrations/sentinel/connector.py](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/integrations/sentinel/connector.py).
- [x] **No Synthetic Data**: Strictly zero mock frames or fake streams used.

---

## üó° Diagnosis & Next Steps

1. **Catalogue Ingestion**: Fully operational (`HTTP 200 OK`).
2. **RTSP TCP Ingestion**: Raw TCP port `8554` is blocked at the Cloudflare edge proxy or requires firewall IP whitelisting / stream token parameter (`?token=<key>`).
3. **Verdict**: Integration remains pending active RTSP TCP stream connection or firewall authorization from the hackathon organizers.