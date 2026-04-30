from fastapi import FastAPI
from pydantic import BaseModel
import base64
from PIL import Image
from predict import process, annotate_image
import io


class Input(BaseModel):
    uuid: str
    image: str


class Output(BaseModel):
    uuid: str
    count: int
    detections: list[str]
    boxes: list[dict]
    speed_preprocess_ms: float
    speed_inference_ms: float
    speed_postprocess_ms: float


class AnnotateOutput(BaseModel):
    uuid: str
    image: str


app = FastAPI()


@app.post("/api/predict")
def predict(request: Input):
    bs64string = base64.b64decode(request.image)
    image = Image.open(io.BytesIO(bs64string)).convert("RGB")

    output = process(image)

    return Output(
        uuid=request.uuid,
        count=len(output["detections"]),
        detections=output["detections"],
        boxes=output["boxes"],
        speed_preprocess_ms=output["speed_preprocess_ms"],
        speed_inference_ms=output["speed_inference_ms"],
        speed_postprocess_ms=output["speed_postprocess_ms"],
    )


@app.post("/api/annotate")
def annotate(request: Input):
    bs64string = base64.b64decode(request.image)
    image = Image.open(io.BytesIO(bs64string)).convert("RGB")

    encoded_image = annotate_image(image)

    return AnnotateOutput(
        uuid=request.uuid,
        image=encoded_image,
    )