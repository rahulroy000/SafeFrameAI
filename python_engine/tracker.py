
import math


class SubjectTracker:
    """
    Associates detected faces across sampled video frames.
    Assigns persistent tracking IDs.
    """

    def __init__(self, max_distance=150, max_missed=5):
        self.max_distance = max_distance
        self.max_missed = max_missed
        self.tracks = {}
        self.next_id = 1

    def update(self, detections):
        """
        Input: list of face bounding boxes.
        Output: list of faces with tracking IDs.
        """

        candidates = []

        # Calculate distances between existing tracks
        # and new detections.
        for track_id, track in self.tracks.items():

            for index, detection in enumerate(detections):

                dx = (
                    track["center_x"] -
                    detection["center_x"]
                )

                dy = (
                    track["center_y"] -
                    detection["center_y"]
                )

                distance = math.sqrt(dx * dx + dy * dy)

                if distance <= self.max_distance:
                    candidates.append(
                        (distance, track_id, index)
                    )

        # Match nearest available pairs first.
        candidates.sort(key=lambda item: item[0])

        used_tracks = set()
        used_detections = set()

        for distance, track_id, index in candidates:

            if track_id in used_tracks:
                continue

            if index in used_detections:
                continue

            detection = detections[index]

            detection["track_id"] = track_id

            self.tracks[track_id].update({
                "center_x": detection["center_x"],
                "center_y": detection["center_y"],
                "missed": 0
            })

            used_tracks.add(track_id)
            used_detections.add(index)

        # Create new tracks for unmatched detections.
        for index, detection in enumerate(detections):

            if index in used_detections:
                continue

            track_id = self.next_id
            self.next_id += 1

            detection["track_id"] = track_id

            self.tracks[track_id] = {
                "center_x": detection["center_x"],
                "center_y": detection["center_y"],
                "missed": 0
            }

        # Update missing tracks.
        for track_id in list(self.tracks.keys()):

            if track_id not in used_tracks:

                matched_new = any(
                    d.get("track_id") == track_id
                    for d in detections
                )

                if not matched_new:
                    self.tracks[track_id]["missed"] += 1

            if (
                self.tracks[track_id]["missed"]
                > self.max_missed
            ):
                del self.tracks[track_id]

        return detections


import math


class SubjectTracker:
    def __init__(self, max_distance=180, max_missed=15):
        self.next_id = 1
        self.tracks = {}
        self.max_distance = max_distance
        self.max_missed = max_missed

    @staticmethod
    def distance(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def update(self, detections):
        """
        detections: list of dictionaries containing center=[x, y]
        Returns detections with track_id added.
        """

        unmatched_tracks = set(self.tracks.keys())
        unmatched_detections = set(range(len(detections)))

        candidates = []

        # Build possible matches using nearest distance.
        for track_id, track in self.tracks.items():
            for index, detection in enumerate(detections):
                center = detection["center"]
                distance = self.distance(track["center"], center)

                if distance <= self.max_distance:
                    candidates.append((distance, track_id, index))

        # Greedy matching: shortest distance first.
        candidates.sort(key=lambda item: item[0])

        matches = []

        for distance, track_id, index in candidates:
            if track_id not in unmatched_tracks:
                continue
            if index not in unmatched_detections:
                continue

            matches.append((track_id, index))
            unmatched_tracks.remove(track_id)
            unmatched_detections.remove(index)

        # Update matched tracks.
        for track_id, index in matches:
            detection = detections[index]
            center = detection["center"]

            self.tracks[track_id]["center"] = center
            self.tracks[track_id]["missed"] = 0
            detection["track_id"] = track_id

        # Keep temporarily missing tracks alive.
        for track_id in unmatched_tracks:
            self.tracks[track_id]["missed"] += 1

            if self.tracks[track_id]["missed"] > self.max_missed:
                del self.tracks[track_id]

        # Create tracks for unmatched detections.
        for index in unmatched_detections:
            detection = detections[index]
            track_id = self.next_id
            self.next_id += 1

            detection["track_id"] = track_id

            self.tracks[track_id] = {
                "center": detection["center"],
                "missed": 0
            }

        return detections
