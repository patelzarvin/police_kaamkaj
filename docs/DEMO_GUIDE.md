# Gujarat Police Sentinel — Hackathon Evaluation Demo Guide

---

## 2–3 Minute Hackathon Evaluation Storyboard

### Scene 1: Command Center Launch
- **Action**: Open Police Dashboard (`http://localhost:3000`).
- **Visual**: Showcase futuristic dark command center UI, active camera counts, live clock, and system health status.

### Scene 2: Live Sentinel CCTV Camera Grid
- **Action**: Navigate to **Live Camera Grid** tab.
- **Visual**: Show live stream feeds from Gujarat cameras (Ahmedabad, Gandhinagar, GIFT City Toll Gate). Point out `RTSP TCP LIVE`, `H.264`/`H.265` codec badges, and real-time PTS timestamps.

### Scene 3: Vehicle Movement & Watchlist Alert Trigger
- **Action**: Run `python scripts/demo_simulation.py` or observe real-time detection feed.
- **Visual**: Vehicle `GJ01AB1234` is detected by YOLO and ANPR. A real-time **🚨 CRITICAL WATCHLIST ALERT** pulses on screen with sound trigger.

### Scene 4: Police Vehicle Search Query
- **Action**: Type target vehicle plate `GJ01AB1234` into the top search bar and click **TRACK**.
- **Visual**: Reconstructs the complete chronological journey timeline:
  - **Node #1**: `CAM-01 (Ahmedabad SG Highway ISCON)` @ `10:32 AM`
  - **Node #2**: `CAM-07 (Ahmedabad SG Highway Vaishno Devi)` @ `10:41 AM`
  - **Node #3**: `CAM-19 (Gandhinagar CH-0 Circle)` @ `10:55 AM`
  - **Node #4**: `CAM-31 (Gandhinagar GIFT City Toll Gate)` @ `11:08 AM`

### Scene 5: GIS Trajectory Polyline Visualization
- **Action**: Scroll down to the interactive **GIS Route Map**.
- **Visual**: Shows camera markers across Gujarat connected by an animated Cyan polyline showing the exact path taken by `GJ01AB1234`.
