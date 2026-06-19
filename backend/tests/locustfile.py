from locust import HttpUser, task, between


class ParkSightLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        self.client.get("/api/v1/health")

    @task(3)
    def get_heatmap(self):
        self.client.get("/api/v1/heatmap?hours=24&resolution=0.001")

    @task(2)
    def get_priority_queue(self):
        self.client.get("/api/v1/priority-queue?top_n=10&hours=24")

    @task(1)
    def get_alerts(self):
        self.client.get("/api/v1/alerts")

    @task(1)
    def get_analytics(self):
        self.client.get("/api/v1/analytics/trends?days=30")

    @task(1)
    def login(self):
        self.client.post("/api/v1/auth/login", data={
            "username": "test@parksight.com",
            "password": "test123",
        })
