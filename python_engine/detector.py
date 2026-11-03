
import cv2
from pathlib import Path


class FaceDetector:

    def __init__(self):

        # SafeFrame AI project root
        project_root = Path(__file__).resolve().parent.parent

        # Local model location
        model_path = (
            project_root
            / "assets"
            / "models"
            / "haarcascade_frontalface_default.xml"
        )

        if not model_path.is_file():
            raise FileNotFoundError(
                f"Face model missing: {model_path}"
            )

        # Load OpenCV model
        self.detector = cv2.CascadeClassifier(
            str(model_path)
        )

        if self.detector.empty():
            raise RuntimeError(
                "OpenCV could not load the Haar Cascade model"
            )

        print("SafeFrame AI Face Detector Ready!")
        print(f"Model: {model_path}")

    def detect(self, frame):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40)
        )

        results = []

        for x, y, w, h in faces:

            results.append({
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "center_x": int(x + w / 2),
                "center_y": int(y + h / 2)
            })

        return results
