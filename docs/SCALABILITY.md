# Gujarat Police Sentinel — Scalability Architecture Strategy (~80,000 Cameras)

---

## 1. Architectural Strategy for Statewide Deployment

To scale from local PoC (5–50 cameras) to full Gujarat statewide deployment (~80,000 cameras across 26 government departments), the system employs a **3-Tier Federated Architecture**:

```
[District Edge Gateways] ---> [Kafka Event Backbone] ---> [Central GPU Pool & PostGIS]
(~800 Regional Nodes)        (100k events/sec)           (Partitioned Storage & Dashboard)
```

### Tier 1: District Edge AI Gateways (~800 Edge Clusters)
- Deployed at District Police Headquarters & Command Centers (e.g., Ahmedabad, Surat, Vadodara, Rajkot, Coastal/Border Districts).
- Local stream ingestion handling RTSP over TCP for ~100 cameras per edge node.
- Performs edge H.264/H.265 decoding, lightweight YOLO vehicle detection, and ANPR plate crop extraction.
- Sends lightweight metadata JSON payloads rather than raw video streams to conserve WAN network bandwidth.

### Tier 2: Distributed Event Messaging Backbone (Kafka / RabbitMQ)
- High-throughput Kafka cluster handling 100,000+ detection events per second.
- Decouples stream ingestion workers from database persistence and alert routing engines.
- Topic partitioning based on `district_id` and `camera_id` for parallel processing.

### Tier 3: Central Control Plane & PostGIS Database Tier
- **Database Horizontal Partitioning**: PostgreSQL `detections` table partitioned by `timestamp` range (monthly/weekly partitions).
- **PostGIS Spatial Indexing**: `GIST` indexes on `GEOMETRY(Point, 4326)` camera locations enabling sub-50ms radius geospatial queries.
- **Caching & Hot Storage**: Redis cluster storing active vehicle tracks and real-time alert state.
- **Object Storage Tiering**: MinIO / S3 distributed object storage for vehicle bounding box crops and plate crops with 30-day hot retention and S3 Glacier archive tiering.
