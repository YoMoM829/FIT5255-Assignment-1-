from locust import HttpUser, task, between
import base64 

with open("testing/image0.jpeg", "rb") as f:
    IMAGE_B64 = base64.b64encode(f.read()).decode("utf-8")

class YoloUser(HttpUser):
    wait_time = between(1, 5)

    @task 
    def predict(self):
        with self.client.post(
            "/api/predict",
            json={
                "uuid": "e4b2c1d0-8d2e-11eb-8dcd-0242ac130003",
                "image": IMAGE_B64
            },
            timeout=60,
            catch_response=True,
            name="predict"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}: {response.text[:200]}")