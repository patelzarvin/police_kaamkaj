import numpy as np
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("sentinel.ai.tracker")

class CentroidTracker:
    """
    Multi-Object Centroid Tracker.
    Assigns persistent track_ids to detected vehicles across sequential video frames.
    """
    def __init__(self, max_disappeared: int = 25, max_distance: int = 120):
        self.next_object_id = 101
        self.objects: Dict[int, Tuple[int, int]] = {}
        self.disappeared: Dict[int, int] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid: Tuple[int, int]) -> int:
        object_id = self.next_object_id
        self.objects[object_id] = centroid
        self.disappeared[object_id] = 0
        self.next_object_id += 1
        return object_id

    def deregister(self, object_id: int):
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Input: List of detections dicts with 'bbox' [x1, y1, x2, y2]
        Output: Updated list of detections with assigned 'track_id'
        """
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return detections

        input_centroids = np.zeros((len(detections), 2), dtype="int")
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det["bbox"]
            cX = int((x1 + x2) / 2.0)
            cY = int((y1 + y2) / 2.0)
            input_centroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                track_id = self.register(tuple(input_centroids[i]))
                detections[i]["track_id"] = track_id
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Distance matrix computation
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > self.max_distance:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = tuple(input_centroids[col])
                self.disappeared[object_id] = 0
                detections[col]["track_id"] = object_id

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])) - used_rows
            unused_cols = set(range(0, D.shape[1])) - used_cols

            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    track_id = self.register(tuple(input_centroids[col]))
                    detections[col]["track_id"] = track_id

        return detections
