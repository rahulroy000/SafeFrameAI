
import cv2
import json
import argparse
from pathlib import Path


def create_preview(video_path, json_path, output_path):

    video_path = Path(video_path)
    json_path = Path(json_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(video_path)

    if not json_path.exists():
        raise FileNotFoundError(json_path)

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError("Could not open video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = cv2.VideoWriter(
        str(output_path),
        fourcc,
        fps,
        (width, height)
    )

    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Could not create output video")

    # Map analyzed frame numbers to tracking data
    frame_map = {
        item["frame"]: item
        for item in data["frames"]
    }

    frame_index = 0

    print("Creating tracking preview...")

    try:
        while True:

            success, frame = cap.read()

            if not success:
                break

            if frame_index in frame_map:

                frame_data = frame_map[frame_index]

                for subject in frame_data["subjects"]:

                    box = subject["bounding_box"]

                    x = box["x"]
                    y = box["y"]
                    w = box["width"]
                    h = box["height"]

                    track_id = subject["track_id"]

                    center = subject["smoothed_center"]

                    # Draw bounding box
                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

                    # Draw tracking ID
                    label = f"Subject ID: {track_id}"

                    cv2.putText(
                        frame,
                        label,
                        (x, max(25, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                    # Draw smoothed center
                    cx = int(center["x"])
                    cy = int(center["y"])

                    cv2.circle(
                        frame,
                        (cx, cy),
                        6,
                        (0, 0, 255),
                        -1
                    )

            writer.write(frame)
            frame_index += 1

    finally:
        cap.release()
        writer.release()

    print("Preview created successfully!")
    print(f"Output: {output_path.resolve()}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--json", required=True)
    parser.add_argument(
        "--output",
        default="../assets/tracking_preview.mp4"
    )

    args = parser.parse_args()

    create_preview(
        args.input,
        args.json,
        args.output
    )
