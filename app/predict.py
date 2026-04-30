import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

from ultralytics import YOLO
from PIL import Image
import base64
import io


model_path = "fire-models/fire_m.pt"
model = YOLO(model_path)

conf_threshold = 0.5
iou_threshold = 0.5


def run_model(image):
    return model.predict(
        image,
        conf=conf_threshold,
        iou=iou_threshold,
        device="cpu",
        imgsz=640,
        verbose=False
    )[0]


def process(image):
    result = run_model(image)

    class_names = model.model.names

    detections = []
    boxes = []

    for i in range(len(result.boxes)):
        cls_id = int(result.boxes.cls[i])
        label = class_names[cls_id]
        detections.append(label)

        x1, y1, x2, y2 = result.boxes.xyxy[i].tolist()
        conf = float(result.boxes.conf[i])

        boxes.append({
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1,
            "probability": conf
        })

    speeds = result.speed

    return {
        "detections": detections,
        "boxes": boxes,
        "speed_preprocess_ms": speeds["preprocess"],
        "speed_inference_ms": speeds["inference"],
        "speed_postprocess_ms": speeds["postprocess"]
    }


def annotate_image(image):
    result = run_model(image)

    annotated_array = result.plot()

    # Ultralytics/OpenCV gives BGR, PIL expects RGB
    annotated_array = annotated_array[:, :, ::-1]

    annotated_image = Image.fromarray(annotated_array)

    buffered = io.BytesIO()
    annotated_image.save(buffered, format="JPEG")

    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return encoded_image