
import cv2
import json
import argparse

from pathlib import Path

from detector import FaceDetector
from tracker import SubjectTracker
from smoother import CoordinateSmoother


def analyze_video(video_path, output_path, sample_every=15, alpha=0.35):

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    if sample_every < 1:
        raise ValueError(
            "sample_every must be at least 1"
        )

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open input video"
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    detector = FaceDetector()

    tracker = SubjectTracker(
        max_distance=150,
        max_missed=5
    )

    smoother = CoordinateSmoother(alpha=alpha)

    output = {
        "project": "SafeFrame AI",
        "version": "0.2.0",
        "video": video_path.name,

        "video_info": {
            "width": width,
            "height": height,
            "fps": fps,
            "total_frames": total_frames
        },

        "tracking_settings": {
            "sample_every": sample_every,
            "smoothing_alpha": 0.35
        },

        "frames": []
    }

    frame_index = 0

    print("Starting SafeFrame AI tracking...")

    try:

        while True:

            success, frame = cap.read()

            if not success:
                break

            if frame_index % sample_every == 0:

                # 1. Detect faces
                faces = detector.detect(frame)

                # 2. Associate faces with existing tracks
                tracked_faces = tracker.update(faces)

                frame_results = []

                for face in tracked_faces:

                    track_id = face["track_id"]

                    # 3. Smooth subject coordinates
                    smooth_position = smoother.smooth(
                        track_id,
                        face["center_x"],
                        face["center_y"]
                    )

                    frame_results.append({

                        "track_id": track_id,

                        "bounding_box": {
                            "x": face["x"],
                            "y": face["y"],
                            "width": face["width"],
                            "height": face["height"]
                        },

                        "center": {
                            "x": face["center_x"],
                            "y": face["center_y"]
                        },

                        "smoothed_center": smooth_position

                    })

                # Remove smoothing history for expired tracks
                active_ids = set(tracker.tracks.keys())

                for old_id in list(smoother.previous.keys()):

                    if old_id not in active_ids:
                        smoother.remove_track(old_id)

                timestamp = (
                    frame_index / fps
                    if fps > 0 else 0
                )

                output["frames"].append({

                    "frame": frame_index,

                    "time": round(timestamp, 3),

                    "subjects": frame_results

                })

                print(
                    f"Frame {frame_index}: "
                    f"{len(frame_results)} subject(s) tracked"
                )

            frame_index += 1

    finally:
        cap.release()

    # 4. Export tracking data
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4
        )

    print("\nTracking completed!")

    print(
        f"Frames analyzed: {len(output['frames'])}"
    )

    print(
        f"JSON saved: {output_path.resolve()}"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="SafeFrame AI Subject Tracking"
    )

    parser.add_argument(
        "--input",
        required=True
    )

    parser.add_argument(
        "--output",
        default="../communication/output.json"
    )

    parser.add_argument(
        "--sample-every",
        type=int,
        default=15
    )

    args = parser.parse_args()

    analyze_video(
        args.input,
        args.output,
        args.sample_every
    )
