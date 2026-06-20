from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "ParkSight"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql+psycopg2://parksight:parksight@localhost:5432/parksight"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SERVICE_NAME: str = "unknown"
    CORS_ORIGINS: str = "*"
    SENTRY_DSN: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = "parksight-media"
    CLOUDWATCH_LOG_GROUP: str = "parksight"

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    OFFICER_APP_RATE_LIMIT: int = 60
    ANALYTICS_RATE_LIMIT: int = 20
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_LOCKOUT_MINUTES: int = 15

    HEATMAP_CACHE_TTL: int = 300
    PRIORITY_QUEUE_CACHE_TTL: int = 300
    ZONE_CACHE_TTL: int = 3600

    DETECTION_CONFIDENCE_THRESHOLD: float = 0.5
    FRAME_SAMPLE_INTERVAL_SECONDS: int = 5
    MAX_QUEUE_SIZE: int = 1000
    MODEL_PATH: str = "yolov8n.pt"
    MODEL_INPUT_SIZE: int = 640
    ENABLE_HALF_PRECISION: bool = True
    STREAM_CACHE_DIR: str = "/tmp/parksight-frames"
    BATCH_INTERVAL: float = 2.0

    KAFKA_CIRCUIT_BREAKER_THRESHOLD: int = 5
    KAFKA_CIRCUIT_BREAKER_COOLDOWN: float = 30.0
    FRAME_MAX_AGE_SECONDS: float = 10.0
    ENABLE_MODEL_HOT_RELOAD: bool = False
    SHADOW_MODEL_PATH: str = ""
    ENABLE_SHADOW_MODE: bool = False
    MODEL_WATCH_INTERVAL: float = 10.0
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
