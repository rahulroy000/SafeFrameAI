
import json
import argparse
from pathlib import Path
from collections import Counter


FORMATS = {
    "9:16": {
        "width": 1080,
        "height": 1920
    },
    "1:1": {
        "width": 1080,
        "height": 1080
    },
    "4:5": {
        "width": 1080,
        "height": 1350
    },
    "16:9": {
        "width": 1920,
        "height": 1080
    }
}


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def calculate_crop(
    source_width,
    source_height,
    target_ratio,
    subject_x,
    subject_y,
    subject_y_ratio=0.38
):
    """
    Calculate a crop rectangle in original video coordinates.
    Keeps the subject inside the crop and places the face
    around the requested vertical position.
    """

    source_ratio = source_width / source_height

    if source_ratio > target_ratio:

        crop_height = float(source_height)
        crop_width = crop_height * target_ratio

    else:

        crop_width = float(source_width)
        crop_height = crop_width / target_ratio

    # Center the subject horizontally.
    crop_x = subject_x - crop_width / 2

    # Position the subject vertically.
    crop_y = subject_y - crop_height * subject_y_ratio

    # Protect crop boundaries.
    crop_x = clamp(
        crop_x,
        0,
        source_width - crop_width
    )

    crop_y = clamp(
        crop_y,
        0,
        source_height - crop_height
    )

    return {
        "x": round(crop_x, 2),
        "y": round(crop_y, 2),
        "width": round(crop_width, 2),
        "height": round(crop_height, 2)
    }


def generate_reframe(
    input_path,
    output_path,
    output_format,
    requested_track_id=None
):

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Tracking JSON not found: {input_path}"
        )

    with open(input_path, "r", encoding="utf-8") as file:
        tracking_data = json.load(file)

    video_info = tracking_data["video_info"]

    source_width = int(video_info["width"])
    source_height = int(video_info["height"])

    if source_width <= 0 or source_height <= 0:
        raise ValueError("Invalid source video dimensions")

    target = FORMATS[output_format]

    target_ratio = (
        target["width"] / target["height"]
    )

    frames = tracking_data.get("frames", [])

    # Find the most frequently detected subject.
    track_counts = Counter()

    for frame in frames:
        for subject in frame.get("subjects", []):
            track_counts[subject["track_id"]] += 1

    if not track_counts:
        raise RuntimeError(
            "No tracked subjects found in input JSON"
        )

    if requested_track_id is None:
        selected_track = track_counts.most_common(1)[0][0]
    else:
        selected_track = requested_track_id

        if selected_track not in track_counts:
            raise ValueError(
                f"Track ID {selected_track} not found"
            )

    keyframes = []

    for frame in frames:

        subjects = frame.get("subjects", [])

        subject = next(
            (
                item for item in subjects
                if item["track_id"] == selected_track
            ),
            None
        )

        # Skip frames where the selected subject is absent.
        if subject is None:
            continue

        center = subject["smoothed_center"]

        subject_x = float(center["x"])
        subject_y = float(center["y"])

        crop = calculate_crop(
            source_width,
            source_height,
            target_ratio,
            subject_x,
            subject_y
        )

        keyframes.append({

            "frame": frame["frame"],
            "time": frame["time"],

            "track_id": selected_track,

            "subject_center": {
                "x": round(subject_x, 2),
                "y": round(subject_y, 2)
            },

            "crop": crop

        })

    if not keyframes:
        raise RuntimeError(
            "No keyframes generated for selected subject"
        )

    result = {

        "project": "SafeFrame AI",

        "version": "0.3.0",

        "source": {
            "width": source_width,
            "height": source_height,
            "fps": video_info["fps"]
        },

        "output": {
            "format": output_format,
            "width": target["width"],
            "height": target["height"]
        },

        "tracking": {
            "selected_track_id": selected_track,
            "subject_samples": len(keyframes)
        },

        "keyframes": keyframes
    }

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
            result,
            file,
            indent=4
        )

    print("\nSAFEFRAME SMART REFRAMING COMPLETE")
    print("-----------------------------------")
    print(f"Format: {output_format}")
    print(f"Subject ID: {selected_track}")
    print(f"Keyframes: {len(keyframes)}")
    print(f"Output: {output_path.resolve()}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="SafeFrame AI Smart Reframing"
    )

    parser.add_argument(
        "--input",
        default="../communication/output.json"
    )

    parser.add_argument(
        "--output",
        default="../communication/reframe.json"
    )

    parser.add_argument(
        "--format",
        choices=list(FORMATS.keys()),
        default="9:16"
    )

    parser.add_argument(
        "--track-id",
        type=int,
        default=None
    )

    args = parser.parse_args()

    generate_reframe(
        args.input,
        args.output,
        args.format,
        args.track_id
    )
