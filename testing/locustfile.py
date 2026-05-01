from locust import HttpUser, task, between, events, LoadTestShape
import base64
import csv
import os
import gevent
import time

# ==============================
# CONFIG
# ==============================
FAILURE_THRESHOLD = 0.50   # 50%
MAX_USERS = 100
SPAWN_RATE = 5

MAX_USERS = 2000  # change this higher if needed

USER_STEPS = [1, 10, 25, 50, 75, 100] + list(range(125, MAX_USERS + 1, 25))

SUMMARY_CSV = "auto_results_summary.csv"
TEST_IMAGE = "testing/image0.jpeg"

current_stage_index = 0
stage_start_time = None


def request_limit_for_users(users):
    if users < 10:
        return 50
    return users * 7


# ==============================
# LOCUST USER
# ==============================
class YoloUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        with open(TEST_IMAGE, "rb") as f:
            self.image_data = base64.b64encode(f.read()).decode("utf-8")

    # @task
    # def annotate(self):
    #     with self.client.post(
    #         "/api/annotate",
    #         json={
    #             "uuid": "e4b2c1d0-8d2e-11eb-8dcd-0242ac130003",
    #             "image": self.image_data
    #         },
    #         timeout=60,
    #         catch_response=True,
    #         name="annotate"
    #     ) as response:
    #         if response.status_code != 200:
    #             response.failure(f"Status {response.status_code}: {response.text[:200]}")

    # Predict check
    @task
    def predict(self):
        with self.client.post(
            "/api/predict",
            json={
                "uuid": "e4b2c1d0-8d2e-11eb-8dcd-0242ac130003",
                "image": self.image_data
            },
            timeout=60,
            catch_response=True,
            name="predict"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}: {response.text[:200]}")


# ==============================
# LOAD SHAPE
# ==============================
class AutoStepLoadShape(LoadTestShape):
    def tick(self):
        global current_stage_index

        if current_stage_index >= len(USER_STEPS):
            return None

        users = USER_STEPS[current_stage_index]
        return users, SPAWN_RATE


# ==============================
# CSV SETUP
# ==============================
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    if not os.path.exists(SUMMARY_CSV):
        with open(SUMMARY_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "users",
                "request_limit",
                "requests",
                "failures",
                "failure_rate",
                "avg_response_time_ms",
                "min_response_time_ms",
                "max_response_time_ms",
                "requests_per_second",
                "duration_seconds",
                "stopped_reason"
            ])


# ==============================
# AUTO TEST MONITOR
# ==============================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    def monitor():
        global current_stage_index, stage_start_time

        # Give Locust a moment to start
        gevent.sleep(2)

        while current_stage_index < len(USER_STEPS):
            users = USER_STEPS[current_stage_index]
            request_limit = request_limit_for_users(users)

            print(f"\n[START] Testing {users} users")
            print(f"[INFO] Request target: {request_limit}")

            environment.runner.stats.reset_all()
            stage_start_time = time.time()

            # Wait until the current user count has ramped properly
            while environment.runner.user_count < users:
                gevent.sleep(1)

            while True:
                stats = environment.runner.stats.total
                requests = stats.num_requests
                failures = stats.num_failures

                if requests > 0:
                    failure_rate = failures / requests
                else:
                    failure_rate = 0

                if requests >= request_limit:
                    stopped_reason = "request_limit_reached"
                    break

                if requests >= 10 and failure_rate >= FAILURE_THRESHOLD:
                    stopped_reason = "failure_threshold_reached"
                    break

                gevent.sleep(1)

            duration = time.time() - stage_start_time
            stats = environment.runner.stats.total

            requests = stats.num_requests
            failures = stats.num_failures
            failure_rate = failures / requests if requests > 0 else 0

            with open(SUMMARY_CSV, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    users,
                    request_limit,
                    requests,
                    failures,
                    round(failure_rate, 4),
                    round(stats.avg_response_time, 2),
                    stats.min_response_time,
                    stats.max_response_time,
                    round(stats.total_rps, 2),
                    round(duration, 2),
                    stopped_reason
                ])

            if failure_rate >= FAILURE_THRESHOLD:
                print("[STOP] Failure threshold reached. Stopping entire Locust test.")
                environment.runner.quit()
                return

            current_stage_index += 1

        print("[COMPLETE] All user levels tested.")
        environment.runner.quit()

    gevent.spawn(monitor)