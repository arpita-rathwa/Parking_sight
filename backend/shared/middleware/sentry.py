import sentry_sdk

from shared.config.settings import settings


def init_sentry(service_name: str):
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            service_name=service_name,
            traces_sample_rate=0.2,
            environment="production" if not settings.DEBUG else "development",
        )
